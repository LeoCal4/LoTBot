from telegram import Bot
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, MessageHandler,
                          PreCheckoutQueryHandler, Updater)
from telegram.ext.dispatcher import Dispatcher

from lot_bot import config as cfg
from lot_bot import filters
from lot_bot.handlers import (callback_handlers, message_handlers,
                              payment_handler, ref_code_handlers, 
                              command_handlers, budget_handlers)

bot = None
updater = None
dispatcher = None


def get_referral_conversation_handler() -> ConversationHandler:
    """Creates the conversation handler to contain the referral choice.
    This approach was used in order to avoid restrictions on the referral/affiliation 
    codes, since asking for any string as a code would have meant that any of the user
    text messages to the bot would have been interpreted as a referral code. 

    This conversation handler does not include the pre-checkout and the payment end
    since adding them here did not make them work.

    Returns:
        ConversationHandler
    """
    payment_conversation_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(payment_handler.to_add_linked_referral_before_payment, pattern=r"^to_add_referral$")],
        states={
            payment_handler.REFERRAL: [
                MessageHandler(filters.get_referral_filter(), payment_handler.received_linked_referral_during_payment),
                MessageHandler(filters.get_codice10euro_filter(), payment_handler.received_codice_during_payment), # TODO make this more generic, not only for codice10euro
                #MessageHandler(filters.get_qualsiasicodice_filter(), payment_handler.received_codice_during_payment),
                CallbackQueryHandler(payment_handler.to_payments, pattern=r"^to_payments$")
                ],
        },
        fallbacks=[
            CallbackQueryHandler(payment_handler.to_homepage_from_referral_callback, pattern=r"^to_homepage_from_referral$"),
            MessageHandler(filters.get_normal_messages_filter(), ref_code_handlers.to_homepage_from_referral_message),
            ],
    )
    return payment_conversation_handler


def update_referral_conversation_handler() -> ConversationHandler:
    update_ref_code_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ref_code_handlers.to_update_personal_ref_code, pattern=r"^to_update_personal_ref_code_conversation$"),
            CallbackQueryHandler(ref_code_handlers.to_update_linked_referral, pattern=r"^to_update_linked_ref_code_conversation$")
            ],
        states={
            ref_code_handlers.UPDATE_PERSONAL_REFERRAL: [
                MessageHandler(filters.get_text_messages_filter(), ref_code_handlers.received_personal_referral),
                CallbackQueryHandler(ref_code_handlers.to_ref_code_menu_from_referral_update_callback, pattern=r"^to_ref_code_menu_from_referral$")
            ],
            ref_code_handlers.UPDATE_LINKED_REFERRAL: [
                MessageHandler(filters.get_text_messages_filter(), ref_code_handlers.received_linked_referral_handler),
                CallbackQueryHandler(ref_code_handlers.to_ref_code_menu_from_referral_update_callback, pattern=r"^to_ref_code_menu_from_referral$")
            ]
        },
        fallbacks=[
            MessageHandler(filters.get_normal_messages_filter(), ref_code_handlers.to_homepage_from_referral_message),
        ],
    )
    return update_ref_code_conv_handler

def get_new_budget_conversation_handler() -> ConversationHandler:
    """Creates the conversation handler to contain the budget update.
    Returns:
        ConversationHandler
    """
    new_budget_conversation_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(budget_handlers.create_new_budget, pattern=r"^create_new_budget$")
            ],
        states={
            budget_handlers.CREATE_BUDGET_NAME: [
                MessageHandler(filters.get_text_messages_filter(), budget_handlers.received_name_for_new_budget),
                CallbackQueryHandler(budget_handlers.to_budgets_menu, pattern=r"^to_budgets_menu$")
                ],
            #budget_handlers.SET_BUDGET_INTEREST: [
            #    CallbackQueryHandler(budget_handlers.received_interest_type_for_new_budget, pattern=r"^interest_type_(semplice|composto)_[a-zA-Z0-9_ ]+$"),
            #    CallbackQueryHandler(budget_handlers.to_budgets_menu, pattern=r"^to_budgets_menu$")
            #    ],
            budget_handlers.SET_BUDGET_BALANCE: [
                MessageHandler(filters.get_float_filter(), budget_handlers.received_balance_for_budget),
                CallbackQueryHandler(budget_handlers.to_budgets_menu, pattern=r"^to_budgets_menu$")
                ],
        },
        fallbacks=[ #TODO da modificare filter
            MessageHandler(filters.get_command_messages_filter(), ref_code_handlers.to_homepage_from_referral_message),
            ],
    )
    return new_budget_conversation_handler

def get_edit_budget_conversation_handler() -> ConversationHandler:
    """Creates the conversation handler to contain the budget update.
    Returns:
        ConversationHandler
    """
    edit_budget_conversation_handler = ConversationHandler( 
        entry_points=[
            CallbackQueryHandler(budget_handlers.edit_budget_name, pattern=r"^edit_budget_name_[a-zA-Z0-9_ ]+$"),
            CallbackQueryHandler(budget_handlers.edit_budget_balance, pattern=r"^edit_budget_balance_[a-zA-Z0-9_ ]+$"),
            CallbackQueryHandler(budget_handlers.set_budget_interest_semplice, pattern=r"^set_budget_interest_semplice_[a-zA-Z0-9_ ]+$")
            ],
        states={
            budget_handlers.EDIT_BUDGET_NAME: [
                MessageHandler(filters.get_text_messages_filter(), budget_handlers.received_name_for_existing_budget),
                ],
            budget_handlers.EDIT_BUDGET_BALANCE: [
                MessageHandler(filters.get_float_filter(), budget_handlers.received_balance_for_budget), #add handler for text messages - the bot will ask the user to insert a number, not text
                ],
            budget_handlers.EDIT_BASE_SIMPLY_INTEREST: [
                MessageHandler(filters.get_float_filter(), budget_handlers.received_base_interest_semplice),
                ],
        },
        fallbacks=[
            CallbackQueryHandler(budget_handlers.to_budgets_menu_end_conversation, pattern=r"^to_budgets_menu_end_conversation$"),
            MessageHandler(filters.get_command_messages_filter(), ref_code_handlers.to_homepage_from_referral_message),
            ],
    )
    return edit_budget_conversation_handler

def get_first_budget_creation() -> ConversationHandler:
    """
    Creates the conversation handler to create the first budget,
    when the user start the bot, for now budget name is 'DEMO'
    Returns:
        ConversationHandler
    """
    first_budget_conversation_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(budget_handlers.create_first_budget, pattern=r"^create_first_budget$")
            ],
        states={
            budget_handlers.SET_FIRST_BUDGET_BALANCE: [
                MessageHandler(filters.get_float_filter(), budget_handlers.received_balance_for_first_budget)
                ],
        },
        fallbacks=[ #users must create a budget
            MessageHandler(filters.get_nothing(), ref_code_handlers.to_homepage_from_referral_message),
           ],
    )
    return first_budget_conversation_handler

def add_handlers(dispatcher: Dispatcher):
    """Adds all the bot's handlers to the dispatcher.

    Args:
        dispatcher (Dispatcher)
    """
    # ================ COMMAND HANDLERS ================
    dispatcher.add_handler(CommandHandler("start", command_handlers.start_command))
    dispatcher.add_handler(CommandHandler("broadcast_scaduti", command_handlers.broadcast_scaduti_handler))
    dispatcher.add_handler(CommandHandler("broadcast_attivi", command_handlers.broadcast_attivi_handler))
    dispatcher.add_handler(CommandHandler("broadcast_nuovi", command_handlers.broadcast_nuovi_handler))
    dispatcher.add_handler(CommandHandler("broadcast", command_handlers.broadcast_handler))
    dispatcher.add_handler(CommandHandler("invia_messaggio", command_handlers.send_message_handler))
    # ------------ Users managing commands --------------
    dispatcher.add_handler(CommandHandler("aggiungi_giorni", command_handlers.aggiungi_giorni))
    dispatcher.add_handler(CommandHandler("resoconto_utente", command_handlers.get_user_resoconto))
    dispatcher.add_handler(CommandHandler("modifica_referral", ref_code_handlers.update_user_ref_code_handler))
    dispatcher.add_handler(CommandHandler("cambia_ruolo", command_handlers.set_user_role))
    dispatcher.add_handler(CommandHandler("blocca_utente", command_handlers.block_messages_to_user))
    dispatcher.add_handler(CommandHandler("sblocca_utente", command_handlers.unlock_messages_to_user))
    dispatcher.add_handler(CommandHandler("visualizza_utente", command_handlers.visualize_user_info))
    dispatcher.add_handler(CommandHandler("analytics_utente", command_handlers.visualize_user_analytics))
    dispatcher.add_handler(CommandHandler("elimina_utente", command_handlers.delete_user))

    # ------------ Trend commands --------------
    dispatcher.add_handler(CommandHandler("trend_giorni", command_handlers.get_trend_by_days))
    dispatcher.add_handler(CommandHandler("trend_eventi", command_handlers.get_trend_by_events))
    # ------------ Personal stake commands --------------
    dispatcher.add_handler(CommandHandler("crea_stake", command_handlers.create_personal_stake))
    dispatcher.add_handler(CommandHandler("visualizza_stake", command_handlers.visualize_personal_stakes))
    dispatcher.add_handler(CommandHandler("elimina_stake", command_handlers.delete_personal_stakes))
    # ---------------- Budget commands -----------------
    dispatcher.add_handler(CommandHandler("visualizza_budget", command_handlers.get_user_budget))
    dispatcher.add_handler(CommandHandler("imposta_budget", command_handlers.set_user_budget))


    # ======= CALLBACK QUERIES HANDLERS =======
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_homepage, pattern=r"^to_homepage$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_bot_config_menu, pattern=r"^to_bot_config_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_payments_and_referrals_menu, pattern=r"^to_payments_and_referrals_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_use_guide_menu, pattern=r"^to_use_guide_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.select_sport_strategies, pattern=r"^sport_\w+$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.set_sport_strategy_state, pattern=r"^\w+_\w+_(activate|disable)$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_sports_menu, pattern=r"^to_sports_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_how_work, pattern=r"^to_how_work$"))
    # dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_social_menu, pattern=r"^to_social_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_service_status, pattern=r"^to_service_status$"))
    # dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_strat_expl_menu, pattern=r"^to_strat_expl_menu$"))
    # dispatcher.add_handler(CallbackQueryHandler(callback_handlers.strategy_explanation, pattern=filters.get_explanation_pattern())) 
    # dispatcher.add_handler(CallbackQueryHandler(callback_handlers.strategy_text_explanation, pattern=filters.get_strat_text_explanation_pattern())) 
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.accept_register_giocata, pattern=r"^register_giocata_yes$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.refuse_register_giocata, pattern=r"^register_giocata_no$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_resoconti, pattern=r"^to_resoconti$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_referral, pattern=r"^to_referral$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.last_24_hours_resoconto, pattern=r"^resoconto_24_hours$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.last_7_days_resoconto, pattern=r"^resoconto_7_days$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.last_30_days_resoconto, pattern=r"^resoconto_30_days$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.get_free_month_subscription, pattern=r"^to_get_free_month_subscription$"))
    # BUDGET CALLBACK HANDLERS
    dispatcher.add_handler(CallbackQueryHandler(budget_handlers.to_budgets_menu, pattern=r"^to_budgets_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(budget_handlers.edit_budget, pattern=r"^edit_budget_(?!name|balance|interest)[a-zA-Z0-9_ ]+$")) #to get edit_budget_<budget_name> but not edit_budget_name_<budget_name> or edit_budget_balance_<budget_name>
    dispatcher.add_handler(CallbackQueryHandler(budget_handlers.set_default_budget, pattern=r"^set_default_budget_[a-zA-Z0-9_ ]+$"))
    dispatcher.add_handler(CallbackQueryHandler(budget_handlers.pre_delete_budget, pattern=r"^pre_delete_budget_[a-zA-Z0-9_ ]+$"))
    dispatcher.add_handler(CallbackQueryHandler(budget_handlers.delete_budget, pattern=r"^delete_budget[a-zA-Z0-9_ ]+$")) 
    dispatcher.add_handler(CallbackQueryHandler(budget_handlers.edit_budget_interest_menu, pattern=r"^edit_budget_interest_[a-zA-Z0-9_ ]+$")) #TODO da modificare forse in to_edit_budget.. ecc.
    dispatcher.add_handler(CallbackQueryHandler(budget_handlers.set_budget_interest_composto, pattern=r"^set_budget_interest_composto_[a-zA-Z0-9_ ]+$"))

   # dispatcher.add_handler(CallbackQueryHandler(budget_handlers.create_new_budget, pattern=r"^create_new_budget$"))
    
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.feature_to_be_added, pattern=r"^new$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.do_nothing, pattern=r"^do_nothing$"))

    # =========== FIRST START HANDLERS ===========
    dispatcher.add_handler(get_first_budget_creation()) 
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.send_socials_list, pattern=r"^send_socials_list$"))

    # =========== BUDGET HANDLERS ===========
    dispatcher.add_handler(get_new_budget_conversation_handler())
    dispatcher.add_handler(get_edit_budget_conversation_handler())

    # =========== PAYMENTS HANDLERS ===========
    dispatcher.add_handler(get_referral_conversation_handler())
    dispatcher.add_handler(PreCheckoutQueryHandler(payment_handler.pre_checkout_handler))
    dispatcher.add_handler(MessageHandler(filters.get_successful_payment_filter(), payment_handler.successful_payment_callback))

    dispatcher.add_handler(update_referral_conversation_handler())

    # ============ MESSAGE HANDLERS ===========
    dispatcher.add_handler(MessageHandler(filters.get_sport_channel_normal_message_filter(), command_handlers.normal_message_to_abbonati_handler))
    dispatcher.add_handler(MessageHandler(filters.get_cashout_filter(), message_handlers.exchange_cashout_handler))
    dispatcher.add_handler(MessageHandler(filters.get_giocata_filter(), message_handlers.giocata_handler))
    dispatcher.add_handler(MessageHandler(filters.get_teacherbet_giocata_filter(), message_handlers.teacherbet_giocata_handler))
    dispatcher.add_handler(MessageHandler(filters.get_outcome_giocata_filter(), message_handlers.outcome_giocata_handler))
    dispatcher.add_handler(MessageHandler(filters.get_teacherbet_giocata_outcome_filter(), message_handlers.teacherbet_giocata_outcome_handler))
    dispatcher.add_handler(MessageHandler(filters.get_send_file_id_filter(), command_handlers.send_file_id))
    dispatcher.add_handler(MessageHandler(filters.get_broadcast_media_filter(), command_handlers.broadcast_media))
    dispatcher.add_handler(MessageHandler(filters.get_homepage_filter(), message_handlers.homepage_handler))
    dispatcher.add_handler(MessageHandler(filters.get_bot_config_filter(), message_handlers.bot_configuration_handler))
    dispatcher.add_handler(MessageHandler(filters.get_payment_and_referrals_filter(), message_handlers.payment_and_referrals_handler))
    dispatcher.add_handler(MessageHandler(filters.get_experience_settings_filter(), message_handlers.experience_settings_handler))
    dispatcher.add_handler(MessageHandler(filters.get_use_guide_filter(), message_handlers.use_guide_handler))

    # ============ ERROR HANDLERS =============
    dispatcher.add_error_handler(message_handlers.error_handler)

    dispatcher.add_handler(MessageHandler(filters.get_all_filter(), message_handlers.unrecognized_message))



def create_bot():
    """Creates the bot, updater and dispatcher objects that will
    be used in the main.
    As of now, this method should be called by the main entry
    point of the application, only AFTER the config, the 
    logger and the db objects have been created.
    """
    global bot
    global updater
    global dispatcher
    bot = Bot(token=cfg.config.TOKEN)
    updater = Updater(cfg.config.TOKEN)
    dispatcher = updater.dispatcher
    add_handlers(dispatcher)
