from telegram.ext.filters import Filters

from lot_bot import config as cfg


def get_giocata_filter():
    GIOCATA_EMOJI = "⚜️"
    sport_channels_filter = Filters.chat()
    sport_channels_filter.add_chat_ids(cfg.config.SPORTS_CHANNELS_ID.values())
    giocata_text_filter = Filters.regex("Stake") & Filters.regex(GIOCATA_EMOJI)
    return sport_channels_filter & giocata_text_filter
