import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "worktree-create" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import merge as merge_mod  # noqa: E402
from create import WorktreeError, create  # noqa: E402
from merge import assess, main, merge_back  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=T", "-c", "commit.gpgsign=false"]


def git(repo, *args, check=True):
    return subprocess.run(GIT + list(args), cwd=repo, check=check, capture_output=True, text=True)


def commit(repo, name, body="x\n"):
    (repo / name).write_text(body)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", f"add {name}")


def rev(repo, ref):
    return git(repo, "rev-parse", ref).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("SUITE_LOCK_DIR", str(tmp_path / "lock"))
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    commit(r, "README.md", "base\n")
    return r


@pytest.fixture
def epic(repo):
    """An integration tree 'ep' plus a task tree 'ep-t1' forked from it with one commit."""
    ept = Path(create("ep", start=repo)["path"])
    task = Path(create("ep-t1", base="ep", start=repo)["path"])
    commit(task, "t1.py", "1\n")
    return repo, ept, task


def test_lands_into_integration_tree(epic):
    repo, ept, task = epic
    main_before = rev(repo, "main")
    info = merge_back("ep-t1", base="ep", start=repo)
    assert (ept / "t1.py").exists(), "work did not land in the integration tree"
    assert not (repo / "t1.py").exists()
    assert rev(repo, "main") == main_before
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() == "main"
    assert info["baseAfter"] == rev(repo, "ep") != info["baseBefore"]
    assert not task.exists()
    assert git(repo, "branch", "--list", "ep-t1").stdout.strip() == "", "branch not deleted"


def test_summary_carries_verification_and_base_shas(epic):
    repo, ept, _ = epic
    before = rev(repo, "ep")
    info = merge_back("ep-t1", base="ep", verify="echo ok", start=repo)
    assert info["baseBefore"] == before
    assert info["verification"]["command"] == "echo ok"
    assert info["verification"]["passed"] is True


def test_verify_runs_in_rebased_tree_before_fast_forward(epic):
    repo, ept, task = epic
    commit(ept, "moved.py")  # base moves, so a rebase is needed
    ep_before = rev(repo, "ep")
    cmd = "test -f moved.py && test -f t1.py && git -C . rev-parse ep > seen.out; pwd > cwd.out"
    merge_back("ep-t1", base="ep", verify=cmd, keep=True, start=repo)
    # ran in the task tree (rebased onto moved.py), while ep was still at its old commit
    assert (task / "seen.out").read_text().strip() == ep_before
    assert (task / "cwd.out").read_text().strip() == str(task.resolve())


def test_verify_failure_exits_4_and_never_advances_base(epic, monkeypatch, capsys):
    repo, ept, task = epic
    commit(ept, "moved.py")
    ep_before = rev(repo, "ep")
    monkeypatch.chdir(repo)
    rc = main(["--name", "ep-t1", "--base", "ep", "--verify", "seq 1 30; exit 3"])
    out = capsys.readouterr().out
    assert rc == 4
    assert "\n  16\n" in out and "\n  15\n" not in out
    assert rev(repo, "ep") == ep_before
    assert not (ept / "t1.py").exists()
    assert task.exists() and (task / "moved.py").exists(), "named tree must keep rebased commits"
    assert git(task, "merge-base", "--is-ancestor", ep_before, "HEAD", check=False).returncode == 0


def test_failing_verify_result_dict(epic):
    repo, _, _ = epic
    info = merge_back("ep-t1", base="ep", verify="echo boom; exit 2", start=repo)
    assert info["verification"]["passed"] is False
    assert "boom" in info["verification"]["tail"]
    assert info["baseAfter"] == info["baseBefore"]
    assert info["cleaned"] is False


def test_base_moved_rebases_and_reverifies(epic):
    repo, ept, task = epic
    calls = []
    real = merge_mod._run_verify

    def spy(cmd, wt):
        calls.append(rev(repo, "ep"))
        if len(calls) == 1:
            commit(ept, "late.py")  # base moves after the first verify
        return real(cmd, wt)

    merge_mod._run_verify = spy
    try:
        info = merge_back("ep-t1", base="ep", verify="true", start=repo)
    finally:
        merge_mod._run_verify = real
    assert len(calls) == 2 and calls[0] != calls[1]
    assert (ept / "t1.py").exists() and (ept / "late.py").exists()
    assert info["baseBefore"] == calls[1]


def test_gives_up_after_three_attempts_without_moving_base(epic):
    repo, ept, task = epic
    real = merge_mod._run_verify
    n = []

    def spy(cmd, wt):
        n.append(1)
        commit(ept, f"late{len(n)}.py")  # base always moves under us
        return real(cmd, wt)

    merge_mod._run_verify = spy
    try:
        with pytest.raises(WorktreeError) as e:
            merge_back("ep-t1", base="ep", verify="true", start=repo)
    finally:
        merge_mod._run_verify = real
    assert len(n) == 3 and "3 attempts" in str(e.value)
    assert not (ept / "t1.py").exists()
    assert task.exists()


def test_refuses_base_checked_out_nowhere(epic):
    repo, ept, task = epic
    git(repo, "worktree", "remove", "--force", str(ept))
    ep_before = rev(repo, "ep")
    task_before = rev(task, "HEAD")
    with pytest.raises(WorktreeError) as e:
        merge_back("ep-t1", base="ep", start=repo)
    msg = str(e.value)
    assert "ep is not checked out in any worktree of" in msg
    assert "ticket.py move <epic> in-progress" in msg
    assert rev(repo, "ep") == ep_before and rev(task, "HEAD") == task_before


def test_never_switches_main_checkout(repo):
    git(repo, "checkout", "-q", "-b", "other")
    wt = Path(create("feat", start=repo)["path"])
    commit(wt, "f.py")
    with pytest.raises(WorktreeError) as e:
        merge_back("feat", start=repo)
    assert "main is not checked out in any worktree" in str(e.value)
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() == "other"


def test_merge_py_never_runs_git_checkout():
    src = Path(merge_mod.__file__).read_text()
    assert '"checkout"' not in src


def test_failing_suite_after_ff_exits_4_in_target_tree(epic, monkeypatch, capsys):
    repo, ept, _ = epic
    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / "workbench.json").write_text(
        json.dumps({"suites": ["pwd > s.out; exit 5"]})
    )
    monkeypatch.chdir(repo)
    rc = main(["--name", "ep-t1", "--base", "ep"])
    assert rc == 4
    assert (ept / "s.out").read_text().strip() == str(ept.resolve())
    assert (ept / "t1.py").exists(), "merge stays in place"


def test_epic_close_verifies_rebased_tip_and_records_base_before(epic):
    repo, ept, task = epic
    merge_back("ep-t1", base="ep", start=repo)
    commit(repo, "hotfix.py")  # main moved while the epic ran
    main_before = rev(repo, "main")
    cmd = "test -f hotfix.py && test -f t1.py && git rev-parse main > m.out"
    info = merge_back("ep", base="main", keep=True, verify=cmd, start=repo)
    assert (ept / "m.out").read_text().strip() == main_before, "main moved before verify passed"
    assert info["baseBefore"] == main_before
    assert info["baseAfter"] == rev(repo, "main") == rev(ept, "HEAD")
    assert (repo / "t1.py").exists() and (repo / "hotfix.py").exists()
    assert ept.exists() and git(repo, "branch", "--list", "ep").stdout.strip()


def test_epic_close_failed_verify_leaves_main(epic):
    repo, ept, _ = epic
    merge_back("ep-t1", base="ep", start=repo)
    before = rev(repo, "main")
    info = merge_back("ep", base="main", keep=True, verify="exit 1", start=repo)
    assert info["verification"]["passed"] is False
    assert rev(repo, "main") == before and not (repo / "t1.py").exists()


def test_assess_works_against_an_epic_base(epic):
    repo, ept, _ = epic
    a = assess("ep-t1", base="ep", start=repo)
    assert a["commits"] == 1 and a["files"] == 1 and a["conflictPredicted"] is False


def test_epic_close_fast_forwards_main_keeping_integration_tree(epic):
    repo, ept, _ = epic
    merge_back("ep-t1", base="ep", start=repo)
    info = merge_back("ep", base="main", keep=True, verify="true", start=repo)
    assert rev(repo, "main") == rev(repo, "ep") == info["baseAfter"]
    assert (repo / "t1.py").exists()
    assert ept.exists() and git(repo, "branch", "--list", "ep").stdout.strip()


def test_cleanup_deletes_branch_merged_into_epic(epic):
    repo, ept, task = epic
    merge_back("ep-t1", base="ep", start=repo)
    assert git(repo, "branch", "--list", "ep-t1").stdout.strip() == ""
    assert git(repo, "merge-base", "--is-ancestor", "ep", "main", check=False).returncode != 0


def test_nothing_ahead_cleanup_runs_from_the_target_tree(epic):
    repo, ept, task = epic
    merge_back("ep-t1", base="ep", start=repo)
    commit(ept, "more.py")  # epic is now ahead of main
    create("ep-t2", base="ep", start=repo)
    merge_back("ep-t2", base="ep", start=repo)
    assert git(repo, "branch", "--list", "ep-t2").stdout.strip() == ""
