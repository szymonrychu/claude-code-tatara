"""U3 at epic level: doc files and done/merged tasks do not count as cross-epic file overlaps."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_ticket_check import check, cli, epic, task  # noqa: E402


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "plans"
    r.mkdir()
    return r


def two_epics(root, files_a, files_b, mark_done=False):
    a = epic(root, "Alpha thing", "in-progress")
    task(root, a, "Alpha task", files_a)
    b = epic(root, "Beta thing")
    return a, b


def test_doc_overlap_not_refused(root):
    a, b = two_epics(root, "CHANGELOG.md,docs/README.md", "")
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        b,
        "--title",
        "Beta task",
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        "CHANGELOG.md,docs/README.md",
        "--verify",
        "true",
    )
    assert r.returncode == 0, r.stderr
    assert check(root, "--epic", b).returncode == 0


def test_non_doc_file_shared_with_open_task_still_fails(root):
    a, b = two_epics(root, "src/x.py", "")
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        b,
        "--title",
        "Beta task",
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        "src/x.py",
        "--verify",
        "true",
    )
    assert r.returncode != 0
    assert "src/x.py" in r.stderr


def test_repo_overlap_ignore_honoured(root):
    a, b = two_epics(root, "gen/out.lock", "")
    (root / ".claude").mkdir()
    (root / ".claude" / "workbench.json").write_text('{"overlapIgnore": ["*.lock"]}')
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        b,
        "--title",
        "Beta task",
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        "gen/out.lock",
        "--verify",
        "true",
    )
    assert r.returncode == 0, r.stderr


def test_done_task_overlap_ignored(root):
    a, b = two_epics(root, "src/x.py", "")
    p = next((root / "in-progress" / a / "tasks").glob("*.md"))
    p.write_text(re.sub(r"^status: .*$", "status: done", p.read_text(), flags=re.M))
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        b,
        "--title",
        "Beta task",
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        "src/x.py",
        "--verify",
        "true",
    )
    assert r.returncode == 0, r.stderr


def test_merged_fallback_branch_single_hyphen(tmp_path):
    repo = tmp_path / "repo"
    root = repo / "plans"
    root.mkdir(parents=True)

    def g(*a):
        subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True)

    g("init", "-b", "main")
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    (repo / "f").write_text("1")
    g("add", "-A")
    g("commit", "-m", "init")
    a, b = two_epics(root, "src/x.py", "")
    tp = next((root / "in-progress" / a / "tasks").glob("*.md"))
    branch = f"{a}-{tp.stem}"
    g("branch", branch)  # at main's head: merged
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        b,
        "--title",
        "Beta task",
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        "src/x.py",
        "--verify",
        "true",
    )
    assert r.returncode == 0, r.stderr


def _move_pair(root, shared):
    a = epic(root, "Alpha thing")
    task(root, a, "Alpha task", shared)
    b = epic(root, "Beta thing")
    task(root, b, "Beta task", shared)
    assert cli("move", a, "in-progress", "--root", root).returncode == 0
    return b


def test_move_doc_vs_source_overlap(tmp_path):
    root1 = tmp_path / "one"
    root1.mkdir()
    b = _move_pair(root1, "docs/README.md")
    assert cli("move", b, "in-progress", "--root", root1).returncode == 0
    root2 = tmp_path / "two"
    root2.mkdir()
    b = _move_pair(root2, "src/x.py")
    r = cli("move", b, "in-progress", "--root", root2)
    assert r.returncode != 0 and "src/x.py" in r.stderr


def test_malformed_workbench_config_is_reported(root):
    a, b = two_epics(root, "gen/out.lock", "")
    (root / ".claude").mkdir()
    (root / ".claude" / "workbench.json").write_text("{not json")
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        b,
        "--title",
        "Beta task",
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        "gen/out.lock",
        "--verify",
        "true",
    )
    assert r.returncode != 0 and "workbench.json" in r.stderr
