import pytest
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
    with pytest.raises(Exception):
        utils.get_strategy_from_giocata(giocata)
