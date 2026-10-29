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

Design D13, verbatim: "In `_claim_in_session`, a `priority = 'immediate'` head picks with `_PICK_IMMEDIATE`: the target or the leader, `ready`, not gone, with a wrapper session, any state; no `state = 'idle'` and no `free_since` predicate. The claim writes the `agents.last_dispatched_at` reservation exactly as an idle claim does (interrogate 2): an immediate message that starts a turn on an idle agent would otherwise leave the agent pickable by `_PICK` until the ingester flips its state, and the next idle message would be dispatched, refused 409 and requeued every poll; on a busy agent the reservation is harmless (the turn's end moves `free_since` past it). It is exempt from the busy-leader hold, so it overtakes older queued `idle` messages of its session (Q5), and it still waits for backoff (`not_before`), the handover hold (`_handover_pending`, so it reaches the successor leader) and a gone leader. Order: an immediate message is not claimed while an older message of its session is `dispatching` (the slash D10 per-session order rule), nor while an older `immediate` message of its session on the same route (untargeted, or the same target) is still queued, for example in backoff (interrogate 3), so pastes reach the wrapper in id order. `loop._send` sends `priority`; 202 `merged` or not is `mark_sent` with the returned turn id; a 409 other than booting|dead (`busy`, `command_active`, `dialog_open`, `interrupting`) and 429 `merge_queue_full` release the reservation (`release_agent`, as every non-accept does today) and requeue with `not_before = now() + retry_backoff_base_seconds`, no attempt counted (my call: an immediate requeue would spin against a busy wrapper). `idle` messages keep today's path exactly."

Design D8, verbatim: "`kind = 'command'` messages keep the slash epic's path (D9 run at the Stop, D10 dispatch); their `priority` is stored as sent and ignored (Q4)."

Scope (agents-orchestrator): `db/queue.py` (`Claim.priority`, `_PICK_IMMEDIATE`, the immediate leg of `_claim_in_session` with the older-immediate hold, `_dispatch` writing the reservation for both legs, `requeue_backoff` or an equivalent guarded update), `dispatcher/loop.py` (`_send` passes `priority`, the immediate outcome mapping after the existing `release_agent`), `tests/test_dispatcher.py`, `tests/test_queue_leader_routing.py`, `README.md` (dispatch section), `MEMORY.md`.

## Acceptance conditions

- ac1: (CI or a Docker host) an untargeted immediate message for a session whose leader is busy is claimed at once for the leader and writes the agents.last_dispatched_at reservation like an idle claim (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_to_busy_leader_claimed_with_reservation]
- ac2: (CI or a Docker host) an immediate message claimed for an idle agent reserves it: an idle message of the session queued behind it is not claimed for that agent until its free_since moves past the reservation (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_to_idle_agent_reserves_it]
- ac3: (CI or a Docker host) an immediate message overtakes older queued idle messages of its session, and those idle messages still wait for an idle leader (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_overtakes_queued_idle]
- ac4: (CI or a Docker host) an immediate message still waits for its backoff, for a pending handover (then reaches the successor) and for a gone leader's successor (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_waits_for_backoff_handover_and_gone_leader]
- ac5: (CI or a Docker host) an immediate message is not claimed while an older message of its session is dispatching, so sends reach the wrapper in id order (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_keeps_session_order]
- ac6: (CI or a Docker host) an immediate message is not claimed while an older immediate message of its session on the same route (untargeted, or the same target) is queued in backoff; a targeted immediate for another agent still flows (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_waits_behind_older_immediate_in_backoff]
- ac7: (CI or a Docker host) a targeted immediate message for a busy target is claimed for that target (new) [evidence: test:tests/test_queue_leader_routing.py::test_targeted_immediate_to_busy_target]
- ac8: (CI or a Docker host) _send passes the message's priority; a merged 202 marks the message sent with the running turn id and keeps the reservation (new) [evidence: test:tests/test_dispatcher.py::test_immediate_send_merged_marks_sent_with_running_turn]
- ac9: (CI or a Docker host) for an immediate message 409 busy, command_active, dialog_open, interrupting and 429 merge_queue_full release the reservation (last_dispatched_at back to the claim's previous value) and requeue it with not_before about retry_backoff_base_seconds ahead, attempts unchanged (new) [evidence: test:tests/test_dispatcher.py::test_immediate_refusal_requeues_with_backoff]
- ac10: (CI or a Docker host) a kind command message ignores its priority and follows the slash D10 path (new) [evidence: test:tests/test_dispatcher.py::test_command_ignores_priority]
- ac11: (CI or a Docker host) idle messages behave exactly as before: the existing leader-routing and dispatcher suites pass unchanged [evidence: command:uv run --frozen pytest tests/test_queue_leader_routing.py tests/test_dispatcher.py tests/test_dispatch_queue.py]
- ac12: the README dispatch section and MEMORY.md describe immediate dispatch, the reservation on both legs, the exemptions, the older-immediate hold and the backoff requeue [evidence: command:grep -q '_PICK_IMMEDIATE\|immediate message' README.md && grep -q 'immediate' MEMORY.md && grep -q 'reservation' MEMORY.md]
- ac13: Docker-free suites and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint]

## Files

- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `tests/test_dispatcher.py`
- `tests/test_queue_leader_routing.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- `db/queue.py`: `Claim.priority: str`; `_PICK_IMMEDIATE` (as `_PICK` without `s.state = 'idle'` and the `free_since` predicate, `FOR UPDATE OF a SKIP LOCKED`); the claim of an immediate message goes through `_dispatch` like an idle one (sets `status = 'dispatching'`, `agent_id`, `dispatched_at`, `heartbeat_at` and writes the `agents.last_dispatched_at` reservation, `previous_dispatched_at` kept on the claim); the immediate leg skips a head while an older `immediate` message of its session on the same route (untargeted, or the same target) is queued; one guarded update for "dispatching -> queued with not_before, attempts unchanged" (reuse or extend `requeue`, `WHERE status = 'dispatching'`).
- `dispatcher/loop.py:_send`: `client.submit_turn(wsid, text, metadata, priority=claim.priority)`; every non-accept keeps today's `release_agent` call (guarded by `claimed_at`), then an immediate refusal requeues with backoff.
- Kind `command` claims: unchanged (slash D10).

## Expected outcome

A message to a busy agent is dispatched at once and lands in its running turn; idle messages, commands, handovers and backoff behave exactly as before.

## Steps

- Read `db/queue.py` (`_CANDIDATES`, `_PICK`, `_PICK_COMMAND`, `_claim_in_session`, `_dispatch`, `requeue`, `record_failure`, `release_agent`), `dispatcher/loop.py` (`_send`), `tests/test_queue_leader_routing.py`, `tests/test_dispatcher.py`, `tests/test_dispatch_queue.py`, the README dispatch section and MEMORY.md in one pass.
- Red: add every new test named in the acceptance conditions; they need Postgres, so they fail in CI (and error locally without Docker); run the Docker-free verify to confirm nothing else broke.
- Green: implement the pick, the claim leg, the order rule, the send and the outcome mapping; README and MEMORY; run the task's verify; expect all passed. Quote the summary line; the reviewer quotes the CI summary for the Postgres tests.

## Notes

- Headline promise check (retro, recurring): every place that reads or writes the reservation (`_PICK`, `_PICK_IMMEDIATE`, `release_agent`, `retry_message`, the rollout replacer's BUSY predicate) must stay correct now that an immediate claim reserves too (design D13, interrogate 2); name each in the report.
- CI: from this task until orch-wrapper-pin-0-5-0 the real-wrapper integration and kind legs run against wrapper 0.4.1, which refuses `priority`; the orchestrator PR merges only after the pin tasks are green (design Constraints, builder Q5). Do not skip or xfail those legs here.
- Per-task security check (retro): `target_queue_full` counts queued rows only, so the wrapper's 429 cap is the flood bound for immediate messages; do not add a second cap here.
- The busy-leader hold still applies to idle messages behind an immediate one; the handover hold applies to both.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design
