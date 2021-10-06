from telegram import Bot
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, MessageHandler,
                          PreCheckoutQueryHandler, Updater)
from telegram.ext.dispatcher import Dispatcher

from lot_bot import config as cfg
from lot_bot import filters
from lot_bot.handlers import (callback_handlers, message_handlers,
                              payment_handler)


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
        entry_points=[CallbackQueryHandler(payment_handler.to_add_referral_before_payment, pattern=r"^to_add_referral$")],
        states={
            payment_handler.REFERRAL: [
                MessageHandler(filters.get_referral_filter(), payment_handler.received_referral),
                CallbackQueryHandler(payment_handler.to_payments, pattern=r"^to_payments$")
                ],
        },
        fallbacks=[
            CallbackQueryHandler(payment_handler.to_homepage_from_referral_callback, pattern=r"^to_homepage_from_referral$"),
            MessageHandler(filters.get_normal_messages_filter(), payment_handler.to_homepage_from_referral_message),
            ],
    )
    return payment_conversation_handler


def add_handlers(dispatcher: Dispatcher):
    """Adds all the bot's handlers to the dispatcher.

    Args:
        dispatcher (Dispatcher)
    """
    # ============ COMMAND HANDLERS ===========
    dispatcher.add_handler(CommandHandler("start", message_handlers.start_command))
    # dispatcher.add_handler(CommandHandler("send_all_videos", message_handlers.send_all_videos_for_file_ids))
    dispatcher.add_handler(CommandHandler("set_user_role", message_handlers.set_user_role))

    # ======= CALLBACK QUERIES HANDLERS =======
    # matches any callback with pattern "sport_<...>"
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.select_sport_strategies, pattern=r"^sport_\w+$"))
    # matches any callback with pattern "<sport>_<strategy>_[activate | disable]"
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.set_sport_strategy_state, pattern=r"^\w+_\w+_(activate|disable)$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_sports_menu, pattern=r"^to_sports_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_homepage, pattern=r"^to_homepage$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.feature_to_be_added, pattern=r"^new$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_links, pattern=r"^links$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_explanations_menu, pattern=r"^to_explanation_menu$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.strategy_explanation, pattern=filters.get_explanation_pattern()))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.accept_register_giocata, pattern=r"^register_giocata_yes$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.refuse_register_giocata, pattern=r"^register_giocata_no$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.to_resoconti, pattern=r"^to_resoconti$"))
    dispatcher.add_handler(CallbackQueryHandler(callback_handlers.last_24_hours_resoconto, pattern=r"^resoconto_24_hours$"))

    
    # =========== PAYMENTS HANDLERS ===========
    dispatcher.add_handler(get_referral_conversation_handler())
    dispatcher.add_handler(PreCheckoutQueryHandler(payment_handler.pre_checkout_handler))
    dispatcher.add_handler(MessageHandler(filters.get_successful_payment_filter(), payment_handler.successful_payment_callback))

    # ============ MESSAGE HANDLERS ===========
    dispatcher.add_handler(MessageHandler(filters.get_cashout_filter(), message_handlers.exchange_cashout_handler))
    dispatcher.add_handler(MessageHandler(filters.get_giocata_filter(), message_handlers.giocata_handler))
    dispatcher.add_handler(MessageHandler(filters.get_outcome_giocata_filter(), message_handlers.outcome_giocata_handler))
    dispatcher.add_handler(MessageHandler(filters.get_sport_channel_normal_message_filter(), message_handlers.normal_message_to_abbonati_handler))
    dispatcher.add_handler(MessageHandler(filters.get_send_file_id_filter(), message_handlers.send_file_id))
    dispatcher.add_handler(MessageHandler(filters.get_homepage_filter(), message_handlers.homepage_handler))

    # ============ ERROR HANDLERS =============
    dispatcher.add_error_handler(message_handlers.error_handler)


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
