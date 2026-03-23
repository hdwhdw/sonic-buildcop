# Roadmap: sonic-buildcop

## Milestones

- ✅ **v1.0** — Submodule Staleness Dashboard (Phases 1-3, 7 plans) → [Archive](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1** — Dashboard Polish (Phases 4-5, 4 plans) → [Archive](milestones/v1.1-ROADMAP.md)
- 🚧 **v1.2** — Detail Enrichment (Phases 6-7)

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

### 🚧 v1.2 Detail Enrichment

**Milestone Goal:** Add expandable detail rows showing bot PR status, pointer update history, and repo activity — making each row actionable without cluttering the main table.

- [ ] **Phase 6: Data Enrichment** — Collector fetches bot PR status, latest repo commits, and computes update delay
- [ ] **Phase 7: Expandable Detail Rows** — Clickable rows with inline detail panel showing PR status, pointer history, repo activity

## Phase Details

### Phase 6: Data Enrichment
**Goal**: Collector outputs all detail data that expandable rows will display
**Depends on**: Phase 5 (existing collector infrastructure)
**Requirements**: ENRICH-01, ENRICH-02, ENRICH-03, ENRICH-04
**Success Criteria** (what must be TRUE):
  1. Running the collector produces JSON containing open bot PR info (URL, age, CI status) for each submodule that has one, and null for those without
  2. JSON includes the last merged bot PR (URL, merge date) for each submodule
  3. JSON includes the latest commit (URL, date) from each submodule's own repo
  4. JSON includes average delay in days between repo commits and pointer bumps for each submodule
**Plans**: 2 plans

Plans:
- [ ] 06-01-PLAN.md — Bot PR enrichment + latest commits (ENRICH-01, ENRICH-02, ENRICH-03)
- [ ] 06-02-PLAN.md — Average delay + collector integration (ENRICH-04)

### Phase 7: Expandable Detail Rows
**Goal**: Users can click any dashboard row to see actionable detail without leaving the page
**Depends on**: Phase 6
**Requirements**: EXPAND-01, EXPAND-02, EXPAND-03, EXPAND-04, EXPAND-05
**Success Criteria** (what must be TRUE):
  1. Clicking a submodule row toggles an inline detail panel below it; clicking again collapses it
  2. Detail panel shows open bot PR with clickable link, age badge, and CI status (pass/fail/pending) — or "No open PR" if none exists
  3. Detail panel shows last pointer update date linked to the merged bot PR
  4. Detail panel shows last repo commit date linked to the commit on GitHub
  5. Detail panel shows average delay between repo commits and pointer bumps
**Plans**: TBD

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Data Pipeline & Deployment | v1.0 | 3/3 | Complete | 2026-03-21 |
| 2. Staleness Model | v1.0 | 2/2 | Complete | 2026-03-21 |
| 3. Dashboard UI | v1.0 | 2/2 | Complete | 2026-03-21 |
| 4. Data Expansion | v1.1 | 2/2 | Complete | 2026-03-21 |
| 5. Visual Overhaul & Linkification | v1.1 | 2/2 | Complete | 2026-03-21 |
| 6. Data Enrichment | v1.2 | 0/? | Not started | - |
| 7. Expandable Detail Rows | v1.2 | 0/? | Not started | - |
