"""Tests for the staleness computation module."""
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import requests

from staleness import (
    get_bump_dates,
    compute_cadence,
    compute_thresholds,
    classify,
    enrich_with_staleness,
)


# ---------------------------------------------------------------------------
# compute_cadence tests
# ---------------------------------------------------------------------------


def test_compute_cadence_regular_commits():
    """10 commits 1 day apart → median_days=1.0, commit_count=10, is_fallback=False."""
    base = datetime(2025, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    dates = [base + timedelta(days=i) for i in range(10)]
    result = compute_cadence(dates)
    assert result["median_days"] == 1.0
    assert result["commit_count"] == 10
    assert result["is_fallback"] is False


def test_compute_cadence_weekly_commits():
    """10 commits 7 days apart → median_days=7.0."""
    base = datetime(2025, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    dates = [base + timedelta(days=i * 7) for i in range(10)]
    result = compute_cadence(dates)
    assert result["median_days"] == 7.0
    assert result["commit_count"] == 10
    assert result["is_fallback"] is False


def test_compute_cadence_median_resists_outliers():
    """9 × 1-day intervals + 1 × 30-day gap → median still close to 1.0."""
    base = datetime(2025, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    dates = [base + timedelta(days=i) for i in range(9)]
    dates.append(base + timedelta(days=9 + 30))  # 30-day gap at end
    result = compute_cadence(dates)
    assert result["median_days"] == 1.0  # median resists the outlier
    assert result["commit_count"] == 10
    assert result["is_fallback"] is False


def test_compute_cadence_fallback_few_commits():
    """3 commits → is_fallback=True, median_days=None."""
    base = datetime(2025, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    dates = [base + timedelta(days=i) for i in range(3)]
    result = compute_cadence(dates)
    assert result["median_days"] is None
    assert result["commit_count"] == 3
    assert result["is_fallback"] is True


def test_compute_cadence_fallback_zero_commits():
    """Empty list → is_fallback=True, median_days=None, commit_count=0."""
    result = compute_cadence([])
    assert result["median_days"] is None
    assert result["commit_count"] == 0
    assert result["is_fallback"] is True


def test_compute_cadence_minimum_floor():
    """10 commits all within 1 hour (intervals ≈ 0) → median_days=1.0 (floor)."""
    base = datetime(2025, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    dates = [base + timedelta(minutes=i * 6) for i in range(10)]
    result = compute_cadence(dates)
    assert result["median_days"] == 1.0  # floor applied
    assert result["commit_count"] == 10
    assert result["is_fallback"] is False


# ---------------------------------------------------------------------------
# compute_thresholds tests
# ---------------------------------------------------------------------------


def test_compute_thresholds_from_cadence():
    """median_days=2.0 → yellow_days=4.0, red_days=8.0."""
    cadence = {"median_days": 2.0, "commit_count": 10, "is_fallback": False}
    result = compute_thresholds(cadence)
    assert result["yellow_days"] == 4.0
    assert result["red_days"] == 8.0
    assert result["is_fallback"] is False


def test_compute_thresholds_frequent_repo():
    """median_days=1.0 → yellow_days=2.0, red_days=4.0."""
    cadence = {"median_days": 1.0, "commit_count": 30, "is_fallback": False}
    result = compute_thresholds(cadence)
    assert result["yellow_days"] == 2.0
    assert result["red_days"] == 4.0


def test_compute_thresholds_slow_repo():
    """median_days=8.0 → yellow_days=16.0, red_days=32.0 (under cap)."""
    cadence = {"median_days": 8.0, "commit_count": 15, "is_fallback": False}
    result = compute_thresholds(cadence)
    assert result["yellow_days"] == 16.0
    assert result["red_days"] == 32.0


def test_compute_thresholds_fallback():
    """is_fallback=True → fixed fallback thresholds."""
    cadence = {"median_days": None, "commit_count": 3, "is_fallback": True}
    result = compute_thresholds(cadence)
    assert result["yellow_days"] == 30
    assert result["red_days"] == 60
    assert result["is_fallback"] is True


def test_compute_thresholds_capped_very_slow_repo():
    """median_days=20.0 → uncapped would be 40/80, capped to 30/60."""
    cadence = {"median_days": 20.0, "commit_count": 15, "is_fallback": False}
    result = compute_thresholds(cadence)
    assert result["yellow_days"] == 30
    assert result["red_days"] == 60
    assert result["is_fallback"] is False


def test_compute_thresholds_capped_boundary():
    """median_days=14.0 → yellow=28.0 (under 30), red=56.0 (under 60) — no cap applied."""
    cadence = {"median_days": 14.0, "commit_count": 10, "is_fallback": False}
    result = compute_thresholds(cadence)
    assert result["yellow_days"] == 28.0
    assert result["red_days"] == 56.0
    assert result["is_fallback"] is False


def test_compute_thresholds_capped_both_hit():
    """median_days=18.0 → yellow=min(36,30)=30, red=min(72,60)=60."""
    cadence = {"median_days": 18.0, "commit_count": 15, "is_fallback": False}
    result = compute_thresholds(cadence)
    assert result["yellow_days"] == 30
    assert result["red_days"] == 60
    assert result["is_fallback"] is False


def test_classify_with_capped_thresholds():
    """Slow repo (median=125d) with 40 days behind → yellow (not green) due to cap."""
    cadence = {"median_days": 125.0, "commit_count": 30, "is_fallback": False}
    thresholds = compute_thresholds(cadence)
    assert thresholds["yellow_days"] == 30
    assert thresholds["red_days"] == 60
    assert classify(40, thresholds) == "yellow"


# ---------------------------------------------------------------------------
# classify tests
# ---------------------------------------------------------------------------


def test_classify_green():
    """days=1 < yellow_days=4 → green."""
    thresholds = {"yellow_days": 4.0, "red_days": 8.0, "is_fallback": False}
    assert classify(1, thresholds) == "green"


def test_classify_yellow_by_days():
    """days=5 > yellow_days=4.0 → yellow."""
    thresholds = {"yellow_days": 4.0, "red_days": 8.0, "is_fallback": False}
    assert classify(5, thresholds) == "yellow"


def test_classify_red_by_days():
    """days=10 > red_days=8.0 → red."""
    thresholds = {"yellow_days": 4.0, "red_days": 8.0, "is_fallback": False}
    assert classify(10, thresholds) == "red"


# ---------------------------------------------------------------------------
# get_bump_dates tests (mocked)
# ---------------------------------------------------------------------------


def test_get_bump_dates_returns_sorted_dates(mock_bump_response):
    """5 bump commits (unsorted) → returns 5 sorted ascending datetimes."""
    session = MagicMock()
    resp = MagicMock()
    resp.json.return_value = mock_bump_response
    session.get.return_value = resp

    dates = get_bump_dates(session, "src/sonic-swss")
    assert len(dates) == 5
    # Verify sorted ascending
    for i in range(len(dates) - 1):
        assert dates[i] <= dates[i + 1]
    # Verify actual datetime objects with correct dates
    assert dates[0].day == 1  # Aug 1 is earliest
    assert dates[-1].day == 5  # Aug 5 is latest


def test_get_bump_dates_empty_response():
    """Empty commits list → returns []."""
    session = MagicMock()
    resp = MagicMock()
    resp.json.return_value = []
    session.get.return_value = resp

    dates = get_bump_dates(session, "src/sonic-swss")
    assert dates == []


def test_get_bump_dates_api_error():
    """RequestException → returns []."""
    session = MagicMock()
    session.get.side_effect = requests.RequestException("timeout")

    dates = get_bump_dates(session, "src/sonic-swss")
    assert dates == []


def test_get_bump_dates_non_list_response():
    """Non-list response (e.g., API error dict) → returns []."""
    session = MagicMock()
    resp = MagicMock()
    resp.json.return_value = {"message": "API rate limit exceeded"}
    session.get.return_value = resp

    dates = get_bump_dates(session, "src/sonic-swss")
    assert dates == []


# ---------------------------------------------------------------------------
# enrich_with_staleness tests (integration-level with mocks)
# ---------------------------------------------------------------------------


@patch("staleness.time.sleep")
@patch("staleness.get_bump_dates")
def test_enrich_adds_staleness_fields(mock_get_dates, mock_sleep, sample_submodule_ok):
    """Submodule with status=ok gets staleness fields added via bump dates."""
    base = datetime(2025, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
    mock_get_dates.return_value = [base + timedelta(days=i) for i in range(10)]

    submodules = [sample_submodule_ok]
    enrich_with_staleness(MagicMock(), submodules)

    sub = submodules[0]
    assert sub["staleness_status"] in ("green", "yellow", "red")
    assert sub["median_days"] is not None
    assert sub["commit_count_6m"] == 10
    assert sub["thresholds"] is not None
    assert "yellow_days" in sub["thresholds"]
    assert "red_days" in sub["thresholds"]


@patch("staleness.time.sleep")
@patch("staleness.get_bump_dates")
def test_enrich_skips_unavailable(mock_get_dates, mock_sleep, sample_submodule_unavailable):
    """Submodule with status=unavailable gets all staleness fields set to None."""
    submodules = [sample_submodule_unavailable]
    enrich_with_staleness(MagicMock(), submodules)

    sub = submodules[0]
    assert sub["staleness_status"] is None
    assert sub["median_days"] is None
    assert sub["commit_count_6m"] is None
    assert sub["thresholds"] is None
    # get_bump_dates should NOT have been called
    mock_get_dates.assert_not_called()
