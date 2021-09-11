import pytest
import datetime
from lot_bot.dao import user_manager

class TestUserManager:
    """Class containing all the tests for the user_manager module
    """

    # @classmethod
    # def setup_class(cls):
    #     """Imports the user_manager and sets it locally for the class.
    #         user_manager is not imported at the top of the file as usual, 
    #         since doing that would execute all the imported modules BEFORE
    #         the env variable is set to "testing" by tests/conftest.py
    #     """
    #     from lot_bot.dao import user_manager
    #     cls.user_manager = user_manager


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


    def test_create_user(self):
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

    # new_user is specified in the params of the funcion,
    #   so that the fixture with the same name is called and 
    #   its return/yield value is used as a parameter
    def test_update_user(self, new_user):
        user_id = new_user["_id"]
        new_name = "Oiram"
        user_manager.update_user(user_id, {"name": new_name})
        updated_user = user_manager.retrieve_user(user_id)
        assert updated_user["name"] == new_name
        assert updated_user["surname"] == new_user["surname"]

    def test_delete_user(self, new_user):
        user_id = new_user["_id"]
        user_manager.delete_user(user_id)
        assert user_manager.retrieve_user(user_id) == None

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

    def test_check_user_active_validity_and_update(self, new_user):
        user_expiration_date = str((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())
        new_user["validoFino"] = user_expiration_date
        user_manager.update_user(new_user["_id"], {"validoFino": user_expiration_date})
        validity = user_manager.check_user_validity(datetime.datetime.now(), new_user, update_user_state_if_expired=True)
        assert validity == True
        retrieved_user_data = user_manager.retrieve_user(new_user["_id"])["validoFino"]
        assert retrieved_user_data == user_expiration_date

    def test_check_user_expired_validity_and_update(self, new_user):
        user_expiration_date = str((datetime.datetime.now() - datetime.timedelta(days=1)).timestamp())
        new_user["validoFino"] = user_expiration_date
        user_manager.update_user(new_user["_id"], {"validoFino": user_expiration_date, "attivo": 1})
        validity = user_manager.check_user_validity(datetime.datetime.now(), new_user, update_user_state_if_expired=True)
        assert validity == False
        retrieved_user = user_manager.retrieve_user(new_user["_id"])
        assert retrieved_user["validoFino"] == user_expiration_date
        assert retrieved_user["attivo"] == 0
