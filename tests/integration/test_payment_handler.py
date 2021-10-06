import datetime

import pytest
from lot_bot import config as cfg
from lot_bot import constants as cst
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import sport_subscriptions_manager, user_manager
from telethon import TelegramClient, functions
from telethon.tl.custom.message import Message
from lot_bot.models import sports as spr, strategies as strat

BOT_TEST_TIMEOUT = 15


# @pytest.mark.asyncio
# async def test_successful_payment(client: TelegramClient):
#     PAYMENTS_MAIN_MENU_BUTTON_INDEX = 2
#     TO_PAYMENTS_BUTTON_INDEX = 0
#     INVOICE_BUTTON_INDEX = 0
#     async with client.conversation(cfg.config.BOT_TEST_USERNAME, timeout=BOT_TEST_TIMEOUT) as conv:
#         await conv.send_message("/start")
#         await conv.get_response()
#         await conv.get_response()
#         await conv.send_message(cst.HOMEPAGE_BUTTON_TEXT)
#         response: Message = await conv.get_response()
#         await response.click(PAYMENTS_MAIN_MENU_BUTTON_INDEX)
#         response: Message = await conv.get_edit()
#         await response.click(TO_PAYMENTS_BUTTON_INDEX)
#         response: Message = await conv.get_response()
#         lgr.logger.error(f"After click to payments: {str(response)}")
#         await response.click(INVOICE_BUTTON_INDEX)
#         response: Message = await conv.get_response()
#         lgr.logger.error(f"After click on invoice: {str(response)}")
#         assert False
        # client(functions.payments.SendPaymentFormRequest(
        #     form_id=0,
        #     peer=0,
        #     msg_id=0,
        # ))
