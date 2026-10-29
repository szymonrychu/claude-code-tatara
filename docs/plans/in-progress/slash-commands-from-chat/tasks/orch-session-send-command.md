---
title: orch session send command
status: done
repo: agents-orchestrator
value: "a superleader's slash text to another session becomes a command for that session's leader"
files: [src/agents_orchestrator/api/agent.py, tests/test_agent_session_messaging.py, README.md]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint"
depends_on: [orch-message-kind]
model: sonnet
review: ""
verified_head: 58eeeba799ec0a657e6317e3900e9e71922dfb3a
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: 2
actual_minutes: 2
actual_tokens: 418923
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 278625, review 140298"
---

# orch session send command

## Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text." User request, verbatim: "Both user and superleader can send them."

Design D1, verbatim: "`POST /api/v1/sessions/{id}/messages` (`api/messages.py:post_message`, the chat) and `POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:session_send`, the superleader) both call one new `agents_orchestrator.slash.parse(text) -> tuple[str, str] | None` and store the message with `kind = 'command'` when it matches, else `kind = 'turn'`. On the agent route a match stores `kind = 'command'` only when the sender's own session has `spec.session_messaging` (a superleader); a leader of any other session sending to a superleader (admitted by the D7 check of `api/agent.py:session_send`, `own.spec.session_messaging or target.spec.session_messaging`) keeps `kind = 'turn'`, so its slash text is delivered as framed prose (my call, interrogate item 1: the user asked for "user and superleader")."

Interrogate item 1 (interrogate.md), verbatim: "Non-superleader to superleader command execution (A, B, C). D7 admits any leader sending to a superleader (api/agent.py:412), so with the change a plain worker session runs unframed commands on a superleader. The user asked for "user and superleader". Store `kind='command'` only when the sender's session has `session_messaging`; otherwise the text stays a framed turn. AC with a worker-to-superleader test."

Scope (agents-orchestrator): `api/agent.py:session_send` passes `kind="command"` to `queue.enqueue_message` when `slash.parse(body.text)` matches and `own.spec.session_messaging` is true, else `kind="turn"`; every D7 check (leader only, self send, superleader, deleting, hop, rate, pair budget, queue cap) applies unchanged and in the same order; `README.md` (the superleader messaging section says slash text from a superleader runs as a command on the target's leader, unframed, and slash text from any other session is delivered as a framed message).

## Acceptance conditions

- ac1: (Docker: CI or a Docker host) a superleader's session_send "/compact" stores kind command with sender_session_id, sender_slug and hop (new) [evidence: test:tests/test_agent_session_messaging.py::test_session_send_slash_is_command_kind]
- ac2: (Docker) a leader of a session without session_messaging sending "/compact" to a superleader is accepted 202 and stored kind turn, so the dispatcher frames it as a session message (new) [evidence: test:tests/test_agent_session_messaging.py::test_session_send_slash_from_non_superleader_stays_turn]
- ac3: (Docker) the D7 refusals still apply to slash text in the same order (not_leader, target_not_superleader, rate_limited) (new) [evidence: test:tests/test_agent_session_messaging.py::test_session_send_slash_keeps_refusals]
- ac4: README documents that only a superleader's slash text runs as a command [evidence: command:grep -i "slash" README.md | grep -qi "superleader"]
- ac5: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

## Files

- `src/agents_orchestrator/api/agent.py`
- `tests/test_agent_session_messaging.py`
- `README.md`

## Interfaces

- `POST /agent/v1/sessions/{slug}/messages` unchanged on the wire; the stored message carries `kind`.

## Expected outcome

A superleader's `orchestrator_session_send` with "/x ..." becomes a command message for the target session's leader; the dispatcher (orch-dispatch-commands) sends it unframed.

## Steps

- Red: add ac1-ac3; on a Docker host ac1 fails (kind turn).
- Green: change `session_send` and the README; run the task's verify: passes. Quote the summary line; the Docker legs run in CI.

## Notes

- Reuse `_leads` and the D7 check order (api/agent.py:session_send); the kind decision reads `own.spec.session_messaging` after every refusal check.
- Ruling, pinned by ac2: a non-superleader's slash text stays a framed turn (interrogate item 1).
- Depends on orch-message-kind (`enqueue_message(kind=...)`).

- 2026-10-27 amended: interrogate item 1 (only a superleader's slash text becomes a command; a worker-to-superleader slash text stays a framed turn), design D1 revised

- 2026-10-29 done
