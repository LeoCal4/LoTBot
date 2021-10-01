import random
from typing import Dict

import mongomock
import pytest
from lot_bot import database as db
from lot_bot.dao import user_manager
from lot_bot import utils


# scope="session" is used to call this fixture only once for the whole test session
# autouse=True is used to auto-run this fixture at the beginning of the session
@pytest.fixture(scope="session", autouse=True)
def mock_db(monkeysession):
    monkeysession.setattr(db, "mongo", mongomock.MongoClient().client)
    db.mongo.utenti.create_index([("referral_code", 1)], unique=True)
    db.mongo.giocate.create_index([("giocata_num", 1), ("sport", 1)], unique=True)
    db.mongo.abbonamenti.create_index([("telegramID", 1), ("sport", 1), ("strategia", 1)], unique=True)
    


# if no scope is defined, it will be "function", hence it will last 
#   only for the duration of the test function
@pytest.fixture()
def new_user() -> Dict:
    """Fixture which creates a new user, then 
        deletes it once the test is completed

    Yields:
        dict: the user data
    """
    user_data = {
        "_id": random.randint(0, 999),
        "name": "Mario",
        "surname": "Rossi",
        "payments": [],
        "referral_code": utils.generate_referral_code()
    }
    user_manager.create_user(user_data)
    yield user_data
    user_manager.delete_user(user_data["_id"])
