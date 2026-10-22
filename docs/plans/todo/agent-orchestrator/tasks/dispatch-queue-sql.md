---
title: dispatch queue sql
status: todo
repo: agent-orchestrator
value: "The round-robin core: a message goes to the agent free the longest, never twice, even with several dispatchers."
files: [src/agent_orchestrator/db/queue.py, tests/test_dispatch_queue.py]
verify: "uv run pytest tests/test_dispatch_queue.py -q && mise run lint"
depends_on: [migrations-and-schema]
owns: [queue-sql]
uses: [schema-v1, pg-fixture]
model: opus
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

# dispatch queue sql

## Requirement

The SQL of the three queue tables, `messages`, `commands` and `checks` (D2, D4). Every status change is a guarded UPDATE (`WHERE status = <expected>`), and a function reports whether it won.

Messages:
- `enqueue_message(conn, cluster_id, text, target_agent_id=None) -> id` and NOTIFY `message_queued {cluster_id}`
- `cancel_message(conn, id) -> bool` (only from queued)
- `retry_message(conn, id) -> bool` (only from failed; resets attempts and error)
- `claim_and_pick(conn) -> Claim | None`: one transaction, one clock. Every comparison and write uses Postgres `now()`; wrapper timestamps are stored but never compared with database time (D23).
  - Candidates are the oldest queued message of each cluster. For each, in id order, take `pg_try_advisory_xact_lock` on a per-cluster key and skip the cluster when another dispatcher holds it, so two dispatchers can never take msg2 before msg1 (FIFO per cluster).
  - Under the lock, read the cluster's oldest queued message that can be dispatched now: an untargeted message, or a targeted one whose target is pickable. A targeted message whose target is busy or booting is skipped (it does not block later messages); a targeted message whose target has `gone_at` set (or no longer exists) is marked `failed` with error `target_gone` and the scan continues (D23).
  - Claim it with `FOR UPDATE SKIP LOCKED`. Pick the agent of that cluster that is `ready`, has `gone_at IS NULL` and a session, has state idle, matches `target_agent_id` when set, and has `free_since` newer than `agents.last_dispatched_at` (the reservation rule; null last_dispatched_at counts as older). Order by `free_since ASC`, `FOR UPDATE OF agents SKIP LOCKED`, limit 1.
  - On a pick, in the same transaction, UPDATE the agent row setting `last_dispatched_at = now()` (the row change makes a concurrent READ COMMITTED claim recheck the predicate instead of using a stale snapshot) and mark the message `dispatching` with agent_id, `dispatched_at = now()` and `heartbeat_at = now()`. Return the Claim, which carries the agent's previous `last_dispatched_at`.
  - With no free agent, leave the message queued and try the next cluster, so one busy cluster never blocks another.
- `release_agent(conn, agent_id, previous_dispatched_at)`: restores `last_dispatched_at` after any outcome where no turn was accepted (409, unavailable, gone, config error, rejected, a requeue), so the agent is pickable again on the next pass (D23). Never called for an accepted or ambiguous send.
- `heartbeat_dispatching(conn, id) -> bool`: sets `heartbeat_at = now()` while the row is still `dispatching` (D24).
- `fail_message(conn, id, error) -> bool`: guarded `dispatching` to `failed` with a reason, no retry (used for `ambiguous`, `rejected`, `config_error`).
- `mark_sent(conn, id, turn_id)`; `requeue(conn, id)` (409: back to queued, attempts unchanged); `record_failure(conn, id, error, max_attempts)` (attempts+1, then back to queued or `failed` at max_attempts)
- `fail_stale_dispatching(conn, older_than_seconds) -> int`: dispatching rows whose `coalesce(heartbeat_at, dispatched_at)` is older than the bound (database clock) become `failed` with error `dispatcher_lost` and are never re-sent, because the turn may already have been accepted; the agent reservation is kept.
- Every transition NOTIFYs `status {cluster_id}`.

Commands:
- `enqueue_command(conn, agent_id, kind) -> id`
- `claim_command(conn, kinds) -> Command | None` (SKIP LOCKED, sets running)
- `complete_command(conn, id, status, result)`

Checks:
- `enqueue_check(conn, cluster_id, command) -> id`
- `claim_check(conn) -> Check | None`
- `set_check_job(conn, id, job_name)`
- `complete_check(conn, id, status, exit_code, log_tail)`
- `cancel_checks(conn, cluster_id) -> int`

## Acceptance conditions

- AC1: the idle agent with the oldest free_since is picked [evidence: test:tests/test_dispatch_queue.py::test_claim_picks_oldest_free_since]
- AC2: target_agent_id restricts the pick to that agent [evidence: test:tests/test_dispatch_queue.py::test_target_agent_restricts_pick]
- AC3: with every agent busy the message stays queued and other clusters still dispatch [evidence: test:tests/test_dispatch_queue.py::test_busy_agents_leave_message_queued]
- AC4: an agent whose send was accepted is not picked again until a free_since newer than its last_dispatched_at is recorded [evidence: test:tests/test_dispatch_queue.py::test_reservation_rule_blocks_redispatch_before_idle_seen]
- AC5: two concurrent claimers over 50 messages and 5 agents never claim one message twice nor one agent twice per free_since [evidence: test:tests/test_dispatch_queue.py::test_two_dispatchers_never_double_dispatch]
- AC6: messages of one cluster are claimed in id order [evidence: test:tests/test_dispatch_queue.py::test_fifo_per_cluster]
- AC7: cancel succeeds only while queued; retry only from failed [evidence: test:tests/test_dispatch_queue.py::test_cancel_and_retry_guards]
- AC8: record_failure requeues until max_attempts then fails [evidence: test:tests/test_dispatch_queue.py::test_requeue_and_fail_at_max_attempts]
- AC9: stale dispatching rows fail with dispatcher_lost and are not re-sent [evidence: test:tests/test_dispatch_queue.py::test_stale_dispatching_fails]
- AC10: commands are claimed by kind, checks run through their lifecycle [evidence: test:tests/test_dispatch_queue.py::test_commands_and_checks_lifecycle]
- AC11: after a non-accepted outcome release_agent makes the agent pickable on the very next claim, for 409, unavailable, gone, config error and rejected alike [evidence: test:tests/test_dispatch_queue.py::test_release_makes_agent_pickable_after_non_accept]
- AC12: forced interleaving: with two connections and a controlled commit order, a claim that has written last_dispatched_at but not committed makes the second claim re-evaluate and pick another agent or none, never the same agent [evidence: test:tests/test_dispatch_queue.py::test_forced_interleaving_never_double_picks_agent]
- AC13: a targeted message whose target is busy is skipped and the next untargeted message of that cluster dispatches [evidence: test:tests/test_dispatch_queue.py::test_busy_target_does_not_block_head_of_line]
- AC14: a targeted message whose target is gone fails with target_gone [evidence: test:tests/test_dispatch_queue.py::test_gone_target_fails_with_target_gone]
- AC15: forced interleaving: while one claim of a cluster is uncommitted, a second dispatcher never claims that cluster's later message first [evidence: test:tests/test_dispatch_queue.py::test_advisory_lock_keeps_fifo_under_two_dispatchers]
- AC16: a message failed as ambiguous keeps the agent reserved until a newer free_since [evidence: test:tests/test_dispatch_queue.py::test_ambiguous_failure_keeps_reservation]
- AC17: heartbeat_dispatching defers the stale cutoff and a missing heartbeat does not [evidence: test:tests/test_dispatch_queue.py::test_heartbeat_defers_stale_cutoff]

## Files

- `src/agent_orchestrator/db/queue.py`
- `tests/test_dispatch_queue.py`

## Interfaces

- `agent_orchestrator.db.queue` (contract `queue-sql`): the functions above plus dataclasses `Claim(message, agent, previous_dispatched_at)`, `Command`, `Check`

## Expected outcome

Round-robin and every queue transition are proven against a real Postgres, including two concurrent claimers.

## Steps

- Write tests/test_dispatch_queue.py with the seventeen named tests; seed rows with tests/factories.py; the concurrency test runs two claimers on separate connections with asyncio.gather; run it; expect failures.
- Implement db/queue.py.
- Rerun `uv run pytest tests/test_dispatch_queue.py -q`; expect `17 passed`; run `mise run lint`.

## Notes

Pick SQL from design-orchestrator section 2, amended by D23 (advisory lock, last_dispatched_at, release). The claim writes `agents.last_dispatched_at` (D23) so the agents row changes inside the claim transaction; the pick reads that column, not a subquery over messages. The reservation rule closes the race between a 202 and the ingester seeing busy; the wrapper's 409 is the backstop. Reconciler claims restart and rebootstrap commands, dispatcher claims interrupt and compact (D3); the dispatcher also inserts `rebootstrap` rows when a turn submit answers 404 (queue tables are the multi-writer tables, D2).
