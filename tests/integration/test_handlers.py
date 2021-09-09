from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from lot_bot import config as cfg

BOT_TEST_TIMEOUT = 15

class TestHandlers:

    @mark.asyncio
    async def test_help(self, client: TelegramClient):
        # Create a conversation
        async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
            # Send a command
            await conv.send_message("/test")
            # Get response
            resp: Message = await conv.get_response()
            # Make assertions
            assert "wow" in resp.raw_text


    @mark.asyncio
    async def test_start(self, client: TelegramClient):
        async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
            await conv.send_message("/start")
            first_resp: Message = await conv.get_response()
            assert "Bentornato" in first_resp.raw_text
            # TODO finish
            # second_resp: Message = await conv.get_response()
            # assert "lista dei canali" in second_resp.raw_text
