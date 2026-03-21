# sonic-buildcop

## What This Is

A build health dashboard for sonic-net/sonic-buildimage that tracks submodule staleness. Shows how far behind each sonic-net submodule pointer is, with cadence-aware thresholds derived from each submodule's development pace. Live at https://hdwhdw.github.io/sonic-buildcop/.

## Current State

**v1.0 shipped** — 2026-03-21

Dashboard tracks 10 sonic-net submodules with green/yellow/red staleness badges, sorted worst-first, updated daily via GitHub Actions cron. 57 unit tests, ~1,770 lines of Python/HTML.

See `.planning/milestones/v1.0-ROADMAP.md` for full v1.0 details.

## Current Milestone: v1.1 Dashboard Polish

**Goal:** Upgrade the dashboard from functional to professional — better visuals, richer data, everything linkable.

**Target features:**
- Visual overhaul: professional CSS, dark mode support, improved table styling
- Linkify everything: submodule name → repo, path → buildimage directory, SHA → commit
- More data columns: median cadence, thresholds, last upstream commit date
- Drop noise: remove Path column (redundant with linked name)
- Human-friendly timestamps ("3 hours ago" instead of ISO 8601)
- Expand to all 31 sonic-net submodules
- Footer with link to source repo

## Core Value

Make submodule staleness visible and actionable — so maintainers catch drift early instead of discovering months-old pointers during crunch time.

## Next Milestone Goals

- GitHub Issues alerting for submodules that cross red threshold
- Auto-close issues when pointer is updated
- Expand to all 31 sonic-net submodules
- Team ownership mapping from CODEOWNERS

## Out of Scope

- Tracking external (non-sonic-net) submodules (p4lang, Marvell, etc.)
- Integration into sonic-net/sonic-buildimage repo directly — will upstream if proven useful
- Auto-merging or auto-updating submodule pointers — this is observability, not automation

## Constraints

- **Hosting**: GitHub Pages (GitHub-native, no external hosting)
- **Automation**: GitHub Actions only (no external CI/CD)
- **Repo location**: `hdwhdw/sonic-buildcop` (can move to sonic-net later)
- **Data source**: Queries sonic-net/sonic-buildimage remotely via GitHub API
- **Cost**: GitHub Actions free tier for public repos

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Standalone repo (hdwhdw/sonic-buildcop) | Easier to iterate without sonic-net admin permissions | ✅ Validated |
| Auto-compute staleness thresholds from cadence | Fixed thresholds don't work — submodules have wildly different update frequencies | ✅ Validated |
| 10 target submodules for v1 | Focused scope, expand in v2 | ✅ Shipped |
| Dashboard first, alerting second | Need to validate the staleness model before sending notifications | ✅ Validated |
| Python for all scripts | SONiC ecosystem consistency, pre-installed on runners | ✅ Validated |
| Median not mean for cadence | Resists holiday gaps and burst outliers | ✅ Validated |

---
*Last updated: 2026-03-21 after v1.0 milestone completion*
