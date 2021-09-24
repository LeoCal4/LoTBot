import re
from typing import Dict

import pytest
from lot_bot import constants as cst
from lot_bot import logger as lgr
from lot_bot.dao import user_manager
from lot_bot import utils


def test_get_sport_from_correct_giocata(correct_giocata):
    giocata, sport, _  = correct_giocata
    sport = utils.get_sport_from_giocata(giocata)
    assert sport == sport


def test_get_sport_from_wrong_giocata(wrong_giocata):
    giocata, _, _ = wrong_giocata
    sport = utils.get_sport_from_giocata(giocata)
    assert sport is None


def test_get_strategy_from_correct_giocata(correct_giocata):
    giocata, _, random_strategy = correct_giocata
    strategy = utils.get_strategy_from_giocata(giocata)
    assert strategy == random_strategy


def test_get_strategy_from_wrong_giocata(wrong_giocata):
    giocata, _, _ = wrong_giocata
    assert utils.get_strategy_from_giocata(giocata) == ""


@pytest.mark.parametrize(
    "percentage_text,expected",
    [("-999.00", "🔴"), ("+999,00", "🟢"), ("0", "🟢"), ("/start", "")]
)
def test_get_emoji_for_cashout_percentage(percentage_text, expected):
    emoji = utils.get_emoji_for_cashout_percentage(percentage_text)
    assert emoji == expected


def test_generate_referral_code():
    referral_code = utils.generate_referral_code()
    assert len(referral_code) == len("lot-ref-") + cst.REFERRAL_CODE_LEN
    assert not re.match(r"lot-ref-(\w|-)+$", referral_code) is None


def test_check_referral_code_availability(new_user):
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
    
