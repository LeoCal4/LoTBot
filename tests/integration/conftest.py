import asyncio
import sys
from pathlib import Path
from random import randrange

import pytest
from lot_bot import config as cfg
from lot_bot import logger as lgr
from lot_bot.database import create_db
from telethon.client.telegramclient import TelegramClient
from xprocess import ProcessStarter

"""The fixtures found in this file are automatically added by pytest 
    to all the tests files in this directory
"""

# this is here because of this:
# https://github.com/pytest-dev/pytest-asyncio/issues/68
# the event_loop has a base scope of "function", so if it
# is used on a fixture with a bigger scope, it needs to be 
# redefined with said bigger scope
@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def run_integration_tests_db():
    create_db()


@pytest.fixture(scope="session", autouse=True)
def run_bot_for_tests(xprocess):
    """Runs the main.py file in another process, in order to have
        the bot running for the tests. The bot is automatically shut
        down after the tests are finished.

    Args:
        xprocess

    Raises:
        FileNotFoundError: raised when the main.py file can't be found
    """
    class BotStarter(ProcessStarter):
        def get_main_path():
            # lot_bot/tests/integration/conftest.py -> lot_bot/main.py
            path = Path(__file__).parent.absolute().parent.absolute().parent.absolute().joinpath("main.py")
            if not path.exists():
                raise FileNotFoundError(f"main.py path not found: {path}")
            return path
        print("Activating bot for tests")
        # the pattern that will be waited for to be printed
        #   in the console
        # ! WARNING: the logger MUST write on the console during 
        # !  integration testing and not on a log file,
        # !   otherwise the pattern won't be found
        pattern = "Scheduler started"
        # maximum time to wait for the patter to appear
        #   before timing out
        timeout = 120
        # path to python executable
        python_exec_path = sys.executable
        # path to the main bot file
        main_file_path = get_main_path()
        args = [python_exec_path, main_file_path]
        # makes the process receive interrupts from the console
        terminate_on_interrupt = True
    
    print(xprocess.ensure("run_bot_for_tests", BotStarter))
    # print("Bot activated")
    yield

    xprocess.getinfo("run_bot_for_tests").terminate()


def generate_random_fake_number(dc_id: int) -> str:
    """Generates a random fake number, as specified in the following links:
       - https://docs.telethon.dev/en/latest/developing/test-servers.html
       - https://core.telegram.org/api/auth#test-phone-numbers
       - https://docs.pyrogram.org/topics/test-servers
    Valid phone numbers are 99966XYYYY, where X is the dc_id (1 to 3) and
        YYYY is any number you want

    Args:
        dc_id (int): the id of the chosen data center, between 1 and 3

    Returns:
        str: the random fake phone number generated
    """
    random_phone_suffix = str(randrange(1000, stop=9999))
    return f"99966{str(dc_id)}{random_phone_suffix}"


@pytest.fixture(scope="session")
async def client() -> TelegramClient:
    """Creates a real Telegram Client, connected to Telegram's test servers,
        using a fake phone number. This is used by all of the integration tests 
        to simulate real users using the bot.
    Everything that is found before the yield is run at the beginning
        of the session, the rest is run at its end
    
    Yields:
        TelegramClient: the Telegram client connected to the test servers
    """
    client = TelegramClient(None, cfg.config.API_ID, cfg.config.API_HASH, sequential_updates=True)
    DC_ID = 3
    TELEGRAM_TEST_SERVER_IP = "149.154.167.40"
    TELEGRAM_TEST_SERVER_PORT = 443
    client.session.set_dc(DC_ID, TELEGRAM_TEST_SERVER_IP, TELEGRAM_TEST_SERVER_PORT)
    phone_number = generate_random_fake_number(DC_ID)
    lgr.logger.info(f"Generated fake number {phone_number}")
    confirmation_code = str(DC_ID) * 5
    await client.start(phone=phone_number, code_callback=lambda: confirmation_code)

    yield client

    await client.disconnect()
    await client.disconnected


@pytest.fixture(scope="session")
async def channel_admin_client() -> TelegramClient:
    """Same as client, but instead of creating a random user, 
    it logs in with an existing one which is the admin of the 
    test channel.
    ======================== ! IMPORTANT ! ===========================
    Integration tests involving channels won't work if you have not 
    performed the following steps yet.
    To create an admin for the channel, choose a phone number among the
    available ones and run the following lines of code to have that
    account join the channel:
    
        `from telethon.tl.functions.channels import JoinChannelRequest`
        `await channel_admin_client(JoinChannelRequest(channel))`

    where `channel` is the id of the channel.
    Once the client is part of the channel, you have to manually make it an
    admin.    
    
    Yields:
        TelegramClient: the Telegram client connected to the test servers
    """
    client = TelegramClient(None, cfg.config.API_ID, cfg.config.API_HASH, sequential_updates=True)
    DC_ID = 3
    TELEGRAM_TEST_SERVER_IP = "149.154.167.40"
    TELEGRAM_TEST_SERVER_PORT = 443
    CHANNEL_ADMIN_PHONE_NUMBER = f"99966{DC_ID}0001"
    client.session.set_dc(DC_ID, TELEGRAM_TEST_SERVER_IP, TELEGRAM_TEST_SERVER_PORT)
    confirmation_code = str(DC_ID) * 5
    await client.start(first_name="Channel Admin", phone=CHANNEL_ADMIN_PHONE_NUMBER, 
                        code_callback=lambda: confirmation_code, password="")

    yield client

    await client.disconnect()
    await client.disconnected
