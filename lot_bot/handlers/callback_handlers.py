"""Module for the Callback Query Handlers"""
import datetime

from telegram import Update
from telegram.ext.dispatcher import CallbackContext

from lot_bot.dao import user_manager, abbonamenti_manager
from lot_bot import logger as lgr
from lot_bot import constants as cst
from lot_bot import keyboards as kyb


def select_sport_strategies(update: Update, context: CallbackContext):
    """Shows the inline keyboard containing the strategies for the
    callback's sport.
    Triggered by callback sport_<sport name>

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        Exception: raised in case the sport is not valid
    """
    sport = update.callback_query.data.replace("sport_", "")
    if not sport in cst.SPORTS:
        lgr.logger.error(f"Could not open strategies for sport {sport}")
        raise Exception
    context.bot.edit_message_text(
        f"Ecco le strategie disponibili per {sport}",
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.create_strategies_inline_keyboard(update, sport),
    )
    # must answer the callback query, even if it is useless
    context.bot.answer_callback_query(update.callback_query.id, text="")


def set_sport_strategy_state(update: Update, context: CallbackContext):
    """Sets the states of the sport's strategy to the one specified in the callback. 
    The operation is aborted in case the user is trying to set 
    a strategy to the state it is already in.

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        Exception: in case any among sport, strategy and state are invalid. 
    """
    sport, strategy, state = update.callback_query.data.split("_")
    if not sport in cst.SPORTS:
        lgr.logger.error(f"Could not set strategies for sport {sport}")
        raise Exception
    if not strategy in cst.STRATEGIES[sport]:
        lgr.logger.error(f"Could not find strategies in sport {sport}")
        raise Exception
    if state != "activate" and state != "disable":
        lgr.logger.error(f"Invalid set strategy state {state}")
        raise Exception

    # ! check if the strategy is being set to the same state it is already in
    # (that would mean that we would edit the inline keyboard with an identical one
    #   and that would cause an error)
    abb_results = abbonamenti_manager.retrieve_abbonamento_sport_strategy_from_user_id(update.effective_user.id, sport, strategy)
    if (abb_results == [] and state == "disable") or (abb_results != [] and state == "activate"):
        # we are either trying to disable an already disabled strategy or activate an already active one
        context.bot.answer_callback_query(update.callback_query.id, text="")
        return
    abbonamento_data = {
        "telegramID": update.callback_query.from_user.id,
        "sport": sport,
        "strategia": strategy
    }
    if state == "activate":
        if not abbonamenti_manager.create_abbonamento(abbonamento_data):
            lgr.logger.error(f"Could not create abbonamento with data {abbonamento_data}")
    else:
        if not abbonamenti_manager.delete_abbonamento(abbonamento_data):
            lgr.logger.error(f"Could not disable abbonamento with data {abbonamento_data}")
    context.bot.edit_message_reply_markup(
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.create_strategies_inline_keyboard(update, sport),
    )
    # must answer the callback query, even if it is useless
    context.bot.answer_callback_query(update.callback_query.id, text="")


def to_homepage(update: Update, context: CallbackContext):
    """Loads the homepage of the bot.
    The callback for this is "to_homepage".

    Args:
        update (Update)
        context (CallbackContext)
    """
    context.bot.edit_message_text(
        cst.HOMEPAGE_MESSAGE,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
        parse_mode="HTML"
    )
    # must answer the callback query, even if it is useless
    context.bot.answer_callback_query(update.callback_query.id, text="")
    

def to_sports_menu(update: Update, context: CallbackContext):
    """Loads the sports menù.
    The callback for this is "to_sports_menu".

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        Exception: in case the user cannot be found
    """
    user_id = update.effective_user.id
    user_data = user_manager.retrieve_user(user_id)
    if not user_data:
        lgr.logger.error(f"Could not find user {user_id} going back from strategies menu")
        raise Exception
    expiration_date = datetime.datetime.utcfromtimestamp(float(user_data["validoFino"])).strftime('%d/%m/%Y alle %H:%M')
    tip_text = cst.TIP_MESSAGE.format(expiration_date)
    context.bot.edit_message_text(
        tip_text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.create_sports_inline_keyboard(update)
    )
    # must answer the callback query, even if it is useless
    context.bot.answer_callback_query(update.callback_query.id, text="")


def to_links(update: Update, context: CallbackContext):
    context.bot.edit_message_text(
        "💥 Qui trovi tutti i tasti per muoverti nelle varie aree del LoTVerse ! 💥",
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.USEFUL_LINKS_INLINE_KEYBOARD,
    )
    # must answer the callback query, even if it is useless
    context.bot.answer_callback_query(update.callback_query.id, text="")

def feature_to_be_added(update: Update, context: CallbackContext):
    # must answer the callback query, even if it is useless
    context.bot.answer_callback_query(update.callback_query.id, text="")
