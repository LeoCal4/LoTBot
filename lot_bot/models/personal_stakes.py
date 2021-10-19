from typing import Dict, List

from lot_bot import logger as lgr
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot import custom_exceptions
from lot_bot import utils


def create_base_personal_stake():
    return {
        "min_quota": 0,
        "max_quota": 0,
        "stake": 0,
        "sport": None,
        "strategies": None,
    }


def parse_personal_stake(personal_stake_data: List) -> Dict:
    """Parses and create the personal stake from a /crea_stake command.

    Args:
        personal_stake_data (List): the list of arguments passed to the /crea_stake command.
            It is divided in:
                - user identification
                - min quota
                - max quota
                - stake
                - sport (optional)
                - strategies (variable number, optional, sport needs to be specified)

    Raises:
        custom_exceptions.PersonalStakeParsingError: in case quotas and stake cannot be parsed
        custom_exceptions.PersonalStakeParsingError: in case min quota is gte than max quota
        custom_exceptions.PersonalStakeParsingError: in case stake is not a valid %
        custom_exceptions.PersonalStakeParsingError: in case sport is not valid
        custom_exceptions.PersonalStakeParsingError: in case a strategy is not valid
        custom_exceptions.PersonalStakeParsingError: in case a strategy is not available for the sport

    Returns:
        Dict: the parsed personal stake
    """
    SPORT_INDEX = 4
    STRATEGIES_START_INDEX = SPORT_INDEX + 1
    _, raw_min_quota, raw_max_quota, raw_personal_stake = personal_stake_data[:SPORT_INDEX]
    # * check if the quota range and the stake are valid floats and turn them to ints
    try:
        min_quota = utils.parse_float_string_to_int(raw_min_quota)
        max_quota = utils.parse_float_string_to_int(raw_max_quota)
        personal_stake = utils.parse_float_string_to_int(raw_personal_stake)
    except:
        raise custom_exceptions.PersonalStakeParsingError(f"ERRORE: impossibile analizzare min/max quota o stake")
    # * check if the min quota is less then the max quota
    if min_quota >= max_quota:
        raise custom_exceptions.PersonalStakeParsingError(f"ERRORE: la quota minima {raw_min_quota} è maggiore o uguale alla quota massima {raw_max_quota}")
    # * check if the personal stake is a valid percentage
    if personal_stake > 10000 or personal_stake <= 0:
        raise custom_exceptions.PersonalStakeParsingError(f"ERRORE: lo stake {raw_personal_stake} è maggiore di 100 o minore o uguale a 0")
    # * check if the sport is valid    
    sport = "all"
    if len(personal_stake_data) > SPORT_INDEX:
        found_sport = spr.sports_container.get_sport(personal_stake_data[SPORT_INDEX])
        if not found_sport:
            raise custom_exceptions.PersonalStakeParsingError(f"ERRORE: lo sport {personal_stake_data[SPORT_INDEX]} non è valido")
        sport = found_sport.name
    # * check if the strategies are valid and if they are avaliable for the selected sport    
    strategies = ["all"]
    if len(personal_stake_data) > STRATEGIES_START_INDEX:
        strategies = []
        for strategy in personal_stake_data[STRATEGIES_START_INDEX:]:
            found_strat = strat.strategies_container.get_strategy(strategy)
            if not found_strat:
                raise custom_exceptions.PersonalStakeParsingError(f"ERRORE: la strategia {strategy} non esiste")
            if not found_strat in found_sport.strategies:
                raise custom_exceptions.PersonalStakeParsingError(f"ERRORE: la strategia {strategy} non è disponibile per lo sport {sport}")
            strategies.append(found_strat.name)
    # * create the new personal stake
    personal_stake_data = create_base_personal_stake() 
    personal_stake_data["min_quota"] = min_quota
    personal_stake_data["max_quota"] = max_quota
    personal_stake_data["stake"] = personal_stake
    personal_stake_data["sport"] = sport
    personal_stake_data["strategies"] = list(set(strategies))
    return personal_stake_data


def check_stakes_overlapping(new_stake: Dict, user_stakes: List) -> bool:
    """Checks if the new stake overlaps with any of the user's stakes.

    Args:
        new_stake (Dict)
        user_stakes (List)

    Returns:
        bool: True if the stakes are overlapping, False otherwise
    """
    if not user_stakes:
        return False
    for stake in user_stakes:
        stake_sport = stake["sport"] 
        # * sports are different and neither of them are "all"
        # * if sports overlap, no common strategies and none or them are "all"
        if ((stake_sport != "all" and new_stake["sport"] != "all" and stake_sport != new_stake["sport"]) or 
            (len(set(stake["strategies"]) & set(new_stake["strategies"])) == 0 and "all" not in stake["strategies"] and "all" not in new_stake["strategies"])):
            continue
        retrieved_min_quota = stake["min_quota"]
        retrieved_max_quota = stake["max_quota"]
        if retrieved_min_quota <= new_stake["min_quota"] <= retrieved_max_quota or retrieved_min_quota <= new_stake["max_quota"] <= retrieved_max_quota:
            return True
    return False
