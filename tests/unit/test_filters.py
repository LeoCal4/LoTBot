import datetime
import random

import pytest
from lot_bot import config as cfg
from lot_bot import filters
from telegram import Chat, Message, Update, User, MessageEntity


def get_update_from_sports_channel(sports_channel_id=None):
    if sports_channel_id is None:
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

def get_command_update_from_private_chat():
    return Update(
        0,
        Message(
            0,
            datetime.datetime.utcnow(),
            Chat(0, "private"),
            from_user=User(0, "Testuser", False),
            forward_from=User(0, "HAL9000", False),
            entities=[MessageEntity(MessageEntity.BOT_COMMAND, 0 , 0)]
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


def test_get_normal_messages_filter():
    update = get_update_from_sports_channel()
    normal_message_filter = filters.get_normal_messages_filter()
    update.message.text = "hi"
    assert normal_message_filter(update) == True
    # apparently commands are recognized by the entities field of the message,
    #   not by the text
    update = get_command_update_from_private_chat()
    assert normal_message_filter(update) == False


@pytest.mark.parametrize(
    "message_text,expected",
    [("#1234 -999.00", True), ("1234 -999.00", False), ("   #21987 +15", True), ("/start", False)]
)
def test_get_cashout_filter(message_text, expected, monkeypatch): 
    fake_exchange_channel_id = 123
    monkeypatch.setitem(cfg.config.SPORTS_CHANNELS_ID, "exchange", fake_exchange_channel_id)
    # correct
    update = get_update_from_sports_channel(sports_channel_id=fake_exchange_channel_id)
    update.message.text = message_text
    cashout_filter = filters.get_cashout_filter()
    assert bool(cashout_filter(update)) == expected
    # wrong channels
    update = get_update_from_sports_channel(sports_channel_id=-1)
    update.message.text = message_text
    cashout_filter = filters.get_cashout_filter()
    assert bool(cashout_filter(update)) == False


@pytest.mark.parametrize(
    "message_text,expected",
    [("normal message", True), ("sport strategia \n giocata error", True)]
)
def test_get_sport_channel_normal_message_filter(message_text, expected, monkeypatch):
    fake_exchange_channel_id = 123
    monkeypatch.setitem(cfg.config.SPORTS_CHANNELS_ID, "exchange", fake_exchange_channel_id)
    update = get_update_from_sports_channel(sports_channel_id=fake_exchange_channel_id)
    update.message.text = message_text
    normal_message_filter = filters.get_sport_channel_normal_message_filter()
    assert bool(normal_message_filter(update)) == expected
    # wrong channel
    update = get_update_from_sports_channel(sports_channel_id=-1)
    update.message.text = message_text
    normal_message_filter = filters.get_sport_channel_normal_message_filter()
    assert bool(normal_message_filter(update)) == False

