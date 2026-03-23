"""Data enrichment module for submodule detail information.

Fetches bot PR status, latest repo commits, and CI check status for each
submodule. Follows the staleness.py pattern: enrich submodule dicts in-place.

Exports:
    match_pr_to_submodule     — match a PR title to a submodule name (longest-first)
    get_ci_status_for_pr      — aggregate CI check-run status for a PR
    fetch_open_bot_prs        — batch-fetch open bot PRs and enrich submodules
    fetch_merged_bot_prs      — batch-fetch merged bot PRs and enrich submodules
    fetch_latest_repo_commits — fetch latest commit from each submodule's repo
"""
import time
from datetime import datetime, timezone

import requests

# --- Constants ---

PARENT_OWNER = "sonic-net"
PARENT_REPO = "sonic-buildimage"
API_BASE = "https://api.github.com"
BOT_AUTHOR = "mssonicbld"


# --- Functions ---


def match_pr_to_submodule(pr: dict, submodule_names: list[str]) -> str | None:
    """Match a PR to a submodule by scanning the title for known names.

    ``submodule_names`` MUST be sorted longest-first by the caller so that
    ``sonic-swss-common`` is tried before ``sonic-swss``, preventing prefix
    collisions.

    Returns the matched name, or ``None`` if no submodule name appears in
    the PR title.
    """
    title_lower = pr["title"].lower()
    for name in submodule_names:
        if name.lower() in title_lower:
            return name
    return None


def get_ci_status_for_pr(session: requests.Session, pr_number: int) -> str | None:
    """Aggregate CI check-run status for a pull request.

    Fetches the PR to get the head SHA, then queries the Check Runs API.
    Returns:
        ``"pass"``    — all checks completed with success/neutral/skipped
        ``"fail"``    — at least one completed check has a non-success conclusion
        ``"pending"`` — at least one check is still running (no failures)
        ``None``      — no check runs found, or API error
    """
    try:
        # Get head SHA from the PR
        pr_url = f"{API_BASE}/repos/{PARENT_OWNER}/{PARENT_REPO}/pulls/{pr_number}"
        pr_resp = session.get(pr_url)
        pr_resp.raise_for_status()
        head_sha = pr_resp.json()["head"]["sha"]

        # Get check runs for the head SHA
        checks_url = (
            f"{API_BASE}/repos/{PARENT_OWNER}/{PARENT_REPO}"
            f"/commits/{head_sha}/check-runs"
        )
        checks_resp = session.get(
            checks_url,
            headers={"Accept": "application/vnd.github+json"},
        )
        checks_resp.raise_for_status()
        data = checks_resp.json()

        check_runs = data.get("check_runs", [])
        if not check_runs:
            return None

        has_failure = False
        has_pending = False

        for run in check_runs:
            if run["status"] != "completed":
                has_pending = True
            else:
                conclusion = run.get("conclusion", "")
                if conclusion not in ("success", "neutral", "skipped"):
                    has_failure = True

        if has_failure:
            return "fail"
        if has_pending:
            return "pending"
        return "pass"

    except (requests.RequestException, KeyError):
        return None


def fetch_open_bot_prs(
    session: requests.Session,
    submodules: list[dict],
) -> None:
    """Batch-fetch open bot PRs and enrich submodule dicts in-place.

    Uses the GitHub Search Issues API to fetch all open PRs authored by
    the bot in one call, then matches each PR to a submodule by title.

    Sets ``sub["open_bot_pr"]`` to a dict with ``url``, ``age_days``, and
    ``ci_status`` keys — or ``None`` if no open PR exists for the submodule.
    """
    # Initialize all submodules first
    for sub in submodules:
        sub["open_bot_pr"] = None

    # Build lookup for status="ok" submodules only
    sub_by_name: dict[str, dict] = {}
    for sub in submodules:
        if sub["status"] == "ok":
            sub_by_name[sub["name"]] = sub

    if not sub_by_name:
        return

    sorted_names = sorted(sub_by_name.keys(), key=len, reverse=True)

    # Batch-fetch open bot PRs
    query = (
        f"repo:{PARENT_OWNER}/{PARENT_REPO} "
        f"author:{BOT_AUTHOR} is:pr is:open"
    )
    try:
        resp = session.get(
            f"{API_BASE}/search/issues",
            params={"q": query, "per_page": 50, "sort": "updated", "order": "desc"},
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except (requests.RequestException, KeyError):
        return  # All already None

    now = datetime.now(timezone.utc)

    for pr in items:
        matched = match_pr_to_submodule(pr, sorted_names)
        if matched and matched in sub_by_name:
            created_str = pr["created_at"]
            created_at = datetime.fromisoformat(
                created_str.replace("Z", "+00:00")
            )
            age_days = round((now - created_at).total_seconds() / 86400, 1)

            ci_status = get_ci_status_for_pr(session, pr["number"])

            sub_by_name[matched]["open_bot_pr"] = {
                "url": pr["html_url"],
                "age_days": age_days,
                "ci_status": ci_status,
            }

            # Remove to prevent double-matching
            sorted_names.remove(matched)
            time.sleep(0.5)


def fetch_merged_bot_prs(
    session: requests.Session,
    submodules: list[dict],
) -> None:
    """Batch-fetch last merged bot PR for each submodule.

    Uses the GitHub Search Issues API to fetch merged bot PRs, then matches
    each to a submodule. Only the first (most recent) merged PR per submodule
    is kept.

    Sets ``sub["last_merged_bot_pr"]`` to a dict with ``url`` and ``merged_at``
    keys — or ``None``.
    """
    # Initialize all submodules first
    for sub in submodules:
        sub["last_merged_bot_pr"] = None

    sub_by_name: dict[str, dict] = {}
    for sub in submodules:
        if sub["status"] == "ok":
            sub_by_name[sub["name"]] = sub

    if not sub_by_name:
        return

    sorted_names = sorted(sub_by_name.keys(), key=len, reverse=True)

    query = (
        f"repo:{PARENT_OWNER}/{PARENT_REPO} "
        f"author:{BOT_AUTHOR} is:pr is:merged sort:updated-desc"
    )
    try:
        resp = session.get(
            f"{API_BASE}/search/issues",
            params={"q": query, "per_page": 100, "sort": "updated", "order": "desc"},
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except (requests.RequestException, KeyError):
        return  # All already None

    matched_set: set[str] = set()

    for pr in items:
        matched = match_pr_to_submodule(pr, sorted_names)
        if matched and matched not in matched_set and matched in sub_by_name:
            merged_at = pr.get("pull_request", {}).get("merged_at")
            sub_by_name[matched]["last_merged_bot_pr"] = {
                "url": pr["html_url"],
                "merged_at": merged_at,
            }
            matched_set.add(matched)


def fetch_latest_repo_commits(
    session: requests.Session,
    submodules: list[dict],
) -> None:
    """Fetch latest commit from each submodule's own repo.

    For each submodule with ``status="ok"``, fetches the HEAD commit on
    its branch and records the URL and date.

    Sets ``sub["latest_repo_commit"]`` to a dict with ``url`` and ``date``
    keys — or ``None`` for unavailable submodules or on API error.
    """
    for sub in submodules:
        if sub["status"] != "ok":
            sub["latest_repo_commit"] = None
            continue

        try:
            url = (
                f"{API_BASE}/repos/{sub['owner']}/{sub['repo']}"
                f"/commits/{sub['branch']}"
            )
            resp = session.get(url)
            resp.raise_for_status()
            data = resp.json()

            sub["latest_repo_commit"] = {
                "url": data["html_url"],
                "date": data["commit"]["committer"]["date"],
            }
        except (requests.RequestException, KeyError, ValueError):
            sub["latest_repo_commit"] = None

        time.sleep(0.5)
