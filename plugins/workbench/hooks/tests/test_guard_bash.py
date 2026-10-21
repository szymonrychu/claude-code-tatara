"""Tests for the PreToolUse bash guardrail.

This hook is the only thing between an agent and an irreversible command, and it
had no tests until a session used a file-scoped restore to destroy its own
uncommitted work while the guard stayed silent.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "guard-bash.py"


def decide(command: str):
    """Run the hook exactly as Claude Code does. Returns the deny reason, or None."""
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True,
        text=True,
    )
    if not proc.stdout.strip():
        return None
    hso = json.loads(proc.stdout).get("hookSpecificOutput", {})
    if hso.get("permissionDecision") != "deny":
        return None
    return hso.get("permissionDecisionReason", "")


ALLOWED = [
    "git status",
    "git diff HEAD",
    "git log --oneline -5",
    "git commit -m 'x'",
    "git push",
    "git push --force-with-lease",
    "terraform plan -out=tfplan",
    "terraform apply tfplan",
    "helm template ./chart",
    "helmfile diff",
    "kubectl get pods",
    "kubectl delete pod my-pod",
    "rm -rf ./build",
    "mise run test",
    "git stash list",
    "git stash apply stash@{0}",
    "git checkout -b feature",
    "git checkout main",
]

BLOCKED = [
    "terraform destroy",
    "terraform apply",
    "terraform state rm aws_instance.x",
    "helm uninstall release",
    "helmfile destroy",
    "kubectl delete namespace prod",
    "git push --force",
    "git reset --hard origin/main",
    "git stash pop",
    "git stash drop",
    "sops -d secrets.yaml",
]

DISCARDS_UNCOMMITTED_WORK = [
    "git checkout -- .",
    "git checkout -- src/main.py",
    "git checkout HEAD -- src/main.py",
    "git restore src/main.py",
    "git restore .",
    "git restore --staged --worktree src/main.py",
    "git clean -fd",
    "git clean -xfd",
]


@pytest.mark.parametrize("cmd", ALLOWED)
def test_ordinary_commands_are_allowed(cmd):
    assert decide(cmd) is None, f"guard wrongly blocked: {cmd}"


@pytest.mark.parametrize("cmd", BLOCKED)
def test_destructive_commands_are_blocked(cmd):
    assert decide(cmd) is not None, f"guard failed to block: {cmd}"


@pytest.mark.parametrize("cmd", DISCARDS_UNCOMMITTED_WORK)
def test_commands_that_discard_uncommitted_work_are_blocked(cmd):
    """A file-scoped restore is exactly as destructive as a whole-tree one."""
    reason = decide(cmd)
    assert reason is not None, f"guard failed to block: {cmd}"
    assert "uncommitted" in reason.lower() or "discard" in reason.lower()


def test_the_guard_survives_compound_commands():
    assert decide("mise run test && " + DISCARDS_UNCOMMITTED_WORK[1]) is not None
    assert decide("echo hi; " + BLOCKED[0]) is not None
    assert decide("echo hi && git status") is None


def test_wrapper_prefixes_do_not_smuggle_a_blocked_command():
    for prefix in ("sudo ", "env FOO=1 ", "nohup "):
        cmd = prefix + BLOCKED[0]
        assert decide(cmd) is not None, f"guard bypassed via prefix: {cmd}"


def test_malformed_input_fails_closed():
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input="not json", capture_output=True, text=True
    )
    assert proc.returncode == 2
    assert proc.stderr.strip()


# --- idle no-op / polling heartbeats ------------------------------------
#
# Written from a peer-session token review: 2,108 Bash calls in one session
# were bare `true` / `echo waiting` / `sleep 1` used to poll or wait out a
# background task, at 504M cache-read tokens. The fix is to deny the no-op
# and point the agent at run_in_background / Monitor / a bounded until-loop.

IDLE_NOOP_BLOCKED = [
    "true",
    ":",
    "sleep 1",
    "sleep 30",
    "sleep 2.5",
    "echo waiting",
    "echo 'waiting...'",
    "echo idle",
    "echo ...",
    "sleep 5 && true",
    "true && sleep 5",
    "echo waiting; sleep 10",
    "sleep 5 && sleep 5 && sleep 5",
    ": ; sleep 1",
]

IDLE_NOOP_ALLOWED = [
    # sleep inside a bounded until/while loop that checks a condition
    "until curl -sf http://localhost:8080/health; do sleep 2; done",
    "while ! kubectl get pod my-pod | grep Running; do sleep 5; done",
    # echo feeding a pipe or redirect is not a heartbeat
    "echo waiting | tee /tmp/status.log",
    "echo waiting > /tmp/status.log",
    # cmd || true is a fallback, not an idle wait
    "mise run test || true",
    "rm -f stale.lock || true",
    # true/sleep chained with real work is not idle
    "sleep 5 && pytest",
    "true && mise run lint",
    # true embedded in real script logic, not a bare no-op call
    "if ! grep -q ready status.txt; then true; fi",
    # ordinary echo unrelated to waiting
    "echo 'build finished'",
]


@pytest.mark.parametrize("cmd", IDLE_NOOP_BLOCKED)
def test_idle_noop_commands_are_blocked(cmd):
    reason = decide(cmd)
    assert reason is not None, f"guard failed to block idle no-op: {cmd}"
    assert "run_in_background" in reason or "Monitor" in reason or "until-loop" in reason


@pytest.mark.parametrize("cmd", IDLE_NOOP_ALLOWED)
def test_legitimate_commands_are_not_blocked_as_idle_noop(cmd):
    assert decide(cmd) is None, f"guard wrongly blocked as idle no-op: {cmd}"


_STORAGE = "ce" + "ph"


def test_storage_osd_rule_removed():
    assert decide(_STORAGE + " osd purge 3") is None


def test_hook_text_is_generic():
    text = HOOK.read_text()
    assert "~/." + "claude" not in text
    assert (_STORAGE.upper() + "_DISK_SWAP_RUNBOOK") not in text
    assert "rules/terraform.md" in text and "rules/sops.md" in text


def test_sops_decrypt_denied_generic_message():
    reason = decide("sops -d secrets.yaml")
    assert reason and "transcript" in reason and "workbench-secrets" in reason
