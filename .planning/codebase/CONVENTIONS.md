# Coding Conventions

**Analysis Date:** 2025-07-17

## Naming Patterns

**Files:**
- Use lowercase `snake_case` for all Python source files: `collector.py`, `enrichment.py`, `staleness.py`, `renderer.py`
- Test files are prefixed with `test_`: `test_collector.py`, `test_enrichment.py`, `test_staleness.py`, `test_renderer.py`
- Shared test fixtures live in `conftest.py` (pytest convention)

**Functions:**
- Use `snake_case` for all functions: `parse_gitmodules()`, `get_pinned_sha()`, `compute_cadence()`
- Prefix getters with `get_`: `get_pinned_sha()`, `get_default_branch()`, `get_staleness()`, `get_bump_dates()`
- Prefix computation functions with `compute_`: `compute_cadence()`, `compute_thresholds()`, `compute_summary()`, `compute_avg_delay()`
- Prefix data-fetching enrichment functions with `fetch_`: `fetch_open_bot_prs()`, `fetch_merged_bot_prs()`, `fetch_latest_repo_commits()`
- Use `enrich_with_*` for top-level in-place enrichment entry points: `enrich_with_staleness()`, `enrich_with_details()`
- Use `build_*` for URL construction: `build_compare_url()`
- Use `match_*` for matching logic: `match_pr_to_submodule()`

**Variables:**
- Use `snake_case` for all variables: `commits_behind`, `days_behind`, `sub_by_name`
- Use `SCREAMING_SNAKE_CASE` for module-level constants: `REPO_OWNER`, `API_BASE`, `BOT_MAINTAINED`, `MIN_BUMPS_FOR_CADENCE`
- Prefix private sort keys with `_`: `_sort_key()`, `_TIER_ORDER`

**Types:**
- Use Python 3.10+ built-in generics for type hints: `list[dict]`, `dict[str, dict]`, `str | None`, `float | None`
- Do NOT use `typing.List`, `typing.Dict`, `typing.Optional` — use built-in syntax

## Code Style

**Formatting:**
- No explicit formatter config detected (no `pyproject.toml`, `setup.cfg`, `.flake8`, or `ruff.toml`)
- Follows PEP 8 implicitly: 4-space indentation, blank lines between functions, max ~100 char lines
- Two blank lines between top-level functions
- One blank line between class methods (not applicable — no classes used)

**Linting:**
- No linter config detected
- Code follows PEP 8 conventions consistently

**Line Length:**
- Approximately 88–100 characters, with occasional long lines for URLs
- Long strings (URLs, f-strings) are broken across lines using parenthetical continuation:
  ```python
  gitmodules_url = (
      f"{API_BASE}/repos/{REPO_OWNER}/{PARENT_REPO}/contents/.gitmodules"
  )
  ```

## Import Organization

**Order:**
1. Standard library imports (alphabetical): `base64`, `configparser`, `json`, `os`, `statistics`, `time`
2. Third-party imports: `import requests`, `from jinja2 import ...`
3. Local project imports: `from staleness import ...`, `from enrichment import ...`

**Style:**
- Use `import module` for top-level modules: `import requests`, `import json`
- Use `from module import name` for specific functions: `from staleness import enrich_with_staleness`
- One import per line (no multi-imports from stdlib)

**Path Aliases:**
- None — `sys.path.insert()` is used in `conftest.py` to add `scripts/` to the import path:
  ```python
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
  ```

## Error Handling

**Patterns:**

1. **Catch-and-return-default for API calls:** Functions that make HTTP requests catch broad exception tuples and return safe defaults:
   ```python
   except (requests.RequestException, KeyError, ValueError):
       return []
   ```
   Used in: `submodule-status/scripts/staleness.py` (`get_bump_dates`), `submodule-status/scripts/enrichment.py` (`get_ci_status_for_pr`, `compute_avg_delay_for_submodule`)

2. **Catch-and-set-None for enrichment functions:** In-place enrichment sets fields to `None` on error:
   ```python
   except (requests.RequestException, KeyError, ValueError):
       sub["latest_repo_commit"] = None
   ```
   Used in: `submodule-status/scripts/enrichment.py` (`fetch_latest_repo_commits`, `compute_avg_delay`), `submodule-status/scripts/staleness.py` (`enrich_with_staleness`)

3. **Retry with exponential backoff for critical paths:** `collect_submodule()` in `submodule-status/scripts/collector.py` retries up to 3 times with `time.sleep(2 ** attempt)` and returns a dict with `status='unavailable'` on exhaustion.

4. **`raise_for_status()` for non-recoverable API calls:** Used in `submodule-status/scripts/collector.py` for `get_pinned_sha()`, `get_default_branch()`, and `get_staleness()` — these let exceptions bubble up to the retry wrapper in `collect_submodule()`.

5. **`ValueError` for invalid data:** `get_pinned_sha()` raises `ValueError` when a path is not a submodule type.

**Exception tuple convention:** Always catch `(requests.RequestException, KeyError, ValueError)` as a group — this covers HTTP errors, missing JSON keys, and date parsing failures.

## Logging

**Framework:** `print()` statements only — no logging framework.

**Patterns:**
- Print summary after data collection: `print(f"Collected {len(results)} submodules: {ok_count} ok, {fail_count} unavailable")` in `submodule-status/scripts/collector.py`
- Print output path after rendering: `print(f"Dashboard rendered: ...")` in `submodule-status/scripts/renderer.py`
- No debug/trace logging — errors are silently caught and handled via return values

## Comments

**When to Comment:**
- Every module has a module-level docstring explaining purpose and exports
- Complex or non-obvious decisions get inline `# CRITICAL:` comments:
  ```python
  # CRITICAL: use .removesuffix() not .rstrip() — rstrip('.git') mangles
  # 'sonic-gnmi' to 'sonic-gnm'
  ```
- Section separators use `# --- Section Name ---` format in `submodule-status/scripts/enrichment.py` and `submodule-status/scripts/staleness.py`

**Docstrings:**
- All public functions have docstrings
- Use reStructuredText-style inline code with double backticks: `` ``field_name`` ``
- Docstrings explain the algorithm, edge cases, and return values
- Module docstrings include an `Exports:` section listing all public names (see `submodule-status/scripts/enrichment.py`, `submodule-status/scripts/staleness.py`)

**Format:**
```python
def compute_cadence(bump_dates: list[datetime]) -> dict:
    """Compute median inter-bump interval from sorted bump dates.

    Returns a dict with:
        median_days  — median interval in days (or None if fallback)
        commit_count — total number of bumps
        is_fallback  — True if too few bumps for reliable cadence

    If fewer than MIN_BUMPS_FOR_CADENCE bumps, returns fallback mode.
    Zero or near-zero medians are floored to MIN_MEDIAN_DAYS.
    """
```

## Function Design

**Size:** Functions are small and focused — typically 10–30 lines of logic. The largest is `collect_submodule()` at ~60 lines (including retry loop).

**Parameters:**
- `session: requests.Session` is always the first parameter for functions making HTTP calls
- Enrichment functions take `submodules: list[dict]` and mutate in-place
- Use keyword defaults for optional params: `retries: int = 3`, `num_bumps: int = 5`

**Return Values:**
- Pure computation functions return values: `dict`, `str`, `list[datetime]`, `float | None`
- Enrichment functions return `None` and mutate the input list in-place
- Error states are expressed via `None` values in dict fields, not via exceptions

## Module Design

**Exports:**
- No `__all__` definitions — all public functions are importable
- Module docstrings list exports explicitly for documentation purposes
- No classes — the codebase is entirely function-based

**Barrel Files:**
- None — each script is an independent module. `collector.py` imports from `staleness.py` and `enrichment.py` directly.

**Data Flow Pattern:**
- `collector.py` is the orchestrator: collects data → calls `enrich_with_staleness()` → calls `enrich_with_details()` → writes `data.json`
- `renderer.py` reads `data.json` → renders HTML via Jinja2
- Enrichment modules (`staleness.py`, `enrichment.py`) follow an "enrich in-place" pattern: they receive a `list[dict]` and mutate each dict by adding new keys

**Entry Points:**
- Scripts use `if __name__ == "__main__": main()` pattern
- `main()` functions read environment variables for configuration: `GITHUB_TOKEN`, `DATA_PATH`, `SITE_DIR`

## Data Structures

**Submodule dict:** The core data structure is a plain `dict` (not a dataclass or TypedDict). All modules pass around `list[dict]` where each dict has a consistent schema with keys like `name`, `path`, `url`, `owner`, `repo`, `status`, `error`, etc. New enrichment fields are added in-place.

**Status field convention:** `status` is either `"ok"` or `"unavailable"`. Enrichment functions check `sub["status"] == "ok"` before processing and set fields to `None` for unavailable submodules.

**Constants as module globals:** Constants like `REPO_OWNER`, `API_BASE`, `BOT_MAINTAINED` are defined at module level. No config files or environment-based constants (except `GITHUB_TOKEN` in `main()`).

---

*Convention analysis: 2025-07-17*
