"""Module containing all the message handlers (including the command ones)"""

import datetime
import html
import json
import os
import traceback
from typing import Dict, List

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import custom_exceptions
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import sport_subscriptions_manager, user_manager, giocate_manager
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot.models import users as user_model
from lot_bot.models import giocate as giocata_model
from telegram import ParseMode, Update, User, user
from telegram.error import Unauthorized
from telegram.ext.dispatcher import CallbackContext

################################# HELPER METHODS #######################################


def create_first_time_user(user: User) -> Dict:
    """Creates the user using the bot for the first time.

    First, it creates the user itself, setting its expiration date to 7 days 
    from now, then creates an sport_subscription to calcio - piaquest and another
    one to exchange - maxexchange. 

    Args:
        user (User)

    Returns:
        Dict: the created user data
    """
    # * create user
    user_data = user_model.create_base_user_data()
    user_data["_id"] = user.id
    user_data["name"] = user.first_name
    user_data["username"] = user.username
    trial_expiration_timestamp = (datetime.datetime.now() + datetime.timedelta(days=7)).timestamp()
    user_data["lot_subscription_expiration"] = trial_expiration_timestamp
    user_manager.create_user(user_data)
    # * create calcio - piaquest sport_subscription
    sport_subscriptions_calcio_data = {
        "user_id": user.id,
        "sport": spr.sports_container.CALCIO.name,
        "strategy": strat.strategies_container.PIAQUEST.name,
    }
    sport_subscriptions_manager.create_sport_subscription(sport_subscriptions_calcio_data)
    # * create exchange - maxexchange sport_subscription
    sport_subscriptions_exchange_data = {
        "user_id": user.id,
        "sport": spr.sports_container.EXCHANGE.name,
        "strategy": strat.strategies_container.MAXEXCHANGE.name,  
    }
    sport_subscriptions_manager.create_sport_subscription(sport_subscriptions_exchange_data)
    return user_data


def first_time_user_handler(update: Update):
    """Sends welcome messages to the user, then creates two standard
    sport_subscriptions for her/him and creates the user itself.

    Args:
        update (Update)
    """
    user = update.effective_user
    first_time_user_data = create_first_time_user(update.effective_user)
    trial_expiration_date = datetime.datetime.utcfromtimestamp(first_time_user_data["lot_subscription_expiration"]) + datetime.timedelta(hours=2)
    trial_expiration_date_string = trial_expiration_date.strftime("%d/%m/%Y alle %H:%M")
    welcome_message = cst.WELCOME_MESSAGE_PART_ONE.format(user.first_name, trial_expiration_date_string)
    # the messages are sent only if the previous operations succeeded, this is fundamental
    #   for the integration tests too
    update.message.reply_text(welcome_message, reply_markup=kyb.STARTUP_REPLY_KEYBOARD, parse_mode="html")
    update.message.reply_text(cst.WELCOME_MESSAGE_PART_TWO, parse_mode="html")


def send_messages_to_developers(context: CallbackContext, messages_to_send: List[str], parse_mode=None):
    for dev_chat_id in cfg.config.DEVELOPER_CHAT_IDS:
        for msg in messages_to_send:
            try:
                context.bot.send_message(chat_id=dev_chat_id, text=msg, parse_mode=parse_mode)
            except Exception as e:
                lgr.logger.error(f"Could not send message {msg} to developer {dev_chat_id}")
                lgr.logger.error(f"{str(e)}") # cannot raise e since it would loop with the error handler


def send_message_to_all_abbonati(update: Update, context: CallbackContext, text: str, sport: str, strategy: str, is_giocata: bool = False):
    """Sends a message to all the user subscribed to a certain sport's strategy.
    If the message is a giocata, the reply_keyboard is the one used for the giocata registration.

    In case the number of messages sent is less than the number of abbonati, 
    a message is sent to the developers. 

    Args:
        update (Update)
        context (CallbackContext)
        text (str)
        sport (str)
        strategy (str)
        is_giocata (bool, default = False): False if it is not a giocata, True otherwise.

    """
    sub_user_ids = sport_subscriptions_manager.retrieve_all_user_ids_sub_to_sport_and_strategy(sport, strategy)
    if sub_user_ids == []:
        lgr.logger.warning(f"There are no sport_subscriptions for {sport=} {strategy=}")
        return
    messages_sent = 0
    messages_to_be_sent = len(sub_user_ids)
    lgr.logger.info(f"Found {messages_to_be_sent} sport_subscriptions for {sport} - {strategy}")
    for user_id in sub_user_ids:
        user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["lot_subscription_expiration"])
        if not user_data:
            lgr.logger.warning(f"No user found with id {user_id} while handling giocata")
            messages_to_be_sent -= 1
            continue
        if not user_manager.check_user_validity(update.effective_message.date, user_data):
            lgr.logger.warning(f"User {user_id} is not active")
            messages_to_be_sent -= 1
            continue
        lgr.logger.debug(f"Sending message to {user_id}")
        if is_giocata:
            custom_reply_markup = kyb.REGISTER_GIOCATA_KEYBOARD
            text += "\n\nHai effettuato la giocata?"
        else:
            custom_reply_markup = kyb.STARTUP_REPLY_KEYBOARD
        try:
            result = context.bot.send_message(
                user_id, 
                text, 
                reply_markup=custom_reply_markup)
            messages_sent += 1
        except Unauthorized:
            lgr.logger.warning(f"Could not send message {text}: user {user_id} blocked the bot")
            messages_to_be_sent -= 1
        except Exception as e:
            lgr.logger.error(f"Could not send message {text} to user {user_id} - {str(e)}")
    if messages_sent < messages_to_be_sent:
        error_text = f"{messages_sent} messages have been sent out of {messages_to_be_sent} for {sport} - {strategy}"
        lgr.logger.warning(error_text)
        send_messages_to_developers(context, [error_text])


################################## COMMANDS ########################################


def start_command(update: Update, _):
    """Checks wheter the user is a first timer or not, then,
    in case it is, it creates it; otherwise, it opens the canali 
    menu with a welcome back message.

    Args:
        update (Update): the Update containing the command message
        context (CallbackContext)
    """
    # the effective_message field is always present in normal messages
    # from_user gets the user which sent the message
    user_id = update.effective_user.id
    lgr.logger.debug(f"Received /start command from {user_id}")
    if not user_manager.retrieve_user_fields_by_user_id(user_id, ["_id"]):
        # * the user does not exist yet
        first_time_user_handler(update)
        return
    # update.message.reply_text is equal to bot.send_message(update.effective_message.chat_id, ...)
    update.message.reply_text(cst.BENTORNATO_MESSAGE, reply_markup=kyb.STARTUP_REPLY_KEYBOARD)
    update.message.reply_text(cst.LISTA_CANALI_MESSAGE, reply_markup=kyb.create_sports_inline_keyboard(update))


def normal_message_to_abbonati_handler(update: Update, context: CallbackContext):
    """Sends a message coming from one of the sports channels to
    all the users subscribed to the specified sport and strategy.
    The structure of the message must be:
    /messaggio_abbonati <sport> - <strategy>
    <text>

    Args:
        update (Update)
        context (CallbackContext)
        
    """
    # TODO check if author is entitled to do so
    text = update.effective_message.text
    try:
        sport, strategy = utils.get_sport_and_strategy_from_normal_message(text)
    except custom_exceptions.NormalMessageParsingError as e:
        update.effective_message.reply_text(f"ATTENZIONE: il messaggio non è stato inviato perchè presenta un errore, si prega di controllare e rimandarlo.\nL'errore è:\n{str(e)}")
        return
    lgr.logger.debug(f"Received normal message")
    # * remove first line
    parsed_text = "\n".join(text.split("\n")[1:]).strip()
    if parsed_text == "":
        update.effective_message.reply_text(f"ATTENZIONE: il messaggio non è stato inviato perchè è vuoto")
        return
    send_message_to_all_abbonati(update, context, parsed_text, sport.name, strategy.name)


def reset_command(update: Update, context: CallbackContext):
    """Resets giocate, utenti and sport_subscriptions for the command sender,
        only if he/she is an admin

    Args:
        update (Update): the Update containing the reset command
        context (CallbackContext)
    """
    # user_id = update.effective_user.id
    # lgr.logger.info(f"Received /reset command from {user_id}")
    # # ! TODO check for admin rights set on the DB, not for specific ID
    # if user_id != ID_MANUEL and user_id != ID_MASSI:
    #     return
    # user_manager.delete_user(user_id)
    # sport_subscriptions_manager.delete_sport_subscriptions_for_user_id(user_id)
    return


def send_all_videos_for_file_ids(update: Update, context: CallbackContext):
    # TODO ERASE AND DO IT DECENTLY
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

def check_user_permission(user_id: int, permitted_roles: List[str] = None, forbidden_roles: List[str] = None):
    user_role = user_manager.retrieve_user_fields_by_user_id(user_id, ["role"])["role"]
    lgr.logger.error(f"Retrieved user role: {user_role} - {permitted_roles=} - {forbidden_roles=}")
    permitted = True
    if not permitted_roles is None:
        permitted = user_role in permitted_roles
    if not forbidden_roles is None:
        permitted = not user_role in forbidden_roles 
    return permitted


#da controllare
def aggiungi_giorni(update: Update, context: CallbackContext, _):
    user_id = update.effective_user.id
    if not check_user_permission(user_id, permitted_roles=["admin"]): #aggiungere l' altro ruolo accettato, (analista o consulente)?
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    text : str = update.effective_message.text
    text_tokens = text.strip().split(" ")
    if len(text_tokens) != 3:
        update.effective_message.reply_text(f"ERRORE: comando non valido, specificare id (o @username) e giorni di prova da aggiungere")
        return
    _, target_user_id, giorni_aggiuntivi = text.strip().split(" ")
    lgr.logger.debug(f"Received /aggiungi_giorni with {target_user_id} and {giorni_aggiuntivi}")

    # * check whetever the specified user identification is a Telegram ID or a username
    try:
        target_user_id = int(target_user_id)
    except ValueError:
        lgr.logger.debug(f"{target_user_id} was a username, not a user_id")
    # * an actual user_id was sent
    if type(target_user_id) is int: 
        lgr.logger.debug(f"Updating user with user_id {target_user_id} with {giorni_aggiuntivi}")
        user_data = user_manager.retrieve_user_fields_by_user_id(target_user_id, ["lot_subscription_expiration"])["lot_subscription_expiration"]
        new_lot_subscription_expiration = {"lot_subscription_expiration":utils.extend_expiration_date(user_data,giorni_aggiuntivi)}
        update_result = user_manager.update_user(target_user_id, new_lot_subscription_expiration)
    else:
        lgr.logger.debug(f"Updating user with username {target_user_id} adding {giorni_aggiuntivi} days to its subscription expiration date")
        user_data = user_manager.retrieve_user_fields_by_username(user_id, ["lot_subscription_expiration"])["lot_subscription_expiration"]
        new_lot_subscription_expiration = {"lot_subscription_expiration":utils.extend_expiration_date(user_data,giorni_aggiuntivi)}        
        update_result = user_manager.update_user_by_username(target_user_id, giorni_aggiuntivi) #bisognerebbe utilizzare "$inc" invece di "$set"
    if update_result:
        reply_message = f"Operazione avvenuta con successo: l'utente {target_user_id} ha {giorni_aggiuntivi} giorni aggiuntivi"
        message_to_user = f"Hai ricevuto {giorni_aggiuntivi} giorni aggiuntivi gratuiti"
        if type(target_user_id) is int:
            context.bot.send_message(target_user_id,message_to_user)
        else:
            target_from_username = user_manager.retrieve_user_fields_by_username(username, ["_id"])["_id"]
            context.bot.send_message(target_from_username,message_to_user)
    else:
        reply_message = f"Nessun utente specificato da {target_user_id} è stato trovato"
    update.effective_message.reply_text(reply_message)



def set_user_role(update: Update, _):
    user_id = update.effective_user.id
    if not check_user_permission(user_id, permitted_roles=["admin"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    text : str = update.effective_message.text
    text_tokens = text.strip().split(" ")
    if len(text_tokens) != 3:
        update.effective_message.reply_text(f"ERRORE: comando non valido, specificare id o username e il ruolo ")
        return
    _, target_user_id, role = text.strip().split(" ")
    if role not in user_model.ROLES and role != "admin":
        update.effective_message.reply_text(f"ERRORE: Il ruolo {role} non è valido")
        return
    lgr.logger.debug(f"Received /set_user_role with {target_user_id} and {role}")
    user_role = {"role": role}
    # * check whetever the specified user identification is a Telegram ID or a username
    try:
        target_user_id = int(target_user_id)
    except ValueError:
        lgr.logger.debug(f"{target_user_id} was a username, not a user_id")
    # * an actual user_id was sent
    if type(target_user_id) is int:
        lgr.logger.debug(f"Updating user with user_id {target_user_id} with role {user_role}")
        update_result = user_manager.update_user(target_user_id, user_role)
    # * a username was sent
    else:
        lgr.logger.debug(f"Updating user with username {target_user_id} with role {user_role}")
        update_result = user_manager.update_user_by_username(target_user_id, user_role)
    if update_result:
        reply_message = f"Operazione avvenuta con successo: l'utente {target_user_id} è un {user_role['role']}"
    else:
        reply_message = f"Nessun utente specificato da {target_user_id} è stato trovato"
    update.effective_message.reply_text(reply_message)


def send_file_id(update: Update, _):
    user_id = update.effective_user.id
    if not check_user_permission(user_id, permitted_roles=["admin"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    file_id = None
    if not update.effective_message.document is None:
        file_id = update.effective_message.document.file_id
    elif not update.effective_message.photo is None:
    # elif hasattr(update.effective_message, "photo"):
        file_id = update.effective_message.photo[-1].file_id
    elif not update.effective_message.video is None:
    # elif hasattr(update.effective_message, "video"):
        file_id = update.effective_message.video.file_id
    if file_id is None:
        reply_message = "Impossibile ottenere il file_id dal media inviato"
    else:
        reply_message = f"{file_id}"
    update.effective_message.reply_text(reply_message)


    

##################################### MESSAGE HANDLERS #####################################


def homepage_handler(update: Update, _):
    update.message.reply_text(
        cst.HOMEPAGE_MESSAGE,
        reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
        parse_mode="HTML"
    )


def assistance_handler(update: Update, context: CallbackContext):
    pass # TODO


def community_handler(update: Update, context: CallbackContext):
    pass # TODO


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
    # * parse giocata
    try:
        parsed_giocata = utils.parse_giocata(text)
    except custom_exceptions.GiocataParsingError as e:
        update.effective_message.reply_text(f"ATTENZIONE: la giocata non è stata inviata perchè presenta un errore, si prega di controllare e rimandarla.\nL'errore è:\n{str(e)}")
        return
    # * save giocata in db
    try:
        giocate_manager.create_giocata(parsed_giocata)
    except custom_exceptions.GiocataCreationError:
        update.effective_message.reply_text(f"ATTENZIONE: la giocata non è stata inviata perchè la combinazione '#{parsed_giocata['giocata_num']}' - '{parsed_giocata['sport']}' è già stata utilizzata.")
        return
    sport = parsed_giocata["sport"]
    strategy = parsed_giocata["strategy"]
    lgr.logger.info(f"Received giocata {sport} - {strategy}")
    send_message_to_all_abbonati(update, context, text, sport, strategy, is_giocata=True)


def outcome_giocata_handler(update: Update, context: CallbackContext):
    """Sends the outcome of the giocata to all the abbonati of that
    giocata sport and strategy.

    Args:
        update (Update)
        context (CallbackContext)
    """
    text = update.effective_message.text
    try:
        sport, giocata_num, outcome = giocata_model.get_giocata_outcome_data(text)
    except custom_exceptions.GiocataOutcomeParsingError as e:
        error_message = f"ATTENZIONE: il risultato non è stato inviato perchè presenta un errore. Si prega di ricontrollare e rimandarlo."
        if e.message:
            error_message += f"\nErrore: {e.message}"
        update.effective_message.reply_text(error_message)
        return
    update_result = giocate_manager.update_giocata_outcome(sport, giocata_num, outcome)
    if not update_result:
        update.effective_message.reply_text(f"ATTENZIONE: il risultato non è stata inviato perchè la giocata non è stata trovata nel database. Si prega di ricontrollare e rimandare l'esito.")
        return
    updated_giocata = giocate_manager.retrieve_giocata_by_num_and_sport(giocata_num, sport)
    strategy = strat.strategies_container.get_strategy(updated_giocata["strategy"])
    send_message_to_all_abbonati(update, context, text, sport, strategy.name)


def exchange_cashout_handler(update: Update, context: CallbackContext):
    """Sends out the cashout message to all the MaxExchange subscribers.

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        Exception: when there is an error parsing the cashout or sending the messages
    """
    cashout_text = utils.create_cashout_message(update.effective_message.text)
    lgr.logger.info(f"Received cashout message {cashout_text}")
    send_message_to_all_abbonati(
        update, 
        context, 
        cashout_text, 
        spr.sports_container.EXCHANGE.name, 
        strat.strategies_container.MAXEXCHANGE.name
    )


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
    send_messages_to_developers(context, to_send, parse_mode=ParseMode.HTML)
    # ! send a message to the user
    try:
        user_chat_id = None
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
