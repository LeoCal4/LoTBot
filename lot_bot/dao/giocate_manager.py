from json import dumps
from typing import Dict, List, Optional

from lot_bot import custom_exceptions
from lot_bot import database as db
from lot_bot import logger as lgr
from lot_bot.models import sports as spr
from pymongo.collection import ReturnDocument
from pymongo.errors import DuplicateKeyError
from pymongo.results import InsertOneResult


def create_giocata(giocata: Dict) -> Optional[int]:
    """Creates the giocata from the data in the giocata dict.

    Args:
        giocata (Dict)

    Returns:
        int: the _id of the inserted giocata

    Raises:
        GiocataCreationError: in case of a DuplicateKeyError
        e (Exception): in case there was another error with the db
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
        e (Exception): in case of db errors
    """
    lgr.logger.debug(f"Searching for giocata {giocata_num=} - {sport=}")
    try:
        return db.mongo.giocate.find_one({ "giocata_num": giocata_num, "sport": sport })
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


def update_giocata_outcome_and_get_giocata(sport: str, giocata_num: str, outcome: str) -> Optional[Dict]:
    """Updates the giocata specified by the combination of sport and giocata_num
    with its outcome, returning it if it was found.

    Args:
        sport (str)
        giocata_num (str)
        outcome (str): either "win", "loss" or "?"

    Raises:
        e: in case of db errors

    Returns:
        Dict: the updated giocata if the outcome was updated, None otherwise
    """
    try:
        found_giocata : Dict =  db.mongo.giocate.find_one_and_update(
            { "sport": sport, "giocata_num": giocata_num },
            { "$set": {"outcome": outcome} },
            return_document=ReturnDocument.AFTER
        )
        if found_giocata and found_giocata["outcome"] != outcome:
            found_giocata = None
        return found_giocata
    except Exception as e:
        lgr.logger.error(f"Error during update giocata outcome {sport=} - {giocata_num=} - {outcome=}")
        raise e


def update_exchange_giocata_outcome_and_get_giocata(giocata_num: str, percentage_outcome: int) -> Optional[Dict]:
    """Updates the outcome of the exchange giocata, along with its cashout, and returns
    the updated giocata if the previous operations were successful.

    Args:
        giocata_num (str)
        percentage_outcome (int)

    Raises:
        e: in case of db errors

    Returns:
        Optional[Dict]: the updated giocata if it was updated, None otherwise or if it was not found
    """
    if percentage_outcome > 0:
        outcome = "win"
    elif percentage_outcome < 0:
        outcome = "loss"
    else:
        outcome = "abbinata"
    try:
        updated_giocata = db.mongo.giocate.find_one_and_update(
            { "sport": spr.sports_container.EXCHANGE.name, "giocata_num": giocata_num },
            { "$set": {"outcome": outcome, "cashout": percentage_outcome} },
            return_document=ReturnDocument.AFTER
            )
        if updated_giocata["outcome"] != outcome:
            updated_giocata = None
        return updated_giocata
    except Exception as e:
        lgr.logger.error(f"Error during update Exchange giocata outcome {giocata_num=} - {percentage_outcome=}")
        raise e


def delete_giocata(giocata_id):
    try:
        db.mongo.giocate.delete_one({"_id": giocata_id})
        return True
    except Exception as e:
        lgr.logger.error(f"Error during giocata deletion {giocata_id=}")
        raise e
