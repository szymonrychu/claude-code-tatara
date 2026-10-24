"""Shared helpers for the worktree hooks (commit guard, verification recorder).

Kept dependency-free: hooks import it by putting their own directory on
sys.path, because hook scripts have hyphens in their names and run as scripts.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "lib"))
import workbench  # noqa: E402

# Path segments that mark a directory as a worktree handed to an agent.
WORKTREE_MARKERS = tuple(workbench.worktree_markers())

GIT_TIMEOUT_SECONDS = 10

RECORD_NAME = "workbench-verify.json"

# A leading `cd <path>` followed by a command separator. The path may be single-
# or double-quoted; the separator is `&&`, `;`, `||` or a newline.
_LEADING_CD = re.compile(
    r"""^\s*cd[ \t]+(?:'([^']*)'|"([^"]*)"|([^\s;&|'"]+))[ \t]*(?:&&|;|\|\||\n)"""
)


# The capture-and-cap wrapper bash-output-filter.py puts around a command. The
# format lives here so the hook that writes it and the code that unwraps it
# cannot drift apart. The group closes on its own line so a trailing `;`,
# `# comment` or heredoc terminator in the command cannot swallow the brace.
# The spill file lives in `<main checkout>/.logs/bash-output/`; only when no
# main checkout is found does it fall back to `${TMPDIR:-/tmp}`. The directory
# is the only variable part of the head.
SPILL_NAME = "bash-output-filter.XXXXXX"
SPILL_SUBDIR = "bash-output"
_TMPDIR_TEMPLATE = '"${TMPDIR:-/tmp}/' + SPILL_NAME + '"'
WRAP_HEAD_PREFIX = 'TMP_OUT="$(mktemp '
WRAP_HEAD_SUFFIX = ')"; { '
WRAP_TAIL = (
    '\n} >"$TMP_OUT" 2>&1; '
    "TMP_OUT_STATUS=$?; "
    'TMP_OUT_SIZE=$(wc -c < "$TMP_OUT" | tr -d " "); '
    'if [ "$TMP_OUT_SIZE" -gt 8000 ]; then '
    'head -c @CAP@ "$TMP_OUT"; '
    'printf "\\n... [output capped at ~8k chars; full log: %s]...\\n" "$TMP_OUT"; '
    'tail -c @CAP@ "$TMP_OUT"; '
    "else "
    'cat "$TMP_OUT"; rm -f "$TMP_OUT"; '
    "fi; "
    # `(exit N)` sets $? without ending the caller's shell.
    '(exit "$TMP_OUT_STATUS")'
)

_WRAP_HEAD_RE = re.compile(
    re.escape(WRAP_HEAD_PREFIX)
    + r"(?:"
    + re.escape(_TMPDIR_TEMPLATE)
    + r"|[^\n]*?/"
    + re.escape(SPILL_NAME)
    + r"'?)"
    + re.escape(WRAP_HEAD_SUFFIX)
)


def spill_dir(start: str | None = None) -> str | None:
    """`<main checkout>/.logs/bash-output` (created), or None without a main checkout."""
    logs = workbench.logs_dir(Path(start) if start else None)
    if logs is None:
        return None
    d = logs / SPILL_SUBDIR
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return str(d)


def wrap_output_filter(command: str, cap_chars: int, spill_dir: str | None = None) -> str:
    """`command` under bash-output-filter's capture-and-cap wrapper.

    The spill file goes to `spill_dir`, or `${TMPDIR:-/tmp}` when it is None.
    """
    if spill_dir is None:
        template = _TMPDIR_TEMPLATE
    else:
        template = shlex.quote(f"{spill_dir}/{SPILL_NAME}")
    head = WRAP_HEAD_PREFIX + template + WRAP_HEAD_SUFFIX
    return head + command + WRAP_TAIL.replace("@CAP@", str(cap_chars))


_WRAP_TAIL_RE = re.compile(re.escape(WRAP_TAIL).replace("@CAP@", r"\d+"))


def unwrap_output_filter(command: str) -> str:
    """The original command inside bash-output-filter's wrapper, else `command`.

    Recognises the wrapper for any spill directory. The kubectl/stern variant
    only inserts `--tail`, so it has no wrapper.
    """
    head = _WRAP_HEAD_RE.match(command)
    if head is None:
        return command
    match = _WRAP_TAIL_RE.search(command, head.end())
    if match is None or match.end() != len(command):
        return command
    return command[head.end() : match.start()]


def is_agent_worktree(path: str) -> bool:
    """True for a worktree an agent was dispatched into, not the main checkout."""
    posix = Path(path).as_posix()
    return any(marker in posix + "/" for marker in WORKTREE_MARKERS)


def _split_leading_cd(command: str) -> tuple[str | None, str]:
    match = _LEADING_CD.match(command)
    if not match:
        return None, command
    target = next(g for g in match.groups() if g is not None)
    if len(target) > 1:
        target = target.rstrip("/") or "/"
    return target, command[match.end() :].strip()


def leading_cd_target(command: str) -> str | None:
    """The path of a leading `cd <path>` followed by a separator, else None."""
    return _split_leading_cd(command)[0]


def strip_leading_cd(command: str) -> str:
    """The command with a leading `cd <path> <separator>` segment removed."""
    return _split_leading_cd(command)[1]


def _git(path: str, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-C", path, *args],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def git_dir(path: str) -> str | None:
    out = _git(path, "rev-parse", "--absolute-git-dir")
    return out.strip() or None if out is not None else None


def head(path: str) -> str | None:
    out = _git(path, "rev-parse", "HEAD")
    return out.strip() or None if out is not None else None


def dirty_files(path: str) -> list[str]:
    """Porcelain entries for the worktree, or [] when this is not a usable repo."""
    out = _git(path, "status", "--porcelain")
    if out is None:
        return []
    return [line for line in out.splitlines() if line.strip()]


def record_path(path: str) -> Path | None:
    gd = git_dir(path)
    return Path(gd) / RECORD_NAME if gd else None


def read_record(path: str) -> dict | None:
    rp = record_path(path)
    if rp is None:
        return None
    try:
        data = json.loads(rp.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None
