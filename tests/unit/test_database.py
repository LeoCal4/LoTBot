import pytest

from lot_bot import database as db
from lot_bot import config as cfg


def test_database(monkeypatch):
    real_mongo_db_url = cfg.config.MONGO_DB_URL
    monkeypatch.setattr(cfg.config, "MONGO_DB_URL", "wrong url")
    with pytest.raises(Exception):
        db.create_db()
    monkeypatch.setattr(cfg.config, "MONGO_DB_URL", real_mongo_db_url)
    db.create_db()
    assert db.mongo
    assert db.mongo.abbonamenti
    assert db.mongo.utenti
