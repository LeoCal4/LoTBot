import datetime
import html
import json
import traceback

from telegram import ParseMode, Update
from telegram.ext.dispatcher import CallbackContext

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import abbonamenti_manager, user_manager


def start_command(update: Update, context: CallbackContext):
    """Sends the welcome message and the sports channel 
        list message, updating the Update user's situazione
        and message

    Args:
        update (Update): the Update containing the command message
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    lgr.logger.info(f"Received /start command from {user_id}")
    # the effective_message field is always present in normal messages
    # from_user gets the user which sent the message
    language_code = update.effective_user.language_code or "it"
    # update.message.reply_text is equal to bot.send_message(update.effective_message.chat_id, ...)
    bentornato_message = "Bentornato, puoi continuare ad utilizzare il bot"
    update.message.reply_text(bentornato_message, reply_markup=kyb.startup_reply_keyboard)
    lista_canali_message = "Questa è la lista dei canali di cui è possibile ricevere le notifiche"
    # ! this next line should probably be moved after the creation of the account
    sent_message = update.message.reply_text(lista_canali_message, reply_markup=kyb.create_sports_inline_keyboard(update))
    new_user_data = {
        "_id": user_id,
        "situazione": "gestioneSport", 
        "message": sent_message.to_json(),
        "lingua": language_code
    }
    if not user_manager.update_user(user_id, new_user_data):
        user_manager.create_user(new_user_data)


def reset_command(update: Update, context: CallbackContext):
    """Resets giocate, utenti and abbonamenti for the command sender,
        only if he/she is an admin

    Args:
        update (Update): the Update containing the reset command
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    lgr.logger.info(f"Received /reset command from {user_id}")
    # ! TODO check for admin rights set on the DB, not for specific ID
    if user_id != ID_MANUEL and user_id != ID_MASSI:
        return
    user_manager.delete_user(user_id)
    abbonamenti_manager.delete_abbonamenti_for_user_id(user_id)


def error_handler(update: Update, context: CallbackContext):
    """Handles all the errors coming from any other handler.
         The error is written in the logs and a message is sent
         to all the developers to notify them about it.
         (taken from: 
         https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/errorhandlerbot.py)

    Args:
        update (Update)
        context (CallbackContext)
    """
    lgr.logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    #   list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    
    for dev_chat_id in cfg.config.DEVELOPER_CHAT_IDS:
        context.bot.send_message(chat_id=dev_chat_id, text=message, parse_mode=ParseMode.HTML)        


def send_message_to_all_abbonati(update: Update, context: CallbackContext, text: str, sport: str, strategy: str) -> bool:
    abbonamenti = abbonamenti_manager.retrieve_abbonamenti_from_sport_strategy(sport, strategy)
    if not abbonamenti:
        lgr.logger.warning(f"No abbonamenti found for sport {sport} and strategy {strategy} while handling giocata")
        return False
    for abbonamento in abbonamenti:
        user_data = user_manager.retrieve_user(abbonamento["telegramID"])
        if not user_data:
            lgr.logger.warning(f"No user found with id {abbonamento['telegramID']} while handling giocata")
            continue
        lgr.logger.debug(f"Retrieved user data from id {user_data['_id']}")
        if not user_manager.check_user_validity(update.effective_message.date, user_data, update_user_state_if_expired=True):
            lgr.logger.info(f"User {user_data['_id']} is not active (1)")
            continue
        # ! this is redundant
        if not user_data["attivo"]:
            lgr.logger.info(f"User {user_data['_id']} is not active (2)")
            continue
        lgr.logger.debug(f"Sending giocata to {user_data['_id']}")
        context.bot.send_message(abbonamento["telegramID"], text, reply_markup=kyb.startup_reply_keyboard)
    return True


def giocata_handler(update: Update, context: CallbackContext):
    """Sends the received giocata to all the active user subscribed to 
    its sport and strategy.

    Args:
        update (Update)
        context (CallbackContext)
    
    Raise:
        Exception: when there is an error sending the messages
    """
    text = update.effective_message.text
    strategy = utils.get_strategy_from_giocata(text)
    sport = utils.get_sport_from_giocata(text)
    lgr.logger.debug(f"Received giocata {sport} - {strategy}")
    if not send_message_to_all_abbonati(update, context, text, sport, strategy):
        lgr.logger.error(f"Error with sending giocata {text} for {sport} - {strategy}")
        raise Exception


def first_message_handler(update: Update, context: CallbackContext):
    """Sends welcome messages to the user, then creates two standard
    abbonamenti for her/him and creates the user itself.
    In case the user already exists, the function just exits.

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        Exception: in case any of the db operation fails
    """
    user = update.effective_user
    if user_manager.retrieve_user(user.id):
        lgr.logger.warning(f"User with id {user.id} already exists, not sending welcome messages")
        return
    trial_expiration_timestamp = (datetime.datetime.now() + datetime.timedelta(days=7)).timestamp()
    trial_expiration_date = datetime.datetime.utcfromtimestamp(trial_expiration_timestamp).strftime("%d/%m/%Y alle %H:%M")
    welcome_message = cst.WELCOME_MESSAGE_PART_ONE.format(user.first_name, trial_expiration_date)
    abbonamenti_calcio_data = {
        "telegramID": user.id,
        "sport": "calcio",
        "strategia": "PiaQuest",
    }
    abb_result = abbonamenti_manager.create_abbonamenti(abbonamenti_calcio_data)
    if not abb_result:
        lgr.logger.error(f"Could not create abbonamento upon first message - {abbonamenti_calcio_data=}")
        raise Exception
    abbonamenti_exchange_data = {
        "telegramID": user.id,
        "sport": "exchange",
        "strategia": "MaxExchange",  
    }
    abb_result = abbonamenti_manager.create_abbonamenti(abbonamenti_exchange_data)
    if not abb_result:
        lgr.logger.error(f"Could not create abbonamento upon first message - {abbonamenti_exchange_data=}")
        raise Exception
    user_data = {
        "_id": user.id,
        "piano": "Sport Signals 19.90 -60%",
        "nome": user.first_name,
        "nomeUtente": user.username,
        "validoFino": trial_expiration_timestamp,
        "situazione": "domanda1",
        "attivo": 1,
        "lingua": "it",
        "primoAlert": 0
    }
    user_result = user_manager.create_user(user_data)
    if not user_result:
        lgr.logger.error(f"Could not create user upon first message - {user_data=}")
        raise Exception
    # the messages are sent only if the previous operations succeeded, this is fundamental
    #   for the integration tests too
    update.message.reply_text(welcome_message, reply_markup=kyb.startup_reply_keyboard, parse_mode="html")
    update.message.reply_text(cst.WELCOME_MESSAGE_PART_TWO, parse_mode="html")

    # ? TODO do we still need this?
#     if chat_id != idManuel:
#         temp = f"Un nuovo utente ha avviato il bot!\n\nTelegram ID: {str(chat_id)}\nNome: {str(nome)}\nUsername: @{str(nomeUtente)}"
#         bot.sendMessage(canaleNuoviUtenti, temp)


def exchange_cashout_handler(update: Update, context: CallbackContext):
    """Sends out the cashout message to all the MaxExchange subscribers.

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        Exception: when there is an error parsing the cashout or sending the messages
    """
    cashout_text = utils.create_cashout_message(update.effective_message.text)
    if cashout_text == "":
        lgr.logger.error(f"Could not parse cashout text {update.effective_message.text}")
        raise Exception
    if not send_message_to_all_abbonati(update, context, cashout_text, "exchange", "MaxExchange"):
        lgr.logger.error(f"Error with sending cashout {cashout_text}")
        raise Exception
