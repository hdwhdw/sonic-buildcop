"""Typed data models for SONiC build infrastructure tools.

Defines TypedDict contracts for data flowing through the submodule-status
pipeline: collector → staleness → enrichment → renderer.  Uses NotRequired
for fields that are progressively populated at each pipeline stage.
"""

from typing import NotRequired, TypedDict


class OpenBotPR(TypedDict):
    """An open pull request created by the mssonicbld bot."""

    url: str
    age_days: float
    ci_status: str | None


class LastMergedBotPR(TypedDict):
    """The most recently merged bot PR for a submodule."""

    url: str
    merged_at: str | None


class LatestRepoCommit(TypedDict):
    """The latest commit on a submodule's upstream branch."""

    url: str
    date: str


class Cadence(TypedDict):
    """Pointer-bump cadence statistics for a submodule."""

    median_days: float | None
    commit_count: int
    is_fallback: bool


class Thresholds(TypedDict):
    """Yellow/red staleness thresholds derived from bump cadence."""

    yellow_days: float
    red_days: float
    is_fallback: bool


class SubmoduleInfo(TypedDict):
    """Complete submodule record accumulated across pipeline stages.

    Base fields are always present after parse_gitmodules.  Pipeline-stage
    fields are progressively added by collect_submodule, enrich_with_staleness,
    and enrich_with_details — marked NotRequired so a partial dict is valid at
    any stage.
    """

    # --- Base fields (after parse_gitmodules) ---
    name: str
    path: str
    url: str
    owner: str
    repo: str
    branch: str | None

    # --- After collect_submodule ---
    pinned_sha: NotRequired[str | None]
    commits_behind: NotRequired[int | None]
    days_behind: NotRequired[float | None]
    compare_url: NotRequired[str | None]
    status: NotRequired[str]
    error: NotRequired[str | None]

    # --- After enrich_with_staleness ---
    staleness_status: NotRequired[str | None]
    median_days: NotRequired[float | None]
    commit_count_6m: NotRequired[int | None]
    thresholds: NotRequired[Thresholds | None]

    # --- After enrich_with_details ---
    open_bot_pr: NotRequired[OpenBotPR | None]
    last_merged_bot_pr: NotRequired[LastMergedBotPR | None]
    latest_repo_commit: NotRequired[LatestRepoCommit | None]
    avg_delay_days: NotRequired[float | None]
