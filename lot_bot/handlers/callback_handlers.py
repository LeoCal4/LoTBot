"""Module for the Callback Query Handlers"""
import datetime
import random

from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import custom_exceptions
from lot_bot import keyboards as kyb
from lot_bot import logger as lgr
from lot_bot import database as db
from lot_bot import utils
from lot_bot.dao import (giocate_manager, sport_subscriptions_manager,
                         user_manager, budget_manager, analytics_manager)
from lot_bot.models import users
from lot_bot.models import giocate as giocata_model
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot.models import subscriptions as subs_model
from lot_bot.handlers import message_handlers
from telegram import Update, ReplyKeyboardRemove
from telegram.error import BadRequest
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
        utils.create_strategies_explanation_message(sport),
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.create_strategies_inline_keyboard(update, sport),
        parse_mode="HTML",
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


def to_homepage(update: Update, context: CallbackContext, send_new_message: bool = False, delete_last_message: bool = True):
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
    homepage_message = cst.HOMEPAGE_MESSAGE
    #* check if user completed tutorial
    homepage_message += utils.create_checklist_completion_message(chat_id)
    if hasattr(update.callback_query.message, "text") and update.callback_query.message.text and not send_new_message:
        context.bot.edit_message_text(
            homepage_message,
            chat_id=chat_id,
            disable_web_page_preview=True,
            message_id=message_id,
            reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
            parse_mode="HTML"
        )
    else:
        if delete_last_message:
            delete_message_if_possible(update, context)
        context.bot.send_message(
            chat_id,
            homepage_message,
            disable_web_page_preview=True,
            reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
            parse_mode="HTML"
        )
    
def to_bot_config_menu(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    menu_message = cst.BOT_CONFIG_MENU_MESSAGE
    #* check if user completed tutorial
    menu_message += utils.create_checklist_completion_message(chat_id)
    context.bot.edit_message_text(
        text = menu_message,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.BOT_CONFIGURATION_INLINE_KEYBOARD,
        parse_mode="HTML"
    )

def to_payments_and_referrals_menu(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    menu_message = cst.PAY_AND_REF_MENU_MESSAGE
    #* check if user completed tutorial
    menu_message += utils.create_checklist_completion_message(chat_id)
    context.bot.edit_message_text(
        text=menu_message,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.PAYMENT_AND_REFERRAL_MENU_INLINE_KEYBOARD,
        parse_mode="HTML"
    )

def to_use_guide_menu(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    menu_message = cst.USE_GUIDE_MENU_MESSAGE
    #* check if user completed tutorial
    menu_message += utils.create_checklist_completion_message(chat_id)
    context.bot.edit_message_text(
        text=menu_message,
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.USE_GUIDE_MENU_KEYBOARD,
        parse_mode="HTML"
    )

def to_how_work(update: Update, context: CallbackContext):
    context.bot.edit_message_text(
        text=cst.HOW_WORK_MESSAGE,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.TO_HOW_WORK_KEYBOARD,
        parse_mode="HTML"
    )

def to_sports_menu(update: Update, context: CallbackContext):
    """Loads the sports menù.
    The callback for this is "to_sports_menu".

    Args:
        update (Update)
        context (CallbackContext)
    """
    user_id = update.effective_user.id
    user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["_id"])
    if not user_data:
        lgr.logger.error(f"Could not find user {user_id} going back from strategies menu")
        context.bot.send_message(
            user_id,
            f"Usa /start per attivare il bot prima di procedere alla scelta degli sport.",
        )
        return
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
    user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["name", "subscriptions"])
    service_status = cst.SERVICE_STATUS_MESSAGE.format(user_data["name"])
    for sub in user_data["subscriptions"]: 
        sub_exp_date = sub["expiration_date"]
        expiration_date = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(sub_exp_date) + datetime.timedelta(hours=1), "%d/%m/%Y alle %H:%M")
        if sub_exp_date == 9999999999:
            expiration_date_text = " (sempre attivo)"
        elif float(sub_exp_date) >= update.effective_message.date.timestamp():
            expiration_date_text = f": valido fino a {expiration_date}"
        else:
            expiration_date_text = f": scaduto il {expiration_date}"

        sub_name = subs_model.sub_container.get_subscription(sub["name"])
        sub_emoji = "🟢" if float(sub_exp_date) >= update.effective_message.date.timestamp() else "🔴"
        service_status += f"\n- {sub_emoji} {sub_name.display_name}{expiration_date_text}"
    if "- 🟢 LoT Versione Premium:" in service_status:
        service_status = service_status.replace("\n- 🟢 LoT Versione Base","").replace(" (sempre attivo)","")
    #if "- 🔴 Lot Versione Premium" in service_status:
        #mettere prima versione base in alto e sotto "- 🔴 Lot Versione Premium"
        #magari aggiungendo una frase per far acquistare al cliente il Premium

    context.bot.edit_message_text(
        service_status,
        user_id, 
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.SERVICE_STATUS_KEYBOARD
    )

#related to text explanations (not video!)
def to_strat_expl_menu(update: Update, context: CallbackContext): 
    """Shows the inline keyboard containing all strategies,
        user clicks a button to see the strategy's explanation 

    Args:
        update (Update)
        context (CallbackContext)

    """
    user_id = update.effective_user.id
    text = "📊 Questo è l'elenco delle strategie! Selezionane una per scoprire di cosa si tratta ! 📊"
    #context.bot.edit_message_text(
    #    text,
    #    user_id,
    #    message_id=update.callback_query.message.message_id,
    #    reply_markup=kyb.create_strategies_expl_inline_keyboard(update),
    #)
    context.bot.edit_message_text(
        text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.create_strategies_expl_inline_keyboard(update),
        parse_mode="HTML"
    )

#related to text explanations (not video!)
def strategy_text_explanation(update: Update, context: CallbackContext):
    """Shows the choosen strategy's explanation
    Triggered by callback <strategy name>_explanation

    Args:
        update (Update)
        context (CallbackContext)

    Raises:
        Exception: raised in case the strategy is not valid 
    """
    strategy_token = update.callback_query.data.replace("text_explanation_", "")
    strategy = strat.strategies_container.get_strategy(strategy_token)
    text = cst.DEFAULT_STRAT_EXPLANATION_TEXT
    if not strategy:
        lgr.logger.error(f"Could not find strategy {strategy_token} to show its explanation, showing default text instead")
    else:
        text = f"{strategy.display_name}:\n\n"+strategy.explanation
    context.bot.edit_message_text(
        text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.BACK_TO_EXPL_STRAT_MENU_KEYBOARD,
        parse_mode="HTML"
    )

def feature_to_be_added(_: Update, __: CallbackContext):
    return
    
def do_nothing(_: Update, __: CallbackContext):
    return

def to_social_menu(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    context.bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=kyb.SOCIAL_MENU_INLINE_KEYBOARD,
    )


def to_referral(update: Update, context: CallbackContext, send_new: bool = False):
    user_id = update.effective_user.id
    user_fields = ["linked_referral_user", "referral_code", "successful_referrals_since_last_payment"]
    user_data = user_manager.retrieve_user_fields_by_user_id(user_id, user_fields)
    succ_referrals = len(user_data["successful_referrals_since_last_payment"])
    referral_message = utils.create_personal_referral_updated_text(user_data["referral_code"], succ_referrals)
    if not send_new:
        context.bot.edit_message_text(
            referral_message,
            chat_id=user_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=kyb.get_referral_menu_keyboard(number_of_referrals=succ_referrals),
            parse_mode="HTML",
        )
    else:
        context.bot.send_message(
            user_id,
            referral_message,
            reply_markup=kyb.get_referral_menu_keyboard(number_of_referrals=succ_referrals),
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
    # * avoid reloading the same video strategy
    if update.effective_message.caption and strategy.display_name in update.effective_message.caption:
        return
    strategy_video_explanation_id = cfg.config.VIDEO_FILE_IDS[strategy.name]
    caption = f"Spiegazione di {strategy.display_name}"
    # * if the previous message has a video, edit that message
    if update.effective_message.video:
        context.bot.edit_message_media(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            media=InputMediaVideo(strategy_video_explanation_id, caption=caption),
            reply_markup=kyb.EXPLANATION_TEST_INLINE_KEYBOARD,
        )
    # * otherwise, send a new message and delete the previous one (if possible)
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


def accept_register_giocata(update: Update, context: CallbackContext):
    """
    The callback for this is register_giocata_yes

    Args:
        update (Update): [description]
        context (CallbackContext): [description]

    Raises:
        e (Exception): in case of error editing message
    """
    user_chat_id = update.callback_query.message.chat_id
    giocata_text = update.callback_query.message.text
    # * modify message text to specify that the giocata has been registered
    giocata_text_rows = giocata_text.split("\n")
    giocata_text_without_answer_row = "\n".join(giocata_text_rows[:-1])
    updated_giocata_text = giocata_text_without_answer_row + "\n🟩 Operazione effettuata 🟩"
    # * identify the giocata type and parse it accordingly
    if "status:" not in giocata_text_rows[0].lower():
        lgr.logger.debug("Parsing LoT giocata")
        parsed_giocata = giocata_model.parse_giocata(giocata_text, message_sent_timestamp=update.callback_query.message.date)
    else:
        lgr.logger.debug("Parsing TB giocata")
        parsed_giocata = giocata_model.parse_teacherbet_giocata(giocata_text, message_sent_timestamp=update.callback_query.message.date)[0]
    # * retrieve and save the giocata for the user
    retrieved_giocata = giocate_manager.retrieve_giocata_by_num_and_sport(parsed_giocata["giocata_num"], parsed_giocata["sport"])
    if not retrieved_giocata:
        lgr.logger.error(f"Cannot retrieve giocata upon giocata acceptation - {parsed_giocata['giocata_num']=} {parsed_giocata['sport']=}")
        raise Exception("Cannot retrieve giocata upon giocata acceptation")
    personal_user_giocata = giocata_model.create_user_giocata()
    personal_user_giocata["original_id"] = retrieved_giocata["_id"]
    personal_user_giocata["acceptance_timestamp"] = datetime.datetime.utcnow().timestamp()
    # * check for differences in the saved stake and the current one (personalized stake)
    if "base_stake" in parsed_giocata and parsed_giocata["base_stake"] != retrieved_giocata["base_stake"]:
        personal_user_giocata["personal_stake"] = parsed_giocata["base_stake"]
    user_manager.register_giocata_for_user_id(personal_user_giocata, user_chat_id)
    # * update user budget if giocata has an outcome
    giocata_outcome = retrieved_giocata["outcome"]
    if (giocata_outcome == "win" or giocata_outcome == "loss") and parsed_giocata["sport"] != spr.sports_container.EXCHANGE:
        #temporary
        #user_budget = budget_manager.retrieve_budgets_from_user_id(chat_id)
        #user_budget = user_manager.retrieve_user_fields_by_user_id(user_chat_id, ["budget"])["budget"]
        #if not user_budget is None:
        #    user_budget = int(user_budget)
        #    update_result = users.update_single_user_budget_with_giocata(user_chat_id, user_budget, personal_user_giocata["original_id"], retrieved_giocata)
        #    if not update_result:
        #        context.bot.send_message(user_chat_id, "ERRORE: impossibile aggiornare il budget, la giocata non è stata trovata")
        default_budget = budget_manager.retrieve_default_budget_from_user_id(user_chat_id)
        if not default_budget is None:
            default_budget_balance = int(default_budget["balance"])
            update_result = users.update_single_user_budget_with_giocata2(user_chat_id, default_budget_balance, personal_user_giocata["original_id"], retrieved_giocata)
            if not update_result:
                context.bot.send_message(user_chat_id, "ERRORE: impossibile aggiornare il budget, la giocata non è stata trovata")
    #* update analtics and check checklist completion
    analytics_update = analytics_manager.update_accepted_giocate(user_chat_id, retrieved_giocata["_id"])
    if not analytics_update:
        lgr.logger.warning(f"Could not update analytics with accepted giocata {retrieved_giocata['_id']}")
    if analytics_manager.check_checklist_completion(user_chat_id):
        message_handlers.checklist_completed_handler(update, context)
    #* complete operation editing the giocata message
    try:                      
        context.bot.edit_message_text(
            updated_giocata_text,
            chat_id=user_chat_id,
            message_id=update.callback_query.message.message_id,
        )
    except BadRequest:
        lgr.logger.error(f"BadRequest error in accept_register_giocata")
        dev_message = f"ERRORE BadRequest in accept_register_giocata per l'utente {update.callback_query.message.chat_id}."
        message_handlers.send_messages_to_developers(context, [dev_message])


def refuse_register_giocata(update: Update, context: CallbackContext):
    """
    The callback for this is register_giocata_no

    Args:
        update (Update): [description]
        context (CallbackContext): [description]
    """
    user_chat_id = update.callback_query.message.chat_id
    giocata_text = update.callback_query.message.text
    giocata_text_without_answer_row = "\n".join(giocata_text.split("\n")[:-1])
    updated_giocata_text = giocata_text_without_answer_row + "\n🟥 Operazione non effettuata 🟥"
    #* retrieve giocata id
    parsed_giocata = giocata_model.parse_giocata(giocata_text, message_sent_timestamp=update.callback_query.message.date)
    retrieved_giocata = giocate_manager.retrieve_giocata_by_num_and_sport(parsed_giocata["giocata_num"], parsed_giocata["sport"])
    if not retrieved_giocata:
        lgr.logger.error(f"Cannot retrieve giocata upon giocata acceptation - {parsed_giocata['giocata_num']=} {parsed_giocata['sport']=}")
        raise Exception("Cannot retrieve giocata upon giocata acceptation")
    #* update analtics and check checklist completion
    analytics_manager.update_refused_giocate(user_chat_id, retrieved_giocata["_id"])
    if analytics_manager.check_checklist_completion(user_chat_id):
        message_handlers.checklist_completed_handler(update, context)
    try:
        context.bot.edit_message_text(
            updated_giocata_text,
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
        )
    except BadRequest:
        lgr.logger.error(f"BadRequest error in refuse_register_giocata")
        dev_message = f"ERRORE BadRequest in refuse_register_giocata per l'utente {update.callback_query.message.chat_id}."
        message_handlers.send_messages_to_developers(context, [dev_message])


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


def _create_and_send_resoconto(context: CallbackContext, chat_id: int, giocate_since_timestamp: float, resoconto_message_header: str, edit_messages: bool = True, message_id: int = None, receiver_user_id: int = None):
    user_giocate_data = user_manager.retrieve_user_giocate_since_timestamp(chat_id, giocate_since_timestamp)
    if receiver_user_id is None:
        receiver_user_id = chat_id
    if user_giocate_data == []:
        no_giocata_found_text = resoconto_message_header + "\nNessuna giocata trovata."
        if edit_messages:
            context.bot.edit_message_text(
                no_giocata_found_text,
                chat_id=receiver_user_id,
                message_id=message_id,
                reply_markup=kyb.RESOCONTI_KEYBOARD,
            )
        else:
            context.bot.send_message(
                receiver_user_id,
                no_giocata_found_text,
            )
        return
    user_giocate_data_dict = {giocata["original_id"]: giocata for giocata in user_giocate_data}
    user_giocate_ids = list(user_giocate_data_dict.keys())
    giocate_full_data = giocate_manager.retrieve_giocate_from_ids(user_giocate_ids)
    resoconto_message = resoconto_message_header + "\n" + utils.create_resoconto_message(giocate_full_data, user_giocate_data_dict)
    # * edit last message/send message with resoconto
    if edit_messages:
        context.bot.edit_message_text(
            resoconto_message,
            chat_id=receiver_user_id,
            message_id=message_id,
            reply_markup=None,
        )
        # * send new message with menu
        context.bot.send_message(
            receiver_user_id,
            cst.RESOCONTI_MESSAGE.format(resoconto_message_header),
            reply_markup=kyb.RESOCONTI_KEYBOARD,
        )
    else:
        context.bot.send_message(
            receiver_user_id,
            resoconto_message,
        )

def send_latest_giocate_to_new_user(update: Update, context: CallbackContext):
    lgr.logger.debug("Sending last 5 giocate in last 10h")
    chat_id = update.callback_query.message.chat_id
    latest_giocate = giocate_manager.retrieve_giocate_between_timestamps(
        datetime.datetime.now().timestamp(), (datetime.datetime.now()+datetime.timedelta(hours=-10)).timestamp()
    )
    lgr.logger.debug(f"{latest_giocate=}")

    if not latest_giocate:
        context.bot.send_message(
            chat_id, 
            text=cst.NO_GIOCATA_TO_SEND_ON_FIRST_USAGE, 
            disable_web_page_preview=True,
            parse_mode ="HTML",
            reply_markup=kyb.STARTUP_REPLY_KEYBOARD)
        return
    context.bot.send_message(
        text = "Ecco gli eventi che potrebbero essere ancora in corso!",
        chat_id=chat_id,
        disable_web_page_preview=True,
        reply_markup=kyb.STARTUP_REPLY_KEYBOARD,
        parse_mode="HTML"
    )
    sport_validi = ["calcio","basket","tennis","exchange","hockey","pallavolo","pingpong","tuttoilresto"]
    for i, giocata in enumerate(latest_giocate):
        if i > 0:
            break
        if giocata["sport"] in sport_validi:
            text = giocata["raw_text"]
 
            custom_reply_markup = kyb.REGISTER_GIOCATA_KEYBOARD
            user_budget = budget_manager.retrieve_default_budget_from_user_id(chat_id)
            if user_budget:
                #user_budget_balance = int(user_budget["simply_interest_base"]) temporary
                user_budget_balance = int(user_budget["balance"])
                text = giocata_model.update_giocata_text_with_stake_money_value(text, user_budget_balance)                
                #if user_budget["interest_type"] == "semplice":
                #    user_budget_balance = int(user_budget["simply_interest_base"])
                #    text = giocata_model.update_giocata_text_with_stake_money_value(text, user_budget_balance)
                #elif user_budget["interest_type"] == "composto":
                #    user_budget_balance = int(user_budget["balance"])
                #    text = giocata_model.update_giocata_text_with_stake_money_value(text, user_budget_balance)
            try:
                text += "\n\nSeguirai questo evento?"
                context.bot.send_message(
                    chat_id, 
                    text, 
                    reply_markup=custom_reply_markup)
            except Exception as e:
                lgr.logger.error(f"Could not send message {text} to user {chat_id} - {str(e)}")

    # context.bot.send_message(
    #     chat_id,
    #     cst.HOMEPAGE_MESSAGE,
    #     disable_web_page_preview=True,
    #     reply_markup=kyb.HOMEPAGE_INLINE_KEYBOARD,
    #     parse_mode="HTML"
    # )

def send_socials_list(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    update.callback_query.edit_message_reply_markup(reply_markup = None)
    send_latest_giocate_to_new_user(update,context)
    #Creating user subscription
    free_sub = {"name": subs_model.sub_container.LOTFREE.name, "expiration_date": 9999999999}
    #if not teacherbet_code:
    trial_expiration_timestamp = (datetime.datetime.now() + datetime.timedelta(days=5)).timestamp()
    sub = {"name": subs_model.sub_container.LOTCOMPLETE.name, "expiration_date": trial_expiration_timestamp}
    #else:
    #    sub = subs_model.create_teacherbet_base_sub()
    subscriptions = [sub,free_sub]
    db.mongo.utenti.update_one({ "_id": chat_id }, { "$set": { "subscriptions": subscriptions } } )
    #user_data["subscriptions"].append(sub)
    #user_data["subscriptions"].append(free_sub)
    to_homepage(update, context, send_new_message=True, delete_last_message=False)

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
    # * avoid sending again the same type of resoconto
    if resoconto_message_header.strip().lower() in last_message_text.split("\n")[0].strip().lower():
        return
    # TODO add analyitics with type and timestamp
    # context.dispatcher.run_async(_create_and_send_resoconto, context, chat_id, giocate_since_timestamp, resoconto_message_header, message_id=message_id)
    _create_and_send_resoconto(context, chat_id, giocate_since_timestamp, resoconto_message_header, message_id=message_id)


def get_free_month_subscription(update: Update, context: CallbackContext):
    # extend subscription of 1 month
    user_id = update.effective_user.id
    user_update_result = users.add_days_to_user_subscription(user_id, 30)
    if not user_update_result:
        lgr.logger.warning(f"Could not extend user {user_id}'s sub by 30 days")
    retrieved_user = user_manager.retrieve_user_fields_by_user_id(user_id, ["successful_referrals_since_last_payment", "referral_code"])
    # * reset user successful referrals
    user_data = {"successful_referrals_since_last_payment": retrieved_user["successful_referrals_since_last_payment"][10:]}
    try:
        user_update_result = user_manager.update_user(user_id, user_data) and user_update_result
    except:
        user_update_result = False
    free_sub_message = "Mese gratuito riscattato con successo!"
    if not user_update_result:
        lgr.logger.error(f"Could not add free month for user {user_id}")
        free_sub_message = "ERRORE: impossibile riscattare il mese gratuito, contattaci su @teamlot"
    free_sub_message += "\n\n" + utils.create_personal_referral_updated_text(retrieved_user["referral_code"], 0)
    context.bot.edit_message_text(
        free_sub_message,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        reply_markup=kyb.get_referral_menu_keyboard(number_of_referrals=0),
        parse_mode="HTML",
    )
