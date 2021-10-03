"""Module containing the handlers for the payment"""

import datetime
from typing import Optional

from lot_bot import config as cfg
from lot_bot import custom_exceptions
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import constants as cst
from lot_bot import utils
from lot_bot.dao import user_manager
from lot_bot.handlers import callback_handlers, message_handlers
from telegram import LabeledPrice, Update
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.dispatcher import CallbackContext

REFERRAL = 0


def to_add_referral_before_payment(update: Update, context: CallbackContext) -> Optional[int]:
    """Asks the user to add a new referral/affiliation code, possibily showing the one that he/she
    has already inserted previously, while presenting a button to proceed with the payment 
    or to go back.

    This is part of a ConversationHandler regulating the referral code.

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        custom_exceptions.UserNotFound: in case the user from the update is not found

    Returns:
        int: the REFERRAL state for the ConversationHandler
    """
    chat_id = update.callback_query.message.chat_id
    retrieved_user = user_manager.retrieve_user_fields_by_user_id(chat_id, ["linked_referral_code"])
    if not retrieved_user:
        lgr.logger.error(f"Could not find update user {chat_id} to get its external referral code")
        raise custom_exceptions.UserNotFound(chat_id, update=update)
        # TODO the conversation dies without exiting
    linked_referral_code = retrieved_user["linked_referral_code"]
    if linked_referral_code != "":
        referral_text = cst.PAYMENT_EXISTING_REFERRAL_CODE_TEXT.format(linked_referral_code)
    else:
        referral_text = cst.PAYMENT_ADD_REFERRAL_CODE_TEXT
    message_text = f"{cst.PAYMENT_BASE_TEXT}\n{referral_text}"
    context.bot.edit_message_text(
        message_text,
        chat_id=chat_id, 
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.PROCEED_TO_PAYMENTS_KEYBOARD,
    )
    return REFERRAL


def received_referral(update: Update, _: CallbackContext) -> int:
    """Checks the referral code specified by the user in order to know if the 
    code exists and if it is not the current user's one. If the referral code was 
    valid, it is added to its data.
    Finally, the user is prompted to add another code or to proceed to payment.

    This is part of a ConversationHandler regulating the referral code.
    
    Args:
        update (Update)
        _ (CallbackContext)

    Returns:
        int: the REFERRAL state for the ConversationHandler
    """
    chat_id = update.effective_user.id
    referral_text = update.effective_message.text
    referral_user = user_manager.retrieve_user_by_referral(referral_text)
    is_referral_valid = True
    message_text = ""
    retry_text = "Prova di nuovo ad inviare un messaggio con un codice di referral oppure premi il bottone sottostante per procedere."
    # * check if referral is not valid
    if not referral_user:
        lgr.logger.debug(f"Referral code {referral_text} not found")
        message_text = "Il codice di referral specificato non è collegato a nessun utente.\n" + retry_text
        is_referral_valid = False
    elif referral_user["_id"] == update.effective_user.id:
        lgr.logger.debug(f"Referral code {referral_text} is the current user's one")
        message_text = "Non puoi utilizzare il tuo codice di referral.\n" + retry_text
        is_referral_valid = False
    if is_referral_valid:
        # ! link referral code to user
        user_manager.update_user(chat_id, {"linked_referral_code": referral_text})
        lgr.logger.debug(f"Correctly added referral code {referral_text} for user {chat_id}")
        message_text = "Codice di referral aggiunto con successo!\nClicca il bottone sottostante per procedere al pagamento."        
    update.message.reply_text(
        message_text,
        reply_markup=kyb.PROCEED_TO_PAYMENTS_KEYBOARD,
    )
    return REFERRAL
    

def to_payments(update: Update, context: CallbackContext):
    """Sends an invoice so that the user can buy LoT's abbonamento. 
    The invoice has a timeout of 120 seconds "hardcoded" in the payload, and the price
    receives a discout that is calculated based on the user.
    Before sending the invoice, the last message sent by the bot (supposedly the 
    referral one) is deleted.

    Args:
        update (Update)
        context (CallbackContext)
    """
    INVOICE_TIMEOUT_SECONDS = 180
    chat_id = update.callback_query.message.chat_id
    title = "LoT Abbonamento Premium"
    description = "LoT Abbonamento Premium"
    # ! since there is no way to know when the invoice has been sent 
    # !     once we reach the pre-checkout, we add a timestamp to the base payload
    # !     so that we can check it during the pre-checkout
    payload = "pagamento_abbonamento_" + f"{(datetime.datetime.utcnow() + datetime.timedelta(seconds=INVOICE_TIMEOUT_SECONDS)).timestamp()}"
    currency = "EUR"
    price = 7999 # cents
    discount = user_manager.get_discount_for_user(chat_id)
    discounted_prince = price - int(price * discount) # TODO check if right
    prices = [LabeledPrice("LoT Abbonamento", discounted_prince)]

    try:
        callback_handlers.delete_message_if_possible(update, context)
    except Exception as e:
        lgr.logger.warning("Could not delete previous message before sending invoice")
        lgr.logger.warning(f"{str(e)}")
    context.bot.send_invoice(
        chat_id, title, description, payload, cfg.config.PAYMENT_TOKEN, currency, prices,
        need_email=True, need_name=True, start_parameter="Paga"
    ) # TODO add photo for abbonamento
    return ConversationHandler.END


def pre_checkout_handler(update: Update, _: CallbackContext):
    """This handler is called when the user has clicked on 
    an invoice and has inserted all the needed payment info.

    The payload of the payment is parsed to check for its timestamp, in order to 
    know if it is still valid or not.

    Args:
        update (Update)
        _ (CallbackContext)
    """
    # TODO check if the user has already payed (?)
    PAYLOAD_TIMESTAMP_INDEX = 2
    query = update.pre_checkout_query
    payload = query.invoice_payload
    payload_tokens = payload.split("_")
    payload_base = "_".join(payload_tokens[0:PAYLOAD_TIMESTAMP_INDEX])
    payload_timestamp = payload_tokens[PAYLOAD_TIMESTAMP_INDEX]
    if payload_base != "pagamento_abbonamento":
        query.answer(ok=False, error_message="Qualcosa è andato storto...")
    elif float(payload_timestamp) < datetime.datetime.utcnow().timestamp():
        query.answer(ok=False, error_message="L'invoice selezionato è scaduto. Si prega di ricominciare la procedura di pagamento dall'inizio.")
    else:
        query.answer(ok=True)


def successful_payment_callback(update: Update, context: CallbackContext):
    """Sends a final "thank you" message to the user to complete the transaction,
    then saves the user's payment and update the referred user referral count, if there
    was a referred user.

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        custom_exceptions.UserNotFound: in case the update's user is not found
    """
    user_id = update.effective_user.id
    update.message.reply_text("Grazie per aver acquistato il nostro servizio!")
    retrieved_user = user_manager.retrieve_user_fields_by_user_id(user_id, ["validoFino", "linked_referral_code"])
    if not retrieved_user:
        lgr.logger.error("Cannot retrieve user {user_id} to save its payment")
        raise custom_exceptions.UserNotFound(user_id, update=update)
    # * extend the user's subscription up to the same day of the next month
    new_expiration_date: float = utils.extend_expiration_date(retrieved_user["validoFino"])
    # * reset user successful referrals
    # * add email to user data
    user_email = update.message.successful_payment.order_info.email
    user_data = {
        "validoFino": new_expiration_date,
        "successful_referrals": 0,
        "email": user_email,
    }
    user_manager.update_user(user_id, user_data)
    # * update the referred user's successful referrals, if there is a referral code
    linked_referral_code = retrieved_user["linked_referral_code"]
    linked_user = None
    if linked_referral_code != "":
        lgr.logger.debug(f"Updating referred user {linked_referral_code} after successful payment by {user_id}")
        linked_user = user_manager.retrieve_user_by_referral(linked_referral_code)
        update_result = user_manager.update_user(linked_user["_id"], {
            "successful_referrals": int(linked_user["successful_referrals"]) + 1 # TODO change with payment infos?
        })
        if not update_result:
            lgr.logger.error(f"Could not update referred user {linked_referral_code} referral count after {user_id} payment")
    # * register the user's payment
    payment_data = update.message.successful_payment.to_dict()
    payment_data["datetime"] = datetime.datetime.utcnow().timestamp()
    referred_by_id = ""
    if linked_user:
        referred_by_id = linked_user["_id"]
    payment_data["referred_by"] = referred_by_id
    lgr.logger.debug(f"Registering payment {str(payment_data)} for {user_id}")
    register_result = user_manager.register_payment_for_user_id(payment_data, user_id)
    if not register_result:
        lgr.logger.error(f"Could not register payment {str(payment_data)} for user {user_id}")
    # * send homepage
    message_handlers.homepage_handler(update, context)


def to_homepage_from_referral_callback(update: Update, context: CallbackContext) -> int:
    """Homepage callback handler that closes the conversation.

    Args:
        update (Update)
        context (CallbackContext)

    Returns:
        int: ConversationHandler.END (-1), to signal the end of the conversation
    """
    callback_handlers.to_homepage(update, context)
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
