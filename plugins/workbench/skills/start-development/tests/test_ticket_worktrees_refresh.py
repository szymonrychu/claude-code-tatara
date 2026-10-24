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
        "pytest -q tests/test_x.py",
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


def integration(repo, ep):
    return repo / ".claude" / "worktrees" / ep


def trees(repo):
    d = repo / ".claude" / "worktrees"
    return sorted(x.name for x in d.iterdir()) if d.is_dir() else []


def claimed(repo, root, titles=("Alpha", "Beta")):
    ep = mk_epic(root)
    for t in titles:
        mk_task(root, ep, t)
    commit_all(repo)
    r = cli("move", ep, "in-progress", "--root", root, "--owner", "t")
    assert r.returncode == 0, r.stderr
    return ep


def test_worktrees_creates_integration_tree_only(repo, root):
    help_text = cli("worktrees", "--help").stdout
    assert "--integration" not in help_text and "--refresh" in help_text
    assert "--task" not in cli("reap", "--help").stdout
    todo = mk_epic(root, "Still todo")
    mk_task(root, todo, "Waiting")
    commit_all(repo)
    r = cli("worktrees", todo, "--root", root)
    assert r.returncode == 1 and "in-progress" in r.stderr and trees(repo) == []
    ep = claimed(repo, root)
    tasks = root / "in-progress" / ep / "tasks"
    set_status(tasks / "beta.md", "escalated")
    commit_all(repo)
    git(repo, "worktree", "remove", str(integration(repo, ep)))
    before = {p.name: p.read_text() for p in tasks.iterdir()}
    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli("worktrees", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [f"integration {integration(repo, ep)} (created)"]
    assert trees(repo) == [ep]
    assert git(integration(repo, ep), "branch", "--show-current").stdout.strip() == ep
    branches = git(repo, "branch", "--format=%(refname:short)").stdout.split()
    assert sorted(branches) == sorted(["main", ep])
    assert {p.name: p.read_text() for p in tasks.iterdir()} == before
    assert git(repo, "rev-parse", "HEAD").stdout == head  # nothing to record, no commit
    r = cli("worktrees", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [f"integration {integration(repo, ep)} (reused)"]
    assert trees(repo) == [ep]
    r = cli("worktrees", ep, "--root", root, "--integration")
    assert r.returncode == 2 and "--integration" in r.stderr
    r = cli("reap", "--epic", ep, "--task", "alpha", "--root", root)
    assert r.returncode == 2 and "--task" in r.stderr


def test_refresh_fast_forwards_the_integration_tree(repo, root):
    ep = claimed(repo, root)
    wt = integration(repo, ep)
    (repo / "new.txt").write_text("n")
    git(repo, "add", "new.txt")
    git(repo, "commit", "-m", "main moves")
    r = cli("worktrees", ep, "--root", root, "--refresh")
    assert r.returncode == 0, r.stderr
    assert f"refresh {wt} updated" in r.stdout.splitlines()
    assert (wt / "new.txt").exists()
    r = cli("worktrees", ep, "--root", root, "--refresh")
    assert f"refresh {wt} current" in r.stdout.splitlines()
    (wt / "task.py").write_text("t = 1\n")
    git(wt, "add", "task.py")
    git(wt, "commit", "-m", "feat: task work on the epic")
    (repo / "newer.txt").write_text("n")
    git(repo, "add", "newer.txt")
    git(repo, "commit", "-m", "main moves again")
    r = cli("worktrees", ep, "--root", root, "--refresh")
    assert f"refresh {wt} ahead" in r.stdout.splitlines()
    assert not (wt / "newer.txt").exists()
    (wt / "wip.txt").write_text("x")
    r = cli("worktrees", ep, "--root", root, "--refresh")
    assert f"refresh {wt} dirty" in r.stdout.splitlines()
