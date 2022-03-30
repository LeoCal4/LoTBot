from telegram import Update

from lot_bot import bot
from lot_bot import config as cfg
from lot_bot import database as db
from lot_bot import logger as lgr
from lot_bot import languages as lang


def run_bot_locally():
    cfg.create_config()
    lgr.create_logger()
    lgr.logger.info("Starting bot locally")
    if not cfg.config.TOKEN:
        lgr.logger.error("ERROR: TOKEN not valid")
        raise Exception("No config TOKEN")
    db.create_db()
    bot.create_bot()
    lang.update_language("en")
    lgr.logger.info("Start polling")
    bot.updater.start_polling(timeout=15.0)
    bot.updater.idle()


def check_components():
    """Checks if config, logger, db and bot are up and running,
    creating them again if needed"""
    if not cfg.config:
        cfg.create_config()
    if not lgr.logger:
        lgr.create_logger()
        lgr.logger.info("Logger object created")
    if not db.mongo:
        db.create_db()
        lgr.logger.info("DB object created")
    if not bot.bot or not bot.updater:
        bot.create_bot()
        lgr.logger.info("Bot object created")


def staging_webhook(request):
    """Staging webhook function which will be called at each test bot request.

    Args:
        request: the Flask request object containing the request 

    Returns:
        str
    """
    check_components()
    if request.method != "POST":
        lgr.logger.error(f"Staging bot received {request.method} request")
        return
    update = Update.de_json(request.get_json(force=True), bot.bot)
    bot.dispatcher.process_update(update)
    return "Ok"


def webhook(request):
    """Webhook function which will be called at each bot request.

    Args:
        request: the Flask request object containing the request 

    Returns:
        str
    """
    check_components()
    if request.method != "POST":
        lgr.logger.error(f"Bot received {request.method} request")
        return
    update = Update.de_json(request.get_json(force=True), bot.bot)
    bot.dispatcher.process_update(update)
    return "Ok"


# this represents the default behaviour in case
#   main.py is run
if __name__ == "__main__":
    run_bot_locally()
