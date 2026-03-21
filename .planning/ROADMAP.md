# Roadmap: sonic-buildcop

## Milestones

- ✅ **v1.0** — Submodule Staleness Dashboard (Phases 1-3, 7 plans) → [Archive](milestones/v1.0-ROADMAP.md)
- 🚧 **v1.1** — Dashboard Polish (Phases 4-5)

## Phases

<details>
<summary>✅ v1.0 Submodule Staleness Dashboard (Phases 1-3) — SHIPPED 2026-03-21</summary>

- [x] **Phase 1: Data Pipeline & Deployment** — Collector, renderer, CI/CD
- [x] **Phase 2: Staleness Model** — Cadence-aware thresholds and classification
- [x] **Phase 3: Dashboard UI** — Sort, summary, CSS polish

See [v1.0 Archive](milestones/v1.0-ROADMAP.md) for full details.

</details>

### 🚧 v1.1 Dashboard Polish

- [ ] **Phase 4: Data Expansion** — Track all 31 submodules with cadence metrics and human-readable timestamps
- [ ] **Phase 5: Visual Overhaul & Linkification** — Professional styling, dark mode, and everything linked to GitHub

## Phase Details

### Phase 4: Data Expansion
**Goal**: Dashboard shows comprehensive staleness data for all 31 sonic-net submodules with cadence metrics and human-readable timestamps
**Depends on**: Phase 3 (v1.0 dashboard)
**Requirements**: DATA-09, DATA-07, DATA-08, DATA-10
**Success Criteria** (what must be TRUE):
  1. Dashboard displays all 31 sonic-net submodules from sonic-buildimage (not just the original 10)
  2. Each submodule row shows its median cadence (e.g., "~1.2 days")
  3. Each submodule row shows its staleness thresholds (e.g., "yellow: 2d / red: 5d")
  4. "Last updated" timestamp displays as relative time (e.g., "3 hours ago") instead of ISO 8601
**Plans**: 2 plans

Plans:
- [ ] 04-01-PLAN.md — Expand collector to all sonic-net submodules (DATA-09)
- [ ] 04-02-PLAN.md — Add cadence columns and human-friendly timestamps (DATA-07, DATA-08, DATA-10)

### Phase 5: Visual Overhaul & Linkification
**Goal**: Dashboard looks professional with consistent styling, dark mode support, and every entity linked to its GitHub source
**Depends on**: Phase 4
**Requirements**: VIS-01, VIS-02, VIS-03, VIS-04, LINK-01, LINK-02, LINK-03, LINK-04
**Success Criteria** (what must be TRUE):
  1. Submodule names are clickable links to their GitHub repos (e.g., sonic-net/sonic-gnmi)
  2. Pinned SHA values link to the exact commit on GitHub
  3. Path column is removed or replaced with a direct link to the submodule directory in sonic-buildimage
  4. Page has a header with project title/description and a footer linking to the source repo
  5. Dashboard renders with professional CSS (system fonts, refined borders, row hover), colored status pills (not plain text), and correct colors in both light and dark mode
**Plans**: 2 plans

Plans:
- [ ] 05-01-PLAN.md — Linkification + structural changes (LINK-01, LINK-02, LINK-03, LINK-04, VIS-04)
- [ ] 05-02-PLAN.md — CSS overhaul + dark mode (VIS-01, VIS-02, VIS-03)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Data Pipeline & Deployment | v1.0 | 3/3 | Complete | 2026-03-21 |
| 2. Staleness Model | v1.0 | 2/2 | Complete | 2026-03-21 |
| 3. Dashboard UI | v1.0 | 2/2 | Complete | 2026-03-21 |
| 4. Data Expansion | v1.1 | 0/? | Not started | - |
| 5. Visual Overhaul & Linkification | v1.1 | 0/? | Not started | - |
