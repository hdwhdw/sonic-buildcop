"""Tests for the staleness computation module."""
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from staleness import (
    get_commit_dates,
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
    """median_days=2.0 → yellow_days=4.0, red_days=8.0, yellow_commits=2, red_commits=4."""
    cadence = {"median_days": 2.0, "commit_count": 10, "is_fallback": False}
    result = compute_thresholds(cadence)
    assert result["yellow_days"] == 4.0
    assert result["red_days"] == 8.0
    assert result["yellow_commits"] == 2
    assert result["red_commits"] == 4
    assert result["is_fallback"] is False


def test_compute_thresholds_frequent_repo():
    """median_days=1.0 → yellow_days=2.0, red_days=4.0."""
    cadence = {"median_days": 1.0, "commit_count": 30, "is_fallback": False}
    result = compute_thresholds(cadence)
    assert result["yellow_days"] == 2.0
    assert result["red_days"] == 4.0


def test_compute_thresholds_slow_repo():
    """median_days=8.0 → yellow_days=16.0, red_days=32.0."""
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
    assert result["yellow_commits"] == 10
    assert result["red_commits"] == 20
    assert result["is_fallback"] is True


# ---------------------------------------------------------------------------
# classify tests
# ---------------------------------------------------------------------------


def test_classify_green():
    """days=1, commits=1, thresholds with yellow_days=4, red_days=8 → green."""
    thresholds = {
        "yellow_days": 4.0, "red_days": 8.0,
        "yellow_commits": 2, "red_commits": 4,
        "is_fallback": False,
    }
    assert classify(1, 1, thresholds) == "green"


def test_classify_yellow_by_days():
    """days=5 > yellow_days=4.0, commits=0 → yellow."""
    thresholds = {
        "yellow_days": 4.0, "red_days": 8.0,
        "yellow_commits": 2, "red_commits": 4,
        "is_fallback": False,
    }
    assert classify(5, 0, thresholds) == "yellow"


def test_classify_yellow_by_commits():
    """days=0, commits=3 > yellow_commits=2 → yellow."""
    thresholds = {
        "yellow_days": 4.0, "red_days": 8.0,
        "yellow_commits": 2, "red_commits": 4,
        "is_fallback": False,
    }
    assert classify(0, 3, thresholds) == "yellow"


def test_classify_red_by_days():
    """days=10 > red_days=8.0, commits=0 → red."""
    thresholds = {
        "yellow_days": 4.0, "red_days": 8.0,
        "yellow_commits": 2, "red_commits": 4,
        "is_fallback": False,
    }
    assert classify(10, 0, thresholds) == "red"


def test_classify_red_by_commits():
    """days=0, commits=5 > red_commits=4 → red."""
    thresholds = {
        "yellow_days": 4.0, "red_days": 8.0,
        "yellow_commits": 2, "red_commits": 4,
        "is_fallback": False,
    }
    assert classify(0, 5, thresholds) == "red"


def test_classify_worst_of_rule():
    """days=5 (yellow), commits=5 (red) → red (worst wins)."""
    thresholds = {
        "yellow_days": 4.0, "red_days": 8.0,
        "yellow_commits": 2, "red_commits": 4,
        "is_fallback": False,
    }
    assert classify(5, 5, thresholds) == "red"


# ---------------------------------------------------------------------------
# get_commit_dates tests (mocked)
# ---------------------------------------------------------------------------


def test_get_commit_dates_single_page(mock_commits_page_1):
    """5 commits on one page, no next link → returns 5 sorted datetimes."""
    session = MagicMock()
    resp = MagicMock()
    resp.json.return_value = mock_commits_page_1
    resp.links = {}  # no next page
    session.get.return_value = resp

    dates = get_commit_dates(session, "sonic-net", "sonic-swss", "master")
    assert len(dates) == 5
    # Verify sorted ascending
    for i in range(len(dates) - 1):
        assert dates[i] <= dates[i + 1]
    # Verify actual datetime objects
    assert dates[0].year == 2025
    assert dates[0].month == 8
    assert dates[0].day == 1


def test_get_commit_dates_with_pagination(mock_commits_page_1, mock_commits_page_2):
    """2 pages of commits → returns all 8 commits sorted."""
    session = MagicMock()

    # Page 1 response: has next link
    resp1 = MagicMock()
    resp1.json.return_value = mock_commits_page_1
    resp1.links = {
        "next": {"url": "https://api.github.com/repos/sonic-net/sonic-swss/commits?page=2"}
    }

    # Page 2 response: no next link
    resp2 = MagicMock()
    resp2.json.return_value = mock_commits_page_2
    resp2.links = {}

    session.get.side_effect = [resp1, resp2]

    with patch("staleness.time.sleep"):
        dates = get_commit_dates(session, "sonic-net", "sonic-swss", "master")

    assert len(dates) == 8
    # Verify sorted ascending
    for i in range(len(dates) - 1):
        assert dates[i] <= dates[i + 1]
    assert dates[-1].day == 8  # Aug 8 is last


# ---------------------------------------------------------------------------
# enrich_with_staleness tests (integration-level with mocks)
# ---------------------------------------------------------------------------


@patch("staleness.time.sleep")
@patch("staleness.get_commit_dates")
def test_enrich_adds_staleness_fields(mock_get_dates, mock_sleep, sample_submodule_ok):
    """Submodule with status=ok gets staleness fields added."""
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
@patch("staleness.get_commit_dates")
def test_enrich_skips_unavailable(mock_get_dates, mock_sleep, sample_submodule_unavailable):
    """Submodule with status=unavailable gets all staleness fields set to None."""
    submodules = [sample_submodule_unavailable]
    enrich_with_staleness(MagicMock(), submodules)

    sub = submodules[0]
    assert sub["staleness_status"] is None
    assert sub["median_days"] is None
    assert sub["commit_count_6m"] is None
    assert sub["thresholds"] is None
    # get_commit_dates should NOT have been called
    mock_get_dates.assert_not_called()
