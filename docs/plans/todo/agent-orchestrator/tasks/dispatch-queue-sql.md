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
- `claim_and_pick(conn) -> Claim | None`: one transaction. Claim the oldest queued message with `FOR UPDATE SKIP LOCKED`. Pick the agent of that cluster that is `ready`, has `gone_at IS NULL` and a session, has state idle, matches `target_agent_id` when set, and has `free_since` newer than its latest `dispatched_at` (the reservation rule). Order by `free_since ASC`, `FOR UPDATE OF agents SKIP LOCKED`, limit 1. On a pick, mark the message `dispatching` with agent_id and `dispatched_at = now()` and return both. With no free agent, leave the message queued and try the next cluster's oldest message, so one busy cluster never blocks another; the order stays FIFO within each cluster.
- `mark_sent(conn, id, turn_id)`; `requeue(conn, id)` (409: back to queued, attempts unchanged); `record_failure(conn, id, error, max_attempts)` (attempts+1, then back to queued or `failed` at max_attempts)
- `fail_stale_dispatching(conn, older_than_seconds) -> int`: dispatching rows older than the bound become `failed` with error `dispatcher_lost` and are never re-sent, because the turn may already have been accepted.
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
- AC4: an agent is not picked again until a free_since newer than its last dispatch is recorded [evidence: test:tests/test_dispatch_queue.py::test_reservation_rule_blocks_redispatch_before_idle_seen]
- AC5: two concurrent claimers over 50 messages and 5 agents never claim one message twice nor one agent twice per free_since [evidence: test:tests/test_dispatch_queue.py::test_two_dispatchers_never_double_dispatch]
- AC6: messages of one cluster are claimed in id order [evidence: test:tests/test_dispatch_queue.py::test_fifo_per_cluster]
- AC7: cancel succeeds only while queued; retry only from failed [evidence: test:tests/test_dispatch_queue.py::test_cancel_and_retry_guards]
- AC8: record_failure requeues until max_attempts then fails [evidence: test:tests/test_dispatch_queue.py::test_requeue_and_fail_at_max_attempts]
- AC9: stale dispatching rows fail with dispatcher_lost and are not re-sent [evidence: test:tests/test_dispatch_queue.py::test_stale_dispatching_fails]
- AC10: commands are claimed by kind, checks run through their lifecycle [evidence: test:tests/test_dispatch_queue.py::test_commands_and_checks_lifecycle]

## Files

- `src/agent_orchestrator/db/queue.py`
- `tests/test_dispatch_queue.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
