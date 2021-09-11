from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from lot_bot import config as cfg
from lot_bot import logger as lgr


# the mongo object that is used in the other modules
# just import this variable in any of the other file which
#   needs to access the db (theorically only DAOs)
mongo = None

class MongoDatabase:
    """Wrapper for the db object
    """
    def __init__(self):
        try:
            self.client = MongoClient(
                cfg.config.MONGO_DB_URL,
                maxPoolsize=1 # TODO check this
            )
            # The ping command is cheap and does not require auth, 
            #   so it is run to check if the db is active
            self.client.admin.command("ping")
        except ConnectionFailure:
            lgr.logger.error(f"Error creating DB: server not available - {cfg.config.MONGO_DB_URL=}")
            raise Exception
        lgr.logger.info("Connected to db") 
        db = self.client[cfg.config.MONGO_DB_NAME]
        self.abbonamenti = db["abbonamenti2"]
        self.canaliConReportInCorso = db["canaliConReportInCorso"]
        self.utenti = db["utenti2"]
        self.inlineGiocate = db["inlineGiocate2"]
        self.messaggiUpdateID = db["updateID2"]


def create_db():
    """Creates the db object that will be used in the other modules.
    As of now, this method should be called by the main entry
    point of the application, only AFTER the config and the 
    logger objects have been created.
    """
    global mongo
    mongo = MongoDatabase()
    # else:
    #     import mongomock
    #     db = mongomock.MongoClient().client
    # return db
