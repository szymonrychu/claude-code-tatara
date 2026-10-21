"""handoff skill: create a handoff file at the workbench root, redact secrets."""

import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "handoff.py"


@pytest.fixture
def root(tmp_path):
    (tmp_path / ".gitmodules").write_text("")
    (tmp_path / "code").mkdir()
    return tmp_path


def run(root, *args):
    env = {**os.environ, "WORKBENCH_ROOT": str(root)}
    env.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )


def test_new_writes_sections(root):
    r = run(root, "new", "--slug", "my-task")
    assert r.returncode == 0, r.stderr
    path = root / "docs" / "handoffs" / f"{date.today().isoformat()}-my-task.md"
    assert r.stdout.strip() == str(path)
    text = path.read_text()
    first = text.splitlines()[0]
    assert f"continue from {path}" in first
    heads = re.findall(r"^## (.+)$", text, re.M)
    assert heads == ["State", "Done", "Next", "Gotchas", "Suggested skills"]


def test_new_refuses_overwrite(root):
    assert run(root, "new", "--slug", "a").returncode == 0
    r = run(root, "new", "--slug", "a")
    assert r.returncode != 0
    assert "exists" in r.stderr


def test_new_rejects_bad_slug(root):
    assert run(root, "new", "--slug", "../evil").returncode != 0


def test_new_outside_workbench_fails(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("WORKBENCH_ROOT", "CLAUDE_PROJECT_DIR")}
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "new", "--slug", "x"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0


def test_redact(root):
    p = root / "h.md"
    p.write_text(
        "\n".join(
            [
                "GITHUB_TOKEN=" + "ghp_" + "x" * 36,
                "export DB_PASSWORD=hunter2",
                "api_key: abc123",
                "MY_PRIVATE_KEY=zzz",
                "client_secret = s3cr3t",
                "Authorization: Bearer " + "a" * 30,
                "-----" + "BEGIN RSA PRIVATE" + " KEY-----",
                "MIIBOgIBAAJBAK",
                "-----" + "END RSA PRIVATE" + " KEY-----",
                "PATH=/usr/bin",
                "see commit f00d1e5",
            ]
        )
        + "\n"
    )
    assert run(root, "redact", str(p)).returncode == 0
    out = p.read_text()
    for leaked in ("ghp_", "hunter2", "abc123", "zzz", "s3cr3t", "MIIBOg", "a" * 30):
        assert leaked not in out
    assert "GITHUB_TOKEN=<redacted>" in out
    assert "export DB_PASSWORD=<redacted>" in out
    assert "Bearer <redacted>" in out
    begin = "-----" + "BEGIN RSA PRIVATE" + " KEY-----"
    end = "-----" + "END RSA PRIVATE" + " KEY-----"
    assert f"{begin}\n<redacted>\n{end}" in out
    assert "PATH=/usr/bin" in out and "commit f00d1e5" in out


def test_redact_missing_file(root):
    assert run(root, "redact", str(root / "nope.md")).returncode != 0
