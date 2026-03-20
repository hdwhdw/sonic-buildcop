# Project Research Summary

**Project:** sonic-buildcop (GitHub submodule staleness dashboard)
**Domain:** Static CI/CD dashboard — GitHub Actions ETL pipeline → GitHub Pages
**Researched:** 2025-07-18
**Confidence:** HIGH (stack and pitfalls verified against live APIs and actual repo data; architecture validated against sonic-buildimage structure)

## Executive Summary

sonic-buildcop is a static staleness dashboard for the 31 sonic-net submodules in `sonic-net/sonic-buildimage`. The canonical architecture is a **linear ETL pipeline** executed as a single GitHub Actions cron job: a data-collection script fetches submodule pointers and upstream HEADs from the GitHub REST API, a cadence analyzer computes per-submodule staleness thresholds from historical update intervals, a site generator produces a single HTML page, and the output is committed to `docs/` for GitHub Pages to serve. No servers, no databases, no build toolchain — just Python (or Node.js) scripts plus CDN-loaded Chart.js and Pico CSS. The entire pipeline completes in under two minutes and uses ~6% of the hourly GitHub API rate limit.

The **core differentiator** — and the hardest thing to get right — is cadence-aware staleness thresholds. Fixed thresholds (e.g., "red after 30 days") are useless because sonic-buildimage's submodules range from daily-updated (`sonic-swss`) to once-a-year (`sonic-ztp`). The algorithm must compute a per-submodule `medianInterval` from commit history and set `yellow = 2×median`, `red = 4×median` with minimum floors. This requires careful handling of sparse data (submodules with fewer than 5 historical updates must fall back to a global default) and statistical robustness (use median over mean to resist outlier gaps like holiday periods).

The biggest risks are operational, not algorithmic. Three verified pitfalls can corrupt the entire dataset silently: comparing against the wrong upstream branch (3 of 31 submodules track a non-default branch), URL normalization errors in `.gitmodules` parsing (`rstrip('.git')` mangles names — use `removesuffix('.git')`), and the dashboard going stale itself when GitHub disables the workflow after 60 days of repo inactivity. All three must be addressed in Phase 1 before a single line of UI code is written.

---

## Key Findings

### Recommended Stack

The stack is intentionally minimal — zero infrastructure footprint. **STACK.md recommends Python 3.12**; **ARCHITECTURE.md recommends Node.js 20 with `@octokit/rest`**. This is the only cross-file conflict in the research. Both are valid; the decision should be made in Phase 1 (see Research Flags). The rest of the stack is unambiguous:

**Core technologies:**
- **Python 3.12 OR Node.js 20**: Data collection + analysis scripts — Python wins on "zero setup" (pre-installed on `ubuntu-latest`, `configparser` parses `.gitmodules` natively); Node.js wins on `@octokit/rest` auto-handling auth/retry and native `Promise.allSettled` for concurrency
- **GitHub REST API v3**: The only viable API — `GET /compare/` (staleness counts), `GET /contents/` (pinned SHAs), `GET /commits?path=` (cadence history) — GraphQL cannot replicate `/compare/`
- **`git ls-remote`**: Upstream HEAD resolution for all 31 submodules — uses git protocol directly, **zero REST API quota impact**
- **Chart.js 4.5.1** (CDN): Horizontal bar charts for commits-behind visualization — 70KB, declarative, no build step
- **Pico CSS 2.1.1** (CDN): Base styling — classless, semantic HTML gets styled automatically, no CSS maintenance
- **`actions/deploy-pages` v4.0.5** OR **commit to `docs/`**: GitHub Pages deployment — deploy-pages requires no git history pollution; docs/ commit is simpler and gives free git history of dashboard states

**Critical version/config notes:**
- `actions/checkout` must NOT use `submodules: true` — sonic-buildimage would trigger a multi-GB clone
- GitHub Pages must be set to "GitHub Actions" source OR `docs/` folder (not branch-based)
- Workflow needs `contents: write` permission to commit generated files back to repo

### Expected Features

**Must have (table stakes) — v1 launch:**
- Submodule listing with pinned SHA, commits-behind count, days-behind — the core data
- Cadence-aware color badges (green/yellow/red with icon fallback for accessibility) — requires cadence thresholds
- Summary header: "X critical / Y warning / Z healthy" — 2-second project health read
- Compare view links (`github.com/{repo}/compare/{pinned}...HEAD`) — one-click investigation
- Sort by severity descending (default) + name/commits/days columns — worst-first ordering
- Last-refreshed timestamp prominently displayed — non-negotiable trust signal
- Self-stale check in browser JS — warn if data is >48 hours old
- Daily GitHub Actions cron + `workflow_dispatch` manual trigger
- GitHub Pages deployment at stable URL

**Should have (differentiators) — v1.x after validation:**
- Team ownership grouping via CODEOWNERS parsing (~6 teams in sonic-buildimage)
- Update cadence sparklines — makes "why is this yellow?" self-answering
- JSON data endpoint (`docs/data.json`) — enables downstream consumers; near-zero extra effort
- Historical JSON snapshots — **start collecting day 1** even if visualization is deferred (you can't backfill)
- Commit diff summary (first N missed commits) — transforms "42 commits behind" into actionable context

**Defer to v2+:**
- Historical trend charts — needs months of accumulated snapshot data before useful
- GitHub Issues / Slack alerting — validate thresholds are meaningful first; premature alerting = noise
- Bot PR status integration — `mssonicbld` already creates PRs; show their status alongside staleness
- External submodule tracking (non-sonic-net) — different ownership model, dilutes the signal
- CI gates blocking merges — needs very high threshold confidence before enforcement

**Explicit anti-features (never add):**
- Auto-update submodule pointers — conflates observability with automation, destroys trust
- Database backend — 31 rows × daily snapshots = a JSON file
- Any JS framework (React, Vue, Svelte) — single page, no routing, zero benefit over vanilla HTML
- GitHub GraphQL API exclusively — `/compare/` is REST-only

### Architecture Approach

The architecture is a **4-stage linear ETL pipeline** implemented as a single GitHub Actions job. Data flows strictly forward: GitHub API/git → `raw-data.json` → `cadence-data.json` → `docs/index.html` + `docs/data.json`. Intermediate JSON files enable independent debugging and stage re-running without repeating expensive API calls. History is accumulated in `data/history.json` committed to the repo — git serves as the database.

**Major components:**
1. **`collect.js` / `collect.py`** — Discovers submodules from `.gitmodules` (API), resolves pinned SHAs (tree API), computes commits-behind (compare API), date-behind (from compare `base_commit.date`). Writes `raw-data.json`.
2. **`analyze.js` / `analyze.py`** — Fetches update history per submodule (`/commits?path=`), computes median interval, derives yellow/red thresholds (2×/4× median with 7d/14d floors), classifies each submodule. Appends to `data/history.json`. Writes `cadence-data.json`.
3. **`render.js` / `render.py`** — Reads `cadence-data.json`, generates `docs/index.html` (table + Chart.js bar chart) and `docs/data.json` (machine-readable output). Pico CSS and Chart.js loaded from CDN.
4. **GitHub Actions workflow** — Orchestrates all stages, passes `GITHUB_TOKEN`, commits output, deploys to Pages. Concurrency group prevents overlapping runs.

### Critical Pitfalls

1. **Wrong branch comparison** — 3 of 31 submodules track non-default branches (`frr-10.4.1`, `sdk-6.5.22-gpl-dnx`, `master`). Always read `branch` field from `.gitmodules`; query each repo's `default_branch` via API for the rest. Using wrong branch causes ~500 false-stale or false-fresh results. **Phase 1.**

2. **`.gitmodules` URL parsing (`rstrip` vs `removesuffix`)** — URLs inconsistently end with `.git` (25 repos) or not (23 repos). `str.rstrip('.git')` treats the argument as a character set and mangles names ending in `g`, `i`, `t`, `.` (e.g., `sonic-snmpagent` → `sonic-snmpagen`, causing 404s). Use `str.removesuffix('.git')`. **Phase 1.**

3. **Cadence fails on sparse data** — Some submodules have ≤2 update events in recent history. Statistical thresholds on N<5 samples are meaningless noise. Enforce minimum N≥5; fall back to global default (e.g., 30-day yellow, 90-day red) for insufficient data. Flag these submodules in the UI. Use median over mean (robust to 94-day holiday gaps observed in `sonic-swss`). **Phase 2.**

4. **The dashboard going stale (meta-irony)** — GitHub disables scheduled workflows after 60 days of repo inactivity. Workflow failures don't notify by default. Prevention: commit `data/history.json` on every run (creates activity), add a browser-side freshness check that warns if data is >48 hours old, add `if: failure()` notification step, show explicit last-updated timestamp. **Phase 1.**

5. **Accidentally cloning sonic-buildimage** — `actions/checkout` with `submodules: true` would trigger a 2GB+ clone. Use GitHub REST API for `.gitmodules` content and submodule pointer SHAs; use `git ls-remote` (git protocol, no API quota) for upstream HEADs. Never `git clone` or `git submodule update`. **Phase 1.**

---

## Implications for Roadmap

Based on combined research, the architecture researcher's 4-phase build order is well-justified by component dependencies. Phases 1-3 are v1; Phase 4 is v2 scope.

### Phase 1: Foundation — Pipeline Skeleton + Correct Data

**Rationale:** All downstream features (badges, charts, trends) are worthless if the raw staleness data is wrong. The three critical pitfalls (wrong branch, URL parsing, submodule clone) all manifest here. Get data right before building any UI.

**Delivers:** Working end-to-end pipeline. Daily cron collects data, generates a bare-bones HTML table, deploys to GitHub Pages. Data is correct. Dashboard has last-updated timestamp and self-stale check.

**Addresses (from FEATURES.md):** Submodule listing, commits-behind, days-behind, compare links, timestamp, sort by severity, Pages deployment, `workflow_dispatch`

**Avoids (from PITFALLS.md):**
- Pitfall 1 (wrong branch) — hardcoded branch handling from day 1
- Pitfall 2 (URL normalization) — `removesuffix('.git')`, URL as source of truth
- Pitfall 4 (dashboard staleness) — mandatory timestamp + history.json commit for keep-alive
- Pitfall 5 (clone prevention) — API-only data collection, `git ls-remote` for HEADs
- Pitfall 7 (compare API limit) — use `ahead_by` field, not commit iteration
- Pitfall 8 (wrong date metric) — `date(upstream HEAD) - date(pinned)`, not `now() - date(pinned)`
- Pitfall 10 (Jekyll) — `.nojekyll` file in deployed output
- Pitfall 12 (concurrent runs) — concurrency group in workflow YAML
- Pitfall 14 (hardcoded list) — dynamic discovery from `.gitmodules`

**Uses (from STACK.md):** Python/Node.js (decision made here), GitHub REST API, `requests`/`@octokit/rest`, `actions/checkout` (no submodules), `actions/configure-pages`/`upload-pages-artifact`/`deploy-pages`

**⚠️ Research flag:** Language choice (Python vs Node.js) must be decided here. STACK.md prefers Python; ARCHITECTURE.md prefers Node.js. See Gaps section.

---

### Phase 2: Cadence-Aware Staleness Model

**Rationale:** This is THE differentiator and the reason the project exists. Without it, the dashboard is just a worse `git submodule status`. Must be built on top of stable Phase 1 data schema. Color badges are meaningless until thresholds are computed.

**Delivers:** Per-submodule dynamic thresholds based on historical update cadence. Color-coded badges (green/yellow/red + icons). Fallback thresholds for sparse-data submodules. Summary header with aggregate counts. Start accumulating `data/history.json` snapshots even if trend visualization is deferred.

**Addresses (from FEATURES.md):** Cadence-aware thresholds (P1 differentiator), color-coded badges (P1 table stakes), summary/aggregate counts (P1 table stakes), historical JSON snapshot collection (start now, visualize later)

**Avoids (from PITFALLS.md):**
- Pitfall 3 (sparse cadence data) — minimum N≥5 sample size, global fallback, IQR-based thresholds, flag uncertain submodules in UI
- Pitfall 6 (secondary rate limits) — serial requests with 100-200ms delay, respect `Retry-After`
- Pitfall 11 (cron timing) — idempotent generation (same data = no commit)

**Implements (from ARCHITECTURE.md):** `analyze.js`/`analyze.py`, `data/history.json` initialization, staleness classification algorithm (median interval × 2/4 with 7d/14d floors)

---

### Phase 3: Dashboard UI Polish

**Rationale:** Data is correct and thresholds are validated; now make the dashboard actually pleasant and useful for maintainers. CODEOWNERS team grouping adds a distinct organizational layer that no comparable tool provides.

**Delivers:** Responsive layout, horizontal bar chart (Chart.js) for commits-behind visualization, CODEOWNERS team grouping (~6 teams), client-side column sorting, accessible badges (color + icon + label), update cadence sparklines, JSON data endpoint (`docs/data.json`) for downstream consumers.

**Addresses (from FEATURES.md):** Team ownership grouping (P2), update cadence visualization (P2), JSON data endpoint (P2), responsive layout (P1 table stakes), staleness heatmap (P2)

**Avoids (from PITFALLS.md):**
- Pitfall 9 (archived/renamed repos) — "⚠️ Repo unavailable" badge for non-200 API responses
- Pitfall 13 (treating all submodules equally) — sort by severity, group by activity level, allow collapsing green rows

**Uses (from STACK.md):** Chart.js 4.5.1 (CDN), Pico CSS 2.1.1 (CDN), vanilla JS `<script>` for client-side sorting

---

### Phase 4: History & Trends (v2 scope)

**Rationale:** Requires 2-3 months of accumulated `data/history.json` snapshots before trend charts have meaningful data. Cannot be meaningfully built until Phase 1+2 have been running for months.

**Delivers:** Historical trend charts showing each submodule's staleness over time, "getting better/worse" trend indicator, bot PR status integration (check if `mssonicbld` has an open PR for each stale submodule).

**Addresses (from FEATURES.md):** Historical trend charts (P3), bot PR status integration (P3)

**Note:** Start collecting `data/history.json` in Phase 2 — you can't backfill. Phase 4 only adds the visualization layer on top of data already being accumulated.

---

### Phase Ordering Rationale

- **Data before display:** Phases 1→2 establish correct data and thresholds before any UI investment. Building UI on wrong data wastes effort and erodes trust.
- **Core differentiator early:** The cadence model (Phase 2) is what makes this project worth building. It must be in v1, not deferred.
- **Accumulate early, visualize later:** `data/history.json` snapshots should start in Phase 2 even though trend visualization is Phase 4. This is the only time-dependent feature — you cannot retroactively collect historical data.
- **UI polish is the last dependency:** Phase 3 depends on final data schema (cadence fields from Phase 2). Changing the schema after UI is built is expensive.

### Research Flags

**Needs deeper research during planning:**
- **Phase 1 (language choice):** STACK.md (Python) vs ARCHITECTURE.md (Node.js) conflict must be resolved. Key question: does `@octokit/rest`'s auto-retry and pagination justify Node.js over Python's pre-installed simplicity? Recommend a quick spike: prototype the `.gitmodules` parser and one API call in both languages before committing.
- **Phase 2 (cadence algorithm validation):** The median×2/median×4 multipliers are reasonable starting points but untested on the full 31-submodule dataset. Recommend running the algorithm against live data before building the UI around its output.

**Standard patterns (skip research-phase):**
- **Phase 1 (workflow structure):** Well-documented GitHub Actions patterns. The YAML skeleton in STACK.md and ARCHITECTURE.md is copy-paste ready.
- **Phase 3 (frontend rendering):** Vanilla HTML with Chart.js and Pico CSS is a fully-solved problem. No research needed.
- **Phase 4 (history trends):** Straightforward Chart.js line charts. Only complexity is data schema design, which is already defined in ARCHITECTURE.md.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified live against CDN and GitHub Releases API on 2025-07-18. One unresolved conflict: Python vs Node.js — both are valid, decision is implementation preference |
| Features | MEDIUM | No direct competitor products exist; features synthesized from adjacent tools (Dependabot, Renovate, libyear). Table stakes features are unambiguous; differentiator features are well-reasoned but untested with actual users |
| Architecture | HIGH | ETL pipeline pattern validated against actual sonic-buildimage repo structure. API call counts verified. Cadence algorithm validated against real update history data |
| Pitfalls | HIGH | All critical pitfalls verified against live data: wrong branch (tested on sonic-frr), URL parsing (rstrip bug confirmed), clone size (826MB repo), 60-day disable policy (GitHub docs). Cadence pitfall confirmed from actual `sonic-swss`/`sonic-dbsyncd` update history |

**Overall confidence:** HIGH

### Gaps to Address

- **Python vs Node.js decision:** The two most thorough research files conflict. STACK.md chose Python for zero-install simplicity and stdlib richness. ARCHITECTURE.md chose Node.js for `@octokit/rest`. Resolve in Phase 1 planning with a quick prototype. **Lean toward Node.js** if the architecture researcher designed around its concurrency model (`Promise.allSettled` + `p-limit`); lean toward Python if simplicity and reproducibility (no `npm install`) are priorities.

- **Cadence algorithm multiplier validation:** The `2×` and `4×` multipliers (yellow/red thresholds) are theoretically sound but should be validated against the live dataset before being shipped as the UX. Run the algorithm on all 31 submodules and sanity-check: does `sonic-swss` compute to 7/14 day thresholds? Does `sonic-ztp` compute to 180/360 days? This takes 30 minutes of manual verification.

- **CODEOWNERS coverage:** ~6 teams are visible in CODEOWNERS, but some submodule paths may map to individual users rather than teams. Coverage of the 31 sonic-net submodule paths in CODEOWNERS should be validated before Phase 3 team grouping is designed.

- **History snapshot schema lock-in:** `data/history.json` schema defined in ARCHITECTURE.md should be finalized before Phase 2 ships — changing it later requires migrating accumulated data. The schema looks clean but needs explicit versioning.

---

## Sources

### Primary (HIGH confidence — live verified)
- **sonic-net/sonic-buildimage `.gitmodules`** — 49 submodules enumerated, 31 sonic-net confirmed, name/path/URL mismatches verified, 3 branch-tracking submodules identified
- **GitHub REST API (live)** — Contents, Compare, Commits, Git Trees endpoints tested against sonic-net repos on 2025-07-18. `ahead_by` accuracy at 1,319-commit divergence confirmed.
- **Chart.js 4.5.1** — Version confirmed via `cdn.jsdelivr.net/npm/chart.js@latest` HTTP header
- **Pico CSS 2.1.1** — Version confirmed via `cdn.jsdelivr.net/npm/@picocss/pico@latest` HTTP header
- **GitHub Actions versions** — All confirmed via GitHub Releases API
- **Python 3.12 + requests 2.31** — Verified on ubuntu environment matching `ubuntu-latest` runner
- **sonic-buildimage update history** — Cadence data: sonic-swss=55 updates/yr (8-day median), sonic-dbsyncd=2 updates/yr (87-day interval), sonic-ztp ~quarterly cadence. Used to validate threshold algorithm.

### Secondary (MEDIUM confidence — training data / docs)
- **GitHub Actions documentation** — 60-day workflow disable policy, cron scheduling delays (5-15 min), concurrency groups
- **GitHub Pages documentation** — Jekyll processing, `.nojekyll` file behavior, `actions/deploy-pages` permissions
- **GitHub API rate limits** — 60/hr unauthenticated, 5,000/hr PAT, 1,000/hr GITHUB_TOKEN (from docs + training data, not live rate-limit testing)
- **Dependabot, Renovate, libyear, deps.dev** — Analyzed for feature pattern inspiration; no direct competitor exists for git submodule staleness dashboards

### Tertiary (LOW confidence — inference)
- **CODEOWNERS team coverage** — ~6 teams inferred from FEATURES.md analysis; exact coverage of all 31 submodule paths not validated
- **Cadence multiplier appropriateness** — `2×`/`4×` multipliers are principled but require validation against actual submodule data

---
*Research completed: 2025-07-18*
*Ready for roadmap: yes*
