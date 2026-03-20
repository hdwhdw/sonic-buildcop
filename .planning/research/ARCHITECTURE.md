# Architecture Patterns

**Domain:** GitHub Actions-powered static staleness dashboard for git submodules
**Researched:** 2026-03-21
**Confidence:** HIGH (verified against actual sonic-buildimage repo structure and GitHub API behavior)

## Recommended Architecture

**Pattern: Linear ETL Pipeline with Static Output**

The dashboard follows a classic Extract–Transform–Load pipeline executed as a single GitHub Actions workflow. Data flows in one direction: GitHub API/git → raw data → computed metrics → static HTML → GitHub Pages. No servers, no databases, no runtime dependencies.

```
┌─────────────────────────────────────────────────────────────┐
│              GitHub Actions Cron Workflow                     │
│              (daily + manual dispatch)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  Stage 1: DATA COLLECTION           │
         │                                     │
         │  Inputs:                            │
         │    - GitHub API (tree, .gitmodules)  │
         │    - git ls-remote (upstream HEADs)  │
         │    - GitHub Compare API (diff stats) │
         │                                     │
         │  Outputs: raw-data.json             │
         │    { submodules: [{                 │
         │        name, path, url,             │
         │        pointerSha, upstreamSha,     │
         │        commitsBehind, daysBehind,   │
         │        pointerDate, upstreamDate    │
         │    }] }                             │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  Stage 2: CADENCE ANALYSIS          │
         │                                     │
         │  Inputs:                            │
         │    - raw-data.json                  │
         │    - GitHub Commits API (history)    │
         │    - data/history.json (accumulated) │
         │                                     │
         │  Outputs: cadence-data.json         │
         │    { submodules: [{                 │
         │        ...raw fields,               │
         │        medianIntervalDays,          │
         │        yellowThresholdDays,         │
         │        redThresholdDays,            │
         │        status: green|yellow|red     │
         │    }] }                             │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  Stage 3: STATIC SITE GENERATION    │
         │                                     │
         │  Inputs: cadence-data.json          │
         │                                     │
         │  Outputs:                           │
         │    - docs/index.html                │
         │    - docs/data.json (for JS sort)   │
         │    - data/history.json (appended)   │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │  Stage 4: DEPLOY                    │
         │                                     │
         │  - Commit updated files to repo     │
         │  - GitHub Pages serves docs/        │
         └────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With | I/O |
|-----------|---------------|-------------------|-----|
| **Workflow** (`.github/workflows/update.yml`) | Orchestrate pipeline stages, manage secrets, schedule | All scripts | Triggers scripts, passes `GITHUB_TOKEN` |
| **Data Collector** (`scripts/collect.js`) | Fetch submodule pointers, upstream HEADs, commit counts | GitHub API, git CLI | Reads: GitHub API. Writes: `raw-data.json` |
| **Cadence Analyzer** (`scripts/analyze.js`) | Compute update cadence, derive thresholds, classify staleness | GitHub API (commits history), local history file | Reads: `raw-data.json`, `data/history.json`. Writes: `cadence-data.json` |
| **Site Generator** (`scripts/render.js`) | Produce static HTML dashboard | Filesystem only | Reads: `cadence-data.json`. Writes: `docs/index.html`, `docs/data.json` |
| **History Store** (`data/history.json`) | Accumulate daily snapshots for cadence accuracy | Written by Analyzer, persisted via git commit | Append-only JSON array |
| **Config** (`scripts/config.js`) | Submodule allow-list, threshold multipliers, display settings | Imported by all scripts | Static configuration |

### Data Flow

```
GitHub API ──────────┐
  (tree endpoint)    │
                     ├──► Data Collector ──► raw-data.json
git ls-remote ───────┤                          │
  (upstream HEADs)   │                          │
                     │                          ▼
GitHub Compare API ──┘                   Cadence Analyzer ──► cadence-data.json
                                              │  ▲                  │
GitHub Commits API ──────────────────────────►│  │                  │
  (path-filtered history)                     │  │                  ▼
                                              │  │           Site Generator
data/history.json ◄───────────────────────────┘  │                  │
  (accumulated snapshots)  ────────────────────►──┘                  │
                                                                    ▼
                                                          docs/index.html
                                                          docs/data.json
                                                                    │
                                                                    ▼
                                                           GitHub Pages
```

## Data Collection Strategy

### Submodule Discovery (2 API calls)

**Step 1: Get `.gitmodules`** via GitHub Contents API:
```
GET /repos/sonic-net/sonic-buildimage/contents/.gitmodules?ref=master
```
Parse to extract `[submodule "name"]` → `path` and `url` mappings. Filter to URLs matching `github.com/sonic-net/`.

**Step 2: Get submodule pointer SHAs** via GitHub Git Trees API:
```
GET /repos/sonic-net/sonic-buildimage/git/trees/master?recursive=true
```
Filter entries where `mode === "160000"` (git submodule entries). Each entry gives `path` and `sha` (the commit the parent repo points to).

**Confidence:** HIGH — verified against actual repo. The tree endpoint returns `160000` mode entries for submodules, confirmed by `git ls-tree HEAD` showing `160000 commit <sha>` for each submodule.

### Upstream HEAD Resolution (31 calls, but free)

For each submodule, use `git ls-remote` to get the upstream HEAD without consuming API quota:

```bash
git ls-remote --heads <url> refs/heads/master
```

**Why not GitHub API?** `git ls-remote` uses the git protocol directly — it doesn't count against GitHub REST API rate limits. For 31 submodules this runs in ~15 seconds total on a GitHub Actions runner.

**Confidence:** HIGH — verified: `git ls-remote --heads https://github.com/sonic-net/sonic-swss.git refs/heads/master` returns the HEAD SHA in <1 second.

### Commit Delta Calculation (31 API calls)

For each submodule where `pointerSha !== upstreamSha`, use the Compare API:

```
GET /repos/sonic-net/{repo}/compare/{pointerSha}...master
```

Response includes `ahead_by` (commits upstream has that pointer doesn't = our "commits behind" metric) and `total_commits`. The `ahead_by` field is accurate even when the commit list is truncated at 250 entries.

**Edge case:** If the pointer SHA is very old or has been force-pushed away, the compare API returns 404. Handle by falling back to "unknown" status and flagging for manual review.

**Confidence:** HIGH — GitHub Compare API docs confirm `ahead_by`/`behind_by` are always returned. Truncation only affects the `commits[]` array, not the counts.

### Date-Behind Calculation (0 additional API calls)

The Compare API response includes the `base_commit` (pointer) and the latest commit. Extract `committer.date` from each to compute `daysBehind = (upstreamDate - pointerDate) / MS_PER_DAY`.

### Historical Cadence (31 API calls)

For cadence calculation, query the parent repo's commit history filtered by submodule path:

```
GET /repos/sonic-net/sonic-buildimage/commits?path=src/sonic-swss&per_page=30&sha=master
```

This returns the last 30 commits that touched the submodule pointer. From the commit dates, compute the median interval between updates.

**Important nuance from actual data:** sonic-buildimage submodule paths are inconsistent:
- Some are at `src/sonic-swss` (most common)
- Some are at `platform/broadcom/saibcm-modules-dnx`
- Some are at `platform/alpinevs` or `platform/vpp`
- The `.gitmodules` `path` field is the source of truth

**Confidence:** HIGH — verified by running `git log --format='%aI' -- src/sonic-swss` against the actual repo and observing consistent cadence data.

### Total API Budget Per Run

| Operation | Calls | Rate Limit Impact |
|-----------|-------|-------------------|
| Get .gitmodules content | 1 | REST API |
| Get tree (recursive) | 1 | REST API |
| Compare API (per submodule, only if behind) | ≤31 | REST API |
| Commits history (per submodule) | 31 | REST API |
| git ls-remote (per submodule) | 31 | **None** (git protocol) |
| **Total REST API calls** | **~64** | **of 1,000/hour limit** |

GitHub Actions workflows get 1,000 REST API requests/hour with `GITHUB_TOKEN`. At 64 calls per run, we use **6.4% of budget** — enormous headroom. Even running hourly would be safe.

## Cadence-Aware Staleness Model

### The Problem

Fixed thresholds don't work for sonic-buildimage. Verified from actual data:
- **sonic-swss**: Updated nearly daily. 5 days behind = concerning.
- **sonic-ztp**: Updated every few months. 30 days behind after one commit = normal.

### The Algorithm

For each submodule:

1. **Collect update timestamps** from the last N parent-repo commits touching that submodule path
2. **Compute intervals** between consecutive updates (in days)
3. **Calculate median interval** (robust to outliers — e.g., holiday gaps)
4. **Derive thresholds:**
   - `yellowThreshold = medianInterval × 2.0` (2× the normal cadence)
   - `redThreshold = medianInterval × 4.0` (4× the normal cadence)
   - Floor: `yellowThreshold >= 7 days`, `redThreshold >= 14 days` (prevent over-alerting on hyper-active submodules)

5. **Classify:**
   - 🟢 **Green:** `daysBehind < yellowThreshold` — within normal cadence
   - 🟡 **Yellow:** `yellowThreshold ≤ daysBehind < redThreshold` — drifting, needs attention
   - 🔴 **Red:** `daysBehind ≥ redThreshold` — stale, action required

### Example (from actual data)

**sonic-swss** (high cadence):
- Recent updates: Mar 21, Mar 19, Mar 18, Mar 15, Mar 14, Mar 13, Mar 1, Feb 25, Feb 19...
- Median interval: ~2 days
- Yellow threshold: max(4 days, 7 days) = **7 days**
- Red threshold: max(8 days, 14 days) = **14 days**

**sonic-ztp** (low cadence):
- Recent updates: Mar 18, Feb 17, Feb 15, Jul 2025, Jul 2024, Feb 2024...
- Median interval: ~90 days
- Yellow threshold: **180 days**
- Red threshold: **360 days**

### History Accumulation

The `data/history.json` file accumulates daily snapshots to improve cadence accuracy over time. Structure:

```json
{
  "snapshots": [
    {
      "date": "2026-03-21",
      "submodules": {
        "src/sonic-swss": { "pointerSha": "c20ded7...", "commitsBehind": 0, "daysBehind": 0 },
        ...
      }
    }
  ]
}
```

**File size management:** Keep only the last 365 snapshots (~200KB for 31 submodules). Older entries are pruned on each run.

## Recommended Project Structure

```
sonic-buildcop/                        # hdwhdw/sonic-buildcop repo
├── .github/
│   └── workflows/
│       └── update-dashboard.yml       # Cron + manual dispatch workflow
├── scripts/
│   ├── collect.js                     # Stage 1: Data collection
│   ├── analyze.js                     # Stage 2: Cadence analysis + classification
│   ├── render.js                      # Stage 3: HTML generation
│   └── config.js                      # Shared configuration
├── templates/
│   └── dashboard.html                 # HTML template (or inline in render.js)
├── data/
│   └── history.json                   # Accumulated daily snapshots (committed)
├── docs/                              # GitHub Pages source directory
│   ├── index.html                     # Generated dashboard (committed)
│   └── data.json                      # Machine-readable dashboard data (committed)
├── package.json                       # Node.js dependencies (octokit)
├── package-lock.json
└── README.md
```

**Why `docs/` for GitHub Pages:** GitHub Pages can serve from either root or `docs/` folder. Using `docs/` keeps generated output separate from source code. No need for a separate `gh-pages` branch — simpler git history.

**Confidence:** HIGH — `docs/` folder deployment is a standard GitHub Pages option available in repo settings.

## Patterns to Follow

### Pattern 1: Single-Workflow Linear Pipeline
**What:** Run all stages sequentially in one GitHub Actions job rather than using separate jobs or workflow dispatch chains.

**When:** Pipeline is fast (<5 min total) and stages are tightly coupled.

**Why:** For ~64 API calls + HTML rendering, the entire pipeline runs in under 2 minutes. Separate jobs add overhead (runner spin-up, artifact passing) without benefit. A single job also means a single `GITHUB_TOKEN` context — no token-passing complexity.

```yaml
# .github/workflows/update-dashboard.yml
name: Update Dashboard
on:
  schedule:
    - cron: '0 6 * * *'    # Daily at 06:00 UTC
  workflow_dispatch:         # Manual trigger

permissions:
  contents: write            # To commit updated files

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: node scripts/collect.js
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - run: node scripts/analyze.js
      - run: node scripts/render.js
      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/ data/
          git diff --staged --quiet || git commit -m "chore: update dashboard $(date -u +%Y-%m-%d)"
          git push
```

### Pattern 2: Intermediate JSON Files Between Stages
**What:** Each stage reads a JSON file and writes a JSON file. No in-memory coupling.

**When:** Pipeline stages may need independent debugging, testing, or re-running.

**Why:** If the Compare API fails for one submodule, you can inspect `raw-data.json` to see what was collected. If thresholds look wrong, you can inspect `cadence-data.json` without re-running collection. This also enables unit testing each stage with fixture files.

```javascript
// scripts/collect.js
const rawData = await collectSubmoduleData();
fs.writeFileSync('raw-data.json', JSON.stringify(rawData, null, 2));

// scripts/analyze.js
const rawData = JSON.parse(fs.readFileSync('raw-data.json'));
const history = JSON.parse(fs.readFileSync('data/history.json'));
const analyzed = analyzeAndClassify(rawData, history);
fs.writeFileSync('cadence-data.json', JSON.stringify(analyzed, null, 2));
// Also append to history
appendToHistory(history, rawData);
fs.writeFileSync('data/history.json', JSON.stringify(history, null, 2));

// scripts/render.js
const data = JSON.parse(fs.readFileSync('cadence-data.json'));
const html = renderDashboard(data);
fs.writeFileSync('docs/index.html', html);
fs.writeFileSync('docs/data.json', JSON.stringify(data, null, 2));
```

### Pattern 3: Defensive API Calls with Graceful Degradation
**What:** Wrap every GitHub API call in try/catch. If a single submodule fails, mark it as "unknown" and continue. Never fail the entire pipeline for one submodule.

**When:** Always — GitHub API can return 404 (deleted repo), 403 (rate limit), or 422 (SHA not found after force-push).

```javascript
async function getCompareData(octokit, owner, repo, pointerSha) {
  try {
    const { data } = await octokit.repos.compareCommits({
      owner, repo,
      base: pointerSha,
      head: 'master',
    });
    return { commitsBehind: data.ahead_by, status: 'ok' };
  } catch (err) {
    if (err.status === 404) {
      // Pointer SHA was garbage-collected or repo renamed
      return { commitsBehind: null, status: 'pointer-missing' };
    }
    if (err.status === 403) {
      // Rate limited — back off and retry once
      await sleep(60000);
      return getCompareData(octokit, owner, repo, pointerSha);
    }
    return { commitsBehind: null, status: 'error', error: err.message };
  }
}
```

### Pattern 4: Git-Commit-Based Deploy (No Deploy Action Needed)
**What:** Commit generated files directly to the repo. GitHub Pages auto-deploys from `docs/` on the default branch.

**When:** The generated content is small (single HTML page + JSON) and version history of the output is valuable.

**Why not `actions/deploy-pages`?** That action deploys to a separate environment and requires artifact uploads. For a single HTML file that changes daily, committing to `docs/` is simpler and creates a git history of every dashboard state — useful for debugging staleness model changes.

**Guard against no-op commits:** The workflow uses `git diff --staged --quiet || git commit` to skip commits when nothing changed (e.g., all submodules still at same state as yesterday).

## Anti-Patterns to Avoid

### Anti-Pattern 1: Cloning sonic-buildimage in the Action
**What:** `git clone https://github.com/sonic-net/sonic-buildimage.git` in the workflow.

**Why bad:** sonic-buildimage is enormous (100+ submodules, deep history). Even a shallow clone takes minutes and GBs. Submodule init is another 30+ minutes. Completely unnecessary — the GitHub API gives us everything we need in 2 fast calls.

**Instead:** Use GitHub REST API for tree and .gitmodules content. Use `git ls-remote` (which doesn't clone anything) for upstream HEADs.

### Anti-Pattern 2: GraphQL Batch Query for Everything
**What:** Try to get all submodule data in one GraphQL query.

**Why bad:** GitHub's GraphQL API can't resolve submodule pointers from the tree. You'd still need REST for the tree and compare endpoints. Mixing two API styles adds complexity without benefit for this use case.

**Instead:** Use REST API consistently. The 64 calls are well within limits.

### Anti-Pattern 3: Separate `gh-pages` Branch
**What:** Push generated files to a separate `gh-pages` branch.

**Why bad:** Creates merge complexity, requires force-pushes, obscures the generated output from the main branch. Makes it harder to debug what the dashboard showed on a given date.

**Instead:** Use `docs/` folder on the default branch. Configure GitHub Pages to serve from `docs/`. Dashboard output is committed alongside source code — everything in one branch.

### Anti-Pattern 4: Running Compare API Sequentially
**What:** `for (const sub of submodules) { await compare(sub); }` — one at a time.

**Why bad:** 31 sequential HTTP requests add unnecessary latency (~15-30 seconds).

**Instead:** Use `Promise.allSettled()` with concurrency limiting (e.g., 5 at a time via `p-limit`) to parallelize API calls while respecting rate limits:

```javascript
import pLimit from 'p-limit';
const limit = pLimit(5);
const results = await Promise.allSettled(
  submodules.map(sub => limit(() => getCompareData(octokit, sub)))
);
```

### Anti-Pattern 5: Storing Thresholds in Config Instead of Computing Them
**What:** Hardcode `{ "sonic-swss": { yellowDays: 7, redDays: 14 } }` in a config file.

**Why bad:** 31 submodules with different cadences. Manual threshold maintenance is a burden. Cadences change over time (a submodule may get more or less active). The whole point of this project is cadence-aware automation.

**Instead:** Compute thresholds dynamically from historical update patterns. Allow config overrides only as escape hatches for exceptional cases.

## Scalability Considerations

| Concern | At 31 submodules (now) | At 100 submodules | At 500 submodules |
|---------|----------------------|-------------------|-------------------|
| API calls per run | ~64 (6.4% of budget) | ~204 (20.4%) | ~1,004 (exceeds limit) |
| Pipeline runtime | ~30 seconds | ~2 minutes | ~10 minutes (need batching) |
| HTML page size | ~15KB | ~50KB | Split into pages or add search |
| history.json (365 days) | ~200KB | ~700KB | ~3.5MB (consider SQLite) |
| git ls-remote calls | ~15 sec | ~50 sec | ~4 min (parallelize) |

**At current scale (31 submodules), everything is trivially within limits.** No premature optimization needed. If scope expands to all 49 submodules, still well within limits.

**Breaking point:** At ~500 submodules (not realistic for this project), the API budget would be exceeded. The mitigation would be switching to GraphQL for batch queries or caching compare results when pointer SHAs haven't changed.

## Key Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Node.js for scripts | `@octokit/rest` handles auth, pagination, rate limiting automatically. GitHub Actions ecosystem is JS-native. Template literals sufficient for HTML generation. |
| `git ls-remote` for upstream HEADs | Zero API quota impact. Faster than REST API for 31 repos. Already available on Actions runners. |
| Intermediate JSON files | Enables independent testing, debugging, and stage re-running. Trivial overhead for small data volumes. |
| History accumulation in git | No external database needed. Git provides free versioning. Daily snapshots for cadence accuracy. |
| `docs/` folder for Pages | Simplest deployment model. No separate branch. Dashboard state versioned alongside source. |
| Daily cron schedule | Matches the submodule update bot's cadence (the bot runs frequently, so daily dashboard refresh catches most drift within 24 hours). |
| Threshold floors (7d yellow, 14d red) | Prevents hyper-active submodules (daily updates) from triggering yellow at 4 days. Floor provides minimum "reaction time" for maintainers. |

## Suggested Build Order

The components have clear dependencies. Build in this order:

### Phase 1: Data Collection + Minimal Display
Build the collector and a bare-bones HTML renderer. Skip cadence analysis — use fixed thresholds (7/14 days) as placeholders. This gets the pipeline running end-to-end.

**Components:** `collect.js`, `render.js` (basic), workflow YAML
**Dependencies:** None (greenfield)
**Validates:** GitHub API access works, git ls-remote works, Pages deployment works

### Phase 2: Cadence-Aware Staleness Model
Add the cadence analyzer. Compute dynamic thresholds per submodule. Replace fixed thresholds from Phase 1.

**Components:** `analyze.js`, `data/history.json` initialization
**Dependencies:** Phase 1 (needs raw data format to be stable)
**Validates:** Threshold model produces sensible results for all 31 submodules

### Phase 3: Polish Dashboard UI
Add sorting, color-coded badges, last-updated timestamp, CODEOWNERS team mapping, and a clean responsive layout.

**Components:** Updated `render.js`, `templates/dashboard.html`, CSS
**Dependencies:** Phase 2 (needs final data schema with cadence fields)
**Validates:** Dashboard is readable and useful for maintainers

### Phase 4: History + Trends (v2 scope)
Implement history accumulation, trend sparklines, and the "getting better/worse" indicator.

**Components:** History append logic, sparkline rendering
**Dependencies:** Phase 2 (history schema), Phase 3 (UI)

## GitHub Actions-Specific Considerations

### Token Permissions
The workflow needs `contents: write` to commit generated files back to the repo. The default `GITHUB_TOKEN` in GitHub Actions has this permission when configured in workflow `permissions`. No PAT needed for public repo API reads.

### Concurrency Control
Add `concurrency` to prevent overlapping runs (e.g., if manual dispatch overlaps with cron):

```yaml
concurrency:
  group: dashboard-update
  cancel-in-progress: true
```

### Cron Reliability
GitHub Actions cron is not precise — it may run 5-15 minutes late during high-load periods, or be skipped entirely if the repo has been inactive for 60+ days. This is acceptable for a daily dashboard. The `workflow_dispatch` trigger provides a manual fallback.

### Runner Environment
GitHub Actions `ubuntu-latest` runners include: Node.js (via setup-node), git, curl, jq. No special runner requirements. The workflow runs in <2 minutes, well under the 6-hour job timeout.

## Sources

- **GitHub REST API — Git Trees:** `GET /repos/{owner}/{repo}/git/trees/{tree_sha}` — confirmed submodule entries appear as `mode: "160000"` [GitHub Docs, HIGH confidence]
- **GitHub REST API — Compare Commits:** `ahead_by`/`behind_by` fields are accurate regardless of commit list truncation [GitHub Docs, HIGH confidence]
- **GitHub REST API — Rate Limits:** 1,000 requests/hour for `GITHUB_TOKEN` in Actions [GitHub Docs, HIGH confidence]
- **GitHub Pages — Deploy from `docs/`:** Supported via repository Settings → Pages → Source [GitHub Docs, HIGH confidence]
- **git ls-remote:** Does not consume GitHub API quota — uses git smart HTTP protocol directly [Verified empirically, HIGH confidence]
- **sonic-buildimage submodule structure:** 49 total submodules, 31 under sonic-net org, paths verified from actual `.gitmodules` [Verified from repo, HIGH confidence]
- **Submodule update patterns:** Automated bot creates `[submodule] Update submodule X to the latest HEAD automatically` PRs [Verified from git log, HIGH confidence]

---

*Architecture research: 2026-03-21*
