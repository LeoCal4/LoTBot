from json import dumps
from typing import Dict, Optional, List

from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.results import InsertOneResult, UpdateResult


def create_giocata(giocata: Dict) -> Optional[int]:
    """Creates the giocata from the data in the giocata dict.

    Args:
        giocata (Dict)

    Returns:
        int: the _id of the inserted giocata
        None: in case of error
    """
    try:
        result: InsertOneResult = db.mongo.giocate.insert_one(giocata)
        # checks if the inserted id is the one that was passed
        return result.inserted_id
    except Exception as e:
        lgr.logger.error("Error during giocata creation")
        lgr.logger.error(f"Exception: {str(e)}")
        if "_id" in giocata:
            giocata["_id"] = str(giocata["_id"])
        lgr.logger.error(f"Giocata data: {dumps(giocata)}")
        return None


def retrieve_giocata_by_num_and_sport(giocata_num: str, sport: str) -> Optional[Dict]:
    """Retrieves the giocata based on giocata's num and sport,
    since they are unique.

    Args:
        giocata_num: str
        sport: str

    Returns:
        Dict: giocata
        None: in case of error or giocata not found
    """
    lgr.logger.debug(f"Searching for giocata {giocata_num=} - {sport=}")
    try:
        return db.mongo.giocate.find_one({
            "giocata_num": giocata_num,
            "sport": sport
        })
    except Exception as e:
        lgr.logger.error("Error during giocata retrieval")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"Giocata data: {giocata_num=} - {sport=}")
        return None


def retrieve_giocate_from_ids(ids_list: List[int]) -> List[Dict]:
    try:
        return db.mongo.giocate.find({
            "_id": { "$in" : ids_list }
        })
    except Exception as e:
        lgr.logger.error("Error during giocate by ids list retrieval")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"Giocata data: {ids_list}")
        return None


def update_giocata_outcome(sport: str, giocata_num: str, outcome: str) -> bool:
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
        lgr.logger.error("Error during update giocata outcome")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"Giocata data: {sport=} - {giocata_num=} - {outcome=}")
        return None
