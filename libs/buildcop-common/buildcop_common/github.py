"""GitHub API session factory, response checker, and retry decorator.

Builds on create_session() from http.py — adds auth headers, typed response
checking, and reusable retry with exponential backoff.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import TYPE_CHECKING, Callable, ParamSpec, TypeVar

import requests

from buildcop_common.config import get as config_get
from buildcop_common.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    TransientError,
)
from buildcop_common.http import create_session

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

def create_github_session(token: str | None = None) -> requests.Session:
    """Create an authenticated GitHub API session.

    Args:
        token: GitHub personal access token.  If None, reads from the
            ``GITHUB_TOKEN`` environment variable via config.get().

    Returns:
        requests.Session with Authorization and Accept headers plus
        timeout defaults from create_session().

    Raises:
        AuthenticationError: If token is missing or empty.
    """
    if token is None:
        try:
            token = config_get("GITHUB_TOKEN", str)
        except ValueError as exc:
            raise AuthenticationError(
                "GITHUB_TOKEN environment variable is not set. "
                "Provide a token or set GITHUB_TOKEN."
            ) from exc

    if not token or not token.strip():
        raise AuthenticationError(
            "GitHub token is empty. Provide a valid token."
        )

    session = create_session()
    session.headers.update({
        "Authorization": f"token {token.strip()}",
        "Accept": "application/vnd.github.v3+json",
    })
    return session


# ---------------------------------------------------------------------------
# Response checker
# ---------------------------------------------------------------------------

def check_response(response: requests.Response) -> None:
    """Raise a typed exception for non-2xx responses.

    Call after ``session.get()`` / ``session.post()`` instead of
    ``raise_for_status()``.

    Priority order:
        1. 401 → AuthenticationError
        2. 403 with X-RateLimit-Remaining: 0 → RateLimitError
        3. 429 → RateLimitError
        4. 5xx → TransientError (retriable)
        5. Other 4xx → APIError
    """
    if response.ok:
        return None

    status = response.status_code

    if status == 401:
        raise AuthenticationError(
            f"GitHub authentication failed: {response.text[:200]}",
            status_code=status,
            response=response,
        )

    # Rate limit: 429 always, 403 only when remaining == 0
    if status == 429 or (
        status == 403
        and response.headers.get("X-RateLimit-Remaining") == "0"
    ):
        reset_at = float(response.headers.get("X-RateLimit-Reset", "0"))
        raise RateLimitError(
            f"GitHub rate limit exceeded (HTTP {status}). "
            f"Resets at {reset_at}",
            reset_at=reset_at,
            status_code=status,
            response=response,
        )

    if 500 <= status < 600:
        raise TransientError(
            f"GitHub server error (HTTP {status}): {response.text[:200]}",
            status_code=status,
            response=response,
        )

    # All other errors (403 without rate-limit, 404, 422, etc.)
    raise APIError(
        f"GitHub API error (HTTP {status}): {response.text[:200]}",
        status_code=status,
        response=response,
    )


# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------

def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Retry decorator with exponential backoff for transient API failures.

    Retries on:
        - TransientError (5xx from check_response)
        - requests.ConnectionError (network failures)
        - requests.Timeout (connect/read timeouts)

    Does NOT retry:
        - RateLimitError (caller must handle)
        - AuthenticationError (permanent)
        - APIError (4xx client errors)

    Args:
        max_retries: Maximum number of retry attempts (not counting initial).
        base_delay: Initial delay in seconds before first retry.
        backoff_factor: Multiplier applied each retry (delay = base * factor^attempt).
        max_delay: Maximum delay cap in seconds.
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exc: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (TransientError, requests.ConnectionError,
                        requests.Timeout) as exc:
                    last_exc = exc
                    if attempt < max_retries:
                        delay = min(
                            base_delay * (backoff_factor ** attempt),
                            max_delay,
                        )
                        logger.warning(
                            "Retry %d/%d for %s: %s (sleeping %.1fs)",
                            attempt + 1,
                            max_retries,
                            func.__name__,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
            # All retries exhausted — re-raise last exception
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
