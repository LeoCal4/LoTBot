from lot_bot import database as db

def retrieve_abbonamenti_from_user_id(user_id: int) -> list:
    """Retrieves all the abbonamenti of the user identified
        by the user_id

    Args:
        user_id (int)

    Returns:
        list: a list of the user's abbonamenti 
        None: if no abbonamenti were found or if there was an error
    """
    try:
        return db.mongo.abbonamenti.find({"telegramID": user_id})
    except Exception as e:
        print("Error during retrieve abbonamenti from user id")
        print(f"Exception: {str(e)}")
        print(f"User id: {user_id}")
        return None 


def delete_abbonamenti_for_user_id(user_id: int) -> bool:
    """Deletes all the abbonamenti of the user identified
        by the user_id

    Args:
        user_id (int)
    
    Returns:
        bool: True if the operation was successful,
            False otherwise
    """
    try:
        db.mongo.abbonamenti.delete_many({"telegramID": user_id})
        # there may be a case in which a user has not abbonamenti,
        #   so we don't do any check on the result of the operation 
        return True
    except Exception as e:
        print("Error during delete abbonamenti from user id")
        print(f"Exception: {str(e)}")
        print(f"User id: {user_id}")
        return False
