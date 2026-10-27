---
title: orch command turn link
status: todo
repo: agents-orchestrator
value: "a superleader's command that becomes a turn keeps its hop count, so the session-message hop limit still holds"
files: [src/agents_orchestrator/db/queue.py, src/agents_orchestrator/ingester/loop.py, tests/test_ingester.py, tests/test_agent_session_messaging.py, MEMORY.md]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint"
depends_on: [orch-dispatch-commands]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch command turn link

## Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."

Interrogate item 9 (interrogate.md), verbatim: "Hop guard for promoted prompt commands (B, C). A command message stores no `turn_id`, so sends from its promoted turn restart at hop 1 and bypass session_message_max_hops. Set messages.turn_id on `command_completed` with `result=turn` through a status-guarded update by the single writer."

Design D10, verbatim (the hop-guard part): "Hop guard (my call, interrogate item 9): a command message stores no `turn_id` at 202, so sends from its promoted turn (D8) would restart at hop 1 and bypass `session_message_max_hops`. `queue.link_command_turn(conn, wrapper_command_id, turn_id)` is the one writer of the transition "sent command, no turn -> linked turn": `UPDATE messages SET turn_id = ... WHERE kind = 'command' AND status = 'sent' AND wrapper_command_id = ... AND turn_id IS NULL`, called by the ingester when it stores a `command_completed` envelope whose record has `result = 'turn'` and a `turn_id`. For the reverse arrival order (the event stored before the dispatcher's 202 handling), `mark_sent_command` takes that `turn_id` from the stored `command_completed` event in its own guarded update (`dispatching -> sent`). `queue.turn_hop` then finds the command message of the promoted turn, so a send from it counts that message's hop plus one; agents-common's run tracker also sees the promoted turn's completion on the message."

Scope (agents-orchestrator):
- `src/agents_orchestrator/db/queue.py`: `link_command_turn(conn, wrapper_command_id, turn_id) -> bool` (the guarded UPDATE above); `mark_sent_command` (from task orch-dispatch-commands) also sets `turn_id` from an already stored `command_completed` event of that command id with `result = 'turn'`, in the same guarded `dispatching -> sent` update.
- `src/agents_orchestrator/ingester/loop.py`: `_project` calls `queue.link_command_turn` for a `command_completed` envelope whose `data.record` has `result == "turn"` and a non-empty `turn_id`; every other command event projects nothing new.
- `MEMORY.md`: a dated entry tagged `(slash-commands-from-chat)` naming `link_command_turn`, its single-writer transition and why (the hop guard).

## Acceptance conditions

- ac1: (Docker: CI or a Docker host) storing a command_completed envelope whose record has result turn and a turn_id sets turn_id on the sent command message with that wrapper_command_id; result ok links nothing; a second event never overwrites a set turn_id (new) [evidence: test:tests/test_ingester.py::test_command_completed_turn_links_message]
- ac2: (Docker) when the command_completed event is stored before mark_sent_command runs, mark_sent_command sets turn_id in the same guarded update (new) [evidence: test:tests/test_ingester.py::test_command_turn_linked_when_event_precedes_sent]
- ac3: (Docker) a superleader's "/x" (hop 1) promoted to a turn on the target: a session_send from that turn by the target's leader is stored with hop 2, and with session_message_max_hops 1 it is refused hop_limit (new) [evidence: test:tests/test_agent_session_messaging.py::test_promoted_command_turn_keeps_hop_count]
- ac4: MEMORY.md records the link_command_turn transition under this epic's tag [evidence: command:grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\)" MEMORY.md | grep -q "link_command_turn"]
- ac5: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

## Files

- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/ingester/loop.py`
- `tests/test_ingester.py`
- `tests/test_agent_session_messaging.py`
- `MEMORY.md`

## Interfaces

- `queue.link_command_turn(conn, wrapper_command_id: str, turn_id: str) -> bool`: `UPDATE messages SET turn_id = %s WHERE kind = 'command' AND status = 'sent' AND wrapper_command_id = %s AND turn_id IS NULL`.
- `queue.mark_sent_command(conn, id, wrapper_command_id) -> bool` (task orch-dispatch-commands) also writes `turn_id` from a stored `command_completed` event of that command id with `result = 'turn'`.
- Ingester `_project`: `command_completed` with `data.record.result == "turn"` and a `turn_id` -> `link_command_turn`.

## Expected outcome

A command message whose prompt command became a turn carries that turn id, so a session message sent from the promoted turn counts the right hop and the hop limit holds; the message's turn also shows its completion to API readers such as agents-common.

## Steps

- Red: add ac1-ac3; on a Docker host run `uv run --frozen pytest tests/test_ingester.py tests/test_agent_session_messaging.py`: they fail (turn_id stays null, hop 1). In this container only ac5 runs.
- Green: queue.py, ingester/loop.py, MEMORY.md; run the task's verify: passes. Quote the summary line; the Docker legs run in CI.

## Notes

- One writer per transition (design Constraints): `link_command_turn` for sent -> linked, `mark_sent_command` for dispatching -> sent; both guarded (`turn_id IS NULL`).
- If a layering test forbids the ingester importing `db.queue`, return that as a question instead of moving the write elsewhere.
- The ingester stores every envelope first (`insert_events`); the link runs in the same projection transaction.
- Depends on orch-dispatch-commands (`kind`, `wrapper_command_id`, `mark_sent_command`).
