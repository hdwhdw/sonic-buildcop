# Phase 2: Core Foundations - Research

**Researched:** 2026-03-25
**Domain:** Python stdlib configuration, TypedDict data models, structured logging, HTTP session management
**Confidence:** HIGH

## Summary

Phase 2 builds the foundation layer in `buildcop_common` — centralized configuration, typed data models, structured logging, and timeout-aware HTTP sessions. The key insight is that **no external dependencies are needed**: Python 3.12 stdlib provides everything (TypedDict with NotRequired, logging, os.environ). The only dependency is `requests` for the HTTP session factory, already installed in the workspace.

The existing codebase has 11 hardcoded constants across 3 files, 8 dict shapes used as untyped plain dicts, 3 print statements, 8 silent exception handlers, and 3 env var access points. Phase 2 defines the core modules that Phase 4 will migrate these to. This phase writes new code in `buildcop_common` — it does NOT modify the existing `submodule_status` code (that's Phase 4).

**Primary recommendation:** Keep it stdlib-only. TypedDict from `typing`, `logging` stdlib for structured logging, `os.environ` for config, `requests.adapters.HTTPAdapter` subclass for timeout defaults. Zero new pip dependencies in `buildcop-common` (except `requests` for the session factory).

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Formalize all 8 dict shapes as TypedDicts now (not deferred to Phase 4)
- One flat `SubmoduleInfo` TypedDict with ALL fields (base + staleness + enrichment), `Optional` for fields not yet populated at each pipeline stage
- `StalenessData` dissolves into `SubmoduleInfo` fields directly (`commits_behind`, `days_behind`)
- Small nested TypedDicts: `OpenBotPR`, `LastMergedBotPR`, `LatestRepoCommit`, `Cadence`, `Thresholds`
- TypedDict chosen over dataclass for dict-compatibility — existing code uses `sub["field"]` access throughout, Phase 4 migration becomes mechanical (add type annotations, swap imports)
- Human-readable log format for GitHub Actions console readability
- Default log level: INFO — matches current `print()` behavior (progress messages stay visible)
- Core provides a `setup_logging()` convenience function that apps call in their `main()`
- Consistent format across all apps: timestamp, level, module name, message
- Library modules use `logging.getLogger(__name__)` internally
- Fixed constants exposed as module attributes: `from buildcop_common.config import API_BASE, PARENT_OWNER, PARENT_REPO`
- Dynamic env-var-backed config via typed helper: `config.get("GITHUB_TOKEN", str)`, `config.get("TIMEOUT", int, 30)`
- Missing required env vars (called without default) raise `ValueError` immediately with clear message — fail fast, no silent failures
- Constants to centralize: `API_BASE`, `PARENT_OWNER`, `PARENT_REPO`, `BOT_AUTHOR`, `BOT_MAINTAINED` set, `MIN_BUMPS_FOR_CADENCE`, `NUM_BUMPS`, `MAX_YELLOW_DAYS`, `MAX_RED_DAYS`

### Claude's Discretion
- Exact TypedDict field names and Optional annotations
- `setup_logging()` function signature and configurable parameters
- Log format string details (timestamp format, separator style)
- Internal module organization within `buildcop_common` (flat vs subpackages)
- HTTP session factory placement (common vs github package)
- Whether to add `NotRequired` (Python 3.11+) vs `Optional` for progressive fields

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CFG-01 | Centralized constants module (`API_BASE`, `PARENT_OWNER`, `PARENT_REPO`) — single source of truth | `config.py` module with 11 constants as module-level attributes; verified 3 files with duplicated constants to consolidate |
| CFG-02 | Env-var-based config helper with typed defaults (`core.config.get()`) | `config.get()` function using `os.environ`, type coercion with `cast` parameter, `ValueError` on missing required vars |
| CFG-03 | Request timeout defaults on all HTTP sessions (30s connect, 60s read) | `TimeoutHTTPAdapter` subclass of `requests.adapters.HTTPAdapter`; verified pattern works on Python 3.12 + requests |
| LOG-01 | Structured logging via Python `logging` stdlib replacing all bare `print()` statements | `setup_logging()` configuring `logging.basicConfig()` with human-readable format; 3 print statements identified |
| LOG-02 | Caught exceptions logged at WARNING level (no more silent `None` returns) | `logging.getLogger(__name__)` in library modules + `logger.warning("...", exc_info=True)` pattern; 8 silent handlers identified |
| MDL-01 | Typed dataclasses for cross-module types (`SubmoduleInfo`, `StalenessResult`, `PRInfo`) | TypedDicts (per CONTEXT decision) with `NotRequired` for progressive fields; all 8 dict shapes mapped from source code |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `typing` | stdlib (3.12) | TypedDict, NotRequired | Built-in, no dependencies. Python 3.12 has full TypedDict + NotRequired support. |
| Python `logging` | stdlib (3.12) | Structured logging | CONTEXT decision: human-readable format, `getLogger(__name__)`. stdlib is sufficient — no need for structlog in this phase. |
| Python `os` | stdlib (3.12) | Environment variable access | `os.environ` for config.get() helper. No external config library needed. |
| `requests` | ≥2.31 (installed) | HTTP session with timeout | Already a workspace dependency. `HTTPAdapter` subclass for timeout defaults. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | ≥8.0 (installed) | Test runner | Testing all new core modules. Already configured in root pyproject.toml. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `logging` | `structlog` | structlog adds key-value structured logging but CONTEXT decided human-readable format. stdlib is simpler, zero-dependency, sufficient for this phase. structlog can be evaluated later. |
| `TypedDict` | `@dataclass` | CONTEXT explicitly chose TypedDict for dict-compatibility. Existing code uses `sub["field"]` access. Dataclass would require rewriting all bracket access to dot access in Phase 4. |
| `os.environ` | `pydantic-settings` | Over-engineered for 3 env vars. `os.environ.get()` + type cast is all that's needed. |
| `NotRequired` | `total=False` | `total=False` makes ALL fields optional. `NotRequired` is surgical — only progressive fields are optional. Better type safety. |

**Installation:**
```bash
# No new packages needed — all stdlib + already-installed requests
# Only need to add requests to buildcop-common's dependencies
uv add --package buildcop-common requests
```

**Version verification:** All libraries are Python stdlib (3.12) or already installed (`requests 2.32.3` in uv.lock). No new external packages.

## Architecture Patterns

### Recommended Module Structure
```
libs/buildcop-common/buildcop_common/
├── __init__.py      # re-exports: config, models, logging setup
├── config.py        # CFG-01, CFG-02: constants + get() helper
├── models.py        # MDL-01: all TypedDict definitions
├── log.py           # LOG-01, LOG-02: setup_logging() + format config
└── http.py          # CFG-03: TimeoutHTTPAdapter + create_session()
```

**Why flat modules, not subpackages:** The CONTEXT lists only 4 concerns (config, models, logging, http). Each maps to a single module file. Subpackages add import depth without value at this scale.

**Why `log.py` not `logging.py`:** Naming a module `logging.py` inside a package can cause confusion and edge-case import shadowing with the stdlib `logging` module. While Python 3 absolute imports usually handle this correctly, using `log.py` avoids the ambiguity entirely. This is standard practice in production Python codebases.

### Pattern 1: Flat TypedDict with NotRequired for Progressive Fields
**What:** One `SubmoduleInfo` TypedDict where base fields are required and pipeline-stage fields use `NotRequired[T | None]`.
**When to use:** When a dict accumulates fields through a pipeline and you need type safety at each stage.
**Why NotRequired over Optional:** `Optional[T]` (i.e., `T | None`) means the key MUST exist but value can be None. `NotRequired[T]` means the key itself may be absent. The existing pipeline creates dicts progressively — `parse_gitmodules` returns dicts WITHOUT staleness fields, then `collect_submodule` adds them. `NotRequired` correctly models this. After the full pipeline, all fields ARE present (with None for unavailable submodules).

### Pattern 2: Module-Level Constants with Import Access
**What:** Constants defined as `UPPER_SNAKE_CASE` module attributes in `config.py`, imported directly.
**When to use:** Fixed values that never change at runtime (API URLs, repo names, threshold values).
**Example access:** `from buildcop_common.config import API_BASE, PARENT_OWNER`

### Pattern 3: Typed Environment Variable Helper
**What:** `config.get(name, cast, default)` function that reads `os.environ`, casts to type, raises on missing required vars.
**When to use:** Runtime-configurable values from environment (tokens, paths, timeouts).
**Calling convention:** `get("TOKEN", str)` = required (raises ValueError), `get("TIMEOUT", int, 30)` = optional with default.

### Pattern 4: TimeoutHTTPAdapter for Default Timeouts
**What:** Subclass `requests.adapters.HTTPAdapter` that injects default timeout on every request.
**When to use:** CFG-03 requires 30s connect / 60s read on all HTTP sessions.
**Why adapter, not session wrapper:** The adapter pattern is the standard `requests` approach. It works with any code that uses the session, including code that doesn't pass explicit timeout. The `session.request()` override approach is more fragile.

### Pattern 5: setup_logging() Convenience Function
**What:** Single function that configures `logging.basicConfig()` with consistent format.
**When to use:** Called once in each app's `main()` entry point. Library modules use `logging.getLogger(__name__)` and don't call setup_logging().
**Why basicConfig:** It's idempotent (only configures the root logger once), simple, and handles the common case. No need for `dictConfig` or `fileConfig` complexity.

### Anti-Patterns to Avoid
- **Don't name module `logging.py`:** Shadows stdlib. Use `log.py` instead.
- **Don't use `total=False` on SubmoduleInfo:** Makes ALL fields optional, losing type safety on base fields (name, path, url, etc. should always be required).
- **Don't put business logic in models.py:** TypedDicts are pure type definitions. No methods, no validation logic, no imports beyond `typing`.
- **Don't import `typing.Optional`:** Python 3.12 uses `X | None` syntax. Project convention (from CONVENTIONS.md) is built-in generics.
- **Don't use `@dataclass`:** CONTEXT explicitly chose TypedDict for dict-compatibility.
- **Don't add `structlog` dependency:** CONTEXT decided human-readable format with stdlib logging. Keep it zero-dependency.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP timeout defaults | Manual `timeout=` on every request call | `TimeoutHTTPAdapter` subclass | Every caller would need to remember timeout; adapter guarantees it |
| Log formatting | Custom string formatting in print() | `logging.basicConfig(format=...)` | stdlib handles timestamps, levels, module names automatically |
| Type coercion for env vars | Inline `int(os.environ.get(...))` | `config.get()` with cast parameter | Consistent error messages, DRY, testable |
| TypedDict validation | Runtime isinstance checks | mypy / pyright static checking | TypedDicts are a static typing tool, not runtime validation |

**Key insight:** Phase 2 is almost entirely stdlib Python. The temptation is to add libraries (structlog, pydantic, etc.) but the CONTEXT decisions explicitly chose simple, dependency-free patterns. The value is in organization and type safety, not new dependencies.

## Common Pitfalls

### Pitfall 1: Naming Module `logging.py`
**What goes wrong:** Creating `buildcop_common/logging.py` can confuse developers (and some tools) about whether `import logging` refers to stdlib or local module.
**Why it happens:** Natural naming — the module IS about logging.
**How to avoid:** Name it `log.py`. The function is `setup_logging()` so imports read naturally: `from buildcop_common.log import setup_logging`.
**Warning signs:** `AttributeError: module 'logging' has no attribute 'getLogger'` or mypy complaining about logging types.

### Pitfall 2: TypedDict NotRequired vs Optional Confusion
**What goes wrong:** Using `Optional[T]` (= `T | None`) when you mean `NotRequired[T]`, or vice versa. `Optional` means "key exists, value might be None". `NotRequired` means "key might not exist".
**Why it happens:** Both relate to "optional" in natural language. The SubmoduleInfo pattern needs BOTH — progressive fields are `NotRequired[T | None]` (key may be absent, and when present, value may be None).
**How to avoid:** Use `NotRequired[T | None]` for fields added by later pipeline stages. Use plain `T | None` for fields that are always present but may be None (like `branch` from parse_gitmodules).
**Warning signs:** mypy errors about missing keys; `KeyError` at runtime when accessing a field before its pipeline stage runs.

### Pitfall 3: config.get() Sentinel vs None Default
**What goes wrong:** Using `None` as the default parameter makes it impossible to distinguish "no default provided" from "default is None". Both should raise ValueError for missing env vars when no default, but silently return None when default is None.
**Why it happens:** Python function signatures can't distinguish `get("X", str)` from `get("X", str, None)` if default parameter is `None`.
**How to avoid:** Use a sentinel object: `_MISSING = object()`. Check `if default is _MISSING` to know if a default was provided. This is the standard Python pattern (used by `dataclasses.field`, `dict.pop`, etc.).
**Warning signs:** `get("GITHUB_TOKEN", str)` silently returns None instead of raising ValueError.

### Pitfall 4: Circular Import Between config.py and models.py
**What goes wrong:** If `config.py` imports types from `models.py` and `models.py` imports constants from `config.py`, you get a circular import error at startup.
**Why it happens:** Natural desire to use model types in config signatures.
**How to avoid:** Keep `models.py` completely standalone — it imports ONLY from `typing`. Keep `config.py` standalone — it imports ONLY from `os`. No cross-module imports within `buildcop_common`. The `__init__.py` re-exports from both.
**Warning signs:** `ImportError: cannot import name 'X' from partially initialized module`.

### Pitfall 5: basicConfig() Only Works Once
**What goes wrong:** `logging.basicConfig()` is a no-op if the root logger already has handlers. If a test or library calls it before `setup_logging()`, the configuration is silently ignored.
**Why it happens:** `basicConfig()` is designed for simple single-call configuration.
**How to avoid:** In `setup_logging()`, use `force=True` parameter (Python 3.8+): `logging.basicConfig(..., force=True)`. This removes existing handlers first, ensuring our configuration always takes effect.
**Warning signs:** Log output uses default format instead of configured format; no timestamps in log lines.

### Pitfall 6: requests Dependency in buildcop-common
**What goes wrong:** Adding `requests` to `buildcop-common`'s dependencies for the HTTP session factory can create a tight coupling. Future packages that want config/models but not HTTP get an unnecessary dependency.
**Why it happens:** CFG-03 (timeout defaults) is assigned to Phase 2.
**How to avoid:** The HTTP session factory (`http.py`) uses `requests`, which is already an installed workspace dependency. Add `requests>=2.31` to `buildcop-common`'s `pyproject.toml` dependencies. This is acceptable — `requests` is lightweight and will be needed by any package doing HTTP. Alternatively, if a lighter dependency footprint is desired, the session factory could live in `buildcop-github` instead.
**Recommendation:** Put it in `buildcop_common` — both `buildcop-github` and `submodule-status` need HTTP sessions with timeout defaults. Centralizing avoids duplication.

## Code Examples

Verified patterns from Python 3.12 stdlib and requests library:

### config.py — Constants and get() Helper
```python
# Source: Python 3.12 stdlib os.environ + verified pattern
"""Centralized configuration for SONiC build infrastructure tools."""

import os
from typing import TypeVar, overload

_T = TypeVar("_T")
_MISSING = object()

# --- Fixed constants (single source of truth) ---

API_BASE = "https://api.github.com"
PARENT_OWNER = "sonic-net"
PARENT_REPO = "sonic-buildimage"
BOT_AUTHOR = "mssonicbld"
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

# Staleness thresholds
MIN_BUMPS_FOR_CADENCE = 5
NUM_BUMPS = 30
MAX_YELLOW_DAYS = 30
MAX_RED_DAYS = 60


# --- Environment variable helper ---

@overload
def get(name: str, cast: type[_T]) -> _T: ...
@overload
def get(name: str, cast: type[_T], default: _T) -> _T: ...

def get(name: str, cast: type[_T], default: _T | object = _MISSING) -> _T:
    """Read an environment variable with type coercion.

    Args:
        name: Environment variable name.
        cast: Type to coerce to (str, int, float, bool).
        default: Fallback if not set. Omit to require the variable.

    Returns:
        The coerced value.

    Raises:
        ValueError: If variable is missing and no default provided.
        ValueError: If type coercion fails.
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
```

### models.py — TypedDict Definitions
```python
# Source: Python 3.12 typing.TypedDict + typing.NotRequired
"""Typed data models for SONiC build infrastructure tools."""

from typing import NotRequired, TypedDict


class OpenBotPR(TypedDict):
    """An open bot-authored PR in the parent repo."""
    url: str
    age_days: float
    ci_status: str | None


class LastMergedBotPR(TypedDict):
    """The most recently merged bot PR for a submodule."""
    url: str
    merged_at: str | None


class LatestRepoCommit(TypedDict):
    """The latest commit on a submodule's tracked branch."""
    url: str
    date: str


class Cadence(TypedDict):
    """Computed bump cadence for a submodule."""
    median_days: float | None
    commit_count: int
    is_fallback: bool


class Thresholds(TypedDict):
    """Yellow/red staleness thresholds for a submodule."""
    yellow_days: float
    red_days: float
    is_fallback: bool


class SubmoduleInfo(TypedDict):
    """Full submodule data — fields accumulate through the pipeline.

    Base fields (from parse_gitmodules) are always required.
    Later-stage fields use NotRequired — they are absent until
    their pipeline stage runs, then present (possibly None for
    unavailable submodules).
    """
    # Base fields — always present after parse_gitmodules
    name: str
    path: str
    url: str
    owner: str
    repo: str
    branch: str | None

    # After collect_submodule
    pinned_sha: NotRequired[str | None]
    commits_behind: NotRequired[int | None]
    days_behind: NotRequired[float | None]
    compare_url: NotRequired[str | None]
    status: NotRequired[str]
    error: NotRequired[str | None]

    # After enrich_with_staleness
    staleness_status: NotRequired[str | None]
    median_days: NotRequired[float | None]
    commit_count_6m: NotRequired[int | None]
    thresholds: NotRequired[Thresholds | None]

    # After enrich_with_details
    open_bot_pr: NotRequired[OpenBotPR | None]
    last_merged_bot_pr: NotRequired[LastMergedBotPR | None]
    latest_repo_commit: NotRequired[LatestRepoCommit | None]
    avg_delay_days: NotRequired[float | None]
```

### log.py — Logging Setup
```python
# Source: Python 3.12 stdlib logging
"""Structured logging configuration for SONiC build infrastructure tools."""

import logging
import sys

DEFAULT_FORMAT = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    fmt: str = DEFAULT_FORMAT,
    datefmt: str = DEFAULT_DATEFMT,
) -> None:
    """Configure root logger with human-readable format.

    Call once in each app's main() entry point.
    Library modules use logging.getLogger(__name__) internally
    and do NOT call this function.

    Args:
        level: Logging level (default: INFO).
        fmt: Log format string.
        datefmt: Timestamp format string.
    """
    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
        stream=sys.stderr,
        force=True,  # Override any existing configuration
    )
```

### http.py — Timeout-Aware Session Factory
```python
# Source: requests library HTTPAdapter pattern (verified on requests 2.32)
"""HTTP session factory with default timeout configuration."""

import requests
from requests.adapters import HTTPAdapter


class TimeoutHTTPAdapter(HTTPAdapter):
    """HTTPAdapter that applies default timeout to all requests."""

    def __init__(
        self,
        *args,
        timeout: tuple[float, float] = (30.0, 60.0),
        **kwargs,
    ):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        """Send with default timeout if none specified."""
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def create_session(
    timeout: tuple[float, float] = (30.0, 60.0),
) -> requests.Session:
    """Create a requests.Session with default timeout on all requests.

    Args:
        timeout: (connect_timeout, read_timeout) in seconds.
                 Default: (30, 60) per CFG-03.

    Returns:
        Configured requests.Session.
    """
    session = requests.Session()
    adapter = TimeoutHTTPAdapter(timeout=timeout)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
```

### __init__.py — Re-exports
```python
"""Shared utilities for SONiC build infrastructure tools."""

__version__ = "0.1.0"

# Re-export key items for convenience
from buildcop_common.config import (
    API_BASE,
    PARENT_OWNER,
    PARENT_REPO,
    BOT_AUTHOR,
    BOT_MAINTAINED,
    get,
)
from buildcop_common.log import setup_logging
from buildcop_common.models import (
    SubmoduleInfo,
    OpenBotPR,
    LastMergedBotPR,
    LatestRepoCommit,
    Cadence,
    Thresholds,
)
from buildcop_common.http import create_session
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `typing.Optional[X]` | `X \| None` | Python 3.10 (PEP 604) | Use union syntax, not Optional import |
| `typing.List`, `typing.Dict` | `list`, `dict` | Python 3.9 (PEP 585) | Use built-in generics |
| `TypedDict` from `typing_extensions` | `TypedDict` from `typing` | Python 3.8 | No need for typing_extensions |
| `NotRequired` from `typing_extensions` | `NotRequired` from `typing` | Python 3.11 (PEP 655) | Native in stdlib |
| `total=False` for optional TypedDict fields | `NotRequired` per field | Python 3.11 (PEP 655) | Granular control over which fields are optional |
| `logging.basicConfig()` without `force` | `logging.basicConfig(force=True)` | Python 3.8 | Ensures config takes effect even if logging was already configured |

**Deprecated/outdated:**
- `typing.Optional`: Use `X | None` syntax (project convention from CONVENTIONS.md)
- `typing.List`, `typing.Dict`: Use built-in `list`, `dict` generics
- `typing_extensions`: Not needed for Python 3.12+
- `set` for `BOT_MAINTAINED`: Use `frozenset` — it's a constant that should never be mutated

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ≥8.0 (installed) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` at repo root |
| Quick run command | `uv run pytest libs/buildcop-common/tests/ -x -q` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CFG-01 | Constants accessible via import | unit | `uv run pytest libs/buildcop-common/tests/test_config.py::test_constants_accessible -x` | ❌ Wave 0 |
| CFG-01 | No duplicated constants (grep check) | unit | `uv run pytest libs/buildcop-common/tests/test_config.py::test_constants_values -x` | ❌ Wave 0 |
| CFG-02 | get() returns typed value from env | unit | `uv run pytest libs/buildcop-common/tests/test_config.py::test_get_with_default -x` | ❌ Wave 0 |
| CFG-02 | get() raises ValueError on missing required | unit | `uv run pytest libs/buildcop-common/tests/test_config.py::test_get_missing_required -x` | ❌ Wave 0 |
| CFG-02 | get() coerces int/float/bool | unit | `uv run pytest libs/buildcop-common/tests/test_config.py::test_get_type_coercion -x` | ❌ Wave 0 |
| CFG-03 | Session applies timeout defaults | unit | `uv run pytest libs/buildcop-common/tests/test_http.py::test_session_timeout -x` | ❌ Wave 0 |
| CFG-03 | Explicit timeout overrides default | unit | `uv run pytest libs/buildcop-common/tests/test_http.py::test_timeout_override -x` | ❌ Wave 0 |
| LOG-01 | setup_logging configures root logger | unit | `uv run pytest libs/buildcop-common/tests/test_log.py::test_setup_logging -x` | ❌ Wave 0 |
| LOG-01 | Log format includes timestamp/level/module | unit | `uv run pytest libs/buildcop-common/tests/test_log.py::test_log_format -x` | ❌ Wave 0 |
| LOG-02 | Library modules use getLogger(__name__) | unit | `uv run pytest libs/buildcop-common/tests/test_log.py::test_module_logger -x` | ❌ Wave 0 |
| MDL-01 | TypedDicts importable from core | unit | `uv run pytest libs/buildcop-common/tests/test_models.py::test_typeddict_import -x` | ❌ Wave 0 |
| MDL-01 | SubmoduleInfo supports progressive construction | unit | `uv run pytest libs/buildcop-common/tests/test_models.py::test_progressive_construction -x` | ❌ Wave 0 |
| MDL-01 | Nested TypedDicts (OpenBotPR, etc.) | unit | `uv run pytest libs/buildcop-common/tests/test_models.py::test_nested_typedicts -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest libs/buildcop-common/tests/ -x -q`
- **Per wave merge:** `uv run pytest -q` (full suite including existing 122 tests)
- **Phase gate:** Full suite green + mypy check before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `libs/buildcop-common/tests/` — test directory doesn't exist yet
- [ ] `libs/buildcop-common/tests/__init__.py` — package marker
- [ ] `libs/buildcop-common/tests/test_config.py` — covers CFG-01, CFG-02
- [ ] `libs/buildcop-common/tests/test_http.py` — covers CFG-03
- [ ] `libs/buildcop-common/tests/test_log.py` — covers LOG-01, LOG-02
- [ ] `libs/buildcop-common/tests/test_models.py` — covers MDL-01
- [ ] `requests` dependency addition to `buildcop-common/pyproject.toml`

## Open Questions

1. **BOT_MAINTAINED: set vs frozenset?**
   - What we know: Currently a `set` literal in `collector.py`. It's a constant that should never be mutated.
   - Recommendation: Use `frozenset` — it's immutable, signals intent, and is slightly more efficient for `in` checks. Type annotation: `frozenset[str]`.

2. **HTTP session factory placement: common vs github?**
   - What we know: CONTEXT lists this as Claude's discretion. `buildcop_common` currently has no dependencies. Adding `requests` is necessary for the session factory.
   - Recommendation: Put in `buildcop_common.http`. Both `buildcop-github` (Phase 3) and `submodule-status` (Phase 4) need timeout-aware sessions. Centralizing avoids duplication. `requests` is a lightweight, ubiquitous dependency.

3. **Should existing 122 tests still pass without modification?**
   - What we know: Phase 2 ONLY adds new modules to `buildcop_common`. It does NOT modify existing `submodule_status` code.
   - Recommendation: Yes — all 122 existing tests must pass unchanged. This is a regression check, not a modification.

## Sources

### Primary (HIGH confidence)
- Python 3.12 `typing` module — TypedDict, NotRequired, overload (verified locally: `python -c "from typing import TypedDict, NotRequired"`)
- Python 3.12 `logging` module — basicConfig with force parameter (verified locally)
- `requests` library HTTPAdapter pattern — verified locally with subclass and timeout injection
- Existing codebase — all 4 source files examined for constant values, dict shapes, env var patterns

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md` — prior research on structlog, ruff, mypy (Phase 2 uses simpler stdlib approach per CONTEXT decisions)
- `.planning/codebase/CONCERNS.md` — tech debt inventory (11 constants, 8 dict shapes, 3 prints, 8 silent handlers)
- `.planning/codebase/CONVENTIONS.md` — naming patterns, import style, error handling patterns

### Tertiary (LOW confidence)
- None — all claims verified against local Python 3.12 runtime and existing codebase.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all stdlib Python 3.12, verified locally
- Architecture: HIGH — module structure follows CONTEXT decisions, verified import patterns
- Pitfalls: HIGH — all pitfalls verified against Python 3.12 behavior and codebase analysis
- TypedDict design: HIGH — verified NotRequired + progressive construction pattern locally
- Code examples: HIGH — all examples tested in local Python 3.12 interpreter

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable — stdlib patterns don't change)
