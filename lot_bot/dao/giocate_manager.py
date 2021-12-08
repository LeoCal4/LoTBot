from json import dumps
from typing import Dict, List, Optional

from lot_bot.models import sports as spr
from lot_bot import custom_exceptions
from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.errors import DuplicateKeyError
from pymongo.results import InsertOneResult, UpdateResult


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


def retrieve_giocate_between_timestamps(max_timestamp: float, min_timestamp: float, include_only_giocate_with_outcome: bool=False) -> List:
    query_filter = {"sent_timestamp": {"$gt": min_timestamp, "$lt": max_timestamp}}
    if include_only_giocate_with_outcome:
        query_filter["outcome"] = {"$ne": "?"}
    try:
        return list(db.mongo.giocate.find(query_filter))
    except Exception as e:
        lgr.logger.error(f"Error during retrieve giocate since timestamp - {max_timestamp=} - {min_timestamp=}")
        raise e


def retrieve_last_n_giocate(num_of_giocate: int, include_only_giocate_with_outcome: bool=False) -> List:
    only_giocate_with_outcome_filter = {}
    if include_only_giocate_with_outcome:
        only_giocate_with_outcome_filter = {"outcome": {"$ne": "?"}}
    try:
        return list(db.mongo.giocate.find(only_giocate_with_outcome_filter).sort([("_id", -1)]).limit(num_of_giocate))
    except Exception as e:
        lgr.logger.error(f"Error during retrieve last n giocate - {num_of_giocate=}")
        raise e


def update_giocata_outcome(sport: str, giocata_num: str, outcome: str) -> bool:
    """Updates the giocata specified by the combination of sport and giocata_num
    with its outcome.

    Args:
        sport (str)
        giocata_num (str)
        outcome (str): either "win", "loss", "void", "abbinata" or "?"

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


def update_exchange_giocata_outcome(giocata_num: str, percentage_outcome: int):
    if percentage_outcome > 0:
        outcome = "win"
    elif percentage_outcome < 0:
        outcome = "loss"
    else:
        outcome = "abbinata"
    try:
        update_result : UpdateResult = db.mongo.giocate.update_one(
            { "sport": spr.sports_container.EXCHANGE.name, "giocata_num": giocata_num },
            { "$set": {"outcome": outcome, "cashout": percentage_outcome} },
            )
        return bool(update_result.modified_count)
    except Exception as e:
        lgr.logger.error(f"Error during update Exchange giocata outcome {giocata_num=} - {percentage_outcome=}")
        raise e
