from telegram import Bot
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, MessageHandler,
                          PreCheckoutQueryHandler, Updater)
from telegram.ext.dispatcher import Dispatcher

from lot_bot import config as cfg
from lot_bot import filters
from lot_bot.handlers import (callback_handlers, message_handlers,
                              payment_handler, ref_code_handlers, 
                              command_handlers)


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


def add_handlers(dispatcher: Dispatcher):
    """Adds all the bot's handlers to the dispatcher.

    Args:
        dispatcher (Dispatcher)
    """
    # ================ COMMAND HANDLERS ================
    dispatcher.add_handler(CommandHandler("start", command_handlers.start_command))
    dispatcher.add_handler(CommandHandler("broadcast", command_handlers.broadcast_handler))
    # ------------ Users managing commands --------------
    dispatcher.add_handler(CommandHandler("aggiungi_giorni", command_handlers.aggiungi_giorni))
    dispatcher.add_handler(CommandHandler("resoconto_utente", command_handlers.get_user_resoconto))
    dispatcher.add_handler(CommandHandler("modifica_referral", ref_code_handlers.update_user_ref_code_handler))
    dispatcher.add_handler(CommandHandler("cambia_ruolo", command_handlers.set_user_role))
    dispatcher.add_handler(CommandHandler("blocca_utente", command_handlers.block_messages_to_user))
    dispatcher.add_handler(CommandHandler("sblocca_utente", command_handlers.unlock_messages_to_user))
    # ------------ Trend commands --------------
    dispatcher.add_handler(CommandHandler("trend_giorni", command_handlers.get_trend_by_days))
    dispatcher.add_handler(CommandHandler("trend_eventi", command_handlers.get_trend_by_events))
    # ------------ Personal stake commands --------------
    dispatcher.add_handler(CommandHandler("crea_stake", command_handlers.create_personal_stake))
    dispatcher.add_handler(CommandHandler("visualizza_stake", command_handlers.visualize_personal_stakes))
    dispatcher.add_handler(CommandHandler("elimina_stake", command_handlers.delete_personal_stakes))


    # ======= CALLBACK QUERIES HANDLERS =======
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_homepage, pattern=r"^to_homepage$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_bot_config_menu, pattern=r"^to_bot_config_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_experience_menu, pattern=r"^to_experience_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_use_guide_menu, pattern=r"^to_use_guide_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.select_sport_strategies, pattern=r"^sport_\w+$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.set_sport_strategy_state, pattern=r"^\w+_\w+_(activate|disable)$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_sports_menu, pattern=r"^to_sports_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_explanations_menu, pattern=r"^to_explanation_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_gestione_budget_menu, pattern=r"^to_gestione_budget_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_social_menu, pattern=r"^to_social_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_service_status, pattern=r"^to_service_status$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_strat_expl_menu, pattern=r"^to_strat_expl_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.strategy_explanation, pattern=filters.get_explanation_pattern())) 
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.strategy_text_explanation, pattern=filters.get_strat_text_explanation_pattern())) #related to text explanations (not video!)
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.accept_register_giocata, pattern=r"^register_giocata_yes$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.refuse_register_giocata, pattern=r"^register_giocata_no$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_resoconti, pattern=r"^to_resoconti$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_referral, pattern=r"^to_referral$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.last_24_hours_resoconto, pattern=r"^resoconto_24_hours$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.last_7_days_resoconto, pattern=r"^resoconto_7_days$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.last_30_days_resoconto, pattern=r"^resoconto_30_days$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.feature_to_be_added, pattern=r"^new$"))

    
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
