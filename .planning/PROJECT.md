# sonic-buildcop

## What This Is

A build health dashboard for sonic-net/sonic-buildimage that tracks submodule staleness. Shows how far behind each sonic-net submodule pointer is, with cadence-aware thresholds derived from each submodule's development pace. Live at https://hdwhdw.github.io/sonic-buildcop/.

## Current State

**v1.1 shipped** — 2026-03-21

Dashboard tracks all ~31 sonic-net submodules with cadence-aware staleness badges, linked names/SHAs, dark mode support, and professional CSS. 81 unit tests. Updated daily via GitHub Actions cron. Live at https://hdwhdw.github.io/sonic-buildcop/.

See `.planning/milestones/v1.1-ROADMAP.md` for full v1.1 details.

## Core Value

Make submodule staleness visible and actionable — so maintainers catch drift early instead of discovering months-old pointers during crunch time.

## Next Milestone Goals

- GitHub Issues alerting for submodules that cross red threshold
- Auto-close issues when pointer is updated
- Team ownership mapping from CODEOWNERS
- Historical trend charts

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
| 10 target submodules for v1 | Focused scope, expand in v1.1 | ✅ Shipped (expanded to all in v1.1) |
| CSS-only dark mode | No JS toggle, prefers-color-scheme auto-detection | ✅ Validated |
| Drop Path column | Redundant with linked name; always `src/<name>` | ✅ Shipped |
| Dashboard first, alerting second | Need to validate the staleness model before sending notifications | ✅ Validated |
| Python for all scripts | SONiC ecosystem consistency, pre-installed on runners | ✅ Validated |
| Median not mean for cadence | Resists holiday gaps and burst outliers | ✅ Validated |

---
*Last updated: 2026-03-21 after v1.1 milestone completion*
