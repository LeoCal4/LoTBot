from telegram.ext import CommandHandler, Updater

from lot_bot import config as cfg
from lot_bot import database as db
from lot_bot import logger as lgr
from lot_bot.handlers import error_handler, fake_command_handler, start_command


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
    dispatcher.add_handler(CommandHandler("test", fake_command_handler))
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_error_handler(error_handler)
    lgr.logger.info("Start polling")
    updater.start_polling(timeout=15.0)
    updater.idle()


def run_test_bot():
    cfg.create_config()
    print(f"{cfg.config.ENV=}")
    print("Aaoooooooooo")
    lgr.create_logger()
    lgr.logger.info("Starting bot locally")
    if not cfg.config.TOKEN:
        lgr.logger.error("ERROR: TOKEN not valid")
        raise Exception("No config TOKEN")
    db.create_db()
    updater = Updater(cfg.config.TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("test", fake_command_handler))
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_error_handler(error_handler)
    lgr.logger.info("Start polling")
    updater.start_polling(timeout=15.0)
    updater.idle()


# this represents the default behaviour in case
#   main.py is run
if __name__ == "__main__":
    run_bot_locally()
