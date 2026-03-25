# Testing Patterns

**Analysis Date:** 2025-07-17

## Test Framework

**Runner:**
- pytest (version not pinned in `submodule-status/requirements.txt` — installed separately)
- Config: No `pytest.ini`, `pyproject.toml`, or `setup.cfg` — uses pytest defaults
- Path setup: `submodule-status/tests/conftest.py` adds `scripts/` to `sys.path`

**Assertion Library:**
- Built-in `assert` statements (pytest rewrites)
- No third-party assertion libraries

**Run Commands:**
```bash
cd submodule-status && python -m pytest tests/         # Run all tests
cd submodule-status && python -m pytest tests/ -v      # Verbose output
cd submodule-status && python -m pytest tests/ --tb=short  # Short tracebacks
```

## Test File Organization

**Location:**
- Separate `tests/` directory at `submodule-status/tests/`
- NOT co-located with source files

**Naming:**
- Test files: `test_{module_name}.py` — mirrors the source file name
- Test functions: `test_{function_name}_{scenario}` pattern

**Structure:**
```
submodule-status/
├── scripts/
│   ├── collector.py
│   ├── enrichment.py
│   ├── staleness.py
│   └── renderer.py
└── tests/
    ├── conftest.py          # Shared fixtures (415 lines)
    ├── test_collector.py    # Tests for collector.py (308 lines)
    ├── test_enrichment.py   # Tests for enrichment.py (443 lines)
    ├── test_staleness.py    # Tests for staleness.py (268 lines)
    └── test_renderer.py     # Tests for renderer.py (678 lines)
```

**Line counts:** Test code (2,112 lines) exceeds source code (946 lines) — roughly 2.2:1 ratio.

## Test Structure

**Suite Organization:**
```python
# Tests are flat functions grouped by section comments, NOT nested classes.
# Each section tests one function from the source module.

# ---------------------------------------------------------------------------
# parse_gitmodules tests
# ---------------------------------------------------------------------------

def test_parse_gitmodules_returns_bot_maintained_only(sample_gitmodules):
    """parse_gitmodules should return only bot-maintained sonic-net submodules."""
    result = parse_gitmodules(sample_gitmodules)
    assert len(result) == 10

def test_parse_gitmodules_extracts_path(sample_gitmodules):
    """All parsed submodule entries should have a path starting with src/."""
    result = parse_gitmodules(sample_gitmodules)
    for entry in result:
        assert entry["path"].startswith("src/"), f"{entry['name']} path={entry['path']}"

# ---------------------------------------------------------------------------
# get_pinned_sha tests
# ---------------------------------------------------------------------------

def test_get_pinned_sha(mock_contents_response):
    """get_pinned_sha should return the sha from a Contents API response."""
    ...
```

**Patterns:**
- Every test has a docstring explaining what is being tested and expected outcome
- Docstrings follow format: `"""function_name should do X when Y."""`
- Section separators: `# ---------------------------------------------------------------------------`
- No `setUp`/`tearDown` — use pytest fixtures
- No test classes — all flat functions

## Mocking

**Framework:** `unittest.mock` (stdlib) — `MagicMock`, `patch`

**Patterns:**

**1. Mock `requests.Session` for API calls (most common pattern):**
```python
from unittest.mock import MagicMock
import requests

def test_get_pinned_sha(mock_contents_response):
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = mock_contents_response
    session.get.return_value = resp

    sha = get_pinned_sha(session, "src/sonic-swss")
    assert sha == "abc123def4567890abc123def4567890abc123de"
    session.get.assert_called_once()
```

**2. Chain multiple API responses with `side_effect`:**
```python
def test_collect_submodule_success(mock_sleep):
    session = MagicMock(spec=requests.Session)

    resp_sha = MagicMock()
    resp_sha.json.return_value = {"type": "submodule", "sha": "abc123..."}

    resp_branch = MagicMock()
    resp_branch.json.return_value = {"default_branch": "master"}

    resp_compare = MagicMock()
    resp_compare.json.return_value = {"ahead_by": 5, ...}

    session.get.side_effect = [resp_sha, resp_branch, resp_compare]
    result = collect_submodule(session, submodule)
```

**3. Patch `time.sleep` to avoid delays:**
```python
@patch("collector.time.sleep")
def test_collect_submodule_success(mock_sleep):
    ...
```

**4. Patch module-level functions for integration tests:**
```python
@patch("staleness.time.sleep")
@patch("staleness.get_bump_dates")
def test_enrich_adds_staleness_fields(mock_get_dates, mock_sleep, sample_submodule_ok):
    base = datetime(2025, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    mock_get_dates.return_value = [base + timedelta(days=i) for i in range(10)]
    ...
```

**5. Patch `datetime` for time-dependent tests:**
```python
@patch("collector.datetime")
def test_get_staleness_uses_now_minus_first_ahead(mock_dt):
    from datetime import datetime, timezone
    fake_now = datetime(2025, 1, 25, 10, 0, 0, tzinfo=timezone.utc)
    mock_dt.now.return_value = fake_now
    mock_dt.fromisoformat = datetime.fromisoformat
    ...
```

**6. Simulate API failures with exception side_effect:**
```python
session.get.side_effect = requests.RequestException("API down")
```

**What to Mock:**
- `requests.Session.get()` — always mock, never make real HTTP calls
- `time.sleep()` — always patch to avoid test delays
- `datetime.now()` — patch when testing time-dependent calculations
- Internal functions — patch at module level for integration-style tests (e.g., `@patch("enrichment.get_ci_status_for_pr")`)

**What NOT to Mock:**
- Pure computation functions (`compute_cadence`, `compute_thresholds`, `classify`, `sort_submodules`, `compute_summary`, `format_relative_time`) — test directly with real inputs
- `parse_gitmodules()` — test with fixture string data

## Fixtures and Factories

**Test Data:**
All fixtures are defined in `submodule-status/tests/conftest.py` and organized by phase/module.

**Fixture categories:**

1. **Input data fixtures:**
   ```python
   @pytest.fixture
   def sample_gitmodules():
       """Multi-line .gitmodules INI string with 14 entries."""
       return """\
   [submodule "sonic-swss"]
   \tpath = src/sonic-swss
   \turl = https://github.com/sonic-net/sonic-swss
   ...
   """
   ```

2. **Mock API response fixtures:**
   ```python
   @pytest.fixture
   def mock_contents_response():
       """Mock GitHub Contents API response for a submodule entry."""
       return {
           "type": "submodule",
           "sha": "abc123def4567890abc123def4567890abc123de",
           ...
       }
   ```

3. **Submodule dict fixtures (status=ok and status=unavailable):**
   ```python
   @pytest.fixture
   def sample_submodule_ok():
       """A single submodule dict with status='ok'."""
       return {
           "name": "sonic-swss",
           "status": "ok",
           ...
       }

   @pytest.fixture
   def sample_submodule_unavailable():
       """A single submodule dict with status='unavailable'."""
       return {
           "name": "sonic-swss",
           "status": "unavailable",
           ...
       }
   ```

4. **Multi-submodule list fixture:**
   ```python
   @pytest.fixture
   def sample_submodule_list():
       """Two ok submodules + one unavailable for enrichment testing."""
       return [...]
   ```

**Fixture organization in `conftest.py`:**
- Fixtures are grouped by phase with section comments:
  - Phase 1: Collector fixtures (lines 1–146)
  - Phase 2: Staleness module fixtures (lines 148–222)
  - Phase 6: Enrichment module fixtures (lines 224–415)

**Helper functions in test files:**
- `submodule-status/tests/test_renderer.py` defines local helpers prefixed with `_`:
  ```python
  def _make_data(submodules=None, generated_at="2026-03-20T06:00:00Z"):
      """Helper: create a data dict matching the data.json schema."""

  def _write_data(tmp_path, data=None):
      """Helper: write data.json to tmp_path, return path."""

  def _render(tmp_path, data=None):
      """Helper: write data and render, return HTML string."""

  def _make_sub(name, staleness_status, days_behind, ...):
      """Minimal submodule dict for sort/summary testing."""
  ```

**Location:**
- Shared fixtures: `submodule-status/tests/conftest.py`
- Test-specific helpers: defined at top of respective test file (e.g., `_make_data` in `test_renderer.py`)

## Coverage

**Requirements:** None enforced — no coverage config or CI coverage gates detected.

**View Coverage:**
```bash
cd submodule-status && python -m pytest tests/ --cov=scripts --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Pure function tests: `compute_cadence()`, `compute_thresholds()`, `classify()`, `sort_submodules()`, `compute_summary()`, `format_relative_time()`, `parse_gitmodules()`, `build_compare_url()`, `match_pr_to_submodule()`
- Called with real data, no mocks needed
- Examples in: `submodule-status/tests/test_staleness.py` (lines 21–78, 157–176), `submodule-status/tests/test_renderer.py` (lines 210–287), `submodule-status/tests/test_enrichment.py` (lines 23–42)

**Integration Tests (with mocks):**
- Test enrichment pipelines with mocked HTTP layer
- Verify in-place mutation of submodule dicts
- Examples: `test_enrich_adds_staleness_fields`, `test_enrich_with_details`, `test_fetch_open_bot_prs`, `test_compute_avg_delay_for_submodule`
- Located in: `submodule-status/tests/test_staleness.py` (lines 232–268), `submodule-status/tests/test_enrichment.py` (lines 128–443)

**Rendering/Output Tests:**
- Write `data.json` to `tmp_path`, render HTML, assert on HTML content
- Use pytest's built-in `tmp_path` fixture for filesystem isolation
- Verify: file creation, HTML structure, column headers, links, dark mode CSS, expandable rows
- Located in: `submodule-status/tests/test_renderer.py` (84–678)

**E2E Tests:**
- Not used — no end-to-end tests that hit real APIs

## Common Patterns

**Async Testing:**
- Not applicable — codebase is synchronous (no async/await)

**Error Testing:**
```python
@patch("collector.time.sleep")
def test_collect_submodule_unavailable_after_retries(mock_sleep):
    """collect_submodule should return status=unavailable after exhausting retries."""
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = requests.RequestException("API down")

    submodule = { "name": "sonic-swss", ... }
    result = collect_submodule(session, submodule)
    assert result["status"] == "unavailable"
    assert result["error"] is not None
    assert isinstance(result["error"], str)
    assert result["pinned_sha"] is None
```

**Retry Testing:**
```python
@patch("collector.time.sleep")
def test_collect_submodule_retries_on_failure(mock_sleep):
    """collect_submodule should retry on failure and succeed on the 3rd try."""
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = [
        requests.RequestException("timeout"),
        requests.RequestException("timeout"),
        resp_sha, resp_branch, resp_compare,
    ]
    result = collect_submodule(session, submodule)
    assert result["status"] == "ok"
    assert session.get.call_count >= 3
```

**HTML Content Assertion Pattern:**
```python
def test_html_contains_table_headers(tmp_path):
    """HTML output contains all 8 table column headers."""
    html = _render(tmp_path)
    assert "<th>Submodule</th>" in html
    assert "<th>Status</th>" in html
```

**Position-based ordering tests:**
```python
def test_render_html_sorted_worst_first(tmp_path):
    """Rendered HTML table has submodules sorted: red → yellow → green → unavailable."""
    ...
    red_pos = html.index("sub-red")
    yellow_pos = html.index("sub-yellow")
    assert red_pos < yellow_pos < green_pos < unavail_pos
```

**Boundary/Edge Case Pattern:**
```python
def test_compute_cadence_fallback_zero_bumps():
    """Empty list → is_fallback=True, median_days=None, commit_count=0."""
    result = compute_cadence([])
    assert result["median_days"] is None

def test_compute_avg_delay_all_negative(mock_sleep):
    """All delays negative → returns None."""
    ...
    assert result is None
```

**Time-dependent Testing:**
```python
def test_format_relative_time_just_now():
    """Timestamps less than 60 seconds ago return 'just now'."""
    now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
    assert format_relative_time("2026-03-20T11:59:30Z", now=now) == "just now"
```
Functions accept an optional `now` parameter for testability (see `format_relative_time` in `submodule-status/scripts/renderer.py`).

---

*Testing analysis: 2025-07-17*
