import datetime
import re
from typing import Dict, List, Optional, Tuple

from pymongo import database

from lot_bot import custom_exceptions, filters
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot.dao import giocate_manager

STAKE_PATTERN = r"\s*Stake\s*(\d+[.,]?\d*)\s*"


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
    win_keywords = ["vincente", "vinta", "vittoria", "vincita", "positiva", "positivo"]
    loss_keywords = ["perdente", "persa", "perdita", "sconfitta", "negativa", "negativo"]
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
    """Extracts the giocata number and the cashout percentage from a cashout message.

    Args:
        cashout_message (str)

    Raises:
        custom_exceptions.GiocataOutcomeParsingError: in case there are less than 2 tokens
        custom_exceptions.GiocataOutcomeParsingError: in case the percentage is not a valid float

    Returns:
        Tuple[str, int]: giocata number and cashout percentage
    """
    # cashout_tokens = cashout_message.strip().split()
    match_results = re.match(filters.get_cashout_pattern(), cashout_message.strip())
    # * check if both id and % are present
    if not match_results:
        raise custom_exceptions.GiocataOutcomeParsingError("\nIndicare il numero della giocata e mese/anno, preceduti da #, e la percentuale del cashout [esempio: #123 01/21 15]")
    giocata_num = match_results.group(1).strip()
    # * convert cashout percentage to int
    try:
        cashout_percentage = utils.parse_float_string_to_int(match_results.group(2))
    except Exception as e:
        lgr.logger.error(f"During cashout parsing - {str(e)}")
        raise custom_exceptions.GiocataOutcomeParsingError("\nPercentuale di cashout non valida")

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
    TODO just create a dict

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
    regex_match = re.search(filters.get_giocata_num_pattern(), giocata_text)
    if not regex_match:
        error_message = f"giocata_model.get_giocata_num_from_giocata: giocata num not found from {giocata_text}"
        lgr.logger.error(error_message)
        raise custom_exceptions.GiocataParsingError(f"numero della giocata non trovato o non corretto. Assicurati che tu abbia usato la seguente struttura: [nome_sport #numero_giocata mese/anno]")
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


def get_exchange_trend_emoji(trend_value: float) -> str:
    if trend_value >= 2:
        return "⬆️"
    elif 0 < trend_value < 2:
        return "↗️"
    elif trend_value == 0:
        return "➡️"
    elif -8 < trend_value < 0:
        return "↘️"
    else: # <= -8
        return "⬇️"


def get_calcio_and_tennis_trend_emoji(trend_value: float) -> str:
    if trend_value >= 5:
        return "⬆️"
    elif 2.5 <= trend_value < 5:
        return "↗️"
    elif 0 < trend_value < 2.5:
        return "➡️"
    elif -5 < trend_value < 0:
        return "↘️"
    else: # <= -5
        return "⬇️"


def get_ping_pong_trend_emoji(trend_value: float) -> str:
    if trend_value >= 10:
        return "⬆️"
    elif 5 <= trend_value < 10:
        return "↗️"
    elif 0 < trend_value < 5:
        return "➡️"
    elif -10 < trend_value < 0:
        return "↘️"
    else: # <= -10
        return "⬇️"


def get_trend_emoji(sport_name: str, trend_value: float) -> str:
    if sport_name == spr.sports_container.EXCHANGE.name:
        return get_exchange_trend_emoji(trend_value)
    elif sport_name == spr.sports_container.CALCIO.name or spr.sports_container.TENNIS.name:
        return get_calcio_and_tennis_trend_emoji(trend_value)
    if sport_name == strat.strategies_container.PINGPONG:
        return get_ping_pong_trend_emoji(trend_value)


def get_giocate_trend_since_days(days_for_trend: int) -> str:
    last_midnight = datetime.datetime.combine(datetime.datetime.today(), datetime.time.min)
    days_for_trend_midnight = last_midnight - datetime.timedelta(days=days_for_trend) 
    latest_giocate = giocate_manager.retrieve_giocate_between_timestamps(last_midnight.timestamp(), days_for_trend_midnight.timestamp())
    trend_counts_and_totals = {}
    for giocata in latest_giocate:
        # * skip void and unfinished giocate
        if giocata["outcome"] == "void" or giocata["outcome"] == "?":
            continue
        lgr.logger.debug(f"{giocata['sport']=} - {giocata['outcome']=}")
        # * use cashout value for maxexchange giocate
        giocata_sport = giocata["sport"]
        # * use strat names as sport for tutto il resto giocate
        if giocata_sport == "tuttoilresto":
            giocata_sport = giocata["strategy"]
        # * get the outcome percentage
        if "cashout" in giocata: # maxexchange
            outcome_percentage = giocata["cashout"] / 100
        elif giocata["strategy"] == strat.strategies_container.MB.name: # mb
            if giocata["outcome"] == "win":
                outcome_percentage = 0.7
            elif giocata["outcome"] == "loss":
                outcome_percentage = -500
        else: # all the others
            outcome_percentage = get_outcome_percentage(giocata["outcome"], giocata["base_stake"], giocata["base_quota"])
        # * update dict with values
        if giocata_sport not in trend_counts_and_totals:
            trend_counts_and_totals[giocata_sport] = (1, outcome_percentage)
        else:
            giocate_count, total_percentage = trend_counts_and_totals[giocata_sport]
            trend_counts_and_totals[giocata_sport] = (giocate_count + 1, total_percentage + outcome_percentage)
    start_date = days_for_trend_midnight.strftime("%d/%m/%Y")
    end_date = last_midnight.strftime("%d/%m/%Y")
    trend_message = f"✍️ LoT TREND ({start_date} - {end_date})\n\n"
    for key in trend_counts_and_totals:
        giocate_count, total_percentage = trend_counts_and_totals[key]
        giocata_sport = spr.sports_container.get_sport(key)
        if not giocata_sport:
            giocata_sport = strat.strategies_container.get_strategy(key)
            if not giocata_sport:
                raise custom_exceptions.SportNotFoundError(key)
        # sport_trend = round(total_percentage / giocate_count, 2)
        daily_trend = round(total_percentage / days_for_trend, 2)
        lgr.logger.debug(f"{giocata_sport.display_name}: {total_percentage}% in {days_for_trend} giorni [{giocate_count} giocate] = {daily_trend}%")
        trend_emoji = get_trend_emoji(giocata_sport.name, daily_trend)
        percentage_string = ""
        if giocata_sport.name != spr.sports_container.EXCHANGE.name:
            percentage_string = f"Totale: {total_percentage:.2f}% - Media: {daily_trend:.2f}% - "
        trend_message += f"{giocata_sport.emoji} {giocata_sport.display_name}: {percentage_string}{trend_emoji}\n"
    return trend_message
