import datetime
from json import dumps
from typing import Dict, Optional, List, Union
from dateutil.relativedelta import relativedelta

from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.collection import ReturnDocument
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


def check_checklist_completion(user_id: int) -> bool:
    try:
        checklist_fields = db.mongo.analytics.find_one({"_id": user_id}, {
            "has_modified_referral", 
            "accepted_giocate",
        })
        has_completed_checklist = checklist_fields["has_modified_referral"]
        has_completed_checklist = len(checklist_fields["accepted_giocate"]) > 0 and has_completed_checklist
        if has_completed_checklist:
            update_analytics(user_id, {"has_completed_checklist": True})
            # add 2 days and send message 
    except Exception as e:
        lgr.logger.error("Error during checklist completion check")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        return None

def create_analytics(analytics_data: Dict) -> bool:
    """Creates a user analytics' data container using the data found in analytics_data

    Args:
        analytics_data (Dict)

    Raises:
        e (Exception): in case there is a db error

    Returns:
        bool: True if the user analytics' data container was created,
            False otherwise
    """
    try:
        result: InsertOneResult = db.mongo.analytics.insert_one(analytics_data)
        return result.inserted_id == analytics_data["_id"]
    except Exception as e:
        if "_id" in analytics_data:
            analytics_data["_id"] = str(analytics_data["_id"])
        lgr.logger.error(f"Error during user creation - {dumps(analytics_data)=}")
        raise e


def update_analytics(user_id: int, analytics_data: Dict) -> bool:
    """Updates the analytics of the user specified by the user_id,
        using the data found in analytics_data

    Args:
        user_id (int)
        analytics_data (Dict)
    
    Raises:
        e (Exception): in case of db errors
    
    Returns:
        bool: True if the user was updated,
            False otherwise
    """
    try:
        update_result: UpdateResult = db.mongo.analytics.update_one(
            {"_id": user_id},
            {"$set": analytics_data}
        )
        # this will be true if there was at least a match
        return bool(update_result.modified_count)
    except Exception as e:
        if "_id" in analytics_data:
            analytics_data["_id"] = str(analytics_data["_id"])
        lgr.logger.error(f"Error during user update - {user_id=} - {dumps(analytics_data)=}")
        raise e


def update_accepted_giocate(user_id: int, giocata_id: int) -> bool:
    try:
        update_result: UpdateResult = db.mongo.utenti.update_one(
            { "_id": user_id, },
            { "$addToSet": { "accepted_giocate": giocata_id } }
        )
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during update of accepted giocate: {user_id=} - {str(giocata_id)=}")
        raise e



def update_refused_giocate(user_id: int, giocata_id: int) -> bool:
    try:
        update_result: UpdateResult = db.mongo.utenti.update_one(
            { "_id": user_id, },
            { "$addToSet": { "refused_giocate": giocata_id } }
        )
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during update of refused giocate: {user_id=} - {str(giocata_id)=}")
        raise e
