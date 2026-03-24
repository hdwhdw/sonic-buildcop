# Requirements: sonic-buildcop

**Defined:** 2026-03-23
**Core Value:** Make submodule staleness visible and actionable — so maintainers catch drift early instead of discovering months-old pointers during crunch time.

## v1.3 Requirements

Requirements for Cadence Fix milestone. Each maps to roadmap phases.

### Cadence Model

- [x] **CAD-01**: Cadence is computed from pointer bump commit intervals in sonic-buildimage (not submodule repo commit intervals)
- [x] **CAD-02**: Median inter-bump interval replaces median inter-commit interval as the cadence metric
- [ ] **CAD-03**: Yellow threshold remains 2× median cadence, red remains 4× median cadence (derived from bump intervals)
- [ ] **CAD-04**: Staleness classification uses corrected cadence-derived thresholds

### Data Pipeline

- [x] **DATA-01**: Pointer bump history is collected from sonic-buildimage commit log (commits that update submodule pointers)
- [x] **DATA-02**: Fallback thresholds apply when fewer than 5 pointer bumps exist in the lookback window

### Tests

- [ ] **TEST-01**: Unit tests validate cadence computed from pointer bump intervals
- [ ] **TEST-02**: Unit tests validate threshold derivation from bump-based cadence
- [ ] **TEST-03**: Existing tests updated to reflect new cadence definition

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

### Alerting

- **ALERT-01**: GitHub Issues alerting for submodules that cross red threshold
- **ALERT-02**: Auto-close issues when pointer is updated

### Ownership

- **OWN-01**: Team ownership mapping from CODEOWNERS

### Analytics

- **ANAL-01**: Historical trend charts

## Out of Scope

| Feature | Reason |
|---------|--------|
| Tracking external (non-sonic-net) submodules | Not part of core value |
| Auto-merging or auto-updating submodule pointers | This is observability, not automation |
| Changing threshold multipliers (2×/4×) | Only the cadence source changes, not the formula |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CAD-01 | Phase 8 | Complete |
| CAD-02 | Phase 8 | Complete |
| CAD-03 | Phase 9 | Pending |
| CAD-04 | Phase 9 | Pending |
| DATA-01 | Phase 8 | Complete |
| DATA-02 | Phase 8 | Complete |
| TEST-01 | Phase 9 | Pending |
| TEST-02 | Phase 9 | Pending |
| TEST-03 | Phase 9 | Pending |

**Coverage:**
- v1.3 requirements: 9 total
- Mapped to phases: 9 ✓
- Unmapped: 0

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-23 after roadmap creation*
