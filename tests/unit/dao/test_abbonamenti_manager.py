import random

import pytest
from lot_bot import constants as cst
from lot_bot import database as db
from lot_bot.dao import abbonamenti_manager
from lot_bot.models import sports as spr


def get_abbonamento_data(user_id=None, sport_name=None, strategy_name=None) -> dict:
    user_id = user_id if user_id else random.randrange(0, 1000)
    sport = None
    if not sport_name:
        sport = random.choice(spr.sports_container.astuple())
        sport_name = sport.name
    if not strategy_name:
        sport = sport if sport else spr.sports_container.get_sport_from_string(sport_name)
        strategy_name = random.choice(sport.strategies)
    return {
        "telegramID": user_id,
        "sport": sport_name,
        "strategia": sport_name,
    }

@pytest.fixture
def clear_abbonamenti():
    yield
    abbonamenti_manager.delete_all_abbonamenti()


@pytest.fixture
def new_abbonamento():
    abbonamento_data = get_abbonamento_data()
    abbonamenti_manager.create_abbonamento(abbonamento_data)
    yield abbonamento_data


def test_create_abbonamento(monkeypatch, clear_abbonamenti):
    abbonamento_data = get_abbonamento_data()
    abbonamenti_manager.create_abbonamento(abbonamento_data)
    ret_abbonamento = abbonamenti_manager.retrieve_abbonamento_sport_strategy_from_user_id(
        abbonamento_data["telegramID"],
        abbonamento_data["sport"],
        abbonamento_data["strategia"])
    assert ret_abbonamento, "Abbonamento was not created"
    for key in abbonamento_data:
        assert abbonamento_data[key] == ret_abbonamento[key]
    # db error
    abbonamento_data = get_abbonamento_data()
    monkeypatch.setattr(db, "mongo", None)
    assert not abbonamenti_manager.create_abbonamento(abbonamento_data)


def test_retrieve_abbonamenti(monkeypatch, new_abbonamento: dict, clear_abbonamenti):
    # single retrieve with one field tested in create_abbonamento
    # single retrieve with more than one field
    assert len(abbonamenti_manager.retrieve_abbonamenti({
        "sport": new_abbonamento["sport"], 
        "strategia": new_abbonamento["strategia"]
    })) == 1
    # multiple document retrieve
    abbonamento_data2 = get_abbonamento_data(sport_name=new_abbonamento["sport"])
    abbonamenti_manager.create_abbonamento(abbonamento_data2)
    ret_abbonamenti = abbonamenti_manager.retrieve_abbonamenti({"sport": new_abbonamento["sport"]})
    assert len(ret_abbonamenti) == 2
    # inexistent retrieve
    assert len(abbonamenti_manager.retrieve_abbonamenti({"sport": "non existent sport"})) == 0
    # db error
    monkeypatch.setattr(db, "mongo", None)
    assert abbonamenti_manager.retrieve_abbonamenti({"sport": new_abbonamento["sport"]}) is None


def test_retrieve_abbonamento_sport_strategy_from_user_id(monkeypatch, new_abbonamento: dict, clear_abbonamenti):
    assert abbonamenti_manager.retrieve_abbonamento_sport_strategy_from_user_id(
        new_abbonamento["telegramID"], 
        new_abbonamento["sport"], 
        new_abbonamento["strategia"]
    )
    # inexistent retrieve
    assert abbonamenti_manager.retrieve_abbonamento_sport_strategy_from_user_id(
        -1, 
        "", 
        ""
    ) is None
    # db error
    monkeypatch.setattr(db, "mongo", None)
    assert abbonamenti_manager.retrieve_abbonamento_sport_strategy_from_user_id(
        new_abbonamento["telegramID"], 
        new_abbonamento["sport"], 
        new_abbonamento["strategia"]
    ) is None


def test_delete_abbonamento(monkeypatch, new_abbonamento: dict, clear_abbonamenti):
    assert abbonamenti_manager.retrieve_abbonamenti(new_abbonamento)
    assert abbonamenti_manager.delete_abbonamento(new_abbonamento)
    assert abbonamenti_manager.retrieve_abbonamenti(new_abbonamento) == []
    # inexistent delete (still true)
    fake_abbonamento = get_abbonamento_data()
    assert abbonamenti_manager.delete_abbonamento(fake_abbonamento)
    # db error
    monkeypatch.setattr(db, "mongo", None)
    assert not abbonamenti_manager.delete_abbonamento(new_abbonamento)


def test_delete_abbonamenti_for_user_id(monkeypatch, new_abbonamento: dict, clear_abbonamenti):
    user_id = new_abbonamento["telegramID"]
    abbonamento_data = get_abbonamento_data(user_id=user_id)
    abbonamenti_manager.create_abbonamento(abbonamento_data)
    assert abbonamenti_manager.delete_abbonamenti_for_user_id(user_id)
    assert abbonamenti_manager.retrieve_abbonamenti({"telegramID": user_id}) == []
    # inexistent delete (still true)
    fake_abbonamento = get_abbonamento_data()
    assert abbonamenti_manager.delete_abbonamenti_for_user_id(fake_abbonamento["telegramID"])
    # db error
    monkeypatch.setattr(db, "mongo", None)
    assert not abbonamenti_manager.delete_abbonamenti_for_user_id(new_abbonamento["telegramID"])
