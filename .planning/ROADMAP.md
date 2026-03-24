# Roadmap: sonic-buildcop

## Milestones

- ✅ **v1.0** — Submodule Staleness Dashboard (Phases 1-3, 7 plans) → [Archive](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1** — Dashboard Polish (Phases 4-5, 4 plans) → [Archive](milestones/v1.1-ROADMAP.md)
- ✅ **v1.2** — Detail Enrichment (Phases 6-7, 3 plans) → [Archive](milestones/v1.2-ROADMAP.md)
- 🔄 **v1.3** — Cadence Fix (Phases 8-9)

## Phases

<details>
<summary>✅ v1.0 Submodule Staleness Dashboard (Phases 1-3) — SHIPPED 2026-03-21</summary>

- [x] **Phase 1: Data Pipeline & Deployment** — Collector, renderer, CI/CD
- [x] **Phase 2: Staleness Model** — Cadence-aware thresholds and classification
- [x] **Phase 3: Dashboard UI** — Sort, summary, CSS polish

See [v1.0 Archive](milestones/v1.0-ROADMAP.md) for full details.

</details>

<details>
<summary>✅ v1.1 Dashboard Polish (Phases 4-5) — SHIPPED 2026-03-21</summary>

- [x] **Phase 4: Data Expansion** — All sonic-net submodules, cadence columns, relative timestamps
- [x] **Phase 5: Visual Overhaul & Linkification** — Dark mode, badge pills, linked names/SHAs, header/footer

See [v1.1 Archive](milestones/v1.1-ROADMAP.md) for full details.

</details>

<details>
<summary>✅ v1.2 Detail Enrichment (Phases 6-7) — SHIPPED 2026-03-23</summary>

- [x] **Phase 6: Data Enrichment** — Bot PR status, latest repo commits, average update delay
- [x] **Phase 7: Expandable Detail Rows** — Toggle icon, inline detail panels, Expand All, dark mode CSS

See [v1.2 Archive](milestones/v1.2-ROADMAP.md) for full details.

</details>

### v1.3 Cadence Fix

- [ ] **Phase 8: Cadence Data & Computation** — Collect pointer bump history, compute cadence from bump intervals
- [ ] **Phase 9: Thresholds, Classification & Validation** — Derive thresholds from bump cadence, update classification, validate with tests

## Phase Details

### Phase 8: Cadence Data & Computation
**Goal**: Cadence is computed from pointer bump intervals in sonic-buildimage instead of submodule repo commit intervals
**Depends on**: Nothing (fix to existing Phase 2 functionality)
**Requirements**: DATA-01, DATA-02, CAD-01, CAD-02
**Success Criteria** (what must be TRUE):
  1. Collector gathers pointer bump commit history from sonic-buildimage for each submodule
  2. `compute_cadence` returns median interval between pointer bumps (not submodule repo commits)
  3. When fewer than 5 pointer bumps exist in the lookback window, fallback thresholds are applied
  4. Dashboard data JSON shows cadence values reflecting pointer bump intervals
**Plans:** 1 plan

Plans:
- [ ] 08-01-PLAN.md — Swap cadence data source to pointer bump intervals from sonic-buildimage

### Phase 9: Thresholds, Classification & Validation
**Goal**: Staleness model uses corrected cadence for thresholds and classification, all tests validate new behavior
**Depends on**: Phase 8
**Requirements**: CAD-03, CAD-04, TEST-01, TEST-02, TEST-03
**Success Criteria** (what must be TRUE):
  1. Yellow threshold is 2× median bump cadence, red threshold is 4× median bump cadence
  2. Staleness badges on the dashboard reflect thresholds derived from bump intervals
  3. All unit tests pass and validate cadence computation from pointer bump intervals
  4. No test references the old submodule-commit-based cadence definition
**Plans**: TBD

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Data Pipeline & Deployment | v1.0 | 3/3 | Complete | 2026-03-21 |
| 2. Staleness Model | v1.0 | 2/2 | Complete | 2026-03-21 |
| 3. Dashboard UI | v1.0 | 2/2 | Complete | 2026-03-21 |
| 4. Data Expansion | v1.1 | 2/2 | Complete | 2026-03-21 |
| 5. Visual Overhaul & Linkification | v1.1 | 2/2 | Complete | 2026-03-21 |
| 6. Data Enrichment | v1.2 | 2/2 | Complete | 2026-03-23 |
| 7. Expandable Detail Rows | v1.2 | 1/1 | Complete | 2026-03-23 |
| 8. Cadence Data & Computation | v1.3 | 0/? | Not started | - |
| 9. Thresholds, Classification & Validation | v1.3 | 0/? | Not started | - |
