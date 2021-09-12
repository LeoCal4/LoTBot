from telegram.ext.filters import Filters

from lot_bot import config as cfg


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
    exchange_channel_filter = Filters.chat(cfg.config.SPORTS_CHANNELS_ID["exchange"])
    cashout_text_filter = Filters.regex(r"^\s*#")
    return exchange_channel_filter & cashout_text_filter
