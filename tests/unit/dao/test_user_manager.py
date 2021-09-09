import pytest


class TestUserManager:
    """Class containing all the tests for the user_manager module
    """

    @classmethod
    def setup_class(cls):
        """Imports the user_manager and sets it locally for the class.
            user_manager is not imported at the top of the file as usual, 
            since doing that would execute all the imported modules BEFORE
            the env variable is set to "testing" by tests/conftest.py
        """
        from lot_bot.dao import user_manager
        cls.user_manager = user_manager


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
        self.user_manager.create_user(user_data)
        yield user_data
        self.user_manager.delete_user(user_data["_id"])


    def test_create_user(self):
        user_data = {
            "_id": 0,
            "name": "Franco",
            "surname": "Rossi"
        }
        self.user_manager.create_user(user_data)
        user = self.user_manager.retrieve_user(user_data["_id"])
        assert len(user_data.keys()) == len(user.keys())
        for key in user.keys():
            assert user[key] == user_data[key]

    # new_user is specified in the params of the funcion,
    #   so that the fixture with the same name is called and 
    #   its return/yield value is used as a parameter
    def test_update_user(self, new_user):
        user_id = new_user["_id"]
        new_name = "Oiram"
        self.user_manager.update_user(user_id, {"name": new_name})
        updated_user = self.user_manager.retrieve_user(user_id)
        assert updated_user["name"] == new_name
        assert updated_user["surname"] == new_user["surname"]

    def test_delete_user(self, new_user):
        user_id = new_user["_id"]
        self.user_manager.delete_user(user_id)
        assert self.user_manager.retrieve_user(user_id) == None
