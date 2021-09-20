import datetime
from json import dumps

from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


def create_user(user_data: dict) -> bool:
    """Creates a user using the data found in user_data

    Args:
        user_data (dict)

    Returns:
        bool: True if the user was created,
            False otherwise
    """
    # TODO add user data validation
    #   https://docs.mongodb.com/manual/core/schema-validation/
    # https://stackoverflow.com/questions/46569262/does-pymongo-have-validation-rules-built-in/51520384
    try:
        result: InsertOneResult = db.mongo.utenti.insert_one(user_data)
        # checks if the inserted id is the one that was passed
        return result.inserted_id == user_data["_id"]
    except Exception as e:
        lgr.logger.error("Error during user creation")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User data: {dumps(user_data)}")
        return False



def retrieve_user(user_id: int) -> dict:
    """Retrieve the user specified by user_id

    Args:
        user_id (int)

    Returns:
        dict: the user data 
        None: if no user was found or if there was an error
    """
    try:
        return db.mongo.utenti.find_one({"_id": user_id})
    except Exception as e:
        lgr.logger.error("Error during user retrieval")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        return None


def update_user(user_id: int, user_data: dict) -> bool:
    """Updates the user specified by the user_id,
        using the data found in user_data

    Args:
        user_id (int)
        user_data (dict)
    
    Returns:
        bool: True if the user was updated,
            False otherwise
    """
    try:
        # TODO add document fields validation 
        update_result: UpdateResult = db.mongo.utenti.update_one({
            "_id": user_id,
            },
            {
                "$set": user_data
            }
        )
        # this will be true if there was at least a match
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error("Error during user update")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        lgr.logger.error(f"User data: {dumps(user_data)}")
        return False


def register_giocata_for_user_id(giocata: dict, user_id: int) -> bool:
    try:
        # TODO add document fields validation 
        # TODO check if it is already present
        lgr.logger.debug(f"Registering {giocata=} for {user_id=}")
        update_result: UpdateResult = db.mongo.utenti.update_one(
            {
                "_id": user_id,
            },
            {
                "$push": {
                    "giocate": giocata
                }
            }
        )
        # this will be true if there was at least a match
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error("Error during giocata registration")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        lgr.logger.error(f"User data: {dumps(giocata)}")
        return False


def delete_user(user_id: int) -> bool:
    """Deletes the user specified by user_id

    Args:
        user_id (int)
    
    Returns: True if the user was deleted,
        False otherwise
    """
    try:
        result: DeleteResult = db.mongo.utenti.delete_one({"_id": user_id})
        return bool(result.deleted_count)
    except Exception as e:
        lgr.logger.error("Error during user deletion")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        return False


def check_user_validity(message_date: datetime.datetime, user_data: dict) -> bool:
    """Checks if the user subscription is still valid.

    Args:
        message_date (datetime): the date of the message being checked


    Returns:
        bool: True if the the user's subscription is still valid, 
            False otherwise
    """
    return float(user_data["validoFino"]) > message_date.timestamp()
