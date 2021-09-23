import random
import string

from lot_bot import logger as lgr
from lot_bot.dao import user_manager
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat


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
        None: if the sport was not found
    """
    sport_row = text.split("\n")[0].lower()
    # ? could be faster if we would just get the second token
    for sport in spr.sports_container:
        if sport.display_name.lower() in sport_row:
            return sport.name
    lgr.logger.error(f"Could not find in any sport in line {sport_row}")
    return None


def get_strategy_from_giocata(text: str) -> str:
    """Extracts the strategy name from a giocata message.

    Args:
        text (str): a giocata message

    Returns:
        str: the name of the strategy or empty string if it's not valid
    """
    STRATEGY_ROW = 2
    STRATEGY_INDEX = 1
    played_strategy = text.split("\n")[STRATEGY_ROW].split()[STRATEGY_INDEX]
    sport = get_sport_from_giocata(text)
    if check_sport_validity(sport) and check_sport_strategy_validity(sport, played_strategy):
        return played_strategy.lower().strip()
    else:
         return ""


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
    giocata_id = message_tokens[0]
    cashout_percentage = message_tokens[1]
    emoji = get_emoji_for_cashout_percentage(cashout_percentage)
    if emoji == "":
        lgr.logger.error(f"Error parsing cashout message {message_text}")
        return ""
    return f"{emoji} CASHOUT Exchange {giocata_id} {cashout_percentage}% {emoji}"



######################################## TESTING #############################################
"""
🏀 Exchange 🏀
🇮🇹Supercoppa Serie A🇮🇹
⚜️  MaxExchange  ⚜️

Trieste 🆚 Trento
🧮 1 inc overtime 🧮
📈 Quota 1.55 📈

Cremona 🆚 Sassari
🧮 2 inc overtime 🧮
📈 Quota 1.30 📈

🧾 2.02 🧾 

🕑 18:30 🕑 

🏛 Stake 5% 🏛
🖊 hockey #8🖊
"""
def parse_giocata(giocata_text: str) -> dict:
    # giocata_rows = giocata_text.split("\n")
    # TODO che informazioni salvare
    sport = get_sport_from_giocata(giocata_text)
    strategy = get_strategy_from_giocata(giocata_text)
    parsed_giocata = {
        "sport": sport,
        "strategia": strategy,
        "raw_text": giocata_text
    }
    return parsed_giocata


def generate_referral_code() -> str:
    """Generates a valid referral code for a new user, trying again until
    it is not already used.

    The pattern is lot-ref-<8 chars among digits and lowercase letters>

    Returns:
        str: a valid referral code
    """
    REFERRAL_CODE_LEN = 8
    code_chars = string.ascii_lowercase + string.digits
    new_referral = ""
    while True:
        new_referral = "lot-ref-" + "".join((random.choice(code_chars) for x in range(REFERRAL_CODE_LEN)))
        if user_manager.retrieve_user_by_referral(new_referral) is None:
            break
    return new_referral
