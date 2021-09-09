from json import dumps

from lot_bot import database as db
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult


def create_user(user_data: dict) -> bool:
    """Creates a user using the data found in user_data

    Args:
        user_data (dict)

    Returns:
        bool: True if the user was created,
            False otherwise
    """
    # TODO add user data validation
    #   https://docs.mongodb.com/manual/core/schema-validation/
    try:
        result: InsertOneResult = db.mongo.utenti.insert_one(user_data)
        # checks if the inserted id is the one that was passed
        return result.inserted_id == user_data["_id"]
    except Exception as e:
        print("Error during user creation")
        print(f"Exception: {str(e)}")
        print(f"User data: {dumps(user_data)}")
        return False



def retrieve_user(user_id: int) -> dict:
    """Retrieve the user specified by user_id

    Args:
        user_id (int)

    Returns:
        dict: the user data 
        None: if no user was found or if there was an error
    """
    try:
        return db.mongo.utenti.find_one({"_id": user_id})
    except Exception as e:
        print("Error during user retrieval")
        print(f"Exception: {str(e)}")
        print(f"User id: {user_id}")
        return None


def update_user(user_id: int, user_data: dict) -> bool:
    """Updates the user specified by the user_id,
        using the data found in user_data

    Args:
        user_id (int)
        user_data (dict)
    
    Returns:
        bool: True if the user was updated,
            False otherwise
    """
    try:
        # TODO add document fields validation 
        update_result: UpdateResult = db.mongo.utenti.update_one({
            "_id": user_id,
            },
            {
                "$set": user_data
            }
        )
        # this will be true if there was at least a match
        return bool(update_result.matched_count)
    except Exception as e:
        print("Error during user update")
        print(f"Exception: {str(e)}")
        print(f"User id: {user_id}")
        print(f"User data: {dumps(user_data)}")
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
        print("Error during user deletion")
        print(f"Exception: {str(e)}")
        print(f"User id: {user_id}")
        return False


