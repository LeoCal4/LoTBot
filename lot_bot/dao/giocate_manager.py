from json import dumps
from typing import Dict, Optional, List

from lot_bot import database as db
from lot_bot import logger as lgr
from lot_bot import custom_exceptions
from pymongo.results import InsertOneResult, UpdateResult
from pymongo.errors import DuplicateKeyError


def create_giocata(giocata: Dict) -> Optional[int]:
    """Creates the giocata from the data in the giocata dict.

    Args:
        giocata (Dict)

    Returns:
        int: the _id of the inserted giocata

    Raises:
        GiocataCreationError: in case of a DuplicateKeyError
        Exception: in case there was another error with the db
    """
    try:
        result: InsertOneResult = db.mongo.giocate.insert_one(giocata)
        # checks if the inserted id is the one that was passed
        return result.inserted_id
    except DuplicateKeyError:
        if "_id" in giocata:
            giocata["_id"] = str(giocata["_id"])
        lgr.logger.error(f"Giocata has a duplicate key - {dumps(giocata)}")
        raise custom_exceptions.GiocataCreationError
    except Exception as e:
        if "_id" in giocata:
            giocata["_id"] = str(giocata["_id"])
        lgr.logger.error(f"Error during giocata creation - {dumps(giocata)}")
        raise e


def retrieve_giocata_by_num_and_sport(giocata_num: str, sport: str) -> Optional[Dict]:
    """Retrieves the giocata based on giocata's num and sport,
    since they are unique.

    Args:
        giocata_num: str
        sport: str

    Returns:
        Dict: giocata
        None: in case of  giocata not found

    Raises:
        Exception: in case of db errors
    """
    lgr.logger.debug(f"Searching for giocata {giocata_num=} - {sport=}")
    try:
        return db.mongo.giocate.find_one({
            "giocata_num": giocata_num,
            "sport": sport
        })
    except Exception as e:
        lgr.logger.error(f"Error during giocata retrieval - {giocata_num=} - {sport=}")
        raise e


def retrieve_giocate_from_ids(ids_list: List[int]) -> List[Dict]:
    """Retrieves all the giocate specified by the ids in the list.

    Args:
        ids_list (List[int])

    Raises:
        e: in case of db errors

    Returns:
        List[Dict]: the retrieved giocate
    """
    try:
        return list(db.mongo.giocate.find({
            "_id": { "$in" : ids_list }
        }))
    except Exception as e:
        lgr.logger.error(f"Error during giocate by ids list retrieval - {ids_list=}")
        raise e


def update_giocata_outcome(sport: str, giocata_num: str, outcome: str) -> bool:
    """Updates the giocata specified by the combination of sport and giocata_num
    with its outcome.

    Args:
        sport (str)
        giocata_num (str)
        outcome (str): either "win", "loss" or "?"

    Raises:
        e: in case of db errors

    Returns:
        bool: True if the outcome was updated, False otherwise
    """
    try:
        update_result: UpdateResult =  db.mongo.giocate.update_one({
                "sport": sport,
                "giocata_num": giocata_num
            },
            {
                "$set": {"outcome": outcome}
            }
        )
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during update giocata outcome {sport=} - {giocata_num=} - {outcome=}")
        raise e
