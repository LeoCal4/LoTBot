import pytest

from lot_bot import config as cfg

@pytest.fixture
def reset_config(monkeypatch):
    yield
    monkeypatch.setenv("ENV", "testing")
    cfg.create_config()


def test_config(monkeypatch, reset_config):
    monkeypatch.setenv("ENV", "")
    cfg.create_config()
    assert type(cfg.config) == cfg.Development
    monkeypatch.setenv("ENV", "dotenv")
    cfg.create_config()
    assert type(cfg.config) == cfg.Config
    monkeypatch.setenv("ENV", "testing")
    cfg.create_config()
    assert type(cfg.config) == cfg.Testing
    monkeypatch.setenv("ENV", "development")
    cfg.create_config()
    assert type(cfg.config) == cfg.Development

