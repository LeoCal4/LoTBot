import datetime
import random
import re
from typing import Dict, List, Optional, Tuple

from lot_bot import custom_exceptions, filters
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot.dao import giocate_manager

STAKE_PATTERN = r"\s*Stake\s*(\d+[.,]?\d*)\s*"

OUTCOME_EMOJIS = {
    "win": "🟢",
    "loss": "🔴",
    "?": "🕔",
    "neutral": "⚪",
    "abbinata": "⚪",
    "void": "🟡",
}

def create_base_giocata():
    return {
        "sport": "",
        "strategy": "",
        "giocata_num": "",
        "base_quota": 0, # quota (float) * 100 => (int)
        "base_stake": 0, # stake (float) * 100 => (int)
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


def get_teacherbet_giocata_outcome_data(tb_giocata_outcome:str) -> Tuple[str, str]:
    win_keywords = ["✅", "✔️", "☑️"]
    loss_keywords = ["❌", "❎"]
    matches = re.search(filters.get_teacherbet_giocata_outcome_pattern(), tb_giocata_outcome)
    # giocata_num = matches.group(1).strip() + f" {utils.get_month_and_year_string()}"
    giocata_num = matches.group(1).strip()
    if re.search(r"\d+/\d+", giocata_num) is None:
        giocata_num += f" {utils.get_month_and_year_string()}"
    outcome = matches.group(2).strip()
    if outcome in win_keywords:
        outcome = "win"
    elif outcome in loss_keywords:
        outcome = "loss"
    else:
        outcome = "neutral"
    return giocata_num, outcome


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
    """[summary]

    Args:
        outcome (str): [description]
        stake (int): [description]
        quota (int): [description]

    Returns:
        float: the outcome percentage (as in x.y%)
    """
    lgr.logger.debug(f"Calculating outcome percentage on {outcome} - {stake} - {quota}")
    if outcome == "win":
        outcome_percentage = (stake * (quota - 100)) / 10000
    elif outcome == "loss":
        outcome_percentage = -stake / 100
    else:
        outcome_percentage = 0.0
    return outcome_percentage


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
    if " (TEST)" in played_strategy:
        played_strategy = " ".join(played_strategy.split()[:-1])
    strategy = strat.strategies_container.get_strategy(played_strategy)
    sport = spr.sports_container.get_sport(sport)
    if strategy and strategy in sport.strategies:
        lgr.logger.debug(f"Parsed strategy {strategy.display_name}")
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
    """TODO tests

    Args:
        giocata_text (str): [description]
        personal_stakes (List): [description]
        sport_name (str): [description]
        strategy_name (str): [description]

    Returns:
        str: [description]
    """
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


def create_personal_giocata_from_new_giocata(retrieved_giocata: Dict, stake_from_giocata_message: str) -> Tuple[Dict, str]:
    personal_user_giocata = create_user_giocata()
    personal_user_giocata["original_id"] = retrieved_giocata["_id"]
    personal_user_giocata["acceptance_timestamp"] = datetime.datetime.utcnow().timestamp()
    # * check for differences in the saved stake and the current one (personalized stake)
    if stake_from_giocata_message != retrieved_giocata["base_stake"]:
        personal_user_giocata["personal_stake"] = stake_from_giocata_message
    return personal_user_giocata


def update_text_with_stake_money_value(text: str, user_budget: int, stake: int) -> str:
    try:
        percentage_index = text.index("%")
    except ValueError:
        print("VALUE ERROR ON UPDATE TEXT WIT STAKE MONEY VALUE")
        return text
    stake_money_value = (user_budget / 100) * (stake / 10000)
    return f"{text[:percentage_index+1]} ({stake_money_value:.2f}€){text[percentage_index+1:]}"


def update_giocata_text_with_stake_money_value(text: str, user_budget: int) -> str:
    parsed_giocata = parse_giocata(text)
    stake = parsed_giocata["base_stake"]
    return update_text_with_stake_money_value(text, user_budget, stake)


def update_outcome_text_with_money_value(text: str, user_budget: int, stake: int, quota: int, outcome: str) -> str:
    try:
        percentage_index = text.index("%")
    except ValueError:
        print("VALUE ERROR ON UPDATE TEXT WIT STAKE MONEY VALUE")
        return text
    outcome_percentage = get_outcome_percentage(outcome, stake, quota)
    outcome_money_value = (user_budget / 100) *  (outcome_percentage/ 100)
    return f"{text[:percentage_index+1]} ({outcome_money_value:.2f}€){text[percentage_index+1:]}"

  
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
    elif 0 <= trend_value < 2.5:
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
    elif 0 <= trend_value < 5:
        return "➡️"
    elif -10 <= trend_value < 0:
        return "↘️"
    else: # <= -10
        return "⬇️"


def get_trend_emoji(sport_name: str, trend_value: float) -> str:
    """Returns the trend arrow emoji for one of the following sports and the relative value:
         - Exchange
         - Calcio
         - Tennis
         - Pingpong (Tutto il resto strategy)
    For all the others, a empty string is returned.

    Args:
        sport_name (str)
        trend_value (float)

    Returns:
        str: the trend arrow emoji relative or an empty string
    """
    if sport_name == spr.sports_container.EXCHANGE.name:
        return get_exchange_trend_emoji(trend_value)
    elif sport_name == spr.sports_container.CALCIO.name or sport_name == spr.sports_container.TENNIS.name:
        return get_calcio_and_tennis_trend_emoji(trend_value)
    elif sport_name == spr.sports_container.PINGPONG.name:
        return get_ping_pong_trend_emoji(trend_value)
    return ""


def create_trend_counts_and_totals_for_giocate(latest_giocate: List) -> Dict[str, Tuple[int, float]]:
    """Creates the giocate count and percentage total to be used for a trend message, divided by sport.

    Args:
        latest_giocate (List): the giocate to count and calculate the percentage sport

    Returns:
        Dict[str, Tuple[int, float]]: a dict with sport names as keys and the relative giocate count and total percentage as items. 
    """
    trend_counts_and_totals = {}
    for giocata in latest_giocate:
        lgr.logger.debug(f"{giocata['sport']=} - {giocata['outcome']=}")
        # * skip void and unfinished giocate
        if giocata["outcome"] == "void" or giocata["outcome"] == "?":
            continue
        giocata_sport = spr.sports_container.get_sport(giocata["sport"])
        giocata_strategy = strat.strategies_container.get_strategy(giocata["strategy"])
        # * use strat names as sport for tutto il resto giocate
        if giocata_sport == spr.sports_container.TUTTOILRESTO and giocata_strategy != strat.strategies_container.BASE and giocata_strategy != strat.strategies_container.TEST:
            giocata_sport = giocata_strategy
        # * get the outcome percentage
        # * (use cashout value for maxexchange giocate)
        if "cashout" in giocata: # maxexchange
            outcome_percentage = giocata["cashout"] / 100
        # * (use fixed values for MB giocate)
        elif giocata_strategy == strat.strategies_container.MB: # mb
            if giocata["outcome"] == "win":
                outcome_percentage = 0.7
            elif giocata["outcome"] == "loss":
                outcome_percentage = -500
        elif "base_stake" in giocata and "base_quota" in giocata: # * (most of the others)
            outcome_percentage = get_outcome_percentage(giocata["outcome"], giocata["base_stake"], giocata["base_quota"])
        else:
            outcome_percentage = ""
        # * update dict with values
        if giocata_sport.name not in trend_counts_and_totals:
            trend_counts_and_totals[giocata_sport.name] = (1, outcome_percentage)
        else:
            giocate_count, total_percentage = trend_counts_and_totals[giocata_sport.name]
            trend_counts_and_totals[giocata_sport.name] = (giocate_count + 1, total_percentage + outcome_percentage)
    return trend_counts_and_totals


def create_trend_message(trend_counts_and_totals: Dict[str, Tuple[int, float]], days_for_trend: int = None) -> str:
    """Creates the trend message. If days_for_trend is not specified, it uses the giocate counts for the 
    overall trend, otherwise it is daily based.

    Args:
        trend_counts_and_totals (Dict[str, Tuple[int, float]])
        days_for_trend (int, optional): the number of days for the trend. Defaults to None.

    Raises:
        custom_exceptions.SportNotFoundError: in case one of the specified sports does not exist

    Returns:
        str: the trend message
    """
    trend_message = ""
    for key in trend_counts_and_totals:
        giocate_count, total_percentage = trend_counts_and_totals[key]
        # * check if the sport/strat exists
        giocata_sport = spr.sports_container.get_sport(key)
        if not giocata_sport:
            giocata_sport = strat.strategies_container.get_strategy(key)
            if not giocata_sport:
                lgr.logger.error(f"Could not find sport or strategy {key}")
                # raise custom_exceptions.SportNotFoundError(key)
                continue
        # * calculate sport trend
        if days_for_trend:
            sport_trend = round(total_percentage / days_for_trend, 2)
            lgr.logger.debug(f"{giocata_sport.display_name}: {total_percentage}% in {days_for_trend} giorni [{giocate_count} giocate] = {sport_trend}%")
        else:
            sport_trend = round(total_percentage / giocate_count, 2)
            lgr.logger.debug(f"{giocata_sport.display_name}: {total_percentage}% in {giocate_count} giocate = {sport_trend}%")
        # * create trend entry for sport
        trend_emoji = get_trend_emoji(giocata_sport.name, sport_trend)
        percentage_string = ""
        if giocata_sport.name != spr.sports_container.EXCHANGE.name:
            percentage_string = f"Totale: {total_percentage:.2f}% - Media: {sport_trend:.2f}% "
        trend_message += f"{giocata_sport.emoji} {giocata_sport.display_name}: {percentage_string}{trend_emoji}\n"
    return trend_message


def get_giocate_trend_message_since_days(days_for_trend: int) -> str:
    last_midnight = datetime.datetime.combine(datetime.datetime.today(), datetime.time.min)
    days_for_trend_midnight = last_midnight - datetime.timedelta(days=days_for_trend) 
    latest_giocate = giocate_manager.retrieve_giocate_between_timestamps(last_midnight.timestamp(), 
        days_for_trend_midnight.timestamp(), 
        include_only_giocate_with_outcome=True, 
        exclude_sports_not_in_trend=True)
    lgr.logger.info(f"Retrieving giocate from {days_for_trend_midnight} to {last_midnight}")
    trend_counts_and_totals = create_trend_counts_and_totals_for_giocate(latest_giocate)
    trend_message = create_trend_message(trend_counts_and_totals, days_for_trend=days_for_trend)
    start_date = days_for_trend_midnight.strftime("%d/%m/%Y")
    end_date = last_midnight.strftime("%d/%m/%Y")
    trend_message = f"✍️ LoT TREND ({start_date} - {end_date})\n\n" + trend_message
    return trend_message


def get_giocate_trend_for_lastest_n_giocate(num_of_giocate_for_trend: int):
    lgr.logger.info(f"Retrieving last {num_of_giocate_for_trend} giocate to create trend")
    latest_giocate = giocate_manager.retrieve_last_n_giocate(num_of_giocate_for_trend, 
        include_only_giocate_with_outcome=True, 
        exclude_sports_not_in_trend=True)
    trend_counts_and_totals = create_trend_counts_and_totals_for_giocate(latest_giocate)
    trend_message = create_trend_message(trend_counts_and_totals)
    trend_message = f"✍️ LoT TREND (ultime {num_of_giocate_for_trend} giocate)\n\n" + trend_message
    return trend_message


def parse_teacherbet_giocata(text: str, message_sent_timestamp: float=None, add_month_year_to_raw_text:bool=False) -> List[Dict]:
    """
    Example:
        UPDATE: 21/11/2021 21:51 GMT+1

        NOW GOAL FULL


        ⏳ Status: 🔴 1-1 17' 1T
        🏆 Primera Division de Colombiano-Apertura
        ⚽️ Atletico Nacional Medellin - Millonarios
        💰 Alert BTTS ▶️
        #65

    Args:
        text (str): [description]
        message_sent_timestamp (float, optional): [description]. Defaults to None.
        add_month_year_to_raw_text (bool, optional): [description]. Defaults to False.

    Returns:
        List[Dict]: [description]
    """
    parsed_giocate = []
    # regex_pattern = r"⏳(?:[^▶️]?[^▶]?)+[▶️▶]" if is_raw else r"⏳[^#]+#\d+"
    regex_pattern = r"⏳[^#]+#\d+(?:\s\d+/\d+)?"
    raw_giocate = re.findall(regex_pattern, text)
    if not message_sent_timestamp:
        message_sent_timestamp = datetime.datetime.utcnow().timestamp()
    base_giocata = create_base_giocata()
    base_giocata["sport"] = spr.sports_container.TEACHERBET.name
    base_giocata["strategy"] = strat.strategies_container.TEACHERBETLUXURY.name
    del base_giocata["base_quota"]
    del base_giocata["base_stake"]
    for raw_giocata in raw_giocate:
        parsed_giocata = base_giocata.copy()
        parsed_giocata["giocata_num"] = re.search(r"#(\d+(?:\s\d+/\d+)?)", raw_giocata).group(1)
        if add_month_year_to_raw_text:
            month_and_year_string = utils.get_month_and_year_string()
            raw_giocata += f" {month_and_year_string}"
            if re.search(r"\s+\d+/\d+", parsed_giocata["giocata_num"]) is None:
                parsed_giocata["giocata_num"] += f" {month_and_year_string}"
        parsed_giocata["raw_text"] = raw_giocata
        parsed_giocate.append(parsed_giocata)
    return parsed_giocate
