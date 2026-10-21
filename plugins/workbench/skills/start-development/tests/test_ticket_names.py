"""ticket_names: the one lookup from a tree or branch name to its ticket (design D3, D10)."""

import importlib.util
import re
import sys
from pathlib import Path

import pytest
from test_ticket_check import epic, task

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ticket.py"


@pytest.fixture(scope="module")
def tk():
    sys.path.insert(0, str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("ticket_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_maps_epics_and_tasks_in_every_phase(tk, tmp_path):
    root = tmp_path / "plans"
    root.mkdir()
    a = epic(root, "Alpha", "todo")
    b = epic(root, "Beta", "in-progress")
    c = epic(root, "Gamma", "done")
    task(root, a, "Build core")
    task(root, b, "Wire it")
    names = tk.ticket_names(root)
    assert names[a] == (a, None) and names[b] == (b, None) and names[c] == (c, None)
    assert names[f"{a}-build-core"] == (a, "build-core")
    assert names[f"{b}-wire-it"] == (b, "wire-it")


def test_hyphenated_epic_and_task_are_not_split(tk, tmp_path):
    root = tmp_path / "plans"
    root.mkdir()
    a = epic(root, "Alpha one", "in-progress")
    ab = epic(root, "Alpha one two", "in-progress")
    task(root, a, "Two three")
    names = tk.ticket_names(root)
    assert names[f"{a}-two-three"] == (a, "two-three")
    assert names[ab] == (ab, None)
    assert "alpha" not in names


def test_unknown_name_is_absent(tk, tmp_path):
    root = tmp_path / "plans"
    root.mkdir()
    epic(root, "Alpha")
    assert "plain-name" not in tk.ticket_names(root)


def test_ticket_py_has_no_name_parser():
    src = SCRIPT.read_text()
    assert "}--{" not in src
    assert not re.search(r'split\(\s*"--"', src)
