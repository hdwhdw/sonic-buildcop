"""Tests for the data enrichment module — Task 1 RED phase (basic importability)."""
from enrichment import (
    match_pr_to_submodule,
    get_ci_status_for_pr,
    fetch_open_bot_prs,
    fetch_merged_bot_prs,
    fetch_latest_repo_commits,
)


def test_match_pr_to_submodule_exists():
    """match_pr_to_submodule should be callable."""
    assert callable(match_pr_to_submodule)


def test_get_ci_status_for_pr_exists():
    """get_ci_status_for_pr should be callable."""
    assert callable(get_ci_status_for_pr)


def test_fetch_open_bot_prs_exists():
    """fetch_open_bot_prs should be callable."""
    assert callable(fetch_open_bot_prs)


def test_fetch_merged_bot_prs_exists():
    """fetch_merged_bot_prs should be callable."""
    assert callable(fetch_merged_bot_prs)


def test_fetch_latest_repo_commits_exists():
    """fetch_latest_repo_commits should be callable."""
    assert callable(fetch_latest_repo_commits)
