import random
from typing import Dict, Tuple

import pytest
from lot_bot.models import giocate as giocata_model


def test_get_outcome_percentage():
    # win
    outcome, stake, quota = "win", random.randint(100, 10000), random.randint(100, 10000)
    outcome_perc = giocata_model.get_outcome_percentage(outcome, stake, quota)
    assert outcome_perc == ((quota - 100) * stake) / 10000
    # loss
    outcome, stake, quota = "loss", random.randint(100, 10000), random.randint(100, 10000)
    outcome_perc = giocata_model.get_outcome_percentage(outcome, stake, quota)
    assert outcome_perc == -stake / 100
    # ?
    outcome, stake, quota = "?", random.randint(100, 10000), random.randint(100, 10000)
    outcome_perc = giocata_model.get_outcome_percentage(outcome, stake, quota)
    assert outcome_perc == 0.0
    # other cases
    outcome, stake, quota = "test", random.randint(100, 10000), random.randint(100, 10000)
    outcome_perc = giocata_model.get_outcome_percentage(outcome, stake, quota)
    assert outcome_perc == 0.0


@pytest.mark.parametrize(
    "giocata_text,sport,num,outcome",
    [
        ("🟢 Calcio#83 Vincente +5,25% 🟢", "calcio", "83", "win"), 
        ("🔴 Exchange #999 Perdente -5,00%🔴", "exchange", "999", "loss"),
        ("🟢 Tutto il Resto # 0 vinta +5,25% 🟢", "tuttoilresto", "0", "win"), 
        ("🔴 Tennis #123 Persa -5,00%🔴", "tennis", "123", "loss"),
    ]
)
def test_get_giocata_outcome_data(giocata_text, sport, num, outcome):
    sport_data, num_data, outcome_data = giocata_model.get_giocata_outcome_data(giocata_text)
    assert sport == sport_data
    assert num == num_data
    assert outcome == outcome_data


@pytest.mark.parametrize(
    "giocata_text",
    [
        ("🟢 Calcio Vincente +5,25% 🟢"), 
        ("Calcio#999 Perdente -5,00%🔴"),
        ("test"),
    ]
)
def test_error_get_giocata_outcome_data(giocata_text):
    with pytest.raises(Exception):
        _, _, _ = giocata_model.get_giocata_outcome_data(giocata_text)


def test_get_sport_from_correct_giocata(correct_giocata: Tuple[str, Dict]):
    giocata_text, giocata_data  = correct_giocata
    sport = giocata_model.get_sport_name_from_giocata(giocata_text)
    assert giocata_data["sport"] == sport


def test_get_sport_from_wrong_giocata(wrong_giocata: Tuple[str, Dict]):
    giocata_text, _ = wrong_giocata
    with pytest.raises(Exception):
        giocata_model.get_sport_name_from_giocata(giocata_text)


def test_get_strategy_from_correct_giocata(correct_giocata: Tuple[str, Dict]):
    giocata_text, giocata_data = correct_giocata
    strategy = giocata_model.get_strategy_name_from_giocata(giocata_text, giocata_data["sport"])
    assert strategy == giocata_data["strategy"]


def test_get_strategy_from_wrong_giocata(wrong_giocata: Tuple[str, Dict]):
    giocata_text, _ = wrong_giocata
    with pytest.raises(Exception):
        giocata_model.get_strategy_name_from_giocata(giocata_text, "")

def test_get_giocata_num_from_giocata(correct_giocata: Tuple[str, Dict]):
    correct_giocata_text, giocata_data = correct_giocata
    giocata_num = giocata_model.get_giocata_num_from_giocata(correct_giocata_text)
    assert giocata_data["giocata_num"] == giocata_num


def test_get_quota_from_giocata(correct_giocata: Tuple[str, Dict]):
    correct_giocata_text, giocata_data = correct_giocata
    quota = giocata_model.get_quota_from_giocata(correct_giocata_text)
    assert  quota == int(float(giocata_data["quota"])*100)


def test_get_stake_from_giocata(correct_giocata: Tuple[str, Dict]):
    correct_giocata_text, giocata_data = correct_giocata
    stake = giocata_model.get_stake_from_giocata(correct_giocata_text)
    assert stake == int(float(giocata_data["stake"]) * 100)


def test_get_quota_from_giocata(correct_giocata: Tuple[str, Dict], correct_giocata_multipla: Tuple[str, Dict]):
    correct_giocata_text, giocata_data = correct_giocata
    single_quota = giocata_model.get_quota_from_giocata(correct_giocata_text)
    assert single_quota == int(float(giocata_data["quota"])*100)
    multiple_giocata_text, multiple_giocata_data = correct_giocata_multipla
    multiple_quota = giocata_model.get_quota_from_giocata(multiple_giocata_text)
    assert multiple_quota == int(float(multiple_giocata_data["quota"])*100)


def test_parse_giocata(correct_giocata: Tuple[str, Dict]):
    correct_giocata_text, giocata_data = correct_giocata
    parsed_giocata = giocata_model.parse_giocata(correct_giocata_text)
    assert parsed_giocata["sport"] == giocata_data["sport"]
    assert parsed_giocata["strategy"] == giocata_data["strategy"]
    assert parsed_giocata["giocata_num"] == giocata_data["giocata_num"]
    assert parsed_giocata["base_quota"] == int(float(giocata_data["quota"])*100)
    assert parsed_giocata["base_stake"] == int(float(giocata_data["stake"])*100)
    assert parsed_giocata["raw_text"] == correct_giocata_text
