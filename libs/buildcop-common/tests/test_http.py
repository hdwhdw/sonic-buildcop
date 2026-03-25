"""Tests for buildcop_common.http — timeout-aware HTTP session factory."""
from unittest.mock import MagicMock, patch

import requests

from buildcop_common.http import TimeoutHTTPAdapter, create_session


def test_create_session_returns_session():
    session = create_session()
    assert isinstance(session, requests.Session)


def test_session_has_timeout_adapter():
    session = create_session()
    adapter = session.get_adapter("https://example.com")
    assert isinstance(adapter, TimeoutHTTPAdapter)


def test_default_timeout():
    session = create_session()
    adapter = session.get_adapter("https://example.com")
    assert adapter.timeout == (30.0, 60.0)


def test_custom_timeout():
    session = create_session(timeout=(5.0, 10.0))
    adapter = session.get_adapter("https://example.com")
    assert adapter.timeout == (5.0, 10.0)


def test_timeout_injected_on_send():
    adapter = TimeoutHTTPAdapter(timeout=(30.0, 60.0))
    mock_request = MagicMock()
    with patch.object(
        requests.adapters.HTTPAdapter, "send", return_value=MagicMock()
    ) as mock_send:
        adapter.send(mock_request)
        _, kwargs = mock_send.call_args
        assert kwargs["timeout"] == (30.0, 60.0)


def test_explicit_timeout_not_overridden():
    adapter = TimeoutHTTPAdapter(timeout=(30.0, 60.0))
    mock_request = MagicMock()
    with patch.object(
        requests.adapters.HTTPAdapter, "send", return_value=MagicMock()
    ) as mock_send:
        adapter.send(mock_request, timeout=(1.0, 2.0))
        _, kwargs = mock_send.call_args
        assert kwargs["timeout"] == (1.0, 2.0)
