# Phase 6: Data Enrichment - Research

**Researched:** 2026-03-23
**Domain:** GitHub REST API — PR search, check runs, commit history, submodule pointer tracking
**Confidence:** HIGH

## Summary

Phase 6 enriches the collector's output JSON with four new data fields per submodule: open bot PR info, last merged bot PR, latest repo commit, and average delay between repo commits and pointer bumps. All data comes from the GitHub REST API using endpoints the project already knows how to call (authenticated `requests.Session` with `GITHUB_TOKEN`).

The key architectural insight is that **ENRICH-01 and ENRICH-02 can batch all 16 submodules into 2-3 Search API calls** (one for open PRs, one for merged PRs), then match results to submodules by title parsing. This avoids 32 individual search calls. ENRICH-03 is nearly free — the HEAD commit URL and date are already fetched by the existing `get_staleness()` code path but not captured. ENRICH-04 is the most API-intensive, requiring pointer bump history and SHA-to-date lookups, but 16×(1+5+5) ≈ 176 calls is well within the 5,000/hour rate limit.

**Primary recommendation:** Create a new `enrichment.py` module following the `staleness.py` pattern (enrich submodule dicts in-place), called from `collector.py` main() after `enrich_with_staleness()`. Use batch Search API calls for PRs and graceful per-submodule error handling with `None` defaults.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ENRICH-01 | Collector fetches open bot PR (from mssonicbld) for each submodule in sonic-buildimage | Search Issues API `is:pr is:open author:mssonicbld` + Check Runs API for CI status; batch-fetch all open PRs in 1 call, match by title |
| ENRICH-02 | Collector fetches last merged bot PR for each submodule | Search Issues API `is:pr is:merged author:mssonicbld sort:updated-desc`; batch-fetch in 1 call, match by title |
| ENRICH-03 | Collector fetches latest commit date from each submodule's own repo | Commits API `GET /repos/{owner}/{repo}/commits/{branch}` — returns `html_url` and `commit.committer.date`; already partially fetched by `get_staleness()` |
| ENRICH-04 | Collector computes average delay between repo commits and pointer bumps | Commits API with `path` filter for bump history + Contents API for submodule SHA at each bump + Commits API for SHA date; compute `mean(bump_date - commit_date)` |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.32+ | HTTP client for GitHub API | Already used by collector.py and staleness.py |
| json (stdlib) | — | Data serialization | Already used for data.json output |
| datetime (stdlib) | — | Date computation for age/delay | Already used throughout |
| statistics (stdlib) | — | Mean computation for avg delay | Already used in staleness.py for median |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0+ | Test framework | Already configured and in use (78 tests passing) |
| unittest.mock | stdlib | Mocking GitHub API responses | Same pattern as existing tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Search Issues API | Individual PR list per repo | Search batches 16 submodules into 1-2 calls vs 32+ calls |
| Check Runs API | Combined Status API | Check Runs covers GitHub Actions; Status API only covers legacy statuses. Use Check Runs, fall back to Status |
| Contents API for SHA lookup | Parse bot commit messages | Contents API is reliable; commit message parsing is fragile |

**Installation:** No new dependencies needed. All requirements already in `requirements.txt`.

## Architecture Patterns

### Recommended Project Structure
```
submodule-status/
├── scripts/
│   ├── collector.py     # Main entry; calls enrichment after staleness
│   ├── staleness.py     # Existing: cadence-aware classification
│   ├── enrichment.py    # NEW: bot PR, latest commit, avg delay enrichment
│   └── renderer.py      # Template rendering (no changes in this phase)
├── templates/
│   └── dashboard.html   # (no changes in this phase)
└── tests/
    ├── conftest.py      # Add new fixtures for PR/commit mock data
    ├── test_collector.py
    ├── test_staleness.py
    ├── test_enrichment.py  # NEW: tests for enrichment module
    └── test_renderer.py
```

### Pattern 1: Batch Search + Client-Side Match
**What:** Fetch ALL open bot PRs in 1 Search API call, then match each to its submodule by scanning PR titles for submodule names.
**When to use:** ENRICH-01 and ENRICH-02 — when you need per-submodule PR data but want to minimize API calls.
**Example:**
```python
# Source: GitHub Search Issues API documentation
def fetch_bot_prs(session, state="open"):
    """Batch-fetch bot PRs from sonic-buildimage.
    
    Args:
        state: "open" for ENRICH-01, "closed" (with is:merged) for ENRICH-02
    """
    query = f"repo:sonic-net/sonic-buildimage author:mssonicbld is:pr"
    if state == "open":
        query += " is:open"
    else:
        query += " is:merged"
    
    url = "https://api.github.com/search/issues"
    params = {"q": query, "sort": "updated", "order": "desc", "per_page": 50}
    resp = session.get(url, params=params)
    resp.raise_for_status()
    return resp.json()["items"]


def match_pr_to_submodule(pr, submodule_names):
    """Match a PR to a submodule by scanning the title for known names.
    
    Bot PR titles follow patterns like:
      "[submodule] Bump sonic-swss to ..."
      "Update submodule src/sonic-swss ..."
    """
    title = pr["title"].lower()
    for name in submodule_names:
        if name.lower() in title:
            return name
    return None
```

### Pattern 2: In-Place Enrichment (following staleness.py)
**What:** Each enrichment function takes the list of submodule dicts and modifies them in place, setting new fields to `None` on error.
**When to use:** All ENRICH requirements — keeps the pipeline pattern consistent.
**Example:**
```python
def enrich_with_details(session, submodules):
    """Main enrichment entry point — enrich submodule dicts in-place.
    
    Called from collector.py main() after enrich_with_staleness().
    """
    fetch_open_bot_prs(session, submodules)
    fetch_merged_bot_prs(session, submodules)
    fetch_latest_repo_commits(session, submodules)
    compute_avg_delay(session, submodules)
```

### Pattern 3: CI Status Aggregation
**What:** Query Check Runs API for a PR's head commit, aggregate to a single pass/fail/pending status.
**When to use:** ENRICH-01 — determining CI status for open bot PRs.
**Example:**
```python
def get_ci_status(session, owner, repo, sha):
    """Get aggregated CI status for a commit SHA.
    
    Returns: "pass", "fail", or "pending"
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}/check-runs"
    resp = session.get(url, headers={"Accept": "application/vnd.github+json"})
    resp.raise_for_status()
    
    check_runs = resp.json().get("check_runs", [])
    if not check_runs:
        # Fall back to combined status API
        return get_combined_status(session, owner, repo, sha)
    
    statuses = set()
    for run in check_runs:
        if run["status"] != "completed":
            statuses.add("pending")
        elif run["conclusion"] in ("success", "neutral", "skipped"):
            statuses.add("pass")
        else:  # failure, cancelled, timed_out, action_required
            statuses.add("fail")
    
    if "fail" in statuses:
        return "fail"
    if "pending" in statuses:
        return "pending"
    return "pass"
```

### Pattern 4: Average Delay Computation (ENRICH-04)
**What:** For each submodule, look at recent pointer bump commits in the parent repo, determine what submodule SHA each bump pointed to, compute the delay between that SHA's date and the bump date.
**When to use:** ENRICH-04
**Example:**
```python
def compute_avg_delay_for_submodule(session, owner, repo, submodule_path,
                                      sub_owner, sub_repo, num_bumps=5):
    """Compute average delay between repo commits and pointer bumps.
    
    Steps:
    1. Get last `num_bumps` commits in parent repo touching submodule path
    2. For each bump, get the submodule SHA via Contents API
    3. Get the date of that SHA from the submodule repo
    4. delay = bump_date - submodule_commit_date
    5. Return mean(delays) in days
    """
    # Step 1: Get bump history
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"path": submodule_path, "per_page": num_bumps}
    resp = session.get(url, params=params)
    resp.raise_for_status()
    bumps = resp.json()

    delays = []
    for bump in bumps:
        bump_date = parse_date(bump["commit"]["committer"]["date"])
        bump_sha = bump["sha"]

        # Step 2: Get submodule SHA at this bump
        contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{submodule_path}"
        contents_resp = session.get(contents_url, params={"ref": bump_sha})
        contents_resp.raise_for_status()
        sub_sha = contents_resp.json()["sha"]

        # Step 3: Get submodule commit date
        commit_url = f"https://api.github.com/repos/{sub_owner}/{sub_repo}/commits/{sub_sha}"
        commit_resp = session.get(commit_url)
        commit_resp.raise_for_status()
        commit_date = parse_date(commit_resp.json()["commit"]["committer"]["date"])

        # Step 4: Compute delay
        delay_days = (bump_date - commit_date).total_seconds() / 86400
        if delay_days >= 0:
            delays.append(delay_days)

        time.sleep(0.5)

    if delays:
        return round(statistics.mean(delays), 1)
    return None
```

### Data Model Extension

New fields added to each submodule dict:
```python
{
    # Existing fields...
    "name": "sonic-swss",
    "status": "ok",
    # ...

    # ENRICH-01: Open bot PR (null if none exists)
    "open_bot_pr": {
        "url": "https://github.com/sonic-net/sonic-buildimage/pull/123",
        "age_days": 5.2,
        "ci_status": "pass"  # "pass" | "fail" | "pending" | null
    },  # or null

    # ENRICH-02: Last merged bot PR (null if none found)
    "last_merged_bot_pr": {
        "url": "https://github.com/sonic-net/sonic-buildimage/pull/120",
        "merged_at": "2025-01-10T15:30:00Z"
    },  # or null

    # ENRICH-03: Latest commit in submodule's own repo
    "latest_repo_commit": {
        "url": "https://github.com/sonic-net/sonic-swss/commit/def456...",
        "date": "2025-02-19T08:00:00Z"
    },  # or null

    # ENRICH-04: Average delay in days (null if insufficient data)
    "avg_delay_days": 3.5  # or null
}
```

### Anti-Patterns to Avoid
- **Per-submodule search calls:** Don't make 16 separate Search API calls for PRs. Batch into 1-2 calls and match client-side. The Search API has a 30 req/min rate limit.
- **Parsing bot commit messages for SHAs:** The Contents API is reliable and documented. Commit message formats can change without notice.
- **Blocking on enrichment errors:** A failure to get PR info for one submodule must not prevent enrichment of the others. Use per-submodule try/except with `None` defaults.
- **Forgetting to handle unavailable submodules:** Submodules with `status='unavailable'` should get all enrichment fields set to `None`, same as the staleness.py pattern.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PR search by author | Custom commits/diff scanning | GitHub Search Issues API | Purpose-built, supports author/state/repo filtering |
| CI status aggregation | Parsing GitHub Actions logs | Check Runs API + Combined Status API | Returns structured status per check run |
| Submodule SHA at a point in time | Git log parsing or diff parsing | Contents API with `ref` parameter | Returns submodule type entries with SHA directly |
| Date parsing | Manual string splitting | `datetime.fromisoformat()` with Z→+00:00 cleanup | Already established pattern in codebase |

**Key insight:** The GitHub REST API has specific endpoints for every piece of data we need. The codebase already has the session/auth/retry patterns — enrichment is just new endpoint calls following the same patterns.

## Common Pitfalls

### Pitfall 1: Search API Rate Limits (30/min)
**What goes wrong:** Making individual search calls per submodule hits the 30 req/min search rate limit, causing 422 or 403 errors.
**Why it happens:** The Search API has separate, lower rate limits from the regular REST API (5,000/hour).
**How to avoid:** Batch all open PRs into 1 search call, all merged PRs into 1-2 calls. Match to submodules client-side by title.
**Warning signs:** HTTP 403 with "rate limit" or 422 with "validation failed" from search endpoints.

### Pitfall 2: Check Runs vs Commit Statuses
**What goes wrong:** Querying only the Combined Status API returns "pending" when CI is actually complete (or vice versa), because modern CI uses Check Runs (GitHub Actions) not the legacy Statuses API.
**Why it happens:** Two separate CI reporting mechanisms coexist in GitHub.
**How to avoid:** Query Check Runs API first. If `check_runs` is empty, fall back to Combined Status API. Only report "no CI" if both are empty.
**Warning signs:** CI status always shows "pending" for repos using GitHub Actions.

### Pitfall 3: PR Title Matching Ambiguity
**What goes wrong:** A PR title like "Update sonic-swss-common" incorrectly matches "sonic-swss" because `"sonic-swss" in title` is True.
**Why it happens:** Naive substring matching with submodule names that are prefixes of other names.
**How to avoid:** Sort submodule names longest-first when matching, so `sonic-swss-common` is checked before `sonic-swss`. Or use word-boundary matching (check that the character after the match is not alphanumeric/hyphen).
**Warning signs:** Multiple submodules matching the same PR, or the wrong submodule matching.

### Pitfall 4: Empty Pointer Bump History
**What goes wrong:** A submodule with no recent pointer bumps (inactive submodule) causes `avg_delay_days` computation to fail or produce misleading values.
**Why it happens:** Some submodules in BOT_MAINTAINED may have zero pointer bumps in recent history.
**How to avoid:** Return `None` for `avg_delay_days` when fewer than 2 pointer bumps are found. The UI should display "N/A" for this.
**Warning signs:** Division by zero, empty list means.

### Pitfall 5: Negative Delay Values
**What goes wrong:** Pointer bump date < submodule commit date, producing negative delay values.
**Why it happens:** Clock skew, rebased commits, or force-pushed branches can create commits with future dates that were bumped before the commit's authored date.
**How to avoid:** Filter out negative delays before computing the mean. If all delays are negative, return `None`.
**Warning signs:** Negative `avg_delay_days` values.

### Pitfall 6: Search API Returns PRs Without pull_request Field
**What goes wrong:** The Search Issues API returns both issues and PRs. While we filter with `is:pr`, the `pull_request` field in results is an object (not null) for PRs but may lack `html_url` for draft PRs.
**Why it happens:** Draft PRs and some edge cases.
**How to avoid:** Use `items[].html_url` directly (which is always the web URL for the PR/issue). The `items[].pull_request.html_url` is also available but `items[].html_url` is simpler and always present.
**Warning signs:** KeyError on `pull_request.html_url`.

## Code Examples

### Batch Open Bot PR Fetch (ENRICH-01)
```python
# Source: GitHub Search Issues API
PARENT_OWNER = "sonic-net"
PARENT_REPO = "sonic-buildimage"
BOT_AUTHOR = "mssonicbld"

def fetch_open_bot_prs(session, submodules):
    """Fetch open bot PRs and match to submodules in-place."""
    query = f"repo:{PARENT_OWNER}/{PARENT_REPO} author:{BOT_AUTHOR} is:pr is:open"
    url = f"{API_BASE}/search/issues"
    params = {"q": query, "per_page": 50}
    
    try:
        resp = session.get(url, params=params)
        resp.raise_for_status()
        prs = resp.json()["items"]
    except (requests.RequestException, KeyError):
        for sub in submodules:
            sub["open_bot_pr"] = None
        return
    
    # Build name→submodule lookup
    sub_by_name = {sub["name"]: sub for sub in submodules if sub["status"] == "ok"}
    # Sort names longest-first to avoid prefix matching issues
    sorted_names = sorted(sub_by_name.keys(), key=len, reverse=True)
    
    # Initialize all to None
    for sub in submodules:
        sub["open_bot_pr"] = None
    
    now = datetime.now(timezone.utc)
    for pr in prs:
        title = pr["title"].lower()
        for name in sorted_names:
            if name.lower() in title:
                created = datetime.fromisoformat(
                    pr["created_at"].replace("Z", "+00:00")
                )
                age_days = round((now - created).total_seconds() / 86400, 1)
                
                # Get CI status for the PR's head commit
                ci_status = get_ci_status_for_pr(session, pr["number"])
                
                sub_by_name[name]["open_bot_pr"] = {
                    "url": pr["html_url"],
                    "age_days": age_days,
                    "ci_status": ci_status,
                }
                break  # Each PR maps to at most one submodule
```

### Get CI Status for PR Head (ENRICH-01)
```python
# Source: GitHub Check Runs API + Pull Request API
def get_ci_status_for_pr(session, pr_number):
    """Get CI status for a PR by checking its head commit."""
    # First get the PR details to find head SHA
    pr_url = f"{API_BASE}/repos/{PARENT_OWNER}/{PARENT_REPO}/pulls/{pr_number}"
    try:
        resp = session.get(pr_url)
        resp.raise_for_status()
        head_sha = resp.json()["head"]["sha"]
    except (requests.RequestException, KeyError):
        return None
    
    # Then get check runs for that SHA
    checks_url = f"{API_BASE}/repos/{PARENT_OWNER}/{PARENT_REPO}/commits/{head_sha}/check-runs"
    try:
        resp = session.get(checks_url, headers={"Accept": "application/vnd.github+json"})
        resp.raise_for_status()
        check_runs = resp.json().get("check_runs", [])
    except (requests.RequestException, KeyError):
        return None
    
    if not check_runs:
        return None  # No CI configured
    
    has_failure = any(
        r["status"] == "completed" and r["conclusion"] not in ("success", "neutral", "skipped")
        for r in check_runs
    )
    has_pending = any(r["status"] != "completed" for r in check_runs)
    
    if has_failure:
        return "fail"
    if has_pending:
        return "pending"
    return "pass"
```

### Latest Repo Commit (ENRICH-03)
```python
# Source: GitHub Commits API
def fetch_latest_repo_commits(session, submodules):
    """Fetch latest commit info from each submodule's own repo."""
    for sub in submodules:
        if sub["status"] != "ok":
            sub["latest_repo_commit"] = None
            continue
        
        try:
            url = f"{API_BASE}/repos/{sub['owner']}/{sub['repo']}/commits/{sub['branch']}"
            resp = session.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            sub["latest_repo_commit"] = {
                "url": data["html_url"],
                "date": data["commit"]["committer"]["date"],
            }
        except (requests.RequestException, KeyError):
            sub["latest_repo_commit"] = None
        
        time.sleep(0.5)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Commit Statuses API only | Check Runs API (primary) + Statuses (fallback) | 2019 (GitHub Actions launch) | Must check Check Runs to see GitHub Actions CI results |
| Search API v2 (legacy) | Search Issues API v3 | Stable since 2013 | Use `/search/issues` with `is:pr` qualifier |

**Relevant GitHub API details:**
- Authenticated rate limit: 5,000 requests/hour (REST API)
- Search API rate limit: 30 requests/minute (authenticated)
- Contents API with `ref` parameter returns submodule entries with their SHA
- Search Issues API `is:merged` qualifier works for filtering merged PRs

## API Call Budget Analysis

| Requirement | Calls per Submodule | Total (16 subs) | Strategy |
|-------------|--------------------|--------------------|----------|
| ENRICH-01 (open PRs) | ~0.1 (batched) | 1-2 search + ~5-10 CI checks | Batch search, individual CI per open PR |
| ENRICH-02 (merged PRs) | ~0.1 (batched) | 1-2 search calls | Batch search, match client-side |
| ENRICH-03 (latest commit) | 1 | 16 | Per-submodule HEAD commit fetch |
| ENRICH-04 (avg delay) | 11 (1+5+5) | 176 | Per-submodule: bump history + contents + commit dates |
| **Total new calls** | — | **~200-205** | Within 5,000/hr budget |

**Current collector calls:** ~113 per run
**New total:** ~313-318 per run (6.4% of hourly budget)
**Time estimate at 0.5s delays:** ~100-150s additional (~2.5 min)

## Open Questions

1. **Bot PR title format**
   - What we know: mssonicbld creates PRs in sonic-buildimage for submodule updates
   - What's unclear: The exact title format used (e.g., "Update submodule src/sonic-swss" vs "[submodule] Bump sonic-swss")
   - Recommendation: During implementation, do a manual check of a few real PR titles from mssonicbld in sonic-buildimage to confirm the matching strategy. Title matching is the recommended approach; if titles are unpredictable, fall back to PR files API (`GET /repos/{owner}/{repo}/pulls/{number}/files`) at the cost of 1 extra call per PR.

2. **sonic-buildimage CI check count**
   - What we know: Check Runs API returns all checks for a commit
   - What's unclear: How many check runs sonic-buildimage PRs typically have — could be dozens (multi-platform builds)
   - Recommendation: The Check Runs API paginates at 100 per page. For status aggregation, the first page should be sufficient. If any failure exists on page 1, status is "fail". Only need to paginate if page 1 is all-success and `total_count > 100`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None (default discovery, `sys.path` set in conftest.py) |
| Quick run command | `cd submodule-status && python -m pytest tests/test_enrichment.py -x` |
| Full suite command | `cd submodule-status && python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENRICH-01 | Open bot PR fetch with URL, age, CI status | unit | `python -m pytest tests/test_enrichment.py::test_fetch_open_bot_prs -x` | ❌ Wave 0 |
| ENRICH-01 | CI status aggregation (pass/fail/pending) | unit | `python -m pytest tests/test_enrichment.py::test_get_ci_status -x` | ❌ Wave 0 |
| ENRICH-01 | No open PR → null | unit | `python -m pytest tests/test_enrichment.py::test_no_open_pr_returns_null -x` | ❌ Wave 0 |
| ENRICH-02 | Last merged bot PR fetch with URL and merge date | unit | `python -m pytest tests/test_enrichment.py::test_fetch_merged_bot_prs -x` | ❌ Wave 0 |
| ENRICH-02 | No merged PR → null | unit | `python -m pytest tests/test_enrichment.py::test_no_merged_pr_returns_null -x` | ❌ Wave 0 |
| ENRICH-03 | Latest repo commit URL and date | unit | `python -m pytest tests/test_enrichment.py::test_fetch_latest_repo_commit -x` | ❌ Wave 0 |
| ENRICH-04 | Average delay computation from bump history | unit | `python -m pytest tests/test_enrichment.py::test_compute_avg_delay -x` | ❌ Wave 0 |
| ENRICH-04 | Insufficient data → null | unit | `python -m pytest tests/test_enrichment.py::test_avg_delay_insufficient_data -x` | ❌ Wave 0 |
| ALL | Unavailable submodules get null enrichment fields | unit | `python -m pytest tests/test_enrichment.py::test_enrich_skips_unavailable -x` | ❌ Wave 0 |
| ALL | Full enrichment pipeline integration | unit | `python -m pytest tests/test_enrichment.py::test_enrich_with_details -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd submodule-status && python -m pytest tests/test_enrichment.py -x`
- **Per wave merge:** `cd submodule-status && python -m pytest tests/ -v`
- **Phase gate:** Full suite green (all 78 existing + new enrichment tests) before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_enrichment.py` — covers ENRICH-01 through ENRICH-04
- [ ] Fixtures in `tests/conftest.py` — mock Search API responses, Check Runs responses, Contents API responses, pointer bump commit responses

*(Existing test infrastructure — pytest, conftest.py with sys.path setup, mock patterns — is solid and reusable. Only new test file and fixtures needed.)*

## Sources

### Primary (HIGH confidence)
- **GitHub REST API docs (Search Issues):** `GET /search/issues` with qualifiers `repo:`, `author:`, `is:pr`, `is:open`, `is:merged` — documented behavior for PR search
- **GitHub REST API docs (Check Runs):** `GET /repos/{owner}/{repo}/commits/{ref}/check-runs` — returns check run status and conclusion
- **GitHub REST API docs (Commits):** `GET /repos/{owner}/{repo}/commits/{ref}` — returns `html_url`, `commit.committer.date`
- **GitHub REST API docs (Contents):** `GET /repos/{owner}/{repo}/contents/{path}?ref={sha}` — returns submodule type with pinned SHA
- **GitHub REST API docs (Rate Limits):** 5,000 REST/hour, 30 Search/minute for authenticated requests
- **Existing codebase:** `collector.py`, `staleness.py`, `test_collector.py`, `conftest.py` — verified patterns for session usage, error handling, in-place enrichment

### Secondary (MEDIUM confidence)
- **Bot PR title format:** Based on common mssonicbld patterns in open source SONiC repos. Should verify with a manual check during implementation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries, all APIs are documented and stable
- Architecture: HIGH — follows established project patterns (enrichment modules, in-place dict mutation, per-submodule error handling)
- Pitfalls: HIGH — API rate limits, Check Runs vs Statuses, and title matching are well-documented concerns
- API call budget: HIGH — calculated from documented endpoints and existing codebase patterns

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable — GitHub REST API v3 is mature)
