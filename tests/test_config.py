"""Config: env loading, clamping, and validation."""

from __future__ import annotations

import pytest

from connector.config import Config, ConfigError


def test_from_env_requires_values(monkeypatch):
    for key in ("WC_STORE_URL", "WC_CONSUMER_KEY", "WC_CONSUMER_SECRET"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ConfigError):
        Config.from_env()


def test_from_env_reads_and_clamps(monkeypatch):
    monkeypatch.setenv("WC_STORE_URL", "https://shop.example.com/")
    monkeypatch.setenv("WC_CONSUMER_KEY", "ck_x")
    monkeypatch.setenv("WC_CONSUMER_SECRET", "cs_x")
    monkeypatch.setenv("WC_PER_PAGE", "500")
    cfg = Config.from_env()
    assert cfg.store_url == "https://shop.example.com"  # trailing slash stripped
    assert cfg.per_page == 100  # clamped to the WooCommerce max
    cfg.validate()  # should not raise


def test_validate_rejects_bad_url():
    cfg = Config(store_url="shop.example.com", consumer_key="a", consumer_secret="b")
    with pytest.raises(ConfigError):
        cfg.validate()


def test_validate_rejects_missing_secret():
    cfg = Config(store_url="https://x.example.com", consumer_key="a", consumer_secret="")
    with pytest.raises(ConfigError):
        cfg.validate()


def test_validate_rejects_nonpositive_rps():
    cfg = Config(store_url="https://x.example.com", consumer_key="a", consumer_secret="b", requests_per_second=0)
    with pytest.raises(ConfigError):
        cfg.validate()
