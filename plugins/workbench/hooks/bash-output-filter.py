#!/usr/bin/env python3
"""PreToolUse hook: cap noisy Bash output (test runs, logs) before it enters context.

Rewrites matched commands to run under a capture-and-cap wrapper: full output
goes to a spill file under `<main checkout>/.logs/bash-output/` (the gitignored
.logs of the workbench root; `$TMPDIR` only when no main checkout is found), and
only a head+tail slice (~8k chars) is printed, with the spill file's path so nothing
is actually lost. The wrapped
command's own exit code is preserved exactly (`$?` is captured right after it
runs, not derived from a `| tail` pipeline) - a failing test run must still
fail the Bash tool call.

The test-runner match happens on the command with any leading `cd <dir> &&`/
`cd <dir>;` prefix(es) stripped first, so `cd <worktree> && mise run test ...`
- the shape every implementer agent actually runs - matches, not only a
command that starts with the runner itself.

For a bare pytest invocation (no further shell chaining after it) `-q -rfE
--no-header --disable-warnings` is appended, so pytest's own output is
failures/errors-only; a `mise run test*`/`suite-lock.sh -- mise run test*`
task is never touched, since that would change what the task actually runs.

Skips commands that already manage their output (pipe/redirect present).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import worktree_lib as wl  # noqa: E402

NOISY = re.compile(
    r"^\s*(?:"
    r"go test\b"
    r"|pytest\b|python3? -m pytest\b|uv run pytest\b"
    r"|npm (?:run )?test\b|yarn test\b|pnpm test\b"
    r"|mise run test\b|mise run lint\b"
    r"|suite-lock\.sh\b.*mise run test\b"
    r"|golangci-lint run\b"
    r"|kubectl logs\b|stern\b"
    r")"
)
ALREADY_MANAGED = re.compile(r"\||>|--tail|-f\b|--follow\b")

# Flags that mean a `kubectl logs`/`stern` invocation already manages its own
# tail/follow behaviour. Checked only within that invocation's own segment of
# a chain (see `find_top_level_chain_break`), never across the whole command
# string, so a `| grep ...` or `&& next-cmd` after it is never mistaken for
# the kubectl call itself already having `--tail`/`-f`.
KUBECTL_ALREADY_MANAGED = re.compile(r"--tail|-f\b|--follow\b")

# A leading `cd <dir> &&` / `cd <dir>;` is not part of the test runner
# invocation itself - strip it (possibly repeated) before matching NOISY, but
# keep it verbatim to re-prepend so the command still actually `cd`s.
LEADING_CD = re.compile(r"""^\s*cd\s+(?:"[^"]*"|'[^']*'|\S+)\s*(?:&&|;)\s*""")

# Only these are a single, unchained pytest invocation - safe to append
# failures-only flags to. Anything chained with && / ; / | / || after the
# pytest call is left alone: appending at the tail would land after the
# wrong command.
BARE_PYTEST = re.compile(r"^\s*(?:pytest|python3?\s+-m\s+pytest|uv run pytest)\b")
# Also refuse on a newline, heredoc/redirect `<`, `&` or a `#` comment: the
# flags would land after a heredoc terminator or inside a comment.
SHELL_CHAIN = re.compile(r"&&|\|\||;|\||\n|<|&|#")

# A trailing lone `&` backgrounds the command; wrapping it would capture
# nothing and delete the spill file the background job is still writing.
BACKGROUNDED = re.compile(r"(?<!&)&\s*$")

# --disable-warnings hides the summary only; `-p no:warnings` would unload the
# plugin that applies `filterwarnings = error` and change test outcomes.
PYTEST_FAILURES_ONLY_FLAGS = "-q -rfE --no-header --disable-warnings"

CAP_CHARS = 4000  # head + tail => ~8k chars total


def split_cd_prefix(cmd: str):
    prefix = ""
    rest = cmd
    while True:
        m = LEADING_CD.match(rest)
        if not m:
            return prefix, rest
        prefix += m.group(0)
        rest = rest[m.end() :]


def is_simple_command(s: str) -> bool:
    """True only for a single simple command: no unquoted `;`, `&`, `|`, newline,
    `<`, `>` (covers `&&`, `||`, `<(`, `>(`, redirections), and no `$(` or
    backtick anywhere outside single quotes (they expand inside double quotes)."""
    quote = None
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if quote == "'":
            if c == "'":
                quote = None
        elif c == "\\" and i + 1 < n:
            i += 1
        elif c == "`" or (c == "$" and s[i + 1 : i + 2] in ("(", "'", '"')):
            # `$'...'` / `$"..."` have escape rules this scanner does not model
            # (`\'` does not close `$'`), so refuse them outright.
            return False
        elif quote == '"':
            if c == '"':
                quote = None
        elif c in ("'", '"'):
            quote = c
        elif c in ";&|\n<>":
            return False
        i += 1
    return quote is None


def is_auto_allowable(cmd: str) -> bool:
    """A command may be auto-allowed only if it is a (possibly `cd`-prefixed)
    single simple command; the cd prefix's own separators are the only
    operators permitted."""
    prefix, rest = split_cd_prefix(cmd)
    if not is_simple_command(rest):
        return False
    pos = 0
    while pos < len(prefix):
        m = LEADING_CD.match(prefix[pos:])
        seg = re.sub(r"\s*(?:&&|;)\s*$", "", m.group(0))
        if not is_simple_command(seg):
            return False
        pos += m.end()
    return True


def find_top_level_chain_break(s: str) -> int:
    """Return the index in `s` of the first top-level `&&`, `||`, `;`, `|` or
    newline - i.e. the end of the first command in a chain/pipeline - honoring
    single/double quotes so an operator character inside a quoted arg is never
    mistaken for a chain break. Returns len(s) if the whole string is one
    command."""
    i = 0
    n = len(s)
    quote = None
    while i < n:
        c = s[i]
        if quote:
            if c == "\\" and quote == '"' and i + 1 < n:
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in ("'", '"'):
            quote = c
            i += 1
            continue
        if c == "\\" and i + 1 < n:
            i += 2
            continue
        if c in (";", "\n", "&", "|"):
            return i
        i += 1
    return n


def build_kubectl_tail_cmd(cmd: str) -> str | None:
    """Insert `--tail=200` right after the `kubectl logs`/`stern` invocation
    itself, wherever it sits ahead of a chain/pipe - never at the tail of the
    whole command string. Returns None if that invocation already has its
    own --tail/-f/--follow."""
    prefix, rest = split_cd_prefix(cmd)
    end = find_top_level_chain_break(rest)
    invocation, remainder = rest[:end], rest[end:]

    if KUBECTL_ALREADY_MANAGED.search(invocation):
        return None

    new_invocation = invocation.rstrip() + " --tail=200"
    if remainder:
        return prefix + new_invocation + " " + remainder.lstrip()
    return prefix + new_invocation


def build_new_cmd(cmd: str, cwd: str | None = None) -> str:
    prefix, rest = split_cd_prefix(cmd)

    if BARE_PYTEST.match(rest) and not SHELL_CHAIN.search(rest):
        rest = rest.rstrip() + " " + PYTEST_FAILURES_ONLY_FLAGS

    full_cmd = prefix + rest

    # Capture full output to a spill file first (never a live pipe into a
    # head/tail reader - that reader can close early and SIGPIPE the writer,
    # corrupting the exit code pipefail would report). Read the exit code
    # right after the wrapped command finishes, then decide head+tail vs cat
    # from the file on disk.
    return wl.wrap_output_filter(full_cmd, CAP_CHARS, wl.spill_dir(cwd))


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd = data.get("tool_input", {}).get("command", "")
    if not cmd:
        sys.exit(0)

    _, rest = split_cd_prefix(cmd)
    if not NOISY.match(rest) or BACKGROUNDED.search(cmd):
        sys.exit(0)  # no rewrite, normal permission flow

    if not is_auto_allowable(cmd):
        sys.exit(0)  # compound/substituted: never auto-approve

    if rest.lstrip().startswith(("kubectl logs", "stern")):
        # `--tail`/`-f` may already be managed further along the chain than
        # ALREADY_MANAGED would see (e.g. a `| grep` after it), so this path
        # checks the kubectl/stern invocation's own segment, not the whole
        # command string.
        new_cmd = build_kubectl_tail_cmd(cmd)
        if new_cmd is None:
            sys.exit(0)
    elif ALREADY_MANAGED.search(cmd):
        sys.exit(0)
    else:
        new_cmd = build_new_cmd(cmd, data.get("cwd") or None)

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "permissionDecisionReason": "output capped by bash-output-filter hook",
                    "updatedInput": {"command": new_cmd},
                }
            }
        )
    )


if __name__ == "__main__":
    main()
