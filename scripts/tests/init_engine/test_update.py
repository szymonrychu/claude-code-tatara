"""init update: merge template tooling into a project, never the template's own docs."""

import os
import subprocess
import sys

from init_helpers import LINT, sh, template_commit, upstream_of, write

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


def test_update_keeps_existing_template_remote(project, run_cli, tmp_path):
    url = str(upstream_of(project))
    assert sh("remote", "get-url", "template", cwd=project).stdout.strip() == url
    assert url != "https://github.com/szymonrychu/workbench"
    template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert (project / "tooling.txt").read_text() == "v2\n"
    assert sh("remote", "get-url", "template", cwd=project).stdout.strip() == url


def test_update_keeps_personal_allow_local(project, run_cli, tmp_path):
    rel = "scripts/personal-allow.local.json"
    body = '{"allow": [{"path": "docs/**"}]}\n'
    write(project, rel, body)
    sh("add", rel, cwd=project)
    sh("commit", "-m", "project allow", cwd=project)
    template_commit(project, tmp_path, TEMPLATE_FILES)
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert (project / rel).read_text() == body
    assert rel in sh("ls-files", cwd=project).stdout.split()


def test_update_keeps_plugin_license_holder(project, run_cli, tmp_path):
    rel = "plugins/workbench/LICENSE"
    text = (project / rel).read_text().replace("Copyright (c) 2026 ", "Copyright (c) 2027 ")
    write(
        project,
        rel,
        text.replace("2027 ", "2027 Project Holder ", 1).replace(
            "Project Holder " + "Szymon Richert", "Project Holder"
        ),
    )
    sh("add", rel, cwd=project)
    sh("commit", "-m", "project holder", cwd=project)
    template_commit(project, tmp_path, {rel: "MIT License\n\nCopyright (c) upstream holder\n"})
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert "Project Holder" in (project / rel).read_text()
