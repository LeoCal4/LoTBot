from json import dumps
from typing import Dict, Optional, List

from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.results import InsertOneResult


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


def retrieve_giocata(giocata: Dict) -> Optional[Dict]:
    """Retrieves the giocata based on giocata's num and sport,
    since they are unique.

    Args:
        giocata (Dict)

    Returns:
        Dict: giocata
        None: in case of error or giocata not found
    """
    giocata_num = giocata["giocata_num"]
    sport = giocata["sport"]
    lgr.logger.warning(f"{giocata_num=} - {sport=}")
    try:
        return db.mongo.giocate.find_one({
            "giocata_num": giocata_num,
            "sport": sport
        })
    except Exception as e:
        lgr.logger.error("Error during giocata retrieval")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"Giocata data: {dumps(giocata)}")
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

