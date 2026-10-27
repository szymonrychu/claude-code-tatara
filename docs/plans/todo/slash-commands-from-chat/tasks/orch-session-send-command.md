---
title: orch session send command
status: todo
repo: agents-orchestrator
value: "a superleader's slash text to another session becomes a command for that session's leader"
files: [src/agents_orchestrator/api/agent.py, tests/test_agent_session_messaging.py, README.md]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint"
depends_on: [orch-message-kind]
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

# orch session send command

## Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text." User request, verbatim: "Both user and superleader can send them."

Design D1, verbatim: "`POST /api/v1/sessions/{id}/messages` (`api/messages.py:post_message`, the chat) and `POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:session_send`, the superleader) both call one new `agents_orchestrator.slash.parse(text) -> tuple[str, str] | None` and store the message with `kind = 'command'` when it matches, else `kind = 'turn'`."

Scope (agents-orchestrator): `api/agent.py:session_send` passes `kind="command"` to `queue.enqueue_message` when `slash.parse(body.text)` matches; every D7 check (leader only, self send, superleader, deleting, hop, rate, pair budget, queue cap) applies unchanged and in the same order; `README.md` (the superleader messaging section says slash text runs as a command on the target's leader, unframed).

## Acceptance conditions

- ac1: (Docker: CI or a Docker host) a superleader's session_send "/compact" stores kind command with sender_session_id, sender_slug and hop (new) [evidence: test:tests/test_agent_session_messaging.py::test_session_send_slash_is_command_kind]
- ac2: (Docker) the D7 refusals still apply to slash text in the same order (not_leader, target_not_superleader, rate_limited) (new) [evidence: test:tests/test_agent_session_messaging.py::test_session_send_slash_keeps_refusals]
- ac3: README documents that slash text from session_send runs as a command [evidence: command:grep -qi "slash" README.md]
- ac4: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

## Files

- `src/agents_orchestrator/api/agent.py`
- `tests/test_agent_session_messaging.py`
- `README.md`

## Interfaces

- `POST /agent/v1/sessions/{slug}/messages` unchanged on the wire; the stored message carries `kind`.

## Expected outcome

A superleader's `orchestrator_session_send` with "/x ..." becomes a command message for the target session's leader; the dispatcher (orch-dispatch-commands) sends it unframed.

## Steps

- Red: add ac1 and ac2; on a Docker host they fail (kind turn).
- Green: change `session_send` and the README; run the task's verify: passes. Quote the summary line; the Docker legs run in CI.

## Notes

- Reuse `_leads` and the D7 check order (api/agent.py:session_send).
- Depends on orch-message-kind (`enqueue_message(kind=...)`).
