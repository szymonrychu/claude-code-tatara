"""ticket.py move, stage, review, rename, lint and reap on real git repos and worktrees."""

import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
MERGE = ROOT / "skills" / "worktree-merge" / "scripts" / "merge.py"
sys.path.insert(0, str(SCRIPT.parent))
import ticket  # noqa: E402

AC = "- AC1: it works [evidence: test:tests/test_x.py::test_works]"
TODAY = datetime.date.today().isoformat()


from ticket_repo_helpers import (  # noqa: E402
    branches,
    cli,
    commit_all,
    deliver,
    epic_dir,
    git,
    init_repo,
    last_subject,
    meta,
    mk_epic,
    mk_task,
    reviewed,
    set_meta,
    started,
    task_path,
)


def summary(r):
    return json.loads(r.stdout)


def left_reasons(s):
    return {Path(x["path"]).name: x["reason"] for x in s["left"]}


# ---------------------------------------------------------------- move in-progress


def test_move_in_progress_git_mv_owner_and_commit(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    commit_all(repo)
    r = cli("move", ep, "in-progress", "--root", root, "--owner", "alice")
    assert r.returncode == 0, r.stderr
    assert not (root / "todo" / ep).exists()
    readme = root / "in-progress" / ep / "README.md"
    assert meta(readme)["owner"] == "alice" and meta(readme)["stage"] == "build"
    assert (root / "in-progress" / ep / "tasks" / "alpha.md").is_file()
    assert last_subject(repo) == f"chore(ticket): {ep} move in-progress"
    stat = git(repo, "show", "--name-status", "--format=", "HEAD").stdout
    assert re.search(rf"R\d+\s+\S*todo/{ep}/tasks/alpha.md", stat)
    assert meta(root / "in-progress" / ep / "tasks" / "alpha.md")["status"] == "in-progress"
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""


def test_move_in_progress_pulls_only_todo_tasks(repo, root):
    ep = mk_epic(root)
    a = mk_task(root, ep, "alpha")
    b = mk_task(root, ep, "beta")
    c = mk_task(root, ep, "gamma")
    set_meta(b, status="blocked")
    set_meta(c, status="done")
    before = {p.name: meta(p) for p in (a, b, c)}
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    tdir = root / "in-progress" / ep / "tasks"
    for name, want in (("alpha", "in-progress"), ("beta", "blocked"), ("gamma", "done")):
        got = meta(tdir / f"{name}.md")
        exp = dict(before[f"{name}.md"], status=want)
        assert got == exp
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""
    assert last_subject(repo) == f"chore(ticket): {ep} move in-progress"


def test_move_in_progress_keeps_tasks_listing_and_time(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    commit_all(repo)

    def listing():
        return [
            {k: v for k, v in t.items() if k != "status"}
            for t in json.loads(cli("tasks", ep, "--root", root).stdout)
        ]

    def time_line(d):
        assert cli("tasks", ep, "--root", root).returncode == 0
        return re.search(r"Estimate:.*", (d / ep / "README.md").read_text()).group(0)

    t0 = time_line(root / "todo")
    before = listing()
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    assert listing() == before
    assert time_line(root / "in-progress") == t0


def test_move_in_progress_owner_defaults_to_git_user(repo, root):
    ep = mk_epic(root)
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    assert meta(root / "in-progress" / ep / "README.md")["owner"] == "Tess"


def test_move_in_progress_refuses_open_blocker(repo, root):
    mk_epic(root, "Base work")
    ep = mk_epic(root, "Top work", blockers="Base work")
    commit_all(repo)
    r = cli("move", ep, "in-progress", "--root", root)
    assert r.returncode == 1 and "Base work" in r.stderr
    assert (root / "todo" / ep).is_dir()
    # still refused while the blocker is in progress
    assert cli("move", "base-work", "in-progress", "--root", root).returncode == 0
    r = cli("move", ep, "in-progress", "--root", root)
    assert r.returncode == 1 and "in-progress" in r.stderr
    assert (root / "todo" / ep).is_dir()


def test_move_in_progress_allows_done_blocker(repo, root):
    mk_epic(root, "Base work")
    ep = mk_epic(root, "Top work", blockers="Base work")
    commit_all(repo)
    (root / "done").mkdir()
    git(repo, "mv", str(root / "todo" / "base-work"), str(root / "done" / "base-work"))
    commit_all(repo)
    r = cli("move", ep, "in-progress", "--root", root)
    assert r.returncode == 0, r.stderr


def test_move_in_progress_refuses_blocker_naming_no_epic(repo, root):
    ep = mk_epic(root, "Top work", blockers="Ghost epic")
    commit_all(repo)
    r = cli("move", ep, "in-progress", "--root", root)
    assert r.returncode == 1 and "Ghost epic" in r.stderr


def test_move_in_progress_refuses_unless_in_todo(repo, root):
    ep = mk_epic(root)
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    r = cli("move", ep, "in-progress", "--root", root)
    assert r.returncode == 1 and "todo" in r.stderr


def test_move_in_progress_refuses_file_overlap_with_in_progress_epic(repo, root):
    a = mk_epic(root, "First epic")
    mk_task(root, a, "one", files="shared.py")
    b = mk_epic(root, "Second epic")
    mk_task(root, b, "two", files="shared.py")
    commit_all(repo)
    assert cli("move", a, "in-progress", "--root", root).returncode == 0
    r = cli("move", b, "in-progress", "--root", root)
    assert r.returncode == 1 and "shared.py" in r.stderr
    assert (root / "todo" / b).is_dir()


# ---------------------------------------------------------------- rename


def test_rename_in_todo_moves_dir_title_and_blockers(repo, root):
    ep = mk_epic(root, "Old name")
    other = mk_epic(root, "Other epic", blockers="Old name")
    mk_task(root, ep, "alpha")
    commit_all(repo)
    r = cli("rename", ep, "New shiny name", "--root", root)
    assert r.returncode == 0, r.stderr
    assert not (root / "todo" / ep).exists()
    readme = root / "todo" / "new-shiny-name" / "README.md"
    assert meta(readme)["title"] == "New shiny name"
    assert (root / "todo" / "new-shiny-name" / "tasks" / "alpha.md").is_file()
    assert meta(root / "todo" / other / "README.md")["blockers"] == ["New shiny name"]
    assert last_subject(repo) == "chore(ticket): new-shiny-name rename"
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""
    assert cli("lint", "--root", root).returncode == 0


def test_rename_refuses_slug_collision(repo, root):
    ep = mk_epic(root, "Old name")
    mk_epic(root, "Taken name")
    commit_all(repo)
    r = cli("rename", ep, "Taken name", "--root", root)
    assert r.returncode == 1
    assert (root / "todo" / ep).is_dir()


def test_rename_frozen_after_todo(repo, root):
    ep = mk_epic(root, "Old name")
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    r = cli("rename", ep, "New name", "--root", root)
    assert r.returncode == 1 and "todo" in r.stderr
    assert (root / "in-progress" / ep).is_dir()
    assert meta(root / "in-progress" / ep / "README.md")["title"] == "Old name"


def test_rename_refused_while_task_worktrees_exist(repo, root):
    ep = mk_epic(root, "Old name")
    mk_task(root, ep, "alpha")
    commit_all(repo)
    assert cli("worktrees", ep, "--root", root).returncode == 0
    r = cli("rename", ep, "New name", "--root", root)
    assert r.returncode == 1 and "worktree" in r.stderr
    assert (root / "todo" / ep).is_dir()


def test_rename_same_title_is_a_no_op(repo, root):
    ep = mk_epic(root, "Old name")
    commit_all(repo)
    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli("rename", ep, "Old name", "--root", root)
    assert r.returncode == 0, r.stderr
    assert git(repo, "rev-parse", "HEAD").stdout == head


# ---------------------------------------------------------------- stage


def test_stage_review_refuses_open_or_unverified_task(repo, root):
    ep = started(repo, root)
    deliver(repo, root, ep, "alpha")
    r = cli("stage", ep, "review", "--root", root)
    assert r.returncode == 1 and "beta" in r.stderr
    p = task_path(root, ep, "beta")
    set_meta(p, status="done", verified_head="")
    commit_all(repo)
    r = cli("stage", ep, "review", "--root", root)
    assert r.returncode == 1 and "verified_head" in r.stderr
    assert meta(epic_dir(root, ep) / "README.md")["stage"] == "build"


def test_stage_review_then_build_round_trip(repo, root):
    ep = started(repo, root)
    deliver(repo, root, ep, "alpha")
    deliver(repo, root, ep, "beta")
    r = cli("stage", ep, "review", "--root", root)
    assert r.returncode == 0, r.stderr
    readme = epic_dir(root, ep) / "README.md"
    assert meta(readme)["stage"] == "review"
    assert last_subject(repo) == f"chore(ticket): {ep} stage review"
    # build is always allowed for an in-progress epic, even with open tasks
    set_meta(task_path(root, ep, "beta"), status="in-progress")
    commit_all(repo)
    r = cli("stage", ep, "build", "--root", root)
    assert r.returncode == 0, r.stderr
    assert meta(readme)["stage"] == "build"
    assert last_subject(repo) == f"chore(ticket): {ep} stage build"


def test_stage_refuses_epic_not_in_progress(repo, root):
    ep = mk_epic(root)
    commit_all(repo)
    assert cli("stage", ep, "build", "--root", root).returncode == 1
    assert cli("stage", ep, "review", "--root", root).returncode == 1


def test_stage_review_refuses_epic_without_tasks(repo, root):
    ep = mk_epic(root)
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    r = cli("stage", ep, "review", "--root", root)
    assert r.returncode == 1 and "no tasks" in r.stderr


# ---------------------------------------------------------------- review


def test_review_appends_verdicts_last_one_counts(repo, root):
    ep = started(repo, root, tasks=("alpha",))
    deliver(repo, root, ep, "alpha")
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    notes = repo / "n.txt"
    notes.write_text("Missing a test for X.")
    r = cli("review", ep, "--verdict", "fail", "--notes-file", notes, "--root", root)
    assert r.returncode == 0, r.stderr
    assert last_subject(repo) == f"chore(ticket): {ep} review fail"
    readme = epic_dir(root, ep) / "README.md"
    assert ticket.last_verdict(readme.read_text()) == "fail"
    notes.write_text("Fixed; all findings acted on.")
    r = cli("review", ep, "--verdict", "pass", "--notes-file", notes, "--root", root)
    assert r.returncode == 0, r.stderr
    assert last_subject(repo) == f"chore(ticket): {ep} review pass"
    body = readme.read_text()
    review = body[body.index("## Review") :]
    assert f"Verdict: fail ({TODAY})\n\nMissing a test for X." in review
    assert f"Verdict: pass ({TODAY})\n\nFixed; all findings acted on." in review
    assert review.index("Verdict: fail") < review.index("Verdict: pass")
    assert ticket.last_verdict(body) == "pass"
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""


def test_review_lands_under_review_section_not_at_eof(repo, root):
    ep = started(repo, root, tasks=("alpha",))
    deliver(repo, root, ep, "alpha")
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    readme = epic_dir(root, ep) / "README.md"
    readme.write_text(readme.read_text() + "\n## Appendix\n\nExtra.\n")
    commit_all(repo)
    notes = repo / "n.txt"
    notes.write_text("ok")
    assert (
        cli("review", ep, "--verdict", "pass", "--notes-file", notes, "--root", root).returncode
        == 0
    )
    body = readme.read_text()
    assert body.index("Verdict: pass") < body.index("## Appendix")


def test_review_refuses_bad_input(repo, root):
    ep = started(repo, root, tasks=("alpha",))
    notes = repo / "n.txt"
    notes.write_text("x")
    # not in stage review yet
    r = cli("review", ep, "--verdict", "pass", "--notes-file", notes, "--root", root)
    assert r.returncode == 1 and "review" in r.stderr
    deliver(repo, root, ep, "alpha")
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    r = cli("review", ep, "--verdict", "maybe", "--notes-file", notes, "--root", root)
    assert r.returncode != 0
    notes.write_text("looks fine\nVerdict: pass (2020-01-01)")
    r = cli("review", ep, "--verdict", "fail", "--notes-file", notes, "--root", root)
    assert r.returncode == 1 and "Verdict:" in r.stderr
    assert ticket.last_verdict((epic_dir(root, ep) / "README.md").read_text()) is None


# ---------------------------------------------------------------- move done: refusals


def test_move_done_refuses_from_todo(repo, root):
    ep = mk_epic(root)
    commit_all(repo)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1 and "in-progress" in r.stderr
    assert (root / "todo" / ep).is_dir()


def test_move_done_refuses_in_build_stage(repo, root):
    ep = started(repo, root, tasks=("alpha",))
    deliver(repo, root, ep, "alpha")
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1 and "stage" in r.stderr
    assert (root / "in-progress" / ep).is_dir()


def test_move_done_refuses_without_verdict(repo, root):
    ep = started(repo, root, tasks=("alpha",))
    deliver(repo, root, ep, "alpha")
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1 and "verdict" in r.stderr.lower()


def test_move_done_refuses_when_last_verdict_fail(repo, root):
    ep = reviewed(repo, root, tasks=("alpha",))
    notes = repo / "n.txt"
    notes.write_text("Regression found.")
    assert (
        cli("review", ep, "--verdict", "fail", "--notes-file", notes, "--root", root).returncode
        == 0
    )
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1 and "fail" in r.stderr
    assert (root / "in-progress" / ep).is_dir()


def test_move_done_refuses_task_not_done_or_unverified(repo, root):
    ep = reviewed(repo, root)
    p = task_path(root, ep, "beta")
    set_meta(p, status="in-progress")
    commit_all(repo)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1 and "beta" in r.stderr
    set_meta(p, status="done", verified_head="")
    commit_all(repo)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1 and "verified_head" in r.stderr
    assert (root / "in-progress" / ep).is_dir()


def test_move_done_refuses_unmerged_branch_and_keeps_everything(repo, root):
    ep = reviewed(repo, root, merge=False)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1 and "not merged" in r.stderr and "main" in r.stderr
    assert (root / "in-progress" / ep).is_dir()
    for t in ("alpha", "beta"):
        assert (repo / ".claude" / "worktrees" / f"{ep}-{t}").is_dir()
        assert f"{ep}-{t}" in branches(repo)


def test_move_done_base_option(repo, root):
    ep = reviewed(repo, root, tasks=("alpha",))
    git(repo, "branch", "release", "HEAD~5")
    r = cli("move", ep, "done", "--root", root, "--base", "release")
    assert r.returncode == 1 and "release" in r.stderr


# ---------------------------------------------------------------- move done: success and cleanup


def test_move_done_sweep_error_keeps_the_move_and_reports(repo, root, monkeypatch, capsys):
    ep = reviewed(repo, root, tasks=("alpha",))

    def boom(self, root_, dest):
        raise RuntimeError("sweep exploded")

    monkeypatch.setattr(ticket.Sweep, "epic", boom)
    rc = ticket.main(["move", ep, "done", "--root", str(root)])
    err = capsys.readouterr().err
    assert rc == 1 and "sweep exploded" in err and "moved to done" in err
    assert (root / "done" / ep / "README.md").is_file()
    assert not (root / "in-progress" / ep).exists()
    assert f"chore(ticket): {ep} move done" in git(repo, "log", "--format=%s").stdout


def test_move_done_moves_and_cleans_merged_clean_trees_only(repo, root):
    ep = reviewed(repo, root)
    wt_a = repo / ".claude" / "worktrees" / f"{ep}-alpha"
    wt_b = repo / ".claude" / "worktrees" / f"{ep}-beta"
    (wt_b / "scratch.txt").write_text("uncommitted work")
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    assert not (root / "in-progress" / ep).exists()
    assert (root / "done" / ep / "README.md").is_file()
    assert f"chore(ticket): {ep} move done" in git(repo, "log", "--format=%s").stdout
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""
    s = summary(r)
    assert str(wt_a) in s["removed"]
    assert not wt_a.exists() and f"{ep}-alpha" not in branches(repo)
    assert wt_b.is_dir() and (wt_b / "scratch.txt").read_text() == "uncommitted work"
    assert f"{ep}-beta" in branches(repo)
    assert "dirty" in left_reasons(s)[f"{ep}-beta"]
    assert str(wt_a) not in git(repo, "worktree", "list").stdout


def test_move_done_leaves_tree_whose_head_is_unmerged(repo, root):
    ep = reviewed(repo, root, tasks=("alpha",))
    wt = repo / ".claude" / "worktrees" / f"{ep}-alpha"
    git(wt, "checkout", "-b", "side-work")
    (wt / "more.py").write_text("y = 2\n")
    git(wt, "add", "more.py")
    git(wt, "commit", "-m", "unmerged work")
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert s["removed"] == []
    assert "unmerged" in left_reasons(s)[f"{ep}-alpha"]
    assert wt.is_dir() and "side-work" in branches(repo)


def test_move_done_accepts_branch_already_cleaned_by_worktree_merge(repo, root):
    ep = reviewed(repo, root, tasks=("alpha",))
    wt = repo / ".claude" / "worktrees" / f"{ep}-alpha"
    git(repo, "worktree", "remove", str(wt))
    git(repo, "branch", "-d", f"{ep}-alpha")
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    assert summary(r) == {"removed": [], "left": []}


def test_move_done_refuses_deleted_branch_whose_head_is_not_on_base(repo, root):
    ep = reviewed(repo, root, tasks=("alpha",), merge=False)
    wt = repo / ".claude" / "worktrees" / f"{ep}-alpha"
    git(wt, "checkout", "--detach")
    git(repo, "branch", "--delete", "--force", f"{ep}-alpha")  # test setup only
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1 and "not merged" in r.stderr


def test_move_done_uses_frontmatter_worktree_path(repo, root):
    ep = started(repo, root, tasks=("alpha",))
    p = task_path(root, ep, "alpha")
    name = f"{ep}-alpha"
    old = Path(meta(p)["worktree"])
    new = repo.parent / "elsewhere" / "moved-alpha"
    new.parent.mkdir()
    git(repo, "worktree", "move", str(old), str(new))
    set_meta(p, worktree=str(new))
    commit_all(repo)
    deliver(repo, root, ep, "alpha")
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    notes = repo / "n.txt"
    notes.write_text("ok")
    assert (
        cli("review", ep, "--verdict", "pass", "--notes-file", notes, "--root", root).returncode
        == 0
    )
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    assert summary(r)["removed"] == [str(new)]
    assert not new.exists() and name not in branches(repo)


def test_worktrees_creates_single_hyphen_trees(repo, root):
    ep = started(repo, root, tasks=("alpha",))
    wt = repo / ".claude" / "worktrees" / f"{ep}-alpha"
    m = meta(task_path(root, ep, "alpha"))
    assert wt.is_dir() and Path(m["worktree"]) == wt
    assert m["branch"] == f"{ep}-alpha" and f"{ep}-alpha" in branches(repo)
    assert f"{ep}--alpha" not in branches(repo)


def test_move_done_fallback_branch_single_hyphen(repo, root):
    ep = reviewed(repo, root, tasks=("alpha",), merge=False)
    set_meta(task_path(root, ep, "alpha"), branch="")
    commit_all(repo)
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 1 and f"branch '{ep}-alpha' is not merged" in r.stderr
    assert f"{ep}--alpha" not in r.stderr


# ---------------------------------------------------------------- component mode


def component_workbench(tmp_path):
    """A workbench with code/proj and code/other (each with an origin) and docs/plans at the top."""
    wb = tmp_path / "wb"
    wb.mkdir()
    git(wb, "init", "-b", "main")
    git(wb, "config", "user.email", "t@t")
    git(wb, "config", "user.name", "Tess")
    (wb / ".gitmodules").write_text("")
    (wb / ".gitignore").write_text("code/\n.claude/\n.worktrees/\n")
    git(wb, "add", "-A")
    git(wb, "commit", "-m", "wb")
    for name in ("proj", "other"):
        bare = tmp_path / "remotes" / f"{name}.git"
        bare.mkdir(parents=True)
        git(bare, "init", "--bare", "-b", "main")
        src = init_repo(wb / "code" / name)
        git(src, "remote", "add", "origin", str(bare))
        git(src, "push", "-u", "origin", "main")
    return wb


def integration_tree(wb, ep, repo_name, merged_on_origin):
    src = wb / "code" / repo_name
    wt = wb / ".worktrees" / ep / repo_name
    wt.parent.mkdir(parents=True, exist_ok=True)
    git(src, "worktree", "add", "-b", ep, str(wt), "main")
    (wt / "int.py").write_text("i = 1\n")
    git(wt, "add", "int.py")
    git(wt, "commit", "-m", "integration")
    if merged_on_origin:
        git(wt, "push", "origin", f"{ep}:main")
    return wt


def test_move_done_component_mode_integration_trees(tmp_path):
    wb = component_workbench(tmp_path)
    root = wb / "docs" / "plans"
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    commit_all(wb)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    r = cli("worktrees", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    p = task_path(root, ep, "alpha")
    wt = Path(meta(p)["worktree"])
    assert wt == wb / ".claude" / "worktrees" / f"{ep}-alpha" / "proj"
    (wt / "alpha.py").write_text("a = 1\n")
    git(wt, "add", "alpha.py")
    git(wt, "commit", "-m", "alpha")
    head = git(wt, "rev-parse", "HEAD").stdout.strip()
    git(wb / "code" / "proj", "merge", "--no-ff", "--no-edit", f"{ep}-alpha")
    set_meta(p, status="done", verified_head=head)
    commit_all(wb)
    merged = integration_tree(wb, ep, "proj", merged_on_origin=True)
    unmerged = integration_tree(wb, ep, "other", merged_on_origin=False)
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    notes = tmp_path / "n.txt"
    notes.write_text("ok")
    assert (
        cli("review", ep, "--verdict", "pass", "--notes-file", notes, "--root", root).returncode
        == 0
    )
    r = cli("move", ep, "done", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert str(wt) in s["removed"] and not wt.exists()
    assert not (wb / ".claude" / "worktrees" / f"{ep}-alpha").exists()
    assert f"{ep}-alpha" not in branches(wb / "code" / "proj")
    assert str(merged) in s["removed"] and not merged.exists()
    assert unmerged.is_dir() and ep in branches(wb / "code" / "other")
    assert "origin" in left_reasons(s)["other"]


# ---------------------------------------------------------------- reap


def stray_tree(repo, name, *, merged, dirty=False):
    wt = repo / ".claude" / "worktrees" / name
    wt.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-b", name, str(wt), "main")
    (wt / f"{name}.txt").write_text("work\n")
    git(wt, "add", ".")
    git(wt, "commit", "-m", f"work {name}")
    if merged:
        git(repo, "merge", "--no-ff", "--no-edit", name)
    if dirty:
        (wt / "dirty.txt").write_text("uncommitted")
    return wt


def test_reap_orphans_and_done_leftovers(repo, root):
    ep = reviewed(repo, root)
    wt_b = repo / ".claude" / "worktrees" / f"{ep}-beta"
    (wt_b / "scratch.txt").write_text("uncommitted work")
    assert cli("move", ep, "done", "--root", root).returncode == 0
    assert wt_b.is_dir()
    live = mk_epic(root, "Live epic")
    commit_all(repo)
    assert cli("move", live, "in-progress", "--root", root).returncode == 0
    orphan_ok = stray_tree(repo, "gone-epic--x", merged=True)
    orphan_unmerged = stray_tree(repo, "gone-epic--y", merged=False)
    orphan_dirty = stray_tree(repo, "gone-epic--z", merged=True, dirty=True)
    live_tree = stray_tree(repo, f"{live}--w", merged=True)
    plain = stray_tree(repo, "plain-name", merged=True)
    unknown = stray_tree(repo, "gone-epic-x", merged=True)  # single hyphen, no ticket: not ours
    live_task = stray_tree(repo, f"{live}-solo", merged=True)  # no such task: not ours

    dry = cli("reap", "--dry-run", "--root", root)
    assert dry.returncode == 0, dry.stderr
    d = summary(dry)
    assert d["dryRun"] is True
    assert str(orphan_ok) in d["removed"]
    kept = (orphan_ok, orphan_unmerged, orphan_dirty, wt_b, live_tree, plain, unknown, live_task)
    for wt in kept:
        assert wt.is_dir()
    assert "gone-epic--x" in branches(repo)

    (wt_b / "scratch.txt").unlink()
    r = cli("reap", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert sorted(s["removed"]) == sorted([str(orphan_ok), str(wt_b)])
    assert not orphan_ok.exists() and "gone-epic--x" not in branches(repo)
    assert not wt_b.exists() and f"{ep}-beta" not in branches(repo)
    reasons = left_reasons(s)
    assert "unmerged" in reasons["gone-epic--y"] and orphan_unmerged.is_dir()
    assert "gone-epic--y" in branches(repo)
    assert "dirty" in reasons["gone-epic--z"] and (orphan_dirty / "dirty.txt").is_file()
    assert live_tree.is_dir() and plain.is_dir() and unknown.is_dir() and live_task.is_dir()
    assert str(unknown) not in s["removed"] and str(live_task) not in s["removed"]
    assert f"{live}--w" not in reasons and "plain-name" not in reasons


def done_epic(repo, root, title, tasks=("alpha", "beta")):
    ep = started(repo, root, tasks, title=title)
    for t in tasks:
        deliver(repo, root, ep, t)
    notes = root.parent / "notes.txt"
    notes.write_text("All good.")
    assert cli("stage", ep, "review", "--root", root).returncode == 0
    r = cli("review", ep, "--verdict", "pass", "--notes-file", notes, "--root", root)
    assert r.returncode == 0, r.stderr
    notes.unlink()
    for t in tasks:  # a dirty tree survives the sweep that `move done` runs
        (repo / ".claude" / "worktrees" / f"{ep}-{t}" / "scratch.txt").write_text("wip")
    assert cli("move", ep, "done", "--root", root).returncode == 0
    for t in tasks:
        wt = repo / ".claude" / "worktrees" / f"{ep}-{t}"
        assert wt.is_dir()
        (wt / "scratch.txt").unlink()
    return ep


def test_reap_epic_scopes_to_one_done_epic(repo, root):
    ep = done_epic(repo, root, "First done")
    other = done_epic(repo, root, "Second done", tasks=("gamma",))
    wt_a = repo / ".claude" / "worktrees" / f"{ep}-alpha"
    wt_b = repo / ".claude" / "worktrees" / f"{ep}-beta"
    other_a = repo / ".claude" / "worktrees" / f"{other}-gamma"
    (wt_b / "scratch.txt").write_text("uncommitted")
    orphan = stray_tree(repo, "gone-epic--x", merged=True)
    r = cli("reap", "--epic", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert s["removed"] == [str(wt_a)] and not wt_a.exists()
    assert "dirty" in left_reasons(s)[wt_b.name] and wt_b.is_dir()
    assert other_a.is_dir() and orphan.is_dir()
    assert f"{other}-gamma" in branches(repo) and "gone-epic--x" in branches(repo)


def test_reap_epic_keeps_unmerged_tree(repo, root):
    ep = done_epic(repo, root, "Late work", tasks=("alpha",))
    wt = repo / ".claude" / "worktrees" / f"{ep}-alpha"
    (wt / "late.txt").write_text("after done\n")
    git(wt, "add", ".")
    git(wt, "commit", "-m", "late work")
    r = cli("reap", "--epic", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert s["removed"] == [] and wt.is_dir()
    assert "unmerged" in left_reasons(s)[wt.name]


def test_reap_epic_refuses_epic_not_done(repo, root):
    todo = mk_epic(root, "Still todo")
    live = started(repo, root, ("alpha",), title="Running")
    commit_all(repo)
    wt = repo / ".claude" / "worktrees" / f"{live}-alpha"
    for ep, phase in ((todo, "todo"), (live, "in-progress")):
        r = cli("reap", "--epic", ep, "--root", root)
        assert r.returncode == 1
        assert f"reap: epic {ep} is not done (in {phase}/)" in r.stderr
    assert wt.is_dir()


def test_reap_epic_unknown_slug(repo, root):
    r = cli("reap", "--epic", "nope", "--root", root)
    assert r.returncode == 1 and "unknown epic 'nope'" in r.stderr


def test_reap_epic_dry_run_removes_nothing(repo, root):
    ep = done_epic(repo, root, "Dry done")
    wt_a = repo / ".claude" / "worktrees" / f"{ep}-alpha"
    wt_b = repo / ".claude" / "worktrees" / f"{ep}-beta"
    r = cli("reap", "--epic", ep, "--dry-run", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert s["dryRun"] is True and sorted(s["removed"]) == sorted([str(wt_a), str(wt_b)])
    assert wt_a.is_dir() and wt_b.is_dir() and f"{ep}-alpha" in branches(repo)


def test_reap_component_integration_trees_of_done_epic(tmp_path):
    wb = component_workbench(tmp_path)
    root = wb / "docs" / "plans"
    ep = mk_epic(root)
    commit_all(wb)
    (root / "done").mkdir(parents=True)
    git(wb, "mv", str(root / "todo" / ep), str(root / "done" / ep))
    commit_all(wb)
    merged = integration_tree(wb, ep, "proj", merged_on_origin=True)
    unmerged = integration_tree(wb, ep, "other", merged_on_origin=False)
    r = cli("reap", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert s["removed"] == [str(merged)] and not merged.exists()
    assert unmerged.is_dir() and "origin" in left_reasons(s)["other"]


# ---------------------------------------------------------------- lint


def test_lint_clean_tree_passes(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "alpha", extra=["--depends-on", "beta"])
    mk_task(root, ep, "beta")
    commit_all(repo)
    r = cli("lint", "--root", root)
    assert r.returncode == 0, r.stderr
    assert cli("lint", ep, "--root", root).returncode == 0


def test_lint_todo_epic_with_non_todo_task(repo, root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "alpha")
    set_meta(p, status="in-progress")
    r = cli("lint", "--root", root)
    assert r.returncode == 1 and "alpha" in r.stderr and "todo" in r.stderr


def test_lint_done_epic_with_open_task(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    commit_all(repo)
    (root / "done").mkdir()
    git(repo, "mv", str(root / "todo" / ep), str(root / "done" / ep))
    r = cli("lint", ep, "--root", root)
    assert r.returncode == 1 and "done" in r.stderr and "alpha" in r.stderr


def test_lint_review_stage_with_open_task(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    set_meta(root / "in-progress" / ep / "README.md", stage="review")
    r = cli("lint", "--root", root)
    assert r.returncode == 1 and "review" in r.stderr and "alpha" in r.stderr


def test_lint_unknown_depends_on(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "alpha", extra=["--depends-on", "nope"])
    r = cli("lint", "--root", root)
    assert r.returncode == 1 and "nope" in r.stderr


def test_lint_blocker_naming_no_epic(repo, root):
    mk_epic(root, "Top work", blockers="Ghost epic")
    r = cli("lint", "--root", root)
    assert r.returncode == 1 and "Ghost epic" in r.stderr


def test_lint_scoped_to_one_epic(repo, root):
    mk_epic(root, "Top work", blockers="Ghost epic")
    ok = mk_epic(root, "Fine epic")
    assert cli("lint", ok, "--root", root).returncode == 0
    assert cli("lint", "--root", root).returncode == 1


def test_lint_bad_status_and_stage_values(repo, root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "alpha")
    set_meta(p, status="finished")
    set_meta(root / "todo" / ep / "README.md", stage="polish")
    r = cli("lint", "--root", root)
    assert r.returncode == 1 and "finished" in r.stderr and "polish" in r.stderr


# ---------------------------------------------------------------- linked-worktree guard


def test_mutating_subcommands_refuse_in_linked_worktree(repo, root):
    ep = mk_epic(root)
    commit_all(repo)
    side = repo.parent / "side"
    git(repo, "worktree", "add", "-b", "side", str(side))
    side_root = side / "docs" / "plans"
    notes = repo / "n.txt"
    notes.write_text("x")
    for args in (
        ["move", ep, "in-progress"],
        ["move", ep, "done"],
        ["stage", ep, "review"],
        ["stage", ep, "build"],
        ["rename", ep, "Other"],
        ["review", ep, "--verdict", "pass", "--notes-file", notes],
        ["reap"],
    ):
        r = cli(*args, "--root", side_root)
        assert r.returncode == 1 and "main checkout" in r.stderr, args
    assert (root / "todo" / ep).is_dir()


# ---------------------------------------------------------------- safety: no force anywhere


def test_no_force_or_capital_d_in_ticket_or_merge_cleanup():
    # only new-epic's own flag lines are exempt; any other --force line still trips
    own = (
        "EXIT_NEAR_DUPLICATE = 3",
        "; pass --force to create anyway",
        'sp.add_argument("--force", action="store_true"',
    )
    own_exact = ('"--force",',)  # new-epic's formatted add_argument flag line
    src = "\n".join(
        line
        for line in SCRIPT.read_text().splitlines()
        if not any(o in line for o in own) and line.strip() not in own_exact
    )
    for bad in ("--force", "branch -D", '"-D"', "'-D'", '"-f"', "'-f'"):
        assert bad not in src, bad
    merge = MERGE.read_text()
    cleanup = merge[merge.index("def cleanup") : merge.index("def main")]
    for bad in ("--force", '"-D"', '"-f"'):
        assert bad not in cleanup, bad


def test_tasks_emit_branch_and_verified_head_for_the_epic_close_audit(root):
    """The auditOnly run reads each task's branch and verified head from `ticket.py tasks`."""
    ep = mk_epic(root)
    p = mk_task(root, ep, "alpha")
    mk_task(root, ep, "beta")
    set_meta(p, branch=f"{ep}-alpha", verified_head="abc123", acs_for_audit=["AC1"])
    r = cli("tasks", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    out = {t["id"]: t for t in json.loads(r.stdout)}
    assert out["alpha"]["branch"] == f"{ep}-alpha"
    assert out["alpha"]["verifiedHead"] == "abc123"
    assert out["alpha"]["acsForAudit"] == ["AC1"]
    assert out["beta"]["branch"] == ""
    assert out["beta"]["verifiedHead"] == ""


def test_reap_all_ignores_dirs_with_no_ticket(repo, root):
    live = mk_epic(root, "Live epic")
    commit_all(repo)
    assert cli("move", live, "in-progress", "--root", root).returncode == 0
    unknown = stray_tree(repo, "gone-epic-x", merged=True)  # single hyphen, maps to no ticket
    plain = stray_tree(repo, "plain-name", merged=True)
    legacy = stray_tree(repo, "gone-epic--x", merged=True)  # merged legacy tree stays reapable
    r = cli("reap", "--root", root)
    assert r.returncode == 0, r.stderr
    s = summary(r)
    assert unknown.is_dir() and plain.is_dir()
    assert str(unknown) not in s["removed"] and str(plain) not in s["removed"]
    assert not legacy.exists() and str(legacy) in s["removed"]
