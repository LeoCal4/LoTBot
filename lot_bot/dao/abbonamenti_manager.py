from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


def create_abbonamenti(abbonamenti_data : dict) -> bool:
    try:
        result: InsertOneResult = db.mongo.abbonamenti.insert_one(abbonamenti_data)
        lgr.logger.info(f"Created new abbonamento for user id {abbonamenti_data['telegramID']}")
        return bool(result.inserted_id)
    except Exception as e:
        lgr.logger.error("Error during create abbonamenti")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"{abbonamenti_data=}")
        return False


def retrieve_abbonamenti_from_user_id(user_id: int) -> list:
    """Retrieves all the abbonamenti of the user identified
        by the user_id

    Args:
        user_id (int)

    Returns:
        list: a list of the user's abbonamenti 
        None: if no abbonamenti were found or if there was an error
    """
    try:
        return db.mongo.abbonamenti.find({"telegramID": user_id})
    except Exception as e:
        lgr.logger.error("Error during retrieve abbonamenti from user id")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        return None 


def retrieve_abbonamenti_from_sport_strategy(sport: str, strategy: str) -> list:
    """Retrieves all the abbonamenti for the specified sport strategy.

    Args:
        sport (str)
        strategy (str)

    Returns:
        list: a list of abbonamenti
        None: if no abbonamenti were found or if there was an error
    """
    try:
        return db.mongo.abbonamenti.find({
            "sport": sport,
            "strategia": strategy
        })
    except Exception as e:
        lgr.logger.error("Error during retrieve abbonamenti from sport and strategy")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"{sport=} - {strategy=}")
        return None


def delete_abbonamenti_for_user_id(user_id: int) -> bool:
    """Deletes all the abbonamenti of the user identified
        by the user_id

    Args:
        user_id (int)
    
    Returns:
        bool: True if the operation was successful,
            False otherwise
    """
    try:
        db.mongo.abbonamenti.delete_many({"telegramID": user_id})
        # there may be a case in which a user has not abbonamenti,
        #   so we don't do any check on the result of the operation 
        return True
    except Exception as e:
        lgr.logger.error("Error during delete abbonamenti from user id")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        return False

