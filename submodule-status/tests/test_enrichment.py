"""Tests for the data enrichment module."""
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import requests

from enrichment import (
    match_pr_to_submodule,
    get_ci_status_for_pr,
    fetch_open_bot_prs,
    fetch_merged_bot_prs,
    fetch_latest_repo_commits,
)


# ---------------------------------------------------------------------------
# match_pr_to_submodule tests
# ---------------------------------------------------------------------------


def test_match_pr_longest_first():
    """PR title with 'sonic-swss-common' should match the longer name first."""
    pr = {"title": "[submodule] Update submodule src/sonic-swss-common to latest"}
    names = ["sonic-swss-common", "sonic-swss"]  # pre-sorted longest-first
    assert match_pr_to_submodule(pr, names) == "sonic-swss-common"


def test_match_pr_basic():
    """PR title containing 'sonic-swss' should match."""
    pr = {"title": "Update sonic-swss to latest"}
    names = ["sonic-swss"]
    assert match_pr_to_submodule(pr, names) == "sonic-swss"


def test_match_pr_no_match():
    """PR title with no known submodule name should return None."""
    pr = {"title": "Unrelated change to build system"}
    names = ["sonic-swss", "sonic-sairedis"]
    assert match_pr_to_submodule(pr, names) is None


# ---------------------------------------------------------------------------
# get_ci_status_for_pr tests
# ---------------------------------------------------------------------------


def test_ci_status_all_pass(mock_pr_detail_response, mock_check_runs_all_pass):
    """All check runs completed with success/neutral → 'pass'."""
    session = MagicMock(spec=requests.Session)

    resp_pr = MagicMock()
    resp_pr.json.return_value = mock_pr_detail_response

    resp_checks = MagicMock()
    resp_checks.json.return_value = mock_check_runs_all_pass

    session.get.side_effect = [resp_pr, resp_checks]

    result = get_ci_status_for_pr(session, 101)
    assert result == "pass"


def test_ci_status_one_failure(mock_pr_detail_response, mock_check_runs_one_fail):
    """One check with conclusion=failure → 'fail'."""
    session = MagicMock(spec=requests.Session)

    resp_pr = MagicMock()
    resp_pr.json.return_value = mock_pr_detail_response

    resp_checks = MagicMock()
    resp_checks.json.return_value = mock_check_runs_one_fail

    session.get.side_effect = [resp_pr, resp_checks]

    result = get_ci_status_for_pr(session, 101)
    assert result == "fail"


def test_ci_status_pending(mock_pr_detail_response, mock_check_runs_pending):
    """One check still in_progress → 'pending'."""
    session = MagicMock(spec=requests.Session)

    resp_pr = MagicMock()
    resp_pr.json.return_value = mock_pr_detail_response

    resp_checks = MagicMock()
    resp_checks.json.return_value = mock_check_runs_pending

    session.get.side_effect = [resp_pr, resp_checks]

    result = get_ci_status_for_pr(session, 101)
    assert result == "pending"


def test_ci_status_no_checks(mock_pr_detail_response, mock_check_runs_empty):
    """No check runs at all → None."""
    session = MagicMock(spec=requests.Session)

    resp_pr = MagicMock()
    resp_pr.json.return_value = mock_pr_detail_response

    resp_checks = MagicMock()
    resp_checks.json.return_value = mock_check_runs_empty

    session.get.side_effect = [resp_pr, resp_checks]

    result = get_ci_status_for_pr(session, 101)
    assert result is None


def test_ci_status_api_error():
    """API error (RequestException) → None."""
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = requests.RequestException("timeout")

    result = get_ci_status_for_pr(session, 101)
    assert result is None


# ---------------------------------------------------------------------------
# fetch_open_bot_prs tests
# ---------------------------------------------------------------------------


@patch("enrichment.get_ci_status_for_pr", return_value="pass")
@patch("enrichment.time.sleep")
def test_fetch_open_bot_prs(mock_sleep, mock_ci, sample_submodule_list, mock_search_open_prs):
    """Two PRs should match two submodules; unavailable submodule gets None."""
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = mock_search_open_prs
    session.get.return_value = resp

    fetch_open_bot_prs(session, sample_submodule_list)

    # sonic-swss matched
    swss = sample_submodule_list[0]
    assert swss["open_bot_pr"] is not None
    assert swss["open_bot_pr"]["url"] == "https://github.com/sonic-net/sonic-buildimage/pull/101"
    assert isinstance(swss["open_bot_pr"]["age_days"], float)
    assert swss["open_bot_pr"]["age_days"] > 0
    assert swss["open_bot_pr"]["ci_status"] == "pass"

    # sonic-swss-common matched
    common = sample_submodule_list[1]
    assert common["open_bot_pr"] is not None
    assert common["open_bot_pr"]["url"] == "https://github.com/sonic-net/sonic-buildimage/pull/102"

    # sonic-sairedis (unavailable) → None
    sairedis = sample_submodule_list[2]
    assert sairedis["open_bot_pr"] is None


@patch("enrichment.time.sleep")
def test_fetch_open_bot_prs_empty(mock_sleep, sample_submodule_list):
    """Empty search response → all submodules get open_bot_pr=None."""
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = {"total_count": 0, "items": []}
    session.get.return_value = resp

    fetch_open_bot_prs(session, sample_submodule_list)

    for sub in sample_submodule_list:
        assert sub["open_bot_pr"] is None


@patch("enrichment.time.sleep")
def test_fetch_open_bot_prs_api_error(mock_sleep, sample_submodule_list):
    """Search API error → all submodules get open_bot_pr=None, no crash."""
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = requests.RequestException("Search API down")

    fetch_open_bot_prs(session, sample_submodule_list)

    for sub in sample_submodule_list:
        assert sub["open_bot_pr"] is None


# ---------------------------------------------------------------------------
# fetch_merged_bot_prs tests
# ---------------------------------------------------------------------------


def test_fetch_merged_bot_prs(sample_submodule_list, mock_search_merged_prs):
    """Merged PR should match sonic-swss with url and merged_at."""
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = mock_search_merged_prs
    session.get.return_value = resp

    fetch_merged_bot_prs(session, sample_submodule_list)

    swss = sample_submodule_list[0]
    assert swss["last_merged_bot_pr"] is not None
    assert swss["last_merged_bot_pr"]["url"] == "https://github.com/sonic-net/sonic-buildimage/pull/99"
    assert swss["last_merged_bot_pr"]["merged_at"] == "2025-01-12T15:30:00Z"


def test_fetch_merged_bot_prs_no_match(sample_submodule_list):
    """Empty search response → all submodules get last_merged_bot_pr=None."""
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = {"total_count": 0, "items": []}
    session.get.return_value = resp

    fetch_merged_bot_prs(session, sample_submodule_list)

    for sub in sample_submodule_list:
        assert sub["last_merged_bot_pr"] is None


# ---------------------------------------------------------------------------
# fetch_latest_repo_commits tests
# ---------------------------------------------------------------------------


@patch("enrichment.time.sleep")
def test_fetch_latest_repo_commits(mock_sleep, sample_submodule_list, mock_latest_commit_response):
    """OK submodule gets latest_repo_commit with url and date."""
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = mock_latest_commit_response
    session.get.return_value = resp

    fetch_latest_repo_commits(session, sample_submodule_list)

    swss = sample_submodule_list[0]
    assert swss["latest_repo_commit"] is not None
    assert swss["latest_repo_commit"]["url"] == "https://github.com/sonic-net/sonic-swss/commit/def456abc789"
    assert swss["latest_repo_commit"]["date"] == "2025-02-19T08:00:00Z"


@patch("enrichment.time.sleep")
def test_fetch_latest_repo_commits_unavailable(mock_sleep, sample_submodule_list, mock_latest_commit_response):
    """Unavailable submodule gets latest_repo_commit=None."""
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.json.return_value = mock_latest_commit_response
    session.get.return_value = resp

    fetch_latest_repo_commits(session, sample_submodule_list)

    sairedis = sample_submodule_list[2]
    assert sairedis["latest_repo_commit"] is None


@patch("enrichment.time.sleep")
def test_fetch_latest_repo_commits_api_error(mock_sleep):
    """API error → latest_repo_commit=None (no crash)."""
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = requests.RequestException("API down")

    submodules = [
        {
            "name": "sonic-swss",
            "path": "src/sonic-swss",
            "url": "https://github.com/sonic-net/sonic-swss",
            "owner": "sonic-net",
            "repo": "sonic-swss",
            "branch": "master",
            "status": "ok",
            "error": None,
        },
    ]

    fetch_latest_repo_commits(session, submodules)

    assert submodules[0]["latest_repo_commit"] is None
