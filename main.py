from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, Updater
from telegram.ext.dispatcher import Dispatcher
from telegram import Bot, Update

from lot_bot import config as cfg
from lot_bot import database as db
from lot_bot.handlers import callback_handlers, message_handlers 
from lot_bot import logger as lgr
from lot_bot import filters


def add_handlers(dispatcher: Dispatcher):
    """Adds all the bot's handlers to the dispatcher.

    Args:
        dispatcher (Dispatcher)
    """
    # ============ COMMAND HANDLERS ===========
    dispatcher.add_handler(CommandHandler("start", message_handlers.start_command))
    dispatcher.add_handler(CommandHandler("send_all_videos", message_handlers.send_all_videos_for_file_ids))

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

    # ============ MESSAGE HANDLERS ===========
    dispatcher.add_handler(MessageHandler(filters.get_cashout_filter(), message_handlers.exchange_cashout_handler))
    dispatcher.add_handler(MessageHandler(filters.get_giocata_filter(), message_handlers.giocata_handler))
    dispatcher.add_handler(MessageHandler(filters.get_sport_channel_normal_message_filter(), message_handlers.sport_channel_normal_message_handler))
    dispatcher.add_handler(MessageHandler(filters.get_homepage_filter(), message_handlers.homepage_handler))
    # this has to be the last one, since they are checked in the same order they are added
    dispatcher.add_handler(MessageHandler(filters.get_normal_messages_filter(), message_handlers.first_message_handler))

    # ============ ERROR HANDLERS =============
    dispatcher.add_error_handler(message_handlers.error_handler)


def run_bot_locally():
    cfg.create_config()
    lgr.create_logger()
    lgr.logger.info("Starting bot locally")
    if not cfg.config.TOKEN:
        lgr.logger.error("ERROR: TOKEN not valid")
        raise Exception("No config TOKEN")
    db.create_db()
    updater = Updater(cfg.config.TOKEN)
    dispatcher = updater.dispatcher
    add_handlers(dispatcher)
    lgr.logger.info("Start polling")
    updater.start_polling(timeout=15.0)
    updater.idle()


def run_test_bot():
    cfg.create_config()
    lgr.create_logger()
    lgr.logger.info("Starting bot locally for tests")
    if not cfg.config.TOKEN:
        lgr.logger.error("ERROR: TOKEN not valid")
        raise Exception("No config TOKEN")
    db.create_db()
    updater = Updater(cfg.config.TOKEN)
    dispatcher = updater.dispatcher
    add_handlers(dispatcher)
    lgr.logger.info("Start polling")
    updater.start_polling(timeout=15.0)
    updater.idle()


def check_components():
    """Checks if config, logger, db and bot are up and running,
    creating them again if needed"""
    if not cfg.config:
        cfg.create_config(),
    if not lgr.logger:
        lgr.create_logger()
    if not db.mongo:
        db.create_db()
    # TODO add bot


def webhook(request):
    """Webhook function which will be called at each bot request.

    Args:
        request: the Flask request object containing the request 

    Returns:
        str
    """
    if request.method != "POST":
        return
    check_components()
    bot = Bot(token=cfg.config.TOKEN)
    updater: Updater = Updater(cfg.config.TOKEN)
    dispatcher = updater.dispatcher
    add_handlers(dispatcher)

    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "Ok"
    


# this represents the default behaviour in case
#   main.py is run
if __name__ == "__main__":
    run_bot_locally()
