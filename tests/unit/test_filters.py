import datetime

import random
from lot_bot import filters
from lot_bot import config as cfg
from telegram import Chat, Message, Update, User

def get_update_from_sports_channel():
    sports_channel_id = random.choice(list(cfg.config.SPORTS_CHANNELS_ID.values()))
    return Update(
            0,
            Message(
                0,
                datetime.datetime.utcnow(),
                Chat(sports_channel_id, "private"),
                from_user=User(0, "Testuser", False),
                via_bot=User(0, "Testbot", True),
                sender_chat=Chat(0, "Channel"),
                forward_from=User(0, "HAL9000", False),
                forward_from_chat=Chat(0, "Channel"),

            ),
    )

def test_get_correct_giocata_filter(correct_giocata: tuple):
    update = get_update_from_sports_channel()
    update.message.text, _, _ = correct_giocata
    giocata_filter = filters.get_giocata_filter()
    assert giocata_filter(update) != False, "Giocata filter not working for correct giocata message"


def test_get_wrong_giocata_filter():
    update = get_update_from_sports_channel()
    giocata_filter = filters.get_giocata_filter()
    update.message.text = "random message"
    assert giocata_filter(update) == False, "Giocata filter not working for wrong giocata message"
