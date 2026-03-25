"""Centralized configuration for SONiC build infrastructure tools."""

import os
from typing import TypeVar, overload

_T = TypeVar("_T")
_MISSING = object()

# ---------------------------------------------------------------------------
# Fixed constants — centralized from collector.py, staleness.py, enrichment.py
# ---------------------------------------------------------------------------

API_BASE: str = "https://api.github.com"
PARENT_OWNER: str = "sonic-net"
PARENT_REPO: str = "sonic-buildimage"
BOT_AUTHOR: str = "mssonicbld"

# Submodules actively maintained by the mssonicbld bot.
# Only these are tracked on the dashboard — unmaintained repos are noise.
BOT_MAINTAINED: frozenset[str] = frozenset({
    "sonic-swss",
    "sonic-sairedis",
    "sonic-platform-daemons",
    "sonic-utilities",
    "sonic-swss-common",
    "sonic-linux-kernel",
    "sonic-platform-common",
    "sonic-dash-ha",
    "dhcprelay",
    "sonic-gnmi",
    "sonic-ztp",
    "sonic-host-services",
    "sonic-dash-api",
    "sonic-mgmt-common",
    "sonic-bmp",
    "sonic-wpa-supplicant",
})

# Staleness computation thresholds
MIN_BUMPS_FOR_CADENCE: int = 5
MIN_MEDIAN_DAYS: float = 1.0
NUM_BUMPS: int = 30
MAX_YELLOW_DAYS: int = 30
MAX_RED_DAYS: int = 60


# ---------------------------------------------------------------------------
# Environment variable helper — typed access with fail-fast semantics
# ---------------------------------------------------------------------------


@overload
def get(name: str, cast: type[_T]) -> _T: ...


@overload
def get(name: str, cast: type[_T], default: _T) -> _T: ...


def get(name: str, cast: type[_T], default: _T | object = _MISSING) -> _T:
    """Read an environment variable, coerce to *cast*, with optional *default*.

    Calling conventions:
        get("TOKEN", str)       — required; raises ValueError if not set
        get("TIMEOUT", int, 30) — optional; returns 30 when not set

    Raises:
        ValueError: If the variable is required and not set, or if the raw
            value cannot be converted to *cast*.
    """
    raw = os.environ.get(name)
    if raw is None:
        if default is _MISSING:
            raise ValueError(
                f"Required environment variable {name!r} is not set"
            )
        return default  # type: ignore[return-value]
    try:
        return cast(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Environment variable {name!r} = {raw!r}: "
            f"cannot convert to {cast.__name__}"
        ) from exc
