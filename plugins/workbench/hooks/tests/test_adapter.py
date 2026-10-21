"""Drive `hooks/adapter.py` as each harness does: payload on stdin, JSON on stdout.

Every case runs the adapter as a subprocess from an unrelated cwd, so the plugin
is resolved by the adapter's own `__file__`, the way harness configs launch it.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

HOOKS = Path(__file__).resolve().parents[1]
ADAPTER = HOOKS / "adapter.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(HOOKS))

import harness_payloads as hp  # noqa: E402
from worktree_lib import read_record  # noqa: E402

HARNESS_IDS = [h.name for h in hp.ALL]
DANGEROUS = "terraform destroy -auto-approve"
SAFE = "ls -la"


def run(
    harness: str, event: str, hook: str, payload: Any, cwd: Path
) -> tuple[int, dict[str, Any], str]:
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, str(ADAPTER), "--harness", harness, "--event", event, "--hook", hook],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    out = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, out, proc.stderr


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def worktree(tmp_path: Path) -> Path:
    path = tmp_path / "wb" / ".claude" / "worktrees" / "t1-adapter"
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "T")
    (path / "seed.txt").write_text("seed\n")
    git(path, "add", "seed.txt")
    git(path, "commit", "-qm", "seed")
    return path


def assert_deny_shape(harness: str, out: dict[str, Any], needle: str) -> None:
    """The harness's documented pre-tool deny shape, carrying the reason."""
    if harness == "copilot":
        assert out["permissionDecision"] == "deny"
        assert needle in out["permissionDecisionReason"]
        nested = out["hookSpecificOutput"]
        assert nested["hookEventName"] == "PreToolUse"
        assert nested["permissionDecision"] == "deny"
        assert needle in nested["permissionDecisionReason"]
    elif harness == "cursor":
        assert out["permission"] == "deny"
        assert needle in out["user_message"]
        assert needle in out["agent_message"]
    elif harness == "codex":
        nested = out["hookSpecificOutput"]
        assert nested["hookEventName"] == "PreToolUse"
        assert nested["permissionDecision"] == "deny"
        assert needle in nested["permissionDecisionReason"]
    elif harness in ("gemini", "antigravity"):
        assert out["decision"] == "deny"
        assert needle in out["reason"]
    else:
        raise AssertionError(f"no shape for {harness}")


def assert_stop_block_shape(harness: str, out: dict[str, Any], needle: str) -> None:
    """The harness's documented stop-block shape, carrying the reason."""
    if harness in ("copilot", "codex"):
        assert out["decision"] == "block"
        assert needle in out["reason"]
    elif harness == "cursor":
        assert needle in out["followup_message"]
    elif harness == "gemini":
        assert out["decision"] == "deny"
        assert needle in out["reason"]
    elif harness == "antigravity":
        assert out["decision"] == "continue"
        assert needle in out["reason"]
    else:
        raise AssertionError(f"no shape for {harness}")


def assert_allow(harness: str, rc: int, out: dict[str, Any], stderr: str) -> None:
    assert rc == 0, stderr
    assert stderr == ""
    assert "deny" not in json.dumps(out)
    assert "block" not in json.dumps(out)
    if harness == "antigravity":
        # Antigravity requires a `decision` on every PreToolUse output.
        assert out.get("decision") in (None, "allow")


# --- AC1 ----------------------------------------------------------------------


@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_shell_deny_every_harness(h: hp.Harness, tmp_path: Path) -> None:
    rc, out, stderr = run(h.harness, "pre-tool", "guard-bash", h.shell(DANGEROUS, "/w"), tmp_path)
    assert rc == 2
    assert "terraform destroy" in stderr
    assert_deny_shape(h.harness, out, "terraform destroy")


@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_shell_allow_every_harness(h: hp.Harness, tmp_path: Path) -> None:
    rc, out, stderr = run(h.harness, "pre-tool", "guard-bash", h.shell(SAFE, "/w"), tmp_path)
    assert_allow(h.harness, rc, out, stderr)


# --- AC2 ----------------------------------------------------------------------


@pytest.mark.parametrize("kind", ["edit", "write"])
@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_protected_edit_deny_every_harness(h: hp.Harness, kind: str, tmp_path: Path) -> None:
    payload = getattr(h, kind)("config/.env", "/w")
    rc, out, stderr = run(h.harness, "pre-tool", "protect-files", payload, tmp_path)
    assert rc == 2
    assert ".env" in stderr
    assert_deny_shape(h.harness, out, ".env")


def test_protected_edit_deny_codex_apply_patch_env(tmp_path: Path) -> None:
    patch = hp.codex_patch(
        "*** Update File: README.md", "@@", "-a", "+b", "*** Add File: .env", "+TOKEN=1"
    )
    rc, out, stderr = run(
        "codex", "pre-tool", "protect-files", hp.codex_apply_patch(patch, "/w"), tmp_path
    )
    assert rc == 2
    assert ".env" in stderr
    assert_deny_shape("codex", out, ".env")


@pytest.mark.parametrize("kind", ["edit", "write"])
@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_protected_edit_allow_every_harness(h: hp.Harness, kind: str, tmp_path: Path) -> None:
    payload = getattr(h, kind)("src/app.py", "/w")
    rc, out, stderr = run(h.harness, "pre-tool", "protect-files", payload, tmp_path)
    assert_allow(h.harness, rc, out, stderr)


# --- Codex patch paths ----------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        ("*** Add File: secrets/.env", "+A=1"),
        ("*** Update File: infra/prod.tfstate", "@@", "-a", "+b"),
        ("*** Delete File: .git/config",),
        ("*** Update File: notes.txt", "*** Move to: deploy/id_rsa", "@@", "-a", "+b"),
    ],
    ids=["add", "update", "delete", "move"],
)
def test_codex_patch_paths_deny(body: tuple[str, ...], tmp_path: Path) -> None:
    payload = hp.codex_apply_patch(hp.codex_patch(*body), "/w")
    rc, out, stderr = run("codex", "pre-tool", "protect-files", payload, tmp_path)
    assert rc == 2, stderr
    assert_deny_shape("codex", out, "BLOCKED by protect-files")


def test_codex_patch_paths_allow(tmp_path: Path) -> None:
    patch = hp.codex_patch(
        "*** Update File: a.py", "*** Move to: b.py", "@@", "-x", "+y", "*** Add File: c.md", "+z"
    )
    rc, out, stderr = run(
        "codex", "pre-tool", "protect-files", hp.codex_apply_patch(patch, "/w"), tmp_path
    )
    assert_allow("codex", rc, out, stderr)


def test_codex_edit_alias_with_patch_text(tmp_path: Path) -> None:
    """`apply_patch` matched under its `Edit` alias still yields the patch paths."""
    payload = hp.codex_apply_patch(hp.codex_patch("*** Add File: .env", "+A=1"), "/w")
    payload["tool_name"] = "Edit"
    rc, out, _ = run("codex", "pre-tool", "protect-files", payload, tmp_path)
    assert rc == 2
    assert_deny_shape("codex", out, ".env")


# --- AC3 ----------------------------------------------------------------------


@pytest.mark.parametrize("h", [hp.COPILOT, hp.COPILOT_NATIVE], ids=["pascal", "native"])
def test_copilot_emits_both_shapes(h: hp.Harness, tmp_path: Path) -> None:
    rc, out, _ = run("copilot", "pre-tool", "guard-bash", h.shell(DANGEROUS, "/w"), tmp_path)
    assert rc == 2
    assert out["permissionDecision"] == "deny"
    assert out["permissionDecisionReason"]
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert out["hookSpecificOutput"]["permissionDecisionReason"] == out["permissionDecisionReason"]


# --- AC4 ----------------------------------------------------------------------


@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_self_filter(h: hp.Harness, tmp_path: Path) -> None:
    """VS Code ignores matchers, so every guard sees every tool and must filter itself."""
    # guard-bash on a write whose content would be a dangerous command: allow.
    write = h.write("notes/terraform destroy.md", "/w")
    rc, out, stderr = run(h.harness, "pre-tool", "guard-bash", write, tmp_path)
    assert_allow(h.harness, rc, out, stderr)
    # protect-files on a shell command that names a protected file: allow.
    rc, out, stderr = run(
        h.harness, "pre-tool", "protect-files", h.shell("cat .env", "/w"), tmp_path
    )
    assert_allow(h.harness, rc, out, stderr)
    # the stop guard on a pre-tool event: allow.
    rc, out, stderr = run(
        h.harness, "pre-tool", "subagent-commit-guard", h.shell(DANGEROUS, "/w"), tmp_path
    )
    assert_allow(h.harness, rc, out, stderr)


@pytest.mark.parametrize("harness", ["copilot", "cursor", "codex", "gemini", "antigravity"])
def test_self_filter_unknown_tool(harness: str, tmp_path: Path) -> None:
    payload = {
        "tool_name": "WebSearch",
        "toolName": "WebSearch",
        "cwd": "/w",
        "tool_input": {"query": "terraform destroy .env"},
    }
    for hook in ("guard-bash", "protect-files"):
        rc, out, stderr = run(harness, "pre-tool", hook, payload, tmp_path)
        assert_allow(harness, rc, out, stderr)


def test_vscode_tool_aliases(tmp_path: Path) -> None:
    """VS Code Local tool names (undocumented) normalize like the Copilot CLI ones."""
    shell = {
        "hook_event_name": "PreToolUse",
        "cwd": "/w",
        "tool_name": "run_in_terminal",
        "tool_input": {"command": DANGEROUS},
    }
    rc, out, _ = run("copilot", "pre-tool", "guard-bash", shell, tmp_path)
    assert rc == 2
    assert_deny_shape("copilot", out, "terraform destroy")
    edit = {
        "hook_event_name": "PreToolUse",
        "cwd": "/w",
        "tool_name": "create_file",
        "tool_input": {"filePath": "/w/.env", "content": "x"},
    }
    rc, out, _ = run("copilot", "pre-tool", "protect-files", edit, tmp_path)
    assert rc == 2
    assert_deny_shape("copilot", out, ".env")


def test_cursor_claude_third_party_payload(tmp_path: Path) -> None:
    """Cursor running a Claude-format hook may hand over Claude tool names."""
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": "/w",
        "tool_name": "Bash",
        "tool_input": {"command": DANGEROUS},
    }
    rc, out, _ = run("cursor", "pre-tool", "guard-bash", payload, tmp_path)
    assert rc == 2
    assert_deny_shape("cursor", out, "terraform destroy")


def test_shell_command_as_argv_list(tmp_path: Path) -> None:
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": "/w",
        "tool_name": "Bash",
        "tool_input": {"command": ["bash", "-lc", DANGEROUS]},
    }
    rc, out, _ = run("codex", "pre-tool", "guard-bash", payload, tmp_path)
    assert rc == 2
    assert_deny_shape("codex", out, "terraform destroy")


# --- AC5 ----------------------------------------------------------------------


@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_stop_block_every_harness(h: hp.Harness, worktree: Path, tmp_path: Path) -> None:
    (worktree / "wip.txt").write_text("unsaved\n")
    rc, out, stderr = run(
        h.harness, "stop", "subagent-commit-guard", h.stop(str(worktree)), tmp_path
    )
    assert rc == 2
    assert "uncommitted" in stderr
    assert_stop_block_shape(h.harness, out, "wip.txt")


@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_stop_allow_clean_every_harness(h: hp.Harness, worktree: Path, tmp_path: Path) -> None:
    rc, out, stderr = run(
        h.harness, "stop", "subagent-commit-guard", h.stop(str(worktree)), tmp_path
    )
    assert rc == 0, stderr
    assert stderr == ""
    assert out == {}


@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_stop_fires_once(h: hp.Harness, worktree: Path, tmp_path: Path) -> None:
    """Once the agent has been told, the harness's loop marker lets the turn end."""
    (worktree / "wip.txt").write_text("unsaved\n")
    payload = h.stop(str(worktree))
    if h.name == "cursor":
        payload["loop_count"] = 1
    elif h.name in ("copilot-native", "antigravity"):
        payload["stopHookActive"] = True
    else:
        payload["stop_hook_active"] = True
    rc, out, stderr = run(h.harness, "stop", "subagent-commit-guard", payload, tmp_path)
    assert rc == 0, stderr
    assert out == {}


# --- verify-recorder ----------------------------------------------------------


@pytest.mark.parametrize("failed", [False, True], ids=["passed", "failed"])
@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_verify_recorder_every_harness(
    h: hp.Harness, failed: bool, worktree: Path, tmp_path: Path
) -> None:
    payload = h.post_shell("pytest -q", str(worktree), failed)
    rc, out, stderr = run(h.harness, "post-tool", "verify-recorder", payload, tmp_path)
    assert rc == 0, stderr
    assert out == {}
    record = read_record(str(worktree))
    assert record is not None
    assert record["command"] == "pytest -q"
    assert record["head"] == git(worktree, "rev-parse", "HEAD")
    assert record["passed"] is (not failed)


@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_verify_recorder_ignores_non_verify(h: hp.Harness, worktree: Path, tmp_path: Path) -> None:
    payload = h.post_shell("ls", str(worktree), False)
    rc, out, _ = run(h.harness, "post-tool", "verify-recorder", payload, tmp_path)
    assert rc == 0
    assert out == {}
    assert read_record(str(worktree)) is None


# --- AC6 ----------------------------------------------------------------------


def _decisions(value: Any) -> list[str]:
    """Every string value anywhere in an output document."""
    if isinstance(value, dict):
        return [s for v in value.values() for s in _decisions(v)]
    if isinstance(value, list):
        return [s for v in value for s in _decisions(v)]
    return [value] if isinstance(value, str) else []


@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
def test_never_ask(h: hp.Harness, worktree: Path, tmp_path: Path) -> None:
    (worktree / "wip.txt").write_text("unsaved\n")
    cases = [
        ("pre-tool", h.shell(DANGEROUS, "/w")),
        ("pre-tool", h.shell(SAFE, "/w")),
        ("pre-tool", h.edit(".env", "/w")),
        ("pre-tool", h.write("ok.txt", "/w")),
        ("post-tool", h.post_shell("pytest", str(worktree), True)),
        ("stop", h.stop(str(worktree))),
        ("pre-tool", "not json"),
    ]
    hooks = ("guard-bash", "protect-files", "verify-recorder", "subagent-commit-guard")
    for event, payload in cases:
        for hook in hooks:
            rc, out, _ = run(h.harness, event, hook, payload, tmp_path)
            assert rc in (0, 2)
            values = _decisions(out)
            assert "ask" not in values and "force_ask" not in values, (event, hook, out)


# --- usage and fail-closed ------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["--harness", "vim", "--event", "pre-tool", "--hook", "guard-bash"],
        ["--harness", "codex", "--event", "pre-commit", "--hook", "guard-bash"],
        ["--harness", "codex", "--event", "pre-tool", "--hook", "rm-guard"],
        ["--harness", "codex", "--event", "pre-tool"],
    ],
    ids=["harness", "event", "hook", "missing"],
)
def test_usage_error_exits_2(argv: list[str], tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(ADAPTER), *argv],
        input=json.dumps(hp.CODEX.shell(SAFE, "/w")),
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert proc.returncode == 2
    assert "usage:" in proc.stderr
    assert proc.stdout == ""


@pytest.mark.parametrize("h", hp.ALL, ids=HARNESS_IDS)
@pytest.mark.parametrize("stdin", ["", "not json", "[1, 2]"], ids=["empty", "garbage", "list"])
def test_unreadable_payload_fails_closed_pre_tool(
    h: hp.Harness, stdin: str, tmp_path: Path
) -> None:
    rc, out, stderr = run(h.harness, "pre-tool", "guard-bash", stdin, tmp_path)
    assert rc == 2
    assert "unreadable" in stderr
    assert_deny_shape(h.harness, out, "unreadable")


@pytest.mark.parametrize(
    "event,hook", [("post-tool", "verify-recorder"), ("stop", "subagent-commit-guard")]
)
def test_unreadable_payload_allows_post_tool_and_stop(
    event: str, hook: str, tmp_path: Path
) -> None:
    rc, out, stderr = run("codex", event, hook, "not json", tmp_path)
    assert rc == 0, stderr
    assert out == {}
