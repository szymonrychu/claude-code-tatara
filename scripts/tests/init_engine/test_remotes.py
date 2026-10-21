"""Forge remote modes, with gh and glab stubbed on PATH. Never a real forge."""

import os
import subprocess

import pytest

STUB = """#!/bin/sh
echo "$(basename "$0") $*" >> "$STUB_LOG"
case "$*" in
  "api user -q .login") echo ghuser ;;
  "api user") echo '{"id": 1, "username": "gluser"}' ;;
  "repo view "*) [ -n "$STUB_EXISTS" ] && exit 0; exit 1 ;;
  "repo create "*)
    slug="$3"
    bare="$STUB_REMOTES/${slug##*/}.git"
    git init -q --bare -b main "$bare"
    echo "$bare" ;;
  *) exit 9 ;;
esac
"""


@pytest.fixture
def forge(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for tool in ("gh", "glab"):
        f = bindir / tool
        f.write_text(STUB)
        f.chmod(0o755)
    log = tmp_path / "calls.log"
    log.write_text("")
    remotes = tmp_path / "forge-remotes"
    remotes.mkdir()
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("STUB_LOG", str(log))
    monkeypatch.setenv("STUB_REMOTES", str(remotes))

    class F:
        calls = lambda self: log.read_text().splitlines()  # noqa: E731
        bare = remotes

    return F()


def g(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def creates(forge):
    return [c for c in forge.calls() if " repo create " in c]


def test_requires_confirmation(workbench, run_cli, forge):
    r = run_cli("new", "--name", "p", "--component", "api", "--remote", "github")
    assert r.returncode == 1
    assert "gh repo create ghuser/api --private" in r.stdout
    assert creates(forge) == []
    assert not (workbench / "code" / "api").exists()
    assert not (workbench / ".git").exists()


def test_creates_private_repo(workbench, run_cli, forge, allow_file):
    r = run_cli(
        "new", "--name", "p", "--component", "api", "--component", "web",
        "--remote", "github", "--confirm-forge",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    assert creates(forge) == [
        "gh repo create ghuser/api --private",
        "gh repo create ghuser/web --private",
    ]
    url = g("remote", "get-url", "origin", cwd=workbench / "code/api").stdout.strip()
    assert url == str(forge.bare / "api.git")
    assert g("rev-parse", "main", cwd=forge.bare / "api.git").returncode == 0


def test_gitlab_confirmed_with_owner_and_public(workbench, run_cli, forge, allow_file):
    r = run_cli(
        "new", "--name", "p", "--component", "api", "--remote", "gitlab",
        "--forge-owner", "team/sub", "--public", "--confirm-forge",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    assert creates(forge) == ["glab repo create team/sub/api --public"]
    assert not any("api user" in c for c in forge.calls())


def test_gitlab_owner_from_authenticated_user(workbench, run_cli, forge):
    r = run_cli("new", "--name", "p", "--component", "api", "--remote", "gitlab")
    assert r.returncode == 1
    assert "glab repo create gluser/api --private" in r.stdout


def test_existing_forge_repo_is_an_error_and_creates_nothing(
    workbench, run_cli, forge, monkeypatch
):
    monkeypatch.setenv("STUB_EXISTS", "1")
    r = run_cli("new", "--name", "p", "--component", "api", "--remote", "github", "--confirm-forge")
    assert r.returncode == 1
    assert "already exists" in r.stderr
    assert creates(forge) == []


def test_confirm_flag_alone_does_not_create_for_other_modes(workbench, run_cli, forge, allow_file):
    r = run_cli(
        "new", "--name", "p", "--component", "api", "--remote", "local-bare", "--confirm-forge"
    )
    assert r.returncode == 0, r.stderr
    assert forge.calls() == []


def test_remote_forge_parse(forge):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "init_engine"))
    import remotes

    assert remotes.parse_mode("github") == ("github", "")
    assert remotes.parse_mode("gitlab") == ("gitlab", "")


def test_owner_resolution(workbench, run_cli, forge):
    # github: defaults to the authenticated user, --forge-owner overrides it
    r = run_cli("new", "--name", "p", "--component", "api", "--remote", "github")
    assert "gh repo create ghuser/api --private" in r.stdout
    r = run_cli(
        "new", "--name", "p", "--component", "api", "--remote", "github",
        "--forge-owner", "acme",
    )  # fmt: skip
    assert "gh repo create acme/api --private" in r.stdout
    assert not any(c.startswith("gh repo create") for c in forge.calls())
    # gitlab: same
    r = run_cli("new", "--name", "p", "--component", "api", "--remote", "gitlab")
    assert "glab repo create gluser/api --private" in r.stdout
    r = run_cli(
        "new", "--name", "p", "--component", "api", "--remote", "gitlab",
        "--forge-owner", "grp/sub",
    )  # fmt: skip
    assert "glab repo create grp/sub/api --private" in r.stdout


def test_relative_local_bare_resolves_against_invoking_cwd(workbench, tmp_path, allow_file):
    import sys

    invoked = tmp_path / "elsewhere"
    invoked.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            str(workbench / "scripts/init_engine/cli.py"),
            "new",
            "--name",
            "p",
            "--component",
            "api",
            "--remote",
            "local-bare:rel-bare",
        ],
        cwd=workbench,
        env={**os.environ, "INIT_ENGINE_CWD": str(invoked)},
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert (invoked / "rel-bare/api.git").is_dir()
    assert not (workbench / "rel-bare").exists()
