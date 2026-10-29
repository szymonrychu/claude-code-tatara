---
title: orch command name single source
status: todo
repo: agents-orchestrator
value: "the orchestrator's command-name rule lives in one place, so the spec and the parser cannot drift"
files: [src/agents_orchestrator/slash.py, src/agents_orchestrator/spec.py, tests/test_slash.py]
verify: "uv run --frozen pytest tests/test_slash.py tests/test_spec_config.py && mise run lint"
depends_on: [orch-plugins-pin-0-5-1]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 624640
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch command name single source

## Requirement

Scope audit (phase 5 re-audit, .scratchpad/slash-fix-phase5/scope-audit.md), verbatim: "the D2 command-name regex is written twice in agents-orchestrator. Where: `src/agents_orchestrator/spec.py:225` (the `AgentCommand` pattern literal) and `src/agents_orchestrator/slash.py:47` (`_NAME`). Suggested task: build `AgentCommand`'s pattern from the one name constant in `slash.py` instead of a second literal."

Scope (agents-orchestrator, branch slash-commands-from-chat): `slash.py` exposes the D2 name regex once as a public string constant `NAME_PATTERN` (`_NAME` compiles it); `spec.py`'s `AgentCommand` builds its pattern from it (`rf"^(\*|{NAME_PATTERN})$"`), so the literal `[a-zA-Z0-9_][a-zA-Z0-9:_-]*` appears once under `src/`. Behaviour unchanged; a test pins the single source and that `AgentCommand` still accepts `*`, `compact`, `plugin:cmd`, `_x` and rejects `/x`, `a.b`, `-x`.

## Acceptance conditions

- ac1: the D2 name regex literal appears exactly once under src/ [evidence: command:test "$(grep -rn 'a-zA-Z0-9_\]\[a-zA-Z0-9:_-' src | wc -l)" -eq 1]
- ac2: AgentCommand is built from slash.NAME_PATTERN and still accepts "*", "compact", "plugin:cmd", "_x" and rejects "/x", "a.b", "-x" (new) [evidence: test:tests/test_slash.py::test_agent_command_pattern_shares_slash_name]
- ac3: slash and spec suites and lint pass [evidence: command:uv run --frozen pytest tests/test_slash.py tests/test_spec_config.py && mise run lint]

## Files

- `src/agents_orchestrator/slash.py`
- `src/agents_orchestrator/spec.py`
- `tests/test_slash.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
