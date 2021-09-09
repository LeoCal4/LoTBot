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
    MONGO_DB_URL = "mongodb://localhost:27017/"
    # ====== Add the values of the following variables ====== 
    TOKEN = None # TBA
    


class Testing(Config):
    ENV = "testing"
    TESTING = True
    LOG_ON_FILE = False
    # ====== Add the values of the following variables ====== 
    BOT_TEST_USERNAME = None # TBA
    TOKEN = None # TBA
    MONGO_DB_USER = None # TBA
    MONGO_DB_PSW = None # TBA
    MONGO_DB_NAME = None # TBA
    MONGO_DB_URL = f"mongodb+srv://{MONGO_DB_USER}:{MONGO_DB_PSW}@{MONGO_DB_NAME}<...>" # TBA
    # to get those two, use the following guide
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
        config.MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", None)
        config.TESTING = os.getenv("TESTING", False)
        config.LOG_ON_FILE = os.getenv("LOG_ON_FILE", True)
        config.LOG_PATH = os.getenv("LOG_PATH", None)
        config.CHANNELS_ID = os.getenv("CHANNELS_ID", {})
        config.DEVELOPER_CHAT_IDS = os.getenv("DEVELOPER_CHAT_IDS", [])
    else:
        if ENV == "testing":
            config = Testing()
            print("Testing config created")
        else:
            config = Development()
            print("Dev config created")
