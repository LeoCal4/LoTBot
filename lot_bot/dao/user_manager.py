import datetime
from json import dumps
from typing import Dict, Optional, List

from telegram import user

from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


def create_user(user_data: Dict) -> bool:
    """Creates a user using the data found in user_data

    Args:
        user_data (Dict)

    Raises:
        e (Exception): in case there is a db error

    Returns:
        bool: True if the user was created,
            False otherwise
    """
    try:
        result: InsertOneResult = db.mongo.utenti.insert_one(user_data)
        return result.inserted_id == user_data["_id"]
    except Exception as e:
        if "_id" in user_data:
            user_data["_id"] = str(user_data["_id"])
        lgr.logger.error(f"Error during user creation - {dumps(user_data)=}")
        raise e


def retrieve_user(user_id: int) -> Optional[Dict]:
    """Retrieve the user specified by user_id
    # TODO kill method, used only in tests

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


def retrieve_all_user_ids() -> List[int]:
    try:
        results = db.mongo.utenti.find({}, {"_id": 1})
        if not results:
            return []
        return [entry["_id"] for entry in results]
    except Exception as e:
        raise e


def retrieve_user_id_by_referral(referral_code: str) -> Optional[Dict]:
    """Retrives the id of the user specified by referral_code.

    Args:
        referral_code (str)

    Raises:
        e (Exception): in case of db errors

    Returns:
        Dict: the user data
        None: if no user was found
    """
    try:
        return db.mongo.utenti.find_one(
            {"referral_code": referral_code},
            {"_id": 1}
        )
    except Exception as e:
        lgr.logger.error(f"Error during user retrieval by ref code - {referral_code=}")
        raise e


def retrieve_user_fields_by_username(username: str, user_fields: List[str]) -> Optional[Dict]:
    """Retrieve the user fields from the user specified by username.

    Args:
        username (str)
        user_fields (List[str]): the list of the fields that will be retrieved
    
    Raises:
        Exception: if there was a db error

    Returns:
        Dict: the user data 

    """
    try:
        user_fields = {field: 1 for field in user_fields}
        return db.mongo.utenti.find_one({"username": username}, user_fields)
    except Exception as e:
        lgr.logger.error(f"Error during user fields retrieval {username=} - {user_fields=}")
        raise e


def retrieve_user_fields_by_user_id(user_id: int, user_fields: List[str]) -> Optional[Dict]:
    """Retrieve the user fields from the user specified by user_id.

    Args:
        user_id (int)
        user_fields (List[str]): the list of the fields that will be retrieved
    
    Raises:
        Exception: if there was a db error

    Returns:
        Dict: the user data 

    """
    try:
        user_fields = {field: 1 for field in user_fields}
        return db.mongo.utenti.find_one({"_id": user_id}, user_fields)
    except Exception as e:
        lgr.logger.error(f"Error during user fields retrieval {user_id=} - {user_fields=}")
        raise e


def retrieve_user_giocate_since_timestamp(user_id: int, timestamp: float) -> Optional[List]:
    """Retrieves all the giocate for user user_id since the time
    indicated by the timestamp.

    Args:
        user_id (int)
        timestamp (float)

    Raises:
        e: in case of db errors

    Returns:
        Optional[List]: the giocate the user has made since timestamp, if any
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
        lgr.logger.error(f"Error during user giocate retrieval - {user_id=}")
        raise e


def update_user(user_id: int, user_data: Dict) -> bool:
    """Updates the user specified by the user_id,
        using the data found in user_data

    Args:
        user_id (int)
        user_data (Dict)
    
    Raises:
        e (Exception): in case of db errors
    
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
        lgr.logger.error(f"Error during user update - {user_id=} - {dumps(user_data)=}")
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
        lgr.logger.error(f"Error during giocata registration: {user_id=} - {dumps(giocata)=}")
        raise e


def update_user_personal_stakes(user_id: int, personal_stake: Dict) -> bool:
    try:
        lgr.logger.debug(f"Registering {personal_stake=} for {user_id=}")
        update_result: UpdateResult = db.mongo.utenti.update_one(
            { "_id": user_id, },
            { "$addToSet": { "personal_stakes": personal_stake } }
        )
        # this will be true if there was at least a match
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during personal stake registration: {user_id=} - {personal_stake=}")
        raise e


def register_payment_for_user_id(payment: Dict, user_id: str) -> bool:
    """Adds a payment to the document of user_id.

    Args:
        payment (Dict): the dict containing the payment info
        user_id (str)
    
    Raises:
        e (Exception): in case of db errors

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
        lgr.logger.error(f"Error during payment registration - {user_id=} - {str(payment)=}")
        raise e


def update_user_succ_referrals(user_id: int, payment_id: str) -> bool:
    try:
        lgr.logger.debug(f"Adding {payment_id=} for {user_id=}")
        update_result: UpdateResult = db.mongo.utenti.update_one(
            { "_id": user_id },
            {"$addToSet": 
                { "successful_referrals_since_last_payment": payment_id, 
                    "referred_payments": payment_id
                }
            }
        )
        # this will be true if there was at least a match
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during successful payment referral registration - {user_id=} - {payment_id=}")
        raise e

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


def get_subscription_price_for_user(user_id: int) -> float:
    """Calculates the price for the user specified by user_id.
    As of now, for a first timer and for LoT's first ever users, the base price is halved.
    For each referred user, the base price is discounted by 33%.

    Args:
        user_id (int)

    Returns:
        int: the final price, with discount applied 
    """
    retrieved_user_data = retrieve_user_fields_by_user_id(user_id, ["payments", "is_og_user", "successful_referrals_since_last_payment"])
    discount = 0
    base_price = 7999
    # * set base price
    if len(retrieved_user_data["payments"]) == 0 or bool(retrieved_user_data["is_og_user"]):
        base_price = base_price // 2
    # * calculate discount
    discount_per_ref = 0.33
    successful_refs = len(retrieved_user_data["successful_referrals_since_last_payment"])
    if successful_refs == 3:
        return 0
    elif successful_refs > 0:
        discount = discount_per_ref * len(retrieved_user_data["successful_referrals_since_last_payment"])
    final_price = base_price - int(base_price * discount)
    return final_price
