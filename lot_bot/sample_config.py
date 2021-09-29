import json
import os

from dotenv import load_dotenv

"""This file contains the configuration data used 
    for development and testing.
    Production data needs to be specified in a .env file
    that has to be available only on the server
"""

# this is the variable that will be used to access the config data
# just import this variable in any of the other file which
#   needs it
config = None


class Config(object):
    ENV = None
    TOKEN = None
    PAYMENT_TOKEN = None
    TESTING = False
    SPORTS_CHANNELS_ID = {}
    LOG_ON_FILE = False
    LOG_PATH = "test_log.log"
    DEVELOPER_CHAT_IDS = []
    VIDEO_BASE_PATH = None
    VIDEO_FILE_NAMES = None
    VIDEO_FILE_IDS = None
    VIDEO_FILE_EXTENSIONS = () # has to be a tuple
    MONGO_DB_NAME = None
    MONGO_DB_URL = None
    API_ID = None
    API_HASH = None
    BOT_TEST_USERNAME = None



class Development(Config):
    ENV = "development"
    # ====== Add the values of the following variables ====== 
    SPORTS_CHANNELS_ID = {
        "exchange": 0, # at least exchange must be present
    }
    MONGO_DB_URL = None
    TOKEN = None # TBA
    DEVELOPER_CHAT_IDS = [] # TBA
    VIDEO_BASE_PATH = "" # TBA
    VIDEO_FILE_NAMES = [] # TBA
    VIDEO_FILE_IDS = {} # TBA
    VIDEO_FILE_EXTENSIONS = (".mp4") # TBA
    


class Testing(Config):
    ENV = "testing"
    TESTING = True
    LOG_ON_FILE = False
    # ====== Add the values of the following variables ====== 
    BOT_TEST_USERNAME = None # TBA
    TOKEN = None # TBA
    MONGO_DB_USER = None # TBA
    MONGO_DB_PSW = None # TBA
    MONGO_DB_CLUSTER = None # TBA
    MONGO_DB_NAME = None # TBA
    MONGO_DB_URL = None
    SPORTS_CHANNELS_ID = {} # TBA
    VIDEO_FILE_NAMES = [] # TBA
    VIDEO_FILE_IDS = [] # TBA
    # to get the following two, use the following guide
    # https://core.telegram.org/api/obtaining_api_id#obtaining-api-id
    API_ID = None # TBA
    API_HASH = None # TBA



def create_config():
    """Creates the config object that will be used by all
    the other modules to access config data.
    As of now, this method should be called by the main entry
    point of the application, BEFORE the logger and the db are
    created.
    """
    global config
    print("Creating config")
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
        config.PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN", None)
        config.MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", None)
        config.MONGO_DB_URL = os.getenv("MONGO_DB_URL", None)
        config.TESTING = os.getenv("TESTING", False)
        config.LOG_ON_FILE = os.getenv("LOG_ON_FILE", True)
        config.LOG_PATH = os.getenv("LOG_PATH", None)
        channels_id = os.getenv("SPORTS_CHANNELS_ID", {})
        if channels_id != {}:
            config.SPORTS_CHANNELS_ID = json.loads(channels_id)
            config.SPORTS_CHANNELS_ID = {key: int(value) for key, value in config.SPORTS_CHANNELS_ID.items()}
        dev_chat_ids = os.getenv("DEVELOPER_CHAT_IDS", [])
        if dev_chat_ids != []:
            config.DEVELOPER_CHAT_IDS = json.loads(dev_chat_ids)
            config.DEVELOPER_CHAT_IDS = [int(chat_id) for chat_id in config.DEVELOPER_CHAT_IDS]
        config.VIDEO_FILE_NAMES = os.getenv("VIDEO_FILE_NAMES", [])
        config.VIDEO_FILE_IDS = os.getenv("VIDEO_FILE_IDS", {})
        config.VIDEO_FILE_EXTENSIONS = os.getenv("VIDEO_FILE_EXTENSIONS", ())

    else:
        if ENV == "testing":
            config = Testing()
            print("Testing config created")
        else:
            config = Development()
            print("Dev config created")
