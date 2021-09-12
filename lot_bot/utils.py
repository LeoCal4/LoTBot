from lot_bot import constants as cst
from lot_bot import logger as lgr


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
    for sport in cst.SPORTS:
        if sport in sport_row:
            return sport
    lgr.logger.error(f"Could not find {sport} in SPORTS")
    return None
    # TODO check
#     if channel_name == "Ping":
#         channel_name = "Ping Pong"
#     if channel_name == "Basebal":
#         channel_name = "Baseball"
#     return channel_name


def get_strategy_from_giocata(text: str) -> str:
    """Extracts the strategy name from a giocata message.

    Args:
        text (str): a giocata message


    Raises:
        Exception: in case the strategy cannot be found among the ones
            of the giocata's sport

    Returns:
        str: the name of the strategy
    """
    # TODO add a safer way to get it
    STRATEGY_ROW = 2
    STRATEGY_INDEX = 1
    played_strategy = text.split("\n")[STRATEGY_ROW].split()[STRATEGY_INDEX]
    # ! for some unknown reason, getting the strategy through find and splicing
    #   makes the resulting substring have some kind of invisible character at the beginning.
    # STRATEGY_EMOJI = "⚜️"
    # first_emoji_index = text.find(STRATEGY_EMOJI)
    # second_emoji_index = first_emoji_index + text[first_emoji_index+1:].find(STRATEGY_EMOJI)
    # # for some unknown reason .strip() does not work
    # played_strategy = text[first_emoji_index+1:second_emoji_index].replace(" ", "")
    sport = get_sport_from_giocata(text)
    if sport and played_strategy in cst.STRATEGIES[sport]:
        return played_strategy 
    else:
        lgr.logger.error(f"Could not find {played_strategy} in strategies for {sport}")
        raise Exception


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
