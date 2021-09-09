import mongomock
import pytest
from _pytest.monkeypatch import MonkeyPatch

from lot_bot import config as cfg
from lot_bot import logger as lgr
from lot_bot import database as db

"""The fixtures found in this file are automatically added by pytest 
    to all the tests files/subdirectories in this directory
"""

# https://github.com/pytest-dev/pytest/issues/363#issuecomment-406536200
@pytest.fixture(scope="session")
def monkeysession(request):
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


# scope="session" is used to call this fixture only once for the whole test session
# autouse=True is used to auto-run this fixture at the beginning of the session
@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown(monkeysession):
    """Sets the ENV variable to "testing", so that testing data
        is loaded.
    Everything that is found before the yield is run at the beginning
        of the session, the rest is run at its end.
    """

    # def create_mock_db():
    #     return mongomock.MongoClient().client
    
    print("Setting ENV to testing")
    monkeysession.setenv("ENV", "testing")
    monkeysession.setattr(db, "mongo", mongomock.MongoClient().client)
    cfg.create_config()
    lgr.create_logger()
