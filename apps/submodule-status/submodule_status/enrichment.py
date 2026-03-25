"""Data enrichment module for submodule detail information.

Fetches bot PR status, latest repo commits, CI check status, and average
delay for each submodule. Follows the staleness.py pattern: enrich
submodule dicts in-place.

Exports:
    match_pr_to_submodule           — match a PR title to a submodule name (longest-first)
    get_ci_status_for_pr            — aggregate CI check-run status for a PR
    fetch_open_bot_prs              — batch-fetch open bot PRs and enrich submodules
    fetch_merged_bot_prs            — batch-fetch merged bot PRs and enrich submodules
    fetch_latest_repo_commits       — fetch latest commit from each submodule's repo
    compute_avg_delay_for_submodule — compute mean delay for a single submodule
    compute_avg_delay               — compute mean delay for all submodules in-place
    enrich_with_details             — main entry point calling all enrichment functions
"""
import logging
import statistics
import time
from datetime import datetime, timezone

import requests

from buildcop_common.config import API_BASE, BOT_AUTHOR, PARENT_OWNER, PARENT_REPO
from buildcop_common.exceptions import APIError
from buildcop_common.github import check_response

# --- Constants ---

logger = logging.getLogger(__name__)


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
        check_response(pr_resp)
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
        check_response(checks_resp)
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

    except (APIError, requests.RequestException, KeyError):
        logger.warning("Failed to get CI status for PR #%d", pr_number, exc_info=True)
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
        check_response(resp)
        items = resp.json().get("items", [])
    except (APIError, requests.RequestException, KeyError):
        logger.warning("Failed to fetch open bot PRs", exc_info=True)
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
        check_response(resp)
        items = resp.json().get("items", [])
    except (APIError, requests.RequestException, KeyError):
        logger.warning("Failed to fetch merged bot PRs", exc_info=True)
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
            check_response(resp)
            data = resp.json()

            sub["latest_repo_commit"] = {
                "url": data["html_url"],
                "date": data["commit"]["committer"]["date"],
            }
        except (APIError, requests.RequestException, KeyError, ValueError):
            logger.warning("Failed to fetch latest commit for %s", sub["name"], exc_info=True)
            sub["latest_repo_commit"] = None

        time.sleep(0.5)


def compute_avg_delay_for_submodule(
    session: requests.Session,
    submodule_path: str,
    sub_owner: str,
    sub_repo: str,
    num_bumps: int = 5,
) -> float | None:
    """Compute average delay between repo commits and pointer bumps.

    Looks at the last ``num_bumps`` commits in sonic-buildimage that touched
    the submodule path, determines what SHA each bump pointed to, and
    computes the delay between that SHA's commit date and the bump date.

    Returns mean delay in days (rounded to 1 decimal), or ``None`` if fewer
    than 2 valid data points.
    """
    # Step 1: Get bump history from parent repo
    url = f"{API_BASE}/repos/{PARENT_OWNER}/{PARENT_REPO}/commits"
    params = {"path": submodule_path, "per_page": num_bumps}
    try:
        resp = session.get(url, params=params)
        check_response(resp)
        bumps = resp.json()
    except (APIError, requests.RequestException, KeyError, ValueError):
        logger.warning("Failed to fetch bump history for %s", submodule_path, exc_info=True)
        return None

    if not isinstance(bumps, list) or len(bumps) < 2:
        return None

    delays: list[float] = []
    for bump in bumps:
        try:
            bump_date_str = bump["commit"]["committer"]["date"]
            bump_date = datetime.fromisoformat(
                bump_date_str.replace("Z", "+00:00")
            )
            bump_sha = bump["sha"]

            # Step 2: Get submodule SHA at this bump
            contents_url = (
                f"{API_BASE}/repos/{PARENT_OWNER}/{PARENT_REPO}"
                f"/contents/{submodule_path}"
            )
            contents_resp = session.get(contents_url, params={"ref": bump_sha})
            check_response(contents_resp)
            sub_sha = contents_resp.json()["sha"]

            # Step 3: Get submodule commit date
            commit_url = (
                f"{API_BASE}/repos/{sub_owner}/{sub_repo}/commits/{sub_sha}"
            )
            commit_resp = session.get(commit_url)
            check_response(commit_resp)
            commit_date_str = commit_resp.json()["commit"]["committer"]["date"]
            commit_date = datetime.fromisoformat(
                commit_date_str.replace("Z", "+00:00")
            )

            # Step 4: Compute delay (filter negatives per Pitfall 5)
            delay_days = (bump_date - commit_date).total_seconds() / 86400
            if delay_days >= 0:
                delays.append(delay_days)

        except (APIError, requests.RequestException, KeyError, ValueError):
            logger.warning("Skipping bump for %s/%s", sub_owner, sub_repo, exc_info=True)
            continue  # Skip this bump, try next

        time.sleep(0.5)

    if len(delays) < 2:
        return None

    return round(statistics.mean(delays), 1)


def compute_avg_delay(
    session: requests.Session,
    submodules: list[dict],
) -> None:
    """Compute average delay for each submodule in-place.

    For each submodule with ``status='ok'``, computes the average delay
    between repo commits and pointer bumps. Sets ``avg_delay_days`` to
    the result (float or ``None``).
    """
    for sub in submodules:
        if sub["status"] != "ok":
            sub["avg_delay_days"] = None
            continue

        try:
            sub["avg_delay_days"] = compute_avg_delay_for_submodule(
                session,
                sub["path"],
                sub["owner"],
                sub["repo"],
            )
        except (APIError, requests.RequestException, KeyError, ValueError):
            logger.warning("Failed to compute avg delay for %s", sub["name"], exc_info=True)
            sub["avg_delay_days"] = None

        time.sleep(0.5)


def enrich_with_details(
    session: requests.Session,
    submodules: list[dict],
) -> None:
    """Main enrichment entry point — enrich submodule dicts in-place.

    Called from collector.py main() after enrich_with_staleness().
    Adds: open_bot_pr, last_merged_bot_pr, latest_repo_commit, avg_delay_days.
    """
    fetch_open_bot_prs(session, submodules)
    fetch_merged_bot_prs(session, submodules)
    fetch_latest_repo_commits(session, submodules)
    compute_avg_delay(session, submodules)
