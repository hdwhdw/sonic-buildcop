"""Tests for buildcop_common.github — session factory, response checker, retry."""
from unittest.mock import patch

import pytest
import requests

from buildcop_common.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    TransientError,
)
from buildcop_common.github import check_response, create_github_session, retry


# ---------------------------------------------------------------------------
# Test helper
# ---------------------------------------------------------------------------

def _make_response(
    status_code: int,
    headers: dict | None = None,
    text: str = "",
) -> requests.Response:
    """Build a requests.Response with the given status, headers, and body."""
    resp = requests.Response()
    resp.status_code = status_code
    resp._content = text.encode()
    if headers:
        resp.headers.update(headers)
    return resp


# ---------------------------------------------------------------------------
# create_github_session
# ---------------------------------------------------------------------------

def test_create_github_session_explicit_token():
    session = create_github_session(token="ghp_test123")
    assert session.headers["Authorization"] == "token ghp_test123"
    assert session.headers["Accept"] == "application/vnd.github.v3+json"


def test_create_github_session_from_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_from_env")
    session = create_github_session()
    assert session.headers["Authorization"] == "token ghp_from_env"


def test_create_github_session_missing_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(AuthenticationError, match="GITHUB_TOKEN"):
        create_github_session()


def test_create_github_session_empty_token():
    with pytest.raises(AuthenticationError, match="empty"):
        create_github_session(token="")


def test_create_github_session_whitespace_token():
    with pytest.raises(AuthenticationError, match="empty"):
        create_github_session(token="   ")


# ---------------------------------------------------------------------------
# check_response
# ---------------------------------------------------------------------------

def test_check_response_success():
    resp = _make_response(200)
    assert check_response(resp) is None


def test_check_response_401_auth_error():
    resp = _make_response(401, text="Bad credentials")
    with pytest.raises(AuthenticationError) as exc_info:
        check_response(resp)
    assert exc_info.value.status_code == 401


def test_check_response_429_rate_limit():
    resp = _make_response(429, headers={
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1700000000",
    })
    with pytest.raises(RateLimitError) as exc_info:
        check_response(resp)
    assert exc_info.value.reset_at == 1700000000.0
    assert exc_info.value.status_code == 429


def test_check_response_403_rate_limit():
    resp = _make_response(403, headers={
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1700000000",
    })
    with pytest.raises(RateLimitError) as exc_info:
        check_response(resp)
    assert exc_info.value.reset_at == 1700000000.0
    assert exc_info.value.status_code == 403


def test_check_response_403_not_rate_limit():
    resp = _make_response(403, text="Forbidden")
    with pytest.raises(APIError) as exc_info:
        check_response(resp)
    assert exc_info.value.status_code == 403
    assert not isinstance(exc_info.value, RateLimitError)


def test_check_response_500_transient():
    resp = _make_response(500, text="Internal Server Error")
    with pytest.raises(TransientError) as exc_info:
        check_response(resp)
    assert exc_info.value.status_code == 500


def test_check_response_502_transient():
    resp = _make_response(502, text="Bad Gateway")
    with pytest.raises(TransientError) as exc_info:
        check_response(resp)
    assert exc_info.value.status_code == 502


def test_check_response_404_api_error():
    resp = _make_response(404, text="Not Found")
    with pytest.raises(APIError) as exc_info:
        check_response(resp)
    assert exc_info.value.status_code == 404
    assert not isinstance(exc_info.value, TransientError)


# ---------------------------------------------------------------------------
# retry decorator
# ---------------------------------------------------------------------------

def test_retry_on_transient_error():
    call_count = 0

    @retry(max_retries=2, base_delay=0)
    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientError("server error", status_code=500)
        return "ok"

    assert flaky() == "ok"
    assert call_count == 3


def test_retry_on_connection_error():
    call_count = 0

    @retry(max_retries=1, base_delay=0)
    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise requests.ConnectionError("refused")
        return "ok"

    assert flaky() == "ok"
    assert call_count == 2


def test_retry_exhaustion():
    @retry(max_retries=2, base_delay=0)
    def always_fails():
        raise TransientError("always broken", status_code=503)

    with pytest.raises(TransientError, match="always broken"):
        always_fails()


def test_no_retry_on_rate_limit():
    call_count = 0

    @retry(max_retries=3, base_delay=0)
    def rate_limited():
        nonlocal call_count
        call_count += 1
        raise RateLimitError("limit hit", reset_at=1700000000.0)

    with pytest.raises(RateLimitError):
        rate_limited()
    assert call_count == 1  # NOT retried


def test_no_retry_on_auth_error():
    call_count = 0

    @retry(max_retries=3, base_delay=0)
    def unauthorized():
        nonlocal call_count
        call_count += 1
        raise AuthenticationError("bad token", status_code=401)

    with pytest.raises(AuthenticationError):
        unauthorized()
    assert call_count == 1  # NOT retried
