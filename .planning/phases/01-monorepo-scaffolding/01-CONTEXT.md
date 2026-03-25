# Phase 1: Monorepo Scaffolding - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up a uv workspace monorepo with two packages: a shared core package and the existing submodule-status deliverable. Both must be installable and importable. Existing tests must pass after restructuring. No business logic changes — this is purely structural.

</domain>

<decisions>
## Implementation Decisions

### Package Naming
- Core Python import name: `sonic_buildcop_core`
- Submodule-status Python import name: `sonic_submodule_status`
- Top-level directory names: `core/` and `submodule-status/` (unchanged from current dir name)

### Directory Layout
- Use uv workspaces with `[tool.uv.workspace]` in root `pyproject.toml`
- Both packages use src-layout (PyPA standard, hatchling default)
- Core layout: `core/src/sonic_buildcop_core/__init__.py`
- Submodule-status layout: `submodule-status/src/sonic_submodule_status/`

### Existing Code Placement
- Move `submodule-status/scripts/*.py` (collector, staleness, enrichment, renderer) into `submodule-status/src/sonic_submodule_status/` as flat modules
- Move `submodule-status/templates/` into `submodule-status/src/sonic_submodule_status/templates/` (included in package via `__file__`)
- Tests stay at `submodule-status/tests/` (standard pytest layout, outside src/)
- Existing `submodule-status/requirements.txt` replaced by `pyproject.toml` dependencies

### Core Skeleton Scope
- Minimal: just `__init__.py` with a `__version__` string
- No placeholder modules — Phases 2-3 add real code
- Core exists to prove the workspace wiring works

### Entry Points
- Define console script entry points in submodule-status `pyproject.toml`:
  - `collect-submodules` → `sonic_submodule_status.collector:main`
  - `render-dashboard` → `sonic_submodule_status.renderer:main`
- Replaces `python scripts/collector.py` invocation pattern

### Build Backend
- hatchling (uv default, handles src-layout natively)

### Test Constraint
- All existing tests must pass after scaffolding — import paths updated accordingly
- The `sys.path.insert` hack in `conftest.py` will be replaced by proper package imports

### Claude's Discretion
- Exact `pyproject.toml` field values (project metadata, classifiers, etc.)
- Whether to include a `py.typed` marker for type-checking support
- `uv.lock` inclusion/exclusion in `.gitignore`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Research Artifacts
- `.planning/research/ARCHITECTURE.md` — uv workspace directory layout patterns, src-layout details, CI migration steps
- `.planning/research/PITFALLS.md` — Packaging pitfalls (#5: sys.path removal must be atomic, #8: conftest.py dual import paths)
- `.planning/research/STACK.md` — uv 0.11.1 workspace config, hatchling 1.29 build backend details

### Existing Codebase
- `.planning/codebase/STRUCTURE.md` — Current directory layout being restructured
- `.planning/codebase/CONCERNS.md` — "No Proper Python Packaging" tech debt section
- `.planning/codebase/CONVENTIONS.md` — Naming conventions to preserve

### Source Files to Move
- `submodule-status/scripts/collector.py` — Main entry point, has `main()` for entry point wiring
- `submodule-status/scripts/renderer.py` — Second entry point, has `main()` for entry point wiring
- `submodule-status/tests/conftest.py` — Has `sys.path.insert` hack that must be removed

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `submodule-status/scripts/*.py` (4 files): Move as-is into new package layout
- `submodule-status/templates/dashboard.html`: Move into package for `__file__`-relative access
- `submodule-status/tests/` (5 files): Keep at same relative position, update imports

### Established Patterns
- All imports are flat within `scripts/` — `from staleness import enrich_with_staleness`
- These become `from sonic_submodule_status.staleness import enrich_with_staleness` after move
- `conftest.py` uses `sys.path.insert(0, ...)` to resolve `scripts/` — will be replaced by package install
- `renderer.py` uses `os.path.dirname(__file__)` for template path — still works after move if templates move with it

### Integration Points
- `.github/workflows/update-dashboard.yml` — must update `working-directory`, `pip install` → `uv sync`, script invocation → entry point
- `.gitignore` — may need updates for `uv.lock`, build artifacts

</code_context>

<specifics>
## Specific Ideas

No specific requirements — decisions above fully define the structure.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-monorepo-scaffolding*
*Context gathered: 2026-03-25*
