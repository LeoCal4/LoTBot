"""Module containing all the message handlers (including the command ones)"""

import datetime
import html
import json
import os
import traceback

from telegram import ParseMode, Update, User
from telegram.ext.dispatcher import CallbackContext

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.models import sports as spr, strategies as strat
from lot_bot.dao import abbonamenti_manager, user_manager
from lot_bot import custom_exceptions

################################# HELPER METHODS #######################################


def create_first_time_user(user: User, trial_expiration_timestamp: float) -> bool:
    """Creates the user using the bot for the first time.

    Args:
        user (User)
        trial_expiration_timestamp (float)

    Returns:
        bool: True if the operation was successful, False otherwise
    """
    abbonamenti_calcio_data = {
        "telegramID": user.id,
        "sport": spr.sports_container.CALCIO.name,
        "strategia": strat.strategies_container.PIAQUEST.name,
    }
    abb_result = abbonamenti_manager.create_abbonamento(abbonamenti_calcio_data)
    if not abb_result:
        lgr.logger.error(f"Could not create abbonamento upon first message - {abbonamenti_calcio_data=}")
        return False
    abbonamenti_exchange_data = {
        "telegramID": user.id,
        "sport": spr.sports_container.EXCHANGE.name,
        "strategia": strat.strategies_container.MAXEXCHANGE.name,  
    }
    abb_result = abbonamenti_manager.create_abbonamento(abbonamenti_exchange_data)
    if not abb_result:
        lgr.logger.error(f"Could not create abbonamento upon first message - {abbonamenti_exchange_data=}")
        return False
    user_data = {
        "_id": user.id,
        "nome": user.first_name,
        "nomeUtente": user.username,
        "validoFino": trial_expiration_timestamp,
        "giocate": []
    }
    user_result = user_manager.create_user(user_data)
    if not user_result:
        lgr.logger.error(f"Could not create user upon first message - {user_data=}")
        return False
    return True


def send_message_to_all_abbonati(update: Update, context: CallbackContext, text: str, sport: str, strategy: str, is_giocata: bool = False) -> bool:
    """Sends a message to all the user subscribed to a certain sport's strategy.
    If the message is a giocata, the reply_keyboard is the one used for the giocata registration.

    Args:
        update (Update)
        context (CallbackContext)
        text (str)
        sport (str)
        strategy (str)
        is_giocata (bool, default = False): indicates if the message is a giocata or not.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    abbonamenti = abbonamenti_manager.retrieve_abbonamenti({"sport": sport, "strategia": strategy})
    if abbonamenti is None:
        lgr.logger.warning(f"No abbonamenti found for sport {sport} and strategy {strategy} while handling giocata")
        return False
    if abbonamenti == []:
        lgr.logger.warning(f"There are not abbonamenti for {sport=} {strategy=}")
    messages_sent = 0
    message_to_be_sent = len(abbonamenti)
    lgr.logger.debug(f"Found {message_to_be_sent} abbonamenti for {sport} - {strategy}")
    for abbonamento in abbonamenti:
        lgr.logger.debug(f"Checking abbonamento {abbonamento}")
        user_data = user_manager.retrieve_user(abbonamento["telegramID"])
        if not user_data:
            lgr.logger.warning(f"No user found with id {abbonamento['telegramID']} while handling giocata")
            message_to_be_sent -= 1
            continue
        lgr.logger.debug(f"Retrieved user data from id {user_data['_id']}")
        if not user_manager.check_user_validity(update.effective_message.date, user_data):
            lgr.logger.warning(f"User {user_data['_id']} is not active")
            message_to_be_sent -= 1
            continue
        lgr.logger.debug(f"Sending message to {user_data['_id']}")
        if is_giocata:
            custom_reply_markup = kyb.REGISTER_GIOCATA_KEYBOARD
            text += "\n\nHai effettuato la giocata?"
        else:
            custom_reply_markup = kyb.STARTUP_REPLY_KEYBOARD
        # TODO check blocco utenti
        result = context.bot.send_message(
            abbonamento["telegramID"], 
            text, 
            reply_markup=custom_reply_markup)
        lgr.logger.debug(f"{result}")
        messages_sent += 1
    lgr.logger.debug(f"{messages_sent} messages have been sent out of {message_to_be_sent}")
    return True


################################## COMMANDS ########################################


def start_command(update: Update, context: CallbackContext):
    """Sends the welcome message and the sports channel 
        list message, updating the Update user's situazione
        and message

    Args:
        update (Update): the Update containing the command message
        context (CallbackContext)
    """
    # the effective_message field is always present in normal messages
    # from_user gets the user which sent the message
    user_id = update.effective_user.id
    lgr.logger.debug(f"Received /start command from {user_id}")
    lista_canali_message = "Questa è la lista dei canali di cui è possibile ricevere le notifiche"
    if not user_manager.retrieve_user(user_id):
        trial_expiration_timestamp = (datetime.datetime.now() + datetime.timedelta(days=7)).timestamp()
        if not create_first_time_user(update.effective_user, trial_expiration_timestamp):
            lgr.logger.error("Could not create first time user upon /start")
            raise Exception
    # update.message.reply_text is equal to bot.send_message(update.effective_message.chat_id, ...)
    bentornato_message = "Bentornato, puoi continuare ad utilizzare il bot"
    update.message.reply_text(bentornato_message, reply_markup=kyb.STARTUP_REPLY_KEYBOARD)
    update.message.reply_text(lista_canali_message, reply_markup=kyb.create_sports_inline_keyboard(update))


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


def send_all_videos_for_file_ids(update: Update, context: CallbackContext):
    """Responds to the command `/send_all_videos` and can be used only by the developers.

    This command is used in order to upload the videos for the first time and get 
    their `file_id`, so that those can be used instead of sending the real files.

    Sends either the videos listed in `VIDEO_FILE_NAMES` (if they exist) and found in the dir `VIDEO_BASE_PATH`
    or all the videos in `VIDEO_BASE_PATH`, in case `VIDEO_FILE_NAMES` is empty.

    In addition to the videos, a message specifiying the `file_id` of each video is sent.

    Args:
        update (Update)
        context (CallbackContext)
    """
    # ! command accessible only by developers
    if not update.effective_user.id in cfg.config.DEVELOPER_CHAT_IDS:
        return
    # ! check whetever to use the whole dir or just some files of it
    if cfg.config.VIDEO_FILE_NAMES and cfg.config.VIDEO_FILE_NAMES != []:
        video_file_names = cfg.config.VIDEO_FILE_NAMES
    else:
        video_file_names = os.listdir(cfg.config.VIDEO_BASE_PATH)
    video_file_paths = [
        os.path.join(cfg.config.VIDEO_BASE_PATH, file_name) 
        for file_name in video_file_names 
        if os.path.isfile(os.path.join(cfg.config.VIDEO_BASE_PATH, file_name)) and \
            file_name.lower().endswith(cfg.config.VIDEO_FILE_EXTENSIONS)
    ]
    for video_file_path in video_file_paths:
        update.message.reply_text(f"Sending {video_file_path}")
        video_to_send = open(video_file_path, "rb")
        video_sent_update = context.bot.send_video(
            update.effective_message.chat_id,
            video_to_send
        )
        context.bot.send_message(
            update.effective_message.chat_id,
            f"Video file_id: {video_sent_update.video.file_id}",
        )


##################################### MESSAGE HANDLERS #####################################


def homepage_handler(update: Update, context: CallbackContext):
    update.message.reply_text(
        cst.HOMEPAGE_MESSAGE,
        reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
        parse_mode="HTML"
    )


def assistance_handler(update: Update, context: CallbackContext):
    pass


def community_handler(update: Update, context: CallbackContext):
    pass


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
    sport = utils.get_sport_from_giocata(text)
    if not sport:
        lgr.logger.error(f"Sport {sport=} not found")
        raise custom_exceptions.SportNotFoundError(sport, update=update)
    strategy = utils.get_strategy_from_giocata(text)
    if strategy == "":
        lgr.logger.error(f"Strategy {strategy=} not found")
        raise custom_exceptions.StrategyNotFoundError(sport, strategy, update=update)
    lgr.logger.debug(f"Received giocata {sport} - {strategy}")
    if not send_message_to_all_abbonati(update, context, text, sport, strategy, is_giocata=True):
        lgr.logger.error(f"Error with sending giocata {text} for {sport} - {strategy}")
        raise custom_exceptions.SendMessageError(text, update=update)
    lgr.logger.debug("Finished sending giocate")


def sport_channel_normal_message_handler(update: Update, context: CallbackContext):
    """Sends a message coming from one of the sports channels to
    all the users subscribed to the specified sport and strategy.
    The structure of the message must be:
    <sport> <strategy>
    <text>

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        Exception: in case the sport or the strategy do not exist or 
            if there was an error sending the messages 
    """
    text = update.effective_message.text
    first_row_tokens = text.split("\n")[0].split()
    sport = first_row_tokens[0]
    if not utils.check_sport_validity(sport):
        lgr.logger.error(f"Could not send normal message: {sport} does not exist")
        raise custom_exceptions.SportNotFoundError(sport)
    strategy = first_row_tokens[1]
    if not utils.check_sport_strategy_validity(sport, strategy):
        lgr.logger.error(f"Could not send normal message: {strategy} does not exist for {sport}")
        raise custom_exceptions.StrategyNotFoundError(sport, strategy)
    lgr.logger.debug(f"Received normal message")
    if not send_message_to_all_abbonati(update, context, text, sport, strategy):
        lgr.logger.error(f"Error with sending normal message {text} for {sport} - {strategy}")
        raise custom_exceptions.SendMessageError(text)


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
    
    # the messages are sent only if the previous operations succeeded, this is fundamental
    #   for the integration tests too
    update.message.reply_text(welcome_message, reply_markup=kyb.STARTUP_REPLY_KEYBOARD, parse_mode="html")
    update.message.reply_text(cst.WELCOME_MESSAGE_PART_TWO, parse_mode="html")


def exchange_cashout_handler(update: Update, context: CallbackContext):
    """Sends out the cashout message to all the MaxExchange subscribers.

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        Exception: when there is an error parsing the cashout or sending the messages
    """
    cashout_text = utils.create_cashout_message(update.effective_message.text)
    lgr.logger.debug(f"Received cashout message {cashout_text}")
    if cashout_text == "":
        lgr.logger.error(f"Could not parse cashout text {update.effective_message.text}")
        raise Exception(f"Could not parse cashout text {update.effective_message.text}")
    if not send_message_to_all_abbonati(
        update, 
        context, 
        cashout_text, 
        spr.sports_container.EXCHANGE.name, 
        strat.strategies_container.MAXEXCHANGE.name
    ):
        lgr.logger.error(f"Error with sending cashout {cashout_text}")
        raise custom_exceptions.SendMessageError(cashout_text)


############################################ ERROR HANDLERS ############################################


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
    base_message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
    )
    to_send = [base_message]
    escaped_tb_string = html.escape(tb_string)
    MAX_MESSAGE_LENGTH = 4000
    splits = int(max(len(escaped_tb_string) // MAX_MESSAGE_LENGTH, 1))
    for i in range(splits):
        start_index = i * MAX_MESSAGE_LENGTH
        end_index = int(min((i+1) * MAX_MESSAGE_LENGTH, len(escaped_tb_string)))
        lgr.logger.error(html.escape(tb_string[start_index:end_index]))
        to_send.append(f"<pre>{html.escape(tb_string[start_index:end_index])}</pre>")
    for dev_chat_id in cfg.config.DEVELOPER_CHAT_IDS:
        for msg in to_send:
            context.bot.send_message(chat_id=dev_chat_id, text=msg, parse_mode=ParseMode.HTML) 
    # ! send a message to the user
    try:
        if update.callback_query:
            user_chat_id = update.callback_query.message.chat_id
        elif update.message:
            user_chat_id = update.message.chat_id
        if user_chat_id:
            context.bot.send_message(
                user_chat_id,
                cst.ERROR_MESSAGE,
            )
    except Exception as e:
        lgr.logger.error(f"Could not send error message to user")
        lgr.logger.error(f"Update: {str(update)}")
        lgr.logger.error(f"Exception: {str(e)}")


# =======================================================================================000

def successful_payment_callback(update: Update, context: CallbackContext):
    # do something after successfully receiving payment?
    update.message.reply_text("Thank you for your payment!")
