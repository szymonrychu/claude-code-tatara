"""Shared helpers for the ticket.py tests that drive real git repos and worktrees."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
sys.path.insert(0, str(SCRIPT.parent))
import ticket  # noqa: E402

AC = "- AC1: it works [evidence: test:tests/test_x.py::test_works]"


def cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True
    )


def git(cwd, *args, check=True):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-b", "main")
    git(path, "config", "user.email", "t@t")
    git(path, "config", "user.name", "Tess")
    (path / "a.py").write_text("x = 1\n")
    git(path, "add", ".")
    git(path, "commit", "-m", "init")
    return path


def mk_epic(root, title="Big epic", blockers=None):
    args = ["new-epic", "--root", root, "--title", title, "--force"]
    if blockers:
        args += ["--blockers", blockers]
    r = cli(*args)
    assert r.returncode == 0, r.stderr
    return ticket.slug(title)


def mk_task(root, epic, title, files=None, extra=()):
    rf, af = root / f"{title}.req", root / f"{title}.ac"
    rf.write_text("Do the thing.")
    af.write_text(AC)
    r = cli(
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
        files or f"{title}.py",
        "--verify",
        "pytest -q tests/test_x.py",
        "--requirement-file",
        rf,
        "--ac-file",
        af,
        *extra,
    )
    rf.unlink()
    af.unlink()
    assert r.returncode == 0, r.stderr
    p = Path(r.stdout.strip().splitlines()[-1])
    text = p.read_text()
    start, end = text.index("## Steps"), text.index("## Notes")
    p.write_text(text[:start] + "## Steps\n\n1. test first\n\n" + text[end:])
    return p


def commit_all(repo, msg="tickets"):
    git(repo, "add", "-A", "--", "docs")
    git(repo, "commit", "-m", msg, "--allow-empty")


def epic_dir(root, ep):
    return ticket.find_epic(ep, root)


def meta(path: Path) -> dict:
    return ticket.load(path.read_text(), path).meta


def set_meta(path: Path, **kw) -> None:
    doc = ticket.load(path.read_text(), path)
    doc.meta.update(kw)
    path.write_text(ticket.dump(doc))


def task_path(root, ep, task):
    return epic_dir(root, ep) / "tasks" / f"{task}.md"


def last_subject(repo):
    return git(repo, "log", "-1", "--format=%s").stdout.strip()


def branches(repo):
    return git(repo, "branch", "--format=%(refname:short)").stdout.split()


def integration_tree(repo, ep) -> Path:
    """The meta-mode integration tree the claim creates for the epic."""
    return repo / ".claude" / "worktrees" / ep


def deliver(repo, root, ep, task):
    """Commit the task's work on <epic> in the integration tree, as the implementer does, then
    record it done with its verified head (the ticket change lands on main)."""
    wt = integration_tree(repo, ep)
    (wt / f"{task}.py").write_text(f"{task} = 1\n")
    git(wt, "add", f"{task}.py")
    git(wt, "commit", "-m", f"feat: {task}")
    head = git(wt, "rev-parse", "HEAD").stdout.strip()
    set_meta(task_path(root, ep, task), status="done", verified_head=head)
    commit_all(repo, f"deliver {task}")
    return wt


def started(repo, root, tasks=("alpha", "beta"), title="Big epic"):
    ep = mk_epic(root, title)
    for t in tasks:
        mk_task(root, ep, t)
    commit_all(repo)
    r = cli("move", ep, "in-progress", "--root", root, "--owner", "tess")
    assert r.returncode == 0, r.stderr
    assert integration_tree(repo, ep).is_dir()
    return ep


def reviewed(repo, root, tasks=("alpha", "beta"), merge=True, verdict="pass"):
    ep = started(repo, root, tasks)
    for t in tasks:
        deliver(repo, root, ep, t)
    if merge:  # the epic close: the integration branch lands on main
        git(repo, "merge", "--no-ff", "--no-edit", ep)
    r = cli("stage", ep, "review", "--root", root)
    assert r.returncode == 0, r.stderr
    notes = root.parent / "notes.txt"
    notes.write_text("All good.")
    r = cli("review", ep, "--verdict", verdict, "--notes-file", notes, "--root", root)
    assert r.returncode == 0, r.stderr
    notes.unlink()
    return ep
