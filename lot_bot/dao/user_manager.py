import datetime
from json import dumps
from typing import Dict, Optional, List, Union

from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.collection import ReturnDocument
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from lot_bot.models import subscriptions as subs
from lot_bot.models import sports as sprt



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


def retrieve_all_active_user_ids() -> List[int]:
    """Retrieves all the users' IDs.

    Raises:
        e: in case of db errors

    Returns:
        List[int]: the list of the users' IDs
    """
    try:
        results = db.mongo.utenti.find({"blocked": False}, {"_id": 1})
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
            { "$match": { "_id": user_id } },
            { "$unwind": "$giocate" },
            { "$match": { "giocate.acceptance_timestamp": { "$gt": timestamp } } },
            { "$replaceRoot": { "newRoot": "$giocate" } }
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


def update_user_by_username_and_retrieve_fields(username: str, user_data: Dict, user_fields: List = ["_id"]) -> Optional[Dict]:
    """Updates the user specified by the username, returning the user's ID.

    Args:
        username (str)
        user_data (Dict)
        user_fields (List): the updated user's fields to return. Defaults to ["_id"]

    Returns:
        Dict: the specified user's fields
        None: if the user is not found
    """
    user_fields_projection = {field: True for field in user_fields}
    try:
        result = db.mongo.utenti.find_one_and_update(
            {"username": username},
            {"$set": user_data},
            projection=user_fields_projection,
            return_document=ReturnDocument.AFTER
        )
        return result
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
            { "_id": user_id, },
            { "$addToSet": { "giocate": giocata } }
        )
        # this will be true if there was at least a match
        return bool(update_result.matched_count)
    except Exception as e:
        if "_id" in giocata:
            del giocata["_id"]
        lgr.logger.error(f"Error during giocata registration: {user_id=} - {dumps(giocata)=}")
        raise e


def update_user_personal_stakes(user_id: int, personal_stake: Dict) -> bool:
    """Adds a personalized stake to the ones of the specified user.

    Args:
        user_id (int)
        personal_stake (Dict)

    Raises:
        e: in case of db errors

    Returns:
        bool: True if the stake was added, False otherwise
    """
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
    """Adds a successful referral (in the form of a payment ID) to the specified user's ones.

    Args:
        user_id (int)
        payment_id (str)

    Raises:
        e: in case of db errors

    Returns:
        bool: True if the payment is added, False otherwise
    """
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


def delete_personal_stake_by_user_id_or_username(user_identification_data: Union[int, str], personal_stake_id: str) -> bool:
    """Deletes a user's personal stake, indicated by its position on the personal stake's list.

    Args:
        user_identification_data (Union[int, str]): either the user's ID or username
        personal_stake_id (str): the position of the stake in the personal stake's list

    Raises:
        e: in case of db errors

    Returns:
        bool: True if the stake was deleted, False otherwise
    """
    # * checks whetever the user identification data is an ID or a username
    if type(user_identification_data) is int:
        user_query = {"_id": user_identification_data}
    else:
        user_query = {"username": user_identification_data}
    try:
        user_data : List[Dict] = db.mongo.utenti.find_one(user_query, {"personal_stakes": 1})
        if not user_data:
            # * user not found
            return False
        personal_stakes = user_data["personal_stakes"]
        del personal_stakes[personal_stake_id]
        result: UpdateResult = db.mongo.utenti.update_one(user_query, {"$set": { "personal_stakes": personal_stakes } })
        return bool(result.modified_count)
    except Exception as e:
        lgr.logger.error(f"Error deletion of user stake - {user_identification_data} - {personal_stake_id}")
        raise e


def delete_all_users() -> bool:
    """Deletes all the users.

    Raises:
        e: in case of db errors

    Returns:
        bool: True
    """
    try:
        db.mongo.utenti.delete_many({})
        return True
    except Exception as e:
        lgr.logger.error(f"Error during deletion of all users")
        raise e


def check_user_subscription_validity(message_date: datetime.datetime, user_subscriptions: Dict, sub_name: str = "") -> bool:
    """Checks if the user subscription is still valid for a given message date, for any subscription or a specific one.

    Args:
        message_date (datetime): the date of the message being checked
        user_subscriptions (List)
        sub_name (str): name of the subscription to check; all of them are checked in case none is specified.

    Returns:
        bool: True if the the user's subscription is still valid, False otherwise
    """
    message_timestamp = message_date.timestamp()
    # * check if any sub is active
    if sub_name == "":
        for sub in user_subscriptions:
            if float(sub["expiration_date"]) > message_timestamp:
                return True
        return False
    # * check if the specified sub is active
    else:
        user_subs_names = [sub["name"] for sub in user_subscriptions]
        if not sub_name in user_subs_names:
            return False
        sub_expiration = [sub["expiration_date"] for sub in user_subscriptions if sub["name"] == sub_name][0]
        return float(sub_expiration) > message_timestamp


def check_user_sport_subscription(message_date: datetime.datetime, user_subscriptions: Dict, sport_name: str) -> bool:
    for sub_entry in user_subscriptions:
        sub = subs.sub_container.get_subscription(sub_entry["name"])
        sport = sprt.sports_container.get_sport(sport_name)
        if sub is None or sport is None:
            raise Exception
        if sub.available_sports == [] or sport in sub.available_sports:
            if check_user_subscription_validity(message_date, user_subscriptions, sub_name=sub.name):
                return True
    return False


def get_subscription_price_for_user(user_id: int) -> float:
    """Calculates the price for the user specified by user_id.
    As of now, for a first timer and for LoT's first ever users, the base price is halved.
    For each referred user, the base price is discounted by 33%.
    # TODO move to user model 

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
