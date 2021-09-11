import pytest
import mongomock

from lot_bot import database as db


# scope="session" is used to call this fixture only once for the whole test session
# autouse=True is used to auto-run this fixture at the beginning of the session
@pytest.fixture(scope="session", autouse=True)
def mock_db(monkeysession):
    monkeysession.setattr(db, "mongo", mongomock.MongoClient().client)
