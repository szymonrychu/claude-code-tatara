---
title: helmfile-smoke-helpers
status: todo
repo: agents-helmfile
value: one copy of the smoke helpers and a quiet chat-smoke
files: [scripts/chat-smoke.sh, scripts/smoke.sh, scripts/lib/smoke-common.sh, tests/test_chat_smoke_script.py, tests/test_smoke_script.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py tests/test_chat_smoke_script.py"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile-smoke-helpers

## Requirement

Epic review findings for agents-helmfile, my call to fix:
1. `scripts/chat-smoke.sh:93`: `< "$d/cmdline" 2> /dev/null` opens the file before stderr is silenced, so a process that exits during the scan prints `/proc/<pid>/cmdline: No such file or directory` (seen live 2026-10-28). Put the stderr redirect first; a test runs the scan against a vanished pid and asserts no output on stderr.
2. Scope audit duplicate (.scratchpad/matrix/review/scope-audit.md): the in-pod `agent_py` snippet and `agent_call`, plus the log/fail/cleanup and stale port-forward helpers, are copied between `scripts/chat-smoke.sh` and `scripts/smoke.sh`. Move them into one sourced script (for example `scripts/lib/smoke-common.sh`) used by both, without changing either script's output or behaviour (their existing tests stay green unchanged).
Test first.

## Acceptance conditions

- AC1: the stale port-forward scan prints nothing on stderr for a vanished pid [evidence: test:tests/test_chat_smoke_script.py::test_stale_scan_silent_for_vanished_pid]
- AC2: chat-smoke.sh and smoke.sh source one shared helper file and define no copy of agent_call [evidence: test:tests/test_smoke_script.py::test_smoke_scripts_share_helpers]
- AC3: the existing smoke and chat-smoke script tests pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py tests/test_chat_smoke_script.py]

## Files

- `scripts/chat-smoke.sh`
- `scripts/smoke.sh`
- `scripts/lib/smoke-common.sh`
- `tests/test_chat_smoke_script.py`
- `tests/test_smoke_script.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
