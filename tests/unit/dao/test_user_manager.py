import datetime

import pytest
from lot_bot import database as db
from lot_bot.dao import user_manager


class TestUserManager:
    """Class containing all the tests for the user_manager module
    """

    # if no scope is defined, it will be "function", hence it will last 
    #   only for the duration of the test function
    @pytest.fixture()
    def new_user(self):
        """Fixture which creates a new user, then 
            deletes it once the test is completed

        Yields:
            dict: the user data
        """
        # TODO use LoT related data
        user_data = {
            "_id": 0,
            "name": "Mario",
            "surname": "Rossi"
        }
        user_manager.create_user(user_data)
        yield user_data
        user_manager.delete_user(user_data["_id"])


    def test_create_user(self, monkeypatch):
        user_data = {
            "_id": 0,
            "name": "Franco",
            "surname": "Rossi"
        }
        user_manager.create_user(user_data)
        user = user_manager.retrieve_user(user_data["_id"])
        assert len(user_data.keys()) == len(user.keys())
        for key in user.keys():
            assert user[key] == user_data[key]
        monkeypatch.setattr(db, "mongo", None)
        user_data2 = {
            "_id": 1,
            "name": "Franco",
            "surname": "Rossi"
        }
        assert not user_manager.create_user(user_data2)


    # new_user is specified in the params of the funcion,
    #   so that the fixture with the same name is called and 
    #   its return/yield value is used as a parameter
    def test_retrieve_user(self, new_user, monkeypatch):
        user_id = new_user["_id"]
        user_from_db = user_manager.retrieve_user(user_id)
        assert user_id == user_from_db["_id"]
        assert user_manager.retrieve_user(-1) is None
        monkeypatch.setattr(db, "mongo", None)
        assert user_manager.retrieve_user(user_id) is None


    def test_update_user(self, new_user, monkeypatch):
        user_id = new_user["_id"]
        new_name = "Oiram"
        user_manager.update_user(user_id, {"name": new_name})
        updated_user = user_manager.retrieve_user(user_id)
        assert updated_user["name"] == new_name
        assert updated_user["surname"] == new_user["surname"]
        # wrong id
        assert not user_manager.update_user(-1, {"name": new_name})
        # db connection error
        monkeypatch.setattr(db, "mongo", None)
        assert not user_manager.update_user(user_id, {"name": new_name})


    def test_delete_user(self, new_user, monkeypatch):
        user_id = new_user["_id"]
        assert user_manager.delete_user(user_id)
        assert user_manager.retrieve_user(user_id) == None
        assert not user_manager.delete_user(-1)
        # db connection error
        monkeypatch.setattr(db, "mongo", None)
        assert not user_manager.delete_user(user_id)
        

    def test_check_user_active_validity(self):
        user_expiration_date = str((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())
        user_data = {"validoFino": user_expiration_date}
        validity = user_manager.check_user_validity(datetime.datetime.now(), user_data)
        assert validity == True
    

    def test_check_user_expired_validity(self):
        user_expiration_date = str((datetime.datetime.now() - datetime.timedelta(days=1)).timestamp())
        user_data = {"validoFino": user_expiration_date}
        validity = user_manager.check_user_validity(datetime.datetime.now(), user_data)
        assert validity == False
