# 🔧 sonic-buildcop

**Build health tools for [sonic-net](https://github.com/sonic-net) repositories**

[![Submodule Status](https://img.shields.io/badge/submodule_status-live-blue)](https://hdwhdw.github.io/sonic-buildcop/)
[![CI](https://github.com/hdwhdw/sonic-buildcop/actions/workflows/update-dashboard.yml/badge.svg)](https://github.com/hdwhdw/sonic-buildcop/actions/workflows/update-dashboard.yml)

## What is this?

A collection of tools that monitor and report on the build health of SONiC repositories. Each tool lives in its own directory with independent scripts, tests, and CI workflows.

## Projects

| Project | Description | Status |
|---|---|---|
| [`submodule-status/`](submodule-status/) | Tracks how far behind submodule pointers are in sonic-buildimage | ✅ Live |

## submodule-status

**Submodule staleness tracker for [sonic-net/sonic-buildimage](https://github.com/sonic-net/sonic-buildimage)**

sonic-buildimage uses dozens of Git submodules (sonic-swss, sonic-gnmi, sonic-utilities, etc.). A bot ([mssonicbld](https://github.com/mssonicbld)) submits PRs to keep submodule pointers up to date, but pointers still fall behind — sometimes by weeks or months.

This tool makes that staleness visible. It queries the GitHub API, computes how far behind each submodule pointer is, and publishes a dashboard to GitHub Pages.

👉 **[View the live dashboard](https://hdwhdw.github.io/sonic-buildcop/)**

### How it works

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
   GitHub Pages (deployed via Actions every 4 hours)
```

### Staleness model

Not all submodules update at the same pace. sonic-buildcop computes **per-submodule thresholds** based on actual development cadence:

| Metric | How it's computed |
|---|---|
| **Median cadence** | Median days between commits over the last 6 months |
| **Yellow threshold** | 2× median cadence (days) or 2 commits behind |
| **Red threshold** | 4× median cadence (days) or 4 commits behind |
| **Classification** | Worst of days-behind vs commits-behind determines color |

### Dashboard features

- **Staleness badges** — Color-coded pills (🟢 🟡 🔴) at a glance
- **Cadence metrics** — Median update frequency and threshold values per repo
- **Linked entities** — Names link to repos, SHAs link to commits
- **Dark mode** — Auto-detects OS preference
- **Sorted by severity** — Red first, then yellow, then green

### Development

```bash
cd submodule-status

# Install dependencies
pip install -r requirements.txt

# Run collector (needs GITHUB_TOKEN)
GITHUB_TOKEN=ghp_... python scripts/collector.py

# Render dashboard
python scripts/renderer.py

# Run tests
python -m pytest tests/ -v
```

## Adding a new project

1. Create a new directory at the repo root (e.g., `flaky-detector/`)
2. Add scripts, tests, and a `requirements.txt`
3. Add a workflow in `.github/workflows/`
4. Update the projects table in this README

## License

MIT
