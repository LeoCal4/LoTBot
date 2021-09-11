from telegram.ext import CommandHandler, MessageHandler, Updater
from telegram.ext.dispatcher import Dispatcher

from lot_bot import config as cfg
from lot_bot import database as db
from lot_bot import handlers
from lot_bot import logger as lgr
from lot_bot import filters


def add_handlers(dispatcher: Dispatcher):
    dispatcher.add_handler(CommandHandler("start", handlers.start_command))
    dispatcher.add_handler(MessageHandler(filters.get_giocata_filter(), handlers.handle_giocata))
    dispatcher.add_error_handler(handlers.error_handler)


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


# this represents the default behaviour in case
#   main.py is run
if __name__ == "__main__":
    run_bot_locally()
