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
            "has_modified_budget", 
            "accepted_giocate",
            "has_completed_checklist",
        })
        if checklist_fields["has_completed_checklist"]:
            return False
        has_completed_checklist = checklist_fields["has_modified_referral"]
        has_completed_checklist = checklist_fields["has_modified_budget"] and has_completed_checklist 
        has_completed_checklist = len(checklist_fields["accepted_giocate"]) > 0 and has_completed_checklist
        if has_completed_checklist:
            update_analytics(user_id, {"has_completed_checklist": True})
            return True 
    except Exception as e:
        lgr.logger.error("Error during checklist completion check")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        return False


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


def retrieve_analytics_fields_by_user_id(user_id: int, fields: List[str]) -> Dict:
    """Retrieve the analytics fields from the user specified by user_id.

    Args:
        user_id (int)
        user_fields (List[str]): the list of the fields that will be retrieved
    
    Raises:
        Exception: if there was a db error

    Returns:
        Dict: the user's analytics data 

    """
    try:
        analytics_fields = {field: 1 for field in fields}
        if analytics_fields == {"all":1}:
            return db.mongo.analytics.find_one({"_id": user_id})
        else:
            return db.mongo.analytics.find_one({"_id": user_id}, analytics_fields)
    except Exception as e:
        lgr.logger.error(f"Error during analytics fields retrieval {user_id=} - {analytics_fields=}")
        raise e


def retrieve_checklist_information_by_user_id(user_id: int) -> Dict:
    checklist_related_fields = [
        "has_completed_checklist",
        "has_modified_referral",
        "accepted_giocate",
        "refused_giocate",
        "has_modified_budget"
    ]
    return retrieve_analytics_fields_by_user_id(user_id, checklist_related_fields)


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
        update_result: UpdateResult = db.mongo.analytics.update_one(
            { "_id": user_id, },
            { "$addToSet": { "accepted_giocate": giocata_id } }
        )
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during update of accepted giocate: {user_id=} - {str(giocata_id)=}")
        raise e


def update_refused_giocate(user_id: int, giocata_id: int) -> bool:
    try:
        update_result: UpdateResult = db.mongo.analytics.update_one(
            { "_id": user_id, },
            { "$addToSet": { "refused_giocate": giocata_id } }
        )
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during update of refused giocate: {user_id=} - {str(giocata_id)=}")
        raise e


def update_resoconto_requests(user_id: int, resoconto_data: Dict) -> bool:
    """_summary_

    Args:
        user_id (int): _description_
        resoconto_data (Dict): resoconto type (1 day, 7 days...) and timestamp

    Raises:
        e: _description_

    Returns:
        bool: _description_
    """
    try:
        update_result: UpdateResult = db.mongo.analytics.update_one(
            { "_id": user_id, },
            { "$addToSet": { "resoconto_requests": resoconto_data } }
        )
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during update of resoconto requests: {user_id=} - {str(resoconto_data)=}")
        raise e


def update_referred_users(user_id: int, referred_user_data: Dict) -> bool:
    """_summary_

    Args:
        user_id (int): _description_
        referred_user_data (Dict): referred user id and timestamp

    Raises:
        e: _description_

    Returns:
        bool: _description_
    """
    try:
        update_result: UpdateResult = db.mongo.analytics.update_one(
            { "_id": user_id, },
            { "$addToSet": { "referred_users": referred_user_data } }
        )
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during update of referred users: {user_id=} - {str(referred_user_data)=}")
        raise e
