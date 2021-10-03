import random

import pytest
from lot_bot.dao import giocate_manager
from lot_bot.models import giocate as giocata_model



def test_create_giocata():
    empty_giocata = giocata_model.create_base_giocata()
    empty_giocata["sport"] = "test"
    empty_giocata["giocata_num"] = 12345
    assert giocate_manager.create_giocata(empty_giocata)
    retrieved_giocata = giocate_manager.retrieve_giocata_by_num_and_sport(empty_giocata["giocata_num"], empty_giocata["sport"])
    assert retrieved_giocata
    for key in empty_giocata:
        assert empty_giocata[key] == retrieved_giocata[key]
    # inserting the same giocata for error
    del empty_giocata["_id"] # creating the giocata adds the _id field to the dict
    with pytest.raises(Exception):
        giocate_manager.create_giocata(empty_giocata)



def test_retrieve_giocata_by_num_and_sport():
    pass


def test_retrieve_giocate_from_ids():
    pass


def test_update_giocata_outcome():
    empty_giocata = giocata_model.create_base_giocata()
    empty_giocata["sport"] = "test_update_outcome"
    empty_giocata["giocata_num"] = 12345
    assert giocate_manager.create_giocata(empty_giocata)
    random_outcome = random.choice(["win", "loss", "?"])
    assert giocate_manager.update_giocata_outcome(empty_giocata["sport"], empty_giocata["giocata_num"], random_outcome)
    updated_giocata = giocate_manager.retrieve_giocata_by_num_and_sport(empty_giocata["giocata_num"], empty_giocata["sport"])
    assert updated_giocata["outcome"] == random_outcome
