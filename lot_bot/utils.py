import datetime
import random
import re
import string
from typing import Dict, List, Optional, Tuple

from dateutil.relativedelta import relativedelta

from lot_bot import constants as cst
from lot_bot import logger as lgr
from lot_bot.dao import user_manager
from lot_bot.models import giocate as giocata_model
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot import custom_exceptions
from lot_bot import filters


def check_sport_strategy_validity(sport: spr.Sport, strategy_token: str) -> bool:
    strategy = strat.strategies_container.get_strategy(strategy_token.lower().strip())
    if sport and strategy and strategy in sport.strategies:
        return strategy


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
    error_message = f"utils.get_sport_name_from_giocata: Could not find in any sport in line {sport_row}"
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
        error_message = f"utils.get_strategy_name_from_giocata: Strategy {played_strategy} not found from {text} for sport {sport.name}"
        lgr.logger.error(error_message)
        raise custom_exceptions.GiocataParsingError(f"strategia '{played_strategy}' non trovata per lo sport '{sport.name}'")


def get_emoji_for_cashout_percentage(percentage_text: str) -> str:
    """Returns the emoji relative to the cashout percentage sign.
    The percentage text can either be integer number or a floating point
    number, with a "," or a "." dividing the decimal part. Additionally,
    it can have a "+" or a "-" sign as a first character.

    Args:
        percentage_text (str): the token of the message containing
            the cashout percentage

    Returns:
        str: 🟢 for a positive cashout,  
             🔴 for a negative cashout,
             ⚪️ for a neutral cashout 

            an empty string in case of errors

    Raises:
        e (Exception): in case of errors in the parsing
    """
    if "," in percentage_text:
        percentage_text = percentage_text.replace(",", ".")
    try:
        if float(percentage_text) > 0:
            return  "🟢"
        elif float(percentage_text) < 0:
            return "🔴"
        else: 
            return "⚪️"
    except Exception as e:
        lgr.logger.error(f"Could not parse the cashout percentage {percentage_text}")
        return ""


def create_cashout_message(message_text: str) -> str: 
    """Creates the cashout message to be broadcasted from a cashout message text.
    The message_text needs to be in the form "#<giocata id> +|-<percentage>.
    The final cashout message has the form:
    🟢|🔴 CASHOUT Exchange <giocata id> +|-<percentage>% 🟢|🔴 or
    ⚪️ Exchange #<giocata id> ABBINATA ⚪️

    Args:
        message_text (str): the text of the message containing the cashout.

    Returns:
        str: the cashout message to be broadcasted,
            or an empty string in case of errors
    """
    matches = re.search(filters.get_cashout_pattern(), message_text)
    giocata_num = matches.group(1)
    cashout_percentage = matches.group(2)
    emoji = get_emoji_for_cashout_percentage(cashout_percentage)
    if int(cashout_percentage) == 0:
        return f"{emoji} Exchange #{giocata_num} ABBINATA {emoji}"
    else:        
        return f"{emoji} CASHOUT Exchange #{giocata_num} {cashout_percentage}% {emoji}"



def generate_referral_code() -> str:
    """Generates a random referral code.
    The pattern is lot-ref-<8 chars among digits and lowercase letters>

    Returns:
        str: the referral code
    """
    code_chars = string.ascii_lowercase + string.digits
    return "".join((random.choice(code_chars) for x in range(cst.REFERRAL_CODE_LEN))) + "-lot"


def check_referral_code_availability(new_referral: str) -> bool:
    return user_manager.retrieve_user_id_by_referral(new_referral) is None


def create_valid_referral_code() -> str:
    """Creates a valid referral code for a new user, generating them
    until one which is not already used is found.

    Returns:
        str: a valid referral code
    """
    new_referral = ""
    while True:
        new_referral = generate_referral_code()
        if check_referral_code_availability(new_referral):
            break
    return new_referral


def extend_expiration_date(expiration_date_timestamp: float, giorni_aggiuntivi: int) -> float:
    """Adds giorni_aggiuntivi to the expiration date timestamp in case it is in the future,
    otherwise it adds giorni_aggiuntivi to the current timestamp.

    Args:
        expiration_date_timestamp (float)
        giorni_aggiuntivi (int)

    Returns:
        float: the original timestamp + giorni_aggiuntivi
    """
    now_timestamp = datetime.datetime.utcnow().timestamp()
    if datetime.datetime.utcnow().timestamp() > expiration_date_timestamp:
        base_timestamp = now_timestamp
    else:
        base_timestamp = expiration_date_timestamp
    return (datetime.datetime.utcfromtimestamp(base_timestamp) + relativedelta(days=giorni_aggiuntivi)).timestamp()


######################################## TESTING #############################################

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
        error_message = f"utils.get_giocata_num_from_giocata: giocata num not found from {giocata_text}"
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
        error_message = f"utils.get_quota_from_giocata: quota not found from {giocata_text}"
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
    regex_match = re.search(fr"\s*Stake\s*(\d+[.,]?\d*)\s*", giocata_text)
    if not regex_match:
        error_message = f"utils.get_stake_from_giocata: stake not found from {giocata_text}"
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
    parsed_giocata = giocata_model.create_base_giocata()
    parsed_giocata["sport"] = sport
    parsed_giocata["strategy"] = strategy
    parsed_giocata["giocata_num"] = giocata_num
    parsed_giocata["base_quota"] = giocata_quota
    parsed_giocata["base_stake"] = giocata_stake
    parsed_giocata["sent_timestamp"] = message_sent_timestamp
    parsed_giocata["raw_text"] = giocata_text
    return parsed_giocata


def get_giocate_since_timestamp(giocate: List[Dict], giocate_since_timestamp: float) -> List[Dict]:
    giocate_to_return = []
    for giocata in giocate:
        if giocata["timestamp"] >= giocate_since_timestamp:
            giocate_to_return.append(giocata)
    return giocate_to_return


def create_resoconto_message(giocate: List[Dict]):
    # Resoconto 24-09-2021
    # 1) Calcio#1124 @2.20 Stake 3%(3€) = +3,60%(+3,60€)
    lgr.logger.debug(f"Creating resoconto with giocate {giocate}")
    # resoconto_message = f"Resoconto {datetime.date.today().strftime('%d-%m-%Y')}\n"
    resoconto_message = ""
    for index, giocata in enumerate(giocate, 1):
        outcome_percentage = giocata_model.get_outcome_percentage(giocata["outcome"], giocata["base_stake"], giocata["base_quota"])
        if outcome_percentage > 0:
            outcome_emoji = "🟢"
        elif outcome_percentage == 0:
            outcome_emoji = "🕔" # TODO add even case 
        else:
            outcome_emoji = "🔴"
        parsed_quota = giocata["base_quota"] / 100
        parsed_stake = giocata["base_stake"] / 100
        sport_name = spr.sports_container.get_sport(giocata['sport']).display_name
        resoconto_message += f"{index}) {sport_name} #{giocata['giocata_num']}: @{parsed_quota:.2f} Stake {parsed_stake:.2f}% = {outcome_percentage:.2f}% {outcome_emoji}\n"
    return resoconto_message


def get_sport_and_strategy_from_normal_message(message: str) -> Tuple[spr.Sport, strat.Strategy]:
    """Gets the sport and the strategy from the first row of 
    a /messaggio_abbonati command.

    Args:
        message (str): it has the form /messaggio_abbonati <sport> - <strategy>

    Raises:
        custom_exceptions.NormalMessageParsingError: in case the sport or the strategy are not valid

    Returns:
        Tuple[spr.Sport, strat.Strategy]: the sport and the strategy found
    """
    # text on the first line after the command
    first_row = message.split("\n")[0]
    matches = re.search(r"^\/messaggio_abbonati\s*([\w\s]+)\s*-\s*([\w\s]+)", first_row)
    if not matches:
        lgr.logger.error(f"Cannot parse {message} with {first_row=}")
        raise custom_exceptions.NormalMessageParsingError("messaggio non analizzabile, assicurati che segua la struttura '/messaggio_abbonati nomesport - nomestrategia'")
    sport_token = matches.group(1)
    sport = spr.sports_container.get_sport(sport_token)
    if not sport:
        lgr.logger.error(f"Sport {sport_token} not valid from normal message {message} - {first_row=}")
        raise custom_exceptions.NormalMessageParsingError(f"sport '{sport_token}' non valido")
    strategy_token = matches.group(2)
    strategy = strat.strategies_container.get_strategy(strategy_token)
    if not strategy or strategy not in sport.strategies:
        lgr.logger.error(f"Strategy {strategy_token} not valid from normal message {message} - {first_row=}")
        raise custom_exceptions.NormalMessageParsingError(f"strategia '{strategy_token}' non valida per lo sport '{sport}'")
    return sport, strategy
