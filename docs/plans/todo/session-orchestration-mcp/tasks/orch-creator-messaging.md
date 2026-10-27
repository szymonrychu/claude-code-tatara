---
title: orch creator messaging
status: todo
repo: agents-orchestrator
value: an orchestrating session and the sessions it created can talk to each other
files: [src/agents_orchestrator/api/agent.py, README.md, MEMORY.md, tests/test_agent_session_messaging.py]
verify: "uv run --frozen pytest tests/test_agent_session_messaging.py && mise run lint"
depends_on: [orch-orchestration-sessions]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch creator messaging

## Requirement

Design D10, verbatim: "The `session_send` rule gains \"or one session created the other\", so replies can come back to a non-superleader owner (Q4, pending the gate)."

Open question Q4 (pending; the plan follows the recommended answer), verbatim: "A session and the sessions it created may message each other even when neither is a superleader?" recommended "yes".

Scope (agents-orchestrator): `api/agent.py:session_send` (the target_not_superleader check also passes when the caller created the target or the target created the caller), README (the `session_send` rule), `MEMORY.md` (dated entry for the epic's decisions: the flag, the user-turn gate, ownership, the schedule relay).

## Acceptance conditions

- ac1: a non-superleader session may send to a session it created and that session may send back, while two unrelated non-superleader sessions are still refused target_not_superleader [evidence: test:tests/test_agent_session_messaging.py::test_creator_and_created_may_message]
- ac2: every other session_send refusal and limit is unchanged [evidence: command:uv run --frozen pytest tests/test_agent_session_messaging.py]
- ac3: the README session_send rule says one session created the other is enough [evidence: command:grep -q "one session created the other" README.md]
- ac4: MEMORY.md records the session orchestration decisions, dated [evidence: command:grep -q "session_orchestration" MEMORY.md]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_agent_session_messaging.py && mise run lint]

## Files

- `src/agents_orchestrator/api/agent.py`
- `README.md`
- `MEMORY.md`
- `tests/test_agent_session_messaging.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
