import re
from typing import Tuple

from lot_bot import filters

def create_base_giocata():
    return {
        "sport": "",
        "strategia": "",
        "giocata_num": "",
        "base_quota": 0, # [quota (float) * 100] => (int)
        "base_stake": 0, # %
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
        raise Exception # TODO 
    sport = matches.group(1).lower()
    giocata_num = matches.group(2)
    outcome = matches.group(3).lower()
    if outcome in win_keywords:
        outcome = "win"
    elif outcome in loss_keywords:
        outcome = "loss"
    else:
        outcome = "?"
    return sport, giocata_num, outcome


def get_outcome_percentage(outcome: str, stake: int, quota: int) -> float:
    # TODO handle outcomes Exchange
    if outcome == "win":
        outcome_percentage = stake * (quota - 100) / 100
    elif outcome == "loss":
        outcome_percentage = float(-stake)
    else:
        outcome_percentage = 0.0
    return outcome_percentage
