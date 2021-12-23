import random
from typing import Dict, List

import pytest
from lot_bot.models import personal_stakes
from lot_bot.models import sports as spr
from lot_bot.models import strategies as strat
from lot_bot import utils
from lot_bot import custom_exceptions

SPORT_INDEX = 4
STRATEGIES_START_INDEX = SPORT_INDEX + 1

def create_random_personal_stake(sport_name: str = None, strategies_names: List[str] = None):
    random_stake_data = personal_stakes.create_base_personal_stake()
    random_stake_data["min_quota"] = str(random.uniform(0, 100))
    random_stake_data["max_quota"] = str(float(random_stake_data["min_quota"]) + random.uniform(0, 100))
    random_stake_data["stake"] = str(random.uniform(1, 100))
    if sport_name:
        random_stake_data["sport"] = sport_name
        random_sport = spr.sports_container.get_sport(sport_name)
    else:
        random_sport : spr.Sport =  random.choice(spr.sports_container.astuple())
        random_stake_data["sport"] = random_sport.name
    if strategies_names:
        random_stake_data["strategies"] = strategies_names
    else:
        # random sport may be None due to a wrong sport passed for testing
        if not random_sport:
            random_stake_data["strategies"] = []
        else:
            random_stake_data["strategies"] = list(set([random.choice(random_sport.strategies).name for _ in range(random.randint(1, 3))]))
    return random_stake_data


def get_fake_stake_command_args(random_stake_data: Dict = None) -> List:
    random_stake_data = create_random_personal_stake() if random_stake_data is None else random_stake_data
    fake_command_args = [
        "",
        random_stake_data["min_quota"],
        random_stake_data["max_quota"],
        random_stake_data["stake"],
        random_stake_data["sport"],
    ]
    fake_command_args.extend(random_stake_data["strategies"])
    return fake_command_args


def test_parse_personal_stake():
    # * correct parsing
    random_stake_data = create_random_personal_stake()
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)
    assert utils.parse_float_string_to_int(random_stake_data["min_quota"]) == parsed_stake["min_quota"]
    assert utils.parse_float_string_to_int(random_stake_data["max_quota"]) == parsed_stake["max_quota"]
    assert utils.parse_float_string_to_int(random_stake_data["stake"]) == parsed_stake["stake"]
    assert random_stake_data["sport"] == parsed_stake["sport"]
    assert random_stake_data["strategies"] == parsed_stake["strategies"]
    # * check 'all' sport and strategy set by default
    random_stake_data = create_random_personal_stake()
    fake_command_args = get_fake_stake_command_args(random_stake_data)[:SPORT_INDEX]
    parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)
    assert parsed_stake["sport"] == "all"
    assert parsed_stake["strategies"] == ["all"]
    # * check 'all' strategy set by default
    random_stake_data = create_random_personal_stake(sport_name="calcio")
    fake_command_args = get_fake_stake_command_args(random_stake_data)[:STRATEGIES_START_INDEX]
    parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)
    assert parsed_stake["sport"] == "calcio"
    assert parsed_stake["strategies"] == ["all"]


@pytest.mark.parametrize(
    "min_quota, max_quota, stake, no_error",
    [
        (str(random.uniform(0, 100)), str(random.uniform(101, 200)), str(random.uniform(0, 100)), True),
        # test number with , instead of .
        ("10,10", str(random.uniform(101, 200)), str(random.uniform(0, 100)), True),
        # test wrong inputs
        (str(random.uniform(0, 100)), "10-20", str(random.uniform(0, 100)), False),
        (str(random.uniform(0, 100)), str(random.uniform(101, 200)), "test", False),
    ]
)
def test_parse_personal_stake_numeric_parsing(min_quota, max_quota, stake, no_error):
    random_stake_data = create_random_personal_stake()
    random_stake_data["min_quota"] = min_quota
    random_stake_data["max_quota"] = max_quota
    random_stake_data["stake"] = stake
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    if no_error:
        parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)
        assert parsed_stake
    else:
        with pytest.raises(custom_exceptions.PersonalStakeParsingError):
            parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)


@pytest.mark.parametrize(
    "min_quota, max_quota, no_error",
    [
        (str(random.uniform(0, 100)), str(random.uniform(101, 200)),  True),
        (str(random.uniform(101, 200)), str(random.uniform(0, 1)),  False),
        (str(0), str(0),  False),
        (str(10), str(10),  False),
        (str(0.5), str(0.5),  False),
        ("1,2", "3,8",  True),
    ]
)
def test_parse_personal_stake_min_max_correctness(min_quota, max_quota, no_error):
    random_stake_data = create_random_personal_stake()
    random_stake_data["min_quota"] = min_quota
    random_stake_data["max_quota"] = max_quota
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    if no_error:
        parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)
        assert parsed_stake
    else:
        with pytest.raises(custom_exceptions.PersonalStakeParsingError):
            parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)


@pytest.mark.parametrize(
    "stake, no_error",
    [
        (str(random.uniform(1, 100)), True),
        ("1,2", True),
        ("100.0", True),
        ("1000000", False),
        ("-123", False),
        ("0", False),
    ]
)
def test_parse_personal_stake_stake_value(stake: str, no_error: bool):
    random_stake_data = create_random_personal_stake()
    random_stake_data["stake"] = stake
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    if no_error:
        parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)
        assert parsed_stake
    else:
        with pytest.raises(custom_exceptions.PersonalStakeParsingError):
            parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)


@pytest.mark.parametrize(
    "sport, no_error",
    [
        ("calcio", True),
        ("exchange", True),
        ("ippica", False),
        ("284", False),
    ]
)
def test_parse_personal_stake_sport_parsing(sport: str, no_error: bool):
    random_stake_data = create_random_personal_stake(sport_name=sport)
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    if no_error:
        parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)
        assert parsed_stake
    else:
        with pytest.raises(custom_exceptions.PersonalStakeParsingError):
            parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)


@pytest.mark.parametrize(
    "sport, strategies, no_error",
    [
        ("calcio", ["singolalow"], True),
        ("calcio", ["singolalow", "singolalow"], True),
        ("calcio", ["multipla", "fake"], False),
        ("calcio", ["ippica"], False),
    ]
)
def test_parse_personal_stake_strategies_parsing(sport: str, strategies: str, no_error: bool):
    random_stake_data = create_random_personal_stake(sport_name=sport, strategies_names=strategies)
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    if no_error:
        parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)
        assert parsed_stake
    else:
        with pytest.raises(custom_exceptions.PersonalStakeParsingError):
            parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)


def test_check_stakes_overlapping():
    fake_command_args = get_fake_stake_command_args()
    parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)
    # * no other user stakes
    assert not personal_stakes.check_stakes_overlapping(parsed_stake, [])
    # * no overlapping stakes
    non_overlapping_stakes = []
    for i, _ in enumerate(range(random.randint(2, 10))):
        random_stake_data = create_random_personal_stake()
        random_stake_data["min_quota"] = str(i * 2)
        random_stake_data["max_quota"] = str(i * 2 + 1)
        fake_command_args = get_fake_stake_command_args(random_stake_data)
        parsed_stake = personal_stakes.parse_personal_stake(fake_command_args[:SPORT_INDEX])
        non_overlapping_stakes.append(parsed_stake)
    random_stake_data = create_random_personal_stake()
    random_stake_data["min_quota"] = str(11 * 2)
    random_stake_data["max_quota"] = str(11 * 2 + 1)
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    parsed_stake = personal_stakes.parse_personal_stake(fake_command_args[:SPORT_INDEX])
    assert not personal_stakes.check_stakes_overlapping(parsed_stake, non_overlapping_stakes)
    # * overlapping stake
    random_stake_data = create_random_personal_stake()
    random_stake_data["min_quota"] = str(0.5)
    random_stake_data["max_quota"] = str(1.5)
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    parsed_stake = personal_stakes.parse_personal_stake(fake_command_args[:SPORT_INDEX])
    assert personal_stakes.check_stakes_overlapping(parsed_stake, non_overlapping_stakes)
    # * overlapping stake - comparing all and a specific sport
    random_stake_data = create_random_personal_stake()
    random_stake_data["min_quota"] = str(0.5)
    random_stake_data["max_quota"] = str(1.5)
    random_stake_data["sport"] = "calcio"
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    parsed_stake = personal_stakes.parse_personal_stake(fake_command_args[:STRATEGIES_START_INDEX])
    assert personal_stakes.check_stakes_overlapping(parsed_stake, non_overlapping_stakes)
    # * overlapping stake - comparing all and strategies
    random_stake_data = create_random_personal_stake()
    random_stake_data["min_quota"] = str(0.5)
    random_stake_data["max_quota"] = str(1.5)
    random_stake_data["sport"] = "calcio"
    random_stake_data["strategies"] = ["singola", "multipla"]
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    parsed_stake_with_sports_and_strat = personal_stakes.parse_personal_stake(fake_command_args)
    assert personal_stakes.check_stakes_overlapping(parsed_stake, non_overlapping_stakes)
    # * overlapping stake - comparing specific sport and strategies
    random_stake_data = create_random_personal_stake()
    random_stake_data["min_quota"] = str(1.5)
    random_stake_data["max_quota"] = str(2.5)
    random_stake_data["sport"] = "calcio"
    random_stake_data["strategies"] = ["singola"]
    fake_command_args = get_fake_stake_command_args(random_stake_data)
    parsed_stake = personal_stakes.parse_personal_stake(fake_command_args)
    assert personal_stakes.check_stakes_overlapping(parsed_stake, [parsed_stake_with_sports_and_strat])
