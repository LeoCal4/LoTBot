import re
from typing import Tuple

from lot_bot import filters
from lot_bot import custom_exceptions
from lot_bot import logger as lgr
from lot_bot.models import sports as spr

def create_base_giocata():
    return {
        "sport": "",
        "strategy": "",
        "giocata_num": "",
        "base_quota": 0, # [quota (float) * 100] => (int)
        "base_stake": 0, # stake (float) % * 100 => (int)
        "sent_timestamp": 0.0,
        "raw_text": "",
        "outcome": "?"
    }


def create_user_giocata():
    return {
        "original_id": 0,
        "acceptance_timestamp": 0.0,
        "personal_quota": 0,
        "personal_stake": 0,
    }


def get_giocata_outcome_data(giocata_outcome: str) -> Tuple[str, str, str]:
    """Finds sport, giocata number and outcome from a giocata outcome message.

    Args:
        giocata_outcome (str)

    Raises:
        Exception: in case of any of the data needed cannot be found

    Returns:
        Tuple[str, str, str]: sport, giocata_num and outcome of the giocata outcome text
    """
    win_keywords = ["vincente", "vinta", "vittoria"]
    loss_keywords = ["perdente", "persa", "perdita", "sconfitta"]
    matches = re.search(filters.get_giocata_outcome_pattern(), giocata_outcome)
    if not matches:
        raise custom_exceptions.GiocataOutcomeParsingError
    sport_token = matches.group(1).lower()
    sport = spr.sports_container.get_sport(sport_token)
    if not sport:
        raise custom_exceptions.GiocataOutcomeParsingError(message=f"sport {sport_token} non valido")
    giocata_num = matches.group(2).strip()
    outcome = matches.group(3).lower().strip()
    if outcome in win_keywords:
        outcome = "win"
    elif outcome in loss_keywords:
        outcome = "loss"
    else:
        outcome = "?"
    return sport.name, giocata_num, outcome


def get_outcome_percentage(outcome: str, stake: int, quota: int) -> float:
    lgr.logger.debug(f"Calculating outcome percentage on {outcome} - {stake} - {quota}")
    if outcome == "win":
        outcome_percentage = (stake * (quota - 100)) / 10000
    elif outcome == "loss":
        outcome_percentage = -stake / 100
    else:
        outcome_percentage = 0.0
    return outcome_percentage
