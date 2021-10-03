import datetime
from typing import Dict

import pytest
from lot_bot import config as cfg
from lot_bot import utils
from lot_bot.dao import abbonamenti_manager, user_manager
from telethon import TelegramClient
from telethon.tl.custom.message import Message
from lot_bot.models import sports as spr, strategies as strat

BOT_TEST_TIMEOUT = 15
TEST_CHANNEL_NAME = "lot_test_channel1"


# =============================== HELPER FUNCTIONS ===============================

def user_exists_and_is_valid(user_id: int) -> bool:
    ret_user_data = user_manager.retrieve_user_fields_by_user_id(user_id, ["_id"])
    if not ret_user_data:
        assert False, f"User does not exist: {ret_user_data=}"
    validity = user_manager.check_user_validity(datetime.datetime.now(), ret_user_data)
    if not validity:
        assert False, f"User not valid: {validity=}"
    return True


def abbonamento_exists_and_is_valid(user_id: int, sport: str, strategy: str) -> bool:
    abb_result = abbonamenti_manager.retrieve_abbonamenti({"telegramID": user_id})
    if not abb_result or len(abb_result) == 0:
        assert False, f"Abbonamento not created for id {user_id}"
    found = False
    for result in abb_result:
        if result["sport"] == sport and result["strategia"] == strategy:
            found = True
    if not found:
        assert False, f"Wrong abbonamenti for id {user_id}: {abb_result}"
    return True


def delete_user_and_abbonamenti(user_id: int):
    user_manager.delete_user(user_id)
    abbonamenti_manager.delete_abbonamenti_for_user_id(user_id)

@pytest.fixture
def clean_abbonamenti_before_test():
    abbonamenti_manager.delete_all_abbonamenti()


# =================================================================================

class TestHandlers:
    # @pytest.mark.asyncio
    # async def test_first_message(self, client: TelegramClient):
    #     async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
    #         await conv.send_message("hi")
    #         first_resp: Message = await conv.get_response()
    #         # TODO use messages in constants
    #         assert "Benvenuto/a" in first_resp.raw_text
    #         second_resp: Message = await conv.get_response()
    #         assert "contrastare la ludopatia" in second_resp.raw_text
    #     client_me = await client.get_me()
    #     assert user_exists_and_is_valid(client_me.id)
    #     # the start messages sets calcio and exchange
    #     assert len(list(abbonamenti_manager.retrieve_abbonamenti({"telegramID": client_me.id}))) == 2
    #     delete_user_and_abbonamenti(client_me.id)


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
        delete_user_and_abbonamenti(client_me.id)


    @pytest.mark.asyncio
    async def test_giocata_handler(self, 
    channel_admin_client: TelegramClient, 
    client: TelegramClient, 
    correct_giocata: tuple[str, Dict]):
        # ! generate correct_giocata
        giocata_text, giocata_data = correct_giocata
        # ! use client to subscribe to sport-strategy, this also sets it to active
        async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
            await conv.send_message("/start")
            await conv.get_response()
            await conv.get_response()
        client_me = await client.get_me()
        assert user_exists_and_is_valid(client_me.id)
        abbonamenti_data = {
            "telegramID": client_me.id,
            "sport": giocata_data["sport"],
            "strategia": giocata_data["strategy"],
        }
        abbonamenti_manager.create_abbonamento(abbonamenti_data)
        assert abbonamento_exists_and_is_valid(client_me.id, giocata_data["sport"], giocata_data["strategy"])
        # ! send giocata on channel using admin_client
        await channel_admin_client.send_message(TEST_CHANNEL_NAME, giocata_text)
        # ! check if the bot sends the message to the client
        dialogs = await client.get_dialogs()
        bot_chat = await client.get_messages(dialogs[0])
        # ! assert
        assert bot_chat[0].message == giocata_text + "\n\nHai effettuato la giocata?"
        # ! reset client
        delete_user_and_abbonamenti(client_me.id)


    @pytest.mark.asyncio
    async def test_exchange_cashout_handler(self, 
        client: TelegramClient, 
        channel_admin_client: TelegramClient, 
        monkeypatch, 
        clean_abbonamenti_before_test
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
        # abbonamenti_exchange_data = {
        #     "telegramID": client_me.id,
        #     "sport": exchange_name,
        #     "strategia": maxexchange_name,
        # }
        # abbonamenti_manager.create_abbonamento(abbonamenti_exchange_data)
        assert abbonamento_exists_and_is_valid(client_me.id, exchange_name, maxexchange_name)
        # ! generate cashout message
        cashout_message = "#123 +100.00"
        # ! send cashout message from exchange channel (patch)
        monkeypatch.setitem(cfg.config.SPORTS_CHANNELS_ID, exchange_name, cfg.config.SPORTS_CHANNELS_ID[TEST_CHANNEL_NAME])
        await channel_admin_client.send_message(TEST_CHANNEL_NAME, cashout_message)
        # ! check if client received the message 
        # ! WARNING: if there other users with the same abbonamenti, this fails because the message sending loop needs to
        #   send the giocate to all the user before this client, since it is the last one in the list
        dialogs = await client.get_dialogs()
        bot_chat = await client.get_messages(dialogs[0])
        # ! final check
        assert bot_chat[0].message == utils.create_cashout_message(cashout_message)
        # ! reset client
        delete_user_and_abbonamenti(client_me.id)
