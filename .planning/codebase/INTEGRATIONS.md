# External Integrations

**Analysis Date:** 2025-03-24

## APIs & External Services

**GitHub REST API v3:**
- Base URL: `https://api.github.com` (constant `API_BASE` in `submodule-status/scripts/collector.py`, `submodule-status/scripts/staleness.py`, `submodule-status/scripts/enrichment.py`)
- SDK/Client: `requests.Session` with persistent auth headers
- Auth: `GITHUB_TOKEN` environment variable (Bearer token via `Authorization: token {token}`)
- Accept header: `application/vnd.github.v3+json`
- Rate limiting: Manual 0.5s courtesy delays between requests (`time.sleep(0.5)`)

**GitHub API Endpoints Used:**

| Endpoint | Used In | Purpose |
|---|---|---|
| `GET /repos/{owner}/{repo}/contents/{path}` | `collector.py` `get_pinned_sha()`, `enrichment.py` `compute_avg_delay_for_submodule()` | Fetch .gitmodules content and submodule SHA at specific refs |
| `GET /repos/{owner}/{repo}` | `collector.py` `get_default_branch()` | Get default branch name for a repo |
| `GET /repos/{owner}/{repo}/compare/{base}...{head}` | `collector.py` `get_staleness()` | Compare pinned SHA vs branch HEAD for commit/day delta |
| `GET /repos/{owner}/{repo}/commits/{ref}` | `collector.py` `get_staleness()`, `enrichment.py` `fetch_latest_repo_commits()`, `enrichment.py` `compute_avg_delay_for_submodule()` | Get commit details (date, SHA) |
| `GET /repos/{owner}/{repo}/commits` | `staleness.py` `get_bump_dates()`, `enrichment.py` `compute_avg_delay_for_submodule()` | List commits touching a path (pointer bump history) |
| `GET /search/issues` | `enrichment.py` `fetch_open_bot_prs()`, `enrichment.py` `fetch_merged_bot_prs()` | Search for bot-authored PRs (open and merged) |
| `GET /repos/{owner}/{repo}/pulls/{number}` | `enrichment.py` `get_ci_status_for_pr()` | Get PR head SHA for CI check lookup |
| `GET /repos/{owner}/{repo}/commits/{sha}/check-runs` | `enrichment.py` `get_ci_status_for_pr()` | Get CI check run status for a commit |

**Target Repositories:**
- Primary: `sonic-net/sonic-buildimage` (parent repo with submodules)
- Submodules: 16 bot-maintained repos under `sonic-net/` org (hardcoded in `BOT_MAINTAINED` set in `submodule-status/scripts/collector.py`)
- Bot author: `mssonicbld` (hardcoded in `BOT_AUTHOR` in `submodule-status/scripts/enrichment.py`)

## Data Storage

**Databases:**
- None — no database used

**File Storage:**
- Local filesystem only
- `data.json` — intermediate JSON file written by `submodule-status/scripts/collector.py`, read by `submodule-status/scripts/renderer.py`
- `site/index.html` — rendered static dashboard output
- `site/.nojekyll` — empty file to disable GitHub Pages Jekyll processing

**Caching:**
- None — all data is fetched fresh from GitHub API on each run

## Authentication & Identity

**Auth Provider:**
- GitHub Actions built-in `GITHUB_TOKEN` (automatic)
  - Implementation: Token passed as `Authorization: token {token}` header on `requests.Session` in `submodule-status/scripts/collector.py` `main()`
  - Scope: Read-only access to public repositories
  - No user authentication — this is a read-only data pipeline

## Monitoring & Observability

**Error Tracking:**
- None — no external error tracking service

**Logs:**
- `print()` statements to stdout in `submodule-status/scripts/collector.py` and `submodule-status/scripts/renderer.py`
- Format: Simple string messages (e.g., `f"Collected {len(results)} submodules: {ok_count} ok, {fail_count} unavailable"`)
- No structured logging framework

**Error Handling:**
- Retry with exponential backoff (3 retries) in `submodule-status/scripts/collector.py` `collect_submodule()`
- Graceful degradation: failed submodules get `status="unavailable"` with error message, pipeline continues
- All enrichment functions catch `(requests.RequestException, KeyError, ValueError)` and set fields to `None`

## CI/CD & Deployment

**Hosting:**
- GitHub Pages (static site)
- URL: `https://hdwhdw.github.io/sonic-buildcop/`

**CI Pipeline:**
- GitHub Actions (`.github/workflows/update-dashboard.yml`)
- Runner: `ubuntu-latest`
- Triggers:
  - `push` to `main` branch
  - `schedule`: cron `0 */4 * * *` (every 4 hours)
  - `workflow_dispatch` (manual trigger)
- Concurrency: `dashboard-deploy` group with `cancel-in-progress: true`
- Permissions: `contents: read`, `pages: write`, `id-token: write`

**Deployment Steps:**
1. Checkout repo (`actions/checkout@v4`)
2. Setup Python 3.12 (`actions/setup-python@v5`)
3. Install deps (`pip install -r requirements.txt`)
4. Run collector (`python scripts/collector.py` with `GITHUB_TOKEN`)
5. Run renderer (`python scripts/renderer.py`)
6. Configure Pages (`actions/configure-pages@v5`)
7. Upload artifact (`actions/upload-pages-artifact@v4` from `submodule-status/site`)
8. Deploy to Pages (`actions/deploy-pages@v4`)

**GitHub Actions Used:**
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/configure-pages@v5`
- `actions/upload-pages-artifact@v4`
- `actions/deploy-pages@v4`

## Environment Configuration

**Required env vars:**
- `GITHUB_TOKEN` — GitHub API authentication (provided automatically in GitHub Actions via `${{ secrets.GITHUB_TOKEN }}`)

**Optional env vars:**
- `DATA_PATH` — Override input data file path (default: `"data.json"`)
- `SITE_DIR` — Override output site directory (default: `"site"`)

**Secrets location:**
- GitHub Actions secrets (repository-level)
- No `.env` files present

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2025-03-24*
