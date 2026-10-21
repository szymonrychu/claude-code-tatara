"""Shared fixture: a copy of the fixture tree in tmp_path (load_config resolves via git)."""

import shutil
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "tree"


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    dest = tmp_path / "tree"
    shutil.copytree(FIXTURE, dest)
    return dest
