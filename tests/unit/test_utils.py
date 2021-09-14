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
    assert utils.get_strategy_from_giocata(giocata) == ""


@pytest.mark.parametrize(
    "percentage_text,expected",
    [("-999.00", "🔴"), ("+999,00", "🟢"), ("0", "🟢"), ("/start", "")]
)
def test_get_emoji_for_cashout_percentage(percentage_text, expected):
    emoji = utils.get_emoji_for_cashout_percentage(percentage_text)
    assert emoji == expected

