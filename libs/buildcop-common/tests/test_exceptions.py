"""Tests for buildcop_common.exceptions — typed API exception hierarchy."""
import time
from unittest.mock import MagicMock

import pytest

from buildcop_common.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    TransientError,
)


def test_api_error_is_exception():
    assert issubclass(APIError, Exception)


def test_api_error_attributes():
    resp = MagicMock()
    err = APIError("something broke", status_code=404, response=resp)
    assert str(err) == "something broke"
    assert err.status_code == 404
    assert err.response is resp


def test_api_error_defaults():
    err = APIError("bare error")
    assert err.status_code is None
    assert err.response is None


def test_authentication_error_inherits_api_error():
    err = AuthenticationError("bad token", status_code=401)
    assert isinstance(err, APIError)
    assert err.status_code == 401


def test_rate_limit_error_attributes():
    err = RateLimitError(
        "rate limited",
        reset_at=1700000000.0,
        status_code=429,
    )
    assert isinstance(err, APIError)
    assert err.reset_at == 1700000000.0
    assert err.status_code == 429


def test_rate_limit_error_retry_after():
    future = time.time() + 60.0
    err = RateLimitError("wait", reset_at=future)
    # retry_after should be roughly 60 (±1s tolerance)
    assert 58.0 <= err.retry_after <= 62.0


def test_rate_limit_error_retry_after_past():
    past = time.time() - 100.0
    err = RateLimitError("expired", reset_at=past)
    assert err.retry_after == 0.0


def test_transient_error_inherits_api_error():
    err = TransientError("server error", status_code=502)
    assert isinstance(err, APIError)
    assert err.status_code == 502
