"""Module for the Callback Query Handlers"""
import datetime

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot import custom_exceptions
from lot_bot.dao import abbonamenti_manager, user_manager
from lot_bot.models import sports as spr, strategies as strat
from telegram import Update, LabeledPrice
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
    sport = spr.sports_container.get_sport_from_string(sport_token)
    if not sport:
        lgr.logger.error(f"Could not open strategies for sport {sport_token}")
        raise custom_exceptions.SportNotFoundError(sport_token)
    context.bot.edit_message_text(
        f"Ecco le strategie disponibili per {sport.display_name}",
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
    sport_token, strategy_token, state = update.callback_query.data.split("_")
    sport = spr.sports_container.get_sport_from_string(sport_token)
    if not sport:
        lgr.logger.error(f"Could not set strategies for sport {sport_token}")
        raise custom_exceptions.SportNotFoundError(sport_token)
    strategy = strat.strategies_container.get_strategy_from_string(strategy_token)
    if not strategy or not strategy in sport.strategies:
        lgr.logger.error(f"Could not find {strategy} taken from {strategy_token} in sport {sport.name}")
        raise custom_exceptions.StrategyNotFoundError(sport_token, strategy_token)
    if state != "activate" and state != "disable":
        lgr.logger.error(f"Invalid set strategy state {state}")
        raise Exception(f"Invalid set strategy state {state}")

    # ! check if the strategy is being set to the same state it is already in
    # (that would mean that we would edit the inline keyboard with an identical one
    #   and that would cause an error)
    abb_results = abbonamenti_manager.retrieve_abbonamento_sport_strategy_from_user_id(update.effective_user.id, sport.name, strategy.name)
    lgr.logger.debug(f"Found abbonamenti {abb_results=}")
    if (not abb_results and state == "disable") or (abb_results and state == "activate"):
        # we are either trying to disable an already disabled strategy or activate an already active one
        context.bot.answer_callback_query(update.callback_query.id, text="")
        return
    abbonamento_data = {
        "telegramID": update.callback_query.from_user.id,
        "sport": sport.name,
        "strategia": strategy.name
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
        context.bot.send_message(
            user_id,
            f"Usa /start per attivare il bot prima di procedere alla scelta degli sport.",
        )
        # must answer the callback query, even if it is useless
        context.bot.answer_callback_query(update.callback_query.id, text="")
        return
        # raise custom_exceptions.UserNotFound(user_id)
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
    """Loads the link menù.

    The callback for this is: to_links

    Args:
        update (Update): [description]
        context (CallbackContext): [description]
    """
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
    # must answer the callback query, even if it is useless
    context.bot.answer_callback_query(update.callback_query.id, text="")



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
    strategy = strat.strategies_container.get_strategy_from_string(strategy_token)
    if strategy and strategy.name not in cfg.config.VIDEO_FILE_IDS.keys():
        lgr.logger.error(f"{strategy} cannot be found for explanation")
        raise Exception(f"Strategy {strategy} not found")
    # ! avoid reloading the same video strategy
    if update.effective_message.caption and strategy.display_name in update.effective_message.caption:
        # must answer the callback query, even if it is useless
        context.bot.answer_callback_query(update.callback_query.id, text="")
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
    # must answer the callback query, even if it is useless
    context.bot.answer_callback_query(update.callback_query.id, text="")


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
    updated_giocata_text = giocata_text_without_answer_row + "\n🟩 Giocata effettuata 🟩"
    parsed_giocata = utils.parse_giocata(giocata_text)
    user_manager.register_giocata_for_user_id(parsed_giocata, user_chat_id)
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
    updated_giocata_text = giocata_text_without_answer_row + "\n🟥 Giocata non effettuata 🟥"
    context.bot.edit_message_text(
        updated_giocata_text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
    )

##############################################################################################################

def test_payment(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    title = "Payment Example"
    description = "Payment Example Description"
    # select a payload just for you to recognize its the donation from your bot
    payload = "pagamento_abbonamento"
    # In order to get a provider_token see https://core.telegram.org/bots/payments#getting-a-token
    currency = "EUR"
    # price in dollars
    price = 1
    # price * 100 so as to include 2 decimal points
    prices = [LabeledPrice("Abbonamento", price * 100)]

    # optionally pass need_name=True, need_phone_number=True,
    # need_email=True, need_shipping_address=True, is_flexible=True
    context.bot.send_invoice(
        chat_id, title, description, payload, cfg.config.PAYMENT_TOKEN, currency, prices,
        need_name=True, need_email=True
    )


def pre_checkout_handler(update: Update, context: CallbackContext):
    query = update.pre_checkout_query
    # check the payload, is this from your bot?
    if query.invoice_payload != 'pagamento_abbonamento':
        # answer False pre_checkout_query
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)


