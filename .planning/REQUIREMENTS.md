# Requirements: sonic-buildcop v1.1

**Defined:** 2026-03-21
**Core Value:** Make submodule staleness visible and actionable — so maintainers catch drift early instead of discovering months-old pointers during crunch time.

## v1.1 Requirements

Requirements for Dashboard Polish milestone. Builds on v1.0's functional dashboard.

### Visual Polish

- [ ] **VIS-01**: Dashboard has professional CSS with system fonts, refined borders, row hover, and consistent spacing
- [ ] **VIS-02**: Dark mode support (auto-detects OS preference via `prefers-color-scheme`)
- [ ] **VIS-03**: Status badges render as colored pills (not plain text "green"/"yellow"/"red")
- [ ] **VIS-04**: Header area with project title and brief description of what the dashboard shows

### Linkification

- [ ] **LINK-01**: Submodule name links to its GitHub repo (e.g., sonic-net/sonic-gnmi)
- [ ] **LINK-02**: Pinned SHA links to the exact commit on GitHub
- [ ] **LINK-03**: Path column replaced by link to submodule directory in sonic-buildimage (or dropped if name link is sufficient)
- [ ] **LINK-04**: Footer with link to hdwhdw/sonic-buildcop source repo

### Data Enrichment

- [ ] **DATA-07**: Display median cadence column (e.g., "~1.2 days") per submodule
- [ ] **DATA-08**: Display threshold values (e.g., "yellow: 2d / red: 5d") per submodule
- [x] **DATA-09**: Expand from 10 to all 31 sonic-net submodules
- [ ] **DATA-10**: Human-friendly "last updated" timestamp (e.g., "3 hours ago" instead of ISO 8601)

## Future Requirements

Deferred to next milestone:
- GitHub Issues alerting for stale submodules (ALERT-01 through ALERT-03)
- Team ownership grouping from CODEOWNERS
- Historical trend charts

## Out of Scope

| Feature | Reason |
|---------|--------|
| Client-side JavaScript sorting/filtering | v1.0 decision: pre-sort in Python, keep page static |
| External CSS frameworks (Bootstrap, Tailwind) | v1.0 decision: inline CSS only, no dependencies |
| Auto-updating submodule pointers | Observability ≠ automation |
| Tracking non-sonic-net submodules | Different ownership model |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| VIS-01 | Phase 5 | Pending |
| VIS-02 | Phase 5 | Pending |
| VIS-03 | Phase 5 | Pending |
| VIS-04 | Phase 5 | Pending |
| LINK-01 | Phase 5 | Pending |
| LINK-02 | Phase 5 | Pending |
| LINK-03 | Phase 5 | Pending |
| LINK-04 | Phase 5 | Pending |
| DATA-07 | Phase 4 | Pending |
| DATA-08 | Phase 4 | Pending |
| DATA-09 | Phase 4 | Complete |
| DATA-10 | Phase 4 | Pending |

**Coverage:**
- v1.1 requirements: 12 total
- Mapped to phases: 12/12 ✓
  - Phase 4: 4 requirements (DATA-07, DATA-08, DATA-09, DATA-10)
  - Phase 5: 8 requirements (VIS-01..04, LINK-01..04)

---
*Requirements defined: 2026-03-21*
