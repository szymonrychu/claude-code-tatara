"""Shared helpers for the ticket.py tests that drive real git repos and worktrees."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ticket.py"
sys.path.insert(0, str(SCRIPT.parent))
import ticket  # noqa: E402

IMPL = "# Big plan implementation plan\n\n## Agreed rung\n\nRung 3.\n"
RETRO = "# Big plan retro\n\n## Review\n\nPassed.\n"


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
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


def commit_all(repo, msg="plans"):
    git(repo, "add", "-A", "--", "docs")
    git(repo, "commit", "-m", msg, "--allow-empty")


def plan_dir(root, plan):
    return ticket.find_plan(plan, root)


def meta(path: Path) -> dict:
    return ticket.load(path.read_text(), path).meta


def set_meta(path: Path, **kw) -> None:
    doc = ticket.load(path.read_text(), path)
    doc.meta.update(kw)
    path.write_text(ticket.dump(doc))


def mk_plan(root, title="Big plan", rung="3", impl=True, repos=None):
    """A todo plan through `new`; `rung` set and implementation-plan.md written when asked, the
    way the plan writer leaves it after the gate. Committed when root sits in a git repo."""
    args = ["new", "--root", root, "--title", title, "--force"]
    if repos:
        args += ["--repos", repos]
    r = cli(*args)
    assert r.returncode == 0, r.stderr
    plan = ticket.slug(title)
    d = root / "todo" / plan
    if rung:
        set_meta(d / "plan.md", rung=rung)
    if impl:
        (d / "implementation-plan.md").write_text(IMPL)
    if ticket._in_git(root):
        commit_all(root.parent.parent, f"docs(plan): {plan} implementation plan")
    return plan


def last_subject(repo):
    return git(repo, "log", "-1", "--format=%s").stdout.strip()


def branches(repo):
    return git(repo, "branch", "--format=%(refname:short)").stdout.split()


def plan_tree(repo, plan) -> Path:
    """The meta-mode plan tree the claim creates."""
    return repo / ".claude" / "worktrees" / plan


def started(repo, root, title="Big plan"):
    plan = mk_plan(root, title)
    r = cli("move", plan, "in-progress", "--root", root, "--owner", "tess")
    assert r.returncode == 0, r.stderr
    assert plan_tree(repo, plan).is_dir()
    return plan


def deliver(repo, plan, name="alpha"):
    """Commit a step's work on <plan> in the plan tree, as the implementer does."""
    wt = plan_tree(repo, plan)
    (wt / f"{name}.py").write_text(f"{name} = 1\n")
    git(wt, "add", f"{name}.py")
    git(wt, "commit", "-m", f"feat: {name}")
    return wt


def write_retro(root, plan):
    """retro.md as the reviewer leaves it on a pass: written, not committed."""
    p = plan_dir(root, plan) / "retro.md"
    p.write_text(RETRO)
    return p


def reviewed(repo, root, steps=("alpha", "beta"), merge=True, retro=True):
    """An in-progress plan with its steps delivered, optionally merged into main the way a
    component MR lands it, and retro.md written."""
    plan = started(repo, root)
    for s in steps:
        deliver(repo, plan, s)
    if merge:
        git(repo, "merge", "--no-ff", "--no-edit", plan)
    if retro:
        write_retro(root, plan)
    return plan
