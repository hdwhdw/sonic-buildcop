# Requirements: sonic-buildcop

**Defined:** 2026-03-20
**Core Value:** Make submodule staleness visible and actionable — so maintainers catch drift early instead of discovering months-old pointers during crunch time.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Collection

- [x] **DATA-01**: Dashboard lists the top 10 sonic-net submodules (sonic-swss, sonic-utilities, sonic-platform-daemons, sonic-sairedis, sonic-gnmi, sonic-swss-common, sonic-platform-common, sonic-host-services, sonic-linux-kernel, sonic-dash-ha) with their path and current pinned commit SHA in sonic-buildimage
- [x] **DATA-02**: Dashboard shows commits-behind count for each submodule (pinned pointer vs upstream HEAD)
- [x] **DATA-03**: Dashboard shows days-behind for each submodule (time since pinned commit was authored)
- [x] **DATA-04**: Dashboard provides a direct link to the GitHub compare view (pinned_sha...HEAD) for each submodule
- [x] **DATA-05**: Data collection correctly resolves each submodule's upstream default branch (not hardcoded to master/main)
- [x] **DATA-06**: Data collection handles .gitmodules parsing edge cases (name≠path mismatches, .git URL suffixes, empty paths)

### Staleness Model

- [x] **STALE-01**: Staleness thresholds are auto-computed per submodule from historical update cadence in sonic-buildimage
- [x] **STALE-02**: Frequently-updated submodules (e.g., weekly) trigger yellow/red status sooner than rarely-updated ones (e.g., yearly)
- [x] **STALE-03**: Staleness computation uses median inter-update interval (not mean) to resist outlier gaps
- [x] **STALE-04**: Submodules with insufficient history (<5 updates) fall back to sensible default thresholds
- [x] **STALE-05**: Each submodule displays a green/yellow/red status badge based on its computed thresholds

### Dashboard UI

- [x] **UI-01**: Dashboard displays a table with columns: submodule name, status badge, commits behind, days behind, link to compare view
- [x] **UI-02**: Table is sorted by staleness severity (worst-first) by default
- [x] **UI-03**: Dashboard shows a summary/aggregate view (e.g., "5 green, 3 yellow, 2 red")
- [x] **UI-04**: Dashboard shows a "last refreshed" timestamp so users know if the data itself is stale
- [x] **UI-05**: Dashboard has a responsive layout that works on laptop and monitor screens
- [ ] **UI-06**: Dashboard is hosted as a static GitHub Pages site on hdwhdw/sonic-buildcop

### CI/CD Pipeline

- [ ] **CICD-01**: GitHub Actions cron workflow runs daily to regenerate the dashboard
- [ ] **CICD-02**: Workflow deploys updated dashboard to GitHub Pages automatically
- [ ] **CICD-03**: Workflow stays within GitHub Actions free tier for public repos
- [x] **CICD-04**: Pipeline handles individual submodule failures gracefully (one failure doesn't break the whole dashboard)
- [ ] **CICD-05**: Workflow supports manual trigger (workflow_dispatch) for on-demand refresh

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Alerting

- **ALERT-01**: GitHub Issues are created/updated for submodules that cross the red threshold
- **ALERT-02**: Issues are auto-closed when the submodule pointer is updated
- **ALERT-03**: Issues mention the team/owner from CODEOWNERS

### Enhanced Dashboard

- **DASH-01**: Team ownership grouping (parse CODEOWNERS, group submodules by team)
- **DASH-02**: Historical staleness trend charts (Chart.js, requires accumulated daily snapshots)
- **DASH-03**: Commit diff summary showing titles/authors of missed commits
- **DASH-04**: JSON data endpoint for downstream consumers (scripts, bots, CI gates)
- **DASH-05**: Update cadence visualization (sparklines showing each submodule's rhythm)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-updating submodule pointers | Observability ≠ automation; updates can break builds and need human review |
| Tracking non-sonic-net submodules | Different ownership model and update expectations; dilutes signal |
| Real-time / webhook-driven updates | Daily cron sufficient for measuring weeks/months of staleness; would require server |
| Database backend | Violates GitHub Pages constraint; JSON snapshots in git sufficient for data volumes |
| User accounts / authentication | Public dashboard for a public repo; zero value from auth |
| Configuration UI in dashboard | Thresholds are auto-computed; manual overrides should be code-reviewed via YAML config |
| PR creation for stale submodules | mssonicbld bot already does this; duplicating creates conflicts |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| DATA-05 | Phase 1 | Complete |
| DATA-06 | Phase 1 | Complete |
| STALE-01 | Phase 2 | Complete |
| STALE-02 | Phase 2 | Complete |
| STALE-03 | Phase 2 | Complete |
| STALE-04 | Phase 2 | Complete |
| STALE-05 | Phase 2 | Complete |
| UI-01 | Phase 3 | Complete |
| UI-02 | Phase 3 | Complete |
| UI-03 | Phase 3 | Complete |
| UI-04 | Phase 3 | Complete |
| UI-05 | Phase 3 | Complete |
| UI-06 | Phase 1 | Pending |
| CICD-01 | Phase 1 | Pending |
| CICD-02 | Phase 1 | Pending |
| CICD-03 | Phase 1 | Pending |
| CICD-04 | Phase 1 | Complete |
| CICD-05 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22 ✓
- Unmapped: 0

---
*Requirements defined: 2026-03-20*
*Last updated: 2026-03-20 after roadmap creation*
