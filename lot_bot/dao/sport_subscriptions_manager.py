from typing import List
from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.results import UpdateResult


def create_sport_subscription(sport_sub_data : dict) -> bool:
    """Creates an sport_subscription using sport_sub_data

    Args:
        sport_sub_data (dict)

    Returns:
        bool: True if the sport_subscription was inserted,
            False otherwise
    
    Raises:
        Exception: in case of errors
    """
    user_id = sport_sub_data['user_id']
    try:
        # db.mongo.utenti.update_one(
        #     { "_id": user_id },
        #     { "$addToSet": { "sport_subscriptions": { "sport": sport_subscription["sport"] } } },
        # )
        # results = db.mongo.utenti.find_one_and_update(
        #     { "_id": user_id, "sport_subscriptions": { "$elemMatch": { "sport": sport_subscription["sport"] } } },
        #     { "$addToSet": { "sport_subscriptions.$.strategies": sport_subscription["strategy"]  } },
        # )
        query_results = db.mongo.utenti.find_one({ "_id": user_id }, { "sport_subscriptions": 1 })
        if not query_results:
            raise Exception("User not found during sport subscription creation")
        sport_subscriptions = list(query_results["sport_subscriptions"])
        found = False
        for subscription in sport_subscriptions:
            if sport_sub_data["sport"] == subscription["sport"]:
                found = True
                if not sport_sub_data["strategy"] in subscription["strategies"]:
                    subscription["strategies"].append(sport_sub_data["strategy"])
                break
        if not found:
            sport_subscriptions.append({"sport": sport_sub_data["sport"], "strategies": [sport_sub_data["strategy"]]})
        update_result : UpdateResult = db.mongo.utenti.update_one({ "_id": user_id }, { "$set": { "sport_subscriptions": sport_subscriptions } } )
        lgr.logger.debug(f"Created new sport_subscription for user id {user_id} with data {sport_sub_data}")
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during create sport_subscriptions - {sport_sub_data=}")
        raise e


def retrieve_all_user_ids_sub_to_sport_and_strategy(sport: str, strategy: str) -> List:
    try:
        raw_user_ids = list(db.mongo.utenti.find(
            { "sport_subscriptions.sport" : sport, "sport_subscriptions": { "$elemMatch": { "strategies": strategy } } },
            { "_id": 1 }
        ))
        return [raw_user_id["_id"] for raw_user_id in raw_user_ids]
    except Exception as e:
        lgr.logger.error(f"Error during retrieve all subscribed users to {sport=} - {strategy=}")
        raise e 


def retrieve_sport_subscriptions_from_user_id(user_id: int) -> List:
    try:
        sub_result = db.mongo.utenti.find_one(
            { "_id": user_id },
            { "sport_subscriptions": 1 }
        )
        if sub_result:
            return sub_result["sport_subscriptions"]
        return []
    except Exception as e:
        lgr.logger.error(f"Error during retrieve sport subscriptions for user id - {user_id=}")
        raise e    


def retrieve_subscribed_strats_from_user_id_and_sport(user_id: int, sport: str) -> List:
    """Returns the user's sport subscription for a certain sport.

    Args:
        user_id (int)
        sport (str)

    Returns:
        List: the list containing the subscribed strategies of the sport found (if there was any)
    
    Raises:
        Exception: in case of db errors
    """
    lgr.logger.debug(f"Retrieving sub strats for {user_id} and sport {sport}")
    try:
        sub_result = db.mongo.utenti.find_one(
            { "_id": user_id, "sport_subscriptions.sport": sport },
            { "sport_subscriptions": { "$elemMatch": { "sport": sport } } }
        )
        if sub_result and len(sub_result["sport_subscriptions"]) > 0:
            lgr.logger.debug(f"{sub_result=}")
            return sub_result["sport_subscriptions"][0]["strategies"]
        return []
    except Exception as e:
        lgr.logger.error(f"Error during retrieve sport strategy sport_subscription for user id - {user_id=} - {sport=}")
        raise e


def delete_sport_subscription(sport_sub_data: dict) -> bool:
    """Deletes any sport_subscription with data equal to sport_sub_data.

    Args:
        sport_sub_data (dict)

    Returns:
        bool: True if the operation was successful,
            Falso otherwise
    """
    user_id = sport_sub_data["user_id"]
    try:
        query_results = db.mongo.utenti.find_one({ "_id": user_id }, { "sport_subscriptions": 1 })
        if not query_results:
            raise Exception("User not found during sport subscription deletion")
        sport_subscriptions = list(query_results["sport_subscriptions"])
        lgr.logger.debug(f"To delete: {sport_sub_data=}")
        lgr.logger.debug(f"Before deletion: {sport_subscriptions=}")
        for subscription in sport_subscriptions:
            if sport_sub_data["sport"] == subscription["sport"]:
                if sport_sub_data["strategy"] in subscription["strategies"]:
                    subscription["strategies"].remove(sport_sub_data["strategy"])
                if subscription["strategies"] == []:
                    sport_subscriptions.remove(subscription)
        lgr.logger.debug(f"After deletion: {sport_subscriptions=}")
        update_result : UpdateResult = db.mongo.utenti.update_one({ "_id": user_id }, { "$set": { "sport_subscriptions": sport_subscriptions } } )
        lgr.logger.debug(f"Delete sport_subscription for user id {user_id} with data {sport_sub_data}")
        return bool(update_result.modified_count)
    except Exception as e:
        lgr.logger.error(f"Error during delete sport_subscription - {sport_sub_data=}")
        raise e


def delete_sport_subscriptions_for_user_id(user_id: int) -> bool:
    """Deletes all the sport_subscriptions of the user identified
        by the user_id

    Args:
        user_id (int)
    
    Returns:
        bool: True if the operation was successful,
            False otherwise
    """
    try:
        db.mongo.sport_subscriptions.delete_many({"user_id": user_id})
        # there may be a case in which a user has no sport_subscriptions,
        #   so we don't do any check on the result of the operation 
        return True
    except Exception as e:
        lgr.logger.error("Error during delete sport_subscriptions from user id")
        lgr.logger.error(f"Exception: {str(e)}")
        lgr.logger.error(f"User id: {user_id}")
        return False


def delete_all_sport_subscriptions():
    try:
        db.mongo.sport_subscriptions.delete_many({})
        return True
    except Exception as e:
        lgr.logger.error("Error during delete all sport_subscriptions")
        lgr.logger.error(f"Exception: {str(e)}")
        return False
