"""Module for the Callback Query Handlers"""
import datetime
from time import time

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import custom_exceptions
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import sport_subscriptions_manager, user_manager, giocate_manager
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot.models import giocate as giocata_model

from telegram import Update
from telegram.ext.dispatcher import CallbackContext
from telegram.files.inputmedia import InputMediaVideo

# ========================================== HELPER FUNCTIONS ================================================

def delete_message_if_possible(update: Update, context: CallbackContext):
    """Deletes the message specified by the update object, if it has 
    been sent in the last 48 hours (as specified by Telegram bot APIs,
    set to 47 just to be sure).

    Args:
        update (Update)
        context (CallbackContext)
    """
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    message_date = update.callback_query.message.date.replace(tzinfo=None)
    if message_date > (datetime.datetime.utcnow() - datetime.timedelta(hours=47)):
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
        )

# =============================================================================================================

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
    sport_token = update.callback_query.data.replace("sport_", "")
    sport = spr.sports_container.get_sport(sport_token)
    if not sport:
        lgr.logger.error(f"Could not open strategies for sport {sport_token}")
        raise custom_exceptions.SportNotFoundError(sport_token)
    context.bot.edit_message_text(
        f"Ecco le strategie disponibili per {sport.display_name}",
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.create_strategies_inline_keyboard(update, sport),
    )


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
    lgr.logger.debug(f"Received callback {update.callback_query.data}")
    sport_token, strategy_token, state = update.callback_query.data.split("_")
    sport = spr.sports_container.get_sport(sport_token)
    if not sport:
        lgr.logger.error(f"Could not set strategies for sport {sport_token}")
        raise custom_exceptions.SportNotFoundError(sport_token)
    strategy = strat.strategies_container.get_strategy(strategy_token)
    if not strategy or not strategy in sport.strategies:
        lgr.logger.error(f"Could not find {strategy} taken from {strategy_token} in sport {sport.name}")
        raise custom_exceptions.StrategyNotFoundError(sport_token, strategy_token)
    if state != "activate" and state != "disable":
        error_message = f"Invalid set strategy state {state}"
        lgr.logger.error(error_message)
        raise Exception(error_message)
    # ! check if the strategy is being set to the same state it is already in
    # (that would mean that we would edit the inline keyboard with an identical one
    #   and that would cause an error)
    abb_results = sport_subscriptions_manager.retrieve_subscribed_strats_from_user_id_and_sport(update.effective_user.id, sport.name)
    has_strategy = strategy.name in abb_results
    lgr.logger.debug(f"Found sport_subscriptions {abb_results=}")
    if (not has_strategy and state == "disable") or (has_strategy and state == "activate"):
        # we are either trying to disable an already disabled strategy or activate an already active one
        lgr.logger.debug(f"Trying to disable a non-active strategy or activate an already subscribed strat")
        return
    sport_sub_data = {
        "user_id": update.callback_query.from_user.id,
        "sport": sport.name,
        "strategy": strategy.name
    }
    if state == "activate":
        if not sport_subscriptions_manager.create_sport_subscription(sport_sub_data):
            lgr.logger.error(f"Could not create sport_subscription with data {sport_sub_data}")
    else:
        if not sport_subscriptions_manager.delete_sport_subscription(sport_sub_data):
            lgr.logger.error(f"Could not disable sport_subscription with data {sport_sub_data}")
    
    context.bot.edit_message_reply_markup(
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.create_strategies_inline_keyboard(update, sport),
    )


def to_homepage(update: Update, context: CallbackContext):
    """Loads the homepage of the bot.
    If the last message sent has a text field, it directly modifies that message, 
    otherwise it sends another one.
    The callback for this is "to_homepage".

    Args:
        update (Update)
        context (CallbackContext)
    """
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    if hasattr(update.callback_query.message, "text") and update.callback_query.message.text:
        context.bot.edit_message_text(
            cst.HOMEPAGE_MESSAGE,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
            parse_mode="HTML"
        )
    else:
        delete_message_if_possible(update, context)
        context.bot.send_message(
            chat_id,
            cst.HOMEPAGE_MESSAGE,
            reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
            parse_mode="HTML"
        )
    

def to_bot_config_menu(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    context.bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.BOT_CONFIGURATION_INLINE_KEYBOARD,
    )


def to_experience_menu(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    context.bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.EXPERIENCE_MENU_INLINE_KEYBOARD,
    )


def to_sports_menu(update: Update, context: CallbackContext):
    """Loads the sports menù.
    The callback for this is "to_sports_menu".

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["_id", "lot_subscription_expiration"])
    if not user_data:
        lgr.logger.error(f"Could not find user {user_id} going back from strategies menu")
        context.bot.send_message(
            user_id,
            f"Usa /start per attivare il bot prima di procedere alla scelta degli sport.",
        )
        return
    # summing 2 hours for the UTC timezone
    # expiration_date = datetime.datetime.utcfromtimestamp(float(user_data["lot_subscription_expiration"])) + datetime.timedelta(hours=2)
    # expiration_date_string = expiration_date.strftime("%d/%m/%Y alle %H:%M")
    tip_text = cst.SPORT_MENU_MESSAGE
    context.bot.edit_message_text(
        tip_text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.create_sports_inline_keyboard(update),
        parse_mode="HTML"
    )


def to_service_status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["name", "lot_subscription_expiration"])
    expiration_date = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(user_data["lot_subscription_expiration"]) + datetime.timedelta(hours=2), "%d/%m/%Y alle %H:%M")
    service_status = cst.SERVICE_STATUS_MESSAGE.format(user_data["name"], expiration_date)
    context.bot.edit_message_text(
        service_status,
        user_id, 
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.SERVICE_STATUS_KEYBOARD
    )


def feature_to_be_added(_: Update, __: CallbackContext):
    return


def to_social_menu(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    context.bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.SOCIAL_MENU_INLINE_KEYBOARD,
    )


def to_explanations_menu(update: Update, context: CallbackContext):
    """Loads the strategies explanation menù.

    The callback data for this is: to_explanation_menu

    Args:
        update (Update)
        context (CallbackContext)
    """
    context.bot.edit_message_text(
        f"Ecco le strategie disponibili",
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.EXPLANATION_TEST_INLINE_KEYBOARD,
    )


def to_referral(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_fields = ["linked_referral_user", "referral_code", "successful_referrals_since_last_payment"]
    user_data = user_manager.retrieve_user_fields_by_user_id(user_id, user_fields)
    succ_referrals = len(user_data["successful_referrals_since_last_payment"])
    referral_message = cst.REFERRAL_MENU_MESSAGE.format(user_data["referral_code"], user_data["linked_referral_user"]["linked_user_code"], succ_referrals)
    context.bot.edit_message_text(
        referral_message,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.REFERRAL_MENU_KEYBOARD,
        parse_mode="HTML",
    )


def strategy_explanation(update: Update, context: CallbackContext):
    """Sends a video explaining the strategy reported in the callback data.

    In case the previous message was a video explanation of the same strategy, 
    nothing is sent.

    If it is possible, the previous message sent by the bot is edited with the video
    of the new explanation. This can only happen if the previous message already has a video.
    Otherwise, the previous message is deleted and a new one with the requested video explanation
    is sent. 

    The callback has the following form: explanation_(strategy1|...|strategyN)

    Args:
        update (Update)
        context (CallbackContext)
    """
    strategy_token = update.callback_query.data.split("_")[1]
    lgr.logger.debug(f"Received {strategy_token=} explanation")
    strategy = strat.strategies_container.get_strategy(strategy_token)
    if not strategy or strategy.name not in cfg.config.VIDEO_FILE_IDS.keys():
        lgr.logger.error(f"{strategy_token} cannot be found for explanation")
        raise Exception(f"Strategy {strategy} not found")
    # ! avoid reloading the same video strategy
    if update.effective_message.caption and strategy.display_name in update.effective_message.caption:
        return
    strategy_video_explanation_id = cfg.config.VIDEO_FILE_IDS[strategy.name]
    caption = f"Spiegazione di {strategy.display_name}"
    # ! if the previous message has a video, edit that message
    if update.effective_message.video:
        context.bot.edit_message_media(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            media=InputMediaVideo(strategy_video_explanation_id, caption=caption),
            reply_markup=kyb.EXPLANATION_TEST_INLINE_KEYBOARD,
        )
    # ! otherwise, send a new message and delete the previous one (if possible)
    else:
        try:
            delete_message_if_possible(update, context)
        except:
            lgr.logger.error("Could not delete previous message upon sending a new strategy")
        context.bot.send_video(
            update.effective_user.id,
            strategy_video_explanation_id, 
            caption=caption,
            reply_markup=kyb.EXPLANATION_TEST_INLINE_KEYBOARD,
        )


######################################### TESTING #########################################


def accept_register_giocata(update: Update, context: CallbackContext):
    """
    The callback for this is register_giocata_yes

    Args:
        update (Update): [description]
        context (CallbackContext): [description]
    """
    user_chat_id = update.callback_query.message.chat_id
    giocata_text = update.callback_query.message.text
    giocata_text_without_answer_row = "\n".join(giocata_text.split("\n")[:-1])
    updated_giocata_text = giocata_text_without_answer_row + "\n🟩 Operazione effettuata 🟩"
    parsed_giocata = utils.parse_giocata(giocata_text, message_sent_timestamp=update.callback_query.message.date)
    retrieved_giocata = giocate_manager.retrieve_giocata_by_num_and_sport(parsed_giocata["giocata_num"], parsed_giocata["sport"])
    personal_user_giocata = giocata_model.create_user_giocata()
    personal_user_giocata["original_id"] = retrieved_giocata["_id"]
    personal_user_giocata["acceptance_timestamp"] = datetime.datetime.utcnow().timestamp()
    user_manager.register_giocata_for_user_id(personal_user_giocata, user_chat_id)
    context.bot.edit_message_text(
        updated_giocata_text,
        chat_id=user_chat_id,
        message_id=update.callback_query.message.message_id,
    )


def refuse_register_giocata(update: Update, context: CallbackContext):
    """
    The callback for this is register_giocata_no

    Args:
        update (Update): [description]
        context (CallbackContext): [description]
    """
    giocata_text = update.callback_query.message.text
    giocata_text_without_answer_row = "\n".join(giocata_text.split("\n")[:-1])
    updated_giocata_text = giocata_text_without_answer_row + "\n🟥 Operazione non effettuata 🟥"
    context.bot.edit_message_text(
        updated_giocata_text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
    )


def to_resoconti(update: Update, context: CallbackContext):
    """
    Callback data: to_resoconti

    Args:
        update (Update)
        context (CallbackContext)
    """
    chat_id = update.callback_query.from_user.id
    message_id = update.callback_query.message.message_id
    context.bot.edit_message_text(
        cst.BASE_RESOCONTI_MESSAGE,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.RESOCONTI_KEYBOARD,
    )


def last_24_hours_resoconto(update: Update, context: CallbackContext):
    """
    Callback data: resoconto_24_hours
    Args:
        update (Update)
        context (CallbackContext)
    """
    giocate_since_timestamp = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).timestamp()
    resoconto_message_header = "RESOCONTO - ULTIME 24 ORE"
    send_resoconto_since_timestamp(update, context, giocate_since_timestamp, resoconto_message_header)


def last_7_days_resoconto(update: Update, context: CallbackContext):
    """
    Callback data: resoconto_7_days
    Args:
        update (Update)
        context (CallbackContext)
    """
    giocate_since_timestamp = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).timestamp()
    resoconto_message_header = "RESOCONTO - ULTIMI 7 GIORNI"
    send_resoconto_since_timestamp(update, context, giocate_since_timestamp, resoconto_message_header)


def last_30_days_resoconto(update: Update, context: CallbackContext):
    """
    Callback data: resoconto_30_days
    Args:
        update (Update)
        context (CallbackContext)
    """
    giocate_since_timestamp = (datetime.datetime.utcnow() - datetime.timedelta(days=30)).timestamp()
    resoconto_message_header = "RESOCONTO - ULTIMI 30 GIORNI"
    send_resoconto_since_timestamp(update, context, giocate_since_timestamp, resoconto_message_header)


def _create_and_send_resoconto(context: CallbackContext, chat_id: int, message_id: int, giocate_since_timestamp: float, resoconto_message_header: str):
    user_giocate_data = user_manager.retrieve_user_giocate_since_timestamp(chat_id, giocate_since_timestamp)
    if user_giocate_data == []:
        no_giocata_found_text = resoconto_message_header + "\nNessuna giocata trovata."
        context.bot.edit_message_text(
            no_giocata_found_text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=kyb.RESOCONTI_KEYBOARD,
        )
        return
    user_giocate_ids = [giocata["original_id"] for giocata in user_giocate_data]
    giocate_full_data = giocate_manager.retrieve_giocate_from_ids(user_giocate_ids)
    resoconto_message = resoconto_message_header + "\n" + utils.create_resoconto_message(giocate_full_data)
    # * edit last message with resoconto
    context.bot.edit_message_text(
        resoconto_message,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=None,
    )
    # * send new message with menu
    context.bot.send_message(
        chat_id,
        cst.RESOCONTI_MESSAGE.format(resoconto_message_header),
        reply_markup=kyb.RESOCONTI_KEYBOARD,
    )


def send_resoconto_since_timestamp(update: Update, context: CallbackContext, giocate_since_timestamp: float, resoconto_message_header: str):
    """[summary]

    Args:
        update (Update)
        context (CallbackContext)
        giocate_since_timestamp (float): timestamp indicating from when to start retrieveing giocate
    """
    chat_id = update.callback_query.from_user.id
    message_id = update.callback_query.message.message_id
    last_message_text = update.callback_query.message.text
    if resoconto_message_header.strip().lower() in last_message_text.split("\n")[0].strip().lower():
        return
    context.dispatcher.run_async(_create_and_send_resoconto, context, chat_id, message_id, giocate_since_timestamp, resoconto_message_header)
