"""Tests for ticket.py check, index and existing: enforced dedup across epics."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GITIGNORE = Path(__file__).resolve().parents[5] / ".gitignore"  # repo root; plugin has none
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "plans"
    r.mkdir()
    return r


def epic(root, title, phase="todo", *extra):
    r = cli("new-epic", "--root", root, "--title", title, "--force", *extra)
    assert r.returncode == 0, r.stderr
    slug = cli("slug", title).stdout.strip()
    if phase != "todo":
        (root / phase).mkdir(exist_ok=True)
        shutil.move(str(root / "todo" / slug), str(root / phase / slug))
    return slug


def task(root, ep, title, files="a.py", *extra):
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        ep,
        "--title",
        title,
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        files,
        "--verify",
        "true",
        *extra,
    )
    assert r.returncode == 0, r.stderr
    return r


def check(root, *args):
    return cli("check", "--root", root, *args)


def test_epic_slug_collision_any_phase_fails(root):
    epic(root, "Alpha thing", "done")
    r = check(root, "--title", "Alpha thing")
    assert r.returncode == 1
    assert "alpha-thing" in r.stderr and "done" in r.stderr


def test_task_slug_collision_same_epic_fails(root):
    e = epic(root, "Alpha thing")
    task(root, e, "Build core")
    r = check(root, "--epic", e, "--title", "Build core")
    assert r.returncode == 1 and "build-core" in r.stderr


def test_near_duplicate_epic_listed_not_failed(root):
    epic(root, "Ticket deduplication tool", "in-progress")
    r = check(root, "--title", "Ticket deduplication tools")
    assert r.returncode == 0, r.stderr
    assert "near-duplicate epic" in r.stdout and "in-progress" in r.stdout


def test_near_duplicate_by_goals_jaccard(root):
    g = root / "g.txt"
    g.write_text("stop duplicate planning across sessions with enforced checks")
    epic(root, "Alpha one", "todo", "--goals-file", g)
    r = check(root, "--title", "Zed two", "--goals-file", g)
    assert r.returncode == 0 and "near-duplicate epic" in r.stdout


def test_near_duplicate_task_listed(root):
    a = epic(root, "Alpha")
    b = epic(root, "Beta")
    task(root, a, "Write the parser module")
    r = check(root, "--epic", b, "--title", "Write the parser modules")
    assert r.returncode == 0 and "near-duplicate task" in r.stdout and "todo" in r.stdout


def test_unrelated_not_listed(root):
    epic(root, "Alpha")
    r = check(root, "--title", "Completely different")
    assert r.returncode == 0 and "near-duplicate" not in r.stdout


def test_files_shared_with_other_in_progress_epic_fails(root):
    a = epic(root, "Alpha", "in-progress")
    task(root, a, "T one", "shared.py")
    b = epic(root, "Beta")
    r = check(root, "--epic", b, "--title", "T two", "--files", "shared.py")
    assert r.returncode == 1 and "shared.py" in r.stderr and a in r.stderr


def test_files_shared_ok_when_blocker(root):
    a = epic(root, "Alpha", "in-progress")
    task(root, a, "T one", "shared.py")
    b = epic(root, "Beta", "todo", "--blockers", a)
    r = check(root, "--epic", b, "--title", "T two", "--files", "shared.py")
    assert r.returncode == 0, r.stderr


def test_files_shared_with_todo_epic_not_failed(root):
    a = epic(root, "Alpha")
    task(root, a, "T one", "shared.py")
    b = epic(root, "Beta")
    assert check(root, "--epic", b, "--title", "T two", "--files", "shared.py").returncode == 0


def test_owns_in_todo_epic_fails(root):
    a = epic(root, "Alpha")
    task(root, a, "T one", "a.py", "--owns", "slugify")
    b = epic(root, "Beta")
    r = check(root, "--epic", b, "--title", "T two", "--owns", "slugify")
    assert r.returncode == 1 and "slugify" in r.stderr and a in r.stderr


def test_owns_in_done_epic_is_existing(root):
    a = epic(root, "Alpha", "done")
    task_path = root / "done" / a / "tasks"
    # new-task refuses done epics, so create in todo and move
    a2 = epic(root, "Gamma")
    task(root, a2, "T one", "a.py", "--owns", "slugify")
    shutil.move(str(root / "todo" / a2), str(root / "done" / a2))
    assert not task_path.exists()
    b = epic(root, "Beta")
    r = check(root, "--epic", b, "--title", "T two", "--owns", "slugify")
    assert r.returncode == 0, r.stderr
    assert "existing" in r.stdout and "slugify" in r.stdout


def test_check_epic_without_title_checks_every_task(root):
    a = epic(root, "Alpha", "in-progress")
    task(root, a, "T one", "shared.py")
    b = epic(root, "Beta")
    task(root, b, "T two", "tmp.py")
    tp = root / "todo" / b / "tasks" / "t-two.md"
    tp.write_text(tp.read_text().replace("files: [tmp.py]", "files: [shared.py]"))
    task(root, b, "T three", "ok.py", "--owns", "thing")
    r = check(root, "--epic", b)
    assert r.returncode == 1
    assert r.stderr.count("shared.py") == 1 and "t-two" in r.stderr
    assert "ok.py" not in r.stderr


def test_check_epic_without_title_clean(root):
    b = epic(root, "Beta")
    task(root, b, "T two", "x.py")
    assert check(root, "--epic", b).returncode == 0


def test_new_epic_refuses_on_collision(root):
    epic(root, "Alpha thing", "done")
    r = cli("new-epic", "--root", root, "--title", "Alpha thing")
    assert r.returncode == 1 and "alpha-thing" in r.stderr


def _epic_dirs(root):
    return sorted(
        p.name
        for ph in ("todo", "in-progress", "done")
        if (root / ph).is_dir()
        for p in (root / ph).iterdir()
    )


@pytest.mark.parametrize("phase", ["todo", "in-progress"])
def test_new_epic_stops_on_live_near_duplicate(root, phase):
    epic(root, "Ticket deduplication tool", phase)
    before = _epic_dirs(root)
    r = cli("new-epic", "--root", root, "--title", "Ticket deduplication tools")
    assert r.returncode == 3
    assert re.fullmatch(
        r"new-epic: near duplicate ticket-deduplication-tool \(\d\.\d\d\); "
        r"pass --force to create anyway",
        r.stderr.strip(),
    ), r.stderr
    assert _epic_dirs(root) == before


def test_new_epic_force_creates_and_prints_note(root):
    epic(root, "Ticket deduplication tool")
    r = cli("new-epic", "--root", root, "--title", "Ticket deduplication tools", "--force")
    assert r.returncode == 0, r.stderr
    assert "near-duplicate epic" in r.stdout
    assert "ticket-deduplication-tools" in _epic_dirs(root)


def test_new_epic_done_near_duplicate_is_only_a_note(root):
    epic(root, "Ticket deduplication tool", "done")
    r = cli("new-epic", "--root", root, "--title", "Ticket deduplication tools")
    assert r.returncode == 0, r.stderr
    assert "near-duplicate epic" in r.stdout


def test_new_epic_force_does_not_override_slug_clash(root):
    epic(root, "Alpha thing", "done")
    r = cli("new-epic", "--root", root, "--title", "Alpha thing", "--force")
    assert r.returncode == 1 and "alpha-thing" in r.stderr


def test_check_title_still_lists_near_duplicate_exit_zero(root):
    epic(root, "Ticket deduplication tool")
    r = check(root, "--title", "Ticket deduplication tools")
    assert r.returncode == 0 and "near-duplicate epic" in r.stdout


def test_new_task_refuses_on_shared_file(root):
    a = epic(root, "Alpha", "in-progress")
    task(root, a, "T one", "shared.py")
    b = epic(root, "Beta")
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        b,
        "--title",
        "T two",
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        "shared.py",
        "--verify",
        "true",
    )
    assert r.returncode == 1 and "shared.py" in r.stderr
    assert not (root / "todo" / b / "tasks" / "t-two.md").exists()


def test_index_writes_json(root):
    a = epic(root, "Alpha", "in-progress")
    task(root, a, "T one", "x.py,y.py", "--owns", "thing")
    r = cli("index", "--root", root)
    assert r.returncode == 0, r.stderr
    data = json.loads((root / "index.json").read_text())
    by = {(e["kind"], e["slug"]): e for e in data}
    ep = by[("epic", a)]
    assert ep["phase"] == "in-progress" and ep["stage"] == "build" and ep["title"] == "Alpha"
    tk = by[("task", "t-one")]
    assert tk["epic"] == a and tk["files"] == ["x.py", "y.py"] and tk["owns"] == ["thing"]
    assert tk["status"] == "todo" and tk["phase"] == "in-progress" and tk["provides"] == []


def test_gitignore_has_index():
    assert "docs/plans/index.json" in GITIGNORE.read_text().split("\n")


def test_existing_lists_done_owns_and_provides(root):
    a = epic(root, "Alpha")
    task(root, a, "T one", "a.py", "--owns", "slugify")
    tp = root / "todo" / a / "tasks" / "t-one.md"
    tp.write_text(tp.read_text().replace("provides: []", "provides: [helper-x]"))
    live = epic(root, "Live")
    task(root, live, "T live", "l.py", "--owns", "notdone")
    shutil.move(str(root / "todo" / a), str(root / "done" / a)) if (root / "done").exists() else (
        (root / "done").mkdir(),
        shutil.move(str(root / "todo" / a), str(root / "done" / a)),
    )
    r = cli("existing", "--root", root)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    names = {e["name"]: e["where"] for e in out}
    assert set(names) == {"slugify", "helper-x"}
    assert a in names["slugify"] and "t-one" in names["slugify"]


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


def test_live_tree_warning_uses_ticket_lookup(tmp_path):
    repo = _repo(tmp_path)
    root = repo / "docs" / "plans"
    root.mkdir(parents=True)
    a = epic(root, "Alpha")
    b = epic(root, "Beta", "in-progress")
    task(root, a, "Tee one")
    task(root, b, "Tee one")
    for n in (f"{a}-tee-one", f"{b}-tee-one", a, b):
        subprocess.run(
            ["git", "worktree", "add", "-q", str(tmp_path / n), "-b", n],
            cwd=repo,
            check=True,
            capture_output=True,
        )
    r = check(root, "--epic", a)
    assert r.returncode == 0, r.stderr
    assert "warning" in r.stderr and f"{a}-tee-one" in r.stderr
    assert f"{b}-tee-one" not in r.stderr and f"'{b}'" not in r.stderr
    assert f"live worktree '{a}'" in r.stderr


def test_new_task_near_duplicate_still_created(root):
    a = epic(root, "Alpha")
    b = epic(root, "Beta")
    task(root, a, "Write the parser module")
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        b,
        "--title",
        "Write the parser modules",
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        "b.py",
        "--verify",
        "true",
    )
    assert r.returncode == 0, r.stderr
    assert "near-duplicate task" in r.stdout
    assert (root / "todo" / b / "tasks" / "write-the-parser-modules.md").exists()


def test_new_task_refuses_epic_path_outside_plans_root(root, tmp_path):
    outside = tmp_path / "elsewhere" / "todo" / "rogue"
    (outside / "tasks").mkdir(parents=True)
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        outside,
        "--title",
        "Rogue task",
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        "a.py",
        "--verify",
        "true",
    )
    assert r.returncode != 0
    assert "outside" in r.stderr and "plans root" in r.stderr
    assert not (outside / "tasks" / "rogue-task.md").exists()


def test_resolve_epic_refuses_path_outside_plans_root(root, tmp_path):
    outside = tmp_path / "elsewhere" / "todo" / "rogue"
    (outside / "tasks").mkdir(parents=True)
    inside = epic(root, "Inside")
    traversal = root / "todo" / inside / ".." / ".." / ".." / "elsewhere" / "todo" / "rogue"
    for arg in (outside, traversal):
        r = cli(
            "new-task",
            "--root",
            root,
            "--epic",
            arg,
            "--title",
            "Rogue task",
            "--repo",
            "p",
            "--value",
            "v",
            "--files",
            "a.py",
            "--verify",
            "true",
        )
        assert r.returncode != 0
        assert "outside the plans root" in r.stderr
    assert not (outside / "tasks" / "rogue-task.md").exists()
    ok = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        root / "todo" / inside,
        "--title",
        "Fine task",
        "--repo",
        "p",
        "--value",
        "v",
        "--files",
        "a.py",
        "--verify",
        "true",
    )
    assert ok.returncode == 0, ok.stderr
