import random
from typing import Tuple

import pytest
from _pytest.monkeypatch import MonkeyPatch
from lot_bot import config as cfg
from lot_bot import logger as lgr
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat

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
    print("Setting ENV to testing")
    monkeysession.setenv("ENV", "testing")
    cfg.create_config()
    lgr.create_logger()



def create_giocata(sport: spr.Sport, strategy: strat.Strategy) -> str:
    giocata = f"""🏀 {sport.display_name} 🏀
🇮🇹 Supercoppa Serie A 🇮🇹
⚜️  {strategy.display_name} ⚜️

Trieste 🆚 Trento
🧮 1 inc overtime 🧮
📈 Quota 1.55 📈

Cremona 🆚 Sassari
🧮 2 inc overtime 🧮
📈 Quota 1.30 📈

🧾 2.02 🧾 

🕑 18:30 🕑 

🏛 Stake 5% 🏛
🖊 {sport.display_name} #8 🖊"""
    return giocata


@pytest.fixture
def correct_giocata() -> Tuple[str, str, str]:
    random_sport : str.Sport = random.choice(spr.sports_container.astuple())
    random_strategy =  random.choice(random_sport.strategies)
    return create_giocata(random_sport, random_strategy), random_sport.name, random_strategy.name


@pytest.fixture
def wrong_giocata() -> Tuple[str, str, str]:
    random_sport = spr.Sport("wrong", [])
    random_strategy = strat.Strategy("wronger")
    return create_giocata(random_sport, random_strategy), random_sport.name, random_strategy.name
