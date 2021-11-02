"""Module containing all the message handlers"""
import datetime
from typing import List, Optional, Union

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import custom_exceptions
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import user_manager
from lot_bot.handlers import message_handlers
from lot_bot.models import personal_stakes, users, giocate
from telegram import ParseMode, Update
from telegram.error import Unauthorized
from telegram.ext.dispatcher import CallbackContext



################################## UTILITIES ########################################


def initial_command_parsing(user_id: int, context_args: List[str], min_num_args: int, permitted_roles: List[str] = None, 
        forbidden_roles: List[str] = None, target_user_identification_data_args_index: int = 0) -> Optional[Union[int, str]]:
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

    Raises:
        custom_exceptions.UserPermissionError: in case the user does not have the permission to use the command
        custom_exceptions.CommandArgumentsError: in case there number of arguments is wrong

    Returns:
        Optional[Union[int, str]]: the target user id or username, or None if it is not needed
    """
    # * check if the user has the permission to use this command
    if not users.check_user_permission(user_id, permitted_roles=permitted_roles, forbidden_roles=forbidden_roles):
        raise custom_exceptions.UserPermissionError()
    # * check if there is the minimum amount of arguments required
    if len(context_args) < min_num_args:
        raise custom_exceptions.CommandArgumentsError()
    # * check whetever the specified user identification is a Telegram ID or a username
    if target_user_identification_data_args_index == -1:
        return 
    target_user_identification_data = context_args[target_user_identification_data_args_index]
    try:
        target_user_id = int(target_user_identification_data)
        return target_user_id
    except ValueError:
        return target_user_identification_data[1:] if target_user_identification_data[0] == "@" else target_user_identification_data


def first_time_user_handler(update: Update, context: CallbackContext, ref_code: str):
    """Sends welcome messages to the user, then creates two standard
    sport_subscriptions for her/him and creates the user itself.

    Args:
        update (Update)
    """
    user = update.effective_user
    first_time_user_data = users.create_first_time_user(update.effective_user, ref_code)
    trial_expiration_date = datetime.datetime.utcfromtimestamp(first_time_user_data["lot_subscription_expiration"]) + datetime.timedelta(hours=1)
    trial_expiration_date_string = trial_expiration_date.strftime("%d/%m/%Y alle %H:%M")
    # * escape chars for HTML
    parsed_first_name = user.first_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    welcome_message = cst.WELCOME_MESSAGE.format(parsed_first_name, trial_expiration_date_string)
    # * check if the referral code was successfulyl added 
    if ref_code:
        if first_time_user_data["linked_referral_user"]["linked_user_id"] is None:
            welcome_message += cst.NO_REFERRED_USER_FOUND_MESSAGE.format(ref_code)
        else:
            welcome_message += cst.SUCC_REFERRED_USER_MESSAGE.format(ref_code)
    # the messages are sent only if the previous operations succeeded, this is fundamental
    #   for the integration tests too
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



################################## COMMANDS ########################################


def start_command(update: Update, context: CallbackContext):
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
    ref_code = None
    if len(context.args) > 0:
        ref_code = context.args[1]
    lgr.logger.debug(f"Received /start command from {user_id}")
    user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["_id", "referral_code"])
    if ref_code and ref_code == user_data["referral_code"]:
        lgr.logger.info("User attempted to /start with its own ref_code")
        ref_code = None
    if not user_data:
        # * the user does not exist yet
        first_time_user_handler(update, context, ref_code)
    elif ref_code:
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
    message_handlers.homepage_handler(update, context)


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
    message_handlers.send_message_to_all_abbonati(update, context, parsed_text, sport.name, strategy.name)


def aggiungi_giorni(update: Update, context: CallbackContext):
    """Adds the specified number of positive days to the specified user's LoT subscription. 
    The structure is:
        /aggiungi_giorni <username o ID> <days>
    

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    # * standard command parsing
    try:
        target_user_identification_data = initial_command_parsing(user_id, context.args, 2, permitted_roles=["admin", "analyst"])
    except custom_exceptions.UserPermissionError as e:
        update.effective_message.reply_text(str(e))
        return
    except custom_exceptions.CommandArgumentsError as e:
        update.effective_message.reply_text(str(e) + "id (o username) e giorni di prova da aggiungere")
        return
    
    giorni_aggiuntivi = context.args[1]
    lgr.logger.debug(f"Received /aggiungi_giorni with {target_user_identification_data} and {giorni_aggiuntivi}")

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
        target_user_data = user_manager.retrieve_user_fields_by_user_id(target_user_identification_data, ["lot_subscription_expiration"])
    else:
        target_user_data = user_manager.retrieve_user_fields_by_username(target_user_identification_data, ["_id", "lot_subscription_expiration"])
    # * check if the user exists
    if target_user_data is None:
        user_not_found_message = f"ERRORE: nessun utente specificato da {target_user_identification_data} è stato trovato (ricorda: gli username sono case-sensitive)"
        update.effective_message.reply_text(user_not_found_message)
        return
    # * extend the user's subscription
    target_user_id = target_user_data["_id"] 
    user_expiration_timestamp = target_user_data["lot_subscription_expiration"]
    new_lot_subscription_expiration = {"lot_subscription_expiration": users.extend_expiration_date(user_expiration_timestamp, giorni_aggiuntivi)}
    update_results = user_manager.update_user(target_user_id, new_lot_subscription_expiration)
    if not update_results:
        update.effective_message.reply_text("ERRORE: impossibile aggiungere giorni")
        return
    # * answer the analyst with the result of the operation and notify the user
    reply_message = f"Operazione avvenuta con successo: l'utente {target_user_identification_data} ha ottenuto {giorni_aggiuntivi} giorni aggiuntivi"
    message_to_user = f"Complimenti!\nHai ricevuto {giorni_aggiuntivi} giorni aggiuntivi gratuiti!"
    context.bot.send_message(target_user_id, message_to_user)
    update.effective_message.reply_text(reply_message)


def _send_broadcast_messages(context: CallbackContext, parsed_text: str):
    """Function to be called in async in order to send a broadcast message.

    Args:
        context (CallbackContext)
        parsed_text (str)
    """
    all_user_ids = user_manager.retrieve_all_user_ids()
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
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not users.check_user_permission(user_id, permitted_roles=["admin"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    parsed_text = "\n".join(update.effective_message.text.split("\n")[1:]).strip()
    context.dispatcher.run_async(_send_broadcast_messages, context, parsed_text)


def unlock_messages_to_user(update: Update, context: CallbackContext):
    """/sblocca_utente <username or ID>

    Args:
        update (Update): [description]
        context (CallbackContext): [description]
    """
    set_user_blocked_status(update, context, False, "⚠️ AVVISO ⚠️: sei stato riabilitato al servizio, da ora inizierai di nuovo a ricevere le giocate 🥳")


def block_messages_to_user(update: Update, context: CallbackContext):
    """/blocca_utente <username or ID>

    Args:
        update (Update): [description]
        context (CallbackContext): [description]
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


def get_trend(update: Update, context: CallbackContext):
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
    # * create giocate trend
    giocate_trend = giocate.get_giocate_trend_since_days(days_for_trend)
    update.effective_message.reply_text(giocate_trend)


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
    target_user_identification_data = initial_command_parsing(user_id, context.args, 4, permitted_roles=["admin", "analyst"])

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



############################################ OTHER COMMANDS ############################################

def send_file_id(update: Update, _):
    """/send_file_id + MEDIA

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
    elif not update.effective_message.photo is None:
        file_id = update.effective_message.photo[-1].file_id
    elif not update.effective_message.video is None:
        file_id = update.effective_message.video.file_id
    if file_id is None:
        reply_message = "Impossibile ottenere il file_id dal media inviato"
    else:
        reply_message = f"{file_id}"
    update.effective_message.reply_text(reply_message)  
