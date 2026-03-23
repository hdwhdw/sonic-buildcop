# Requirements: sonic-buildcop

**Defined:** 2026-03-21
**Core Value:** Make submodule staleness visible and actionable — so maintainers catch drift early instead of discovering months-old pointers during crunch time.

## v1.2 Requirements

Requirements for v1.2 Detail Enrichment. Each maps to roadmap phases.

### Data Enrichment

- [x] **ENRICH-01**: Collector fetches open bot PR (from mssonicbld) for each submodule in sonic-buildimage
- [x] **ENRICH-02**: Collector fetches last merged bot PR for each submodule
- [x] **ENRICH-03**: Collector fetches latest commit date from each submodule's own repo
- [x] **ENRICH-04**: Collector computes average delay between repo commits and pointer bumps

### Expandable UI

- [x] **EXPAND-01**: Dashboard rows are clickable to expand/collapse an inline detail panel
- [x] **EXPAND-02**: Detail panel shows open bot PR with link, age, and CI status (pass/fail/pending)
- [x] **EXPAND-03**: Detail panel shows last pointer update linked to the merged bot PR
- [x] **EXPAND-04**: Detail panel shows last repo commit linked to the commit
- [x] **EXPAND-05**: Detail panel shows average delay metric

## Future Requirements

### Alerting

- **ALERT-01**: GitHub Issues created when submodule crosses red threshold
- **ALERT-02**: Issues auto-closed when pointer is updated
- **ALERT-03**: Team ownership mapping from CODEOWNERS

### Analytics

- **ANAL-01**: Historical trend charts for staleness over time

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-merging bot PRs | This is observability, not automation |
| Non-sonic-net submodules | Not maintained by the SONiC community |
| Server-side rendering | Static GitHub Pages only |
| External JS frameworks | Vanilla JS sufficient for expandable rows |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENRICH-01 | Phase 6 | Complete |
| ENRICH-02 | Phase 6 | Complete |
| ENRICH-03 | Phase 6 | Complete |
| ENRICH-04 | Phase 6 | Complete |
| EXPAND-01 | Phase 7 | Complete |
| EXPAND-02 | Phase 7 | Complete |
| EXPAND-03 | Phase 7 | Complete |
| EXPAND-04 | Phase 7 | Complete |
| EXPAND-05 | Phase 7 | Complete |

**Coverage:**
- v1.2 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-21*
*Last updated: 2026-03-21 after initial definition*
