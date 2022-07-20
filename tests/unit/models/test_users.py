import datetime
import random
import re
from typing import Dict, Tuple

import pytest
from lot_bot import constants as cst
from lot_bot import logger as lgr
from lot_bot.dao import user_manager
from lot_bot.models import users, giocate



def test_generate_referral_code():
    referral_code = users.generate_referral_code()
    assert len(referral_code) == cst.REFERRAL_CODE_LEN + len("-lot")
    assert not re.match(r"(\w|-)+-lot$", referral_code) is None


def test_check_referral_code_availability(new_user: Dict):
    assert not users.check_referral_code_availability(new_user["referral_code"])
    assert users.check_referral_code_availability("random code")


def test_create_valid_referral_code(monkeypatch, new_user: Dict):
    first_code = "lot-abc123" 
    def mock_ref_code():
        nonlocal first_code
        return first_code
    monkeypatch.setattr(users, "generate_referral_code", mock_ref_code)
    assert users.create_valid_referral_code() == first_code
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
        nonlocal yielder
        next_item = next(yielder)
        return next_item
    monkeypatch.setattr(users, "generate_referral_code", mock_ref_code2)
    assert users.create_valid_referral_code() == second_code


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
    extended_timestamp = users.extend_expiration_date(exp_date_timestamp)
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
    extended_date_timestamp = users.extend_expiration_date(exp_date_timestamp)
    extended_date_string = datetime.datetime.utcfromtimestamp(extended_date_timestamp).strftime("%d/%m/%Y")
    extended_now_timestamp = users.extend_expiration_date(datetime.datetime.utcnow().timestamp())
    extended_now_string = datetime.datetime.utcfromtimestamp(extended_now_timestamp).strftime("%d/%m/%Y")
    assert extended_date_string == extended_now_string


@pytest.mark.parametrize(
    "outcome",
    ["win", "loss", "void", "neutral"]
)
def test_calculate_new_budget_after_giocata_base_cases(outcome: str):
    base_giocata = giocate.create_base_giocata()
    base_budget = random.randint(10, 1000)
    random_stake = random.randint(100, 10000) # 1 - 100
    random_quota = random.randint(200, 5000) # 2 - 50
    base_giocata["base_stake"] = random_stake
    base_giocata["base_quota"] = random_quota
    base_giocata["outcome"] = outcome
    new_budget = users.calculate_new_budget_after_giocata(base_budget, base_giocata)
    correct_budget = base_budget + base_budget * round(giocate.get_outcome_percentage(base_giocata["outcome"], random_stake, random_quota) / 100, 2)
    assert new_budget == correct_budget


@pytest.mark.parametrize(
    "outcome",
    ["win", "loss", "void", "neutral"]
)
def test_calculate_new_budget_after_giocata_personalized_stake(outcome: str):
    base_giocata = giocate.create_base_giocata()
    base_budget = random.randint(10, 1000)
    random_stake = random.randint(100, 10000) # 1 - 100
    random_quota = random.randint(200, 5000) # 2 - 50
    base_giocata["base_stake"] = random_stake
    base_giocata["base_quota"] = random_quota
    base_giocata["outcome"] = outcome
    random_personalized_stake = random.randint(100, 10000) # 1 - 100
    new_budget = users.calculate_new_budget_after_giocata(base_budget, base_giocata, personalized_stake=random_personalized_stake)
    correct_budget = base_budget + base_budget * round(giocate.get_outcome_percentage(base_giocata["outcome"], random_personalized_stake, random_quota)  / 100, 2)
    assert new_budget == correct_budget


@pytest.mark.parametrize(
    "outcome",
    ["win", "loss", "void"]
)
def test_calculate_new_budget_after_giocata_cashout(outcome: str):
    base_giocata = giocate.create_base_giocata()
    base_budget = random.randint(10, 1000)
    random_stake = random.randint(100, 10000) # 1 - 100
    random_quota = random.randint(200, 5000) # 2 - 50
    base_giocata["base_stake"] = random_stake
    base_giocata["base_quota"] = random_quota
    base_giocata["outcome"] = outcome
    base_giocata["cashout"] = random.randint(100, 10000) # 1 - 100
    if outcome == "void":
        base_giocata["cashout"] = 0
    new_budget = users.calculate_new_budget_after_giocata(base_budget, base_giocata)
    correct_budget = base_budget + base_budget * round((base_giocata["cashout"] / 100) / 100, 2)
    assert new_budget == correct_budget


def test_update_single_user_budget_with_giocata():
    pass

