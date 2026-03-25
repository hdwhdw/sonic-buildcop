"""Typed exceptions for GitHub API error handling.

Hierarchy:
    APIError (base)
    ├── AuthenticationError  — missing/invalid token, HTTP 401
    ├── RateLimitError       — HTTP 429 or 403 with exhausted limit
    └── TransientError       — HTTP 5xx, retriable server errors
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests


class APIError(Exception):
    """Base exception for GitHub API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: requests.Response | None = None,
    ) -> None:
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class AuthenticationError(APIError):
    """Raised when GitHub token is missing, empty, or invalid (401)."""


class RateLimitError(APIError):
    """Raised when GitHub rate limit is exceeded (429 or 403 with exhausted limit).

    Attributes:
        reset_at: UTC epoch timestamp when the rate limit resets.
        retry_after: Seconds until reset (convenience property).
    """

    def __init__(
        self,
        message: str,
        *,
        reset_at: float,
        status_code: int = 429,
        response: requests.Response | None = None,
    ) -> None:
        self.reset_at = reset_at
        super().__init__(message, status_code=status_code, response=response)

    @property
    def retry_after(self) -> float:
        """Seconds until the rate limit resets (clamped to >= 0)."""
        return max(0.0, self.reset_at - time.time())


class TransientError(APIError):
    """Raised on retriable server errors (5xx). The @retry decorator catches these."""
