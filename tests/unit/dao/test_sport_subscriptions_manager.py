import random
from typing import Dict
from pymongo.message import delete

import pytest
from lot_bot import database as db
from lot_bot.dao import sport_subscriptions_manager, user_manager
from lot_bot.models import sports as spr
from lot_bot import logger as lgr
from lot_bot.models import users as user_model


def get_sport_sub_data(user_id=None, sport_name=None, strategy_name=None) -> dict:
    user_id = user_id if user_id is not None else random.randrange(0, 1000)
    sport = None
    if sport_name is None:
        sport = random.choice(spr.sports_container.astuple())
        sport_name = sport.name
    if strategy_name is None:
        sport = sport if sport else spr.sports_container.get_sport(sport_name)
        strategy_name = random.choice(sport.strategies).name
    return {
        "telegramID": user_id,
        "sport": sport_name,
        "strategy": strategy_name,
    }


def clear_users():
    user_manager.delete_all_users()


@pytest.fixture
def new_sport_subscription(new_user: Dict):
    sport_sub_data = get_sport_sub_data(user_id=new_user["_id"])
    sport_subscriptions_manager.create_sport_subscription(sport_sub_data)
    yield sport_sub_data


def test_create_sport_subscription(monkeypatch, new_user: Dict): #):
    sport_sub_data = get_sport_sub_data(user_id=new_user["_id"])
    sport_subscriptions_manager.create_sport_subscription(sport_sub_data)
    ret_sport_subscription = sport_subscriptions_manager.retrieve_subscribed_strats_from_user_id_and_sport(
        sport_sub_data["telegramID"],
        sport_sub_data["sport"]
    )
    assert ret_sport_subscription, "Abbonamento was not created"
    assert ret_sport_subscription[0] == sport_sub_data["strategy"]
    # * create with sport already there
    # to ensure there is a different strategy
    sport_sub_data2 = get_sport_sub_data(user_id=new_user["_id"], sport_name=sport_sub_data["sport"])
    while sport_sub_data2 == sport_sub_data:
        sport_sub_data2 = get_sport_sub_data(user_id=new_user["_id"], sport_name=sport_sub_data["sport"])
    sport_subscriptions_manager.create_sport_subscription(sport_sub_data2)
    ret_sport_subscription2 = sport_subscriptions_manager.retrieve_subscribed_strats_from_user_id_and_sport(
        sport_sub_data["telegramID"],
        sport_sub_data["sport"]
    )
    assert len(ret_sport_subscription2) == 2
    assert sport_sub_data["strategy"] in ret_sport_subscription2
    assert sport_sub_data2["strategy"] in ret_sport_subscription2
    # * create another sport
    sport_sub_data3 = get_sport_sub_data(user_id=new_user["_id"])
    while sport_sub_data3["sport"] == sport_sub_data["sport"]:
        sport_sub_data3 = get_sport_sub_data(user_id=new_user["_id"])
    sport_subscriptions_manager.create_sport_subscription(sport_sub_data3)
    ret_sport_subscription2 = sport_subscriptions_manager.retrieve_subscribed_strats_from_user_id_and_sport(
        sport_sub_data3["telegramID"],
        sport_sub_data3["sport"]
    )
    # * clear db
    clear_users()
    # db error
    sport_sub_data = get_sport_sub_data()
    monkeypatch.setattr(db, "mongo", None)
    with pytest.raises(Exception):
        sport_subscriptions_manager.create_sport_subscription(sport_sub_data)


def test_retrieve_sport_subscriptions_from_user_id(monkeypatch, new_sport_subscription: dict):
    sport_subscription = sport_subscriptions_manager.retrieve_sport_subscriptions_from_user_id(
        new_sport_subscription["telegramID"]
    )[0]
    assert sport_subscription != []
    assert sport_subscription["sport"] ==  new_sport_subscription["sport"]
    assert sport_subscription["strategies"][0] == new_sport_subscription["strategy"]
    # * multiple retrieve 
    subscriptions = []
    idx = 0
    sports_idx = {}
    # * add first subscription
    subscriptions.append({"sport": sport_subscription["sport"], "strategies": [sport_subscription["strategies"][0]]})
    sports_idx[sport_subscription["sport"]] = idx
    idx += 1
    for _ in range(random.randint(2, 10)):
        sport_sub_data = get_sport_sub_data(user_id=new_sport_subscription["telegramID"])
        creation_result = sport_subscriptions_manager.create_sport_subscription(sport_sub_data)
        if creation_result:
            if sport_sub_data["sport"] in sports_idx:
                # add strategy while removing duplicates
                temp_strats = subscriptions[sports_idx[sport_sub_data["sport"]]]["strategies"]
                temp_strats.append(sport_sub_data["strategy"])
                temp_strats = list(dict.fromkeys(temp_strats))
                subscriptions[sports_idx[sport_sub_data["sport"]]]["strategies"] = temp_strats
            else:
                # create new sport and update the sports indexes
                subscriptions.append({"sport": sport_sub_data["sport"], "strategies": [sport_sub_data["strategy"]]})
                sports_idx[sport_sub_data["sport"]] = idx
                idx += 1
    ret_subscriptions = sport_subscriptions_manager.retrieve_sport_subscriptions_from_user_id(new_sport_subscription["telegramID"])
    assert len(ret_subscriptions) == len(subscriptions)
    for sub in subscriptions:
        assert sub in ret_subscriptions
    # inexistent retrieve
    assert sport_subscriptions_manager.retrieve_sport_subscriptions_from_user_id(-1) == []
    # * clear db
    clear_users()
    # db error
    monkeypatch.setattr(db, "mongo", None)
    with pytest.raises(Exception):
        sport_subscriptions_manager.retrieve_sport_subscriptions_from_user_id(new_sport_subscription["telegramID"])


def test_retrieve_subscribed_strats_from_user_id_and_sport(monkeypatch, new_sport_subscription: dict):
    sport_subscription = sport_subscriptions_manager.retrieve_subscribed_strats_from_user_id_and_sport(
        new_sport_subscription["telegramID"], 
        new_sport_subscription["sport"]
    )
    assert sport_subscription != []
    assert sport_subscription[0] == new_sport_subscription["strategy"]
    # inexistent retrieve
    assert sport_subscriptions_manager.retrieve_subscribed_strats_from_user_id_and_sport(
        -1, 
        ""
    ) == []
    # * clear db
    clear_users()
    # db error
    monkeypatch.setattr(db, "mongo", None)
    with pytest.raises(Exception):
        sport_subscriptions_manager.retrieve_subscribed_strats_from_user_id_and_sport(
        new_sport_subscription["telegramID"], 
        new_sport_subscription["sport"]
    )


def test_retrieve_all_user_ids_sub_to_sport_and_strategy(monkeypatch, new_sport_subscription: dict):
    ret_user = sport_subscriptions_manager.retrieve_all_user_ids_sub_to_sport_and_strategy(
        new_sport_subscription["sport"],
        new_sport_subscription["strategy"]
    )
    assert ret_user != []
    assert ret_user [-1] ==  new_sport_subscription["telegramID"]
    # retrieve multiple
    user_ids = []
    for _ in range(random.randint(2, 10)):
        user_data = user_model.create_base_user_data()
        user_data["_id"] = random.randint(1, 999999)
        user_created = user_manager.create_user(user_data)
        if user_created:
            sport_sub_data = get_sport_sub_data(
                user_id=user_data["_id"], 
                sport_name=new_sport_subscription["sport"],
                strategy_name=new_sport_subscription["strategy"]
            )
            sport_subscriptions_manager.create_sport_subscription(sport_sub_data)
            user_ids.append(user_data["_id"])
    # * add other random subscriptions which won't be returned
    for _ in range(random.randint(2, 10)):
        user_data = user_model.create_base_user_data()
        user_data["_id"] = random.randint(1, 999999)
        user_created = user_manager.create_user(user_data)
        if user_created:
            sport_sub_data = get_sport_sub_data(user_id=user_data["_id"])
            while sport_sub_data["sport"] == new_sport_subscription["sport"]:
                sport_sub_data = get_sport_sub_data(user_id=user_data["_id"])
            sport_subscriptions_manager.create_sport_subscription(sport_sub_data)
    ret_sub_users = sport_subscriptions_manager.retrieve_all_user_ids_sub_to_sport_and_strategy(
        new_sport_subscription["sport"],
        new_sport_subscription["strategy"]
    )
    assert len(ret_sub_users) == len(user_ids) + 1
    for user_id in user_ids:
        assert user_id in ret_sub_users
    # inexistent retrieve
    assert sport_subscriptions_manager.retrieve_all_user_ids_sub_to_sport_and_strategy(
        "", 
        ""
    ) == []
    # * clean db
    clear_users()
    # * db error
    monkeypatch.setattr(db, "mongo", None)
    with pytest.raises(Exception):
        sport_subscriptions_manager.retrieve_all_user_ids_sub_to_sport_and_strategy(
        new_sport_subscription["sport"],
        new_sport_subscription["strategy"]
    )


def test_delete_sport_subscription(monkeypatch, new_sport_subscription: dict):
    assert sport_subscriptions_manager.retrieve_subscribed_strats_from_user_id_and_sport(new_sport_subscription["telegramID"], new_sport_subscription["sport"])
    assert sport_subscriptions_manager.delete_sport_subscription(new_sport_subscription)
    assert sport_subscriptions_manager.retrieve_subscribed_strats_from_user_id_and_sport(
        new_sport_subscription["telegramID"], new_sport_subscription["sport"]) == []
    # * inexistent delete
    fake_sport_subscription = get_sport_sub_data(user_id=new_sport_subscription["telegramID"])
    delete_result = sport_subscriptions_manager.delete_sport_subscription(fake_sport_subscription)
    assert not delete_result
    # * clean db
    clear_users()
    # * db error
    monkeypatch.setattr(db, "mongo", None)
    with pytest.raises(Exception):
        sport_subscriptions_manager.delete_sport_subscription(new_sport_subscription)


# def test_delete_sport_subscriptions_for_user_id(monkeypatch, new_sport_subscription: dict):
#     user_id = new_sport_subscription["telegramID"]
#     sport_sub_data = get_sport_sub_data(user_id=user_id)
#     sport_subscriptions_manager.create_sport_subscription(sport_sub_data)
#     assert sport_subscriptions_manager.delete_sport_subscriptions_for_user_id(user_id)
#     assert sport_subscriptions_manager.retrieve_sport_subscriptions({"telegramID": user_id}) == []
#     # inexistent delete (still true)
#     fake_sport_subscription = get_sport_sub_data()
#     assert sport_subscriptions_manager.delete_sport_subscriptions_for_user_id(fake_sport_subscription["telegramID"])
#     # db error
#     monkeypatch.setattr(db, "mongo", None)
#     assert not sport_subscriptions_manager.delete_sport_subscriptions_for_user_id(new_sport_subscription["telegramID"])
