"""Tests for ticket.py check and the near-duplicate gate of new: dedup across plans."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ticket.py"
sys.path.insert(0, str(SCRIPT.parent))
import ticket  # noqa: E402

PHASES = ("todo", "in-progress", "done")


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "plans"
    r.mkdir()
    return r


def plan(root, title, phase="todo", what=""):
    """A plan made by `new`, moved by hand to `phase`, with `what` as its What and why."""
    r = cli("new", "--root", root, "--title", title, "--force")
    assert r.returncode == 0, r.stderr
    slug = ticket.slug(title)
    p = root / "todo" / slug / "plan.md"
    if what:
        text = p.read_text()
        start = text.index("## What and why")
        end = text.index("## Scope ladder")
        p.write_text(text[:start] + f"## What and why\n\n{what}\n\n" + text[end:])
    if phase != "todo":
        (root / phase).mkdir(exist_ok=True)
        shutil.move(str(root / "todo" / slug), str(root / phase / slug))
    return slug


def check(root, *args):
    return cli("check", "--root", root, *args)


def plan_dirs(root):
    return sorted(p.name for ph in PHASES if (root / ph).is_dir() for p in (root / ph).iterdir())


def test_check_needs_a_title(root):
    r = cli("check", "--root", root)
    assert r.returncode == 2 and "--title" in r.stderr


@pytest.mark.parametrize("opt", ["--epic", "--files", "--blockers", "--goals-file"])
def test_check_has_no_task_options(root, opt):
    r = check(root, "--title", "X", opt, "y")
    assert r.returncode == 2 and opt in r.stderr


@pytest.mark.parametrize("phase", PHASES)
def test_slug_collision_in_any_phase_fails(root, phase):
    plan(root, "Alpha thing", phase)
    r = check(root, "--title", "Alpha thing")
    assert r.returncode == 1
    assert f"plan slug 'alpha-thing' already exists in {phase}" in r.stderr


def test_near_duplicate_by_title_listed_exit_zero(root):
    plan(root, "Ticket deduplication tool")
    r = check(root, "--title", "Ticket deduplication tools")
    assert r.returncode == 0, r.stderr
    assert "near-duplicate plan ticket-deduplication-tool (todo)" in r.stdout


def test_near_duplicate_by_what_and_why(root):
    plan(root, "Alpha", what="dedup tickets tool for plans")
    r = check(root, "--title", "dedup tickets tool plans")
    assert r.returncode == 0 and "near-duplicate plan alpha" in r.stdout


def test_other_sections_do_not_count_for_similarity(root):
    slug = plan(root, "Alpha")
    p = root / "todo" / slug / "plan.md"
    text = p.read_text()
    p.write_text(text.replace("## Design\n", "## Design\n\ndedup tickets tool for plans\n"))
    r = check(root, "--title", "dedup tickets tool plans")
    assert r.returncode == 0 and "near-duplicate" not in r.stdout


def test_unrelated_not_listed(root):
    plan(root, "Robot arm calibration")
    r = check(root, "--title", "Web dashboard theme")
    assert r.returncode == 0 and r.stdout == "" and r.stderr == ""


@pytest.mark.parametrize("phase", ["todo", "in-progress"])
def test_new_stops_on_live_near_duplicate_and_writes_nothing(root, phase):
    plan(root, "Ticket deduplication tool", phase)
    before = plan_dirs(root)
    r = cli("new", "--root", root, "--title", "Ticket deduplication tools")
    assert r.returncode == 3
    assert re.fullmatch(
        r"new: near duplicate ticket-deduplication-tool \(\d\.\d\d\); "
        r"pass --force to create anyway",
        r.stderr.strip(),
    ), r.stderr
    assert plan_dirs(root) == before


def test_new_force_creates_and_prints_note(root):
    plan(root, "Ticket deduplication tool")
    r = cli("new", "--root", root, "--title", "Ticket deduplication tools", "--force")
    assert r.returncode == 0, r.stderr
    assert "near-duplicate plan" in r.stdout
    assert "ticket-deduplication-tools" in plan_dirs(root)


def test_new_done_near_duplicate_is_only_a_note(root):
    plan(root, "Ticket deduplication tool", "done")
    r = cli("new", "--root", root, "--title", "Ticket deduplication tools")
    assert r.returncode == 0, r.stderr
    assert "near-duplicate plan ticket-deduplication-tool (done)" in r.stdout
    assert "ticket-deduplication-tools" in plan_dirs(root)


def test_new_force_does_not_override_slug_clash(root):
    plan(root, "Alpha thing", "done")
    r = cli("new", "--root", root, "--title", "Alpha thing", "--force")
    assert r.returncode == 1 and "alpha-thing" in r.stderr


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    for c in (
        ["init", "-q", "-b", "main"],
        ["config", "user.email", "a@b"],
        ["config", "user.name", "n"],
        ["commit", "-q", "--allow-empty", "-m", "i"],
    ):
        subprocess.run(["git", *c], cwd=repo, check=True, capture_output=True)
    return repo


def test_live_tree_of_a_plan_not_in_progress_is_warned(tmp_path):
    repo = _repo(tmp_path)
    root = repo / "docs" / "plans"
    root.mkdir(parents=True)
    a = plan(root, "Alpha")
    b = plan(root, "Beta", "in-progress")
    for n in (a, b, "unrelated"):
        subprocess.run(
            ["git", "worktree", "add", "-q", str(tmp_path / n), "-b", n],
            cwd=repo,
            check=True,
            capture_output=True,
        )
    r = check(root, "--title", "Gamma")
    assert r.returncode == 0, r.stderr
    assert f"warning: live worktree '{a}' belongs to plan '{a}' which is in todo" in r.stderr
    assert f"'{b}'" not in r.stderr and "unrelated" not in r.stderr
