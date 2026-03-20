---
phase: 01-data-pipeline-deployment
verified: 2026-03-20T18:29:45Z
status: human_needed
score: 5/5 must-haves verified
re_verification: false
human_verification:
  - test: "Visit https://hdwhdw.github.io/sonic-buildcop/ and confirm 10 submodules display"
    expected: "Table with 10 rows showing submodule name, path, pinned SHA, commits behind, days behind, and compare link"
    why_human: "Requires live browser to confirm deployed site renders correctly"
  - test: "Click a compare link from the dashboard"
    expected: "Opens correct GitHub compare view (pinned_sha...HEAD) for that submodule"
    why_human: "Requires live browser to verify link targets resolve"
  - test: "Trigger manual workflow_dispatch via Actions UI"
    expected: "Workflow runs, collects fresh data, deploys updated dashboard"
    why_human: "Requires GitHub Actions UI interaction"
  - test: "Verify daily cron has run at least once"
    expected: "Actions tab shows a scheduled run (check after 24h from deploy)"
    why_human: "Requires waiting for scheduled trigger and checking Actions tab"
---

# Phase 1: Data Pipeline & Deployment — Verification Report

**Phase Goal:** Correct submodule staleness data is collected from sonic-buildimage and deployed to GitHub Pages daily
**Verified:** 2026-03-20T18:29:45Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Success Criteria from ROADMAP.md)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Visiting the GitHub Pages URL shows data for the 10 target sonic-net submodules including each submodule's path and current pinned commit SHA | ✓ VERIFIED | `TARGET_SUBMODULES` has exactly 10 entries; template renders name, path, `pinned_sha[:7]` for each; workflow deploys `site/` to Pages via `actions/deploy-pages@v4` |
| 2 | Each submodule shows an accurate commits-behind count and days-behind value that match GitHub's compare view | ✓ VERIFIED | `get_staleness()` uses Compare API `ahead_by` for commits_behind; days_behind = HEAD date - pinned date (not now() - pinned); tests verify 5 commits / 36 days computation |
| 3 | Each submodule has a clickable link to the correct GitHub compare view (pinned_sha...HEAD on the right branch) | ✓ VERIFIED | `build_compare_url()` generates `https://github.com/{owner}/{repo}/compare/{sha}...{branch}`; template has `<a href="{{ sub.compare_url }}">View</a>`; branch resolved from .gitmodules or API fallback |
| 4 | The GitHub Actions workflow runs on a daily cron schedule and can be triggered manually via workflow_dispatch | ✓ VERIFIED | Workflow has `cron: '0 6 * * *'` and `workflow_dispatch:` trigger; both present in `.github/workflows/update-dashboard.yml` |
| 5 | If one submodule's data collection fails, the remaining submodules still appear on the deployed page | ✓ VERIFIED | `collect_submodule()` catches exceptions, returns `status=unavailable` with error; template renders unavailable entries with em-dash placeholders; test `test_collect_submodule_unavailable_after_retries` confirms |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/collector.py` | Complete data collection pipeline (≥120 lines) | ✓ VERIFIED | 239 lines; exports all 7 functions: `parse_gitmodules`, `get_pinned_sha`, `get_default_branch`, `get_staleness`, `build_compare_url`, `collect_submodule`, `main` |
| `scripts/renderer.py` | HTML generation from data.json (≥30 lines) | ✓ VERIFIED | 47 lines; exports `render_dashboard`, `main`; reads data.json, renders via Jinja2, writes site/index.html + .nojekyll |
| `templates/dashboard.html` | Jinja2 template with table layout (≥30 lines) | ✓ VERIFIED | 54 lines; contains `{% for sub in submodules %}`; 6-column table; error state handling |
| `.github/workflows/update-dashboard.yml` | CI/CD pipeline (≥35 lines) | ✓ VERIFIED | 54 lines; contains `schedule`, `workflow_dispatch`, `deploy-pages`; proper permissions |
| `tests/test_collector.py` | Collector unit tests (≥100 lines) | ✓ VERIFIED | 287 lines; 14 tests all passing |
| `tests/test_renderer.py` | Renderer unit tests (≥40 lines) | ✓ VERIFIED | 139 lines; 9 tests all passing |
| `tests/conftest.py` | Shared fixtures (≥30 lines) | ✓ VERIFIED | 128 lines; 6 fixtures with sample .gitmodules (12 entries) and mock API responses |
| `requirements.txt` | Python dependencies | ✓ VERIFIED | Contains `jinja2` and `requests` |
| `.gitignore` | Excludes generated files | ✓ VERIFIED | Excludes `site/`, `data.json`, Python caches, IDE files |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `update-dashboard.yml` | `scripts/collector.py` | `python scripts/collector.py` step | ✓ WIRED | Line 38: `run: python scripts/collector.py` with GITHUB_TOKEN env |
| `update-dashboard.yml` | `scripts/renderer.py` | `python scripts/renderer.py` step | ✓ WIRED | Line 42: `run: python scripts/renderer.py` |
| `update-dashboard.yml` | `requirements.txt` | `pip install -r requirements.txt` step | ✓ WIRED | Line 35: `run: pip install -r requirements.txt` |
| `update-dashboard.yml` | `site/` | `upload-pages-artifact` path | ✓ WIRED | Line 50: `path: ./site` |
| `collector.py` | `data.json` | `json.dump(output, f)` | ✓ WIRED | Line 229-230: writes to `data.json` |
| `renderer.py` | `data.json` | `json.load(f)` | ✓ WIRED | Line 13: reads data_path (default `data.json`) |
| `renderer.py` | `templates/dashboard.html` | `env.get_template("dashboard.html")` | ✓ WIRED | Line 18: loads template via FileSystemLoader from `../templates` |
| `renderer.py` | `site/index.html` | `f.write(html)` | ✓ WIRED | Line 28-29: writes rendered HTML to site_dir/index.html |
| `test_collector.py` | `collector.py` | `from collector import ...` | ✓ WIRED | Line 5-12: imports all 6 public functions |
| `test_renderer.py` | `renderer.py` | `from renderer import render_dashboard` | ✓ WIRED | Line 10: imports render_dashboard |
| `conftest.py` | `scripts/` | `sys.path.insert` | ✓ WIRED | Line 5: adds scripts/ to sys.path |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-01 | 01-01 | Lists 10 sonic-net submodules with path and pinned SHA | ✓ SATISFIED | `TARGET_SUBMODULES` has exact 10 names; template shows name, path, SHA |
| DATA-02 | 01-01 | Shows commits-behind count | ✓ SATISFIED | `get_staleness()` returns `commits_behind` from Compare API `ahead_by`; template column present |
| DATA-03 | 01-01 | Shows days-behind | ✓ SATISFIED | `get_staleness()` computes `days_behind = (head_date - pinned_date).days`; template column present |
| DATA-04 | 01-01 | Direct link to GitHub compare view | ✓ SATISFIED | `build_compare_url()` generates correct URL; template has clickable `<a href>` link |
| DATA-05 | 01-01 | Resolves default branch dynamically | ✓ SATISFIED | `collect_submodule()` checks `.gitmodules` branch first, falls back to `get_default_branch()` API call |
| DATA-06 | 01-01 | Handles .gitmodules parsing edge cases | ✓ SATISFIED | `removesuffix('.git')` not `rstrip`; configparser handles name≠path; fixture tests 12-entry file with non-targets |
| CICD-01 | 01-03 | Daily cron schedule | ✓ SATISFIED | `cron: '0 6 * * *'` in workflow |
| CICD-02 | 01-03 | GitHub Pages deployment | ✓ SATISFIED | `actions/deploy-pages@v4` with `upload-pages-artifact` of `./site` |
| CICD-03 | 01-03 | Uses GITHUB_TOKEN only | ✓ SATISFIED | `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}`; no PAT references; permissions scoped to `contents:read`, `pages:write`, `id-token:write` |
| CICD-04 | 01-01 | Graceful per-submodule failure | ✓ SATISFIED | `collect_submodule()` catches errors, returns `status=unavailable`; tested by `test_collect_submodule_unavailable_after_retries` |
| CICD-05 | 01-03 | Manual trigger support | ✓ SATISFIED | `workflow_dispatch:` present in workflow triggers |
| UI-06 | 01-03 | Dashboard on GitHub Pages | ✓ SATISFIED | Workflow deploys site/ with .nojekyll to GitHub Pages; 01-03 SUMMARY confirms live at `https://hdwhdw.github.io/sonic-buildcop/` |

**Note:** The phase context mentioned STALE-05, but per ROADMAP.md and REQUIREMENTS.md traceability, STALE-05 ("green/yellow/red status badge") is a Phase 2 requirement. The compare URL functionality referenced is actually DATA-04, which is fully satisfied above.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | No anti-patterns detected |

Zero TODO/FIXME/HACK/placeholder comments found. Zero empty implementations (the `pass` on renderer.py:33 is intentional — creates an empty `.nojekyll` file). Zero console.log-only handlers. All functions have substantive implementations.

### Human Verification Required

### 1. Live Dashboard Renders Correctly

**Test:** Visit https://hdwhdw.github.io/sonic-buildcop/ in a browser
**Expected:** HTML page with a table showing 10 submodules, each with name, path, pinned SHA (7 chars), commits behind count, days behind count, and a "View" compare link
**Why human:** Requires live browser to verify deployed static site renders correctly on GitHub Pages

### 2. Compare Links Resolve Correctly

**Test:** Click 2-3 "View" links from the dashboard
**Expected:** Each opens the correct GitHub compare view showing commits between the pinned SHA and HEAD of the target branch
**Why human:** Requires browser navigation and visual confirmation that GitHub's compare view shows the expected diff

### 3. Manual Workflow Dispatch Works

**Test:** Go to Actions tab → "Update Dashboard" → "Run workflow" → click green button
**Expected:** Workflow runs successfully, re-collects data, re-renders dashboard, and deploys to Pages
**Why human:** Requires GitHub Actions UI interaction

### 4. Daily Cron Executes

**Test:** Check Actions tab after 6 AM UTC the following day
**Expected:** A scheduled run appears in the workflow history with a successful status
**Why human:** Requires waiting for scheduled trigger to fire and checking results

### Gaps Summary

No gaps found in automated verification. All 5 success criteria are verified through code analysis, all 12 requirements have implementation evidence, all 23 tests pass, all key links are wired, and zero anti-patterns detected.

Four items require human verification: live site rendering, compare link resolution, manual dispatch, and daily cron execution. These are inherently human-only checks (live URL, browser interaction, time-delayed events).

**Minor deviation noted:** Plan 01-03 stated "Workflow installs only jinja2 via pip (requests is pre-installed)" but `requests` was added to `requirements.txt` after discovering it wasn't pre-installed on ubuntu-latest runners. This is documented in 01-03-SUMMARY and is a **correct fix**, not a regression.

---

_Verified: 2026-03-20T18:29:45Z_
_Verifier: Claude (gsd-verifier)_
