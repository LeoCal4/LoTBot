"""Module containing all the message handlers"""
import datetime
from typing import List, Optional, Union, Callable, Tuple

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import custom_exceptions
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import user_manager, sport_subscriptions_manager
from lot_bot.handlers import message_handlers, callback_handlers
from lot_bot.models import personal_stakes, users, giocate, subscriptions, strategies, sports
from telegram import ParseMode, Update
from telegram.error import Unauthorized
from telegram.ext.dispatcher import CallbackContext



################################## UTILITIES ########################################


def initial_command_parsing(user_id: int, context_args: List[str], min_num_args: int, permitted_roles: List[str] = None, 
        forbidden_roles: List[str] = None, target_user_identification_data_args_index: int = 0, return_user_role: bool=False) -> Optional[Union[int, str, Tuple[int, str], Tuple[str, str]]]:
    """Parses the command, checking if the user has the permission to use it, 
    if there are enough arguments and retrieving the target user's ID or username.

    Args:
        user_id (int)
        context_args (List[str]): the list of the command's arguments
        min_num_args (int): the minimum number of command arguments needed
        permitted_roles (List[str], optional): the roles that can use the command. Defaults to None.
        forbidden_roles (List[str], optional): the roles that cannot use the command. Defaults to None.
        target_user_identification_data_args_index (int, optional): the index of the target user identification data among 
        the arguments list. If it is equal to -1, it is not search. Defaults to 1.
        return_user_role (bool): flag to make the method return the user's role. Defaults to False.

    Raises:
        custom_exceptions.UserPermissionError: in case the user does not have the permission to use the command
        custom_exceptions.CommandArgumentsError: in case there number of arguments is wrong

    Returns:
        Optional[Union[int, str]]: the target user id or username, or None if it is not needed
    """
    # * check if the user has the permission to use this command
    user_role = users.check_user_permission(user_id, permitted_roles=permitted_roles, forbidden_roles=forbidden_roles)
    if not user_role:
        raise custom_exceptions.UserPermissionError()
    # * check if there is the minimum amount of arguments required
    if len(context_args) < min_num_args:
        raise custom_exceptions.CommandArgumentsError()
    # * check whetever the specified user identification is a Telegram ID or a username
    if target_user_identification_data_args_index == -1:
        return 
    target_user_identification_data = context_args[target_user_identification_data_args_index]
    to_return = None
    try:
        target_user_id = int(target_user_identification_data)
        to_return = target_user_id
    except ValueError:
        to_return = target_user_identification_data[1:] if target_user_identification_data[0] == "@" else target_user_identification_data
    if return_user_role: 
        to_return = (to_return, user_role)
    return to_return


def first_time_user_handler(update: Update, context: CallbackContext, ref_code: str = None, teacherbet_code: str = None):
    """Sends welcome messages to the user, then creates two standard
    sport_subscriptions for her/him and creates the user itself.

    Args:
        update (Update)
    """
    user = update.effective_user
    first_time_user_data = users.create_first_time_user(update.effective_user, ref_code=ref_code, teacherbet_code=teacherbet_code)
    # * get trial sub and add date visualization offset
    user_main_sub = subscriptions.sub_container.get_subscription(first_time_user_data["subscriptions"][0]["name"])
    trial_expiration_date = datetime.datetime.utcfromtimestamp(first_time_user_data["subscriptions"][0]["expiration_date"]) + datetime.timedelta(hours=1)
    trial_expiration_date_string = trial_expiration_date.strftime("%d/%m/%Y alle %H:%M")
    # * escape chars for HTML
    parsed_first_name = user.first_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    welcome_message = cst.WELCOME_MESSAGE.format(parsed_first_name, user_main_sub.display_name, trial_expiration_date_string)
    # * check if the referral code was successfulyl added 
    if ref_code:
        if first_time_user_data["linked_referral_user"]["linked_user_id"] is None:
            welcome_message += f"\n\n{cst.NO_REFERRED_USER_FOUND_MESSAGE.format(ref_code)}"
        else:
            welcome_message += f"\n\n{cst.SUCC_REFERRED_USER_MESSAGE.format(ref_code)}"
    # * check if there was a tb code and notify user
    if teacherbet_code:
        welcome_message += f"\n\n{cst.SUCC_TEACHERBET_TRIAL_MESSAGE}"
    new_user_channel_message = cst.NEW_USER_MESSAGE.format(
        update.effective_user.id, 
        update.effective_user.first_name, 
        update.effective_user.username
    )
    try:
        context.bot.send_message(cfg.config.NEW_USERS_CHANNEL_ID, new_user_channel_message)
    except Exception as e:
        lgr.logger.error(f"Could not send new user message to relative channel {cfg.config.NEW_USERS_CHANNEL_ID=} - {e=}")
        error_message = f"Non è stato possibile inviare il messaggio di nuovo utente per {update.effective_user.id}\n{new_user_channel_message}\n{cfg.config.NEW_USERS_CHANNEL_ID=}"
        message_handlers.send_messages_to_developers(context, [error_message])
    update.message.reply_text(welcome_message, reply_markup=kyb.STARTUP_REPLY_KEYBOARD, parse_mode="HTML")


def existing_user_linking_ref_code_handler(update: Update, user_id: int, ref_code: str):
        # * connect user to used ref_code
        update_result = False
        try:
            # * check if the code is valid and connect to user
            ref_user_data = user_manager.retrieve_user_id_by_referral(ref_code)
            if ref_user_data:
                referral_user_data = {"linked_user_code": ref_code, "linked_user_id": ref_user_data["_id"]}
                update_result = user_manager.update_user(user_id, {"linked_referral_user": referral_user_data})
        except Exception as e:
            lgr.logger.error(f"Error in adding ref code to already existing user from deep linking - {str(e)}")
            update_result = False
        if update_result:
            reply_text = cst.SUCC_REFERRED_USER_MESSAGE.format(ref_code)
        else:
            reply_text = cst.NO_REFERRED_USER_FOUND_MESSAGE.format(ref_code)
        update.message.reply_text(reply_text, parse_mode="HTML")


def existing_user_activating_teacherbet_trial_handler(update: Update, user_id:int, user_subscriptions: List, teacherbet_code: str):
        # * add tb trial only if the user did not already use it or if it was not subscribed already
        already_sub_to_tb = False
        if len(user_subscriptions) > 0:
            # * check if tb is already there and do not give it trial
            for user_sub in user_subscriptions:
                if user_sub["name"] == subscriptions.sub_container.TEACHERBET.name:
                    already_sub_to_tb = True
        # * update subs with tf's one if it's not there instead
        user_data_update = {"teacherbet_code": teacherbet_code}
        if not already_sub_to_tb:
            tb_sub = subscriptions.create_teacherbet_base_sub()
            user_data_update["subscriptions"] = user_subscriptions
            user_data_update["subscriptions"].append(tb_sub)
        update_result = False
        try:
            update_result =  user_manager.update_user(user_id, user_data_update)
        except Exception as e:
            lgr.logger.error(f"Error in adding Teacherbet trial to already existing user from deep linking - {str(e)}")
            update_result = False
        if update_result:
            if already_sub_to_tb:
                reply_text = cst.ALREADY_USED_TEACHERBET_TRIAL_MESSAGE
            else:
                reply_text = cst.SUCC_TEACHERBET_TRIAL_MESSAGE
        else:
            reply_text = cst.FAILED_TEACHERBET_TRIAL_MESSAGE
        update.message.reply_text(reply_text, parse_mode="HTML")


################################## COMMANDS ########################################


def start_command(update: Update, context: CallbackContext):
    """Checks wheter the user is a first timer or not, then,
    in case it is, it creates it; otherwise, it opens the homepage with a welcome back message.

    Args:
        update (Update): the Update containing the command message
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    additional_code = None
    ref_code = None
    teacherbet_code = None
    # * check if a code has been specified
    if len(context.args) > 0:
        additional_code = context.args[0]
        if additional_code.endswith("-lot"):
            ref_code = additional_code
        elif additional_code.endswith("-teacherbet"):
            teacherbet_code = additional_code
    lgr.logger.debug(f"Received /start command from {user_id}")
    # * check if the user exists
    user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["_id", "referral_code", "teacherbet_code", "subscriptions"])
    if not user_data:
        # * the user does not exist yet
        first_time_user_handler(update, context, ref_code=ref_code, teacherbet_code=teacherbet_code)
    # * existing user wants to link a referral code
    elif ref_code and ref_code != user_data["referral_code"]:
        existing_user_linking_ref_code_handler(update, user_id, ref_code)
    # * existing user wants to activate teacherbet trial
    elif teacherbet_code and ("teacherbet_code" not in user_data or user_data["teacherbet_code"] is None):
        existing_user_activating_teacherbet_trial_handler(update, user_id, user_data["subscriptions"], teacherbet_code)
    message_handlers.homepage_handler(update, context)


def normal_message_to_abbonati_handler(update: Update, context: CallbackContext):
    """Sends a message coming from one of the sports channels to
    all the users subscribed to the specified sport and (optional) strategy.
    The structure of the message must be:
        /messaggio_abbonati <sport> - [<strategy>]
        <text>

    Args:
        update (Update)
        context (CallbackContext)
    """
    text = update.effective_message.text
    message_rows = text.split("\n")
    first_row = message_rows[0].strip()
    parsed_text = "\n".join(message_rows[1:]).strip()
    # * check message to send
    if parsed_text == "":
        update.effective_message.reply_text(f"ATTENZIONE: il messaggio non è stato inviato perchè è vuoto")
        return
    # * obtain sport and eventual strategy
    try:
        sport, strategy = utils.get_sport_and_strategy_from_normal_message(first_row)
    except custom_exceptions.NormalMessageParsingError as e:
        update.effective_message.reply_text(f"ATTENZIONE: il messaggio non è stato inviato perchè presenta un errore, si prega di controllare e rimandarlo.\nL'errore è:\n{str(e)}")
        return
    lgr.logger.debug(f"Received normal message")
    # * check if a strategy was specified
    if strategy:
        strategy_name = strategy.name
    else:
        strategy_name = "all"
    message_handlers.send_message_to_all_subscribers(update, context, parsed_text, sport.name, strategy_name)


def aggiungi_giorni(update: Update, context: CallbackContext):
    """Adds the specified number of positive days to the specified user's subscription. 
    If no subscription is specified, it is assumed to be LoT's complete one.

    The structure is:
        /aggiungi_giorni <username o ID> <days> [<subscription name>]

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    # * standard command parsing
    try:
        target_user_identification_data, user_role = initial_command_parsing(user_id, context.args, 2, permitted_roles=["admin", "analyst", "teacherbet"], return_user_role=True)
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "id (o username) e giorni di prova da aggiungere")
        return
    
    giorni_aggiuntivi = context.args[1]
    lgr.logger.debug(f"Received /aggiungi_giorni with {target_user_identification_data} and {giorni_aggiuntivi}")
    subscription_name = ""
    if len(context.args) > 2:
        subscription_name = " ".join(context.args[2:]).strip().lower()
    # * assume it's base lot sub in case no sub has been specified
    if subscription_name == "":
        subscription = subscriptions.sub_container.LOTCOMPLETE
    else:
        subscription = subscriptions.sub_container.get_subscription(subscription_name)
    # * check if the subscription exists
    if subscription is None:
        update.effective_message.reply_text(f"ERRORE: l'abbonamento {subscription_name} non esiste")
        return 
    # * check permissions on subscription
    # TODO make modular
    if subscription == subscriptions.sub_container.LOTCOMPLETE and user_role == "teacherbet":
        update.effective_message.reply_text(f"ERRORE: non hai i permessi necessari per incrementare i giorni dell'abbonamento {subscription.display_name}")
        return        


    # * check whetever the days received are actually an integer
    try:
        giorni_aggiuntivi = int(giorni_aggiuntivi)
    except Exception as e:
        lgr.logger.error(f"Tried to use {giorni_aggiuntivi} as giorni aggiuntivi - Exception type: {type(e).__name__}")
        update.effective_message.reply_text(f"ERRORE: '{giorni_aggiuntivi}' non è un numero di giorni valido")
        return
    
    # * retrieve the user's subscription expiration 
    # TODO check if there is a way to just increment it 
    if type(target_user_identification_data) is int:
        target_user_data = user_manager.retrieve_user_fields_by_user_id(target_user_identification_data, ["subscriptions"])
    else:
        target_user_data = user_manager.retrieve_user_fields_by_username(target_user_identification_data, ["_id", "subscriptions"])
    # * check if the user exists
    if target_user_data is None:
        user_not_found_message = f"ERRORE: nessun utente specificato da {target_user_identification_data} è stato trovato (ricorda: gli username sono case-sensitive)"
        update.effective_message.reply_text(user_not_found_message)
        return
    target_user_id = target_user_data["_id"] 

    # * reify user subs
    user_subs_raw = target_user_data["subscriptions"]
    user_subs_names = [sub["name"] for sub in user_subs_raw] 
    user_subs = [subscriptions.sub_container.get_subscription(sub_entry) for sub_entry in user_subs_names]
    target_sub_name = None
    for user_sub, raw_user_sub in zip(user_subs, user_subs_raw):
        # * check if sub name is valid
        if subscription == user_sub:
            # * extend the user's subscription
            raw_user_sub["expiration_date"] = users.extend_expiration_date(raw_user_sub["expiration_date"], giorni_aggiuntivi)
            target_sub_name = user_sub.display_name
            break
    # * check if user has the specified sub
    if not target_sub_name:
        update.effective_message.reply_text(f"ERRORE: impossibile aggiungere giorni, l'utente non possiede l'abbonamento specificato da {subscription_name}")
        return
    new_subscriptions = {"subscriptions": user_subs_raw}
    update_results = user_manager.update_user(target_user_id, new_subscriptions)
    if not update_results:
        update.effective_message.reply_text("ERRORE: impossibile aggiungere giorni")
        return
    # * answer the analyst with the result of the operation and notify the user
    reply_message = f"Operazione avvenuta con successo: l'utente {target_user_identification_data} ha ottenuto {giorni_aggiuntivi} giorni aggiuntivi per l'abbonamento {target_sub_name}"
    message_to_user = f"Complimenti!\nHai ricevuto {giorni_aggiuntivi} giorni aggiuntivi gratuiti per l'abbonamento {target_sub_name}!"
    context.bot.send_message(target_user_id, message_to_user)
    update.effective_message.reply_text(reply_message)


def _send_broadcast_messages(context: CallbackContext, parsed_text: str):
    """Function to be called in async in order to send a broadcast message.

    Args:
        context (CallbackContext)
        parsed_text (str)
    """
    all_user_ids = user_manager.retrieve_all_active_user_ids()
    lgr.logger.info(f"Starting to send broadcast message in async to approx. {len(all_user_ids)} users")
    for user_id in all_user_ids:
        try:
            context.bot.send_message(                
                user_id,
                parsed_text,
                parse_mode="HTML"
            )
        except Unauthorized:
            lgr.logger.info(f"User {user_id} blocked the bot")
        except Exception as e:
            lgr.logger.info(f"Error in sending message: {str(e)}")


def broadcast_handler(update: Update, context: CallbackContext):
    """ Sends a message to all the users in the db.
    /broadcast LINE BREAK <message>

    Args:
        update (Update)
        context (CallbackContext)
    """
    lgr.logger.info("Received /broadcast")
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not users.check_user_permission(user_id, permitted_roles=["admin"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    parsed_text = "\n".join(update.effective_message.text.split("\n")[1:]).strip()
    # context.dispatcher.run_async(_send_broadcast_messages, context, parsed_text) # TODO find out why it doesn't work
    _send_broadcast_messages(context, parsed_text)



def unlock_messages_to_user(update: Update, context: CallbackContext):
    """/sblocca_utente <username or ID>

    Args:
        update (Update)
        context (CallbackContext)
    """
    set_user_blocked_status(update, context, False, "⚠️ AVVISO ⚠️: sei stato riabilitato al servizio, da ora inizierai di nuovo a ricevere le giocate 🥳")


def block_messages_to_user(update: Update, context: CallbackContext):
    """/blocca_utente <username or ID>

    Args:
        update (Update)
        context (CallbackContext)
    """
    set_user_blocked_status(update, context, True, "⚠️ ATTENZIONE ⚠️: sei stato bloccato, contatta l'Assistenza! ❌")


def set_user_blocked_status(update: Update, context: CallbackContext, user_status: bool, user_message: str):
    """Modifies the blocked bool for the specified user, sending a message to it to notify the change and an ack
    message to the analyst.

    Args:
        update (Update)
        context (CallbackContext)
        user_status (bool)
        user_message (str): the message that is sent to the user, in case the operation is successful.
    """
    user_id = update.effective_user.id
    try:
        target_user_identification_data = initial_command_parsing(user_id, context.args, 1, permitted_roles=["admin", "analyst"]) 
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "username (o ID) dell'utente da bloccare o sbloccare")
        return
    user_status = {"blocked": user_status}
    # * an actual user_id was sent
    if type(target_user_identification_data) is int:
        lgr.logger.debug(f"Updating user with user_id {target_user_identification_data} with status {user_status}")
        update_result = user_manager.update_user(target_user_identification_data, user_status)
        target_user_id = target_user_identification_data
    # * a username was sent
    else:
        lgr.logger.debug(f"Updating user with username {target_user_identification_data} with status {user_status}")
        update_result = user_manager.update_user_by_username_and_retrieve_fields(target_user_identification_data, user_status)
        if update_result:
            target_user_id = update_result["_id"]
    # * check if the user exists
    if not update_result:
        reply_message = f"Nessun utente specificato da {target_user_identification_data} è stato trovato"
        return
    reply_message = f"Operazione avvenuta con successo per l'utente {target_user_identification_data}"
    update.effective_message.reply_text(reply_message)
    context.bot.send_message(target_user_id, user_message)


def set_user_role(update: Update, context: CallbackContext):
    """/cambia_ruolo <username or ID> <new role>

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    try:
        target_user_identification_data = initial_command_parsing(user_id, context.args, 2, permitted_roles=["admin"]) 
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "username (o ID) e il ruolo tra user e analyst")
        return
    
    # * retrieve the target user and role from the command text 
    role = context.args[1]
    if role not in users.ROLES and role != "admin":
        update.effective_message.reply_text(f"ERRORE: Il ruolo {role} non è valido")
        return
    lgr.logger.info(f"Received /cambia_ruolo with {target_user_identification_data} and {role}")
    user_role = {"role": role}
    
    # * an actual user_id was sent
    if type(target_user_identification_data) is int:
        target_user_id = target_user_identification_data
        lgr.logger.debug(f"Updating user with user_id {target_user_id} with role {user_role}")
        update_result = user_manager.update_user(target_user_id, user_role)
    # * a username was sent
    else:
        lgr.logger.debug(f"Updating user with username {target_user_identification_data} with role {user_role}")
        update_result = user_manager.update_user_by_username_and_retrieve_fields(target_user_identification_data, user_role)
    
    if not update_result:
        reply_message = f"Nessun utente specificato da {target_user_identification_data} è stato trovato"
        return
    reply_message = f"Operazione avvenuta con successo: l'utente {target_user_identification_data} è un {user_role['role']}"
    update.effective_message.reply_text(reply_message)


def get_trend_by_days(update: Update, context: CallbackContext):
    MAX_DAYS_FOR_TREND = 365 
    user_id = update.effective_user.id
    try:
        initial_command_parsing(user_id, context.args, 1, permitted_roles=["admin", "analyst"], target_user_identification_data_args_index=-1)
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "il numero di giorni da includere")
        return
    # * check whetever the days received are actually an integer
    try:
        days_for_trend = int(context.args[0])
    except Exception as e:
        lgr.logger.error(f"Tried to use {context.args[0]} as days for trend - Exception type: {type(e).__name__}")
        update.effective_message.reply_text(f"ERRORE: '{context.args[0]}' non è un numero di giorni valido")
        return
    # * check if the number is positive
    if days_for_trend <= 0:
        lgr.logger.error(f"Cannot use {days_for_trend} as num of giocate")
        update.effective_message.reply_text(f"ERRORE: il numero di giorni deve essere maggiore di 0")
        return
    # * clamp number of giocate to MAX_GIORNI_FOR_TREND
    days_for_trend = min(days_for_trend, MAX_DAYS_FOR_TREND)
    # * create giocate trend
    giocate_trend = giocate.get_giocate_trend_message_since_days(days_for_trend)
    update.effective_message.reply_text(giocate_trend)


def get_trend_by_events(update: Update, context: CallbackContext):
    MAX_GIOCATE_FOR_TREND = 200
    user_id = update.effective_user.id
    try:
        initial_command_parsing(user_id, context.args, 1, permitted_roles=["admin", "analyst"], target_user_identification_data_args_index=-1)
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "il numero di giocate da includere")
        return
    # * check whetever the events received are actually an integer
    try:
        events_for_trend : int = int(context.args[0])
    except Exception as e:
        lgr.logger.error(f"Tried to use {context.args[0]} as num of giocate for trend - Exception type: {type(e).__name__}")
        update.effective_message.reply_text(f"ERRORE: '{context.args[0]}' non è un numero di giocate valido")
        return
    # * check if the number is positive
    if events_for_trend <= 0:
        lgr.logger.error(f"Cannot use {events_for_trend} as num of giocate")
        update.effective_message.reply_text(f"ERRORE: il numero di giocate deve essere maggiore di 0")
        return
    # * clamp number of giocate to MAX_GIOCATE_FOR_TREND
    events_for_trend = min(events_for_trend, MAX_GIOCATE_FOR_TREND)
    # * create giocate trend
    giocate_trend = giocate.get_giocate_trend_for_lastest_n_giocate(events_for_trend)
    update.effective_message.reply_text(giocate_trend)



def get_user_resoconto(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        target_user_identification_data = initial_command_parsing(user_id, context.args, 2, permitted_roles=["admin", "analyst"])
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "lo username (o l'ID) dell'utente e il numero di giorni da includere nel resoconto")
        return
    lgr.logger.info(f"Received /get_user_resoconto {context.args[0]} {context.args[1]}")
    # * check whetever the days received are actually an integer
    try:
        days_for_resoconto = int(context.args[1])
    except Exception as e:
        lgr.logger.error(f"Tried to use {context.args[1]} as days for resoconto - Exception type: {type(e).__name__}")
        update.effective_message.reply_text(f"ERRORE: '{context.args[1]}' non è un numero di giorni valido")
        return
    # * check if the number is positive
    if days_for_resoconto <= 0:
        lgr.logger.error(f"Cannot use {days_for_resoconto} as num giorni for resoconto utente")
        update.effective_message.reply_text(f"ERRORE: il numero di giorni deve essere maggiore di 0")
        return

    # * an actual user_id was sent
    if type(target_user_identification_data) is int:
        target_user_id = target_user_identification_data
    # * a username was sent
    else:
        lgr.logger.debug(f"Creating resoconto of user with username {target_user_identification_data}")
        update_result = user_manager.retrieve_user_fields_by_username(target_user_identification_data, ["_id"])
        if not update_result:
            reply_message = f"Nessun utente specificato da {target_user_identification_data} è stato trovato"
            update.effective_message.reply_text(reply_message)
            return
        target_user_id = update_result["_id"]
    # * create resoconto
    lgr.logger.debug(f"Creating resoconto of user with user_id {target_user_id}")
    giocate_since_timestamp = (datetime.datetime.utcnow() - datetime.timedelta(days=days_for_resoconto)).timestamp()
    resoconto_message_header = f"Resoconto utente {target_user_identification_data} -  Ultimi {days_for_resoconto} giorni" # TODO add dates
    # context.dispatcher.run_async(callback_handlers._create_and_send_resoconto, context, target_user_id, giocate_since_timestamp, resoconto_message_header, edit_messages=False)
    callback_handlers._create_and_send_resoconto(context, target_user_id, giocate_since_timestamp, resoconto_message_header, edit_messages=False, receiver_user_id=user_id)
        
    
############################################ STAKE COMMANDS ############################################


def create_personal_stake(update: Update, context: CallbackContext):
    """Creates a new personal stake for the target user.
    If no sport is specified, the stake is applied to all sports.
    If no strategy is specified, the stake is applied to all the specified sport's giocate.
    
        /crea_stake <username o ID> <quota_min> <quota_max> <stake_personale> [<sport> [<strategies>]] 

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    try:
        target_user_identification_data = initial_command_parsing(user_id, context.args, 4, permitted_roles=["admin", "analyst"])
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "username (o ID), quota max, quota min, stake personale")
        return

    lgr.logger.info(f"Received /crea_stake for {target_user_identification_data}")
    
    # * parse and validate data, creating a new stake
    try:
        parsed_stake = personal_stakes.parse_personal_stake(context.args)
    except custom_exceptions.PersonalStakeParsingError as e:
        update.effective_message.reply_text(f"ATTENZIONE: la stake non è stato creato perchè presenta un errore, si prega di controllare e rimandarla.\n{str(e)}")
        return

    # * retrieve target user personal stakes 
    if type(target_user_identification_data) is int:
        target_user_data = user_manager.retrieve_user_fields_by_user_id(target_user_identification_data, ["personal_stakes"])
    else:
        target_user_data = user_manager.retrieve_user_fields_by_username(target_user_identification_data, ["_id", "personal_stakes"])
    # * check if the user exists
    if target_user_data is None:
        update.effective_message.reply_text("ERRORE: utente non trovato")
        return
    
    # * check if the new stake overlaps with any of the present ones
    if personal_stakes.check_stakes_overlapping(parsed_stake, target_user_data["personal_stakes"]):
        update.effective_message.reply_text("ERRORE: lo stake personalizzato inserito si sovrappone ad un altro già presente. Controlla gli stake dell'utente con il comando /visualizza_stake <username o ID>.")
        return

    # * add the personal stake
    target_user_id = target_user_data["_id"]
    update_result = user_manager.update_user_personal_stakes(target_user_id, parsed_stake)
    if not update_result:
        update.effective_message.reply_text("ERRORE: database non raggiungibile")

    update.effective_message.reply_text("Stake aggiunto con successo")


def visualize_personal_stakes(update: Update, context: CallbackContext):
    """Sends a message containing target user's personalized stakes.
    
        /visualizza_stake <username o ID>

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    try:    
        target_user_identification_data = initial_command_parsing(user_id, context.args, 1, permitted_roles=["analyst", "admin"])
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "username (o ID)")
        return
    # * retrieve personal stakes
    if type(target_user_identification_data) is int:
        target_user_data = user_manager.retrieve_user_fields_by_user_id(target_user_identification_data, ["personal_stakes"])
    else:
        target_user_data = user_manager.retrieve_user_fields_by_username(target_user_identification_data, ["personal_stakes"])
    # * check if the user exists
    if target_user_data is None:
        update.effective_message.reply_text("ERRORE: utente non trovato")
        return
    # * create and send personal stakes message
    stakes_message = personal_stakes.create_personal_stakes_message(target_user_data["personal_stakes"])
    stakes_message = f"STAKES PERSONALIZZATI UTENTE {target_user_identification_data}\n{stakes_message}"
    update.effective_message.reply_text(stakes_message)

def delete_personal_stakes(update: Update, context: CallbackContext):
    """Deletes target users's personalized stake identified by its index in the list of personalized stakes.

        /elimina_stake <username or ID> <index of the stake to delete>

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    try:
        target_user_identification_data = initial_command_parsing(user_id, context.args, 2, permitted_roles=["analyst", "admin"])
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "username (o ID) e l'identificatore dello stake da eliminare (specificato dal comando '/visualizza_stake')")
        return
    # * check if the personal stake to delete is actually a number
    personal_stake_to_delete = context.args[1]
    try:
        personal_stake_to_delete = int(personal_stake_to_delete.strip()) - 1
    except:
        update.effective_message.reply_text(f"ERRORE: stake non eliminato, il numero dello stake {personal_stake_to_delete+1} non è valido")
        return
    # * check if the stake number is > 0
    if personal_stake_to_delete < 0:
        update.effective_message.reply_text(f"ERRORE: stake non eliminato, il numero dello stake deve essere maggiore di 0")
        return   
    # * delete personal stakes
    try:
        deletion_result = user_manager.delete_personal_stake_by_user_id_or_username(target_user_identification_data, personal_stake_to_delete)
    except IndexError:
        update.effective_message.reply_text(f"ERRORE: stake non eliminato, il numero dello stake {personal_stake_to_delete+1} è troppo basso o troppo alto")
        return
    if not deletion_result:
        update.effective_message.reply_text("ERRORE: stake non eliminato, utente non trovato")
        return
    update.effective_message.reply_text("Stake rimosso con successo")

def visualize_user_info(update: Update, context: CallbackContext):
    """Sends a message containing target user's general data.
    
        /visualizza_utente <username o ID>

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    try:    
        target_user_identification_data = initial_command_parsing(user_id, context.args, 1, permitted_roles=["admin"])
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "username (o ID)")
        return
    # * retrieve personal info
    if type(target_user_identification_data) is int:
        target_user_data = user_manager.retrieve_user_fields_by_user_id(target_user_identification_data, ["all"])
    else:
        lgr.logger.debug("target id = "+ str(target_user_identification_data))
        target_user_data = user_manager.retrieve_user_fields_by_username(target_user_identification_data, ["all"])
    # * check if the user exists
    if target_user_data is None:#
        update.effective_message.reply_text("ERRORE: utente non trovato")
        return
    # * create and send user info message
    lgr.logger.debug(f"{target_user_data=}")

    name = target_user_data["name"]
    username = target_user_data["username"]
    if not username:
        username = ""
    telegramID = target_user_data["_id"]
    email = target_user_data["email"]
    role = target_user_data["role"]
    blocked = target_user_data["blocked"]

    user_subscriptions = target_user_data["subscriptions"]
    #sport_subscriptions = sport_subscriptions_manager.retrieve_sport_subscriptions_from_user_id(telegramID)
    sport_subscriptions = target_user_data["sport_subscriptions"]

    referral_code = target_user_data["referral_code"]
    linked_referral_user = target_user_data["linked_referral_user"]
    successful_referrals_since_last_payment = target_user_data["successful_referrals_since_last_payment"]

    user_payments = target_user_data["payments"]
    
    # = target_user_data[""]
    # = target_user_data[""]
    # = target_user_data[""]
    # = target_user_data[""]
    # = target_user_data[""]

    user_info_text = f"""<b>Informazioni Utente</b>
Nome: {name}
Username: @{username}
Id: {telegramID}
Email: {email}
Ruolo: {role}
Codice Referral: {referral_code}
L'utente risulta """
    if blocked:
        user_info_text += "bloccato\n"
    else:
        user_info_text += "non bloccato\n"

    subs_text = "<b>Abbonamenti</b>\n"
    try:
        for sub in user_subscriptions: 
            expiration_date = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(sub["expiration_date"]) + datetime.timedelta(hours=1), "%d/%m/%Y alle %H:%M")
            sub_name = subscriptions.sub_container.get_subscription(sub["name"])
            sub_emoji = "🟢" if float(sub["expiration_date"]) >= update.effective_message.date.timestamp() else "🔴"
            subs_text += f"{sub_emoji} {sub_name.display_name}: valido fino a {expiration_date}\n"
    except:
        subs_text += "ERRORE nel recupero degli abbonamenti\n"

    sports_text = "<b>Sport Attivi</b>\n"
    try:
        for sport_data in sport_subscriptions:
            sports_text += sports.sports_container.get_sport(sport_data["sport"]).display_name + ": "
            for strategy_token in sport_data["strategies"]:
                sports_text += strategies.strategies_container.get_strategy(strategy_token).display_name + ", "
            sports_text += "\n"
    except:
        sports_text += "ERRORE nel recupero degli sport e strategie\n"

    payments_text = "<b>Pagamenti</b>\n"
    try:
        if len(user_payments) != 0:
            for payment_data in user_payments:
                date = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(payment_data["datetime_timestamp"]) + datetime.timedelta(hours=2), "%d/%m/%Y alle %H:%M")
                invoice_payload = payment_data["invoice_payload"]
                price = str(payment_data["total_amount"])
                price = price[:-2]+","+price[-2:] + " " + payment_data["currency"] #e.g. 2490 -> 24,90 EUR
                payments_text += f"{date} per: {invoice_payload} - {price}\n"
        else:
            payments_text += "L'utente non ha effettuato pagamenti\n"
    except:
        payments_text += "ERRORE nel recupero dei pagamenti\n"

    other_info_text = "<b>Altro:</b>\n"
    other_info_text+= "Budget: Utilizza /visualizza_budget <ID o username>\n".replace("<", "&lt;").replace(">", "&gt;")
    other_info_text+= "Stakes personalizzati: Utilizza /visualizza_stake <ID o username>".replace("<", "&lt;").replace(">", "&gt;")

    user_info_text += subs_text + sports_text + payments_text + other_info_text

    #stakes_message = personal_stakes.create_personal_stakes_message(target_user_data["personal_stakes"])
    #stakes_message = f"STAKES PERSONALIZZATI UTENTE {target_user_identification_data}\n{stakes_message}"
    update.effective_message.reply_text(user_info_text, parse_mode="HTML")

############################################ OTHER COMMANDS ############################################

def send_file_id(update: Update, _):
    """/file_id + MEDIA

    Args:
        update (Update)
        _
    """
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not users.check_user_permission(user_id, permitted_roles=["admin"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    file_id = None
    if not update.effective_message.document is None:
        file_id = update.effective_message.document.file_id
    elif not update.effective_message.photo is None and update.effective_message.photo != []:
        file_id = update.effective_message.photo[-1].file_id
    elif not update.effective_message.video is None:
        file_id = update.effective_message.video.file_id
    if file_id is None:
        reply_message = "Impossibile ottenere il file_id dal media inviato"
    else:
        reply_message = f"{file_id}"
    update.effective_message.reply_text(reply_message)  


def _send_broadcast_media(send_media_function: Callable, file_id: str, caption: str):
    """Function to be called in async in order to send a broadcast media.

    Args:
        send_media_function (Callable)
        file_id (str)
        caption (str)
    """
    all_user_ids = user_manager.retrieve_all_active_user_ids()
    lgr.logger.info(f"Starting to send broadcast media in async to approx. {len(all_user_ids)} users")
    for user_id in all_user_ids:
        try:
            send_media_function(                
                user_id,
                file_id,
                caption=caption
            )
        except Unauthorized:
            lgr.logger.info(f"User {user_id} blocked the bot")
        except Exception as e:
            lgr.logger.info(f"Error in sending message: {str(e)}")


def broadcast_media(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not users.check_user_permission(user_id, permitted_roles=["admin"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    file_id = None
    if not update.effective_message.document is None:
        file_id = update.effective_message.document.file_id
        send_media_function = context.bot.send_document
    elif not update.effective_message.photo is None and update.effective_message.photo != []:
        file_id = update.effective_message.photo[-1].file_id
        send_media_function = context.bot.send_photo
    elif not update.effective_message.video is None:
        file_id = update.effective_message.video.file_id
        send_media_function = context.bot.send_video
    if file_id is None:
        reply_message = "Impossibile ottenere il file_id dal media inviato"
        update.effective_message.reply_text(reply_message)
        return
    caption = " ".join(update.effective_message.caption.split()[1:]).strip()
    _send_broadcast_media(send_media_function, file_id, caption)


def get_user_budget(update: Update, context: CallbackContext):
    """/visualizza_budget <ID o username>
    Args:
        update (Update): [description]
        context (CallbackContext): [description]
    """
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not users.check_user_permission(user_id, permitted_roles=["admin", "analyst"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return

    # * retrieve the data from the command text 
    command_args_len = len(context.args) 
    if command_args_len != 1:
        update.effective_message.reply_text(f"ERRORE: comando non valido, specificare username (o ID) e il budget")
        return
    target_user_identification_data = context.args[0]

    # * check whetever the specified user identification is a Telegram ID or a username
    target_user_id = None
    target_user_username = None
    try:
        target_user_id = int(target_user_identification_data)
    except ValueError:
        target_user_username = target_user_identification_data

    if not target_user_id is None:
        user_data = user_manager.retrieve_user_fields_by_user_id(target_user_id, {"budget"})
    else:
        user_data = user_manager.retrieve_user_fields_by_username(target_user_username, {"budget"})
    if not user_data:
        update.effective_message.reply_text(f"ERRORE: utente non trovato")
        return
    if user_data["budget"] is None:
        update.effective_message.reply_text(f"Il budget dell'utente non è stato impostato")
        return
    user_budget = int(user_data["budget"]) / 100
    update.effective_message.reply_text(f"Il budget dell'utente {target_user_identification_data} è {user_budget:.2f}€")


def set_user_budget(update: Update, context: CallbackContext):
    """/imposta_budget <username o ID> <new budget>
    Args:
        update (Update): [description]
        context (CallbackContext): [description]
    """
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not users.check_user_permission(user_id, permitted_roles=["admin", "analyst"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return

    # * retrieve the data from the command text 
    command_args_len = len(context.args) 
    if command_args_len != 2:
        update.effective_message.reply_text(f"ERRORE: comando non valido, specificare username (o ID) e il budget")
        return
    target_user_identification_data = context.args[0]
    user_budget = context.args[1]

    # * check whetever the specified user identification is a Telegram ID or a username
    target_user_id = None
    target_user_username = None
    try:
        target_user_id = int(target_user_identification_data)
    except ValueError:
        target_user_username = target_user_identification_data

    # * check if the budget is valid
    try:
        user_budget = utils.parse_float_string_to_int(user_budget)
    except ValueError:
        update.effective_message.reply_text(f"ERRORE: il budget specificato non è un numero valido")

    if not target_user_id is None:
        update_result = user_manager.update_user(target_user_id, {"budget": user_budget})
    else:
        update_result = user_manager.update_user_by_username_and_retrieve_fields(target_user_username, {"budget": user_budget})
    if not update_result:
        update.effective_message.reply_text(f"ERRORE: utente non trovato")
        return
    update.effective_message.reply_text(f"Budget aggiornato con successo")
