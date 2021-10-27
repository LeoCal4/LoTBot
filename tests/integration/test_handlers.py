import datetime
from typing import Dict, Tuple

import pytest
from lot_bot import config as cfg
from lot_bot import utils
from lot_bot.dao import sport_subscriptions_manager, user_manager
from telethon import TelegramClient
from telethon.tl.custom.message import Message
from lot_bot.models import sports as spr, strategies as strat

BOT_TEST_TIMEOUT = 15
TEST_CHANNEL_NAME = "lot_test_channel1"


# =============================== HELPER FUNCTIONS ===============================

def user_exists_and_is_valid(user_id: int) -> bool:
    ret_user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["_id", "lot_subscription_expiration"])
    if not ret_user_data:
        assert False, f"User does not exist: {ret_user_data=}"
    validity = user_manager.check_user_validity(datetime.datetime.now(), ret_user_data)
    if not validity:
        assert False, f"User not valid: {validity=}"
    return True


def sport_subscription_exists_and_is_valid(user_id: int, sport: str, strategy: str) -> bool:
    abb_result = sport_subscriptions_manager.retrieve_sport_subscriptions_from_user_id(user_id)
    if len(abb_result) == 0:
        assert False, f"Abbonamento not created for id {user_id}"
    found = False
    for result in abb_result:
        if result["sport"] == sport and strategy in result["strategies"]:
            found = True
    if not found:
        assert False, f"Wrong sport_subscriptions for id {user_id}: {abb_result}"
    return True


def delete_user_and_sport_subscriptions(user_id: int):
    user_manager.delete_user(user_id)
    sport_subscriptions_manager.delete_sport_subscriptions_for_user_id(user_id)

@pytest.fixture
def clean_sport_subscriptions_before_test():
    sport_subscriptions_manager.delete_all_sport_subscriptions()


# =================================================================================

class TestHandlers:

    @pytest.mark.asyncio
    async def test_start(self, client: TelegramClient):
        async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
            print(await conv.send_message("/start"))
            first_resp: Message = await conv.get_response()
            assert "Bentornato" in first_resp.raw_text
            second_resp: Message = await conv.get_response()
            assert "lista dei canali" in second_resp.raw_text
        client_me = await client.get_me()
        assert user_exists_and_is_valid(client_me.id)
        delete_user_and_sport_subscriptions(client_me.id)


    @pytest.mark.asyncio
    async def test_giocata_handler(self, 
    channel_admin_client: TelegramClient, 
    client: TelegramClient, 
    correct_giocata: Tuple[str, Dict]): #tuple[str, Dict]):
        # ! generate correct_giocata
        giocata_text, giocata_data = correct_giocata
        # ! use client to subscribe to sport-strategy, this also sets it to active
        async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
            await conv.send_message("/start")
            await conv.get_response()
            await conv.get_response()
        client_me = await client.get_me()
        assert user_exists_and_is_valid(client_me.id)
        sport_subscriptions_data = {
            "user_id": client_me.id,
            "sport": giocata_data["sport"],
            "strategy": giocata_data["strategy"],
        }
        sport_subscriptions_manager.create_sport_subscription(sport_subscriptions_data)
        assert sport_subscription_exists_and_is_valid(client_me.id, giocata_data["sport"], giocata_data["strategy"])
        # ! send giocata on channel using admin_client
        await channel_admin_client.send_message(TEST_CHANNEL_NAME, giocata_text)
        # ! check if the bot sends the message to the client
        dialogs = await client.get_dialogs()
        bot_chat = await client.get_messages(dialogs[0])
        # ! assert
        assert bot_chat[0].message == giocata_text + "\n\nHai effettuato la giocata?"
        # ! reset client
        delete_user_and_sport_subscriptions(client_me.id)


    @pytest.mark.asyncio
    async def test_exchange_cashout_handler(self, 
        client: TelegramClient, 
        channel_admin_client: TelegramClient, 
        monkeypatch, 
        clean_sport_subscriptions_before_test
        ):
        # ! send start to have the bot message as the latest one
        async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
            await conv.send_message("/start")
            await conv.get_response()
            await conv.get_response()
        client_me = await client.get_me()
        assert user_exists_and_is_valid(client_me.id)
        # ! subscribe client to exchange - MaxExchange (already done with /start)
        exchange_name = spr.sports_container.EXCHANGE.name
        maxexchange_name = strat.strategies_container.MAXEXCHANGE.name
        # sport_subscriptions_exchange_data = {
        #     "user_id": client_me.id,
        #     "sport": exchange_name,
        #     "strategy": maxexchange_name,
        # }
        # sport_subscriptions_manager.create_sport_subscription(sport_subscriptions_exchange_data)
        assert sport_subscription_exists_and_is_valid(client_me.id, exchange_name, maxexchange_name)
        # ! generate cashout message
        cashout_message = "#123 +100.00"
        # ! send cashout message from exchange channel (patch)
        monkeypatch.setitem(cfg.config.SPORTS_CHANNELS_ID, exchange_name, cfg.config.SPORTS_CHANNELS_ID[TEST_CHANNEL_NAME])
        await channel_admin_client.send_message(TEST_CHANNEL_NAME, cashout_message)
        # ! check if client received the message 
        # ! WARNING: if there other users with the same sport_subscriptions, this fails because the message sending loop needs to
        #   send the giocate to all the user before this client, since it is the last one in the list
        dialogs = await client.get_dialogs()
        bot_chat = await client.get_messages(dialogs[0])
        # ! final check
        assert bot_chat[0].message == utils.create_cashout_message(cashout_message)
        # ! reset client
        delete_user_and_sport_subscriptions(client_me.id)
