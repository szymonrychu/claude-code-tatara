---
title: orch dispatch commands
status: done
repo: agents-orchestrator
value: "a slash message reaches the wrapper command queue at once, even mid-turn, never as a turn, with a visible outcome"
files: [src/agents_orchestrator/db/queue.py, src/agents_orchestrator/dispatcher/loop.py, src/agents_orchestrator/dispatcher/verify.py, tests/test_dispatcher.py, tests/test_queue_leader_routing.py, tests/test_ambiguous_verify.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py tests/test_slash.py && mise run lint"
depends_on: [orch-session-send-command, orch-wrapper-command-client]
model: opus
review: ""
verified_head: d5a0044b2161c6d2c913db6ae3aadd3ef92ccdd0
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: 5
actual_minutes: 24
actual_tokens: 5851628
actual_roles: "impl 21, review 2"
actual_role_tokens: "impl 5591078, review 260550"
---

# orch dispatch commands

## Requirement

Goals (README), verbatim: G1 "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."; G2 "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."; G3 "Sending /reload-plugins (the reported case) no longer hangs the session; a regression test pins it." User decision: "A regression test must pin the reported case: sending '/reload-plugins' from chat never leaves the session busy (wrapper and orchestrator level)." This task is the orchestrator-level pin.

Design D10, verbatim: "`db/queue.py`: `Claim.kind`; a command head picks an agent with `_PICK_COMMAND` (ready, not gone, has a wrapper session, the target or the leader; no `state = 'idle'` and no `free_since` predicate); a command neither needs nor writes the `agents.last_dispatched_at` reservation (my call: a command does not take the orchestrator's turn slot, and a rejected command would otherwise leave `last_dispatched_at > free_since` and starve prose); a command is exempt from the busy-leader hold and the handover hold of `_claim_in_session` but not from backoff (`not_before`) or a gone leader (it waits for the successor) (my call). It may overtake queued prose of its session (intended: "at any moment"). `dispatcher/loop.py:_send` sends kind=command unframed (no `<session-message>`) with `WrapperClient.command(wsid, name, args)`. Outcomes: 202 -> `mark_sent_command` (status `sent`, `wrapper_command_id`); 409 booting|dead and 429 `command_queue_full` -> requeue with `not_before = now() + retry_backoff_base_seconds`, no attempt counted (my call: an immediate requeue would spin on a full wrapper queue); 403 `command_denied` | `command_not_allowed` and 422 -> failed with the wrapper's envelope code as `error` (my call: QueueStrip shows `error`, so the user sees why); 401 -> failed `config_error`; 404/410 -> as a turn (backoff, rebootstrap); an ambiguous send (read timeout, 500, 502) -> failed `ambiguous` (my call: the verifier looks for a turn carrying `orch_message_id`, a command has none, so verifying would resend it blindly); a stale `dispatching` command row is failed `ambiguous` by the verifier instead of resent. Only the user's Retry resends a failed command. [...] The args the dispatcher sends are `slash.parse(text)`'s, so a trailing agents-common run marker is never sent to claude (D2); the stored text keeps it. Per-session order (my call, interrogate item 3): while a session has a `kind = 'command'` row in `dispatching`, no later message of that session (higher id, prose or command) is claimed; the command's 202 puts it in the wrapper's FIFO command queue, so two commands, or a command and later prose, of one session reach the wrapper in id order. Pinned in `tests/test_queue_leader_routing.py`." (The hop-guard part of D10 is task orch-command-turn-link.)

Interrogate item 3 (interrogate.md), verbatim: "Per-session ordering of commands and prose (B, C). Commands write no `last_dispatched_at`, so two commands, or a command and later prose, of one session can be claimed concurrently and arrive out of order. Hold a session's later messages while one of its command rows is `dispatching`; pin in test_queue_leader_routing."

Interrogate item 8, verbatim (the dispatch part): "agents-common runs.py:151 posts `text\n\nmarker`; [...] Strip the ccw marker before classifying [...]; test the marker-suffixed case."

Interrogate item 13, verbatim: "AC evidence that already passes today (A): orch-dispatch-commands ac10 grep matches MEMORY.md:41; web-sync-message-kind ac3 grep matches the current source pin. Replace with assertions specific to the new state."

Scope (agents-orchestrator): `db/queue.py` (`Claim.kind`, `_PICK_COMMAND`, the kind-aware pick, the hold exemption in `_claim_in_session`, the per-session hold behind a `dispatching` command row, no reservation write for commands, `mark_sent_command`, a requeue with `not_before`), `dispatcher/loop.py` (`_send` kind=command branch and outcome mapping; `slash.parse` gives name and args from the stored text, the run marker excluded), `dispatcher/verify.py` (a verifying kind=command row fails `ambiguous` at once), `README.md` (`## API` messages: slash text, kind, the failure codes; `## Architecture` notes the command dispatch and the per-session order), `MEMORY.md` (an entry dated and tagged `(slash-commands-from-chat)` with the why of the no-reservation, hold-exemption and per-session-order rulings, naming `last_dispatched_at`).

## Acceptance conditions

- ac1: (Docker: CI or a Docker host) regression pin: POST message "/reload-plugins" reaches the fake wrapper as POST /commands {name: reload-plugins, args: ""} and never as POST /turns, the message ends sent with wrapper_command_id, and a following prose message is dispatched as a turn to the same agent and completes (new) [evidence: test:tests/test_dispatcher.py::test_reload_plugins_from_chat_runs_as_command_and_frees_agent]
- ac2: (Docker) a superleader command message is sent unframed to /commands; a prose session message is still framed (new) [evidence: test:tests/test_dispatcher.py::test_command_message_sent_unframed_to_commands]
- ac3: (Docker) a command message is dispatched while its agent is busy with a turn (new) [evidence: test:tests/test_dispatcher.py::test_command_message_dispatched_while_agent_busy]
- ac4: (Docker) "/review-pr 12\n\n<!-- agents-webhook:42 -->" is sent as POST /commands {name: review-pr, args: "12"} and the stored text keeps the marker (new) [evidence: test:tests/test_dispatcher.py::test_command_args_exclude_run_marker]
- ac5: (Docker) 429 command_queue_full and 409 booting requeue with not_before about retry_backoff_base_seconds ahead and no attempt counted (new) [evidence: test:tests/test_dispatcher.py::test_command_busy_requeues_with_backoff]
- ac6: (Docker) 403 command_denied fails the message with error command_denied; 422 invalid_command (for example "/ is root", an empty name) fails it with error invalid_command (new) [evidence: test:tests/test_dispatcher.py::test_command_refusal_fails_with_wrapper_code]
- ac7: (Docker) an ambiguous command send fails ambiguous and never enters verifying (new) [evidence: test:tests/test_dispatcher.py::test_command_ambiguous_fails_without_verify]
- ac8: (Docker) a command claim writes no last_dispatched_at; after a refused command the idle agent still takes the next prose message (new) [evidence: test:tests/test_queue_leader_routing.py::test_command_claim_keeps_reservation_free]
- ac9: (Docker) an untargeted command head overtakes queued prose held for a busy leader and for a pending handover, waits on backoff and on a gone leader, and prose order is unchanged (new) [evidence: test:tests/test_queue_leader_routing.py::test_command_skips_leader_holds]
- ac10: (Docker) per-session order: while a session's command row is dispatching, no later message of that session (a second command or prose) is claimed; once it is sent the next is claimed, so the fake wrapper receives them in id order (new) [evidence: test:tests/test_queue_leader_routing.py::test_session_messages_wait_for_dispatching_command]
- ac11: (Docker) a stale dispatching command row is failed ambiguous by the verifier, never resent (new) [evidence: test:tests/test_ambiguous_verify.py::test_stale_command_row_fails_ambiguous]
- ac12: MEMORY.md has an entry tagged with this epic that records the command dispatch rulings and names last_dispatched_at (absent today) [evidence: command:grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\)" MEMORY.md | grep -q "last_dispatched_at"]
- ac13: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py tests/test_slash.py && mise run lint]

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

- Red: add the eleven Docker tests (ac1-ac11); on a Docker host run `uv run --frozen pytest tests/test_dispatcher.py tests/test_queue_leader_routing.py tests/test_ambiguous_verify.py`: they fail. In this container only ac13 runs.
- Green: queue, dispatcher, verifier, README, MEMORY.md; run the task's verify: passes. Quote the summary line; the Docker legs run in CI.

## Notes

- Rulings and their pins (retro proposal): no reservation write (ac8), hold exemption and its limits (ac9), per-session order behind a dispatching command (ac10), backoff requeue (ac5), wrapper code as error (ac6), ambiguous fails (ac7, ac11), run marker excluded from args (ac4).
- The hop-guard link of a promoted command turn is task orch-command-turn-link (it extends `mark_sent_command`).
- Every status change stays a guarded UPDATE (`WHERE status = 'dispatching'`); one writer per transition.
- `release_agent` is skipped for command claims (nothing was reserved).
- Depends on orch-message-kind (the `kind` column) and orch-wrapper-command-client (`command()` outcomes, the fake's command route).

- 2026-10-27 amended: interrogate items 3 (hold a session's later messages while its command row is dispatching), 8 (run marker never sent as args) and 13 (ac10 evidence replaced by an epic-tagged MEMORY.md entry naming last_dispatched_at), design D10 revised

- 2026-10-29 done
