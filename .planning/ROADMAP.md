# Roadmap: sonic-buildcop

## Overview

Deliver a GitHub Pages dashboard that makes sonic-net submodule staleness visible and actionable. The build order is data-first: get correct staleness numbers from the GitHub API (Phase 1), compute cadence-aware thresholds that distinguish urgent drift from acceptable lag (Phase 2), then assemble the polished dashboard maintainers actually use (Phase 3). Each phase delivers an independently verifiable capability deployed to GitHub Pages.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Data Pipeline & Deployment** - Collect correct submodule staleness data via GitHub API and deploy to Pages on a daily cron
- [ ] **Phase 2: Staleness Model** - Compute cadence-aware per-submodule thresholds and classify each as green/yellow/red
- [ ] **Phase 3: Dashboard UI** - Build the polished, sortable, summary-at-a-glance dashboard maintainers use daily

## Phase Details

### Phase 1: Data Pipeline & Deployment
**Goal**: Correct submodule staleness data is collected from sonic-buildimage and deployed to GitHub Pages daily
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, CICD-01, CICD-02, CICD-03, CICD-04, CICD-05, UI-06
**Success Criteria** (what must be TRUE):
  1. Visiting the GitHub Pages URL shows data for the 10 target sonic-net submodules including each submodule's path and current pinned commit SHA
  2. Each submodule shows an accurate commits-behind count and days-behind value that match GitHub's compare view
  3. Each submodule has a clickable link to the correct GitHub compare view (pinned_sha...HEAD on the right branch)
  4. The GitHub Actions workflow runs on a daily cron schedule and can be triggered manually via workflow_dispatch
  5. If one submodule's data collection fails, the remaining submodules still appear on the deployed page
**Plans:** 3 plans

Plans:
- [ ] 01-01-PLAN.md — Data collector with tests (collector.py: .gitmodules parsing, GitHub API, staleness computation)
- [ ] 01-02-PLAN.md — HTML renderer + project config (renderer.py, Jinja2 template, requirements.txt, .gitignore)
- [ ] 01-03-PLAN.md — CI/CD workflow + deployment verification (GitHub Actions daily cron + Pages deploy)

### Phase 2: Staleness Model
**Goal**: Each submodule has cadence-aware staleness thresholds that distinguish urgently-stale from acceptably-behind
**Depends on**: Phase 1
**Requirements**: STALE-01, STALE-02, STALE-03, STALE-04, STALE-05
**Success Criteria** (what must be TRUE):
  1. Each submodule's yellow/red thresholds reflect its historical update frequency — a weekly-updated submodule triggers warning sooner than a rarely-updated one
  2. Thresholds are computed from median inter-update interval (not mean), resisting outlier gaps like holiday periods
  3. Submodules with fewer than 5 historical updates display sensible fallback thresholds instead of meaningless computed ones
  4. Each submodule displays a green, yellow, or red status badge based on its individually-computed thresholds
**Plans:** 2 plans

Plans:
- [ ] 02-01-PLAN.md — Staleness module TDD (staleness.py: cadence computation, threshold derivation, classification)
- [ ] 02-02-PLAN.md — Pipeline integration + badge display (collector.py wiring, dashboard.html status column)

### Phase 3: Dashboard UI
**Goal**: Maintainers can assess project-wide submodule health in under 10 seconds from a polished dashboard
**Depends on**: Phase 2
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05
**Success Criteria** (what must be TRUE):
  1. Dashboard displays a table with columns: submodule name, status badge, commits behind, days behind, and link to compare view
  2. Table is sorted by staleness severity (worst-first) by default
  3. Dashboard shows an aggregate summary (e.g., "5 green, 3 yellow, 2 red") for instant project-wide health assessment
  4. Dashboard displays a "last refreshed" timestamp so users know if the data itself is stale
  5. Dashboard layout is responsive and readable on both laptop and wide monitor screens
**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Sort + summary Python logic with TDD tests (renderer.py: sort_submodules, compute_summary)
- [ ] 03-02-PLAN.md — Template CSS polish, summary display, responsive layout (dashboard.html overhaul + integration tests)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Pipeline & Deployment | 0/3 | Not started | - |
| 2. Staleness Model | 0/2 | Not started | - |
| 3. Dashboard UI | 0/2 | Not started | - |
