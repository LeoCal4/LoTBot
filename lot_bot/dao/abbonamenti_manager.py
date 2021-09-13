from pymongo.uri_parser import _TLSINSECURE_EXCLUDE_OPTS
from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


def create_abbonamento(abbonamento_data : dict) -> bool:
    """Creates an abbonamento using abbonamento_data

    Args:
        abbonamento_data (dict)

    Returns:
        bool: True if the abbonamento was inserted,
            False otherwise
    """
    try:
        result: InsertOneResult = db.mongo.abbonamenti.insert_one(abbonamento_data)
        lgr.logger.info(f"Created new abbonamento for user id {abbonamento_data['telegramID']}")
        return bool(result.inserted_id)
    except Exception as e:
        lgr.logger.error("Error during create abbonamenti")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"{abbonamento_data=}")
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
        return list(db.mongo.abbonamenti.find({"telegramID": user_id}))
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
        return list(db.mongo.abbonamenti.find({
            "sport": sport,
            "strategia": strategy
        }))
    except Exception as e:
        lgr.logger.error("Error during retrieve abbonamenti from sport and strategy")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"{sport=} - {strategy=}")
        return None


def retrieve_abbonamenti_sport_from_user_id(user_id: int, sport: str) -> list:
    """Returns all the abbonamenti of a certain sport for the 
    specified user_id.

    Args:
        user_id (int)
        sport (str)

    Returns:
        list: the list of abbonamenti found 
        None: in case there is an error
    """
    try:
        return list(db.mongo.abbonamenti.find({
            "telegramID": user_id,
            "sport": sport, 
        }))
    except Exception as e:
        lgr.logger.error("Error during retrieve sport abbonamenti for user id")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"{user_id=} - {sport=}")
        return None


def retrieve_abbonamento_sport_strategy_from_user_id(user_id: int, sport: str, strategy: str) -> list:
    """Returns the abbonamento for a certain strategy

    Args:
        user_id (int): [description]
        sport (str): [description]
        strategy (str): [description]

    Returns:
        list: the list containing the abbonamento found (if there was any)
        None: if there was an error
    """
    try:
        return list(db.mongo.abbonamenti.find({
            "telegramID": user_id,
            "sport": sport, 
            "strategia": strategy,
        }))
    except Exception as e:
        lgr.logger.error("Error during retrieve sport strategy abbonamento for user id")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"{user_id=} - {sport=} - {strategy=}")
        return None


def delete_abbonamento(abbonamento_data: dict) -> bool:
    """Deletes any abbonamento with data equal to abbonamento_data.

    Args:
        abbonamento_data (dict)

    Returns:
        bool: True if the operation was successful,
            Falso otherwise
    """
    try:
        db.mongo.abbonamenti.delete_many(abbonamento_data)
        return True
    except Exception as e:
        lgr.logger.error("Error during delete abbonamento")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"{abbonamento_data=}")
        return False


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

