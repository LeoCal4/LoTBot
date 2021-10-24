from typing import Union

from lot_bot import constants as cst
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import user_manager
from lot_bot.handlers import callback_handlers, message_handlers
from telegram import Update
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.dispatcher import CallbackContext


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


def received_personal_referral(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_user.id
    new_referral_text = update.effective_message.text.strip()
    # * add '-lot' at the end of the code if it isn't present
    if new_referral_text[-4:] != "-lot":
        new_referral_text += "-lot"
    ref_code_len = len(new_referral_text)
    retry_text = "Prova di nuovo ad inviare un messaggio con un codice di referral oppure premi il bottone sottostante per tornare al menù Codice Referral."
    # * check if message is too short
    if ref_code_len < 8: # 4 + -lot 
        update.effective_message.reply_text(
            f"Il codice di referral {new_referral_text} è troppo corto.\n{retry_text}",
            reply_markup=kyb.BACK_TO_REF_CODE_MENU_KEYBOARD,
            )
        return UPDATE_PERSONAL_REFERRAL
    # * check if message is too long
    if ref_code_len > 16: # 12 + -lot
        update.effective_message.reply_text(
            f"Il codice di referral {new_referral_text} è troppo lungo.\n{retry_text}",
            reply_markup=kyb.BACK_TO_REF_CODE_MENU_KEYBOARD,
            )
        return UPDATE_PERSONAL_REFERRAL
    # * check if the new referral is valid (it's already used or not)
    referral_user = user_manager.retrieve_user_id_by_referral(new_referral_text)
    if referral_user:
        lgr.logger.debug(f"Referral code {new_referral_text} already present")
        update.effective_message.reply_text(
            f"Il codice di referral {new_referral_text} è già collegato ad un altro utente.\n{retry_text}",
            reply_markup=kyb.BACK_TO_REF_CODE_MENU_KEYBOARD,
            )
        return UPDATE_PERSONAL_REFERRAL
    # * update user referral code
    user_manager.update_user(chat_id, {"referral_code": new_referral_text})
    lgr.logger.debug(f"Correctly updated referral code {new_referral_text} for user {chat_id}")
    # * send success message
    message_text = f"Codice di referral aggiornato con successo in <b>{new_referral_text}</b>!\n\n"
    update.message.reply_text(
        message_text,
        parse_mode="HTML"
    )
    # * load referral menu
    callback_handlers.to_referral(update, context, send_new=True)
    return ConversationHandler.END



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

