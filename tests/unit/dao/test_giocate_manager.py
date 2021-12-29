import random

import pytest
from lot_bot.dao import giocate_manager
from lot_bot.models import giocate as giocata_model
from lot_bot import custom_exceptions
from lot_bot import database as db


def create_random_giocata(user_id=None):
    user_id = user_id if user_id else "123456"
    empty_giocata = giocata_model.create_base_giocata()
    # TODO finish

def test_create_giocata(monkeypatch):
    empty_giocata = giocata_model.create_base_giocata()
    empty_giocata["sport"] = "test"
    empty_giocata["giocata_num"] = "12345"
    assert giocate_manager.create_giocata(empty_giocata)
    retrieved_giocata = giocate_manager.retrieve_giocata_by_num_and_sport(empty_giocata["giocata_num"], empty_giocata["sport"])
    assert retrieved_giocata
    for key in empty_giocata:
        assert empty_giocata[key] == retrieved_giocata[key]
    # * inserting the same giocata for error
    del empty_giocata["_id"] # creating the giocata adds the _id field to the dict
    with pytest.raises(custom_exceptions.GiocataCreationError):
        giocate_manager.create_giocata(empty_giocata)
    # * db error
    monkeypatch.setattr(db, "mongo", None)
    new_giocata = giocata_model.create_base_giocata()
    with pytest.raises(Exception):
        giocate_manager.create_giocata(new_giocata)


def test_retrieve_giocata_by_num_and_sport(monkeypatch):
    # * base case tested in create giocata
    # * retrieve non-existing giocata
    assert giocate_manager.retrieve_giocata_by_num_and_sport("impossible_num", "impossible_sport") is None
    # * db error
    monkeypatch.setattr(db, "mongo", None)
    new_giocata = giocata_model.create_base_giocata()
    with pytest.raises(Exception):
        giocate_manager.retrieve_giocata_by_num_and_sport(new_giocata)


def test_retrieve_giocate_from_ids():
    # TODO finish
    return
#     # * multiple retrieves
#     created_ids = []
#     for _ in range(random.randint(2, 10)):
#         empty_giocata = giocata_model.create_base_giocata()
#         empty_giocata["sport"] = "test"
#         empty_giocata["giocata_num"] = "12345"
#         assert giocate_manager.create_giocata(empty_giocata)


def test_update_giocata_outcome_and_get_giocata():
    empty_giocata = giocata_model.create_base_giocata()
    empty_giocata["sport"] = "test_update_outcome"
    empty_giocata["giocata_num"] = 12345
    assert giocate_manager.create_giocata(empty_giocata)
    random_outcome = random.choice(["win", "loss", "?"])
    updated_giocata = giocate_manager.update_giocata_outcome_and_get_giocata(empty_giocata["sport"], empty_giocata["giocata_num"], random_outcome)
    assert updated_giocata and updated_giocata["outcome"] == random_outcome
    # * giocata not present
    assert giocate_manager.update_giocata_outcome_and_get_giocata(empty_giocata["sport"], "impossible test", random_outcome) is None
