"""ticket.py worktrees --refresh and status handling."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
sys.path.insert(0, str(SCRIPT.parent))
import ticket  # noqa: E402

AC = (
    "- AC1: it lists tasks [evidence: test:tests/test_x.py::test_lists]\n"
    "- AC2: docs say so [evidence: doc-section:README.md#Usage]\n"
    "- AC3: reads well [evidence: judgement]"
)


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    (r / "a.py").write_text("x = 1\n")
    git(r, "add", ".")
    git(r, "commit", "-m", "init")
    return r


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"


def mk_epic(root, title="Big epic"):
    r = cli("new-epic", "--root", root, "--title", title, "--force")
    assert r.returncode == 0, r.stderr
    return ticket.slug(title)


def mk_task(
    root,
    epic,
    title,
    *,
    req="Do the thing.",
    ac=AC,
    steps="1. write test\n2. code",
    files="a.py,b.py",
    extra=(),
):
    rf, af = root / f"{title}.req", root / f"{title}.ac"
    rf.write_text(req)
    af.write_text(ac)
    args = [
        "new-task",
        "--root",
        root,
        "--epic",
        epic,
        "--title",
        title,
        "--repo",
        "proj",
        "--value",
        "why",
        "--files",
        files,
        "--verify",
        "pytest -q",
        "--requirement-file",
        rf,
        "--ac-file",
        af,
        *extra,
    ]
    r = cli(*args)
    assert r.returncode == 0, r.stderr
    p = Path(r.stdout.strip().splitlines()[-1])
    rf.unlink()
    af.unlink()
    if steps is not None:
        text = p.read_text()
        start = text.index("## Steps")
        end = text.index("## Notes")
        p.write_text(text[:start] + f"## Steps\n\n{steps}\n\n" + text[end:])
    return p


def epic_branch(repo, ep):
    """The integration branch `move in-progress` would have made, for fixtures that skip it."""
    if git(repo, "branch", "--list", ep).stdout.strip() == "":
        git(repo, "branch", ep)


def commit_all(repo):
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "tickets", "--allow-empty")


def set_status(p, status):
    p.write_text(
        p.read_text()
        .replace("status: todo", f"status: {status}", 1)
        .replace("status: in-progress", f"status: {status}", 1)
    )


def tree(repo, ep, slug):
    return repo / ".claude" / "worktrees" / f"{ep}-{slug}"


def test_refresh_updates_clean_skips_done(repo, root):
    ep = mk_epic(root)
    for t in ("Clean one", "Dirty one", "Ahead one", "Done one"):
        mk_task(root, ep, t)
    commit_all(repo)
    done = root / "backlog" / ep / "tasks" / "done-one.md"
    if not done.exists():
        done = next(root.rglob("done-one.md"))
    set_status(done, "done")
    commit_all(repo)
    epic_branch(repo, ep)
    cli("worktrees", ep, "--root", root)
    (repo / "new.txt").write_text("n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "advance")
    git(repo, "branch", "-f", ep, "main")  # the refresh follows the epic branch, not main
    (tree(repo, ep, "dirty-one") / "wip.txt").write_text("x")
    a = tree(repo, ep, "ahead-one")
    (a / "mine.txt").write_text("m")
    git(a, "add", "-A")
    git(a, "commit", "-m", "mine")
    r = cli("worktrees", ep, "--root", root, "--refresh")
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert f"{ep}-clean-one updated" in lines or "clean-one updated" in lines
    assert any(x.endswith("dirty-one dirty") for x in lines)
    assert any(x.endswith("ahead-one ahead") for x in lines)
    assert not any("done-one" in x for x in lines)
    assert (tree(repo, ep, "clean-one") / "new.txt").exists()
    assert not (tree(repo, ep, "dirty-one") / "new.txt").exists()


def test_done_task_never_recreated(repo, root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "Gone")
    commit_all(repo)
    set_status(p, "done")
    commit_all(repo)
    for extra in ([], ["--refresh"]):
        epic_branch(repo, ep)
        assert cli("worktrees", ep, "--root", root, *extra).returncode == 0
    assert not tree(repo, ep, "gone").exists()


@pytest.mark.parametrize("status", ["escalated", "blocked"])
def test_keeps_escalated_and_blocked(repo, root, status):
    ep = mk_epic(root)
    p = mk_task(root, ep, "Held")
    commit_all(repo)
    set_status(p, status)
    commit_all(repo)
    epic_branch(repo, ep)
    assert cli("worktrees", ep, "--root", root).returncode == 0
    assert ticket.load(p.read_text(), p).meta["status"] == status
    assert tree(repo, ep, "held").is_dir()


def test_worktrees_todo_becomes_in_progress(repo, root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "Fresh")
    commit_all(repo)
    epic_branch(repo, ep)
    assert cli("worktrees", ep, "--root", root).returncode == 0
    assert ticket.load(p.read_text(), p).meta["status"] == "in-progress"


def test_worktrees_keeps_live_legacy_tree_record(repo, root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "Old")
    commit_all(repo)
    legacy = repo / ".claude" / "worktrees" / f"{ep}--old"
    git(repo, "worktree", "add", "-b", f"{ep}--old", str(legacy), "main")
    doc = ticket.load(p.read_text(), p)
    doc.meta.update(worktree=str(legacy), branch=f"{ep}--old")
    p.write_text(ticket.dump(doc))
    commit_all(repo)
    epic_branch(repo, ep)
    assert cli("worktrees", ep, "--root", root).returncode == 0
    m = ticket.load(p.read_text(), p).meta
    assert m["worktree"] == str(legacy) and m["branch"] == f"{ep}--old"
    assert not tree(repo, ep, "old").exists()


def test_workbench_repo_tree_is_live(tmp_path):
    """A tree of code/<repo> is not in the docs root's worktree list but is still live."""
    wb = tmp_path / "wb"
    wb.mkdir()
    git(wb, "init", "-b", "main")
    src = wb / "code" / "proj"
    src.mkdir(parents=True)
    git(src, "init", "-b", "main")
    git(src, "config", "user.email", "t@t")
    git(src, "config", "user.name", "t")
    (src / "a.py").write_text("x = 1\n")
    git(src, "add", ".")
    git(src, "commit", "-m", "init")
    wt = wb / ".claude" / "worktrees" / "ep-t" / "proj"
    git(src, "worktree", "add", "-b", "ep-t", str(wt), "main")
    assert "proj" not in ticket._live_worktrees(wb / "docs" / "plans")
    assert ticket._tree_live(str(wt))
    assert not ticket._tree_live(str(tmp_path / "gone"))
