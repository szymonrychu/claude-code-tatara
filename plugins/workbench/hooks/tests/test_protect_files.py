"""Tests for the protect_files PreToolUse hook (Edit|Write path guard)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "protect_files.py"

BLOCKED = [
    "/repo/.git/config",
    "/repo/.git/hooks/pre-commit",
    "/repo/.env",
    "/repo/app/.env.local",
    "/repo/.env.production",
    "/repo/terraform/terraform.tfstate",
    "/repo/terraform/terraform.tfstate.backup",
    "/opt/u/.ssh/id_rsa",
    "/opt/u/.ssh/id_ed25519",
    "/repo/certs/server.pem",
    "/repo/certs/tls.key",
    "/repo/charts/app/values.enc.yaml",
    "/repo/config.enc.json",
    "/repo/charts/app/db.secret.yaml",
    "/repo/charts/app/db.secret.prod.yml",
    "/repo/secrets.prod.yaml",
    "/repo/secrets.dev.yml",
    "/repo/charts/app/default.secrets.yaml",
]

ALLOWED = [
    "/repo/.env.example",
    "/repo/src/main.py",
    "/repo/README.md",
    "/repo/.github/workflows/ci.yml",
    "/repo/.gitignore",
    "/repo/docs/environment.md",
    "/repo/charts/app/values.yaml",
    "/repo/secrets.py",
    "/repo/keyboard.keymap",
]


def run(stdin: str):
    return subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True)


def payload(path: str) -> str:
    return json.dumps({"tool_input": {"file_path": path}})


@pytest.mark.parametrize("path", BLOCKED)
def test_blocked(path):
    result = run(payload(path))
    assert result.returncode == 2
    assert "BLOCKED by protect-files hook" in result.stderr
    assert path in result.stderr


@pytest.mark.parametrize("path", ALLOWED)
def test_allowed(path):
    result = run(payload(path))
    assert result.returncode == 0
    assert result.stderr == ""


@pytest.mark.parametrize("stdin", ["{}", '{"tool_input": {}}', '{"tool_input": "x"}'])
def test_empty_input_allowed(stdin):
    assert run(stdin).returncode == 0


@pytest.mark.parametrize("stdin", ["", "not json", "[]"])
def test_malformed_input_denied(stdin):
    assert run(stdin).returncode == 2


def test_message_names_no_personal_helper():
    stderr = run(payload("/repo/.env")).stderr
    assert "~/" not in stderr
    assert "szy" + "mon" not in stderr.lower()
    assert "workbench-secrets" in stderr


def test_patterns_blocked_and_allowed():
    for path in BLOCKED:
        assert run(payload(path)).returncode == 2, path
    for path in ALLOWED:
        assert run(payload(path)).returncode == 0, path
    assert ".env.example" in " ".join(ALLOWED)


@pytest.mark.parametrize(
    ("tool", "key"),
    [
        ("Edit", "file_path"),
        ("MultiEdit", "file_path"),
        ("Write", "file_path"),
        ("NotebookEdit", "notebook_path"),
    ],
)
def test_every_edit_tool_is_guarded(tool, key):
    stdin = json.dumps({"tool_name": tool, "tool_input": {key: "/x/.env"}})
    result = run(stdin)
    assert result.returncode == 2
    assert "/x/.env" in result.stderr


# --- em dash content guard ----------------------------------------------------

EM_DASH = "\u2014"


def tool_payload(tool: str, tool_input: dict) -> str:
    return json.dumps({"tool_name": tool, "tool_input": tool_input})


def assert_em_dash_denied(result) -> None:
    assert result.returncode == 2
    assert "U+2014" in result.stderr
    assert "plain hyphen" in result.stderr
    assert EM_DASH not in result.stderr


def test_em_dash_in_write_content_denied():
    stdin = tool_payload("Write", {"file_path": "/repo/a.md", "content": f"one {EM_DASH} two"})
    assert_em_dash_denied(run(stdin))


def test_em_dash_in_edit_new_string_denied():
    stdin = tool_payload(
        "Edit", {"file_path": "/repo/a.md", "old_string": "a", "new_string": f"a {EM_DASH} b"}
    )
    assert_em_dash_denied(run(stdin))


def test_em_dash_in_multiedit_denied():
    edits = [
        {"old_string": "a", "new_string": "b"},
        {"old_string": "c", "new_string": f"c {EM_DASH} d"},
    ]
    stdin = tool_payload("MultiEdit", {"file_path": "/repo/a.md", "edits": edits})
    assert_em_dash_denied(run(stdin))


def test_em_dash_in_notebook_edit_denied():
    stdin = tool_payload(
        "NotebookEdit",
        {"notebook_path": "/repo/n.ipynb", "cell_id": "c1", "new_source": f"# x {EM_DASH} y"},
    )
    assert_em_dash_denied(run(stdin))


def test_removing_an_em_dash_is_allowed():
    stdin = tool_payload(
        "Edit", {"file_path": "/repo/a.md", "old_string": f"a {EM_DASH} b", "new_string": "a - b"}
    )
    result = run(stdin)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    multi = tool_payload(
        "MultiEdit",
        {"file_path": "/repo/a.md", "edits": [{"old_string": EM_DASH, "new_string": "-"}]},
    )
    assert run(multi).returncode == 0


def test_protected_path_reason_wins_over_em_dash():
    stdin = tool_payload("Write", {"file_path": "/repo/.env", "content": EM_DASH})
    result = run(stdin)
    assert result.returncode == 2
    assert "editing an .env secrets file" in result.stderr
