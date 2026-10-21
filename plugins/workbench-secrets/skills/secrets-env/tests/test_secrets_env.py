import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "secrets_env.py"
# Secret-shaped value built at run time so the secret scanner stays green.
VALUE = "ghp_" + "x" * 36


def _stub(bindir: Path, name: str, body: str) -> None:
    p = bindir / name
    p.write_text("#!/bin/sh\n" + body)
    p.chmod(0o755)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    env = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}
    subprocess.run(["git", "init", "-q"], cwd=r, check=True, env={**os.environ, **env})
    (r / ".gitignore").write_text(".env\n")
    (r / ".env.op").write_text("TOKEN=op://vault/item/token\nOTHER=op://vault/item/other\n")
    return r


@pytest.fixture
def bindir(tmp_path):
    b = tmp_path / "bin"
    b.mkdir()
    return b


def run(repo, bindir, *args, extra_env=None, path_only_stubs=True):
    env = {k: v for k, v in os.environ.items() if k != "WORKBENCH_SECRETS_CMD"}
    base = "/usr/bin:/bin"
    env["PATH"] = f"{bindir}:{base}"
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )


OP = f'while [ $# -gt 0 ]; do case "$1" in -o) o="$2"; shift;; esac; shift; done\nprintf "TOKEN={VALUE}\\nOTHER=abc\\n" > "$o"\n'  # noqa: E501


def test_op_inject_mode(repo, bindir):
    _stub(bindir, "op", OP)
    r = run(repo, bindir)
    assert r.returncode == 0, r.stderr
    out = repo / ".env"
    assert VALUE in out.read_text()
    assert stat.S_IMODE(out.stat().st_mode) == 0o600
    assert VALUE not in r.stdout + r.stderr
    assert "TOKEN" in r.stdout and "OTHER" in r.stdout and "2" in r.stdout


def test_loader_cmd_mode(repo, bindir):
    _stub(bindir, "myloader", f'echo "ref=$1" >&2\nprintf "A={VALUE}\\n"\n')
    r = run(repo, bindir, extra_env={"WORKBENCH_SECRETS_CMD": "myloader"})
    assert r.returncode == 0, r.stderr
    assert (repo / ".env").read_text() == f"A={VALUE}\n"
    assert stat.S_IMODE((repo / ".env").stat().st_mode) == 0o600
    assert VALUE not in r.stdout + r.stderr


def test_custom_out_path(repo, bindir):
    _stub(bindir, "op", OP)
    (repo / ".gitignore").write_text(".env\nlocal.env\n")
    r = run(repo, bindir, "--out", "local.env")
    assert r.returncode == 0, r.stderr
    assert (repo / "local.env").exists()


def test_refuses_without_op_or_loader(repo, bindir):
    r = run(repo, bindir)
    assert r.returncode != 0
    assert "op" in r.stderr and "WORKBENCH_SECRETS_CMD" in r.stderr
    assert not (repo / ".env").exists()


def test_refuses_unignored_output(repo, bindir):
    _stub(bindir, "op", OP)
    (repo / ".gitignore").write_text("")
    r = run(repo, bindir)
    assert r.returncode != 0
    assert "ignored" in r.stderr
    assert not (repo / ".env").exists()


def test_refuses_when_tracked(repo, bindir):
    _stub(bindir, "op", OP)
    (repo / ".env").write_text("X=1\n")
    subprocess.run(["git", "add", "-f", ".env"], cwd=repo, check=True)
    r = run(repo, bindir)
    assert r.returncode != 0
    assert "tracked" in r.stderr
    assert (repo / ".env").read_text() == "X=1\n"


def test_refuses_missing_reference_file(repo, bindir):
    _stub(bindir, "op", OP)
    (repo / ".env.op").unlink()
    r = run(repo, bindir)
    assert r.returncode != 0


def test_pack_has_no_personal_terms():
    # Words built at run time so this file does not trip lint:personal itself.
    words = ["home" + "lab", "har" + "bor", "tat" + "ara", "szy" + "monri"]
    root = SCRIPT.parents[1]
    for p in root.rglob("*"):
        if p.is_file() and "tests" not in p.parts and "__pycache__" not in p.parts:
            text = p.read_text().lower()
            for w in words:
                assert w not in text, (p, w)
