import datetime
from json import dumps
from typing import Dict, Optional, Union, List

from telegram import user

from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


def create_user(user_data: Dict) -> Union[Dict, bool]:
    """Creates a user using the data found in user_data

    Args:
        user_data (Dict)

    Returns:
        bool: True if the user was created,
            False otherwise
    """
    try:
        result: InsertOneResult = db.mongo.utenti.insert_one(user_data)
        # checks if the inserted id is the one that was passed
        return result.inserted_id == user_data["_id"]
    except Exception as e:
        lgr.logger.error("Error during user creation")
        lgr.logger.error(f"Exception: {str(e)}")
        if "_id" in user_data:
            user_data["_id"] = str(user_data["_id"])
        lgr.logger.error(f"User data: {dumps(user_data)}")
        return False


def retrieve_user(user_id: int) -> Optional[Dict]:
    """Retrieve the user specified by user_id

    Args:
        user_id (int)

    Returns:
        Dict: the user data 
        None: if no user was found or if there was an error
    """
    try:
        return db.mongo.utenti.find_one({"_id": user_id})
    except Exception as e:
        lgr.logger.error("Error during user retrieval")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        return None


def retrieve_user_by_referral(referral_code: str) -> Optional[Dict]:
    """Retrives the user specified by referral_code.

    Args:
        referral_code (str)

    Returns:
        Dict: the user data
        None: if no user was found or if there was an error
    """
    try:
        return db.mongo.utenti.find_one({"referral_code": referral_code})
    except Exception as e:
        lgr.logger.error("Error during user retrieval by ref code")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"Referral code: {referral_code}")
        return None # TODO


def retrieve_user_fields_by_user_id(user_id: int, user_fields: List[str]) -> Optional[Dict]:
    """Retrieve the user fields from the user specified by user_id.

    Args:
        user_id (int)
        user_fields (List[str])

    Returns:
        Dict: the user data 
    
    Raises:
        Exception: if there was an error
    """
    try:
        user_fields = {field: 1 for field in user_fields}
        return db.mongo.utenti.find_one({"_id": user_id}, user_fields)
    except Exception as e:
        lgr.logger.error(f"Error during user fields retrieval {user_id=} - {user_fields=}")
        raise e


def retrieve_user_giocate_since_timestamp(user_id: int, timestamp: float) -> Optional[Dict]:
    """Retrieves all the giocate for user user_id since the time
    indicated by the timestamp.

    Args:
        user_id (int)
        timestamp (float)

    Raises:
        e: in case of db errors

    Returns:
        Optional[Dict]: the giocate the user has made since timestamp, if any
    """
    try:
        return list(db.mongo.utenti.aggregate([
            {
                "$match": {
                    "_id": user_id
                }
            },
            {
                "$unwind": "$giocate"
            },
            {
                "$match": {
                    "giocate.acceptance_timestamp": { "$gt": timestamp }
                }
            },
            {
                "$replaceRoot": {
                    "newRoot": "$giocate"
                }
            }
            ])
        )
    except Exception as e:
        lgr.logger.error(f"Error during user giocate retrieval - {user_id}")
        raise e


def update_user(user_id: int, user_data: Dict) -> bool:
    """Updates the user specified by the user_id,
        using the data found in user_data

    Args:
        user_id (int)
        user_data (Dict)
    
    Raises:
        Exception: in case of db errors
    
    Returns:
        bool: True if the user was updated,
            False otherwise
    """
    try:
        update_result: UpdateResult = db.mongo.utenti.update_one(
            {"_id": user_id},
            {"$set": user_data}
        )
        # this will be true if there was at least a match
        return bool(update_result.matched_count)
    except Exception as e:
        if "_id" in user_data:
            del user_data["_id"]
        lgr.logger.error(f"Error during user update - {user_id} - {dumps(user_data)}")
        raise e


def update_user_by_username(username: str, user_data: Dict) -> bool:
    """Updates the user specified by the username.

    Args:
        username (str)
        user_data (Dict) # TODO add check for user_data validation

    Returns:
        bool: True if the user was updated,
            False otherwise
    """
    try:
        result: UpdateResult = db.mongo.utenti.update_one(
            {"username": username},
            {"$set": user_data}
        )
        return bool(result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during user retrieval by username -  {username=}")
        raise e


def register_giocata_for_user_id(giocata: Dict, user_id: int) -> bool:
    """Creates a personal user giocata for user_id.

    Args:
        giocata (Dict)
        user_id (int)

    Raises:
        e: in case of db errors

    Returns:
        bool: True in case the giocata was added, False otherwise
    """
    try:
        lgr.logger.debug(f"Registering {giocata=} for {user_id=}")
        update_result: UpdateResult = db.mongo.utenti.update_one(
            {
                "_id": user_id,
            },
            {
                "$addToSet": {
                    "giocate": giocata
                }
            }
        )
        # this will be true if there was at least a match
        return bool(update_result.matched_count)
    except Exception as e:
        if "_id" in giocata:
            del giocata["_id"]
        lgr.logger.error(f"Error during giocata registration: {user_id} - {dumps(giocata)}")
        raise e


def register_payment_for_user_id(payment: Dict, user_id: str) -> bool:
    """Adds a payment to the document of user_id.

    Args:
        payment (Dict): the dict containing the payment info
        user_id (str)

    Returns:
        bool: True if the operation was successful, False otherwise
    """
    try:
        lgr.logger.debug(f"Registering {payment=} for {user_id=}")
        update_result: UpdateResult = db.mongo.utenti.update_one(
            {
                "_id": user_id,
            },
            {
                "$addToSet": {
                    "payments": payment
                }
            }
        )
        # this will be true if there was at least a match
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error("Error during giocata registration")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        lgr.logger.error(f"User data: {str(payment)}")
        return False


def delete_user(user_id: int) -> bool:
    """Deletes the user specified by user_id

    Args:
        user_id (int)
    
    Returns: True if the user was deleted,
        False otherwise
    """
    try:
        result: DeleteResult = db.mongo.utenti.delete_one({"_id": user_id})
        return bool(result.deleted_count)
    except Exception as e:
        lgr.logger.error("Error during user deletion")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        return False


def delete_all_users():
    try:
        db.mongo.utenti.delete_many({})
        return True
    except Exception as e:
        lgr.logger.error(f"Error during deletion of all users")
        raise e


def check_user_validity(message_date: datetime.datetime, user_data: Dict) -> bool:
    """Checks if the user subscription is still valid.

    Args:
        message_date (datetime): the date of the message being checked


    Returns:
        bool: True if the the user's subscription is still valid, 
            False otherwise
    """
    return float(user_data["lot_subscription_expiration"]) > message_date.timestamp()


def get_discount_for_user(user_id: int) -> float:
    """Calculates the discount for the user specified by user_id.
    As of now, for a first timer, the discount is 50%

    Args:
        user_id (int)

    Returns:
        float [1.0, 0.0]: decimal number representing the discount percentage 
    """
    retrieved_user_payments = retrieve_user_fields_by_user_id(user_id, ["payments"])
    discount = 0
    if retrieved_user_payments and len(retrieved_user_payments["payments"]) == 0:
        discount = 0.5
    return discount
