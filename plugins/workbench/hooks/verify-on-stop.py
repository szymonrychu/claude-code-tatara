#!/usr/bin/env python3
"""Stop hook: opt-in run of the repo `test` task before Claude stops, Claude Code only.

Active only with WORKBENCH_VERIFY_ON_STOP=1. Repos checked: the git toplevel of the event cwd
plus every git worktree under `<cwd>/.worktrees/*/*`, each only when its tree is dirty and a
mise task `test` exists. A failing or timed-out `mise run test` blocks the stop with the output
tail as the reason. `stop_hook_active` (already continuing after a stop hook) is a no-op, so
there is no loop. A helper, not a gate: any internal error goes to stderr and the hook exits
0 with no output.

Timeout per repo: WORKBENCH_VERIFY_TIMEOUT seconds (default 600).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TAIL_LINES = 40
MAX_REASON = 3800
DEFAULT_TIMEOUT = 600


def _run(cmd, cwd, timeout):
    """Return (exit code, combined output); raises TimeoutExpired or OSError."""
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, errors="replace", timeout=timeout
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _toplevel(cwd, run):
    code, out = run(["git", "rev-parse", "--show-toplevel"], cwd, 30)
    return out.strip() if code == 0 and out.strip() else None


def _candidates(cwd, run):
    top = _toplevel(cwd, run)
    if top is None:
        return []
    found = [top]
    for wt in sorted(Path(cwd).glob(".worktrees/*/*")):
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
        return _block(repo, f"timed out after {timeout}s")
    if code == 0:
        return None
    tail = "\n".join(out.splitlines()[-TAIL_LINES:])
    room = MAX_REASON - len(repo) - 60
    return _block(repo, f"failed; last {TAIL_LINES} lines:\n{tail[-room:]}")


def main(stdin_json, env, run=_run):
    try:
        if env.get("WORKBENCH_VERIFY_ON_STOP") != "1" or stdin_json.get("stop_hook_active"):
            return None
        cwd = stdin_json.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            return None
        try:
            timeout = int(env.get("WORKBENCH_VERIFY_TIMEOUT", DEFAULT_TIMEOUT))
        except ValueError:
            timeout = DEFAULT_TIMEOUT
        for repo in _candidates(cwd, run):
            if _qualifies(repo, run):
                result = _verify(repo, timeout, run)
                if result:
                    return result
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
