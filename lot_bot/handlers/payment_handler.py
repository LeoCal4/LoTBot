"""Module containing the handlers for the payment"""

import datetime
from typing import Optional

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot.dao import user_manager
from lot_bot.handlers import callback_handlers, message_handlers, ref_code_handlers
from lot_bot.models import users
from telegram import LabeledPrice, Update
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.dispatcher import CallbackContext

REFERRAL = 0


def to_add_linked_referral_before_payment(update: Update, context: CallbackContext) -> Optional[int]:
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
    user_data = user_manager.retrieve_user_fields_by_user_id(chat_id, ["payments"])
    # ! TODO REVERT 
    # * check if the user has already payed
    if user_data and "payments" in user_data and len(user_data["payments"]) > 0:
        context.bot.edit_message_text(
            "Hai già effettuato il pagamento della prevendita!",
            chat_id=chat_id, 
            message_id=update.callback_query.message.message_id,
        )
        message_handlers.homepage_handler(update, context)
        return ConversationHandler.END
    referral_text = ref_code_handlers.get_update_linked_referral_message(chat_id)
    message_text = f"{cst.PAYMENT_BASE_TEXT}\n{referral_text}"
    context.bot.edit_message_text(
        message_text,
        chat_id=chat_id, 
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.PROCEED_TO_PAYMENTS_KEYBOARD,
        parse_mode="HTML"
    )
    return REFERRAL


def received_linked_referral_during_payment(update: Update, _) -> int:
    """Checks the referral code specified by the user in order to know if the 
    code exists and if it is not the current user's one. If the referral code was 
    valid, it is added to its data.
    Finally, the user is prompted to add another code or to proceed to payment.

    This is part of a ConversationHandler regulating the referral code.
    
    Args:
        update (Update)
        _

    Returns:
        int: the REFERRAL state for the ConversationHandler
    """
    chat_id = update.effective_user.id
    referral_text = update.effective_message.text
    update_successful, message_text = ref_code_handlers.received_linked_referral_handler(chat_id, referral_text)
    if update_successful:
        message_text += "\nClicca il bottone sottostante per procedere al pagamento."
    # * send update outcome message
    update.message.reply_text(
        message_text,
        reply_markup=kyb.PROCEED_TO_PAYMENTS_KEYBOARD,
        parse_mode="HTML"
    )
    return REFERRAL
    

def to_payments(update: Update, context: CallbackContext):
    """Sends an invoice so that the user can buy LoT's sport_subscription. 
    The invoice has a timeout of 120 seconds "hardcoded" in the payload, and the price
    receives a discout that is calculated based on the user.
    Before sending the invoice, the last message sent by the bot (supposedly the 
    referral one) is deleted.

    Args:
        update (Update)
        context (CallbackContext)
    """
    INVOICE_TIMEOUT_SECONDS = 300
    chat_id = update.callback_query.message.chat_id
    title = "LoT Abbonamento TEST TITLE"
    description = "LoT Abbonamento TEST DESCRIPTION"
    context.user_data["payment_limit_timestamp"] = (datetime.datetime.utcnow() + datetime.timedelta(seconds=INVOICE_TIMEOUT_SECONDS)).timestamp()
    payload = "pagamento_sport_subscription"
    currency = "EUR"
    
    # price = user_manager.get_subscription_price_for_user(chat_id)
    price = 500
    prices = [LabeledPrice("LoT Abbonamento", price)]

    try:
        callback_handlers.delete_message_if_possible(update, context)
    except Exception as e:
        lgr.logger.warning(f"Could not delete previous message before sending invoice - {str(e)}")
    context.bot.send_invoice(
        chat_id, title, description, payload, cfg.config.PAYMENT_TOKEN, currency, prices,
        need_email=True, need_name=True, start_parameter="Paga"
    )
    return ConversationHandler.END


def pre_checkout_handler(update: Update, context: CallbackContext):
    """This handler is called when the user has clicked on 
    an invoice and has inserted all the needed payment info.

    The payload of the payment is parsed to check for its timestamp, in order to 
    know if it is still valid or not.

    Args:
        update (Update)
        context (CallbackContext)
    """
    query = update.pre_checkout_query
    payload = query.invoice_payload
    if payload != "pagamento_sport_subscription":
        query.answer(ok=False, error_message="Qualcosa è andato storto con il pagamento, contattare l'Assistenza")
    elif ("payment_limit_timestamp" not in context.user_data or 
        context.user_data["payment_limit_timestamp"] < datetime.datetime.utcnow().timestamp()):
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
    payment_final_message = f"Grazie per aver acquistato il nostro servizio!"
    user_id = update.effective_user.id
    retrieved_user = user_manager.retrieve_user_fields_by_user_id(user_id, ["lot_subscription_expiration", "linked_referral_user"])
    # * extend the user's subscription up to the same day of the next month
    new_expiration_date =  datetime.datetime(2021, 12, 2, hour=22, minute=59).timestamp() # ! TODO REVERT (22 and not 23 because we're at +1)
    # new_expiration_date: float = users.extend_expiration_date(retrieved_user["lot_subscription_expiration"], 30)
    # * reset user successful referrals
    # * add email to user data
    user_email = update.message.successful_payment.order_info.email
    user_data = {
        "lot_subscription_expiration": new_expiration_date,
        "successful_referrals_since_last_payment": [],
        "email": user_email,
    }
    try:
        user_update_result = user_manager.update_user(user_id, user_data)
    except:
        user_update_result = False
    if not user_update_result:
        lgr.logger.error(f"Could not update data after payment for user {user_id} - {user_data=}")
    payment_data = update.message.successful_payment.to_dict()
    payment_data["datetime_timestamp"] = datetime.datetime.utcnow().timestamp()
    payment_data["payment_id"] = str(user_id) + "-" + str(payment_data["datetime_timestamp"])
    # * get linked referral user
    linked_referral_id = retrieved_user["linked_referral_user"]["linked_user_id"]
    if not linked_referral_id is None:
        lgr.logger.debug(f"Updating referred user {linked_referral_id} after successful payment by {user_id}")
        payment_data["referred_by"] = linked_referral_id
    # * registering payment
    lgr.logger.debug(f"Registering payment {str(payment_data)} for {user_id}")
    try:
        register_result = user_manager.register_payment_for_user_id(payment_data, user_id)
    except:
        # this gets both db errors and other issues related to missing users
        register_result = False
    # * handle data registration errors
    if not register_result or not user_update_result:
        lgr.logger.error(f"Could not register payment {str(payment_data)} for user {user_id}")
        payment_final_message = f"ERRORE: il pagamento è stato effettuato con successo, ma non siamo riusciti a registrarlo correttamente.\n"
        payment_final_message += f"Si prega di contattare l'assistenza e di riportare il seguente codice: {payment_data['payment_id']}"
        dev_message = "ERRORE: pagamento non registrato per l'utente {user_id}.\n"
        dev_message += f"Update dati utente: {user_update_result=} - registrazione pagamento: {register_result=}\n"
        dev_message += f"Dati pagamento:\n {str(payment_data)}"
        message_handlers.send_messages_to_developers(context, [dev_message])
    # * update the referred user's successful referrals, if there is a referral code
    if linked_referral_id is not None:
        try:
            update_result = user_manager.update_user_succ_referrals(linked_referral_id, payment_data["payment_id"])
        except:
            # this gets both db errors and other issues related to missing users
            update_result = False
        # * handle referral errors
        if not update_result:
            lgr.logger.error(f"Could not update referred user {linked_referral_id} referral count after {user_id} payment")
            payment_final_message = f"ERRORE: il pagamento è stato effettuato correttamente, ma non siamo riusciti a registrarlo per l'affiliazione.\n"
            payment_final_message += f"Si prega di contattare l'assistenza e di riportare il seguente codice: {payment_data['payment_id']}"
            dev_message = f"ERRORE: referral non registrato per l'utente {user_id} verso l'utente {linked_referral_id}. Dati pagamento:\n"
            dev_message += f"{str(payment_data)}"
            message_handlers.send_messages_to_developers(context, [dev_message])
    # * send final payment message and homepage
    update.message.reply_text(payment_final_message)
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

