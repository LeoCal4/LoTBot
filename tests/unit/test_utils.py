import datetime
import re
from typing import Dict, Tuple

import pytest
from lot_bot import constants as cst
from lot_bot import logger as lgr
from lot_bot.dao import user_manager
from lot_bot import utils


def test_get_sport_from_correct_giocata(correct_giocata: Tuple[str, Dict]):
    giocata_text, giocata_data  = correct_giocata
    sport = utils.get_sport_name_from_giocata(giocata_text)
    assert giocata_data["sport"] == sport


def test_get_sport_from_wrong_giocata(wrong_giocata: Tuple[str, Dict]):
    giocata_text, _ = wrong_giocata
    with pytest.raises(Exception):
        utils.get_sport_name_from_giocata(giocata_text)


def test_get_strategy_from_correct_giocata(correct_giocata: Tuple[str, Dict]):
    giocata_text, giocata_data = correct_giocata
    strategy = utils.get_strategy_name_from_giocata(giocata_text, giocata_data["sport"])
    assert strategy == giocata_data["strategy"]


def test_get_strategy_from_wrong_giocata(wrong_giocata: Tuple[str, Dict]):
    giocata_text, _ = wrong_giocata
    with pytest.raises(Exception):
        utils.get_strategy_name_from_giocata(giocata_text, "")


@pytest.mark.parametrize(
    "percentage_text,expected",
    [("-999.00", "🔴"), ("+999,00", "🟢"), ("0", "⚪️"), ("/start", "")]
)
def test_get_emoji_for_cashout_percentage(percentage_text: str, expected: str):
    emoji = utils.get_emoji_for_cashout_percentage(percentage_text)
    assert emoji == expected


def test_generate_referral_code():
    referral_code = utils.generate_referral_code()
    assert len(referral_code) == cst.REFERRAL_CODE_LEN + len("-lot")
    assert not re.match(r"(\w|-)+-lot$", referral_code) is None


def test_check_referral_code_availability(new_user: Dict):
    assert not utils.check_referral_code_availability(new_user["referral_code"])
    assert utils.check_referral_code_availability("random code")


def test_create_valid_referral_code(monkeypatch, new_user: Dict):
    first_code = "lot-abc123" 
    def mock_ref_code():
        nonlocal first_code
        return first_code
    monkeypatch.setattr(utils, "generate_referral_code", mock_ref_code)
    assert utils.create_valid_referral_code() == first_code
    # check that it does not add an already present ref code
    user_manager.update_user(new_user["_id"], {"referral_code": first_code})
    second_code = "lot-def321"
    def code_yielder():
        nonlocal first_code
        nonlocal second_code
        yield first_code
        yield second_code
    yielder = code_yielder()
    def mock_ref_code2():
        next_item = next(yielder)
        lgr.logger.error(next_item)
        return next_item
    monkeypatch.setattr(utils, "generate_referral_code", mock_ref_code2)
    assert utils.create_valid_referral_code() == second_code


# * for some timezone reason it goes 1 hour back, the month is added correctly though 
@pytest.mark.parametrize(
    "exp_date_timestamp,expected",
    [
        (datetime.datetime(2050, 2, 28, 2, tzinfo=datetime.timezone.utc).timestamp(), datetime.datetime(2050, 3, 28, tzinfo=datetime.timezone.utc).timestamp()),
        # january to february to test a non-existing day in the next month
        (datetime.datetime(2051, 1, 30, 1, tzinfo=datetime.timezone.utc).timestamp(), datetime.datetime(2051, 2, 28, tzinfo=datetime.timezone.utc).timestamp()),
        # december to january test new year
        (datetime.datetime(2050, 12, 30, 1, tzinfo=datetime.timezone.utc).timestamp(), datetime.datetime(2051, 1, 30, tzinfo=datetime.timezone.utc).timestamp()),
    ]
)
def test_extend_expiration_date(exp_date_timestamp: float, expected: float):
    extended_timestamp = utils.extend_expiration_date(exp_date_timestamp)
    extended_string = datetime.datetime.utcfromtimestamp(extended_timestamp).strftime("%d/%m/%Y - %H:%M")
    expected_string = datetime.datetime.utcfromtimestamp(expected).strftime("%d/%m/%Y - %H:%M")
    assert extended_string == expected_string


@pytest.mark.parametrize(
    "exp_date_timestamp",
    [
        (datetime.datetime(2010, 2, 28, 1, tzinfo=datetime.timezone.utc).timestamp()),
        # january to february to test a non-existing day in the next month
        (datetime.datetime(2011, 1, 30, 1, tzinfo=datetime.timezone.utc).timestamp()),
        # december to january test new year
        (datetime.datetime(2010, 12, 30, 1, tzinfo=datetime.timezone.utc).timestamp()),
    ]
)
def test_extend_expiration_date_with_old_date(exp_date_timestamp: float):
    extended_date_timestamp = utils.extend_expiration_date(exp_date_timestamp)
    extended_date_string = datetime.datetime.utcfromtimestamp(extended_date_timestamp).strftime("%d/%m/%Y")
    extended_now_timestamp = utils.extend_expiration_date(datetime.datetime.utcnow().timestamp())
    extended_now_string = datetime.datetime.utcfromtimestamp(extended_now_timestamp).strftime("%d/%m/%Y")
    assert extended_date_string == extended_now_string


def test_get_giocata_num_from_giocata(correct_giocata: Tuple[str, Dict]):
    correct_giocata_text, giocata_data = correct_giocata
    giocata_num = utils.get_giocata_num_from_giocata(correct_giocata_text)
    assert giocata_data["giocata_num"] == giocata_num


def test_get_quota_from_giocata(correct_giocata: Tuple[str, Dict]):
    correct_giocata_text, giocata_data = correct_giocata
    quota = utils.get_quota_from_giocata(correct_giocata_text)
    assert  quota == int(float(giocata_data["quota"])*100)


def test_get_stake_from_giocata(correct_giocata: Tuple[str, Dict]):
    correct_giocata_text, giocata_data = correct_giocata
    stake = utils.get_stake_from_giocata(correct_giocata_text)
    assert stake == int(giocata_data["stake"])


def test_get_quota_from_giocata(correct_giocata: Tuple[str, Dict], correct_giocata_multipla: Tuple[str, Dict]):
    correct_giocata_text, giocata_data = correct_giocata
    single_quota = utils.get_quota_from_giocata(correct_giocata_text)
    assert single_quota == int(float(giocata_data["quota"])*100)
    multiple_giocata_text, multiple_giocata_data = correct_giocata_multipla
    multiple_quota = utils.get_quota_from_giocata(multiple_giocata_text)
    assert multiple_quota == int(float(multiple_giocata_data["quota"])*100)



def test_parse_giocata(correct_giocata: Tuple[str, Dict]):
    correct_giocata_text, giocata_data = correct_giocata
    parsed_giocata = utils.parse_giocata(correct_giocata_text)
    assert parsed_giocata["sport"] == giocata_data["sport"]
    assert parsed_giocata["strategy"] == giocata_data["strategy"]
    assert parsed_giocata["giocata_num"] == giocata_data["giocata_num"]
    assert parsed_giocata["base_quota"] == int(float(giocata_data["quota"])*100)
    assert parsed_giocata["base_stake"] == int(giocata_data["stake"])
    assert parsed_giocata["raw_text"] == correct_giocata_text
