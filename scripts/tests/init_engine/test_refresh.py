"""init refresh: re-run the idempotent writers and the harness sync, keep user-filled text."""

import hashlib
import json

from init_helpers import personal_lint, sh


def make(run_cli, allow_file):
    r = run_cli(
        "new", "--name", "demo", "--component", "api:python", "--remote", "local-bare",
        "--purpose", "A booking service.", "--hard-rule", "No PII in logs",
        "--risk", "The payments path", "--role", "api=HTTP backend",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr


def test_refresh_keeps_user_text_and_rewrites_generated_parts(workbench, run_cli, allow_file):
    make(run_cli, allow_file)
    agents = workbench / "AGENTS.md"
    before = agents.read_text()
    mise = workbench / ".mise.toml"
    mise.write_text(mise.read_text().replace('"mise run --cd code/api test"', '"stale"'))
    r = run_cli("refresh")
    assert r.returncode == 0, r.stderr
    assert agents.read_text() == before
    for kept in ("A booking service.", "No PII in logs", "The payments path", "HTTP backend"):
        assert kept in agents.read_text()
    assert '"stale"' not in mise.read_text()
    args = (workbench.parent / "harness-args").read_text()
    assert args == f"--root {workbench.resolve()}"  # sync with no targets


def test_refresh_idempotent_preserves_user_text(workbench, run_cli, allow_file):
    make(run_cli, allow_file)
    assert run_cli("refresh").returncode == 0
    snap = {p: p.read_text() for p in (workbench / "AGENTS.md", workbench / ".mise.toml")}
    assert run_cli("refresh").returncode == 0
    assert {p: p.read_text() for p in snap} == snap
    for kept in ("A booking service.", "No PII in logs", "The payments path"):
        assert kept in snap[workbench / "AGENTS.md"]


def test_refresh_refuses_an_uninitialised_workbench(workbench, run_cli):
    r = run_cli("refresh")
    assert r.returncode == 1
    assert "not initialised" in r.stderr


def init_zorbax(workbench, run_cli):
    r = run_cli(
        "new", "--name", "zorbaxproj", "--component", "api:python", "--remote", "local-bare",
        "--purpose", "A zorbaxproj service.",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    allow = workbench / "scripts" / "personal-allow.local.json"
    if allow.exists():  # a workbench initialised before the allow file existed
        sh("rm", "-q", "-f", "scripts/personal-allow.local.json", cwd=workbench)
    lint = personal_lint(workbench, "zorbaxproj")
    sh("add", "-A", cwd=workbench)
    sh("commit", "-qm", "pre-fix init", cwd=workbench, check=False)
    return lint, allow


def test_refresh_allows_project_vocabulary(workbench, run_cli, allow_file):
    lint, allow = init_zorbax(workbench, run_cli)
    assert lint().returncode == 1
    r = run_cli("refresh")
    assert r.returncode == 0, r.stderr
    digest = hashlib.sha256(b"zorbaxproj").hexdigest()
    assert json.loads(allow.read_text())["allow"] == [{"path": "**", "pattern": digest}]
    assert lint().returncode == 0, lint().stdout
    staged = sh("diff", "--cached", "--name-only", cwd=workbench).stdout.split()
    assert "scripts/personal-allow.local.json" in staged


def test_refresh_allow_file_idempotent(workbench, run_cli, allow_file):
    lint, allow = init_zorbax(workbench, run_cli)
    assert run_cli("refresh").returncode == 0
    sh("add", "-A", cwd=workbench)
    sh("commit", "-qm", "allow", cwd=workbench)
    before = allow.read_bytes()
    assert run_cli("refresh").returncode == 0
    assert allow.read_bytes() == before
    assert lint().returncode == 0


def test_refresh_stages_only_allow_file(workbench, run_cli, allow_file):
    lint, allow = init_zorbax(workbench, run_cli)
    (workbench / "scratch.txt").write_text("untracked\n")
    (workbench / "README.md").write_text("edited\n")
    assert run_cli("refresh").returncode == 0
    staged = sh("diff", "--cached", "--name-only", cwd=workbench).stdout.split()
    assert staged == ["scripts/personal-allow.local.json"]
