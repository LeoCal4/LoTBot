"""Module containing all the message handlers (including the command ones)"""

import datetime
import html
import json
import traceback
from typing import Callable, Dict, List, Union

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import custom_exceptions
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import (giocate_manager, sport_subscriptions_manager,
                         user_manager)
from lot_bot.models import giocate as giocata_model
from lot_bot.models import personal_stakes
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot.models import users
from telegram import ParseMode, Update, User
from telegram.error import Unauthorized
from telegram.ext.dispatcher import CallbackContext

################################# HELPER METHODS #######################################


def create_first_time_user(user: User, ref_code: str) -> Dict:
    """Creates the user using the bot for the first time.
    First, it creates the user itself, setting its expiration date to 7 days 
    from now, then creates an sport_subscription to calcio - raddoppio and multipla and another
    one to exchange - maxexchange. 

    Args:
        user (User)

    Returns:
        Dict: the created user data
    """
    # * create user
    user_data = users.create_base_user_data()
    user_data["_id"] = user.id
    user_data["name"] = user.first_name
    user_data["username"] = user.username
    if ref_code:
        ref_user_data = user_manager.retrieve_user_id_by_referral(ref_code)
        if ref_user_data:
            user_data["linked_referral_user"] = {
                "linked_user_code": ref_code,
                "linked_user_id": ref_user_data["_id"]
            }
    else:
        lgr.logger.warning(f"Upon creating a new user, {ref_code=} was not valid")
    # ! TODO REVERT
    # trial_expiration_timestamp = (datetime.datetime.now() + datetime.timedelta(days=7)).timestamp()
    trial_expiration_timestamp = datetime.datetime(2021, 10, 31, hour=13, minute=15).timestamp()
    user_data["lot_subscription_expiration"] = trial_expiration_timestamp
    user_manager.create_user(user_data)
    # * create calcio -  sport_subscription
    sport_subscriptions_calcio_raddoppio_data = {
        "user_id": user.id,
        "sport": spr.sports_container.CALCIO.name,
        "strategy": strat.strategies_container.RADDOPPIO.name,
    }
    sub_creation_result = False
    try:
        sub_creation_result = sport_subscriptions_manager.create_sport_subscription(sport_subscriptions_calcio_raddoppio_data)
    except Exception as e:
        lgr.logger.error(f"Could not create subscription {sport_subscriptions_calcio_raddoppio_data} for new user {user_data['_id']} - {str(e)}")
    sport_subscriptions_calcio_multiple_data = {
        "user_id": user.id,
        "sport": spr.sports_container.CALCIO.name,
        "strategy": strat.strategies_container.MULTIPLA.name,
    }
    try:
        sub_creation_result = sub_creation_result and sport_subscriptions_manager.create_sport_subscription(sport_subscriptions_calcio_multiple_data)
    except Exception as e:
        lgr.logger.error(f"Could not create subscription {sport_subscriptions_calcio_multiple_data} for new user {user_data['_id']} - {str(e)}")
    # * create exchange - maxexchange sport_subscription
    sport_subscriptions_exchange_data = {
        "user_id": user.id,
        "sport": spr.sports_container.EXCHANGE.name,
        "strategy": strat.strategies_container.MAXEXCHANGE.name,  
    }
    try:
        sub_creation_result = sub_creation_result and sport_subscriptions_manager.create_sport_subscription(sport_subscriptions_exchange_data)
    except Exception as e:
        lgr.logger.error(f"Could not create subscription {sport_subscriptions_exchange_data} for new user {user_data['_id']} - {str(e)}")
    if not sub_creation_result:
        # send_messages_to_developers(context, [error_message]) # TODO decide if this is the right approach or not
        pass
    return user_data


def first_time_user_handler(update: Update, context: CallbackContext, ref_code: str):
    """Sends welcome messages to the user, then creates two standard
    sport_subscriptions for her/him and creates the user itself.

    Args:
        update (Update)
    """
    user = update.effective_user
    first_time_user_data = create_first_time_user(update.effective_user, ref_code)
    trial_expiration_date = datetime.datetime.utcfromtimestamp(first_time_user_data["lot_subscription_expiration"]) + datetime.timedelta(hours=2)
    trial_expiration_date_string = trial_expiration_date.strftime("%d/%m/%Y alle %H:%M")
    # escape chars for HTML
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
        send_messages_to_developers(context, [error_message])
    update.message.reply_text(welcome_message, reply_markup=kyb.STARTUP_REPLY_KEYBOARD, parse_mode="HTML")


def send_messages_to_developers(context: CallbackContext, messages_to_send: List[str], parse_mode=None):
    for dev_chat_id in cfg.config.DEVELOPER_CHAT_IDS:
        for msg in messages_to_send:
            try:
                context.bot.send_message(chat_id=dev_chat_id, text=msg, parse_mode=parse_mode)
            except Exception as e:
                lgr.logger.error(f"Could not send message {msg} to developer {dev_chat_id}")
                lgr.logger.error(f"{str(e)}") # cannot raise e since it would loop with the error handler


def send_message_to_all_subscribers(update: Update, context: CallbackContext, original_text: str, sport: str, strategy: str, 
                                        is_giocata: bool = False):
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
    text = original_text
    sub_user_ids = sport_subscriptions_manager.retrieve_all_user_ids_sub_to_sport_and_strategy(sport, strategy)
    # * check if there are any subscribers to the specified strategy
    if sub_user_ids == []:
        lgr.logger.warning(f"There are no sport_subscriptions for {sport=} {strategy=}")
        return
    messages_sent = 0
    messages_to_be_sent = len(sub_user_ids)
    lgr.logger.info(f"Found {messages_to_be_sent} sport_subscriptions for {sport} - {strategy}")
    # * eventually add giocata text at the end of the message
    if is_giocata:
        original_text += "\n\nHai effettuato la giocata?"
    for user_id in sub_user_ids:
        user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["lot_subscription_expiration", "personal_stakes", "budget"])
        # * check if the user actually exists
        if not user_data:
            lgr.logger.warning(f"No user found with id {user_id} while handling giocata")
            messages_to_be_sent -= 1
            continue
        # * check if the user has an active subscription
        if not user_manager.check_user_validity(update.effective_message.date, user_data):
            lgr.logger.warning(f"User {user_id} is not active")
            messages_to_be_sent -= 1
            continue
        lgr.logger.debug(f"Sending message to {user_id}")
        # * in case of giocata message, add the register giocata keyboard and personalize the stake
        if is_giocata:
            custom_reply_markup = kyb.REGISTER_GIOCATA_KEYBOARD
            text = giocata_model.personalize_giocata_text(original_text, user_data["personal_stakes"], sport, strategy)
            user_budget = user_data["budget"]
            if not user_budget is None:
                user_budget = int(user_budget)
                text = giocata_model.update_giocata_text_with_stake_money_value(text, user_budget)
        # * otherwise, keep the original text and resend the base keyboard
        else:
            custom_reply_markup = kyb.STARTUP_REPLY_KEYBOARD
            text = original_text
        try:
            context.bot.send_message(
                user_id, 
                text, 
                reply_markup=custom_reply_markup)
            messages_sent += 1
        # * check if the user has blocked the bot
        except Unauthorized:
            lgr.logger.warning(f"Could not send message: user {user_id} blocked the bot")
            messages_to_be_sent -= 1
        except Exception as e:
            lgr.logger.error(f"Could not send message {text} to user {user_id} - {str(e)}")
    if messages_sent < messages_to_be_sent:
        error_text = f"{messages_sent} messages have been sent out of {messages_to_be_sent} for {sport} - {strategy}"
        lgr.logger.warning(error_text)
        send_messages_to_developers(context, [error_text])


def check_user_permission(user_id: int, permitted_roles: List[str] = None, forbidden_roles: List[str] = None):
    user_role = user_manager.retrieve_user_fields_by_user_id(user_id, ["role"])["role"]
    lgr.logger.error(f"Retrieved user role: {user_role} - {permitted_roles=} - {forbidden_roles=}")
    permitted = True
    if not permitted_roles is None:
        permitted = user_role in permitted_roles
    if not forbidden_roles is None:
        permitted = not user_role in forbidden_roles 
    return permitted


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
    message_tokens = update.effective_message.text.split()
    ref_code = None
    if len(message_tokens) > 1:
        ref_code = message_tokens[1]
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
    homepage_handler(update, context)


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
    send_message_to_all_subscribers(update, context, parsed_text, sport.name, strategy.name)


def aggiungi_giorni(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not check_user_permission(user_id, permitted_roles=["admin", "analyst"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    
    # * retrieve the target user and additional days from the command text 
    text : str = update.effective_message.text
    text_tokens = text.strip().split(" ")
    if len(text_tokens) != 3:
        update.effective_message.reply_text(f"ERRORE: comando non valido, specificare id (o username) e giorni di prova da aggiungere")
        return
    _, target_user_identification_data, giorni_aggiuntivi = text.strip().split(" ")
    lgr.logger.debug(f"Received /aggiungi_giorni with {target_user_identification_data} and {giorni_aggiuntivi}")
    
    # * check whetever the days received are actually an integer
    try:
        giorni_aggiuntivi = int(giorni_aggiuntivi)
    except Exception as e:
        lgr.logger.error(f"Tried to use {giorni_aggiuntivi} as giorni aggiuntivi - Exception type: {type(e).__name__}")
        update.effective_message.reply_text(f"ERRORE: '{giorni_aggiuntivi}' non è un numero di giorni valido")
        return
    
    # * check whetever the specified user identification is a Telegram ID or a username
    target_user_id = None
    target_user_username = None
    try:
        target_user_id = int(target_user_identification_data)
    except ValueError:
        lgr.logger.debug(f"{target_user_identification_data} was a username, not a user_id")
        # remove @ if it is present
        target_user_username = target_user_identification_data[1:] if target_user_identification_data[0] == "@" else target_user_identification_data
    
    user_not_found_message = f"ERRORE: nessun utente specificato da {target_user_identification_data} è stato trovato (ricorda che gli username sono case-sensitive)"
    def _update_user_exp_date(user_retrieve_function: Callable, expiration_update_function: Callable, user_identification: Union[int, str]):
        lgr.logger.info(f"Updating user identified by {user_identification} with {giorni_aggiuntivi} days to its subscription expiration date")
        target_user_data = user_retrieve_function(user_identification, ["lot_subscription_expiration"])
        if target_user_data is None:
            raise custom_exceptions.UserNotFound()
        user_expiration_timestamp = target_user_data["lot_subscription_expiration"]
        new_lot_subscription_expiration = {"lot_subscription_expiration": users.extend_expiration_date(user_expiration_timestamp, giorni_aggiuntivi)}
        expiration_update_function(target_user_id, new_lot_subscription_expiration)
        return target_user_data["_id"]

    try:
        # * an actual user_id was sent
        if not target_user_id is None:
            _update_user_exp_date(
                user_manager.retrieve_user_fields_by_user_id, 
                user_manager.update_user, 
                target_user_id
            )
        # * a username was sent
        else:
            target_user_id = _update_user_exp_date(
                user_manager.retrieve_user_fields_by_username, 
                user_manager.update_user_by_username, 
                target_user_username
            )
    except custom_exceptions.UserNotFound:
        update.effective_message.reply_text(user_not_found_message)
        return
    # * answer the analyst with the result of the operation
    reply_message = f"Operazione avvenuta con successo: l'utente {target_user_identification_data} ha ottenuto {giorni_aggiuntivi} giorni aggiuntivi"
    message_to_user = f"Complimenti!\nHai ricevuto {giorni_aggiuntivi} giorni aggiuntivi gratuiti!"
    context.bot.send_message(target_user_id, message_to_user)
    update.effective_message.reply_text(reply_message)


def _send_broadcast_messages(context, parsed_text):
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
    """/broadcast LINE BREAK <message>

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not check_user_permission(user_id, permitted_roles=["admin"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    parsed_text = "\n".join(update.effective_message.text.split("\n")[1:]).strip()
    context.dispatcher.run_async(_send_broadcast_messages, context, parsed_text)


def create_personal_stake(update: Update, context: CallbackContext):
    """- /crea_stake <username o ID> <quota_min> <quota_max> <stake_personale> [<sport> <strategia> (se non specificate va applicato su tutte)] 

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not check_user_permission(user_id, permitted_roles=["admin", "analyst"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    
    # * retrieve the data from the command text 
    command_args_len = len(context.args) 
    if command_args_len < 4:
        update.effective_message.reply_text(f"ERRORE: comando non valido, specificare username (o ID), quota max, quota min, stake personale")
        return
    target_user_identification_data = context.args[0]
    target_user_id = None
    target_user_username = None
    try:
        target_user_id = int(target_user_identification_data)
    except:
        target_user_username = target_user_identification_data if target_user_identification_data[0] != "@" else target_user_identification_data[1:]
    
    lgr.logger.info(f"Received /crea_stake for {target_user_identification_data}")
    
    # * parse and validate data, creating a new stake
    try:
        parsed_stake = personal_stakes.parse_personal_stake(context.args)
    except custom_exceptions.PersonalStakeParsingError as e:
        update.effective_message.reply_text(f"ATTENZIONE: la stake non è stato creato perchè presenta un errore, si prega di controllare e rimandarla.\n{str(e)}")
        return

    # * retrieve target user personal stakes 
    if target_user_id:
        target_user_data = user_manager.retrieve_user_fields_by_user_id(target_user_id, ["personal_stakes"])
    else:
        target_user_data = user_manager.retrieve_user_fields_by_username(target_user_username, ["personal_stakes"])

    if target_user_data is None:
        update.effective_message.reply_text("ERRORE: utente non trovato")
        return
    
    # * (setting target user id, in case we only had the username)
    target_user_id = target_user_data["_id"]

    # * check if the new stake overlaps with any of the present ones
    if personal_stakes.check_stakes_overlapping(parsed_stake, target_user_data["personal_stakes"]):
        update.effective_message.reply_text("ERRORE: lo stake personalizzato inserito si sovrappone ad un altro già presente. Controlla gli stake dell'utente con il comando /visualizza_stake <username o ID>.")
        return

    # * add the personal stake
    update_result = user_manager.update_user_personal_stakes(target_user_id, parsed_stake)
    if not update_result:
        update.effective_message.reply_text("ERRORE: database non raggiungibile")

    update.effective_message.reply_text("Stake aggiunto con successo")


def visualize_personal_stakes(update: Update, context: CallbackContext):
    """/visualizza_stake <username o ID>

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    if not check_user_permission(user_id, permitted_roles=["analyst", "admin"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    # * retrieve the data from the command text 
    command_args_len = len(context.args) 
    if command_args_len != 1:
        update.effective_message.reply_text(f"ERRORE: comando non valido, specificare username (o ID)")
        return
    target_user_identification_data = context.args[0]
    target_user_id = None
    target_user_username = None
    try:
        target_user_id = int(target_user_identification_data)
    except:
        target_user_username = target_user_identification_data if target_user_identification_data[0] != "@" else target_user_identification_data[1:]
    
    # * retrieve personal stakes
    if target_user_id:
        target_user_data = user_manager.retrieve_user_fields_by_user_id(target_user_id, ["personal_stakes"])
    else:
        target_user_data = user_manager.retrieve_user_fields_by_username(target_user_username, ["personal_stakes"])

    if target_user_data is None:
        update.effective_message.reply_text("ERRORE: utente non trovato")
        return
    
    # * (setting target user id, in case we only had the username)
    target_user_id = target_user_data["_id"]

    # * create and send personal stakes message
    stakes_message = personal_stakes.create_personal_stakes_message(target_user_data["personal_stakes"])
    stakes_message = f"STAKES PERSONALIZZATI UTENTE {target_user_identification_data}\n{stakes_message}"
    update.effective_message.reply_text(stakes_message)


def delete_personal_stakes(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not check_user_permission(user_id, permitted_roles=["analyst", "admin"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    # * retrieve the data from the command text 
    command_args_len = len(context.args) 
    if command_args_len != 2:
        update.effective_message.reply_text(f"ERRORE: comando non valido, specificare username (o ID) e l'identificatore dello stake da eliminare (specificato dal comando '/visualizza_stake')")
        return
    target_user_identification_data = context.args[0]
    personal_stake_to_delete = context.args[1]
    # * check if the personal stake to delete is actually a number
    try:
        personal_stake_to_delete = int(personal_stake_to_delete.strip()) - 1
    except:
        update.effective_message.reply_text(f"ERRORE: stake non eliminato, il numero dello stake {personal_stake_to_delete} non è valido")
        return
    # * check if the stake number is > 0
    if personal_stake_to_delete < 0:
        update.effective_message.reply_text(f"ERRORE: stake non eliminato, il numero dello stake deve essere maggiore di 0")
        return
    target_user = None
    try:
        target_user = int(target_user_identification_data)
    except:
        target_user = target_user_identification_data if target_user_identification_data[0] != "@" else target_user_identification_data[1:]
    
    # * delete personal stakes
    try:
        deletion_result = user_manager.delete_personal_stake_by_user_id_or_username(target_user, personal_stake_to_delete)
    except IndexError:
        update.effective_message.reply_text(f"ERRORE: stake non eliminato, il numero dello stake {personal_stake_to_delete} è troppo basso o troppo alto")
        return
    if not deletion_result:
        update.effective_message.reply_text("ERRORE: stake non eliminato, utente non trovato")
        return
    update.effective_message.reply_text("Stake rimosso con successo")
    


def set_user_role(update: Update, context: CallbackContext):
    """/cambia_ruolo <username or ID> <new role>

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not check_user_permission(user_id, permitted_roles=["admin"]):
        update.effective_message.reply_text("ERRORE: non disponi dei permessi necessari ad utilizzare questo comando")
        return
    if len(context.args) != 2:
        update.effective_message.reply_text(f"ERRORE: comando non valido, specificare id o username e il ruolo ")
        return
    
    # * retrieve the target user and role from the command text 
    target_user_identification_data, role = context.args
    if role not in users.ROLES and role != "admin":
        update.effective_message.reply_text(f"ERRORE: Il ruolo {role} non è valido")
        return
    lgr.logger.info(f"Received /cambia_ruolo with {target_user_identification_data} and {role}")
    user_role = {"role": role}
    
    # * check whetever the specified user identification is a Telegram ID or a username
    target_user_id = None
    target_user_username = None
    try:
        target_user_id = int(target_user_identification_data)
    except ValueError:
        target_user_username = target_user_identification_data
    
    # * an actual user_id was sent
    if target_user_id is not None:
        lgr.logger.debug(f"Updating user with user_id {target_user_id} with role {user_role}")
        update_result = user_manager.update_user(target_user_id, user_role)
    # * a username was sent
    else:
        lgr.logger.debug(f"Updating user with username {target_user_username} with role {user_role}")
        update_result = user_manager.update_user_by_username(target_user_username, user_role)
    
    if update_result:
        reply_message = f"Operazione avvenuta con successo: l'utente {target_user_identification_data} è un {user_role['role']}"
    else:
        reply_message = f"Nessun utente specificato da {target_user_identification_data} è stato trovato"
    update.effective_message.reply_text(reply_message)


def send_file_id(update: Update, _):
    """/send_file_id + MEDIA

    Args:
        update (Update)
        _
    """
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not check_user_permission(user_id, permitted_roles=["admin"]):
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


def get_user_budget(update: Update, context: CallbackContext):
    """/visualizza_budget <ID o username>

    Args:
        update (Update): [description]
        context (CallbackContext): [description]
    """
    user_id = update.effective_user.id
    # * check if the user has the permission to use this command
    if not check_user_permission(user_id, permitted_roles=["admin", "analyst"]):
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
    if not check_user_permission(user_id, permitted_roles=["admin", "analyst"]):
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
        update_result = user_manager.update_user_by_username(target_user_username, {"budget": user_budget})
    if not update_result:
        update.effective_message.reply_text(f"ERRORE: utente non trovato")
        return
    update.effective_message.reply_text(f"Budget aggiornato con successo")
    

    

##################################### MESSAGE HANDLERS #####################################


def homepage_handler(update: Update, _):
    update.message.reply_text(
        cst.HOMEPAGE_MESSAGE,
        reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
        parse_mode="HTML"
    )


def bot_configuration_handler(update: Update, _: CallbackContext):
    update.message.reply_text(
        cst.HOMEPAGE_MESSAGE,
        reply_markup=kyb.BOT_CONFIGURATION_INLINE_KEYBOARD,
        parse_mode="HTML"
    )


def experience_settings_handler(update: Update, _: CallbackContext):
    update.message.reply_text(
        cst.HOMEPAGE_MESSAGE,
        reply_markup=kyb.EXPERIENCE_MENU_INLINE_KEYBOARD,
        parse_mode="HTML"
    )


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
        parsed_giocata = giocata_model.parse_giocata(text)
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
    send_message_to_all_subscribers(update, context, text, sport, strategy, is_giocata=True)


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
        error_message += f"\nErrore: {e.message}"
        update.effective_message.reply_text(error_message)
        return
    updated_giocata = giocate_manager.update_giocata_outcome_and_get_giocata(sport, giocata_num, outcome)
    if not updated_giocata:
        update.effective_message.reply_text(f"ATTENZIONE: il risultato non è stato inviato perchè la giocata non è stata trovata nel database. Si prega di ricontrollare e rimandare l'esito.")
        return
    # strategy = strat.strategies_container.get_strategy(updated_giocata["strategy"])
    # * send outcome
    send_giocata_outcome(context, updated_giocata["_id"],  text)
    # send_message_to_all_subscribers(update, context, text, giocata_num, sport, strategy.name)#, is_outcome=True, outcome_data={"giocata_num": giocata_num, "outcome": outcome})
    # * update the budget of all the user's who accepted the giocata
    users.update_users_budget_with_giocata(updated_giocata)


def send_giocata_outcome(context: CallbackContext, giocata_id: str, outcome_text: str):
    giocata = giocate_manager.retrieve_giocate_from_ids([giocata_id])[0]
    target_users_data = user_manager.retrieve_users_who_played_giocata(giocata_id)
    for user_data in target_users_data:
        outcome_text_to_send = outcome_text
        user_id = user_data["_id"]
        user_budget = user_data["budget"]
        if not user_budget is None:
            user_personal_stake = int(user_data["giocate"]["personal_stake"])
            if user_personal_stake:
                stake = user_personal_stake
            else:
                stake = giocata["base_stake"]
            outcome_text_to_send = giocata_model.update_outcome_text_with_money_value(outcome_text_to_send, user_budget, stake, giocata["base_quota"], giocata["outcome"])
        try:
            context.bot.send_message(
                user_id, 
                outcome_text_to_send)
        # * check if the user has blocked the bot
        except Unauthorized:
            lgr.logger.warning(f"Could not send message: user {user_id} blocked the bot")
        except Exception as e:
            lgr.logger.error(f"Could not send message {outcome_text} to user {user_id} - {str(e)}")


def exchange_cashout_handler(update: Update, context: CallbackContext):
    """Sends out the cashout message to all the MaxExchange subscribers.

    Args:
        update (Update)
        context (CallbackContext)
    """
    cashout_text_raw = update.effective_message.text
    # * get giocata num and cashout
    try:
        giocata_num, cashout_percentage = giocata_model.get_cashout_data(cashout_text_raw)
    except custom_exceptions.GiocataParsingError as e:
        update.effective_message.reply_text(f"ATTENZIONE: il cashout non è stato inviato.{str(e)}")
        return
    # * update the giocata outcome
    updated_giocata = giocate_manager.update_exchange_giocata_outcome_and_get_giocata(giocata_num, cashout_percentage)
    if not updated_giocata:
        update.effective_message.reply_text(f"ATTENZIONE: il cashout non è stato inviato. La giocata {giocata_num} non è stata trovata")
    # * create parsed cashout message
    cashout_text = utils.create_cashout_message(cashout_text_raw)
    lgr.logger.info(f"Received cashout message {cashout_text}")
    send_message_to_all_subscribers(
        update, 
        context, 
        cashout_text, 
        spr.sports_container.EXCHANGE.name, 
        strat.strategies_container.MAXEXCHANGE.name
    )
    # * update the budget of all the user's who accepted the giocata
    users.update_users_budget_with_giocata(updated_giocata)


def unrecognized_message(update: Update, _):
    lgr.logger.info(f"Unrecognized message: {update.effective_message}")


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
                parse_mode="HTML"
            )
    except Exception as e:
        lgr.logger.error(f"Could not send error message to user")
        lgr.logger.error(f"Update: {str(update)}")
        lgr.logger.error(f"Exception: {str(e)}")
