"""Module containing the handlers for the payment"""

import datetime
from struct import pack
from typing import Optional

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot.dao import user_manager
from lot_bot.handlers import callback_handlers, message_handlers, ref_code_handlers
from lot_bot.models import users, subscriptions as subs
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
    # user_data = user_manager.retrieve_user_fields_by_user_id(chat_id, ["payments"])
    # # ! TODO REVERT 
    # # * check if the user has already payed
    # if user_data and "payments" in user_data and len(user_data["payments"]) > 0:
    #     context.bot.edit_message_text(
    #         "Hai già effettuato il pagamento della prevendita!",
    #         chat_id=chat_id, 
    #         message_id=update.callback_query.message.message_id,
    #     )
    #     message_handlers.homepage_handler(update, context)
    #     return ConversationHandler.END
    pack_type = update.callback_query.data.split(":")[1]
    context.user_data["pack_type"] = pack_type
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

def received_codice_during_payment(update: Update, context: CallbackContext) -> int:
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
    codice = update.effective_message.text
    message_text = ""
    error_text = "C'è stato un errore nella convalida del codice, invialo di nuovo oppure procedi al pagamento senza codice."
    used_codes = user_manager.retrieve_user_fields_by_user_id(chat_id,["used_codes","active_codes"])["used_codes"]
    active_codes = user_manager.retrieve_user_fields_by_user_id(chat_id,["used_codes","active_codes"])["active_codes"]
    update_result=True
    if not codice in used_codes:
        update_result = user_manager.update_user_active_codes(chat_id,codice,"addToSet")
        if update_result:
            message_text = "Codice valido, clicca il bottone sottostante per procedere al pagamento."
            context.user_data["active_code_to_add"] = codice
        else:
            message_text = error_text
    else:
        message_text = error_text
    update_result = user_manager.update_user_used_codes(chat_id,codice,"addToSet")
    delete_result = user_manager.update_user_active_codes(chat_id,codice,"pull")
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
    TODO UPDATE 
    Args:
        update (Update)
        context (CallbackContext)
    """
    INVOICE_TIMEOUT_SECONDS = 300
    CURRENCY = "EUR"
    chat_id = update.callback_query.message.chat_id
    context.user_data["payment_limit_timestamp"] = (datetime.datetime.utcnow() + datetime.timedelta(seconds=INVOICE_TIMEOUT_SECONDS)).timestamp()
    try:
        callback_handlers.delete_message_if_possible(update, context)
    except Exception as e:
        lgr.logger.warning(f"Could not delete previous message before sending invoice - {str(e)}")
    '''#TODO rimettere per far apparire sia l'abbonamento lot che quello di teacherbet
    for sub in subs.sub_container:
        payload = f"payment_{sub.name}"
        # price = user_manager.get_subscription_price_for_user(chat_id)
        prices = [LabeledPrice(sub.display_name, sub.price)]
        context.bot.send_invoice(
            chat_id, sub.display_name, sub.description, payload, cfg.config.PAYMENT_TOKEN, CURRENCY, prices, 
            need_email=True, need_name=True, start_parameter="Paga"
        )
    '''
    sub = subs.sub_container.get_subscription("lotcomplete")
    # price = user_manager.get_subscription_price_for_user(chat_id)
    print(f"{context.user_data=}")
    codice = None
    if "active_code_to_add" in context.user_data:
        codice = context.user_data["active_code_to_add"]
        del context.user_data["active_code_to_add"]

    durata = "30 Giorni"
    try:
        pack_type = context.user_data["pack_type"]
        payload = "payment_"+pack_type
        if pack_type == "1m":
            durata = "30 Giorni"
            price = 2490
            if codice == "ILVIAGGIOINIZIAORA":
                price = 1000
        elif pack_type == "4m":
            durata = "4 Mesi"
            price = 5990
        else:
            durata = "1 Anno"
            price = 12990
    except:
        pass
    prices = [LabeledPrice(sub.display_name, price)]
    context.bot.send_invoice(
        chat_id, f"{durata} di SportSignalsBot Premium", f"""Comprende {durata} di servizio premium ovvero:

- Tutte le analisi del team LoT su Calcio, Basket, Tennis ed Exchange ✅️

- Consulenza per personalizzazione percorso e supporto lungo termine ✅️

- Assistenza Prioritaria h24 (anche su whatsapp) ✅️""", payload, cfg.config.PAYMENT_TOKEN, CURRENCY, prices, 
        need_email=True, need_name=True, start_parameter="Paga"
    )
    extra_text = """- Analisi personalizzate in base a preferenze, orari ect. ✅️

- Accesso anticipato a nuove funzioni e servizi ✅️

- Accesso ad eventi privati, formativi e informativi ✅️"""
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
    context.user_data["payment_payload"] = payload
    if payload[:8] != "payment_" and payload != "payment_teacherbet": # TODO create method to check if valid
        query.answer(ok=False, error_message="Qualcosa è andato storto con il pagamento, contattare l'Assistenza su @teamlot")
    elif ("payment_limit_timestamp" not in context.user_data or 
        context.user_data["payment_limit_timestamp"] < datetime.datetime.utcnow().timestamp()):
        query.answer(ok=False, error_message="L'invoice selezionato è scaduto. Si prega di ricominciare la procedura di pagamento dall'inizio.")
    else:
        query.answer(ok=True)
    if "payment_limit_timestamp" in context.user_data:
        del context.user_data["payment_limit_timestamp"]


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
    payment_final_message = cst.SUCCESSFUL_PAYMENT_TEXT
    payment_outcome_text = "Pagamento effettuato con successo" # This string is part of the text that will be sent to new payments channel
    user_id = update.effective_user.id
    retrieved_user = user_manager.retrieve_user_fields_by_user_id(user_id, ["subscriptions", "linked_referral_user"])
    retrieved_user_subs = retrieved_user["subscriptions"]
    user_subs_name = [entry["name"] for entry in retrieved_user_subs]
    # new_expiration_date =  datetime.datetime(2021, 12, 2, hour=23, minute=59).timestamp() # TODO REVERT
    sub_name = "lotcomplete" #"_".join(context.user_data["payment_payload"].split("_")[1:])
    # * extend the user's subscription up to the same day of the next month
    days = 30
    pack_type = "_".join(context.user_data["payment_payload"].split("_")[1:])
    if pack_type == "1m":
        days = 30
    elif pack_type == "4m":
        days = 120
    elif pack_type == "1a":
        days = 365
    if sub_name not in user_subs_name:
        new_expiration_date = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).timestamp()
        retrieved_user_subs.append({"name": sub_name, "expiration_date": new_expiration_date})
    else:
        base_exp_date = [entry["expiration_date"] for entry in retrieved_user_subs if entry["name"] == sub_name][0]
        # base_exp_date = retrieved_user_subs[sub_name]["expiration_date"]

        new_expiration_date: float = users.extend_expiration_date(base_exp_date, days)
        for sub_entry in retrieved_user_subs:
            if sub_entry["name"] == sub_name:
                sub_entry["expiration_date"] = new_expiration_date
                break
    # * add email to user data
    user_email = update.message.successful_payment.order_info.email
    user_data = {
        "subscriptions": retrieved_user_subs,
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
        refs_update_result = user_manager.update_user_referred_payments(linked_referral_id, payment_data["payment_id"])
        if not refs_update_result:
            refs_error_message = f"ERRORE PAGAMENTO: non è stato possibile aggiungere il pagamento {payment_data['payment_id']} dell'utente {user_id} all'utente referral {linked_referral_id}"
            message_handlers.send_messages_to_developers(context, [refs_error_message])
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
        payment_final_message += f"Si prega di contattarci su @teamlot e di riportare il seguente codice: {payment_data['payment_id']}"
        dev_message = "ERRORE: pagamento non registrato per l'utente {user_id}.\n"
        dev_message += f"Update dati utente: {user_update_result=} - registrazione pagamento: {register_result=}\n"
        dev_message += f"Dati pagamento:\n {str(payment_data)}"
        message_handlers.send_messages_to_developers(context, [dev_message])
        payment_outcome_text = "Pagamento effettuato con successo, ma non è stato possibile registrarlo correttamente."
    # # * update the referred user's successful referrals, if there is a referral code
    # if linked_referral_id is not None:
    #     try:
    #         update_result = user_manager.update_user_succ_referrals(linked_referral_id, payment_data["payment_id"])
    #     except:
    #         # this gets both db errors and other issues related to missing users
    #         update_result = False
    #     # * handle referral errors
    #     if not update_result:
    #         lgr.logger.error(f"Could not update referred user {linked_referral_id} referral count after {user_id} payment")
    #         payment_final_message = f"ERRORE: il pagamento è stato effettuato correttamente, ma non siamo riusciti a registrarlo per l'affiliazione.\n"
    #         payment_final_message += f"Si prega di contattare l'assistenza e di riportare il seguente codice: {payment_data['payment_id']}"
    #         dev_message = f"ERRORE: referral non registrato per l'utente {user_id} verso l'utente {linked_referral_id}. Dati pagamento:\n"
    #         dev_message += f"{str(payment_data)}"
    #         message_handlers.send_messages_to_developers(context, [dev_message])
    #         payment_outcome_text = "Pagamento effettuato con successo, ma non è stato possibile registrarlo correttamente per l'affiliazione."
    # * send final payment message and homepage
    del context.user_data["payment_payload"]
    update.message.reply_text(payment_final_message, parse_mode="HTML")
    message_handlers.homepage_handler(update, context)

    price = str(payment_data["total_amount"])
    price = price[:-2]+","+price[-2:] + " " + payment_data["currency"]

    new_expiration_date_text = datetime.datetime.strftime( datetime.datetime.utcfromtimestamp(new_expiration_date) + datetime.timedelta(hours=1), "%d/%m/%Y alle %H:%M")
    new_payment_channel_message = cst.NEW_PAYMENT_CHANNEL_MESSAGE.format(
        update.effective_user.id, 
        update.effective_user.first_name, 
        update.effective_user.username,
        sub_name,
        new_expiration_date_text,
        price
    )
    new_payment_channel_message += payment_outcome_text
    try:
        context.bot.send_message(cfg.config.NEW_PAYMENTS_CHANNEL_ID, new_payment_channel_message)
    except Exception as e:
        lgr.logger.error(f"Could not send new payment message to relative channel {cfg.config.NEW_PAYMENTS_CHANNEL_ID=} - {e=}")
        error_message = f"Non è stato possibile inviare il messaggio di nuovo PAGAMENTO per {update.effective_user.id}\n{new_payment_channel_message}\n{cfg.config.NEW_PAYMENTS_CHANNEL_ID=}"
        message_handlers.send_messages_to_developers(context, [error_message])


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
    