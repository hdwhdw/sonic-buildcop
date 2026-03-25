# Phase 3: Core API Infrastructure - Research

**Researched:** 2026-03-25
**Domain:** Python HTTP retry/rate-limit/auth patterns with `requests` library
**Confidence:** HIGH

## Summary

Phase 3 builds GitHub API infrastructure **on top of raw `requests`** — not PyGithub (deferred to v2 per REQUIREMENTS.md). The scope is narrow and well-defined: a typed exception hierarchy, a reusable retry decorator, rate-limit detection from response headers, and an authenticated session factory. All four components live in `buildcop_common` and build on the existing `create_session()` and `config.get()` from Phase 2.

The implementation requires zero new runtime dependencies. Python's stdlib (`functools`, `time`, `logging`) plus the already-installed `requests` (2.31.0) and `urllib3` (2.0.7) provide everything needed. The retry decorator is a pure-Python function decorator (not `tenacity` or `backoff`) — this matches the project's minimal-dependency philosophy and the simple 3-retry, 2^n pattern already proven in `collector.py`. Rate-limit detection inspects `X-RateLimit-*` headers and raises `RateLimitError` with a `reset_at` timestamp — callers decide whether to sleep or abort.

Testing uses `unittest.mock` (already used throughout the project) — no `responses` or `pytest-mock` needed. The existing test style (`MagicMock`, `patch`, direct assertions) is well-established and should be continued.

**Primary recommendation:** Build all four components as pure Python with zero new dependencies. Use `exceptions.py` for the type hierarchy and `github.py` for session factory + response checking. The `@retry` decorator goes in `github.py` (or a separate `retry.py` if the planner prefers separation of concerns). Re-export everything from `__init__.py`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None — user deferred all decisions to Claude's discretion.

### Claude's Discretion
- **Retry mechanism**: Decorator-based (`@retry`) for reusability across any function. Match existing pattern: 3 retries, exponential backoff (2^n seconds). Retry on 5xx, network errors, and timeouts. Rate-limited (429) responses should NOT be retried by the generic retry decorator — they get separate handling.
- **Rate-limit strategy**: Raise `RateLimitError` immediately with `reset_at` timestamp attached to the exception. Callers decide whether to sleep or abort. This is the simpler, more predictable approach — auto-sleeping can block for minutes and is surprising behavior in a library.
- **Auth factory API**: Support both explicit token parameter AND auto-read from `GITHUB_TOKEN` env var. Signature: `create_github_session(token: str | None = None)`. If `token` is None, reads from env via `config.get("GITHUB_TOKEN", str)`. Raises `AuthenticationError` on missing/empty token either way. Explicit param enables testing.
- **Exception hierarchy**: `APIError` base, `AuthenticationError(APIError)`, `RateLimitError(APIError)` with `reset_at: float` attribute. Consider a `TransientError(APIError)` for 5xx so callers can distinguish retriable from permanent failures.
- **Module placement**: New modules in `buildcop_common`: `exceptions.py` for typed exceptions, `github.py` for GitHub session factory + auth + retry + rate-limit. Extend existing `http.py` if needed.
- **Existing retry extraction**: The retry decorator should be generic enough that Phase 4 can replace `collect_submodule()`'s manual retry loop with it.
- **Backoff defaults**: Base=1s, factor=2, max_delay=30s, max_retries=3. Matches existing 2^n pattern.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | GitHub auth & session factory with token validation and proper error on missing token | Session factory pattern: `create_github_session(token=None)` builds on `create_session()`, adds `Authorization: token {token}` + `Accept` header, validates token via `config.get()` or explicit param |
| API-02 | Reusable retry decorator with exponential backoff (extracted from `collect_submodule`) | Pure-Python `@retry` decorator using `functools.wraps` + `time.sleep(2^attempt)`. Catches `TransientError` + `requests.ConnectionError` + `requests.Timeout`. No new dependencies. |
| API-03 | Rate-limit-aware request handling — read `X-RateLimit-*` headers, handle 403/429 specifically | Response-checking function inspects status code + headers. 429 → `RateLimitError`. 403 with `X-RateLimit-Remaining: 0` → `RateLimitError`. `reset_at` from `X-RateLimit-Reset` header. |
| API-04 | Custom exception types: `APIError`, `RateLimitError`, `AuthenticationError` | Exception hierarchy in `exceptions.py`. `APIError(Exception)` base with `status_code` + `message`. `RateLimitError(APIError)` with `reset_at: float`. `AuthenticationError(APIError)`. `TransientError(APIError)`. |
</phase_requirements>

## Standard Stack

### Core (Already Installed — Zero New Dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.31.0 | HTTP client | Already installed, used throughout codebase. Phase 3 wraps it. |
| urllib3 | 2.0.7 | Transport layer (via requests) | Provides `Retry` class if needed at transport level. Already installed. |
| Python stdlib | 3.12+ | `functools`, `time`, `logging`, `typing` | Decorator typing with `ParamSpec`, `TypeVar`. All verified available. |

### Supporting (Already Available)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unittest.mock | stdlib | Test mocking | All tests — `MagicMock`, `patch`, `PropertyMock`. Already used in 145 tests. |
| pytest | 9.0.2 | Test runner | Already configured. `testpaths = ["apps", "libs"]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure Python `@retry` | `tenacity` 9.1.2 | Tenacity is battle-tested but adds a dependency for a 30-line decorator. Overkill for the project's simple 3-retry pattern. |
| Pure Python `@retry` | `backoff` 2.2.1 | Similar to tenacity — well-designed but unnecessary dependency. |
| Pure Python `@retry` | `urllib3.Retry` on HTTPAdapter | Transport-level only — can't distinguish rate-limit 403 from auth 403. No application-level control. |
| `unittest.mock` | `responses` 0.26.0 | `responses` mocks at HTTP transport level. More realistic but adds dependency. `unittest.mock` is already established in the project. |

**No `pip install` needed.** All runtime dependencies are already satisfied.

## Architecture Patterns

### Recommended Project Structure

```
libs/buildcop-common/buildcop_common/
├── __init__.py          # Re-exports (add new exceptions + github)
├── config.py            # Existing — constants + get() helper
├── exceptions.py        # NEW — APIError, AuthenticationError, RateLimitError, TransientError
├── github.py            # NEW — create_github_session(), check_response(), @retry
├── http.py              # Existing — create_session(), TimeoutHTTPAdapter
├── log.py               # Existing — setup_logging()
├── models.py            # Existing — TypedDicts
└── py.typed             # Existing — PEP 561 marker

libs/buildcop-common/tests/
├── __init__.py
├── test_config.py       # Existing
├── test_exceptions.py   # NEW — exception hierarchy tests
├── test_github.py       # NEW — session factory, retry, rate-limit tests
├── test_http.py         # Existing
├── test_log.py          # Existing
└── test_models.py       # Existing
```

### Pattern 1: Typed Exception Hierarchy

**What:** All API failures raise domain-specific exceptions instead of generic `requests.HTTPError` or bare `Exception`.

**When to use:** Any code that makes GitHub API calls through the session factory.

**Example:**

```python
# exceptions.py
class APIError(Exception):
    """Base exception for GitHub API errors."""

    def __init__(self, message: str, status_code: int | None = None,
                 response: "requests.Response | None" = None) -> None:
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class AuthenticationError(APIError):
    """Raised when GitHub token is missing, empty, or invalid (401)."""
    pass


class RateLimitError(APIError):
    """Raised when GitHub rate limit is exceeded (429 or 403 with exhausted limit).

    Attributes:
        reset_at: UTC epoch timestamp when the rate limit resets.
        retry_after: Seconds until reset (convenience, computed from reset_at).
    """

    def __init__(self, message: str, *, reset_at: float,
                 status_code: int = 429,
                 response: "requests.Response | None" = None) -> None:
        self.reset_at = reset_at
        super().__init__(message, status_code=status_code, response=response)

    @property
    def retry_after(self) -> float:
        """Seconds until the rate limit resets (may be negative if already past)."""
        import time
        return max(0.0, self.reset_at - time.time())


class TransientError(APIError):
    """Raised on retriable server errors (5xx). The @retry decorator catches these."""
    pass
```

### Pattern 2: Response Checking (Status → Typed Exception)

**What:** A function that inspects a `requests.Response` and raises the appropriate typed exception.

**When to use:** After every API call, before processing the response body.

**Example:**

```python
# github.py
import logging
import requests

from buildcop_common.exceptions import (
    APIError, AuthenticationError, RateLimitError, TransientError,
)

logger = logging.getLogger(__name__)


def check_response(response: requests.Response) -> None:
    """Raise typed exception for non-2xx responses.

    Call after session.get()/post() instead of raise_for_status().

    Priority order:
    1. 401 → AuthenticationError
    2. 403 with X-RateLimit-Remaining: 0 → RateLimitError
    3. 429 → RateLimitError
    4. 5xx → TransientError (retriable)
    5. Other 4xx → APIError
    """
    if response.ok:
        return

    status = response.status_code

    if status == 401:
        raise AuthenticationError(
            f"GitHub authentication failed: {response.text[:200]}",
            status_code=status, response=response,
        )

    # Rate limit: 429 always, 403 when remaining=0
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
            status_code=status, response=response,
        )

    # All other errors (403 without rate-limit, 404, 422, etc.)
    raise APIError(
        f"GitHub API error (HTTP {status}): {response.text[:200]}",
        status_code=status, response=response,
    )
```

### Pattern 3: Retry Decorator

**What:** A `@retry` decorator that retries functions on transient failures with exponential backoff.

**When to use:** Wrap any function that calls the GitHub API and may encounter transient errors.

**Example:**

```python
# github.py (continued)
import functools
import time
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


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
                        delay = min(base_delay * (backoff_factor ** attempt),
                                    max_delay)
                        logger.warning(
                            "Retry %d/%d for %s: %s (sleeping %.1fs)",
                            attempt + 1, max_retries,
                            func.__name__, exc, delay,
                        )
                        time.sleep(delay)
            # All retries exhausted — re-raise last exception
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
```

### Pattern 4: GitHub Session Factory

**What:** Creates an authenticated `requests.Session` with GitHub-specific headers.

**When to use:** At application entry points before making any GitHub API calls.

**Example:**

```python
# github.py (continued)
from buildcop_common.config import get as config_get
from buildcop_common.http import create_session


def create_github_session(token: str | None = None) -> requests.Session:
    """Create an authenticated GitHub API session.

    Args:
        token: GitHub personal access token. If None, reads from
               GITHUB_TOKEN environment variable.

    Returns:
        requests.Session with auth headers and timeout defaults.

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

    session = create_session()  # Gets timeout defaults from http.py
    session.headers.update({
        "Authorization": f"token {token.strip()}",
        "Accept": "application/vnd.github.v3+json",
    })
    return session
```

### Pattern 5: Usage Pattern (How Phase 4 Will Consume This)

**What:** Shows how the retry + check_response + session integrate in calling code.

```python
# Example: How collector.py will look after Phase 4 migration
from buildcop_common.github import (
    create_github_session, check_response, retry,
)
from buildcop_common.exceptions import RateLimitError, APIError


@retry(max_retries=3)
def get_pinned_sha(session: requests.Session, submodule_path: str) -> str:
    url = f"{API_BASE}/repos/{PARENT_OWNER}/{PARENT_REPO}/contents/{submodule_path}"
    resp = session.get(url)
    check_response(resp)  # Raises typed exception on error
    data = resp.json()
    if data.get("type") != "submodule":
        raise ValueError(f"Not a submodule: {submodule_path}")
    return data["sha"]
```

### Anti-Patterns to Avoid

- **Catching bare `Exception`:** Always catch specific types (`APIError`, `TransientError`, `RateLimitError`). The whole point of typed exceptions is to enable this.
- **Retrying rate-limit errors:** 429/403 rate limits should propagate immediately. Retrying wastes time (can be 60+ minutes) and wastes retry budget.
- **Using `raise_for_status()` directly:** Replace with `check_response(resp)` which converts HTTP errors to the typed hierarchy. `raise_for_status()` raises `requests.HTTPError` which bypasses our exception types.
- **Double retry:** Don't use `urllib3.Retry` on the HTTPAdapter AND the `@retry` decorator for the same failure class. The decorator handles all retries at the application level.
- **Empty token silent pass:** Never let an empty string token through. The current code's `os.environ.get("GITHUB_TOKEN", "")` pattern sends `Authorization: token ` which GitHub treats as unauthenticated (60 req/hr limit).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exception classes | Complex metaclass or exception factory | Simple Python class hierarchy | 4 classes, each 5-15 lines. No framework needed. |
| Retry with backoff | External library (tenacity, backoff) | 30-line decorator with functools.wraps | Project has exactly one retry pattern. A library adds dependency for no benefit. |
| HTTP mocking in tests | `responses` library or `httpretty` | `unittest.mock.MagicMock` + `patch` | Already used in 145 tests. Consistent with project style. |
| Rate-limit header parsing | Complex middleware or session hook | Simple function checking `response.headers` | 3 headers to check, ~15 lines of code. No abstraction needed. |
| Session configuration | requests-toolbelt or custom Session subclass | `create_session()` + header update | Existing factory + 3 lines of header setup. |

**Key insight:** This phase adds ~150-200 lines of Python across 2 new modules. Every component is a straightforward Python class or function. No libraries needed beyond what's already installed.

## Common Pitfalls

### Pitfall 1: 403 ≠ Always Rate Limited
**What goes wrong:** Code treats all HTTP 403 as rate-limit errors. But 403 also means "forbidden" (bad OAuth scope, repo not accessible, secondary rate limit).
**Why it happens:** GitHub uses 403 for both rate-limit exceeded AND actual permission denied. Only the combination of 403 + `X-RateLimit-Remaining: 0` indicates a rate limit.
**How to avoid:** Check `X-RateLimit-Remaining` header. Only raise `RateLimitError` on 403 when `X-RateLimit-Remaining` is `"0"`. Other 403s become regular `APIError`.
**Warning signs:** Tests that mock 403 without headers incorrectly raise `RateLimitError`.

### Pitfall 2: `X-RateLimit-Reset` Is Epoch Seconds (String)
**What goes wrong:** The `X-RateLimit-Reset` header value is a string representation of a Unix epoch timestamp (e.g., `"1700000000"`). Code that treats it as seconds-from-now or fails to cast to float will compute wrong reset times.
**Why it happens:** HTTP headers are always strings. The header name doesn't hint at the format.
**How to avoid:** Always `float(response.headers.get("X-RateLimit-Reset", "0"))`. Store as `reset_at: float` (epoch). Compute `retry_after` as `max(0, reset_at - time.time())`.
**Warning signs:** `RateLimitError.retry_after` returns huge negative numbers or nonsensical values.

### Pitfall 3: Retry Decorator Swallows Non-Retriable Errors
**What goes wrong:** If the retry decorator catches too-broad exceptions (e.g., all `APIError`), it retries on 404 Not Found or 422 Validation Error, which will never succeed.
**Why it happens:** Lazy exception matching — catching the base `APIError` instead of only `TransientError`.
**How to avoid:** Retry ONLY on `TransientError`, `requests.ConnectionError`, and `requests.Timeout`. All other exceptions propagate immediately.
**Warning signs:** Functions take 3× longer when they encounter a 404 (retrying futilely).

### Pitfall 4: Token Validation Happens at Session Creation, Not at First Request
**What goes wrong:** `create_github_session()` validates the token is non-empty but can't validate it's actually authorized until a request is made. A revoked or invalid token passes session creation but fails on first use with 401.
**Why it happens:** Token validation requires a network call. Session creation is a local operation.
**How to avoid:** Accept this limitation. `create_github_session()` validates non-empty. `check_response()` catches 401 → `AuthenticationError` on first actual API call. Document this: "Session creation validates token presence. First API call validates token validity."
**Warning signs:** Tests mock token validation at session level but forget to test 401 handling.

### Pitfall 5: `@retry` Decorator Resets Delay Counter on Each Call
**What goes wrong:** If a function decorated with `@retry` is called in a loop (e.g., for 16 submodules), each call starts fresh with attempt=0. This is correct behavior but can mask cumulative rate-limit buildup — each call retries 3 times independently.
**Why it happens:** Stateless decorator by design.
**How to avoid:** This is actually correct. But be aware: 16 submodules × 3 retries each = up to 48 API calls for a failing endpoint. Combined with rate-limit detection via `check_response()`, rate limits will surface as `RateLimitError` before retries accumulate.
**Warning signs:** Long-running pipelines that retry extensively before finally hitting rate limit.

### Pitfall 6: Missing `__init__.py` Re-exports
**What goes wrong:** New modules are created but not re-exported from `buildcop_common/__init__.py`. Downstream code can't do `from buildcop_common import AuthenticationError`.
**Why it happens:** Forgetting to update `__init__.py` after adding new modules.
**How to avoid:** Verify `__init__.py` imports and re-exports all new public symbols. Test with `from buildcop_common import APIError, RateLimitError, AuthenticationError, TransientError, create_github_session, check_response, retry`.
**Warning signs:** `ImportError` in Phase 4 when migration code tries convenience imports.

## Code Examples

Verified patterns from the existing codebase and stdlib documentation:

### Exception with Typed Attributes (Python 3.12)

```python
class RateLimitError(APIError):
    """Rate limit exceeded. Includes reset timestamp for caller to act on."""

    def __init__(
        self,
        message: str,
        *,
        reset_at: float,
        status_code: int = 429,
        response: "requests.Response | None" = None,
    ) -> None:
        self.reset_at = reset_at
        super().__init__(message, status_code=status_code, response=response)
```

### Decorator with ParamSpec (Python 3.12 typing)

```python
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

def retry(max_retries: int = 3) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # ... retry logic ...
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Testing Pattern — Mocking requests.Response

```python
# Matching existing project test style (unittest.mock)
from unittest.mock import MagicMock, patch
import requests

def _make_response(status_code: int, headers: dict | None = None,
                   text: str = "") -> requests.Response:
    """Helper to create a mock Response with specific status and headers."""
    resp = requests.Response()
    resp.status_code = status_code
    resp._content = text.encode()
    if headers:
        resp.headers.update(headers)
    return resp

def test_check_response_rate_limit_429():
    resp = _make_response(429, headers={
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1700000000",
    })
    with pytest.raises(RateLimitError) as exc_info:
        check_response(resp)
    assert exc_info.value.reset_at == 1700000000.0
    assert exc_info.value.status_code == 429
```

### Testing Pattern — Retry Decorator Verification

```python
def test_retry_retries_on_transient_error():
    call_count = 0

    @retry(max_retries=2, base_delay=0)  # base_delay=0 for fast tests
    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientError("server error", status_code=500)
        return "success"

    result = flaky()
    assert result == "success"
    assert call_count == 3
```

### Testing Pattern — Session Factory Auth

```python
def test_create_github_session_with_explicit_token():
    session = create_github_session(token="ghp_test123")
    assert session.headers["Authorization"] == "token ghp_test123"
    assert session.headers["Accept"] == "application/vnd.github.v3+json"

def test_create_github_session_missing_token():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(AuthenticationError, match="GITHUB_TOKEN"):
            create_github_session()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.environ.get("GITHUB_TOKEN", "")` | `config.get("GITHUB_TOKEN", str)` with fail-fast | Phase 2 (config.py) | No more silent empty-string tokens |
| Bare `except (RequestException, KeyError, ValueError)` | Typed exceptions via `check_response()` | Phase 3 (this phase) | Callers can distinguish rate-limit vs auth vs transient |
| Manual retry loop in `collect_submodule()` | Reusable `@retry` decorator | Phase 3 (this phase) | Any function can be made retry-aware with one decorator |
| Hardcoded `time.sleep(0.5)` courtesy delays | Rate-limit-aware handling via headers | Phase 3 (this phase) | Phase 4 can remove blind sleeps, use actual limit data |
| `raise_for_status()` → `requests.HTTPError` | `check_response(resp)` → typed exceptions | Phase 3 (this phase) | All error handling uses domain-specific types |

**Deprecated/outdated:**
- `requests.HTTPError`: Still exists but should not be caught directly by consuming code after Phase 3. Use `APIError` hierarchy instead.
- Manual retry loops: The `collect_submodule()` pattern with `for attempt in range(retries)` is superseded by `@retry` decorator.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest libs/buildcop-common/tests/ -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | `create_github_session(token="x")` sets auth headers | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_create_github_session_explicit_token -x` | ❌ Wave 0 |
| API-01 | `create_github_session()` reads GITHUB_TOKEN env | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_create_github_session_from_env -x` | ❌ Wave 0 |
| API-01 | `create_github_session()` raises `AuthenticationError` on missing token | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_create_github_session_missing_token -x` | ❌ Wave 0 |
| API-01 | `create_github_session()` raises `AuthenticationError` on empty token | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_create_github_session_empty_token -x` | ❌ Wave 0 |
| API-02 | `@retry` retries on `TransientError` with backoff | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_retry_on_transient_error -x` | ❌ Wave 0 |
| API-02 | `@retry` retries on `requests.ConnectionError` | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_retry_on_connection_error -x` | ❌ Wave 0 |
| API-02 | `@retry` does NOT retry on `RateLimitError` | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_no_retry_on_rate_limit -x` | ❌ Wave 0 |
| API-02 | `@retry` raises last exception after exhausting retries | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_retry_exhaustion -x` | ❌ Wave 0 |
| API-03 | `check_response()` raises `RateLimitError` on 429 with reset_at | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_check_response_429_rate_limit -x` | ❌ Wave 0 |
| API-03 | `check_response()` raises `RateLimitError` on 403 with remaining=0 | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_check_response_403_rate_limit -x` | ❌ Wave 0 |
| API-03 | `check_response()` raises `APIError` on 403 without rate-limit headers | unit | `uv run pytest libs/buildcop-common/tests/test_github.py::test_check_response_403_not_rate_limit -x` | ❌ Wave 0 |
| API-04 | `APIError` hierarchy: all 4 classes importable, correct inheritance | unit | `uv run pytest libs/buildcop-common/tests/test_exceptions.py -x` | ❌ Wave 0 |
| API-04 | `RateLimitError` has `reset_at` and `retry_after` attributes | unit | `uv run pytest libs/buildcop-common/tests/test_exceptions.py::test_rate_limit_error_attributes -x` | ❌ Wave 0 |
| API-04 | `APIError` carries `status_code` and `response` | unit | `uv run pytest libs/buildcop-common/tests/test_exceptions.py::test_api_error_attributes -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest libs/buildcop-common/tests/ -x -q`
- **Per wave merge:** `uv run pytest -x -q` (full suite including apps)
- **Phase gate:** Full suite green (145 existing + new tests) before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `libs/buildcop-common/tests/test_exceptions.py` — covers API-04 (exception hierarchy)
- [ ] `libs/buildcop-common/tests/test_github.py` — covers API-01, API-02, API-03 (session, retry, rate-limit)
- [ ] No framework install needed — pytest 9.0.2 already configured
- [ ] No shared fixtures needed — test helpers are self-contained (e.g., `_make_response()`)

## Open Questions

1. **Should `retry` be a separate module (`retry.py`) or part of `github.py`?**
   - What we know: CONTEXT.md says "generic enough that Phase 4 can replace `collect_submodule()`'s manual retry loop." This suggests it should be reusable beyond GitHub.
   - What's unclear: Whether future phases (Azure DevOps stubs) will also need retry.
   - Recommendation: Keep in `github.py` for now. It's importable as `from buildcop_common.github import retry`. If Phase 5 needs it for Azure, extract then. YAGNI.

2. **Should `check_response()` be called automatically inside the session?**
   - What we know: A custom `Session` subclass or response hook could auto-call `check_response()`.
   - What's unclear: Whether all callers want automatic exception raising (some may want to check status manually).
   - Recommendation: Keep `check_response()` as an explicit function call. It's clearer and matches the existing `resp.raise_for_status()` pattern in the codebase. A session hook would be surprising.

3. **Should `TransientError` be included (4 classes) or omitted (3 classes)?**
   - What we know: CONTEXT.md says "Consider a TransientError(APIError) for 5xx so callers can distinguish retriable from permanent failures."
   - Recommendation: Include it. It costs 3 lines and lets `@retry` catch specifically `TransientError` instead of a status-code range. Makes the retry decorator's catch clause self-documenting.

## Sources

### Primary (HIGH confidence)
- **Existing codebase** — `http.py`, `config.py`, `collector.py`, `enrichment.py`, `staleness.py` (verified, read in full)
- **Python 3.12 stdlib** — `functools.wraps`, `typing.ParamSpec`, `typing.TypeVar` (verified via live Python REPL)
- **requests 2.31.0** — `Response` object, `HTTPError`, `Session.headers` (verified installed version)
- **urllib3 2.0.7** — `Retry` class parameters (verified via live `inspect.signature()`)

### Secondary (MEDIUM confidence)
- **GitHub REST API docs** — Rate limit headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`), 429 vs 403 behavior. Based on established GitHub API behavior (widely documented).

### Tertiary (LOW confidence)
- None — all findings verified against installed code or live REPL.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new dependencies, all verified installed
- Architecture: HIGH — patterns derived from existing codebase + stdlib capabilities
- Pitfalls: HIGH — derived from actual codebase analysis and GitHub API behavior
- Code examples: HIGH — all verified in Python 3.12 REPL

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain — Python stdlib + requests library)
