# 🔍 sonic-buildcop

**Submodule staleness tracker for [sonic-net/sonic-buildimage](https://github.com/sonic-net/sonic-buildimage)**

[![Dashboard](https://img.shields.io/badge/dashboard-live-blue)](https://hdwhdw.github.io/sonic-buildcop/)
[![Update Dashboard](https://github.com/hdwhdw/sonic-buildcop/actions/workflows/update-dashboard.yml/badge.svg)](https://github.com/hdwhdw/sonic-buildcop/actions/workflows/update-dashboard.yml)

## What is this?

sonic-buildimage uses dozens of Git submodules (sonic-swss, sonic-gnmi, sonic-utilities, etc.). A bot ([mssonicbld](https://github.com/mssonicbld)) submits PRs to keep submodule pointers up to date, but pointers still fall behind — sometimes by weeks or months.

**sonic-buildcop** makes that staleness visible. It queries the GitHub API, computes how far behind each submodule pointer is, and publishes a dashboard to GitHub Pages.

👉 **[View the live dashboard](https://hdwhdw.github.io/sonic-buildcop/)**

## How it works

```
.gitmodules (sonic-buildimage)
        │
        ▼
   collector.py ──→ GitHub API (pinned SHA, HEAD, compare)
        │
        ▼
   staleness.py ──→ cadence analysis (median inter-commit interval)
        │
        ▼
    data.json
        │
        ▼
   renderer.py ──→ dashboard.html (Jinja2 template)
        │
        ▼
   GitHub Pages (deployed via Actions)
```

1. **Collect** — Fetches `.gitmodules` from sonic-buildimage, queries each submodule's pinned SHA vs HEAD, computes commits-behind and days-behind
2. **Classify** — Computes each submodule's median commit cadence over 6 months, derives yellow/red thresholds (2×/4× median), classifies as 🟢 green / 🟡 yellow / 🔴 red
3. **Render** — Generates a static HTML dashboard sorted worst-first, with linked entities and dark mode support
4. **Deploy** — GitHub Actions cron runs every 4 hours, deploying to GitHub Pages

## Staleness model

Not all submodules update at the same pace. A repo that commits daily is "stale" after a week; a repo that commits monthly isn't stale after the same period.

sonic-buildcop computes **per-submodule thresholds** based on actual development cadence:

| Metric | How it's computed |
|---|---|
| **Median cadence** | Median days between commits over the last 6 months |
| **Yellow threshold** | 2× median cadence (days) or 2 commits behind |
| **Red threshold** | 4× median cadence (days) or 4 commits behind |
| **Classification** | Worst of days-behind vs commits-behind determines color |

Submodules with fewer than 5 commits in 6 months use fallback thresholds (30d/60d yellow/red).

## Tracked submodules

Only submodules actively maintained by the [mssonicbld](https://github.com/mssonicbld) bot are tracked (16 repos). Unmaintained repos are excluded as noise.

## Dashboard features

- **Staleness badges** — Color-coded pills (🟢 🟡 🔴) at a glance
- **Cadence metrics** — Median update frequency and threshold values per repo
- **Linked entities** — Submodule names link to repos, SHAs link to commits, compare links to diffs
- **Dark mode** — Auto-detects OS preference
- **Relative timestamps** — "3 hours ago" instead of ISO 8601
- **Sorted by severity** — Red first, then yellow, then green

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run collector (needs GITHUB_TOKEN)
GITHUB_TOKEN=ghp_... python scripts/collector.py

# Render dashboard
python scripts/renderer.py

# Run tests
python -m pytest tests/ -v
```

## Project structure

```
scripts/
  collector.py    # Fetches submodule data from GitHub API
  staleness.py    # Cadence computation and staleness classification
  renderer.py     # Jinja2 → HTML rendering, sorting, summaries
templates/
  dashboard.html  # Dashboard template with CSS and dark mode
tests/
  test_collector.py
  test_staleness.py
  test_renderer.py
  conftest.py     # Shared fixtures
```

## License

MIT
