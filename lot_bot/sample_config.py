import os

from dotenv import load_dotenv

"""This file contains the configuration data used 
    for development and testing.
    Production data needs to be specified in a .env file
    that has to be available only on the server
"""


class Config(object):
    ENV = None
    TOKEN = None
    TESTING = False
    CHANNELS_ID = {}
    LOG_ON_FILE = False
    LOG_PATH = "test_log.log"
    DEVELOPER_CHAT_IDS = []
    API_ID = None
    API_HASH = None
    BOT_TEST_USERNAME = None



class Development(Config):
    ENV = "development"
    TOKEN = None # test bot token
    MONGO_DB_NAME = None # test db name
    


class Testing(Config):
    ENV = "testing"
    TESTING = True
    TOKEN = None # test bot token
    MONGO_DB_NAME = None # test db name
    LOG_ON_FILE = False
    BOT_TEST_USERNAME = None
    API_ID = None
    API_HASH = None
    DEVELOPER_CHAT_IDS = []



def create_config() -> Config:
    # dotenv handles the .env file, which we can use to store
    #  environmental variables needed for the application
    # this next line loads the variables stored in the .env file
    load_dotenv()

    # to load an env variable, use os.getenv("NAME", default)
    #   if the "NAME" variable is not present in the environment, 
    #   the default value will be used
    ENV = os.getenv("ENV", False)

    # if the .env file exists, load vars from there
    #   (this should happen only for production)
    if ENV == "dotenv":
        config = Config()
        config.TOKEN = os.getenv("TOKEN", None)
        config.MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", None)
        config.TESTING = os.getenv("TESTING", False)
        config.LOG_ON_FILE = os.getenv("LOG_ON_FILE", True)
        config.LOG_PATH = os.getenv("LOG_PATH", None)
        config.CHANNELS_ID = os.getenv("CHANNELS_ID", {})
        config.DEVELOPER_CHAT_IDS = os.getenv("DEVELOPER_CHAT_IDS", [])
    else:
        if ENV == "testing":
            config = Testing()
        else:
            config = Development()
    return config


config = create_config()
