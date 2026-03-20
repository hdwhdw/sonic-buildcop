# sonic-buildcop

## What This Is

A build health dashboard for the sonic-net/sonic-buildimage repository, focused on tracking submodule staleness. It provides a GitHub Pages dashboard showing how far behind each sonic-net submodule pointer is relative to its upstream HEAD, with staleness thresholds derived automatically from each submodule's historical update cadence. Lives in `hdwhdw/sonic-buildcop` as a standalone repo that queries sonic-buildimage remotely.

## Core Value

Make submodule staleness visible and actionable — so maintainers catch drift early instead of discovering months-old pointers during crunch time.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Dashboard displays all 31 sonic-net submodules with commits behind, days behind, and color-coded status badges (green/yellow/red)
- [ ] Staleness thresholds auto-computed per submodule from historical update cadence (frequently-updated submodules go stale sooner than rarely-updated ones)
- [ ] GitHub Actions cron workflow regenerates the GitHub Pages dashboard daily
- [ ] Dashboard is hosted via GitHub Pages on `hdwhdw/sonic-buildcop`
- [ ] Dashboard queries sonic-net/sonic-buildimage remotely (no local clone required in the action)

### Out of Scope

- GitHub Issues alerting for stale submodules — deferred to v2
- Tracking external (non-sonic-net) submodules (p4lang, Marvell, etc.) — different ownership model
- Integration into sonic-net/sonic-buildimage repo directly — will upstream if proven useful
- Auto-merging or auto-updating submodule pointers — this is observability, not automation

## Context

- sonic-net/sonic-buildimage has 49 submodules total, 31 under the sonic-net org
- A bot attempts daily submodule update PRs, but the automerge GitHub Action (`automerge_scan.yml`) is currently disabled
- CODEOWNERS file maps submodules to team owners (e.g., @sonic-net/sonic-management, @sonic-net/sonic-dataplane)
- Submodule owners manually track freshness today — humans forget, and pointers drift by months
- The staleness problem is nuanced: a submodule updated weekly being 2 weeks behind is alarming; one updated yearly being 30 days behind after one commit is not

## Constraints

- **Hosting**: Must be GitHub Pages (GitHub-native, no external hosting)
- **Automation**: GitHub Actions only (no external CI/CD)
- **Repo location**: `hdwhdw/sonic-buildcop` for v1 (easy iteration, can move to sonic-net later)
- **Data source**: Must work by querying sonic-net/sonic-buildimage remotely via GitHub API or git
- **Cost**: Stay within GitHub Actions free tier for public repos

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Standalone repo (hdwhdw/sonic-buildcop) | Easier to iterate without sonic-net admin permissions; can upstream later | — Pending |
| Auto-compute staleness thresholds from cadence | Fixed thresholds don't work — submodules have wildly different update frequencies | — Pending |
| sonic-net submodules only (31 of 49) | External submodules have different ownership/update expectations | — Pending |
| Dashboard first, alerting second | Need to validate the staleness model before sending notifications | — Pending |

---
*Last updated: 2026-03-20 after initialization*
