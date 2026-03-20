# Phase 2: Staleness Model - Research

**Researched:** 2026-03-20
**Domain:** GitHub API commit history, statistical cadence computation, classification logic
**Confidence:** HIGH

## Summary

Phase 2 enriches the existing Phase 1 data pipeline with cadence-aware staleness thresholds per submodule. The core work is: (1) fetch 6 months of commit history from each submodule's repo via GitHub Commits API, (2) compute median inter-commit interval, (3) derive yellow/red thresholds from that median, and (4) classify each submodule as green/yellow/red by comparing its current days-behind and commits-behind against those thresholds.

The technical risk is low. The GitHub Commits API supports `since` parameter for date-range filtering, and Python's `statistics.median()` handles the math. The main complexity lies in edge cases (repos with <5 commits, zero-interval bursts, unavailable submodules) and cleanly integrating with the existing collector/renderer pipeline without breaking Phase 1's verified behavior.

**Primary recommendation:** Create `scripts/staleness.py` as a separate module imported by `collector.py`. The module exposes pure functions for commit history fetching, cadence computation, threshold derivation, and classification. Collector calls these before writing data.json, keeping the pipeline as a single `python scripts/collector.py` command.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Cadence source: each submodule repo's **own commit history** on its default branch (development activity)
- 6-month lookback window, all commits (not just merges) — sonic-net repos use squash-merge
- Use **median** inter-commit interval for cadence (not mean)
- **Both** days-behind AND commits-behind evaluated; worst determines color
- Fixed multipliers: **2× median = yellow, 4× median = red** for both signals
- Fallback for <5 commits in 6-month window: yellow at 30 days/10 commits, red at 60 days/20 commits
- GitHub Commits API with `since` parameter for lookback

### Claude's Discretion
- Whether staleness is a separate `staleness.py` module or integrated into collector
- Exact API pagination strategy for commit history (per_page, max pages)
- How to derive "expected commits in median window" for commit-based thresholds
- Whether to cache cadence data or recompute daily
- Template changes for rendering status badges (color mapping)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STALE-01 | Staleness thresholds auto-computed per submodule from historical update cadence | GitHub Commits API `since` parameter for 6-month history; `statistics.median()` for interval computation; threshold derivation from median × multiplier |
| STALE-02 | Frequently-updated submodules trigger yellow/red sooner than rarely-updated ones | Median interval naturally differentiates: 1-day median → yellow at 2 days; 8-day median → yellow at 16 days. Commit thresholds complement via worst-of rule |
| STALE-03 | Uses median inter-update interval, not mean, to resist outlier gaps | Python `statistics.median()` built-in; tested edge cases (single value, even/odd counts, all zeros) |
| STALE-04 | <5 updates fall back to default thresholds | Branch on `commit_count_6m < 5` → fixed thresholds (yellow: 30d/10c, red: 60d/20c) |
| STALE-05 | Green/yellow/red status badge per submodule | Classification function + `staleness_status` field in data.json + CSS badge in template |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12 | Runtime | Already used by Phase 1; workflow uses `python-version: '3.12'` |
| requests | (existing) | GitHub API calls | Already in requirements.txt; collector.py session reusable |
| statistics | stdlib | Median computation | Built-in, no install needed; `statistics.median()` |
| datetime | stdlib | Date parsing, interval computation | Already used in collector.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| jinja2 | (existing) | Template rendering | Already in requirements.txt for renderer.py |
| pytest | 9.0.2 | Testing | Already used; 23 tests passing |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| statistics.median | numpy.median | numpy is a heavy dependency for one function; stdlib sufficient |
| Manual pagination | github3.py library | Adds dependency for 20 API calls; requests + manual loop is simpler |

**Installation:** No new packages needed. Existing `requirements.txt` (jinja2, requests) covers everything.

## Architecture Patterns

### Recommended Project Structure
```
scripts/
├── collector.py      # Data pipeline entry point (modified to call staleness)
├── staleness.py      # NEW: cadence computation + classification module
└── renderer.py       # HTML rendering (unchanged except template consumes new fields)
templates/
└── dashboard.html    # Modified: add status badge column
tests/
├── conftest.py       # Extended: add commit history fixtures
├── test_collector.py # Existing tests (unchanged)
├── test_staleness.py # NEW: staleness module tests
└── test_renderer.py  # May need minor updates for new fields in data schema
```

### Pattern 1: Separate Module Imported by Collector
**What:** `staleness.py` exports pure functions; `collector.py` imports and calls them in `main()`.
**When to use:** This is the recommended pattern for Phase 2.
**Why:** Keeps the CI/CD workflow unchanged (single `python scripts/collector.py` command). Maintains separation of concerns. Staleness functions are independently testable. Collector already has the requests session and submodule data — passing them to staleness functions is natural.

**Integration flow:**
```python
# In collector.py main(), after collecting all submodule results:
from staleness import enrich_with_staleness

# Pass session for commit history API calls
enrich_with_staleness(session, results)  # Mutates results in-place

# Then write data.json as before (now includes staleness fields)
```

**Why not a separate CI step:** Reading data.json, enriching, writing back means double I/O and a more complex workflow. Importing is cleaner and keeps the pipeline atomic — if staleness fails, we don't write a partial data.json.

### Pattern 2: Pure Function Architecture for Staleness Module
**What:** Each concern is a separate pure function with clear inputs/outputs.
**Why:** Maximizes testability. Each function can be tested with mock data independently.

```python
# staleness.py — function signatures

def get_commit_dates(
    session: requests.Session,
    owner: str,
    repo: str,
    branch: str,
    since_days: int = 180,
) -> list[datetime]:
    """Fetch commit dates from last N days via GitHub Commits API."""

def compute_cadence(commit_dates: list[datetime]) -> dict:
    """Compute median inter-commit interval from sorted commit dates.
    Returns: {median_days: float, commit_count: int, is_fallback: bool}
    """

def compute_thresholds(cadence: dict) -> dict:
    """Derive yellow/red thresholds from cadence metrics.
    Returns: {yellow_days, red_days, yellow_commits, red_commits, is_fallback}
    """

def classify(
    days_behind: int,
    commits_behind: int,
    thresholds: dict,
) -> str:
    """Return 'green', 'yellow', or 'red' based on worst-of evaluation."""

def enrich_with_staleness(
    session: requests.Session,
    submodules: list[dict],
) -> None:
    """Enrich submodule dicts in-place with staleness fields."""
```

### Pattern 3: Defensive Processing for Unavailable Submodules
**What:** Skip staleness computation for submodules with `status='unavailable'`, setting staleness fields to null.
**Why:** Phase 1 already handles individual submodule failures gracefully (CICD-04). Phase 2 must maintain this contract.

```python
def enrich_with_staleness(session, submodules):
    for sub in submodules:
        if sub["status"] != "ok":
            sub["staleness_status"] = None
            sub["median_days"] = None
            sub["commit_count_6m"] = None
            sub["thresholds"] = None
            continue
        # ... normal staleness computation
```

### Anti-Patterns to Avoid
- **Modifying collector.py's core functions:** Don't change `get_staleness()`, `collect_submodule()`, etc. Only modify `main()` to call the staleness enrichment. This preserves Phase 1's verified behavior.
- **Fetching commit history inside the retry loop:** Commit history is independent of the pinned SHA comparison. Don't add API calls to `collect_submodule()`. Fetch history in a separate pass after all submodules are collected.
- **Caching commit history across runs:** Not needed. The daily cron runs once; 20-30 extra API calls take <15 seconds. Caching adds complexity (stale cache, cache invalidation) for negligible benefit.
- **Using `datetime.now()` for "6 months ago":** Use `datetime.now(timezone.utc)` — the existing codebase uses UTC throughout. Mixing naive/aware datetimes causes TypeErrors.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Median calculation | Custom sort + middle-element | `statistics.median()` | Handles even/odd, single value; raises clean error on empty |
| API pagination | Manual page counter | `response.links['next']` from requests | requests parses Link header automatically; avoids off-by-one |
| Date interval computation | String parsing | `(dt2 - dt1).total_seconds() / 86400` | datetime subtraction handles timezone-aware dates correctly |
| ISO 8601 parsing | Manual string splitting | `datetime.fromisoformat(s.replace('Z', '+00:00'))` | Already used in collector.py; handles the Z suffix |

**Key insight:** The entire staleness computation uses stdlib exclusively (statistics, datetime). No new dependencies. The only I/O-touching code is the commit history fetch, which reuses the existing requests session pattern from collector.py.

## Common Pitfalls

### Pitfall 1: Zero Median Interval
**What goes wrong:** If all commits in the 6-month window happen on the same day (or within hours), `statistics.median()` returns 0.0. Then `2 × 0 = 0`, making every submodule instantly red.
**Why it happens:** Burst imports, rebases, or automation that creates many commits at once.
**How to avoid:** Set a minimum floor for computed median: `max(computed_median, 1.0)`. One day is the smallest meaningful cadence for a daily dashboard.
**Warning signs:** `median_days < 1.0` in the output data.

### Pitfall 2: Empty Commit History
**What goes wrong:** A repo with 0 commits in the 6-month window produces an empty list. `statistics.median([])` raises `StatisticsError`. Even with 1-4 commits, the intervals list (N-1 elements) may be empty or very short.
**Why it happens:** Very slow repos, newly created repos, or repos that had all activity before the lookback window.
**How to avoid:** Check `len(commit_dates) < 5` BEFORE computing intervals. Route to fallback thresholds immediately.
**Warning signs:** `commit_count_6m < 5` in the output data (should have `is_fallback: true`).

### Pitfall 3: Naive vs Aware Datetimes
**What goes wrong:** Subtracting a naive datetime from an aware datetime raises `TypeError`. GitHub API returns UTC dates with 'Z' suffix. Python's `datetime.now()` returns naive.
**Why it happens:** Mixing timezone-aware (from API) and timezone-naive (from `datetime.now()`) values.
**How to avoid:** Always use `datetime.now(timezone.utc)` for the "since" cutoff. Parse API dates with `.replace('Z', '+00:00')` as collector.py already does.
**Warning signs:** `TypeError: can't subtract offset-naive and offset-aware datetimes`.

### Pitfall 4: Pagination Stopping Too Early
**What goes wrong:** Only fetching the first page of commits, missing older commits in the 6-month window.
**Why it happens:** Forgetting to check `response.links` for a `next` URL, or hardcoding `page=1`.
**How to avoid:** Loop while `'next' in response.links`. The `since` parameter ensures the API only returns commits in the window; pagination is just about fetching all of them.
**Warning signs:** `commit_count_6m` suspiciously capped at 100 for active repos.

### Pitfall 5: Commit Date Ordering Assumptions
**What goes wrong:** Assuming API returns commits in chronological order. GitHub returns commits in reverse chronological order (newest first) by default.
**Why it happens:** Not reading the API docs carefully.
**How to avoid:** Sort `commit_dates` before computing intervals: `commit_dates.sort()`. This ensures intervals are computed between adjacent commits in time order.
**Warning signs:** Negative intervals in the computed list.

### Pitfall 6: Modifying `status` Field Semantics
**What goes wrong:** Overloading the existing `status` field (currently "ok" or "unavailable") with staleness status, breaking renderer expectations.
**Why it happens:** Naming collision.
**How to avoid:** Use a distinct field name: `staleness_status` for the green/yellow/red classification. Keep `status` unchanged for data availability.
**Warning signs:** Renderer showing "red" where it should show "unavailable".

## Code Examples

### Example 1: Fetching Commit History with Pagination
```python
from datetime import datetime, timezone, timedelta

def get_commit_dates(
    session,
    owner: str,
    repo: str,
    branch: str,
    since_days: int = 180,
) -> list[datetime]:
    """Fetch commit dates from the last `since_days` days."""
    since = datetime.now(timezone.utc) - timedelta(days=since_days)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"sha": branch, "since": since_str, "per_page": 100}
    dates = []

    while url:
        resp = session.get(url, params=params)
        resp.raise_for_status()

        for commit in resp.json():
            date_str = commit["commit"]["committer"]["date"]
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            dates.append(dt)

        # Follow pagination; params only needed for first request
        url = resp.links.get("next", {}).get("url")
        params = None  # URL already includes params

    dates.sort()
    return dates
```

### Example 2: Cadence Computation with Fallback
```python
import statistics

FALLBACK_THRESHOLDS = {
    "yellow_days": 30,
    "red_days": 60,
    "yellow_commits": 10,
    "red_commits": 20,
    "is_fallback": True,
}

MIN_COMMITS_FOR_CADENCE = 5
MIN_MEDIAN_DAYS = 1.0  # Floor to prevent zero-threshold

def compute_cadence(commit_dates: list[datetime]) -> dict:
    """Compute cadence metrics from sorted commit dates."""
    count = len(commit_dates)

    if count < MIN_COMMITS_FOR_CADENCE:
        return {"median_days": None, "commit_count": count, "is_fallback": True}

    intervals = [
        (commit_dates[i + 1] - commit_dates[i]).total_seconds() / 86400
        for i in range(count - 1)
    ]
    median = max(statistics.median(intervals), MIN_MEDIAN_DAYS)

    return {"median_days": median, "commit_count": count, "is_fallback": False}
```

### Example 3: Threshold Derivation
```python
def compute_thresholds(cadence: dict) -> dict:
    """Derive yellow/red thresholds from cadence."""
    if cadence["is_fallback"]:
        return FALLBACK_THRESHOLDS

    m = cadence["median_days"]

    # Days thresholds: direct multiplier of median
    yellow_days = 2 * m
    red_days = 4 * m

    # Commit thresholds: "expected commits in one median window" = 1
    # So yellow = 2 × 1, red = 4 × 1
    # This is uniform but the worst-of rule with days provides differentiation
    yellow_commits = 2
    red_commits = 4

    return {
        "yellow_days": round(yellow_days, 1),
        "red_days": round(red_days, 1),
        "yellow_commits": yellow_commits,
        "red_commits": red_commits,
        "is_fallback": False,
    }
```

### Example 4: Classification (Worst-Of Rule)
```python
def classify(days_behind: int, commits_behind: int, thresholds: dict) -> str:
    """Classify as green/yellow/red — worst of days and commits wins."""
    def _level(value, yellow_thresh, red_thresh):
        if value > red_thresh:
            return 2  # red
        if value > yellow_thresh:
            return 1  # yellow
        return 0      # green

    day_level = _level(days_behind, thresholds["yellow_days"], thresholds["red_days"])
    commit_level = _level(
        commits_behind, thresholds["yellow_commits"], thresholds["red_commits"]
    )

    worst = max(day_level, commit_level)
    return ["green", "yellow", "red"][worst]
```

### Example 5: data.json Schema Extension
```json
{
  "generated_at": "2026-03-20T06:00:00+00:00",
  "submodules": [
    {
      "name": "sonic-swss",
      "path": "src/sonic-swss",
      "url": "https://github.com/sonic-net/sonic-swss",
      "pinned_sha": "abc123...",
      "branch": "master",
      "commits_behind": 42,
      "days_behind": 15,
      "compare_url": "https://github.com/sonic-net/sonic-swss/compare/abc123...master",
      "status": "ok",
      "error": null,
      "staleness_status": "red",
      "median_days": 1.2,
      "commit_count_6m": 148,
      "thresholds": {
        "yellow_days": 2.4,
        "red_days": 4.8,
        "yellow_commits": 2,
        "red_commits": 4,
        "is_fallback": false
      }
    },
    {
      "name": "sonic-dash-ha",
      "path": "src/sonic-dash-ha",
      "url": "https://github.com/sonic-net/sonic-dash-ha",
      "pinned_sha": null,
      "branch": null,
      "commits_behind": null,
      "days_behind": null,
      "compare_url": null,
      "status": "unavailable",
      "error": "API returned 403",
      "staleness_status": null,
      "median_days": null,
      "commit_count_6m": null,
      "thresholds": null
    }
  ]
}
```

### Example 6: CSS Status Badge (Template Change)
```html
<!-- In dashboard.html, add a Status column -->
<th>Status</th>

<!-- In the row loop -->
<td>
  {% if sub.staleness_status %}
    <span class="badge badge-{{ sub.staleness_status }}">{{ sub.staleness_status }}</span>
  {% else %}
    <span class="badge badge-unknown">—</span>
  {% endif %}
</td>
```

```css
/* Add to <style> block in dashboard.html */
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 600;
  text-transform: uppercase;
}
.badge-green { background-color: #28a745; color: #fff; }
.badge-yellow { background-color: #ffc107; color: #333; }
.badge-red { background-color: #dc3545; color: #fff; }
.badge-unknown { background-color: #6c757d; color: #fff; }
```

## Key Design Decisions (Discretion Areas)

### Decision 1: Separate `staleness.py` Module, Imported by Collector
**Recommendation:** Create `scripts/staleness.py` with pure functions. Modify `collector.py`'s `main()` to import and call `enrich_with_staleness()` after collecting all submodule results but before writing data.json.

**Rationale:**
- No new CI/CD workflow step needed (unchanged `python scripts/collector.py` command)
- Clean module boundary: staleness.py is independently testable
- Collector already has the session object; passing it avoids creating a second HTTP session
- Atomic pipeline: data.json is only written once, with all fields present

### Decision 2: Pagination — `per_page=100`, Follow Link Headers
**Recommendation:** Use `per_page=100` (maximum) and follow `response.links['next']` until exhausted. Set a safety cap of 10 pages (1000 commits) per repo.

**Rationale:**
- Most repos will need 1-3 pages for 6 months of history
- `since` parameter ensures server-side filtering; no wasted data transfer
- 10-page cap prevents runaway pagination on extraordinarily active repos
- Total estimated API calls: 10 repos × ~2 pages avg = ~20 calls

### Decision 3: "Expected Commits in Median Window" = 1
**Recommendation:** The expected number of commits in one median-interval period is exactly 1 (by definition of median interval). Therefore:
- Yellow commits threshold = 2 × 1 = **2**
- Red commits threshold = 4 × 1 = **4**

These are uniform across all repos. The differentiation comes from the day-based thresholds; commit thresholds serve as a complementary safety check that catches burst patterns.

**Mathematical proof:** If the median inter-commit interval is `m` days, then in a window of `2m` days (the yellow day threshold), you expect ~`2m/m = 2` commits. In `4m` days (red), ~4 commits. The math converges to 2 and 4 regardless of `m`.

**Why this works:** For a daily repo (m=1.2), 2 commits behind ≈ 2.4 days — consistent with 2×1.2. For a weekly repo (m=7), 2 commits behind ≈ 14 days — consistent with 2×7. The thresholds are inherently cadence-aligned.

### Decision 4: No Caching — Recompute Daily
**Recommendation:** Recompute cadence from scratch on every run. No caching.

**Rationale:**
- The cron runs once daily; 20-30 extra API calls add <15 seconds
- Well within the 1,000/hr rate limit (~54-64 total calls per run)
- Caching requires storage, invalidation logic, and stale data handling
- Fresh computation ensures thresholds adapt to recent activity changes

### Decision 5: Minimum Median Floor of 1 Day
**Recommendation:** After computing the median, apply `max(median, 1.0)` to prevent zero thresholds.

**Rationale:** If all commits are on the same day, median = 0.0. Without a floor, every submodule would be instantly red (0 × 2 = 0). A 1-day minimum is the smallest meaningful cadence for a dashboard that updates daily.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `datetime.fromisoformat()` rejects 'Z' | Python 3.11+ fromisoformat handles 'Z' | Python 3.11 | Code uses `.replace('Z', '+00:00')` for 3.12 compat; both work |
| `str.rstrip('.git')` for URL cleanup | `str.removesuffix('.git')` | Python 3.9 | Already adopted in collector.py; prevents 'sonic-gnmi' mangling |
| GitHub API v3 (REST) | v3 still current for commits endpoint | Stable | GraphQL alternative exists but overkill for simple commit listing |

**Not deprecated:**
- GitHub REST API v3 Commits endpoint: stable, well-documented, supports pagination and `since` filtering
- `statistics.median()`: stable since Python 3.4, no changes

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none — tests discovered by convention |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STALE-01 | Thresholds auto-computed from commit history | unit | `python -m pytest tests/test_staleness.py::test_compute_thresholds_from_cadence -x` | ❌ Wave 0 |
| STALE-02 | Frequent repos get tighter thresholds | unit | `python -m pytest tests/test_staleness.py::test_frequent_repo_tighter_thresholds -x` | ❌ Wave 0 |
| STALE-03 | Median used, not mean | unit | `python -m pytest tests/test_staleness.py::test_median_resists_outliers -x` | ❌ Wave 0 |
| STALE-04 | Fallback for <5 commits | unit | `python -m pytest tests/test_staleness.py::test_fallback_thresholds -x` | ❌ Wave 0 |
| STALE-05 | Green/yellow/red badge displayed | unit+template | `python -m pytest tests/test_staleness.py::test_classify_green_yellow_red -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q` (~0.2s)
- **Per wave merge:** `python -m pytest tests/ -v` (~0.3s)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_staleness.py` — covers STALE-01 through STALE-05 (cadence computation, thresholds, classification, fallback, edge cases)
- [ ] `tests/conftest.py` — extend with commit history fixtures (mock API responses for commits endpoint)
- [ ] Framework install: none needed — pytest 9.0.2 already available

## Open Questions

1. **Commit-based thresholds at exactly 2/4**
   - What we know: Mathematically, "expected commits in one median window" = 1, giving universal thresholds of 2 and 4
   - What's unclear: Whether the user expects per-repo variation in commit thresholds. The current derivation gives the same 2/4 for all repos.
   - Recommendation: Proceed with 2/4 as derived. The worst-of rule with variable day thresholds still satisfies STALE-02. If more granularity is wanted later, commit thresholds could be scaled by commit rate, but that's equivalent to the day-based check.

2. **Very active repos with >1000 commits in 6 months**
   - What we know: The 10-page safety cap (1000 commits) should cover all sonic-net repos. sonic-swss is the most active and likely has 150-300 commits in 6 months.
   - What's unclear: Exact commit counts for all 10 target repos at any given time.
   - Recommendation: Cap at 10 pages but log a warning if the cap is hit. The median computation is still valid with 1000 commits — we just miss the oldest ones in the window.

## Sources

### Primary (HIGH confidence)
- **Python statistics module** — stdlib documentation; `statistics.median()` behavior verified locally with edge cases (empty, single, all-zeros)
- **Python datetime module** — timezone-aware arithmetic verified locally; `fromisoformat` with Z suffix tested
- **requests.Response.links** — verified locally that it correctly parses GitHub Link headers for pagination
- **Existing codebase** — collector.py, renderer.py, conftest.py, test files all read and analyzed

### Secondary (MEDIUM confidence)
- **GitHub REST API Commits endpoint** — `GET /repos/{owner}/{repo}/commits` with `since`, `sha`, `per_page` parameters. Pagination via Link headers. Based on training data (stable API, no known changes) — format verified against existing collector.py patterns that already use the same API successfully.

### Tertiary (LOW confidence)
- **sonic-net repo commit volumes** — estimated at 10-300 commits per 6 months based on project descriptions in CONTEXT.md. Actual volumes should be validated on first run.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all stdlib + existing packages
- Architecture: HIGH — follows existing patterns in collector.py; pure function module design is standard Python
- Pitfalls: HIGH — edge cases identified and verified locally (zero median, empty lists, datetime mixing)
- GitHub API: MEDIUM — `since` parameter and pagination well-known, but exact behavior verified only via training data and existing codebase patterns
- Commit volumes: LOW — estimated, not measured against live repos

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable domain — stdlib, REST API)
