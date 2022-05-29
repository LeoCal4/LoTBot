import re
from typing import Union

from lot_bot import constants as cst
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import user_manager, analytics_manager
from lot_bot.handlers import callback_handlers, message_handlers
from telegram import Update
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.dispatcher import CallbackContext

MIN_REF_CODE_LEN = 4
MAX_REF_CODE_LEN = 12

################################## CONVERSATION STATES ####################################


UPDATE_PERSONAL_REFERRAL = 0
UPDATE_LINKED_REFERRAL = 1
REFERRAL_UPDATED = 2


################################## GENERAL METHODS ####################################

    
def to_ref_code_menu_from_referral_update_callback(update: Update, context: CallbackContext) -> int:
    """Codice Referral menù handler that closes the conversation.

    Args:
        update (Update)
        context (CallbackContext)

    Returns:
        int: ConversationHandler.END (-1), to signal the end of the conversation
    """
    callback_handlers.to_referral(update, context)
    return ConversationHandler.END


def to_homepage_from_referral_message(update: Update, context: CallbackContext) -> int:
    """Homepage message handler that closes the conversation.

    Args:
        update (Update)
        context (CallbackContext)

    Returns:
        int: ConversationHandler.END (-1), to signal the end of the conversation
    """
    message_handlers.homepage_handler(update, context)
    return ConversationHandler.END



################################## PERSONAL REF CODE METHODS ####################################


def to_update_personal_ref_code(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    retrieved_user_ref_code = user_manager.retrieve_user_fields_by_user_id(chat_id, ["referral_code"])["referral_code"]
    referral_text = cst.UPDATE_PERSONAL_REFERRAL_CODE_TEXT.format(retrieved_user_ref_code)
    context.bot.edit_message_text(
        referral_text,
        chat_id=chat_id, 
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.BACK_TO_REF_CODE_MENU_KEYBOARD,
        parse_mode="HTML"
    )
    return UPDATE_PERSONAL_REFERRAL


def check_referral_code_validity(new_ref_code: str) -> Union[bool, str]:
    update_status = True
    error_message = ""
    ref_code_len = len(new_ref_code)
    # * check if message is too short
    if ref_code_len < MIN_REF_CODE_LEN + 4: # 4 + -lot 
        error_message = f"Il codice di referral {new_ref_code} è troppo corto (minimo {MIN_REF_CODE_LEN} caratteri, escludendo '-lot')."
        update_status = False
    # * check if message is too long
    if ref_code_len > MAX_REF_CODE_LEN + 4: # 12 + -lot
        error_message = f"Il codice di referral {new_ref_code} è troppo lungo (massimo {MAX_REF_CODE_LEN} caratteri, escludendo '-lot')."
        update_status = False
    if re.search(r"[^\w-]", new_ref_code):
        error_message = f"Il codice di referral {new_ref_code} deve contenere solo lettere, numeri o il carattere '-'."
        update_status = False
    # * check if the new referral is valid (it's already used or not)
    referral_user = user_manager.retrieve_user_id_by_referral(new_ref_code)
    if referral_user:
        update_status = False
        error_message = f"Il codice di referral {new_ref_code} è già collegato ad un altro utente."
    return update_status, error_message


def received_personal_referral(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_user.id
    new_ref_code = update.effective_message.text.strip()
    # * add '-lot' at the end of the code if it isn't present
    if new_ref_code[-4:] != "-lot":
        new_ref_code += "-lot"
    # * check if the code is valid and get the eventual error
    update_successful, update_message = check_referral_code_validity(new_ref_code)
    if not update_successful:
        retry_text = "Prova di nuovo ad inviare un messaggio con un codice di referral oppure premi il bottone sottostante per tornare al menù Codice Referral."
        update_message += f"\n{retry_text}"
        update.effective_message.reply_text(
            update_message,
            reply_markup=kyb.BACK_TO_REF_CODE_MENU_KEYBOARD,
        )
        return UPDATE_PERSONAL_REFERRAL
    # * update user referral code
    user_manager.update_user(chat_id, {"referral_code": new_ref_code})
    #* update analtics and check checklist completion
    analytics_manager.update_analytics(chat_id, {"has_modified_referral": True})
    if analytics_manager.check_checklist_completion(chat_id):
        message_handlers.checklist_completed_handler(update, context)
    lgr.logger.debug(f"Correctly updated referral code {new_ref_code} for user {chat_id}")
    # * send success message
    message_text = f"Codice di referral aggiornato con successo in <b>{new_ref_code}</b>!\n\n"
    update.message.reply_text(
        message_text,
        parse_mode="HTML"
    )
    # * load referral menu
    callback_handlers.to_referral(update, context, send_new=True)
    return ConversationHandler.END


def update_user_ref_code_handler(update: Update, context: CallbackContext):
    """/modifica_referral <username o id> <nuovo referral>

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not message_handlers.check_user_permission(user_id, permitted_roles=["admin", "analyst"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    
    # * retrieve the data from the command text 
    command_args_len = len(context.args) 
    if command_args_len != 2:
        update.effective_message.reply_text(f"ERRORE: comando non valido, specificare username (o ID) e nuovo codice referral")
        return
    target_user_identification_data = context.args[0]
    target_user_id = None
    target_user_username = None
    try:
        target_user_id = int(target_user_identification_data)
    except:
        target_user_username = target_user_identification_data if target_user_identification_data[0] != "@" else target_user_identification_data[1:]
    
    lgr.logger.info(f"Received /modifica_referral for {target_user_identification_data}")
    new_ref_code = context.args[1]
    # * add '-lot' at the end of the code if it isn't present
    if new_ref_code[-4:] != "-lot":
        new_ref_code += "-lot"
    # * check if the received code is valid
    update_successful, update_message = check_referral_code_validity(new_ref_code)
    if not update_successful:
        update.effective_message.reply_text(f"ERRORE: codice referral non modificato.\n{update_message}")
        return
    if target_user_id:
        user_manager.update_user(target_user_id, {"referral_code": new_ref_code})
    else:
        user_manager.update_user_by_username_and_retrieve_fields(target_user_username, {"referral_code": new_ref_code})
    lgr.logger.debug(f"Correctly updated referral code {new_ref_code} for user {target_user_identification_data}")
    message_text = f"Codice di referral aggiornato con successo in <b>{new_ref_code}</b> per l'utente {target_user_identification_data}"
    update.message.reply_text(
        message_text,
        parse_mode="HTML"
    )



################################## LINKED REF CODE METHODS ####################################


def get_update_linked_referral_message(user_id: int) -> str:
    retrieved_user = user_manager.retrieve_user_fields_by_user_id(user_id, ["linked_referral_user"])
    linked_referral_id = retrieved_user["linked_referral_user"]["linked_user_id"]
    linked_referral_user_code = retrieved_user["linked_referral_user"]["linked_user_code"]
    if not linked_referral_id is None:
        referral_text = cst.EXISTING_LINKED_REFERRAL_CODE_TEXT.format(linked_referral_user_code)
    else:
        referral_text = cst.ADD_LINKED_REFERRAL_CODE_TEXT
    return referral_text


def to_update_linked_referral(update: Update, context: CallbackContext) -> int:
    chat_id = update.callback_query.message.chat_id
    message_text = get_update_linked_referral_message(chat_id)
    context.bot.edit_message_text(
        message_text,
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.BACK_TO_REF_CODE_MENU_KEYBOARD,
        parse_mode="HTML"
    )
    return UPDATE_LINKED_REFERRAL


def update_linked_referral(user_id: int, referral_text: str) -> Union[bool, str]:
    """Checks the referral code specified by the user in order to know if the 
    code exists and if it is not the current user's one. If the referral code was 
    valid, it is added to its data.

    This method is separated from the handler itself, beacuse it is used during the payment process too.
    
    Args:
        update (Update)
        _
    
    Returns:
        bool: the outcome of the procedure
        str: the message explaining the outcome of the procedure

    """
    referral_user = user_manager.retrieve_user_id_by_referral(referral_text)
    is_referral_valid = True
    message_text = ""
    retry_text = "Prova di nuovo ad inviare un messaggio con un codice di referral oppure premi il bottone sottostante per tornare al menù precedente."
    # * check if referral exists
    if not referral_user:
        lgr.logger.debug(f"Referral code {referral_text} not found")
        message_text = "Il codice di referral specificato non è collegato a nessun utente.\n" + retry_text
        is_referral_valid = False
    # * check if the referred user is not the user itself
    elif referral_user["_id"] == user_id:
        lgr.logger.debug(f"Referral code {referral_text} is the current user's one")
        message_text = "Non puoi utilizzare il tuo codice di referral.\n" + retry_text
        is_referral_valid = False
    if is_referral_valid:
        # * link referral code to user
        linked_user_data = {"linked_user_id": referral_user["_id"], "linked_user_code": referral_text}
        user_manager.update_user(user_id, {"linked_referral_user": linked_user_data})
        lgr.logger.debug(f"Correctly added referral code {referral_text} for user {user_id}")
        message_text = f"Codice di referral {referral_text} aggiunto con successo!"
    return is_referral_valid, message_text



def received_linked_referral_handler(update: Update, context: CallbackContext) -> int:
    """Checks the referral code specified by the user in order to know if the 
    code exists and if it is not the current user's one. If the referral code was 
    valid, it is added to its data.
    Finally, the user is prompted to add another code or it is sent back to the referral menu.

    This is part of a ConversationHandler regulating the update of the linked referral code.
    
    Args:
        update (Update)
        _

    Returns:
        int: either the END state for the ConversationHandler in case of success, 
            or the UPDATE_LINKED_REFERRAL state otherwise 
    """
    chat_id = update.effective_user.id
    referral_text = update.effective_message.text
    # * update linked referral
    update_successful, message_text = update_linked_referral(chat_id, referral_text) 
    # * no keyboard and end conversation if the update was successful
    if update_successful:
        keyboard_to_send = None
        state_to_return = ConversationHandler.END
    # * reload the same state and the "indetro" keyboard otherwise
    else:
        keyboard_to_send = kyb.BACK_TO_REF_CODE_MENU_KEYBOARD
        state_to_return = UPDATE_LINKED_REFERRAL
    # * send update outcome message
    update.message.reply_text(
        message_text,
        reply_markup=keyboard_to_send,
        parse_mode="HTML"
    )
    # * go back to referral menu if the update was successful
    if update_successful:
        callback_handlers.to_referral(update, context, send_new=True)
    return state_to_return

