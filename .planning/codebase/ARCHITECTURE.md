# Architecture

**Analysis Date:** 2026-03-24

## Pattern Overview

**Overall:** Pipeline Architecture — a sequential data pipeline that collects, enriches, and renders submodule staleness data from the GitHub API into a static HTML dashboard.

**Key Characteristics:**
- **Pipeline stages:** Collect → Enrich (staleness) → Enrich (details) → Render
- **In-place mutation:** Enrichment stages mutate submodule dicts in-place rather than returning new data
- **GitHub API as sole data source:** All data comes from the GitHub REST API v3; no database or persistent storage
- **Static output:** Final artifact is a `data.json` file rendered into a static `index.html` via Jinja2
- **CI-driven execution:** Runs on a schedule (every 4 hours) via GitHub Actions, deployed to GitHub Pages

## Layers

**Data Collection Layer:**
- Purpose: Fetch `.gitmodules` from the parent repo, parse submodule definitions, and collect per-submodule staleness metrics (commits behind, days behind) from GitHub API
- Location: `submodule-status/scripts/collector.py`
- Contains: `.gitmodules` parsing, GitHub API calls for pinned SHAs, branch resolution, compare API for staleness, retry logic
- Depends on: `staleness.py`, `enrichment.py`, `requests` library, GitHub REST API
- Used by: GitHub Actions workflow (`main()` entry point)

**Staleness Classification Layer:**
- Purpose: Compute per-submodule cadence from historical pointer bump frequency, derive adaptive yellow/red thresholds, and classify each submodule as green/yellow/red
- Location: `submodule-status/scripts/staleness.py`
- Contains: Bump date fetching, median cadence computation, threshold derivation (2×/4× median with caps), classification logic
- Depends on: `requests` library, GitHub REST API (commits endpoint)
- Used by: `collector.py` via `enrich_with_staleness()`

**Detail Enrichment Layer:**
- Purpose: Fetch supplementary data — open/merged bot PRs, CI status, latest repo commits, average update delay — and attach to submodule dicts
- Location: `submodule-status/scripts/enrichment.py`
- Contains: GitHub Search Issues API queries, Check Runs API aggregation, commit fetching, delay computation
- Depends on: `requests` library, GitHub REST API (search, check-runs, commits, contents endpoints)
- Used by: `collector.py` via `enrich_with_details()`

**Rendering Layer:**
- Purpose: Read `data.json`, sort submodules by severity, compute summary stats, render Jinja2 template to static HTML
- Location: `submodule-status/scripts/renderer.py`
- Contains: Sort logic, summary computation, relative time formatting, Jinja2 template rendering, output writing
- Depends on: `jinja2` library, `submodule-status/templates/dashboard.html`
- Used by: GitHub Actions workflow (`main()` entry point)

**Presentation Layer:**
- Purpose: HTML/CSS/JS template for the dashboard UI with dark mode support, expandable detail rows, and live timestamp updates
- Location: `submodule-status/templates/dashboard.html`
- Contains: Jinja2 template with inline CSS and JavaScript
- Depends on: Data context passed from `renderer.py`
- Used by: `renderer.py` via Jinja2 `FileSystemLoader`

**CI/CD Layer:**
- Purpose: Orchestrate the full pipeline — install deps, run collector, run renderer, deploy to GitHub Pages
- Location: `.github/workflows/update-dashboard.yml`
- Contains: GitHub Actions workflow with scheduled and manual triggers
- Depends on: All script layers, GitHub Pages infrastructure
- Used by: GitHub (triggered on push to `main`, every 4 hours via cron, or manual dispatch)

## Data Flow

**Main Pipeline (Collector → Enrichment → Render → Deploy):**

1. GitHub Actions triggers workflow (cron / push / manual)
2. `collector.py:main()` fetches `.gitmodules` from `sonic-net/sonic-buildimage` via GitHub Contents API
3. `parse_gitmodules()` filters to bot-maintained sonic-net submodules (16 repos in `BOT_MAINTAINED` set)
4. For each submodule, `collect_submodule()` calls:
   - `get_pinned_sha()` — GitHub Contents API for the submodule entry SHA
   - `get_default_branch()` — GitHub Repos API (if no explicit branch in `.gitmodules`)
   - `get_staleness()` — GitHub Compare API for commits-behind and days-behind
5. `enrich_with_staleness()` from `staleness.py` mutates each submodule dict in-place:
   - `get_bump_dates()` — fetches last 30 pointer bump commits from parent repo
   - `compute_cadence()` — computes median inter-bump interval
   - `compute_thresholds()` — derives yellow (2× median) and red (4× median) thresholds
   - `classify()` — assigns green/yellow/red based on days behind vs thresholds
6. `enrich_with_details()` from `enrichment.py` mutates each submodule dict in-place:
   - `fetch_open_bot_prs()` — batch search for open bot PRs + CI status per PR
   - `fetch_merged_bot_prs()` — batch search for last merged bot PR per submodule
   - `fetch_latest_repo_commits()` — fetch HEAD commit from each submodule's repo
   - `compute_avg_delay()` — compute mean days between repo commit and parent pointer bump
7. Collector writes `data.json` with `generated_at` timestamp and `submodules` array
8. `renderer.py:main()` reads `data.json`, sorts by severity, renders `dashboard.html` template
9. Output: `site/index.html` + `site/.nojekyll`
10. GitHub Actions deploys `site/` to GitHub Pages

**State Management:**
- No persistent state between runs — each execution is a fresh pipeline from API to HTML
- Intermediate state is `data.json` written to disk between collector and renderer steps
- Submodule dicts are mutated in-place as they flow through enrichment stages

## Key Abstractions

**Submodule Dict:**
- Purpose: Central data object representing one tracked submodule and all its metrics
- Examples: Created in `submodule-status/scripts/collector.py:collect_submodule()`, enriched in `submodule-status/scripts/staleness.py:enrich_with_staleness()` and `submodule-status/scripts/enrichment.py:enrich_with_details()`
- Pattern: Plain Python dict passed through pipeline stages and mutated in-place. Fields accumulate as each stage adds its data:
  - After collection: `name`, `path`, `url`, `owner`, `repo`, `pinned_sha`, `branch`, `commits_behind`, `days_behind`, `compare_url`, `status`, `error`
  - After staleness: `staleness_status`, `median_days`, `commit_count_6m`, `thresholds`
  - After enrichment: `open_bot_pr`, `last_merged_bot_pr`, `latest_repo_commit`, `avg_delay_days`

**BOT_MAINTAINED Set:**
- Purpose: Filter list of 16 submodule names actively maintained by the `mssonicbld` bot
- Examples: Defined in `submodule-status/scripts/collector.py:BOT_MAINTAINED`
- Pattern: Set literal used in `parse_gitmodules()` to filter parsed submodule definitions

**Cadence/Thresholds:**
- Purpose: Per-submodule adaptive staleness thresholds computed from historical bump frequency
- Examples: Computed in `submodule-status/scripts/staleness.py:compute_cadence()` and `compute_thresholds()`
- Pattern: Dict with `median_days`, `yellow_days`, `red_days`, `is_fallback` — repos with <5 bumps get hardcoded fallback thresholds (30d/60d)

**requests.Session:**
- Purpose: Shared HTTP session with auth headers for all GitHub API calls
- Examples: Created in `submodule-status/scripts/collector.py:main()`, passed to all functions
- Pattern: Single session created at startup with `Authorization` and `Accept` headers, passed as first argument to every API-calling function

## Entry Points

**`submodule-status/scripts/collector.py:main()`:**
- Location: `submodule-status/scripts/collector.py`, line 225
- Triggers: `python scripts/collector.py` from GitHub Actions workflow
- Responsibilities: Orchestrates the full data collection pipeline — creates session, fetches `.gitmodules`, parses, collects per-submodule data, enriches with staleness and details, writes `data.json`

**`submodule-status/scripts/renderer.py:main()`:**
- Location: `submodule-status/scripts/renderer.py`, line 105
- Triggers: `python scripts/renderer.py` from GitHub Actions workflow
- Responsibilities: Reads `data.json`, renders HTML dashboard to `site/index.html`. Configurable via `DATA_PATH` and `SITE_DIR` environment variables (defaults: `data.json`, `site`)

## Error Handling

**Strategy:** Defensive — every API call is wrapped in try/except, failures produce degraded output rather than crashes. Individual submodule failures don't stop the pipeline.

**Patterns:**
- **Retry with backoff** in `collector.py:collect_submodule()`: Retries up to 3 times with exponential backoff (`2^attempt` seconds). On exhaustion, returns `status='unavailable'` with error message.
- **Graceful degradation** in enrichment functions: API errors set enriched fields to `None` and continue to the next submodule. Exceptions caught: `requests.RequestException`, `KeyError`, `ValueError`.
- **Safe defaults for staleness**: Submodules with `status='unavailable'` skip all enrichment and get `None` for staleness/detail fields.
- **Fallback thresholds**: Repos with fewer than 5 bump commits get hardcoded thresholds (30d yellow / 60d red) via `FALLBACK_THRESHOLDS` in `staleness.py`.

## Cross-Cutting Concerns

**Logging:** `print()` statements for summary output only (e.g., "Collected N submodules: X ok, Y unavailable"). No structured logging framework.

**Validation:** Minimal — relies on GitHub API response structure. `parse_gitmodules()` uses `configparser` for `.gitmodules` parsing. `get_pinned_sha()` validates that the contents API response has `type='submodule'`.

**Authentication:** GitHub token from `GITHUB_TOKEN` environment variable, set via `session.headers["Authorization"]` in `collector.py:main()`. Token is a GitHub Actions `secrets.GITHUB_TOKEN` (automatically provided).

**Rate Limiting:** Courtesy `time.sleep()` calls between API requests — 0.5s between submodule collections and between enrichment API calls. No explicit rate-limit header checking.

---

*Architecture analysis: 2026-03-24*
