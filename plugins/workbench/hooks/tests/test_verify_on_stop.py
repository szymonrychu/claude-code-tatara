"""Tests for the opt-in Stop hook that runs the repo test task (verify-on-stop.py)."""

import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
PLUGIN_JSON = HOOKS.parent / ".claude-plugin" / "plugin.json"

spec = importlib.util.spec_from_file_location("verify_on_stop", HOOKS / "verify-on-stop.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

ON = {"WORKBENCH_VERIFY_ON_STOP": "1"}


class FakeRun:
    """Injected subprocess runner: answers git and mise calls from a script."""

    def __init__(self, dirty=True, has_test=True, test=None, git_ok=True, clock=None, cost=0):
        self.clock, self.cost = clock, cost
        self.dirty, self.has_test, self.git_ok = dirty, has_test, git_ok
        self.test = test or (0, "ok\n")
        self.calls = []
        self.timeouts = []

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
            self.timeouts.append(timeout)
            if self.clock:
                self.clock.now += self.cost
            code, out = self.test
            if code == "timeout":
                raise subprocess.TimeoutExpired(cmd, timeout)
            return code, out
        return 0, ""


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def make_repos(tmp_path, n=2):
    for i in range(n - 1):
        (tmp_path / ".worktrees" / "b" / f"r{i}" / ".git").mkdir(parents=True)
    return str(tmp_path)


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


def test_candidates_glob_from_toplevel_not_cwd(tmp_path):
    (tmp_path / ".worktrees" / "b" / "r" / ".git").mkdir(parents=True)
    sub = tmp_path / "sub"
    sub.mkdir()

    def run(cmd, cwd, timeout):
        return 0, f"{tmp_path}\n"

    found = mod._candidates(str(sub), run)
    assert found == [str(tmp_path), str(tmp_path / ".worktrees" / "b" / "r")]


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, 600),
        ("abc", 600),
        ("0", 600),
        ("-5", 600),
        ("30", 30),
        ("5000", 840),
    ],
)
def test_timeout_env_fallback_and_clamp(value, expected):
    env = dict(ON) if value is None else {**ON, "WORKBENCH_VERIFY_TIMEOUT": value}
    run = FakeRun()
    mod.main({"cwd": "/repo"}, env, run=run, clock=Clock())
    assert run.timeouts == [expected]


def test_timeout_capped_to_remaining_budget(tmp_path):
    clock = Clock()
    run = FakeRun(clock=clock, cost=500)
    cwd = make_repos(tmp_path, 2)
    assert mod.main({"cwd": cwd}, ON, run=run, clock=clock) is None
    assert run.timeouts == [600, 340]


def test_budget_exhausted_blocks_naming_unverified(tmp_path):
    clock = Clock()
    run = FakeRun(clock=clock, cost=900)
    cwd = make_repos(tmp_path, 3)
    result = mod.main({"cwd": cwd}, ON, run=run, clock=clock)
    assert result["decision"] == "block"
    assert "not verified" in result["reason"]
    assert str(tmp_path / ".worktrees" / "b" / "r0") in result["reason"]
    assert str(tmp_path / ".worktrees" / "b" / "r1") in result["reason"]
    assert len(run.timeouts) == 1


def test_real_timeout_kills_process_tree(tmp_path):
    pidfile = tmp_path / "pid"
    script = f"sleep 300 & echo $! > {pidfile}; wait"
    with pytest.raises(subprocess.TimeoutExpired):
        mod._run(["sh", "-c", script], str(tmp_path), 1)
    pid = int(pidfile.read_text())
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
        except FileNotFoundError:
            return
        if state == "Z":  # dead, only awaiting reaping by an init that may not reap
            return
        time.sleep(0.1)
    os.kill(pid, 9)
    raise AssertionError("child process survived the timeout")
