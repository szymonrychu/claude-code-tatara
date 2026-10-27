"""ticket.py stage parked / build: parking an in-progress epic on real git repos and worktrees."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ticket_repo_helpers import (  # noqa: E402
    branches,
    cli,
    commit_all,
    deliver,
    epic_dir,
    git,
    integration_tree,
    last_subject,
    meta,
    mk_epic,
    mk_task,
    started,
)


def readme(root, ep):
    return epic_dir(root, ep) / "README.md"


def park(root, ep):
    return cli("stage", ep, "parked", "--root", root)


def test_stage_parked_from_build_writes_stage_and_commits(repo, root):
    ep = started(repo, root)
    r = park(root, ep)
    assert r.returncode == 0, r.stderr
    assert meta(readme(root, ep))["stage"] == "parked"
    assert last_subject(repo) == f"chore(ticket): {ep} stage parked"
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""


def test_stage_parked_refuses_from_review(repo, root):
    ep = started(repo, root)
    deliver(repo, root, ep, "alpha")
    deliver(repo, root, ep, "beta")
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    r = park(root, ep)
    assert r.returncode == 1 and "review" in r.stderr
    assert meta(readme(root, ep))["stage"] == "review"


def test_stage_parked_refuses_when_already_parked(repo, root):
    ep = started(repo, root)
    assert park(root, ep).returncode == 0
    r = park(root, ep)
    assert r.returncode == 1 and "parked" in r.stderr


def test_stage_parked_refuses_epic_not_in_progress(repo, root):
    ep = mk_epic(root)
    commit_all(repo)
    assert park(root, ep).returncode == 1


def test_stage_build_unparks(repo, root):
    ep = started(repo, root)
    assert park(root, ep).returncode == 0
    r = cli("stage", ep, "build", "--root", root)
    assert r.returncode == 0, r.stderr
    assert meta(readme(root, ep))["stage"] == "build"
    assert last_subject(repo) == f"chore(ticket): {ep} stage build"


def test_new_task_overlap_ignores_parked_epic_but_not_unparked(repo, root):
    parked = started(repo, root, tasks=("alpha",), title="Parked epic")
    other = mk_epic(root, "Other epic")
    commit_all(repo)
    # unparked in-progress epic: the shared file still fails
    r = cli(
        "new-task", "--root", root, "--epic", other, "--title", "Gamma", "--repo", "proj",
        "--value", "v", "--files", "alpha.py", "--verify", "true", "--points", "3",
    )  # fmt: skip
    assert r.returncode != 0 and "alpha.py" in r.stderr
    assert park(root, parked).returncode == 0
    mk_task(root, other, "Gamma", files="alpha.py")
    assert cli("check", "--root", root, "--epic", other).returncode == 0
    # unparking counts the epic again
    assert cli("stage", parked, "build", "--root", root).returncode == 0
    assert cli("check", "--root", root, "--epic", other).returncode == 1


def test_move_in_progress_ignores_parked_epic_overlap(repo, root):
    parked = started(repo, root, tasks=("alpha",), title="Parked epic")
    other = mk_epic(root, "Other epic")
    assert park(root, parked).returncode == 0
    mk_task(root, other, "gamma", files="alpha.py")
    commit_all(repo)
    r = cli("move", other, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr


def test_parking_keeps_integration_worktree_and_branch(repo, root):
    ep = started(repo, root)
    wt = deliver(repo, root, ep, "alpha")
    head = git(wt, "rev-parse", "HEAD").stdout
    assert park(root, ep).returncode == 0
    assert integration_tree(repo, ep).is_dir() and wt.is_dir()
    assert ep in branches(repo)
    assert git(wt, "rev-parse", "HEAD").stdout == head
    assert git(wt, "status", "--porcelain").stdout.strip() == ""
    assert epic_dir(root, ep).parent.name == "in-progress"


def test_lint_accepts_parked_stage(repo, root):
    ep = started(repo, root)
    assert park(root, ep).returncode == 0
    r = cli("lint", "--root", root)
    assert r.returncode == 0, r.stderr


def test_stage_review_refuses_on_parked_epic(repo, root):
    ep = started(repo, root)
    deliver(repo, root, ep, "alpha")
    deliver(repo, root, ep, "beta")
    assert park(root, ep).returncode == 0
    r = cli("stage", ep, "review", "--root", root)
    assert r.returncode == 1 and "parked" in r.stderr
    assert meta(readme(root, ep))["stage"] == "parked"
