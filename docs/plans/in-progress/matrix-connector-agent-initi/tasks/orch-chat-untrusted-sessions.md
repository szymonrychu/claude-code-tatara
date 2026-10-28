---
title: orch-chat-untrusted-sessions
status: todo
repo: agents-orchestrator
value: webhook and schedule sessions cannot be steered into messaging the user
files: [src/agents_orchestrator/k8s/on_start.py, src/agents_orchestrator/api/chat.py, tests/test_on_start.py, tests/test_agent_chat.py, tests/e2e/test_e2e_kind.py, MEMORY.md]
verify: uv run pytest tests/test_on_start.py tests/test_agent_chat.py -q
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 965826
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch-chat-untrusted-sessions

## Requirement

Epic review findings for agents-orchestrator, my call to fix:
1. Security MEDIUM 1 (.scratchpad/matrix/review/security.md): `k8s/on_start.py` (about line 41) grants CHAT_TOOLS to every session, so a webhook or schedule session that reads attacker-controlled PR, issue or alert text can be prompt-injected into `chat_send` and message the real Messenger user wherever `agents_may_initiate` is on. Sessions started by the trigger services agents-webhook and agents-schedule (identified by the orchestrator's own record of who created the session, for example the service token name; read how sessions record their creator first, and if no reliable record exists, stop and return that as a question) get no chat tools rendered in onStart, and the chat relay (`api/chat.py`) refuses their calls with 403 and a distinct error code. Every other session keeps today's behaviour (user and connector sessions, including mx-34).
2. Review Consider (.scratchpad/matrix/review/orch-plugins.md): `tests/e2e/test_e2e_kind.py` (about line 292) compares the allow list to `orchestrator_allow()`, i.e. the code to itself; restore a literal expected list there.
Test first. Record the rule in MEMORY.md with the date and why.

## Acceptance conditions

- AC1: a session created by the agents-webhook or agents-schedule service gets no chat tools in its rendered onStart config [evidence: test:tests/test_on_start.py::test_trigger_service_sessions_get_no_chat_tools]
- AC2: the chat relay refuses a call from a trigger-service session with 403 and its own error code [evidence: test:tests/test_agent_chat.py::test_trigger_service_session_refused]
- AC3: a user-created session still gets the chat tools and may call the relay [evidence: test:tests/test_agent_chat.py::test_user_session_may_use_chat]
- AC4: the kind e2e asserts a literal allow list [evidence: command:! grep -n "orchestrator_allow()" tests/e2e/test_e2e_kind.py]
- AC5: MEMORY.md records the rule [evidence: command:grep -q "trigger-service sessions" MEMORY.md]

## Files

- `src/agents_orchestrator/k8s/on_start.py`
- `src/agents_orchestrator/api/chat.py`
- `tests/test_on_start.py`
- `tests/test_agent_chat.py`
- `tests/e2e/test_e2e_kind.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Read every file the step touches, write the AC tests first and run the task verify: the new tests fail for the expected reason.
- Implement the smallest change that passes, rerun the verify and `mise run lint`: green.
- Commit, push, open or update the PR and quote its CI result per job.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
