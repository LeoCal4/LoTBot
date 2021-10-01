from pymongo import MongoClient

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
                maxPoolsize=4 # TODO check this
            )
            # The ping command is cheap and does not require auth, 
            #   so it is run to check if the db is active
            self.client.admin.command("ping")
        except Exception as e:
            lgr.logger.error(f"Error creating DB: {str(e)} - {cfg.config.MONGO_DB_URL=}")
            raise Exception
        lgr.logger.info("Connected to db") 
        db = self.client[cfg.config.MONGO_DB_NAME]
        self.abbonamenti = db["abbonamenti"]
        # ensures the uniqueness of the abbonamenti
        self.abbonamenti.create_index([("telegramID", 1), ("sport", 1), ("strategia", 1)], unique=True)
        self.utenti = db["utenti"]
        # ensures the uniqueness of the users' referral codes
        self.utenti.create_index([("referral_code", 1)], unique=True)
        self.giocate = db["giocate"]
        # ensures the uniqueness of the giocata_num together with sport
        self.giocate.create_index([("giocata_num", 1), ("sport", 1)], unique=True)


def create_db():
    """Creates the db object that will be used in the other modules.
    As of now, this method should be called by the main entry
    point of the application, only AFTER the config and the 
    logger objects have been created.
    """
    global mongo
    mongo = MongoDatabase()
