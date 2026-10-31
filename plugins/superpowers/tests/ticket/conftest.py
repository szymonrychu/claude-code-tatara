"""Shared fixtures for the ticket.py git-repo tests."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ticket_repo_helpers import init_repo  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    return init_repo(tmp_path / "proj")


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"
