import datetime

from lot_bot import config as cfg
from lot_bot import logger as lgr
from lot_bot.dao import abbonamenti_manager, user_manager
from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message

BOT_TEST_TIMEOUT = 15

class TestHandlers:

    # ! IMPORTANT: this test has to be the first for the client
    @mark.asyncio
    async def test_first_message(self, client: TelegramClient):
        async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
            await conv.send_message("hi")
            first_resp: Message = await conv.get_response()
            # TODO use messages in constants
            assert "Benvenuto/a" in first_resp.raw_text
            second_resp: Message = await conv.get_response()
            assert "contrastare la ludopatia" in second_resp.raw_text
            client_me = await client.get_me()
            assert not user_manager.retrieve_user(client_me.id) is None
            assert len(list(abbonamenti_manager.retrieve_abbonamenti_from_user_id(client_me.id))) == 2


    @mark.asyncio
    async def test_start(self, client: TelegramClient):
        async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
            await conv.send_message("/start")
            first_resp: Message = await conv.get_response()
            assert "Bentornato" in first_resp.raw_text
            # TODO finish
            second_resp: Message = await conv.get_response()
            assert "lista dei canali" in second_resp.raw_text



    @mark.asyncio
    async def test_giocata_handler(self, channel_admin_client: TelegramClient, client: TelegramClient, correct_giocata: tuple):
        # ! generate correct_giocata
        giocata, sport, strategia = correct_giocata
        # ! use client to subscribe to sport-strategy
        async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
            await conv.send_message("/start")
            first_resp: Message = await conv.get_response()
        client_me = await client.get_me()
        user_data = {
            "_id": client_me.id,
            "validoFino": (datetime.datetime.now() + datetime.timedelta(days=1)).timestamp(),
            "attivo": 1
        }
        user_manager.update_user(user_data["_id"], user_data)
        abbonamenti_data = {
            "telegramID": client_me.id,
            "sport": sport,
            "strategia": strategia,
        }
        abb_result = abbonamenti_manager.create_abbonamenti(abbonamenti_data)
        if not abb_result:
            lgr.logger.error("abbonamento not created")
            assert False
        # ! send giocata on channel using admin_client
        channel_id = "lot_test_channel1"
        result = await channel_admin_client.send_message(channel_id, giocata)
        # ! check if the bot sends the message to the client
        dialogs = await client.get_dialogs()
        first = dialogs[0]
        chat = await client.get_messages(first)
        # ! reset client abbonamenti
        abbonamenti_manager.delete_abbonamenti_for_user_id(client_me.id)
        assert chat[0].message == giocata
