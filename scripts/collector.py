"""Collect submodule staleness data from sonic-net/sonic-buildimage via GitHub API."""
import configparser
import json
import os
import time
from datetime import datetime, timezone

import requests

TARGET_SUBMODULES = [
    "sonic-swss", "sonic-utilities", "sonic-platform-daemons",
    "sonic-sairedis", "sonic-gnmi", "sonic-swss-common",
    "sonic-platform-common", "sonic-host-services",
    "sonic-linux-kernel", "sonic-dash-ha",
]


def parse_gitmodules(content: str) -> list[dict]:
    raise NotImplementedError


def get_pinned_sha(session: requests.Session, submodule_path: str) -> str:
    raise NotImplementedError


def get_default_branch(session: requests.Session, owner: str, repo: str) -> str:
    raise NotImplementedError


def get_staleness(session: requests.Session, owner: str, repo: str, pinned_sha: str, branch: str) -> dict:
    raise NotImplementedError


def build_compare_url(owner: str, repo: str, pinned_sha: str, branch: str) -> str:
    raise NotImplementedError


def collect_submodule(session: requests.Session, submodule: dict, retries: int = 3) -> dict:
    raise NotImplementedError


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
