import datetime
from json import dumps
from typing import Dict, Optional, List, Union

from lot_bot import database as db
from lot_bot import logger as lgr
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

def retrieve_budgets_from_user_id(user_id: int):
    try:
        budgets_result = db.mongo.utenti.find_one(
            { "_id": user_id },
            { "budgets":1}
        )
        if not budgets_result["budgets"]:
            return {}
        return budgets_result["budgets"]
    except Exception as e:
        lgr.logger.error(f"Error during retrieve budgets for user id - {user_id=}")
        raise e 

def retrieve_default_budget_from_user_id(user_id: int) -> Dict:
    try:
        user_budgets = retrieve_budgets_from_user_id(user_id)
        #user_budgets = utenti.find_one({"_id":123, "budgets.default":True },{"budgets":1})["budgets"]
        if not user_budgets:
            return {}
        else:
            for budget in user_budgets:
                if budget["default"]:
                    return budget
    except Exception as e:
        lgr.logger.error(f"Error during retrieve default budget name for user id - {user_id=}")
        raise e 

def delete_budget(user_id: int, budget_name: str) -> bool:
    """Deletes a user's budget, indicated by its budget_name.

    Args:
        user_id (int): the user's ID 
        budget_name (str): the name of the budget to delete

    Raises:
        e: in case of db errors

    Returns:
        bool: True if the budget was deleted, False otherwise
    """

    try:
        result: UpdateResult = db.mongo.utenti.update_one(
          { "_id": user_id },
          { "$pull": { 'budgets': { "budget_name": budget_name } } }
        )
        return bool(result.modified_count)
    except Exception as e:
        lgr.logger.error(f"Error deletion of user budget - {user_id} - {budget_name}")
        raise e

def retrieve_budget_from_name(user_id: int, budget_name: str):
    try:
        result = db.mongo.utenti.find_one({"_id":user_id, "budgets" : { "$elemMatch": { "budget_name": budget_name } } },{ 'budgets.$': 1 })
        if result:
            return result["budgets"][0]
        else:
            return {}
    except Exception as e:
        lgr.logger.error(f"Error during retrieve {budget_name=} for user id - {user_id=}")
        raise e 

def add_new_budget(user_id: int, budget_data: Dict) -> bool:
    """Adds a budget to the budgets of user_id.

    Args:
        budget_data (Dict): the dict containing the budget info - budget_name, balance, default
        user_id (int)
    
    Raises:
        e (Exception): in case of db errors

    Returns:
        bool: True if the operation was successful, False otherwise
    """
    try:
        lgr.logger.debug(f"Registering {budget_data=} for {user_id=}")
        update_result: UpdateResult = db.mongo.utenti.update_one(
            {
                "_id": user_id,
            },
            {
                "$addToSet": {
                    "budgets": budget_data
                }
            }
        )
        # this will be true if there was at least a match
        return bool(update_result.matched_count)
    except Exception as e:
        lgr.logger.error(f"Error during budget_data registration - {user_id=} - {str(budget_data)=}")
        raise e
#TODO da sostituire con update_budget_data
def update_budget_name(user_id: int, previous_name: str, new_name: str) -> bool:
    """Update a budget name

    Args:
        user_id (int)
        previous_name (str)
        new_name (str)

    Raises:
        e: in case of db errors

    Returns:
        bool: True if the budget name is updated with the new name
    """
    try:
        update_result : UpdateResult = db.mongo.utenti.update_one(
            {"_id": user_id, "budgets.budget_name": previous_name },
            {"$set": {"budgets.$.budget_name": new_name } }
        )
        return bool(update_result.modified_count)
    except Exception as e:
        lgr.logger.error(f"Error during updating budget name {user_id=} - {previous_name=} to {new_name=}")
        raise e

def update_budget_data(user_id: int, budget_name: str, new_data: Dict) -> bool:
    """Update a budget name

    Args:
        user_id (int)
        budget_name (str)
        new_data (Dict)

    Raises:
        e: in case of db errors

    Returns:
        bool: True if the budget is updated with the new data
    """
    new_data = {"budgets.$."+value: new_data[value] for value in new_data}
    try:
        update_result : UpdateResult = db.mongo.utenti.update_one(
            {"_id": user_id, "budgets.budget_name": budget_name },
            {"$set": new_data }
        )
        return bool(update_result.modified_count)
    except Exception as e:
        lgr.logger.error(f"Error during updating budget name {user_id=} - {previous_name=} to {new_name=}")
        raise e
#TODO da sostituire con update_budget_data
def update_budget_balance(user_id: int, budget_name: str, new_balance: int) -> bool:
    """Update a budget name

    Args:
        user_id (int)
        budget_name (str)
        new_balance (int)

    Raises:
        e: in case of db errors

    Returns:
        bool: True if the budget name is updated with the new name
    """
    try:
        update_result : UpdateResult = db.mongo.utenti.update_one(
            {"_id": user_id, "budgets.budget_name": budget_name },
            {"$set": {"budgets.$.balance": new_balance } }
        )
        return bool(update_result.modified_count)
    except Exception as e:
        lgr.logger.error(f"Error during updating budget balance {user_id=} - {budget_name=} to {new_balance=}")
        raise e