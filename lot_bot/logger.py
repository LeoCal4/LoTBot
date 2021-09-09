import logging

from lot_bot import config as cfg

# this is the variable that will be used to write on logs
# just import this variable in any of the other file which
#   needs it
logger = None

def create_logger():
    """Creates the logger object that is used on the whole app.
    It can be set up to write on files or on the console.
    As of now, this method should be called by the main entry
    point of the application, only AFTER the config object
    has been created.
    Logging setup:
     - filename: the path on which the logs are saved
     - encoding: the encoding of the logs
     - format:   the structure of the log messages
     - level:    the types of the log messages that will be written
                    in the logs
    Returns:
        logging.Logger
    """
    global logger
    logger_level = logging.INFO if cfg.config.ENV != "development" else logging.DEBUG
    if cfg.config.LOG_ON_FILE:
        logging.basicConfig(
            filename=cfg.config.LOG_PATH,
            encoding="utf-8", 
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logger_level)
    else:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logger_level)
    logger = logging.getLogger(__name__)
