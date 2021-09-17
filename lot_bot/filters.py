from telegram.ext.filters import Filters

from lot_bot import config as cfg
from lot_bot import constants as cst


def get_giocata_filter() -> Filters:
    """Creates the filter for the giocate. It checks if the
    sender id is among the ones of the sport channels and if
    the message contains "Stake" and the giocata emoji.

    Returns:
        Filter
    """
    GIOCATA_EMOJI = "⚜️"
    sport_channels_filter = Filters.chat()
    sport_channels_filter.add_chat_ids(cfg.config.SPORTS_CHANNELS_ID.values())
    giocata_text_filter = Filters.regex("Stake") & Filters.regex(GIOCATA_EMOJI)
    return sport_channels_filter & giocata_text_filter


def get_normal_messages_filter() -> Filters:
    """Creates the filter that gets all the non-command
    text messages.

    Returns:
        Filters
    """
    return (Filters.text & (~ Filters.command))


def get_cashout_filter() -> Filters:
    """Creates the filter for the cashout messages of the Exchange channel.
    Cashout messages must attive from the Exchange channel and have the form:
         #<numero giocata> (+|-)<giocata percentage>
    For simplicity/possibile human errors in writing the messages, we only check whetever it 
    starts with #.

    Returns:
        Filters
    """
    exchange_channel_filter = Filters.chat(cfg.config.SPORTS_CHANNELS_ID["exchange"])
    # looks for any number of spaces and then #
    cashout_text_filter = Filters.regex(r"^\s*#")
    return exchange_channel_filter & cashout_text_filter


def get_sport_channel_normal_message_filter() -> Filters:
    """Creates the filter for all text messages coming from any 
    sport channels.
    Regardless, they should have the form:
    <sport> <strategy>
    <...> 

    Returns:
        Filters: [description]
    """
    sport_channels_filter = Filters.chat()
    sport_channels_filter.add_chat_ids(cfg.config.SPORTS_CHANNELS_ID.values())
    return sport_channels_filter & Filters.text

def get_homepage_filter() -> Filters:
    return Filters.regex(cst.HOMEPAGE_BUTTON_TEXT)


# ================================================ PATTERNS ================================================


def get_explanation_pattern() -> str:
    """
    explanation_(<str1>|<str2>|...|<strN>)

    Returns:
        str: [description]
    """
    pattern = "explanation_("
    for strategy in cst.STRATEGIES_DISPLAY_NAME.keys():
        pattern += strategy + "|"
    return pattern[:-1] + ")"

