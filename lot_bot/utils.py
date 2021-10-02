import datetime
from logging import error
import random
import re
import string
from typing import Dict, List, Optional

from dateutil.relativedelta import relativedelta

from lot_bot import constants as cst
from lot_bot import logger as lgr
from lot_bot.dao import user_manager
from lot_bot.models import giocate as giocata_model
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot import custom_exceptions


def check_sport_validity(sport_token: str) -> bool:
    return sport_token and bool(spr.sports_container.get_sport_from_string(sport_token.lower().strip()))


def check_sport_strategy_validity(sport_token: str, strategy_token: str) -> bool:
    sport = spr.sports_container.get_sport_from_string(sport_token.lower().strip())
    strategy = strat.strategies_container.get_strategy_from_string(strategy_token.lower().strip())
    return sport and strategy and strategy in sport.strategies


def get_sport_from_giocata(text: str) -> str:
    """Extracts the sport name from a giocata message.

    Args:
        text (str): a giocata message

    Returns:
        str: the name of the sport
    
    Raises:
        Exception: if the sport was not found
    """
    sport_row = text.split("\n")[0].lower()
    # ? could be faster if we would just get the second token
    for sport in spr.sports_container:
        if sport.display_name.lower() in sport_row:
            return sport.name
    error_message = f"utils.get_sport_from_giocata: Could not find in any sport in line {sport_row}"
    lgr.logger.error(error_message)
    raise Exception(error_message)


def get_strategy_from_giocata(text: str) -> str:
    """Extracts the strategy name from a giocata message.

    Args:
        text (str): a giocata message

    Returns:
        str: the name of the strategy
        
    Raises:
        Exception: if the strategy is not found
    """
    STRATEGY_ROW = 2
    STRATEGY_INDEX = 1
    played_strategy = text.split("\n")[STRATEGY_ROW].split()[STRATEGY_INDEX]
    sport = get_sport_from_giocata(text)
    if check_sport_validity(sport) and check_sport_strategy_validity(sport, played_strategy):
        return played_strategy.lower().strip()
    else:
        error_message = f"utils.get_strategy_from_giocata: Strategy not found from {text}"
        lgr.logger.error(error_message)
        raise Exception(error_message)


def get_emoji_for_cashout_percentage(percentage_text: str) -> str:
    """Returns the emoji relative to the cashout percentage sign.
    The percentage text can either be integer number or a floating point
    number, with a "," or a "." dividing the decimal part. Additionally,
    it can have a "+" or a "-" sign as a first character.

    Args:
        percentage_text (str): the token of the message containing
            the cashout percentage

    Returns:
        str: 🟢 for a non-negative cashout,  
            🔴 for a negative cashout,  
            an empty string in case of errors
    """
    if "," in percentage_text:
        percentage_text = percentage_text.replace(",", ".")
    try:
        if float(percentage_text) >= 0:
            return  "🟢"
        else:
            return "🔴"
    except Exception as e:
        lgr.logger.error(f"Could not parse the cashout percentage {percentage_text}")
        lgr.logger.error(f"Exception: {e}")
        return ""


def create_cashout_message(message_text: str) -> str: 
    """Creates the cashout message to be broadcasted from a cashout message text.
    The message_text needs to be in the form "#<giocata id> +|-<percentage>.
    The final cashout message has the form:
    🟢|🔴 CASHOUT Exchange <giocata id> +|-<percentage>% 🟢|🔴

    Args:
        message_text (str): the text of the message containing the cashout.

    Returns:
        str: the cashout message to be broadcasted,
            or an empty string in case of errors

    """
    message_tokens = message_text.split()
    giocata_num = message_tokens[0]
    cashout_percentage = message_tokens[1]
    emoji = get_emoji_for_cashout_percentage(cashout_percentage)
    if emoji == "":
        lgr.logger.error(f"Error parsing cashout message {message_text}")
        return ""
    return f"{emoji} CASHOUT Exchange {giocata_num} {cashout_percentage}% {emoji}"


def generate_referral_code() -> str:
    """Generates a random referral code.
    The pattern is lot-ref-<8 chars among digits and lowercase letters>

    Returns:
        str: the referral code
    """
    code_chars = string.ascii_lowercase + string.digits
    return "".join((random.choice(code_chars) for x in range(cst.REFERRAL_CODE_LEN))) + "-lot"


def check_referral_code_availability(new_referral: str) -> bool:
    return user_manager.retrieve_user_by_referral(new_referral) is None


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


def extend_expiration_date(expiration_date_timestamp: float) -> float:
    """Adds one month to the expiration date timestamp.

    Args:
        expiration_date_timestamp (float)

    Returns:
        float: the original timestamp + 1 month
    """        
    return (datetime.datetime.utcfromtimestamp(expiration_date_timestamp) + relativedelta(months=1)).timestamp()


######################################## TESTING #############################################

def get_giocata_num_from_giocata(giocata_text: str) -> str:
    GIOCATA_NUM_EMOJI = "🖊"
    regex_match = re.search(fr"#\s*(\d+)\s*{GIOCATA_NUM_EMOJI}", giocata_text)
    if not regex_match:
        error_message = f"utils.get_giocata_num_from_giocata: giocata num not found from {giocata_text}"
        lgr.logger.error(error_message)
        raise Exception(error_message)
    return regex_match.group(1)


def get_quota_from_giocata(giocata_text: str) -> int:
    MULTIPLE_QUOTA_EMOJI = "🧾"
    if MULTIPLE_QUOTA_EMOJI in giocata_text:
        regex_match = re.search(fr"{MULTIPLE_QUOTA_EMOJI}\s*(\d+\.\d+)\s*{MULTIPLE_QUOTA_EMOJI}", giocata_text)
    else:
        SINGLE_QUOTA_EMOJI = "📈"
        regex_match = re.search(fr"{SINGLE_QUOTA_EMOJI}\s*Quota(\d+\.\d+)\s*{SINGLE_QUOTA_EMOJI}", giocata_text)
    if not regex_match:
        error_message = f"utils.get_quota_from_giocata: quota not found from {giocata_text}"
        lgr.logger.error(error_message)
        raise Exception(error_message)
    return int(float(regex_match.group(1))*100)


def get_stake_from_giocata(giocata_text: str) -> int:
    STAKE_EMOJI = "🏛"
    regex_match = re.search(fr"{STAKE_EMOJI}\s*Stake\s*(\d+)\s*%\s*{STAKE_EMOJI}", giocata_text)
    if not regex_match:
        error_message = f"utils.get_stake_from_giocata: stake not found from {giocata_text}"
        lgr.logger.error(error_message)
        raise Exception(error_message)
    return int(regex_match.group(1))


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
        giocata_text (str): [description]
        message_sent_timestamp (float, optional): the timestamp of the giocata message. Defaults to None.

    Returns:
        dict: contains the giocata data
        None: in case there is an error parsing the giocata
    """
    try:
        sport = get_sport_from_giocata(giocata_text)
        strategy = get_strategy_from_giocata(giocata_text)
        giocata_num = get_giocata_num_from_giocata(giocata_text)
        giocata_quota = get_quota_from_giocata(giocata_text)
        giocata_stake = get_stake_from_giocata(giocata_text)
    except Exception as e:
        error_message = f"Error parsing giocata {giocata_text}"
        lgr.logger.error(error_message)
        lgr.logger.error(str(e))
        raise Exception(error_message)
    if not message_sent_timestamp:
        message_sent_timestamp = datetime.datetime.utcnow().timestamp()
    parsed_giocata = giocata_model.create_base_giocata()
    parsed_giocata["sport"] = sport
    parsed_giocata["strategia"] = strategy
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
    resoconto_message = f"Resoconto {datetime.date.today().strftime('%d-%m-%Y')}\n"
    for index, giocata in enumerate(giocate, 1):
        outcome_percentage = giocata_model.get_outcome_percentage(giocata["outcome"], giocata["base_stake"], giocata["base_quota"])
        parsed_quota = giocata["base_quota"] / 100
        sport_name = spr.sports_container.get_sport_from_string(giocata['sport']).display_name
        resoconto_message += f"{index}) {sport_name} #{giocata['giocata_num']}: @{parsed_quota:.2f} Stake {giocata['base_stake']}% = {outcome_percentage:.2f}%\n"
    return resoconto_message
