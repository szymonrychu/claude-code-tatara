"""component add/remove: removal never loses unpushed work, and refusals change nothing."""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_adopt import make_source, ok


def g(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


@pytest.fixture
def wb(workbench, run_cli, allow_file):
    r = run_cli(
        "new", "--name", "demo", "--component", "api:python", "--component", "web:python",
        "--remote", "local-bare",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    ok("add", "-A", cwd=workbench)
    g("commit", "-q", "-m", "init", cwd=workbench)
    return workbench


def state(wb: Path):
    return (
        ok("rev-parse", "HEAD", cwd=wb),
        ok("status", "--porcelain", cwd=wb),
        (wb / "code/api").is_dir(),
        (wb / ".git/modules/api").is_dir(),
    )


def refused(wb, run_cli, text):
    before = state(wb)
    r = run_cli("component", "remove", "--name", "api")
    assert r.returncode == 1 and text in r.stderr, (r.stdout, r.stderr)
    assert state(wb) == before
    assert before[2] and before[3]


def test_remove_clean(wb, run_cli):
    r = run_cli("component", "remove", "--name", "api")
    assert r.returncode == 0, r.stderr
    assert not (wb / "code/api").exists()
    assert not (wb / ".git/modules/api").exists()
    assert "api" not in (wb / ".gitmodules").read_text()
    assert ok("log", "-1", "--format=%s", cwd=wb) == "chore(workbench): remove component api"
    assert ok("status", "--porcelain", cwd=wb) == ""
    assert "code/api" not in (wb / ".mise.toml").read_text()
    assert (wb / "code/web").is_dir()


def test_refuse_dirty_tracked(wb, run_cli):
    (wb / "code/api/README.md").write_text("changed\n")
    refused(wb, run_cli, "uncommitted")


def test_refuse_untracked(wb, run_cli):
    (wb / "code/api/new.txt").write_text("x\n")
    refused(wb, run_cli, "uncommitted")


def test_refuse_unpushed_branch(wb, run_cli):
    ok("checkout", "-q", "-b", "side", cwd=wb / "code/api")
    (wb / "code/api/s.txt").write_text("s\n")
    ok("add", "s.txt", cwd=wb / "code/api")
    ok("commit", "-q", "-m", "s", cwd=wb / "code/api")
    ok("checkout", "-q", "main", cwd=wb / "code/api")
    refused(wb, run_cli, "side")


def test_refuse_unpushed_commit_on_main(wb, run_cli):
    (wb / "code/api/s.txt").write_text("s\n")
    ok("add", "s.txt", cwd=wb / "code/api")
    ok("commit", "-q", "-m", "s", cwd=wb / "code/api")
    refused(wb, run_cli, "main")


def test_refuse_stash(wb, run_cli):
    (wb / "code/api/README.md").write_text("stash me\n")
    ok("stash", "push", "-q", cwd=wb / "code/api")
    refused(wb, run_cli, "stash")


def test_refuse_linked_worktree(wb, run_cli, tmp_path):
    ok("worktree", "add", "-q", "--detach", str(tmp_path / "wt"), cwd=wb / "code/api")
    refused(wb, run_cli, "worktree")


def test_unknown_component(wb, run_cli):
    r = run_cli("component", "remove", "--name", "nope")
    assert r.returncode == 1 and "not a component" in r.stderr


def test_remove_adopted_component_with_own_git_dir(workbench, run_cli, tmp_path):
    src, _ = make_source(tmp_path, origin=True)
    ok("worktree", "remove", "--force", str(tmp_path / "proj-wt-out"), cwd=src)
    ok("worktree", "remove", "--force", ".claude/worktrees/inner", cwd=src)
    ok("stash", "drop", cwd=src)
    ok("checkout", "-q", "--", "README.md", cwd=src)
    ok("push", "-q", "origin", "feature", cwd=src)
    ok("branch", "-D", "wt-out", "wt-in", cwd=src)
    ok("clean", "-fdxq", cwd=src)
    assert run_cli("adopt", "--path", str(src)).returncode == 0
    ok("add", "-A", cwd=workbench)
    g("commit", "-q", "-m", "init", cwd=workbench)
    assert (workbench / "code/proj/.git").is_dir()
    r = run_cli("component", "remove", "--name", "proj")
    assert r.returncode == 0, r.stderr
    assert not (workbench / "code/proj").exists()
    assert not (workbench / ".git/modules/proj").exists()


def test_add_new_component(wb, run_cli):
    r = run_cli("component", "add", "--component", "worker:python", "--remote", "local-bare")
    assert r.returncode == 0, r.stderr
    assert (wb / "code/worker/.git").exists()
    assert "worker" in (wb / "AGENTS.md").read_text()
    assert "worker" in (wb / ".mise.toml").read_text()


def test_add_adopt_url(wb, run_cli, tmp_path, allow_file):
    src, bare = make_source(tmp_path, name="extra")
    r = run_cli("component", "add", "--url", str(bare))
    assert r.returncode == 0, r.stderr
    assert (wb / "code/extra").is_dir()
    assert "extra" in (wb / "AGENTS.md").read_text()


def test_add_needs_exactly_one_form(wb, run_cli):
    assert run_cli("component", "add").returncode == 1


def test_add_updates_files(wb, run_cli):
    r = run_cli("component", "add", "--component", "worker:python", "--remote", "local-bare")
    assert r.returncode == 0, r.stderr
    assert (wb / "code/worker/.git").exists()
    assert "worker" in (wb / "AGENTS.md").read_text()
    assert "code/worker" in (wb / ".mise.toml").read_text()
    assert "code/worker" in (wb / "docs/architecture.md").read_text()
    assert "code/worker" in (wb / ".gitmodules").read_text()


def test_remove_refusals(wb, run_cli, tmp_path):
    (wb / "code/api/README.md").write_text("changed\n")
    refused(wb, run_cli, "uncommitted")
    ok("checkout", "--", "README.md", cwd=wb / "code/api")

    (wb / "code/api/new.txt").write_text("x\n")
    refused(wb, run_cli, "uncommitted")
    (wb / "code/api/new.txt").unlink()

    (wb / "code/api/README.md").write_text("stash me\n")
    ok("stash", "push", "-q", cwd=wb / "code/api")
    refused(wb, run_cli, "stash")
    ok("stash", "drop", "-q", cwd=wb / "code/api")

    (wb / "code/api/s.txt").write_text("s\n")
    ok("add", "s.txt", cwd=wb / "code/api")
    ok("commit", "-q", "-m", "s", cwd=wb / "code/api")
    refused(wb, run_cli, "main")
    ok("reset", "-q", "--hard", "origin/main", cwd=wb / "code/api")

    ok("worktree", "add", "-q", "--detach", str(tmp_path / "wt"), cwd=wb / "code/api")
    refused(wb, run_cli, "worktree")


def test_component_add_remove_commit(wb, run_cli):
    before = ok("rev-list", "--count", "HEAD", cwd=wb)
    r = run_cli("component", "add", "--component", "worker:python", "--remote", "local-bare")
    assert r.returncode == 0, r.stderr
    assert int(ok("rev-list", "--count", "HEAD", cwd=wb)) == int(before) + 1
    assert ok("log", "-1", "--format=%s", cwd=wb) == "chore(workbench): add component worker"
    assert ok("status", "--porcelain", cwd=wb) == ""
    assert ok("status", "--porcelain", cwd=wb) == ""
    r = run_cli("component", "remove", "--name", "worker")
    assert r.returncode == 0, r.stderr
    assert int(ok("rev-list", "--count", "HEAD", cwd=wb)) == int(before) + 2
    assert ok("log", "-1", "--format=%s", cwd=wb) == "chore(workbench): remove component worker"
    assert ok("status", "--porcelain", cwd=wb) == ""
