import pytest
from _pytest.monkeypatch import MonkeyPatch
import random


from lot_bot import config as cfg
from lot_bot import constants as cst
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
def set_test_env(monkeysession):
    """Sets the ENV variable to "testing", so that testing data
        is loaded.
    Everything that is found before the yield is run at the beginning
        of the session, the rest is run at its end.
    """

    # def create_mock_db():
    #     return mongomock.MongoClient().client
    
    print("Setting ENV to testing")
    monkeysession.setenv("ENV", "testing")
    # monkeysession.setattr(db, "mongo", mongomock.MongoClient().client)
    cfg.create_config()
    lgr.create_logger()



def create_giocata(sport: str, strategy: str) -> str:
    giocata = f"🏀 {sport} 🏀\n"
    giocata += "🇮🇹Supercoppa Serie A🇮🇹\n"
    giocata += f"⚜️ {strategy} ⚜️\n"
    giocata += "\n"
    giocata += """Trieste 🆚 Trento
🧮 1 inc overtime 🧮
📈 Quota 1.55 📈

Cremona 🆚 Sassari
🧮 2 inc overtime 🧮
📈 Quota 1.30 📈

🧾 2.02 🧾 

🕑 18:30 🕑 

🏛 Stake 5% 🏛\n"""
    giocata += f"🖊 {sport} #8🖊"
    return giocata


@pytest.fixture
def correct_giocata() -> tuple:
    random_sport = random.choice(cst.SPORTS)
    random_strategy = random.choice(cst.STRATEGIES[random_sport])
    return create_giocata(random_sport, random_strategy), random_sport, random_strategy

@pytest.fixture
def wrong_giocata() -> tuple:
    random_sport = "wrong"
    random_strategy = "wronger"
    return create_giocata(random_sport, random_strategy), random_sport, random_strategy
