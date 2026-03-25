"""Tests for buildcop_common.config — constants and env var helper."""
import os
import pytest
from buildcop_common import config


def test_constants_accessible():
    """All 11 constants importable from config module."""
    from buildcop_common.config import (
        API_BASE, PARENT_OWNER, PARENT_REPO, BOT_AUTHOR,
        BOT_MAINTAINED, MIN_BUMPS_FOR_CADENCE, MIN_MEDIAN_DAYS,
        NUM_BUMPS, MAX_YELLOW_DAYS, MAX_RED_DAYS,
    )


def test_constants_values():
    assert config.API_BASE == "https://api.github.com"
    assert config.PARENT_OWNER == "sonic-net"
    assert config.PARENT_REPO == "sonic-buildimage"
    assert config.BOT_AUTHOR == "mssonicbld"
    assert isinstance(config.BOT_MAINTAINED, frozenset)
    assert len(config.BOT_MAINTAINED) == 16
    assert "sonic-swss" in config.BOT_MAINTAINED
    assert "dhcprelay" in config.BOT_MAINTAINED
    assert config.MIN_BUMPS_FOR_CADENCE == 5
    assert config.MIN_MEDIAN_DAYS == 1.0
    assert config.NUM_BUMPS == 30
    assert config.MAX_YELLOW_DAYS == 30
    assert config.MAX_RED_DAYS == 60


def test_get_with_default():
    result = config.get("NONEXISTENT_TEST_VAR_XYZ", int, 42)
    assert result == 42


def test_get_reads_env(monkeypatch):
    monkeypatch.setenv("TEST_CFG_VAR", "99")
    assert config.get("TEST_CFG_VAR", int) == 99


def test_get_missing_required():
    with pytest.raises(ValueError, match="DEFINITELY_MISSING"):
        config.get("DEFINITELY_MISSING", str)


def test_get_type_coercion(monkeypatch):
    monkeypatch.setenv("TEST_FLOAT", "3.14")
    assert config.get("TEST_FLOAT", float) == 3.14


def test_get_coercion_failure(monkeypatch):
    monkeypatch.setenv("TEST_BAD_INT", "not_a_number")
    with pytest.raises(ValueError, match="cannot convert"):
        config.get("TEST_BAD_INT", int)
