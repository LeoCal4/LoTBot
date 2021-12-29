"""Module containing all the message handlers"""

import html
import json
import traceback
from typing import List

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import custom_exceptions
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import (giocate_manager, sport_subscriptions_manager,
                         user_manager)
from lot_bot.models import giocate as giocata_model
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot.models import users
from telegram import ParseMode, Update
from telegram.error import Unauthorized
from telegram.ext.dispatcher import CallbackContext

################################# HELPER METHODS #######################################


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
    # * check if the strategy is all, hence the message has to be sent to all sub to the specified sport
    if strategy != "all":
        sub_user_ids = sport_subscriptions_manager.retrieve_all_user_ids_sub_to_sport_and_strategy(sport, strategy)
    else: 
        sub_user_ids = sport_subscriptions_manager.retrieve_all_user_ids_sub_to_sport(sport)
    # * check if there are any subscribers to the specified strategy
    if sub_user_ids == []:
        lgr.logger.warning(f"There are no sport_subscriptions for {sport=} {strategy=}")
        return
    messages_sent = 0
    messages_to_be_sent = len(sub_user_ids)
    lgr.logger.info(f"Found {messages_to_be_sent} sport_subscriptions for {sport} - {strategy}")
    # * eventually add giocata text at the end of the message
    if is_giocata:
        original_text += "\n\nSeguirai questo evento?"
    for user_id in sub_user_ids:
        user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["subscriptions", "personal_stakes", "blocked", "budget"])
        # * check if the user actually exists
        if not user_data:
            lgr.logger.warning(f"No user found with id {user_id} while handling giocata")
            messages_to_be_sent -= 1
            continue
        # * check if the user is blocked
        if user_data["blocked"]:
            lgr.logger.warning(f"User {user_id} is blocked")
            messages_to_be_sent -= 1
            continue
        # * check if the user has an active subscription for the given sport
        if not user_manager.check_user_sport_subscription(update.effective_message.date, user_data["subscriptions"], sport):
            lgr.logger.warning(f"User {user_id} is not active or does not have access to said sport")
            messages_to_be_sent -= 1
            continue
        lgr.logger.debug(f"Sending message to {user_id}")
        # * in case of giocata message, add the register giocata keyboard and personalize the stake
        if is_giocata:
            custom_reply_markup = kyb.REGISTER_GIOCATA_KEYBOARD
            if "personal_stakes" in user_data:
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


##################################### MESSAGE HANDLERS #####################################


def homepage_handler(update: Update, context: CallbackContext):
    try:
        update.message.reply_text(
            cst.HOMEPAGE_MESSAGE,
            reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
            parse_mode="HTML"
        )
    except AttributeError: # * this happens when the homepage handler is called by a method with no "message" field in the update
        context.bot.send_message(
            update.effective_user.id,
            cst.HOMEPAGE_MESSAGE,
            reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
            parse_mode="HTML"
        )


def bot_configuration_handler(update: Update, _: CallbackContext):
    update.message.reply_text(
        cst.BOT_CONFIG_MENU_MESSAGE,
        reply_markup=kyb.BOT_CONFIGURATION_INLINE_KEYBOARD,
        parse_mode="HTML"
    )


def experience_settings_handler(update: Update, _: CallbackContext):
    update.message.reply_text(
        cst.EXPERIENCE_MENU_MESSAGE,
        reply_markup=kyb.EXPERIENCE_MENU_INLINE_KEYBOARD,
        parse_mode="HTML"
    )

def use_guide_handler(update: Update, _: CallbackContext):
    update.message.reply_text(
        cst.USE_GUIDE_MENU_MESSAGE,
        reply_markup=kyb.USE_GUIDE_MENU_KEYBOARD,
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


def teacherbet_giocata_handler(update: Update, context: CallbackContext):
    text = update.effective_message.text
    parsed_giocate = giocata_model.parse_teacherbet_giocata(text, add_month_year_to_raw_text=True)
    for parsed_giocata in parsed_giocate:
        # TODO OPTIMIZATION: only one access to the db to store them
        try:
            giocate_manager.create_giocata(parsed_giocata)
        except custom_exceptions.GiocataCreationError:
            update.effective_message.reply_text(f"ATTENZIONE: la giocata non è stata inviata perchè la combinazione '#{parsed_giocata['giocata_num']}' - '{parsed_giocata['sport']}' è già stata utilizzata.")
            return
        send_message_to_all_subscribers(update, context, parsed_giocata["raw_text"], spr.sports_container.TEACHERBET.name, strat.strategies_container.TEACHERBETLUXURY.name, is_giocata=True)


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
        error_message = f"ATTENZIONE: il risultato non è stato inviato perchè presenta un errore. Si prega di ricontrollare e rimandarlo.\nErrore: {str(e)}"
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


def teacherbet_giocata_outcome_handler(update: Update, context: CallbackContext):
    text = update.effective_message.text
    try:
        giocata_num, outcome = giocata_model.get_teacherbet_giocata_outcome_data(text)
    except custom_exceptions.GiocataOutcomeParsingError as e:
        error_message = f"ATTENZIONE: il risultato non è stato inviato perchè presenta un errore. Si prega di ricontrollare e rimandarlo.\nErrore: {str(e)}"
        update.effective_message.reply_text(error_message)
        return
    sport = spr.sports_container.TEACHERBET.name
    update_result = giocate_manager.update_giocata_outcome(sport, giocata_num, outcome)
    if not update_result:
        # * the giocata may be from previous month, check that first 
        giocata_num = giocata_num[:-5] + f"{utils.get_month_and_year_string(previous_month=True)}"
        update_result = giocate_manager.update_giocata_outcome(sport, giocata_num, outcome)
        if not update_result:
            update.effective_message.reply_text(f"ATTENZIONE: il risultato non è stata inviato perchè la giocata non è stata trovata nel database. Si prega di ricontrollare e rimandare l'esito.")
            return
    updated_giocata = giocate_manager.retrieve_giocata_by_num_and_sport(giocata_num, sport)
    strategy = strat.strategies_container.get_strategy(updated_giocata["strategy"])
    send_message_to_all_subscribers(update, context, text, sport, strategy.name)



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
        return
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
    # users.update_users_budget_with_giocata(updated_giocata)


def unrecognized_message(update: Update, _):
    lgr.logger.info(f"Unrecognized message: {update.effective_message}")


############################################ ERROR HANDLER ############################################


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
