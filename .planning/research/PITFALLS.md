# Pitfalls Research

**Domain:** Python monorepo refactoring — migrating from raw `requests` to PyGithub, restructuring into proper packaging with `pyproject.toml`, preserving CI/CD and dashboard output
**Researched:** 2025-07-18
**Confidence:** HIGH (verified against PyGithub 2.9.0 source, current codebase analysis)

## Critical Pitfalls

### Pitfall 1: PyGithub Returns Objects, Not Dicts — Pervasive Field Access Change

**What goes wrong:**
The entire codebase accesses GitHub API data via dict key access: `pr["title"]`, `pr["number"]`, `resp.json()["commits"][0]`, `sub["pull_request"]["merged_at"]`. PyGithub returns typed objects with attribute access: `pr.title`, `pr.number`, `comparison.commits[0]`. Every function that reads API response data must change from bracket notation to dot notation. Enrichment functions that build dicts from API responses (`sub["open_bot_pr"] = {"number": pr["number"], ...}`) must extract from objects, not dicts.

**Why it happens:**
Developers change the API client layer but don't propagate the data format change to all consumers. The code compiles fine — `NamedObject["key"]` raises `TypeError` at runtime, not import time. Tests that mock raw JSON responses continue to pass even though production code now returns objects.

**How to avoid:**
- Create an adapter layer in the shared core that converts PyGithub objects to the same dict format currently used. This means the enrichment pipeline sees no change — it still receives and mutates plain dicts.
- Alternatively, define dataclasses/TypedDicts that both the PyGithub adapter and existing code produce. Either way, the boundary should be: PyGithub objects stay inside the core client; everything outside receives dicts or dataclasses.
- Run the full pipeline once against the live API (or a comprehensive mock) and `diff` the `data.json` output against a known-good baseline.

**Warning signs:**
- `TypeError: 'ContentFile' object is not subscriptable` in CI logs
- Tests pass but `data.json` output is empty or has `null` fields that were previously populated
- Type checkers (mypy/pyright) flag bracket access on non-dict types — add type checking early

**Phase to address:**
Core client implementation phase — the adapter/conversion layer must be designed before any migration of consuming code.

---

### Pitfall 2: Double Rate-Limiting — Manual Sleeps + PyGithub Built-In Delays

**What goes wrong:**
The current codebase has `time.sleep(0.5)` scattered across 5+ locations (collector.py line 251, staleness.py line 184, enrichment.py lines 168, 258, 327, 360). PyGithub 2.9.0 has `seconds_between_requests=0.25` by default — it automatically adds 0.25s between every API call. If the manual sleeps aren't removed when migrating to PyGithub, every API call gets a combined 0.75s delay instead of 0.25s. With ~240 API calls per run, that's 180s of pure sleep vs 60s — tripling the pipeline's wall-clock time from ~3 minutes to ~6+ minutes.

**Why it happens:**
The manual sleeps are inside functions that get refactored to use PyGithub internally, but the `time.sleep()` calls look like "safety measures" and developers don't remove them. PyGithub's built-in delay isn't obvious — it's a constructor parameter, not visible at the call site.

**How to avoid:**
- When creating the `Github()` instance in the core client, explicitly set `seconds_between_requests` to the desired value (0.25 is fine for 5000 req/hr rate limit).
- Search the codebase for ALL `time.sleep` calls and remove them from any function that transitions to PyGithub. Use `grep -rn "time.sleep" submodule-status/scripts/` as a checklist.
- Also remove the `@patch("collector.time.sleep")` / `@patch("staleness.time.sleep")` from tests — but only after removing the actual sleeps. Removing test patches before actual sleeps will make tests slow.

**Warning signs:**
- Pipeline runs take 5+ minutes when they used to take ~3 minutes
- GitHub Actions logs show long gaps between API calls
- `grep -rn "time.sleep" scripts/` returns hits alongside PyGithub usage

**Phase to address:**
Core client implementation phase — when defining the shared `Github()` instance. Must also be tracked during the migration phase when individual functions move to PyGithub.

---

### Pitfall 3: `Comparison.commits` Is a PaginatedList — Not a Bounded List

**What goes wrong:**
The current code accesses `resp.json()["commits"][0]` from the Compare API to get the first ahead commit. The raw API limits this to 250 commits. With PyGithub 2.9.0, `Comparison.commits` is a **PaginatedList** that auto-fetches additional pages when iterated. If the code does `list(comparison.commits)` or iterates fully on a submodule that's 500+ commits behind, PyGithub silently makes multiple paginated API calls. For 16 submodules, this could add dozens of unexpected API calls. Worse, `comparison.commits[0]` on a PaginatedList still works but triggers a network fetch for the first page.

**Why it happens:**
PyGithub's PaginatedList looks like a regular list — `[0]` indexing, `len()`, iteration all work. But each operation may trigger network calls. The old code's mental model of "I got a JSON blob, I index into it" doesn't apply.

**How to avoid:**
- Access only `comparison.ahead_by` and `comparison.behind_by` (these are simple integers, no pagination).
- For the first-ahead-commit pattern, use `comparison.get_commits()` with explicit `comparison_commits_per_page=1` and take only the first element. This limits the fetch to one page.
- Never call `list()` or `len()` on `comparison.commits` without understanding the pagination cost.
- Document in the core client: "Compare API returns paginated commits — do not iterate fully."

**Warning signs:**
- Rate limit consumption spikes after migration (check `X-RateLimit-Remaining`)
- Pipeline runtime increases disproportionately for submodules with large `ahead_by` counts
- Unexpected 403 rate-limit errors mid-run

**Phase to address:**
Core client implementation phase — the compare wrapper should encapsulate this and return only the needed data (ahead_by, first commit date).

---

### Pitfall 4: GitHub Actions Workflow Breaks When Directory Paths Change

**What goes wrong:**
The current workflow (`.github/workflows/update-dashboard.yml`) has `working-directory: submodule-status` as a job-level default. Steps run `pip install -r requirements.txt`, `python scripts/collector.py`, `python scripts/renderer.py`, and upload artifact from `submodule-status/site`. After restructuring into a monorepo with `core/` package and relocated deliverables, every path in the workflow must change:

1. `working-directory` must point to the new deliverable location
2. `pip install -r requirements.txt` becomes `pip install -e ./core && pip install -r deliverables/submodule-status/requirements.txt` (or similar)
3. `python scripts/collector.py` path changes
4. `upload-pages-artifact` `path:` must point to new `site/` location

If ANY path is wrong, the workflow fails silently or deploys an empty page. GitHub Actions doesn't validate paths until runtime.

**Why it happens:**
Directory restructuring is done in the code but the workflow file is updated separately (it's YAML, not Python — linters don't catch path issues). The `working-directory` default makes some paths look right while others are broken because they're relative to the repo root, not the working directory (specifically the `upload-pages-artifact` `path:` is relative to repo root).

**How to avoid:**
- Update the workflow in the SAME commit/PR as the directory restructure. Never restructure directories without simultaneously updating the workflow.
- Test the workflow with `workflow_dispatch` (manual trigger) immediately after restructuring — don't wait for the cron schedule.
- For the transition period, consider running BOTH old and new paths in parallel (old workflow deploys, new workflow runs but doesn't deploy) to verify identical output.
- Add a CI step that verifies `data.json` exists and `site/index.html` exists before deployment.

**Warning signs:**
- GitHub Actions run fails with "No such file or directory" in the install or run steps
- Deployment succeeds but the dashboard shows stale data (it deployed old cached artifacts)
- `upload-pages-artifact` step succeeds with 0 files (empty directory — GitHub doesn't fail this)

**Phase to address:**
Directory restructuring phase — the workflow update must be part of the same PR. Add a verification step to CI as part of this phase.

---

### Pitfall 5: Test Import Paths Break During Packaging Migration

**What goes wrong:**
The test suite relies on `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))` in `conftest.py` to import modules. Tests do `from collector import parse_gitmodules` and `@patch("collector.time.sleep")`. After moving to proper packaging, imports become `from sonic_buildcop.core.github_client import ...` or `from submodule_status.collector import parse_gitmodules`. Every `import` statement in every test file changes. More critically, every `@patch("module.function")` decorator must update the module path — `@patch("collector.time.sleep")` becomes `@patch("submodule_status.collector.time.sleep")`. If the patch path is wrong, the mock doesn't apply and tests either fail or — worse — pass but make real API calls.

**Why it happens:**
`@patch` target strings are plain strings, not validated at import time. A wrong patch path means the mock doesn't intercept the target, so the original function runs. If the original is `time.sleep`, the test just runs slowly. If it's an API call, the test makes real network requests (and likely fails with auth errors, but intermittently).

**How to avoid:**
- Update `conftest.py` to remove the `sys.path.insert` hack and instead rely on `pip install -e .` for the core package.
- Use a find-and-replace pass: `grep -rn '@patch("collector\.' tests/` and update ALL patch strings in one commit.
- After migration, run tests with `--timeout=5` (via `pytest-timeout`) to catch any unpatched `time.sleep` calls.
- Consider using `@patch.object(module, "function")` instead of string-based patching — this fails at import time if the module or function doesn't exist, instead of silently not patching.

**Warning signs:**
- Tests suddenly take much longer (unpatched `time.sleep(0.5)` calls)
- `ImportError` or `ModuleNotFoundError` when running tests after restructuring
- Tests pass locally (where `pip install -e .` was run) but fail in CI (where it wasn't)
- `@patch` decorators with old module paths don't raise errors — they silently do nothing

**Phase to address:**
Packaging/restructuring phase — test migration must happen atomically with the import path change. Run full test suite as the gating check.

---

### Pitfall 6: Dashboard Output Drift — PyGithub Datetime Objects vs JSON Strings

**What goes wrong:**
The requirement is "identical dashboard output after migration." The current code stores ISO 8601 strings from raw API responses directly into the submodule dicts: `sub["last_merged_bot_pr"]["merged_at"] = pr["pull_request"]["merged_at"]` (a string like `"2025-01-25T10:00:00Z"`). PyGithub parses these into Python `datetime` objects. If the migration passes `datetime` objects into `data.json` serialization, `json.dumps` will crash (`TypeError: Object of type datetime is not JSON serializable`). If fixed naively with `str(dt)`, the output format changes to `"2025-01-25 10:00:00+00:00"` (note: space instead of `T`, `+00:00` instead of `Z`). The Jinja2 template uses string slicing like `merged_at[:10]` — a `datetime` object would crash the template.

**Why it happens:**
Raw `requests` returns JSON as native Python types (strings stay strings). PyGithub parses strings into richer types (`datetime`, `NamedUser`, etc.). The data pipeline was built assuming string-in/string-out for timestamps.

**How to avoid:**
- In the core client adapter, convert all `datetime` objects back to ISO 8601 strings (`dt.isoformat().replace('+00:00', 'Z')`) before returning data to the pipeline.
- Add a golden-file test: capture current `data.json` output, then after migration, assert the new output matches the schema and format (not exact values, since data changes, but field types and string formats).
- Specifically test: timestamp formats, URL formats, `None` vs missing fields, numeric types (int vs float for `commits_behind`).

**Warning signs:**
- `TypeError: Object of type datetime is not JSON serializable` during `json.dumps()`
- Dashboard shows timestamps in unexpected format (e.g., `2025-01-25 10:00:00+00:00` instead of `2025-01-25T10:00:00Z`)
- Jinja2 `TypeError` on string slicing operations like `[:10]` applied to datetime objects
- `diff` between old and new `data.json` shows structural changes beyond value changes

**Phase to address:**
Core client implementation phase — the adapter must normalize all types. Validate with a schema test in the migration phase.

---

### Pitfall 7: PyGithub Auto-Pagination Causes API Call Explosion

**What goes wrong:**
The current code makes targeted single-page API requests: `session.get(url, params={"per_page": 30})` and processes just that response. PyGithub returns `PaginatedList` objects for most list endpoints (`get_commits()`, `search_issues()`). The default `per_page` is 30. If code does `list(repo.get_commits(path="src/sonic-swss"))` to get bump dates, PyGithub fetches ALL pages — for an active repo, that could be thousands of commits across dozens of API calls. The current `get_bump_dates()` in `staleness.py` fetches commits with `per_page=30` and uses only the first page (30 results). PyGithub equivalent must be explicitly limited.

**Why it happens:**
PaginatedList is iterable and looks like a list. `for commit in repo.get_commits(path=...)` iterates ALL commits, not just the first page. Python idioms like `list(iterable)` or `len(iterable)` trigger full pagination. The code pattern of "fetch a list and process it" doesn't translate safely to "fetch a PaginatedList and process it."

**How to avoid:**
- Use `.get_page(0)` to fetch only the first page: `repo.get_commits(path=...).get_page(0)` returns a plain list of up to `per_page` items with exactly one API call.
- Set `per_page=30` on the `Github()` constructor or per-call where available.
- Never call `list()`, `len()`, or full iteration on a PaginatedList unless you specifically need all results.
- For `search_issues`, which returns paginated results: use `.get_page(0)` if you only need the first page of results.
- Wrap all PaginatedList interactions in the core client — consuming code should never see a PaginatedList.

**Warning signs:**
- Pipeline takes 10+ minutes (was ~3 minutes)
- Rate limit exhaustion mid-run (403 errors)
- `Github.get_rate_limit().core.remaining` drops faster than expected
- Unusually high API call count visible in `X-RateLimit-Used` response header

**Phase to address:**
Core client implementation phase — the client wrapper must handle pagination internally and expose simple lists/values.

---

### Pitfall 8: `conftest.py` sys.path Hack and Package Install Create Dual Import Paths

**What goes wrong:**
During migration, if `pyproject.toml` is added (making modules importable as a package via `pip install -e .`) but `conftest.py` still has `sys.path.insert(0, ...)`, Python may import the same module from two different paths. For example, `collector` could be importable as both `scripts.collector` (from sys.path) and `submodule_status.scripts.collector` (from the package). When tests do `@patch("collector.time.sleep")`, it patches the sys.path-imported version. But if the code under test imports via the package path, the patch doesn't apply. This causes tests to pass but with unpatched functions — sleeps run, API calls aren't mocked.

**Why it happens:**
The `sys.path` hack was a necessary workaround for the lack of packaging. During the transition, both import mechanisms exist simultaneously. Python treats them as different modules because the import paths differ, even though they resolve to the same file.

**How to avoid:**
- Remove the `sys.path.insert` hack from `conftest.py` in the SAME commit that adds `pyproject.toml` and updates all imports to use the package path.
- Never have a transitional state where both `sys.path` and package imports work simultaneously.
- After migration, verify with: `python -c "import submodule_status.collector; print(submodule_status.collector.__file__)"` to confirm the module resolves from the package, not from a stale sys.path.

**Warning signs:**
- Tests pass but with warnings about duplicate module names
- `@patch` calls silently don't apply (no error, but the function isn't mocked)
- `pytest` warnings: "Module already imported so cannot be rewritten"
- Different test behavior between `pytest tests/` and `python -m pytest tests/`

**Phase to address:**
Packaging phase — must be an atomic change: add pyproject.toml + remove sys.path hack + update all imports in one commit.

---

### Pitfall 9: `search_issues` Merged PR `merged_at` Access Requires Nested Object Navigation

**What goes wrong:**
The current code fetches merged bot PRs via the Search Issues API and accesses `pr["pull_request"]["merged_at"]` from the raw JSON. With PyGithub, `search_issues()` returns `IssueSearchResult` objects. The `merged_at` field is NOT on the `IssueSearchResult` directly — it's on `result.pull_request.merged_at` (where `.pull_request` is an `IssuePullRequest` object, verified in PyGithub 2.9.0). If code tries `result.merged_at`, it gets `AttributeError`. If code calls `result.as_pull_request()` instead (to get the full `PullRequest` object), that triggers an EXTRA API call per PR — for 16+ merged PRs, that's 16+ unexpected API calls.

**Why it happens:**
The GitHub Search Issues API returns a `pull_request` sub-object with `merged_at`, but PyGithub models this as an `IssuePullRequest` nested object, not as a flat field. Developers expect PR-related fields to be top-level on the search result.

**How to avoid:**
- Use `result.pull_request.merged_at` — this accesses the already-fetched data without extra API calls.
- Do NOT use `result.as_pull_request()` for this — it's an unnecessary network call.
- In the core client adapter, normalize this: the adapter should return `{"merged_at": result.pull_request.merged_at.isoformat(), ...}` so consuming code doesn't need to know the nesting.
- Note: `result.pull_request.merged_at` returns a `datetime` object, not a string — see Pitfall 6.

**Warning signs:**
- `AttributeError: 'IssueSearchResult' object has no attribute 'merged_at'`
- Unexpected spike in API calls after switching to PyGithub search
- Rate limit warnings specifically during the "fetch merged bot PRs" step

**Phase to address:**
Core client implementation phase — the search wrapper must handle the nested access pattern.

---

### Pitfall 10: Editable Install (`pip install -e .`) Not Set Up in CI

**What goes wrong:**
After creating `pyproject.toml` for the core package, local development uses `pip install -e ./core` for editable installs. But the GitHub Actions workflow still does `pip install -r requirements.txt`. The core package isn't installed, so imports like `from sonic_buildcop_core import github_client` fail at runtime in CI. Tests pass locally (where the editable install exists) but fail in CI.

**Why it happens:**
Developers add `pyproject.toml` and update imports, test locally with `pip install -e .`, and forget that CI doesn't have the same environment. The workflow file is updated separately (YAML, not Python) and is easy to overlook.

**How to avoid:**
- Update the workflow in the SAME PR that introduces the core package.
- CI install step should become: `pip install -e ./core && pip install -r deliverables/submodule-status/requirements.txt` (or whatever the final structure is).
- Add a CI step that verifies imports work: `python -c "from sonic_buildcop_core import github_client"` before running the pipeline.
- Consider a top-level `Makefile` or script that encapsulates the install sequence for both local and CI.

**Warning signs:**
- CI fails with `ModuleNotFoundError` on the very first import of the core package
- Tests pass locally but fail in CI with import errors
- `pip install -r requirements.txt` succeeds but doesn't install the local core package

**Phase to address:**
Packaging phase and CI update phase — must be coordinated. The workflow update is part of the packaging deliverable.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keep `sys.path.insert` alongside `pyproject.toml` during transition | Tests keep working without updating imports | Dual import paths cause silent mock failures, module identity bugs | **Never** — must be atomic swap |
| Pass PyGithub objects directly through the pipeline (skip adapter layer) | Less code to write initially | All consuming code couples to PyGithub types; can't swap clients later; dict-mutation pattern breaks | **Never** — the whole point of the core package is abstraction |
| Copy-paste the current `time.sleep` pattern into PyGithub-wrapped functions | "Safety first" — keep courtesy delays | 3× slower pipeline from doubled delays; masks PyGithub's built-in rate limit handling | **Never** — remove manual sleeps when adopting PyGithub |
| Keep `requirements.txt` unpinned during migration | Fewer files to change | Non-reproducible builds; a PyGithub or Jinja2 update could break CI without any code change | Only in the first PR — pin versions immediately after |
| Defer test migration to a later PR | Ship the restructure faster | Broken tests provide no safety net for the migration that most needs one | **Never** — tests must migrate with the code |
| Use `str(datetime_obj)` for JSON serialization instead of `.isoformat()` | Quick fix for serialization errors | Output format changes (`2025-01-25 10:00:00+00:00` vs `2025-01-25T10:00:00Z`), breaking dashboard template string slicing | **Never** — always use `.isoformat()` with explicit Z suffix |

## Integration Gotchas

Common mistakes when connecting to external services in this migration.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| PyGithub `Github()` constructor | Using `login_or_token=token` (deprecated positional arg) | Use `auth=github.Auth.Token(token)` — the modern auth pattern in PyGithub 2.x |
| PyGithub `get_contents()` | Assuming it always returns a single `ContentFile` | It returns `ContentFile | list[ContentFile]` — check with `isinstance(result, list)` or know your path is a file |
| PyGithub `search_issues()` | Calling `list()` on results to "get all PRs" | Use `.get_page(0)` for the first page only. `list()` fetches ALL matching issues across ALL pages |
| PyGithub `compare()` | Accessing `.commits` and iterating to get `ahead_by` count | Use `.ahead_by` directly (integer, no pagination). Only access `.commits` if you need actual commit data, and use `.get_page(0)` |
| PyGithub rate limiting | Wrapping PyGithub calls in custom retry logic | PyGithub has built-in `GithubRetry(total=10)` by default with secondary rate limit handling. Remove custom retry/backoff unless you need different behavior |
| `azure-devops-python-api` | Installing it now with full integration | Stub the interface only — actual Azure integration is out of scope. Don't let the client library pull in unnecessary dependencies |
| GitHub Actions `working-directory` | Setting it at job level and assuming all paths are relative to it | `upload-pages-artifact` `path:` is relative to repo root, NOT working-directory. Mix of relative/absolute path semantics |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| PaginatedList full iteration | Pipeline takes 10+ min, rate limit exhaustion | Use `.get_page(0)` for single-page fetches; set `per_page` explicitly | >100 commits behind on any submodule |
| PyGithub lazy loading (`_completeIfNotSet`) | Accessing properties triggers unexpected API calls | Access only properties you know are populated from the initial response; use `lazy=True` on `Github()` constructor if needed | When accessing properties not in the initial API response payload |
| Double rate-limiting (manual + PyGithub) | 6+ minute pipeline (was 3 min) | Remove all `time.sleep()` calls from migrated functions | Immediately upon migration |
| PyGithub `GithubRetry(total=10)` + custom retry wrapper | 10 PyGithub retries × 3 custom retries = 30 retries per failure | Remove custom retry logic from functions where PyGithub handles retries; OR disable PyGithub retry and keep custom | First API failure after migration |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Logging the `GITHUB_TOKEN` during debugging | Token appears in CI logs, which are publicly visible on public repos | Use `auth=github.Auth.Token(token)` — PyGithub never logs the token. If adding custom logging, never log headers or auth objects |
| Empty token fallback (`os.environ.get("GITHUB_TOKEN", "")`) creating a `Github(auth=Token(""))` | PyGithub sends malformed auth header; may behave differently than the current raw-requests empty-token behavior | Fail fast: `token = os.environ["GITHUB_TOKEN"]` (raises `KeyError` if missing). Or check explicitly and log a warning before proceeding unauthenticated |
| `pip install -e .` in CI with untrusted `pyproject.toml` | A compromised or malformed `pyproject.toml` could execute arbitrary setup code | Use `build-backend = "setuptools.build_meta"` (declarative only). No `setup.py` with imperative code. Pin `setuptools` version |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Directory restructure:** Files moved but `update-dashboard.yml` workflow still references old paths — verify every `run:`, `working-directory:`, and `path:` in the workflow file
- [ ] **PyGithub migration:** API calls work but `time.sleep()` calls not removed — `grep -rn "time.sleep" scripts/` should return zero hits in migrated modules
- [ ] **Package install:** `pyproject.toml` exists but `conftest.py` still has `sys.path.insert` — verify `grep -rn "sys.path" tests/` returns zero hits
- [ ] **Test migration:** Imports updated but `@patch()` target strings still use old module paths — verify all `@patch("old_module.` strings are updated
- [ ] **Data format parity:** Pipeline runs and produces `data.json` but datetime formats differ — `diff` field formats against a known-good baseline
- [ ] **Search results:** `fetch_merged_bot_prs` works but `merged_at` is `None` because code accesses `result.merged_at` instead of `result.pull_request.merged_at` — verify merged PRs have non-null `merged_at` in `data.json`
- [ ] **CI editable install:** Core package has `pyproject.toml` but CI workflow doesn't `pip install -e ./core` — verify the install step includes the core package
- [ ] **Pagination control:** `get_commits()` and `search_issues()` calls don't use `.get_page(0)` — verify no PaginatedList is fully iterated by adding a rate-limit check step to CI
- [ ] **Retry deduplication:** PyGithub's `GithubRetry(total=10)` is active alongside the custom retry wrapper in `collect_submodule()` — verify only one retry mechanism is active per API call path
- [ ] **`per_page` setting:** PyGithub defaults to `per_page=30` but some API calls may need different page sizes — verify the `Github()` constructor or per-call settings match expectations

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Dashboard output format drift | LOW | Add a `data.json` schema validation test; fix datetime serialization in adapter; redeploy |
| Double rate-limiting (slow pipeline) | LOW | `grep -rn "time.sleep"`, remove manual sleeps, redeploy |
| PaginatedList API call explosion | LOW | Replace `list(paginated)` with `.get_page(0)`, redeploy. Rate limit resets hourly |
| Dual import paths (sys.path + package) | MEDIUM | Remove sys.path hack, update all imports and @patch strings in one atomic commit |
| CI workflow path breakage | LOW | Fix paths in workflow YAML, trigger manual workflow_dispatch to verify |
| Test @patch targets pointing to wrong module | MEDIUM | Audit all @patch strings with `grep -rn '@patch' tests/`; update to new module paths; add `pytest-timeout` to catch unpatched sleeps |
| Editable install missing in CI | LOW | Add `pip install -e ./core` to workflow install step; trigger manual workflow_dispatch |
| Custom retry + PyGithub retry stacking | LOW | Disable PyGithub retry (`retry=None`) OR remove custom retry wrapper; choose one mechanism |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| PyGithub objects vs dicts (Pitfall 1) | Core client implementation | Type checker passes; `data.json` field types match baseline |
| Double rate-limiting (Pitfall 2) | Core client + migration | `grep -rn "time.sleep"` returns 0 hits in migrated code; pipeline runs in ≤4 min |
| PaginatedList commit explosion (Pitfall 3) | Core client implementation | Rate limit consumption per run ≤300 calls; no `.commits` full iteration |
| Workflow path breakage (Pitfall 4) | Directory restructuring | `workflow_dispatch` succeeds; dashboard deploys correctly |
| Test import path breakage (Pitfall 5) | Packaging + test migration | `pytest` passes in CI; `grep "sys.path"` returns 0 hits in test code |
| Datetime format drift (Pitfall 6) | Core client implementation | `data.json` timestamps match `YYYY-MM-DDTHH:MM:SSZ` format; template renders without error |
| Auto-pagination explosion (Pitfall 7) | Core client implementation | All PaginatedList usage wraps `.get_page(0)`; core client returns plain lists |
| Dual import paths (Pitfall 8) | Packaging (atomic swap) | No `sys.path.insert` in codebase; `pytest` shows no "module already imported" warnings |
| Search `merged_at` nesting (Pitfall 9) | Core client implementation | Merged PRs in `data.json` have non-null `merged_at` values |
| CI editable install (Pitfall 10) | Packaging + CI update | CI workflow installs core package; `python -c "import core"` step passes |

## Sources

- PyGithub 2.9.0 source code (verified via `pip install PyGithub` and `inspect.signature()` / `inspect.getsource()`)
- PyGithub `Github.__init__` parameters: `seconds_between_requests=0.25`, `retry=GithubRetry(total=10)`, `per_page=30`
- PyGithub `Comparison.commits` is a paginated property (verified via source inspection)
- PyGithub `IssueSearchResult.pull_request.merged_at` path (verified: `IssueSearchResult` has no `merged_at`; `IssuePullRequest` does)
- Current codebase: `submodule-status/scripts/collector.py`, `staleness.py`, `enrichment.py`, `tests/conftest.py`
- Current workflow: `.github/workflows/update-dashboard.yml` — `working-directory: submodule-status`, step paths
- Codebase analysis: `.planning/codebase/CONCERNS.md`, `ARCHITECTURE.md`, `TESTING.md`, `CONVENTIONS.md`

---
*Pitfalls research for: sonic-buildcop Python monorepo refactoring*
*Researched: 2025-07-18*
