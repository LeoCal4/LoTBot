import pytest
from lot_bot import utils


@pytest.mark.parametrize(
    "percentage_text,expected",
    [("-999.00", "🔴"), ("+999,00", "🟢"), ("0", "⚪️"), ("/start", "")]
)
def test_get_emoji_for_cashout_percentage(percentage_text: str, expected: str):
    emoji = utils.get_emoji_for_cashout_percentage(percentage_text)
    assert emoji == expected
