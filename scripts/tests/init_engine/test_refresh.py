"""init refresh: re-run the idempotent writers and the harness sync, keep user-filled text."""


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
