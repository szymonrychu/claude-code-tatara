"""init update: merge template tooling into a project, never the template's own docs."""

import os
import subprocess
import sys

import pytest

LINT = ["--lint-command", "true"]


def sh(*args, cwd, check=True):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def upstream_of(project):
    return project.parent / "upstream.git"


@pytest.fixture
def project(workbench, run_cli, allow_file, tmp_path):
    """An initialised project sharing history with a bare template upstream."""
    sh("init", "-b", "main", cwd=workbench)
    write(workbench, "tooling.txt", "v1\n")
    write(workbench, "docs/plans/todo/epic.md", "template epic\n")
    write(workbench, "docs/research/r.md", "template research\n")
    sh("add", "-A", cwd=workbench)
    sh("commit", "-m", "template base", cwd=workbench)
    upstream = tmp_path / "upstream.git"
    sh("clone", "--bare", str(workbench), str(upstream), cwd=tmp_path)
    r = run_cli(
        "new", "--name", "demo", "--component", "api:python", "--remote", "local-bare",
        "--purpose", "A booking service.",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    sh("rm", "-rq", "--cached", "--ignore-unmatch", "docs/research", cwd=workbench)
    sh("add", "-A", cwd=workbench)
    sh("commit", "-m", "init project", cwd=workbench, check=False)
    sh("remote", "add", "template", str(upstream), cwd=workbench)
    return workbench


def template_commit(project, tmp_path, files, name="up"):
    work = tmp_path / name
    sh("clone", str(upstream_of(project)), str(work), cwd=tmp_path)
    for rel, text in files.items():
        write(work, rel, text)
    sh("add", "-A", cwd=work)
    sh("commit", "-m", "template change", cwd=work)
    sh("push", "origin", "HEAD:main", cwd=work)
    return sh("rev-parse", "HEAD", cwd=work).stdout.strip()


TEMPLATE_FILES = {
    "tooling.txt": "v2\n",
    "docs/plans/todo/new-epic.md": "template epic 2\n",
    "docs/plans/facts.md": "template facts\n",
    "docs/research/more.md": "x\n",
    "MEMORY.md": "template memory\n",
}


def test_update_takes_tooling_drops_owned_paths(project, run_cli, tmp_path):
    memory = (project / "MEMORY.md").read_text()
    sha = template_commit(project, tmp_path, TEMPLATE_FILES)
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert (project / "tooling.txt").read_text() == "v2\n"
    tracked = sh("ls-files", cwd=project).stdout.split()
    for gone in ("docs/plans/todo/new-epic.md", "docs/plans/facts.md", "docs/research/more.md"):
        assert gone not in tracked
        assert not (project / gone).exists()
    assert "docs/plans/todo/.gitkeep" in tracked
    assert (project / "MEMORY.md").read_text().startswith(memory.rstrip("\n"))
    assert f"template update {sha[:12]}" in (project / "MEMORY.md").read_text()
    assert sh("status", "--porcelain", cwd=project).stdout == ""


def test_update_one_commit_records_template_commit(project, run_cli, tmp_path):
    sha = template_commit(project, tmp_path, TEMPLATE_FILES)
    head = sh("rev-parse", "HEAD", cwd=project).stdout.strip()
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert f"template update {sha[:12]}" in (project / "MEMORY.md").read_text()
    assert sh("status", "--porcelain", cwd=project).stdout == ""
    assert sh("rev-parse", "HEAD^1", cwd=project).stdout.strip() == head
    assert sh("rev-parse", "HEAD^2", cwd=project).stdout.strip() == sha
    msg = sh("log", "-1", "--format=%B", cwd=project).stdout
    assert msg.startswith(f"chore(workbench): template update {sha[:12]}")
    assert f"Template-Commit: {sha}" in msg
    assert f"chore(workbench): template update {sha[:12]}" in r.stdout


def test_update_up_to_date_is_noop(project, run_cli, tmp_path):
    sha = template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    assert run_cli("update", *LINT).returncode == 0
    head = sh("rev-parse", "HEAD", cwd=project).stdout
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert f"up to date with template/main {sha[:12]}" in r.stdout
    assert sh("rev-parse", "HEAD", cwd=project).stdout == head


def test_update_refuses_dirty_tree(project, run_cli):
    head = sh("rev-parse", "HEAD", cwd=project).stdout
    write(project, "stray.txt", "x")
    r = run_cli("update", *LINT)
    assert r.returncode == 1
    assert r.stderr.startswith("refused:")
    assert "stray.txt" in r.stderr
    (project / "stray.txt").unlink()
    (project / "tooling.txt").write_text("edited\n")
    r = run_cli("update", *LINT)
    assert r.returncode == 1
    assert "tooling.txt" in r.stderr
    assert (project / "tooling.txt").read_text() == "edited\n"
    assert sh("rev-parse", "HEAD", cwd=project).stdout == head
    assert not sh("remote", "get-url", "template", cwd=project, check=False).returncode


def test_update_refuses_uninitialised(workbench, run_cli):
    sh("init", "-b", "main", cwd=workbench)
    sh("add", "-A", cwd=workbench)
    sh("commit", "-m", "base", cwd=workbench)
    r = run_cli("update", *LINT)
    assert r.returncode == 1
    assert "not initialised" in r.stderr


def test_update_refuses_merge_in_progress(project, run_cli, tmp_path):
    template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    sh("fetch", "template", "main", cwd=project)
    sh("merge", "--no-commit", "--no-ff", "FETCH_HEAD", cwd=project)
    r = run_cli("update", *LINT)
    assert r.returncode == 1
    assert "merge" in r.stderr


def test_update_adds_missing_remote_from_url_flag(project, run_cli, tmp_path):
    template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    sh("remote", "remove", "template", cwd=project)
    r = run_cli("update", "--url", str(upstream_of(project)), *LINT)
    assert r.returncode == 0, r.stderr
    assert sh("remote", "get-url", "template", cwd=project).stdout.strip() == str(
        upstream_of(project)
    )
    assert (project / "tooling.txt").read_text() == "v2\n"


def test_update_adds_default_template_remote(project, run_cli, tmp_path, monkeypatch):
    from importlib import import_module

    sys.path.insert(0, str(project / "scripts" / "init_engine"))
    try:
        default = import_module("gitops").DEFAULT_TEMPLATE_URL
    finally:
        sys.path.pop(0)
    assert default == "https://github.com/szymonrychu/workbench"
    template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    sh("remote", "remove", "template", cwd=project)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "2")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "protocol.file.allow")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "always")
    monkeypatch.setenv("GIT_CONFIG_KEY_1", f"url.{upstream_of(project)}.insteadOf")
    monkeypatch.setenv("GIT_CONFIG_VALUE_1", default)
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert sh("config", "remote.template.url", cwd=project).stdout.strip() == default
    # and --url is honoured when given
    sh("reset", "--hard", "HEAD^1", cwd=project)
    sh("remote", "remove", "template", cwd=project)
    url = str(upstream_of(project))
    assert run_cli("update", "--url", url, *LINT).returncode == 0
    assert sh("config", "remote.template.url", cwd=project).stdout.strip() == url
    assert (project / "tooling.txt").read_text() == "v2\n"


def test_update_modify_delete_on_owned_path_keeps_project_side(project, run_cli, tmp_path):
    write(project, "docs/plans/todo/mine.md", "project epic\n")
    sh("add", "-A", cwd=project)
    sh("commit", "-m", "project epic", cwd=project)
    template_commit(project, tmp_path, {"docs/plans/todo/epic.md": "changed upstream\n"})
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert (project / "docs/plans/todo/mine.md").read_text() == "project epic\n"
    assert "docs/plans/todo/epic.md" not in sh("ls-files", cwd=project).stdout.split()


def test_update_lint_failure_aborts_the_merge(project, run_cli, tmp_path):
    template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    head = sh("rev-parse", "HEAD", cwd=project).stdout
    r = run_cli("update", "--lint-command", "false")
    assert r.returncode == 1
    assert r.stderr.startswith("refused:")
    assert sh("rev-parse", "HEAD", cwd=project).stdout == head
    assert sh("status", "--porcelain", cwd=project).stdout == ""
    assert (project / "tooling.txt").read_text() == "v1\n"
    assert not (project / ".git" / "MERGE_HEAD").exists()


def test_refresh_event_flag_is_recorded(project, run_cli):
    r = run_cli("refresh", "--event", "template update abc123")
    assert r.returncode == 0, r.stderr
    assert "template update abc123" in (project / "MEMORY.md").read_text()


def test_mise_task_runs_engine_update():
    from pathlib import Path

    text = (Path(__file__).resolve().parents[3] / "mise-tasks/init/update").read_text()
    assert 'exec python3 scripts/init_engine/cli.py update "$@"' in text
    assert os.access(Path(__file__).resolve().parents[3] / "mise-tasks/init/update", os.X_OK)


def test_update_keeps_existing_template_remote(project, run_cli, tmp_path):
    template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    url = sh("remote", "get-url", "template", cwd=project).stdout.strip()
    r = run_cli("update", "--url", "https://example.invalid/other", *LINT)
    assert r.returncode == 0, r.stderr
    assert sh("remote", "get-url", "template", cwd=project).stdout.strip() == url


def test_update_conflict_resolves_in_linked_worktree(project, run_cli, tmp_path):
    write(project, "docs/plans/todo/mine.md", "project epic\n")
    sh("add", "-A", cwd=project)
    sh("commit", "-m", "project epic", cwd=project)
    template_commit(project, tmp_path, {"docs/plans/todo/epic.md": "changed upstream\n"})
    sh("branch", "wt", cwd=project)
    wt = tmp_path / "wt"
    sh("worktree", "add", str(wt), "wt", cwd=project)
    cli = [sys.executable, str(project / "scripts/init_engine/cli.py"), "--root", str(wt)]
    r = subprocess.run([*cli, "update", *LINT], cwd=wt, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert sh("status", "--porcelain", cwd=wt).stdout == ""
