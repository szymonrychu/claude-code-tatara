---
title: statusline absolute command
status: done
repo: claude-code-wrapper
value: "the context gauge and chained statusline work in pods where ccw is not on PATH, without leaking the hook token"
files: [src/claude_code_wrapper/statusline.py, src/claude_code_wrapper/bootstrap/settings.py, tests/test_statusline_relay.py]
verify: "uv run pytest tests/test_statusline_relay.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [idle-since-in-snapshot, user-message-event, history-before-seq-and-types, peer-mesh-view-route, statusline-relay, context-in-snapshot-and-sse, on-start-instance-hook]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/claude-code-wrapper-orchestr-statusline-absolute-command/claude-code-wrapper
branch: HEAD
verified_head: 8cad3c4dd7df7e779d784cd4edefe50c23179382
run: claude-code-wrapper-orchestr
provides: []
acs_for_audit: []
process_gaps: ["The README-only diff command in the prompt covers 28 lines; the code and test changes sit in sibling commit 976c968 and were reviewed via the full merge-base diff (src and tests)."]
fork_point: d41dd76a6710d1ffe7121ad1817075acdd6ec3ce
---

# statusline absolute command

## Requirement

Review finding (medium): statusline.py STATUSLINE_COMMAND is the bare 'ccw statusline' resolved through PATH, while the hook relay uses an absolute path (bootstrap/settings.py default_relay_command, :50-60) because the venv's ccw may not be on PATH. Resolve the statusline command the same way (absolute path to the running ccw), and make _install_statusline recognise an already-installed relay by basename so reinstalls stay idempotent. Security finding (low): statusline.run_chain runs the chained user command with shell=True and the inherited environment, so it receives CCW_HOOK_TOKEN; pass an env with CCW_HOOK_TOKEN removed. Update tests that pin the bare string.

## Acceptance conditions

- AC1: the installed statusLine command is the absolute ccw path from the same resolver as the hook relay [evidence: test:tests/test_statusline_relay.py::test_statusline_command_is_absolute]
- AC2: an installed relay is recognised by basename and not installed twice [evidence: test:tests/test_statusline_relay.py::test_install_statusline_idempotent_by_basename]
- AC3: the chained user command does not receive CCW_HOOK_TOKEN [evidence: test:tests/test_statusline_relay.py::test_chain_env_drops_hook_token]

## Files

- `src/claude_code_wrapper/statusline.py`
- `src/claude_code_wrapper/bootstrap/settings.py`
- `tests/test_statusline_relay.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement above holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
