import datetime
import re
from typing import Dict, List, Optional, Tuple

from lot_bot import custom_exceptions, filters
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat


STAKE_PATTERN = fr"\s*Stake\s*(\d+[.,]?\d*)\s*"


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
    elif outcome == "void":
        outcome = "void"
    else:
        outcome = "neutral"
    return sport.name, giocata_num, outcome


def get_cashout_data(cashout_message: str) -> Tuple[str, int]:
    """[summary]

    Args:
        cashout_message (str)

    Raises:
        custom_exceptions.GiocataOutcomeParsingError: in case there are less than 2 tokens
        custom_exceptions.GiocataOutcomeParsingError: in case the percentage is not a valid float

    Returns:
        Tuple[str, int]: giocata number and cashout percentage
    """
    cashout_tokens = cashout_message.strip().split()
    # * check if both id and % are present
    if len(cashout_tokens) < 2:
        raise custom_exceptions.GiocataOutcomeParsingError("\nIndicare l'id della giocata preceduta da # e la percentuale del cashout")
    # * eventually remove % at the end and convert cashout percentage to int
    cashout_percentage = cashout_tokens[1] if cashout_tokens[1][-1] != "%" else cashout_tokens[1][:-1]
    try:
        cashout_percentage = utils.parse_float_string_to_int(cashout_tokens[1])
    except Exception as e:
        lgr.logger.error(f"During cashout parsing - {str(e)}")
        raise custom_exceptions.GiocataOutcomeParsingError("\nPercentuale di cashout non valida")
    # * remove '#' from giocata num
    giocata_num = cashout_tokens[0][1:]
    return giocata_num, cashout_percentage


def get_outcome_percentage(outcome: str, stake: int, quota: int) -> float:
    lgr.logger.debug(f"Calculating outcome percentage on {outcome} - {stake} - {quota}")
    if outcome == "win":
        outcome_percentage = (stake * (quota - 100)) / 10000
    elif outcome == "loss":
        outcome_percentage = -stake / 100
    else:
        outcome_percentage = 0.0
    return outcome_percentage


def get_outcome_emoji(outcome_percentage: float, outcome_state: str) -> str:
    """TODO only outcome state

    Args:
        outcome_percentage (float)
        outcome_state (str)

    Returns:
        str
    """
    if outcome_state == "neutral" or outcome_state == "abbinata":
        return "⚪"
    if outcome_state == "void":
        return "🟡"
    if outcome_percentage > 0:
        outcome_emoji = "🟢"
    elif outcome_percentage == 0:
        outcome_emoji = "🕔" 
    else:
        outcome_emoji = "🔴"
    return outcome_emoji


def get_sport_name_from_giocata(text: str) -> str:
    """Extracts the sport name from a giocata message.
    It checks if the sports exists.

    Args:
        text (str): a giocata message

    Returns:
        str: the name of the sport
    
    Raises:
        GiocataParsingError: if the sport was not found
    """
    sport_row = text.split("\n")[0].lower()
    # ? could be faster if we would just get the second token
    for sport in spr.sports_container:
        if sport.display_name.lower() in sport_row:
            return sport.name
    error_message = f"giocata_model.get_sport_name_from_giocata: Could not find in any sport in line {sport_row}"
    lgr.logger.error(error_message)
    raise custom_exceptions.GiocataParsingError(f"sport non trovato nella riga '{sport_row}'")



def get_strategy_name_from_giocata(text: str, sport: spr.Sport) -> str:
    """Extracts the strategy name from a giocata message.
    It checks if the strategy exists and if it is present in the sport's ones.

    Args:
        text (str): a giocata message
        sport (str): the strategy's sport

    Returns:
        str: the name of the strategy
        
    Raises:
        GiocataParsingError: if the strategy is not found
    """
    STRATEGY_ROW = 2
    STRATEGY_INDEX = 1
    played_strategy = " ".join(text.split("\n")[STRATEGY_ROW].split()[STRATEGY_INDEX:-1])
    strategy = strat.strategies_container.get_strategy(played_strategy)
    sport = spr.sports_container.get_sport(sport)
    if strategy and strategy in sport.strategies:
        return strategy.name
    else:
        error_message = f"giocata_model.get_strategy_name_from_giocata: Strategy {played_strategy} not found from {text} for sport {sport.name}"
        lgr.logger.error(error_message)
        raise custom_exceptions.GiocataParsingError(f"strategia '{played_strategy}' non trovata per lo sport '{sport.name}'")


def get_giocata_num_from_giocata(giocata_text: str) -> str:
    """Gets the number of the giocata from its text.

    Args:
        giocata_text (str)

    Raises:
        custom_exceptions.GiocataParsingError: in case the giocata num cannot be found

    Returns:
        str
    """
    regex_match = re.search(r"#\s*([\d\-\.]+)", giocata_text)
    if not regex_match:
        error_message = f"giocata_model.get_giocata_num_from_giocata: giocata num not found from {giocata_text}"
        lgr.logger.error(error_message)
        raise custom_exceptions.GiocataParsingError(f"numero della giocata non trovato")
    return regex_match.group(1)


def get_quota_from_giocata(giocata_text: str) -> int:
    """Gets the quota from a giocata text.

    Args:
        giocata_text (str)

    Raises:
        custom_exceptions.GiocataParsingError: in case the quota cannot be found

    Returns:
        int: the quota as a integer number (1.10 => 110)
    """
    MULTIPLE_QUOTA_EMOJI = "🧾"
    if MULTIPLE_QUOTA_EMOJI in giocata_text:
        regex_match = re.search(fr"{MULTIPLE_QUOTA_EMOJI}\s*(\d+\.\d+)\s*{MULTIPLE_QUOTA_EMOJI}", giocata_text)
    else:
        SINGLE_QUOTA_EMOJI = "📈"
        regex_match = re.search(fr"{SINGLE_QUOTA_EMOJI}\s*Quota\s*(\d+\.\d+)\s*{SINGLE_QUOTA_EMOJI}", giocata_text)
    if not regex_match:
        error_message = f"giocata_model.get_quota_from_giocata: quota not found from {giocata_text}"
        lgr.logger.error(error_message)
        raise custom_exceptions.GiocataParsingError(f"quota non trovata")
    return int(float(regex_match.group(1))*100)


def get_stake_from_giocata(giocata_text: str) -> int:
    """Gets the stake from a giocata message.

    Args:
        giocata_text (str)

    Raises:
        custom_exceptions.GiocataParsingError: in case the stake cannot be found

    Returns:
        int: the stake percentage value
    """
    # STAKE_EMOJI = "🏛"
    regex_match = re.search(STAKE_PATTERN, giocata_text)
    if not regex_match:
        error_message = f"giocata_model.get_stake_from_giocata: stake not found from {giocata_text}"
        lgr.logger.error(error_message)
        raise custom_exceptions.GiocataParsingError(f"stake non trovato")
    return int(float(regex_match.group(1).replace(",", "."))*100)


def parse_giocata(giocata_text: str, message_sent_timestamp: float=None) -> Optional[Dict]:
    """Parses the giocata found in giocata_text.
    In case message_sent_timestamp is not specified, the current date timestamp is used.
    An example of a giocata is:
        🏀 Exchange 🏀
        🇮🇹Supercoppa Serie A🇮🇹
        ⚜️ MaxExchange  ⚜️

        Trieste 🆚 Trento
        🧮 1 inc overtime 🧮
        📈 Quota 1.55 📈

        Cremona 🆚 Sassari
        🧮 2 inc overtime 🧮
        📈 Quota 1.30 📈

        🧾 2.02 🧾 

        🕑 18:30 🕑 

        🏛 Stake 5% 🏛
        🖊 Exchange #8🖊
    
    The structure is:
        <sport emoji> <sport name> <sport emoji>
        <emoji><campionato><emoji>
        ⚜️ <strategy name> ⚜️

        <One or more sport event with bet type and quota>

        [🧾 <cumulative quota> 🧾](only in case of multiple events)

        🕑 <sport event time> 🕑

        🏛 Stake <stake %>% 🏛
        🖊 <sport name> #<giocata number> 🖊
    Args:
        giocata_text (str)
        message_sent_timestamp (float, optional): the timestamp of the giocata message. Defaults to None.

    Returns:
        dict: contains the giocata data
        None: in case there is an error parsing the giocata
    """
    sport = get_sport_name_from_giocata(giocata_text)
    strategy = get_strategy_name_from_giocata(giocata_text, sport)
    giocata_num = get_giocata_num_from_giocata(giocata_text)
    giocata_quota = get_quota_from_giocata(giocata_text)
    giocata_stake = get_stake_from_giocata(giocata_text)
    if not message_sent_timestamp:
        message_sent_timestamp = datetime.datetime.utcnow().timestamp()
    parsed_giocata = create_base_giocata()
    parsed_giocata["sport"] = sport
    parsed_giocata["strategy"] = strategy
    parsed_giocata["giocata_num"] = giocata_num
    parsed_giocata["base_quota"] = giocata_quota
    parsed_giocata["base_stake"] = giocata_stake
    parsed_giocata["sent_timestamp"] = message_sent_timestamp
    parsed_giocata["raw_text"] = giocata_text
    return parsed_giocata


def personalize_giocata_text(giocata_text: str, personal_stakes: List, sport_name: str, strategy_name: str) -> str:
    if personal_stakes == []:
        return giocata_text
    giocata_quota = get_quota_from_giocata(giocata_text)
    for personal_stake in personal_stakes:
        # * check sport and strategy
        personal_stake_sport = personal_stake["sport"] 
        personal_stake_strategies = personal_stake["strategies"]
        if ((personal_stake_sport != "all" and personal_stake_sport != sport_name) or 
            (not "all" in personal_stake_strategies and not strategy_name in personal_stake_strategies)):
            continue
        # * check quota in range
        if personal_stake["min_quota"] > giocata_quota or personal_stake["max_quota"] < giocata_quota:
            continue
        # * modify stake
        giocata_text = re.sub(STAKE_PATTERN, f"Stake {personal_stake['stake'] / 100:.2f}", giocata_text)
        break
    giocata_text_rows = giocata_text.split("\n")
    giocata_text_rows = giocata_text_rows[:-1] + ["(stake personalizzato)", "", giocata_text_rows[-1]]
    giocata_text = "\n".join(giocata_text_rows)
    return giocata_text
