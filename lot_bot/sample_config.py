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
    BOT_NAME = None
    TOKEN = None
    PAYMENT_TOKEN = None
    TESTING = False
    SPORTS_CHANNELS_ID = {}
    NEW_USERS_CHANNEL_ID = None
    NEW_PAYMENTS_CHANNEL_ID = None
    TEACHERBET_CHANNEL_ID = None
    WELCOME_DOCUMENT_FILE_ID = None
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
    BOT_NAME = None
    SPORTS_CHANNELS_ID = {
        "exchange": 0, # at least exchange must be present
    }
    TEACHERBET_CHANNEL_ID = None
    MONGO_DB_URL = None
    TOKEN = None # TBA
    DEVELOPER_CHAT_IDS = [] # TBA
    VIDEO_BASE_PATH = "" # TBA
    VIDEO_FILE_NAMES = [] # TBA
    VIDEO_FILE_IDS = {} # TBA
    VIDEO_FILE_EXTENSIONS = (".mp4") # TBA
    NEW_USERS_CHANNEL_ID = None # TBA
    NEW_PAYMENTS_CHANNEL_ID = None # TBA
    TEACHERBET_CHANNEL_ID = None # TBA
    WELCOME_DOCUMENT_FILE_ID = None # TBA
    


class Testing(Config):
    ENV = "testing"
    TESTING = True
    LOG_ON_FILE = False
    # ====== Add the values of the following variables ====== 
    BOT_NAME = None # TBA
    BOT_TEST_USERNAME = None # TBA
    TOKEN = None # TBA
    MONGO_DB_USER = None # TBA
    MONGO_DB_PSW = None # TBA
    MONGO_DB_CLUSTER = None # TBA
    MONGO_DB_NAME = None # TBA
    MONGO_DB_URL = None
    SPORTS_CHANNELS_ID = {} # TBA
    TEACHERBET_CHANNEL_ID = None # TBA
    VIDEO_FILE_NAMES = [] # TBA
    VIDEO_FILE_IDS = [] # TBA
    WELCOME_DOCUMENT_FILE_ID = None # TBA
    # to get the following two, use the following guide
    # https://core.telegram.org/api/obtaining_api_id#obtaining-api-id
    API_ID = None # TBA
    API_HASH = None # TBA



def load_env_variables():
    global config
    config = Config()
    config.TOKEN = os.getenv("TOKEN", None) # gcloud secret
    config.PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN", None) # gcloud secret
    config.MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", None) # gcloud secret
    config.MONGO_DB_URL = os.getenv("MONGO_DB_URL", None) # gcloud secret
    config.BOT_NAME = os.getenv("BOT_NAME", None)
    config.TESTING = os.getenv("TESTING", False)
    config.LOG_ON_FILE = os.getenv("LOG_ON_FILE", True)
    config.LOG_PATH = os.getenv("LOG_PATH", None)

    config.NEW_USERS_CHANNEL_ID = os.getenv("NEW_USERS_CHANNEL_ID", None)
    if not config.NEW_USERS_CHANNEL_ID is None:
        config.NEW_USERS_CHANNEL_ID = int(config.NEW_USERS_CHANNEL_ID)

    config.NEW_PAYMENTS_CHANNEL_ID = os.getenv("NEW_PAYMENTS_CHANNEL_ID", None)
    if not config.NEW_PAYMENTS_CHANNEL_ID is None:
        config.NEW_PAYMENTS_CHANNEL_ID = int(config.NEW_PAYMENTS_CHANNEL_ID)

    channels_id = os.getenv("SPORTS_CHANNELS_ID", {})
    if channels_id != {}:
        config.SPORTS_CHANNELS_ID = json.loads(channels_id)
        config.SPORTS_CHANNELS_ID = {key: int(value) for key, value in config.SPORTS_CHANNELS_ID.items()}

    dev_chat_ids = os.getenv("DEVELOPER_CHAT_IDS", [])
    if dev_chat_ids != []:
        config.DEVELOPER_CHAT_IDS = json.loads(dev_chat_ids)
        config.DEVELOPER_CHAT_IDS = [int(chat_id) for chat_id in config.DEVELOPER_CHAT_IDS]

    config.TEACHERBET_CHANNEL_ID = os.getenv("TEACHERBET_CHANNEL_ID", None)
    if not config.TEACHERBET_CHANNEL_ID is None:
        config.TEACHERBET_CHANNEL_ID = int(config.TEACHERBET_CHANNEL_ID)
        
    config.VIDEO_FILE_NAMES = os.getenv("VIDEO_FILE_NAMES", [])
    config.VIDEO_FILE_IDS = os.getenv("VIDEO_FILE_IDS", {})
    config.VIDEO_FILE_EXTENSIONS = os.getenv("VIDEO_FILE_EXTENSIONS", ())

    config.WELCOME_DOCUMENT_FILE_ID = os.getenv("WELCOME_DOCUMENT_FILE_ID", "")


def create_config():
    """Creates the config object that will be used by all
    the other modules to access config data.
    As of now, this method should be called by the main entry
    point of the application, BEFORE the logger and the db are
    created.
    """
    global config
    print("Creating config")

    # to load an env variable, use os.getenv("NAME", default)
    #   if the "NAME" variable is not present in the environment, 
    #   the default value will be used
    ENV = os.getenv("ENV", "development")

    # if the .env file exists, load vars from there
    #   (this should happen only for production and staging)
    if ENV == "dotenv":
        # dotenv handles the .env file, which we can use to store
        #  environmental variables needed for the application
        # this next line loads the variables stored in the .env file
        load_dotenv()
        load_env_variables()
        print("Production config created")
    elif ENV == "staging":
        load_dotenv("staging.env")
        load_env_variables()
        print("Staging config created")
    elif ENV == "testing":
        config = Testing()
        print("Testing config created")
    else:
        config = Development()
        print("Dev config created")
