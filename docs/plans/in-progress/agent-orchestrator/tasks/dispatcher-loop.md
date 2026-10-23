---
title: dispatcher loop
status: in-progress
repo: agent-orchestrator
value: "Delivers queued messages round-robin and runs interrupt and compact commands, safely with more than one replica."
files: [src/agent_orchestrator/dispatcher/__init__.py, src/agent_orchestrator/dispatcher/loop.py, tests/test_dispatcher.py]
verify: "uv run pytest tests/test_dispatcher.py -q && mise run lint"
depends_on: [dispatch-queue-sql, fake-wrapper-contract, cluster-token-derivation, clusters-repository]
owns: []
uses: [queue-sql, wrapper-client, fake-wrapper, cluster-tokens, pg-fixture, cluster-spec, settings]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# dispatcher loop

## Requirement

The dispatcher (D4, D23, D24).

`Dispatcher.run(stop)` wakes on NOTIFY `agent_free` or `message_queued`, and also every `settings.dispatch_poll_seconds`.

Each wake drains:
- Loop `claim_and_pick` until it returns None.
- For each claim, POST the turn to the picked agent's URL and session with the cluster's derived auth token and `metadata {orch_message_id: <id>, orch_attempt: <attempts + 1>}` (the verifier matches on it, D24), up to 8 sends in flight, with `settings.wrapper_send_timeout_seconds` as the send timeout. While a send is in flight the dispatching row heartbeats every `settings.dispatching_heartbeat_seconds` (`heartbeat_dispatching`) (D24). Result mapping (D23, D24, D27):
  - TurnAccepted: `mark_sent` with turn_id. The reservation stays (the free_since rule covers it).
  - Busy: `release_agent`, then `requeue`.
  - Unavailable (5xx, connect errors): `release_agent`, then `record_failure` with the cluster's `spec.max_attempts`, error `unavailable` and the settings backoff: automatic retry after `not_before`.
  - Gone (404, 410): `release_agent`, `record_failure` with error `session_gone` and the settings backoff, and `enqueue_command(agent_id, 'rebootstrap')` so the reconciler clears the agent's session and bootstraps again.
  - ConfigError (401, 403): `release_agent`, `fail_message` with `config_error`; permanent, no retry.
  - Rejected (413, 422): `release_agent`, `fail_message` with `rejected`; permanent, no retry.
  - Ambiguous (timeout or reset after the request was written): `mark_verifying` with reason `ambiguous`. It is never re-sent here; the reservation is kept because the turn may be running, and the verifier (task ambiguous-send-verifier) decides.
- Claim `interrupt` and `compact` commands and call `interrupt` or `command(compact)`. Complete each as done with the wrapper response, or as failed with the error.
- Call `verify_stale_dispatching(settings.dispatching_stale_seconds)`.
- Call the verifier hook `self.verify_pending()`; this task makes it a no-op that ambiguous-send-verifier replaces.

A crash between claim commit and send leaves a dispatching row. The stale rule hands it to the verifier rather than re-sending it.

## Acceptance conditions

- AC1: three messages to three idle agents go one per agent in free_since order [evidence: test:tests/test_dispatcher.py::test_round_robin_by_free_since]
- AC2: a message waits while every agent is busy and is sent when one frees [evidence: test:tests/test_dispatcher.py::test_message_waits_until_agent_free]
- AC3: a 409 requeues the message [evidence: test:tests/test_dispatcher.py::test_409_requeues]
- AC4: a 503 is retried automatically after its backoff and fails the message at max_attempts [evidence: test:tests/test_dispatcher.py::test_503_retried_with_backoff_then_fails_at_max_attempts]
- AC5: two dispatcher instances never send one message twice [evidence: test:tests/test_dispatcher.py::test_two_dispatchers_no_double_send]
- AC6: a lost NOTIFY is recovered by the poll [evidence: test:tests/test_dispatcher.py::test_notify_loss_recovered_by_poll]
- AC7: interrupt and compact commands reach the wrapper and complete [evidence: test:tests/test_dispatcher.py::test_interrupt_and_compact_commands]
- AC8: every non-accept status (404, 401, 422, 500) releases the agent so the next message goes to it, and applies its mapped message outcome [evidence: test:tests/test_dispatcher.py::test_every_non_accept_status_releases_agent]
- AC9: an ambiguous send (timeout after the turn was received) moves the message to verifying, is not re-sent by the dispatcher and keeps the agent reserved [evidence: test:tests/test_dispatcher.py::test_ambiguous_send_moves_to_verifying_without_resend]
- AC10: a slow send heartbeats the dispatching row so it is not failed as dispatcher_lost, and the send timeout bounds it [evidence: test:tests/test_dispatcher.py::test_slow_send_heartbeats_and_times_out]
- AC11: an agent whose send failed with 503 receives the next message instead of being excluded forever [evidence: test:tests/test_dispatcher.py::test_agent_not_wedged_after_failed_send]
- AC12: two dispatcher instances keep per-cluster FIFO: message 1 is sent before message 2 [evidence: test:tests/test_dispatcher.py::test_two_dispatchers_keep_fifo_per_cluster]
- AC13: a 404 from the wrapper enqueues a rebootstrap command for that agent [evidence: test:tests/test_dispatcher.py::test_session_gone_enqueues_rebootstrap]
- AC14: every submit carries metadata orch_message_id and orch_attempt, and 401 and 422 fail at once without a retry [evidence: test:tests/test_dispatcher.py::test_submit_metadata_and_permanent_failures]

## Files

- `src/agent_orchestrator/dispatcher/__init__.py`
- `src/agent_orchestrator/dispatcher/loop.py`
- `tests/test_dispatcher.py`

## Interfaces

- `agent_orchestrator.dispatcher.loop:Dispatcher(pool, settings, wrapper_factory)` with `drain_once()`, `verify_pending()` and `run(stop)`

## Expected outcome

Messages posted to a cluster reach the agent free the longest; commands reach the wrapper.

## Steps

- Write tests/test_dispatcher.py with the fourteen named tests against FakeWrapper instances and the pool fixture; seed agents with tests/factories.py; run it; expect failures.
- Implement dispatcher/loop.py.
- Rerun `uv run pytest tests/test_dispatcher.py -q`; expect `14 passed`; run `mise run lint`.

## Notes

The dispatcher never writes agent_status: free_since moves only through the ingester. In AC1 the test plays the ingester's role by setting status rows with factories between sends. In AC4 set `ORCH_RETRY_BACKOFF_BASE_SECONDS` small and wait on the database clock, or move `not_before` back with a factory update; never sleep for the real defaults.
