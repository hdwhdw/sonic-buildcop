"""Staleness computation module for submodule cadence analysis.

Computes per-submodule staleness thresholds from commit history and
classifies each submodule as green/yellow/red based on how far behind
its pinned SHA is relative to its own development cadence.

Exports:
    get_commit_dates  — fetch commit dates from GitHub Commits API
    compute_cadence   — compute median inter-commit interval
    compute_thresholds — derive yellow/red thresholds from cadence
    classify          — classify days/commits behind as green/yellow/red
    enrich_with_staleness — enrich submodule dicts with staleness fields
"""
import statistics
import time
from datetime import datetime, timezone, timedelta

import requests

# --- Constants ---

MIN_COMMITS_FOR_CADENCE = 5
MIN_MEDIAN_DAYS = 1.0
LOOKBACK_DAYS = 180
MAX_PAGES = 10

FALLBACK_THRESHOLDS = {
    "yellow_days": 30,
    "red_days": 60,
    "is_fallback": True,
}

API_BASE = "https://api.github.com"


# --- Functions ---


def get_commit_dates(
    session: requests.Session,
    owner: str,
    repo: str,
    branch: str,
    since_days: int = 180,
) -> list[datetime]:
    """Fetch commit dates from GitHub Commits API with pagination.

    Returns a sorted (ascending) list of datetime objects for all commits
    on ``branch`` within the last ``since_days`` days.
    """
    since = datetime.now(timezone.utc) - timedelta(days=since_days)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = f"{API_BASE}/repos/{owner}/{repo}/commits"
    params = {"sha": branch, "since": since_str, "per_page": 100}

    dates: list[datetime] = []
    for page in range(MAX_PAGES):
        resp = session.get(url, params=params)
        resp.raise_for_status()

        for commit in resp.json():
            date_str = commit["commit"]["committer"]["date"]
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            dates.append(dt)

        # Follow pagination
        next_link = resp.links.get("next", {}).get("url")
        if not next_link:
            break

        url = next_link
        params = None  # URL already contains query params
        time.sleep(0.5)  # Rate-limit courtesy delay

    dates.sort()
    return dates


def compute_cadence(commit_dates: list[datetime]) -> dict:
    """Compute median inter-commit interval from sorted commit dates.

    Returns a dict with:
        median_days  — median interval in days (or None if fallback)
        commit_count — total number of commits
        is_fallback  — True if too few commits for reliable cadence

    If fewer than MIN_COMMITS_FOR_CADENCE commits, returns fallback mode.
    Zero or near-zero medians are floored to MIN_MEDIAN_DAYS.
    """
    count = len(commit_dates)
    if count < MIN_COMMITS_FOR_CADENCE:
        return {
            "median_days": None,
            "commit_count": count,
            "is_fallback": True,
        }

    # Compute intervals between consecutive commits (in days)
    intervals = [
        (commit_dates[i + 1] - commit_dates[i]).total_seconds() / 86400
        for i in range(count - 1)
    ]

    median = max(statistics.median(intervals), MIN_MEDIAN_DAYS)

    return {
        "median_days": median,
        "commit_count": count,
        "is_fallback": False,
    }


def compute_thresholds(cadence: dict) -> dict:
    """Derive yellow/red day thresholds from cadence data.

    For normal repos: 2× median = yellow, 4× median = red (days).
    For fallback repos (<5 commits): use FALLBACK_THRESHOLDS.
    """
    if cadence["is_fallback"]:
        return dict(FALLBACK_THRESHOLDS)

    m = cadence["median_days"]
    return {
        "yellow_days": round(2 * m, 1),
        "red_days": round(4 * m, 1),
        "is_fallback": False,
    }


def classify(days_behind: float, thresholds: dict) -> str:
    """Classify staleness as green/yellow/red based on days behind only.

    Commits behind is shown for reference but does not affect classification.
    """
    if days_behind > thresholds["red_days"]:
        return "red"
    if days_behind > thresholds["yellow_days"]:
        return "yellow"
    return "green"


def enrich_with_staleness(
    session: requests.Session,
    submodules: list[dict],
) -> None:
    """Enrich submodule dicts in-place with staleness classification.

    For each submodule with status='ok':
        - Fetches 6-month commit history
        - Computes cadence and thresholds
        - Classifies as green/yellow/red

    For unavailable submodules, sets all staleness fields to None.

    Adds fields: staleness_status, median_days, commit_count_6m, thresholds
    """
    for sub in submodules:
        if sub["status"] != "ok":
            sub["staleness_status"] = None
            sub["median_days"] = None
            sub["commit_count_6m"] = None
            sub["thresholds"] = None
            continue

        try:
            dates = get_commit_dates(
                session, sub["owner"], sub["repo"], sub["branch"]
            )
            cadence = compute_cadence(dates)
            thresholds = compute_thresholds(cadence)
            status = classify(sub["days_behind"], thresholds)

            sub["staleness_status"] = status
            sub["median_days"] = cadence["median_days"]
            sub["commit_count_6m"] = cadence["commit_count"]
            sub["thresholds"] = thresholds

        except (requests.RequestException, KeyError, ValueError):
            sub["staleness_status"] = None
            sub["median_days"] = None
            sub["commit_count_6m"] = None
            sub["thresholds"] = None

        time.sleep(0.5)  # Rate-limit courtesy delay between submodules
