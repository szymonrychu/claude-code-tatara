#!/usr/bin/env python3
"""Stop hook: opt-in run of the repo `test` task before Claude stops, Claude Code only.

Active only with WORKBENCH_VERIFY_ON_STOP=1. Repos checked: the git toplevel of the event cwd
plus every git worktree under `<cwd>/.worktrees/*/*`, each only when its tree is dirty and a
mise task `test` exists. A failing or timed-out `mise run test` blocks the stop with the output
tail as the reason. `stop_hook_active` (already continuing after a stop hook) is a no-op, so
there is no loop. A helper, not a gate: any internal error goes to stderr and the hook exits
0 with no output.

Timeout per repo: WORKBENCH_VERIFY_TIMEOUT seconds (default 600; non-numeric or <= 0 falls back to
the default), clamped to the remaining total budget of 840 s. Repos left when the budget runs out
block the stop as not verified. A timeout kills the whole process group of `mise run test`.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

TAIL_LINES = 40
MAX_REASON = 3800
DEFAULT_TIMEOUT = 600
TOTAL_BUDGET = 840  # below the 900 s hook timeout in plugin.json
KILL_GRACE = 5


def _killpg(proc, sig):
    try:
        os.killpg(proc.pid, sig)
    except (ProcessLookupError, PermissionError):
        pass


def _run(cmd, cwd, timeout):
    """Return (exit code, combined output); raises TimeoutExpired or OSError.

    The command runs in its own session; on timeout the whole process group is killed.
    """
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        start_new_session=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _killpg(proc, signal.SIGTERM)
        try:
            proc.communicate(timeout=KILL_GRACE)
        except subprocess.TimeoutExpired:
            pass
        _killpg(proc, signal.SIGKILL)
        try:
            proc.communicate(timeout=KILL_GRACE)
        except subprocess.TimeoutExpired:
            pass
        raise
    return proc.returncode, out or ""


def _toplevel(cwd, run):
    code, out = run(["git", "rev-parse", "--show-toplevel"], cwd, 30)
    return out.strip() if code == 0 and out.strip() else None


def _candidates(cwd, run):
    top = _toplevel(cwd, run)
    if top is None:
        return []
    found = [top]
    for wt in sorted(Path(top).glob(".worktrees/*/*")):
        if (wt / ".git").exists() and str(wt) not in found:
            found.append(str(wt))
    return found


def _qualifies(repo, run):
    code, out = run(["git", "status", "--porcelain"], repo, 30)
    if code != 0 or not out.strip():
        return False
    code, out = run(["mise", "tasks", "ls", "--json"], repo, 60)
    if code != 0:
        return False
    try:
        return any(t.get("name") == "test" for t in json.loads(out))
    except (ValueError, AttributeError):
        return False


def _block(repo, text):
    reason = f"{repo}: mise run test {text}"
    return {"decision": "block", "reason": reason[:MAX_REASON]}


def _verify(repo, timeout, run):
    try:
        code, out = run(["mise", "run", "test"], repo, timeout)
    except subprocess.TimeoutExpired:
        return _block(repo, f"timed out after {int(timeout)}s")
    if code == 0:
        return None
    tail = "\n".join(out.splitlines()[-TAIL_LINES:])
    room = MAX_REASON - len(repo) - 60
    return _block(repo, f"failed; last {TAIL_LINES} lines:\n{tail[-room:]}")


def main(stdin_json, env, run=_run, clock=time.monotonic):
    try:
        if env.get("WORKBENCH_VERIFY_ON_STOP") != "1" or stdin_json.get("stop_hook_active"):
            return None
        cwd = stdin_json.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            return None
        try:
            per_repo = int(env.get("WORKBENCH_VERIFY_TIMEOUT", DEFAULT_TIMEOUT))
        except ValueError:
            per_repo = DEFAULT_TIMEOUT
        if per_repo <= 0:
            per_repo = DEFAULT_TIMEOUT
        deadline = clock() + TOTAL_BUDGET
        unverified = []
        for repo in _candidates(cwd, run):
            if not _qualifies(repo, run):
                continue
            remaining = deadline - clock()
            if remaining <= 0:
                unverified.append(repo)
                continue
            result = _verify(repo, min(per_repo, remaining), run)
            if result:
                return result
        if unverified:
            names = ", ".join(unverified)
            reason = f"verification budget of {TOTAL_BUDGET}s exhausted; not verified: {names}"
            return {"decision": "block", "reason": reason[:MAX_REASON]}
        return None
    except Exception as exc:  # fail open: never block on the hook's own error
        print(f"verify-on-stop: {exc}", file=sys.stderr)
        return None


if __name__ == "__main__":
    import os

    try:
        payload = json.load(sys.stdin)
        result = main(payload if isinstance(payload, dict) else {}, os.environ)
    except Exception as exc:
        print(f"verify-on-stop: {exc}", file=sys.stderr)
        result = None
    if result:
        print(json.dumps(result))
