"""init update: projects with no shared history with the template, merged through a graft."""

import argparse
import shutil
import sys
from importlib import import_module

import pytest
from helpers import LINT, sh, template_commit, write

T1 = "2024-01-01T00:00:00+0000"
T1_5 = "2024-01-15T00:00:00+0000"
T2 = "2024-02-01T00:00:00+0000"
COPIED = "2024-03-01T00:00:00+0000"
T3 = "2024-04-01T00:00:00+0000"
T4 = "2024-05-01T00:00:00+0000"


@pytest.fixture
def at(monkeypatch):
    def set_date(when):
        monkeypatch.setenv("GIT_AUTHOR_DATE", when)
        monkeypatch.setenv("GIT_COMMITTER_DATE", when)

    return set_date


@pytest.fixture
def make_copied(workbench, run_cli, allow_file, tmp_path, at):
    """A project made by copying the template's files: same content, no shared history."""

    def make(copied_at=COPIED):
        sh("init", "-b", "main", cwd=workbench)
        write(workbench, "tooling.txt", "v1\n")
        write(workbench, "docs/plans/todo/epic.md", "template epic\n")
        at(T1)
        sh("add", "-A", cwd=workbench)
        sh("commit", "-m", "template one", cwd=workbench)
        c1 = sh("rev-parse", "HEAD", cwd=workbench).stdout.strip()
        write(workbench, "tooling.txt", "v2\n")
        at(T2)
        sh("commit", "-am", "template two", cwd=workbench)
        c2 = sh("rev-parse", "HEAD", cwd=workbench).stdout.strip()
        upstream = tmp_path / "upstream.git"
        sh("clone", "--bare", str(workbench), str(upstream), cwd=tmp_path)
        shutil.rmtree(workbench / ".git")
        sh("init", "-b", "main", cwd=workbench)
        at(copied_at)
        sh("add", "-A", cwd=workbench)
        sh("commit", "-m", "copied from the template", cwd=workbench)
        root = sh("rev-parse", "HEAD", cwd=workbench).stdout.strip()
        r = run_cli(
            "new", "--name", "demo", "--component", "api:python", "--remote", "local-bare",
            "--purpose", "A booking service.",
        )  # fmt: skip
        assert r.returncode == 0, r.stderr
        sh("add", "-A", cwd=workbench)
        sh("commit", "-m", "init project", cwd=workbench, check=False)
        sh("remote", "add", "template", str(upstream), cwd=workbench)
        return {"c1": c1, "c2": c2, "root": root}

    return make


def state(project):
    return (
        sh("rev-parse", "HEAD", cwd=project).stdout,
        sh("status", "--porcelain", cwd=project).stdout,
        sh("replace", "-l", cwd=project).stdout,
    )


def assert_clean(project, before):
    assert state(project) == before
    assert before[1] == "" and before[2] == ""


def test_unrelated_refuses_with_candidate(workbench, make_copied, run_cli, tmp_path, at):
    shas = make_copied()
    at(T3)
    template_commit(workbench, tmp_path, {"tooling.txt": "v3\n"})
    before = state(workbench)
    r = run_cli("update", *LINT)
    assert r.returncode == 1
    err = r.stderr.splitlines()
    assert err[0] == "refused: no shared history with template/main"
    assert f"candidate base: {shas['c2']}" in err
    assert f"mise run init:update -- --base {shas['c2']}" in err
    assert_clean(workbench, before)


def test_unrelated_candidate_none_when_template_is_newer(
    workbench, make_copied, run_cli, tmp_path, at
):
    make_copied(copied_at="2023-06-01T00:00:00+0000")
    at(T3)
    template_commit(workbench, tmp_path, {"tooling.txt": "v3\n"})
    before = state(workbench)
    r = run_cli("update", *LINT)
    assert r.returncode == 1
    err = r.stderr.splitlines()
    assert err[0] == "refused: no shared history with template/main"
    assert "candidate base: none" in err
    assert any(line.startswith("mise run init:update -- --base ") for line in err)
    assert_clean(workbench, before)


def test_candidate_uses_oldest_root(workbench, make_copied, run_cli, tmp_path, at):
    shas = make_copied()
    side = tmp_path / "side"
    sh("init", "-q", "-b", "main", str(side), cwd=tmp_path)
    write(side, "side.txt", "older root\n")
    at(T1_5)
    sh("add", "-A", cwd=side)
    sh("commit", "-m", "older root", cwd=side)
    at(COPIED)
    sh("fetch", "-q", str(side), "main", cwd=workbench)
    sh("merge", "-q", "--allow-unrelated-histories", "-m", "join", "FETCH_HEAD", cwd=workbench)
    assert len(sh("rev-list", "--max-parents=0", "HEAD", cwd=workbench).stdout.split()) == 2
    at(T3)
    template_commit(workbench, tmp_path, {"tooling.txt": "v3\n"})
    r = run_cli("update", *LINT)
    assert r.returncode == 1
    assert f"candidate base: {shas['c1']}" in r.stderr.splitlines()


def test_base_grafts_merges_and_cleans_up(workbench, make_copied, run_cli, tmp_path, at):
    shas = make_copied()
    at(T3)
    sha = template_commit(workbench, tmp_path, {"tooling.txt": "v3\n"})
    head = sh("rev-parse", "HEAD", cwd=workbench).stdout.strip()
    r = run_cli("update", "--base", shas["c2"], *LINT)
    assert r.returncode == 0, r.stderr
    assert (workbench / "tooling.txt").read_text() == "v3\n"
    assert sh("rev-parse", "HEAD^1", cwd=workbench).stdout.strip() == head
    assert sh("rev-parse", "HEAD^2", cwd=workbench).stdout.strip() == sha
    assert f"Template-Commit: {sha}" in sh("log", "-1", "--format=%B", cwd=workbench).stdout
    assert sh("replace", "-l", cwd=workbench).stdout == ""
    assert sh("status", "--porcelain", cwd=workbench).stdout == ""
    assert not (workbench / "docs/plans/todo/epic.md").exists()
    roots = sh("rev-list", "--max-parents=0", "HEAD", cwd=workbench).stdout.split()
    assert shas["root"] in roots


def test_next_update_needs_no_base(workbench, make_copied, run_cli, tmp_path, at):
    shas = make_copied()
    at(T3)
    template_commit(workbench, tmp_path, {"tooling.txt": "v3\n"})
    assert run_cli("update", "--base", shas["c2"], *LINT).returncode == 0
    at(T4)
    sha = template_commit(workbench, tmp_path, {"tooling.txt": "v4\n"}, name="up2")
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert (workbench / "tooling.txt").read_text() == "v4\n"
    assert sh("rev-parse", "HEAD^2", cwd=workbench).stdout.strip() == sha
    assert sh("replace", "-l", cwd=workbench).stdout == ""


def test_base_not_a_commit_refused(workbench, make_copied, run_cli, tmp_path, at):
    make_copied()
    at(T3)
    template_commit(workbench, tmp_path, {"tooling.txt": "v3\n"})
    before = state(workbench)
    tree = sh("rev-parse", "HEAD^{tree}", cwd=workbench).stdout.strip()
    for bad in ("0123456789abcdef0123456789abcdef01234567", tree, "no-such-ref"):
        r = run_cli("update", "--base", bad, *LINT)
        assert r.returncode == 1, bad
        assert r.stderr.startswith("refused: --base"), r.stderr
        assert_clean(workbench, before)


def test_base_not_template_ancestor_refused(workbench, make_copied, run_cli, tmp_path, at):
    shas = make_copied()
    at(T3)
    template_commit(workbench, tmp_path, {"tooling.txt": "v3\n"})
    before = state(workbench)
    r = run_cli("update", "--base", shas["root"], *LINT)
    assert r.returncode == 1
    assert "is not an ancestor of template/main" in r.stderr
    assert_clean(workbench, before)


def test_base_refusal_after_graft_drops_replace(workbench, make_copied, run_cli, tmp_path, at):
    shas = make_copied()
    at(T3)
    template_commit(workbench, tmp_path, {"tooling.txt": "v3\n"})
    before = state(workbench)
    r = run_cli("update", "--base", shas["c2"], "--lint-command", "false")
    assert r.returncode == 1
    assert "lint failed" in r.stderr
    assert_clean(workbench, before)


def test_base_exception_drops_replace(workbench, make_copied, tmp_path, at, monkeypatch):
    shas = make_copied()
    at(T3)
    template_commit(workbench, tmp_path, {"tooling.txt": "v3\n"})
    sys.path.insert(0, str(workbench / "scripts" / "init_engine"))
    try:
        update = import_module("update")
    finally:
        sys.path.pop(0)

    def boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(update, "resolve_generated", boom)
    args = argparse.Namespace(
        root=str(workbench), url="unused", branch="main", lint_command="true", base=shas["c2"]
    )
    with pytest.raises(RuntimeError, match="boom"):
        update.cmd_update(args)
    assert sh("replace", "-l", cwd=workbench).stdout == ""


def test_base_ignored_when_history_shared(project, run_cli, tmp_path):
    sha = template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    r = run_cli("update", "--base", sha, *LINT)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines().count("--base ignored: history is shared") == 1
    assert sh("rev-parse", "HEAD^2", cwd=project).stdout.strip() == sha
