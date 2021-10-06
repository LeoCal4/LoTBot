import random

import pytest
from lot_bot.models import giocate as giocata_model


def test_get_outcome_percentage():
    # win
    outcome, stake, quota = "win", random.randint(0, 100), random.randint(0, 9999)
    outcome_perc = giocata_model.get_outcome_percentage(outcome, stake, quota)
    assert outcome_perc == (quota - 100) * stake / 100
    # loss
    outcome, stake, quota = "loss", random.randint(0, 100), random.randint(0, 9999)
    outcome_perc = giocata_model.get_outcome_percentage(outcome, stake, quota)
    assert outcome_perc == float(-stake)
    # ?
    outcome, stake, quota = "?", random.randint(0, 100), random.randint(0, 9999)
    outcome_perc = giocata_model.get_outcome_percentage(outcome, stake, quota)
    assert outcome_perc == 0.0
    # other cases
    outcome, stake, quota = "test", random.randint(0, 100), random.randint(0, 9999)
    outcome_perc = giocata_model.get_outcome_percentage(outcome, stake, quota)
    assert outcome_perc == 0.0


@pytest.mark.parametrize(
    "giocata_text,sport,num,outcome",
    [
        ("🟢 Calcio#83 Vincente +5,25% 🟢", "calcio", "83", "win"), 
        ("🔴 Basket #999 Perdente -5,00%🔴", "basket", "999", "loss"),
        ("🟢 Ippica # 0 vinta +5,25% 🟢", "ippica", "0", "win"), 
        ("🔴 Pallavolo #123 Persa -5,00%🔴", "pallavolo", "123", "loss"),
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
