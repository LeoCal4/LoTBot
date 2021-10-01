import datetime
import random
import string
from typing import Dict, Tuple, Callable

from lot_bot import database as db
from lot_bot import logger as lgr
from lot_bot import utils
from lot_bot.dao import giocate_manager
from lot_bot.models import giocate as giocata_model


def test_create_giocata():
    lgr.logger.error(type(db.mongo))
    empty_giocata = giocata_model.create_base_giocata()
    empty_giocata["sport"] = "test"
    empty_giocata["giocata_num"] = 12345
    assert giocate_manager.create_giocata(empty_giocata)
    retrieved_giocata = giocate_manager.retrieve_giocata(empty_giocata)
    assert retrieved_giocata
    for key in empty_giocata:
        # lgr.logger.warning(key)
        assert empty_giocata[key] == retrieved_giocata[key]
    # inserting the same giocata for error
    del empty_giocata["_id"] # creating the giocata adds the _id field to the dict
    assert not giocate_manager.create_giocata(empty_giocata)



def test_retrieve_giocata():
    pass


def test_retrieve_giocate_from_ids():
    pass
