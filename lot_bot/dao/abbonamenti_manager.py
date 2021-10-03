from _pytest.python_api import raises
from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.results import InsertOneResult


def create_abbonamento(abbonamento_data : dict) -> bool:
    """Creates an abbonamento using abbonamento_data

    Args:
        abbonamento_data (dict)

    Returns:
        bool: True if the abbonamento was inserted,
            False otherwise
    
    Raises:
        Exception: in case of errors
    """
    try:
        result: InsertOneResult = db.mongo.abbonamenti.insert_one(abbonamento_data)
        lgr.logger.debug(f"Created new abbonamento for user id {abbonamento_data['telegramID']} with data {abbonamento_data}")
        return bool(result.inserted_id)
    except Exception as e:
        if "_id" in abbonamento_data:
            abbonamento_data["_id"] = str(abbonamento_data["_id"])
        lgr.logger.error(f"Error during create abbonamenti - {abbonamento_data=}")
        raise e


def retrieve_abbonamenti(abbonamenti_data: dict) -> list:
    """Retrieves all the abbonamenti according to abbonamenti_data.

    Args:
        abbonamenti_data (dict): the fields can be: "telegramID", "sport", "strategia"

    Returns:
        list: the results obtained

    Raises:
        Exception: in case of errors with db
    """
    try:
        return list(db.mongo.abbonamenti.find(abbonamenti_data))
    except Exception as e:
        lgr.logger.error(f"Error during retrieve abbonamenti - {abbonamenti_data=}")
        raise e 


def retrieve_abbonamento_sport_strategy_from_user_id(user_id: int, sport: str, strategy: str) -> dict:
    """Returns the abbonamento for a certain strategy

    Args:
        user_id (int): [description]
        sport (str): [description]
        strategy (str): [description]

    Returns:
        dict: the dict containing the dati of the abbonamento found (if there was any)
        None: if there was an error or if no abbonamento was found

    Raises:
        Exception: in case of db errors
    """
    try:
        return db.mongo.abbonamenti.find_one({
            "telegramID": user_id,
            "sport": sport, 
            "strategia": strategy,
        })
    except Exception as e:
        lgr.logger.error(f"Error during retrieve sport strategy abbonamento for user id - {user_id=} - {sport=} - {strategy=}")
        raise e


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
        # there may be a case in which a user has no abbonamenti,
        #   so we don't do any check on the result of the operation 
        return True
    except Exception as e:
        lgr.logger.error("Error during delete abbonamenti from user id")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        return False


def delete_all_abbonamenti():
    try:
        db.mongo.abbonamenti.delete_many({})
        return True
    except Exception as e:
        lgr.logger.error("Error during delete all abbonamenti")
        lgr.logger.error(f"Exception: {str(e)}")
        return False
