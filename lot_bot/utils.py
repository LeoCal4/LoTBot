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

