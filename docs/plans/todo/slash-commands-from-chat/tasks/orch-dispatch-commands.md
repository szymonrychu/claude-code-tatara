---
title: orch dispatch commands
status: todo
repo: agents-orchestrator
value: "a slash message reaches the wrapper command queue at once, even mid-turn, never as a turn, with a visible outcome"
files: [src/agents_orchestrator/db/queue.py, src/agents_orchestrator/dispatcher/loop.py, src/agents_orchestrator/dispatcher/verify.py, tests/test_dispatcher.py, tests/test_queue_leader_routing.py, tests/test_ambiguous_verify.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py tests/test_slash.py && mise run lint"
depends_on: [orch-session-send-command, orch-wrapper-command-client]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch dispatch commands

## Requirement

Goals (README), verbatim: G1 "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."; G2 "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."; G3 "Sending /reload-plugins (the reported case) no longer hangs the session; a regression test pins it." User decision: "A regression test must pin the reported case: sending '/reload-plugins' from chat never leaves the session busy (wrapper and orchestrator level)." This task is the orchestrator-level pin.

Design D10, verbatim: "`db/queue.py`: `Claim.kind`; a command head picks an agent with `_PICK_COMMAND` (ready, not gone, has a wrapper session, the target or the leader; no `state = 'idle'` and no `free_since` predicate); a command neither needs nor writes the `agents.last_dispatched_at` reservation (my call: a command does not take the orchestrator's turn slot, and a rejected command would otherwise leave `last_dispatched_at > free_since` and starve prose); a command is exempt from the busy-leader hold and the handover hold of `_claim_in_session` but not from backoff (`not_before`) or a gone leader (it waits for the successor) (my call). It may overtake queued prose of its session (intended: "at any moment"). `dispatcher/loop.py:_send` sends kind=command unframed (no `<session-message>`) with `WrapperClient.command(wsid, name, args)`. Outcomes: 202 -> `mark_sent_command` (status `sent`, `wrapper_command_id`); 409 booting|dead and 429 `command_queue_full` -> requeue with `not_before = now() + retry_backoff_base_seconds`, no attempt counted (my call: an immediate requeue would spin on a full wrapper queue); 403 `command_denied` | `command_not_allowed` and 422 -> failed with the wrapper's envelope code as `error` (my call: QueueStrip shows `error`, so the user sees why); 401 -> failed `config_error`; 404/410 -> as a turn (backoff, rebootstrap); an ambiguous send (read timeout, 500, 502) -> failed `ambiguous` (my call: the verifier looks for a turn carrying `orch_message_id`, a command has none, so verifying would resend it blindly); a stale `dispatching` command row is failed `ambiguous` by the verifier instead of resent. Only the user's Retry resends a failed command."

Scope (agents-orchestrator): `db/queue.py` (`Claim.kind`, `_PICK_COMMAND`, the kind-aware pick, the hold exemption in `_claim_in_session`, no reservation write for commands, `mark_sent_command`, a requeue with `not_before`), `dispatcher/loop.py` (`_send` kind=command branch and outcome mapping; `slash.parse` gives name and args from the stored text), `dispatcher/verify.py` (a verifying kind=command row fails `ambiguous` at once), `README.md` (`## API` messages: slash text, kind, the failure codes; `## Architecture` notes the command dispatch), `MEMORY.md` (dated entry with the why of the no-reservation and hold-exemption rulings).

## Acceptance conditions

- ac1: (Docker: CI or a Docker host) regression pin: POST message "/reload-plugins" reaches the fake wrapper as POST /commands {name: reload-plugins, args: ""} and never as POST /turns, the message ends sent with wrapper_command_id, and a following prose message is dispatched as a turn to the same agent and completes (new) [evidence: test:tests/test_dispatcher.py::test_reload_plugins_from_chat_runs_as_command_and_frees_agent]
- ac2: (Docker) a superleader command message is sent unframed to /commands; a prose session message is still framed (new) [evidence: test:tests/test_dispatcher.py::test_command_message_sent_unframed_to_commands]
- ac3: (Docker) a command message is dispatched while its agent is busy with a turn (new) [evidence: test:tests/test_dispatcher.py::test_command_message_dispatched_while_agent_busy]
- ac4: (Docker) 429 command_queue_full and 409 booting requeue with not_before about retry_backoff_base_seconds ahead and no attempt counted (new) [evidence: test:tests/test_dispatcher.py::test_command_busy_requeues_with_backoff]
- ac5: (Docker) 403 command_denied fails the message with error command_denied; 422 invalid_command fails it with error invalid_command (new) [evidence: test:tests/test_dispatcher.py::test_command_refusal_fails_with_wrapper_code]
- ac6: (Docker) an ambiguous command send fails ambiguous and never enters verifying (new) [evidence: test:tests/test_dispatcher.py::test_command_ambiguous_fails_without_verify]
- ac7: (Docker) a command claim writes no last_dispatched_at; after a refused command the idle agent still takes the next prose message (new) [evidence: test:tests/test_queue_leader_routing.py::test_command_claim_keeps_reservation_free]
- ac8: (Docker) an untargeted command head overtakes queued prose held for a busy leader and for a pending handover, waits on backoff and on a gone leader, and prose order is unchanged (new) [evidence: test:tests/test_queue_leader_routing.py::test_command_skips_leader_holds]
- ac9: (Docker) a stale dispatching command row is failed ambiguous by the verifier, never resent (new) [evidence: test:tests/test_ambiguous_verify.py::test_stale_command_row_fails_ambiguous]
- ac10: MEMORY.md records the command dispatch rulings with the date [evidence: command:grep -q "2026-10-2[0-9].*command" MEMORY.md]
- ac11: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py tests/test_slash.py && mise run lint]

## Files

- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `src/agents_orchestrator/dispatcher/verify.py`
- `tests/test_dispatcher.py`
- `tests/test_queue_leader_routing.py`
- `tests/test_ambiguous_verify.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- `Claim.kind: str`; `queue.mark_sent_command(conn, id, wrapper_command_id) -> bool`; a guarded requeue with `not_before` (for example `queue.requeue_later(conn, id, seconds) -> bool`).
- `messages.error` values for commands: `command_denied`, `command_not_allowed`, `invalid_command`, `ambiguous`, `config_error`.

## Expected outcome

A slash message from the chat or a superleader is delivered to the target's wrapper command queue at once, even mid-turn, and never as a turn; its delivery outcome is visible on the message.

## Steps

- Red: add the nine Docker tests (ac1-ac9); on a Docker host run `uv run --frozen pytest tests/test_dispatcher.py tests/test_queue_leader_routing.py tests/test_ambiguous_verify.py`: they fail. In this container only ac11 runs.
- Green: queue, dispatcher, verifier, README, MEMORY.md; run the task's verify: passes. Quote the summary line; the Docker legs run in CI.

## Notes

- Rulings and their pins (retro proposal): no reservation write (ac7), hold exemption and its limits (ac8), backoff requeue (ac4), wrapper code as error (ac5), ambiguous fails (ac6, ac9).
- Every status change stays a guarded UPDATE (`WHERE status = 'dispatching'`); one writer per transition.
- `release_agent` is skipped for command claims (nothing was reserved).
- Depends on orch-message-kind (the `kind` column) and orch-wrapper-command-client (`command()` outcomes, the fake's command route).
