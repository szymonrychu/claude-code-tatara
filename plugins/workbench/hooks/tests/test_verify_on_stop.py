"""Tests for the opt-in Stop hook that runs the repo test task (verify-on-stop.py)."""

import importlib.util
import json
import subprocess
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]
PLUGIN_JSON = HOOKS.parent / ".claude-plugin" / "plugin.json"

spec = importlib.util.spec_from_file_location("verify_on_stop", HOOKS / "verify-on-stop.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

ON = {"WORKBENCH_VERIFY_ON_STOP": "1"}


class FakeRun:
    """Injected subprocess runner: answers git and mise calls from a script."""

    def __init__(self, dirty=True, has_test=True, test=None, git_ok=True):
        self.dirty, self.has_test, self.git_ok = dirty, has_test, git_ok
        self.test = test or (0, "ok\n")
        self.calls = []

    def __call__(self, cmd, cwd, timeout):
        self.calls.append(list(cmd))
        if cmd[:2] == ["git", "rev-parse"]:
            if not self.git_ok:
                return 128, "not a git repository"
            return 0, f"{cwd}\n"
        if cmd[:2] == ["git", "worktree"]:
            return 0, ""
        if cmd[:2] == ["git", "status"]:
            return 0, " M file.py\n" if self.dirty else ""
        if cmd[:3] == ["mise", "tasks", "ls"]:
            return 0, json.dumps([{"name": "test"}] if self.has_test else [])
        if cmd == ["mise", "run", "test"]:
            code, out = self.test
            if code == "timeout":
                raise subprocess.TimeoutExpired(cmd, timeout)
            return code, out
        return 0, ""


def go(payload=None, env=ON, run=None):
    payload = {"cwd": "/repo"} if payload is None else payload
    return mod.main(payload, env, run=run or FakeRun())


def test_off_by_default():
    run = FakeRun(test=(1, "boom"))
    assert go(env={}, run=run) is None
    assert run.calls == []


def test_stop_hook_active_noop():
    assert go({"cwd": "/repo", "stop_hook_active": True}, run=FakeRun(test=(1, "boom"))) is None


def test_clean_tree_noop():
    assert go(run=FakeRun(dirty=False, test=(1, "boom"))) is None


def test_non_git_noop():
    assert go(run=FakeRun(git_ok=False)) is None


def test_passing_tests_noop():
    assert go(run=FakeRun(test=(0, "all green"))) is None


def test_failure_blocks_with_tail():
    out = "\n".join(f"line {i}" for i in range(200)) + "\nFAILED last"
    result = go(run=FakeRun(test=(1, out)))
    assert result["decision"] == "block"
    reason = result["reason"]
    assert "/repo" in reason and "FAILED last" in reason
    assert "line 100" not in reason
    assert len(reason) < 4000


def test_reason_is_capped_for_long_lines():
    result = go(run=FakeRun(test=(1, "x" * 50000)))
    assert len(result["reason"]) < 4000


def test_timeout_blocks():
    result = go(run=FakeRun(test=("timeout", "")))
    assert result["decision"] == "block"
    assert "/repo" in result["reason"] and "timed out" in result["reason"]


def test_internal_error_fails_open(capsys):
    def boom(cmd, cwd, timeout):
        raise RuntimeError("kaput")

    assert go(run=boom) is None
    assert "kaput" in capsys.readouterr().err


def test_registered_as_stop_hook():
    stop = json.loads(PLUGIN_JSON.read_text())["hooks"]["Stop"]
    hook = stop[0]["hooks"][0]
    assert hook["command"] == 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/verify-on-stop.py"'
    assert hook["timeout"] == 900 and hook["statusMessage"] == "Verifying tests..."
