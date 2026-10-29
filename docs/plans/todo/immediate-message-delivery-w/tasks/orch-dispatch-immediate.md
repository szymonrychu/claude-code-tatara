---
title: orch dispatch immediate
status: todo
repo: agents-orchestrator
value: messages reach a busy agent at once instead of waiting for its turn to end
files: [src/agents_orchestrator/db/queue.py, src/agents_orchestrator/dispatcher/loop.py, tests/test_dispatcher.py, tests/test_queue_leader_routing.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m \"not integration\" && mise run lint"
depends_on: [orch-priority-column, orch-wrapper-client-priority]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 10
expected_tokens: 1875101
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch dispatch immediate

## Requirement

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "currently the messages wait for too long. [...] message should get through PTY immediately and let either Claude Code or even agent queue them internally." Scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Goals G1 and G5 (README), verbatim: "a message sent to a busy session reaches its leader through the PTY at once, mid-turn, and Claude Code queues it internally; by default no message waits for the leader to go idle." "slash commands keep running at the turn's Stop whatever the priority, and nothing is pasted while a command runs or a dialog is open."

Design D13, verbatim: "In `_claim_in_session`, a `priority = 'immediate'` head picks with `_PICK_IMMEDIATE`: the target or the leader, `ready`, not gone, with a wrapper session, any state; no `state = 'idle'`, no `free_since` predicate and no `agents.last_dispatched_at` write (the slash D10 rule for commands; a busy agent has no turn slot to reserve). It is exempt from the busy-leader hold, so it overtakes older queued `idle` messages of its session (Q5), and it still waits for backoff (`not_before`), the handover hold (`_handover_pending`, so it reaches the successor leader) and a gone leader. Order: an immediate message is not claimed while an older message of its session is `dispatching` (the slash D10 per-session order rule), so pastes reach the wrapper in id order. `loop._send` sends `priority`; 202 `merged` or not is `mark_sent` with the returned turn id; a 409 other than booting|dead (`busy`, `command_active`, `dialog_open`, `interrupting`) and 429 `merge_queue_full` requeue with `not_before = now() + retry_backoff_base_seconds`, no attempt counted, no reservation to release (my call: an immediate requeue would spin against a busy wrapper). `idle` messages keep today's path exactly."

Design D8, verbatim: "`kind = 'command'` messages keep the slash epic's path (D9 run at the Stop, D10 dispatch); their `priority` is stored as sent and ignored (Q4)."

Scope (agents-orchestrator): `db/queue.py` (`Claim.priority`, `_PICK_IMMEDIATE`, the immediate leg of `_claim_in_session`, `_dispatch` without the reservation write for immediate, `requeue_backoff` or an equivalent guarded update), `dispatcher/loop.py` (`_send` passes `priority`, the immediate outcome mapping), `tests/test_dispatcher.py`, `tests/test_queue_leader_routing.py`, `README.md` (dispatch section), `MEMORY.md`.

## Acceptance conditions

- ac1: (CI or a Docker host) an untargeted immediate message for a session whose leader is busy is claimed at once for the leader, and agents.last_dispatched_at is not written (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_to_busy_leader_claimed_without_reservation]
- ac2: (CI or a Docker host) an immediate message overtakes older queued idle messages of its session, and those idle messages still wait for an idle leader (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_overtakes_queued_idle]
- ac3: (CI or a Docker host) an immediate message still waits for its backoff, for a pending handover (then reaches the successor) and for a gone leader's successor (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_waits_for_backoff_handover_and_gone_leader]
- ac4: (CI or a Docker host) an immediate message is not claimed while an older message of its session is dispatching, so sends reach the wrapper in id order (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_keeps_session_order]
- ac5: (CI or a Docker host) a targeted immediate message for a busy target is claimed for that target (new) [evidence: test:tests/test_queue_leader_routing.py::test_targeted_immediate_to_busy_target]
- ac6: (CI or a Docker host) _send passes the message's priority; a merged 202 marks the message sent with the running turn id (new) [evidence: test:tests/test_dispatcher.py::test_immediate_send_merged_marks_sent_with_running_turn]
- ac7: (CI or a Docker host) for an immediate message 409 busy, command_active, dialog_open, interrupting and 429 merge_queue_full requeue it with not_before about retry_backoff_base_seconds ahead, attempts unchanged and no reservation touched (new) [evidence: test:tests/test_dispatcher.py::test_immediate_refusal_requeues_with_backoff]
- ac8: (CI or a Docker host) a kind command message ignores its priority and follows the slash D10 path (new) [evidence: test:tests/test_dispatcher.py::test_command_ignores_priority]
- ac9: (CI or a Docker host) idle messages behave exactly as before: the existing leader-routing and dispatcher suites pass unchanged [evidence: command:uv run --frozen pytest tests/test_queue_leader_routing.py tests/test_dispatcher.py tests/test_dispatch_queue.py]
- ac10: the README dispatch section and MEMORY.md describe immediate dispatch, the exemptions and the backoff requeue [evidence: command:grep -q '_PICK_IMMEDIATE\|immediate message' README.md && grep -q 'immediate' MEMORY.md]
- ac11: Docker-free suites and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint]

## Files

- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `tests/test_dispatcher.py`
- `tests/test_queue_leader_routing.py`
- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
