---
title: dispatcher leadership pass
status: in-progress
repo: agent-orchestrator
value: "exactly one agent leads each hive, changes are epoch-fenced and a lost leader is replaced"
files: [src/agent_orchestrator/db/leadership.py, src/agent_orchestrator/dispatcher/loop.py, tests/test_leadership_pass.py, README.md]
verify: "uv run pytest tests/test_leadership_pass.py tests/test_dispatcher.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [leadership-requests-api]
owns: [orch-leadership-pass]
uses: [orch-leader-read, orch-hive-tables]
model: opus
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# dispatcher leadership pass

## Requirement

The dispatcher is the single authority for leadership (Q2, Q4, Q10; cluster_leaders single writer). `db/leadership.py` `leadership_pass(conn, cluster_id) -> LeaderChange | None`, run inside the per-cluster `pg_try_advisory_xact_lock(_CLAIM_LOCK_NAMESPACE, hashtext(cluster_id))` that `claim_and_pick` takes (`db/queue.py:314-334`), so a leader change and a claim never interleave; when the lock is not acquired the pass is skipped (another dispatcher holds the cluster). Only hive clusters (`coalesce(spec->>'max_replicas', spec->>'replicas')::int > 1`). One transaction:

1. Initial leader (Q2): no `cluster_leaders` row and at least one ready, not-gone agent with a session: the lowest-ordinal such agent (the pass runs on every readiness change, so this is the first ready agent) becomes leader with epoch 1, reason `initial`.
2. Queued requests in id order, each decided with a status-guarded update (`where status = 'queued'`), `decided_at` set:
   - `handover`: rejected `not_leader` unless `from_agent_id` is the current leader; rejected `stale_epoch` unless `epoch` equals the current epoch; a named target must be in the cluster, ready, not gone and not the leader, else rejected `target_not_ready`; no target picks the ready agent free the longest other than the leader (`free_since asc, id`, the `_PICK` order), none gives rejected `no_peers`.
   - `user` (Q10 override): the target must be ready and not gone, else rejected `target_not_ready`; the epoch is ignored; a target that already leads is applied with no epoch bump.
   - applied: `cluster_leaders` gets the target, `epoch + 1`, `since = now()`, reason `handover: <reason>` or `user`.
3. Lost leader: the leader is gone, or not ready longer than `LEADER_GRACE_SECONDS = 30` (module constant, my call; `unready_since` set on first sight, cleared when ready again): the ready agent free the longest takes over with `epoch + 1`, reason `leader_lost`; with no ready agent the row stays.
4. Every change sends `NOTIFY leader_changed` with `{cluster_id, agent_id, epoch}`.

`dispatcher/loop.py` `drain` runs the pass for hive clusters with queued requests, no leader row, or a leader that is gone or not ready (one candidate query), and the loop also wakes on `leadership_requested` (plus the existing `agent_free` and poll). README `### Leadership` documents the rules and the new NOTIFY channels.

## Acceptance conditions

- AC1: the first ready agent of a hive becomes leader with epoch 1 [evidence: test:tests/test_leadership_pass.py::test_initial_leader]
- AC2: a leader's handover to a named ready agent applies with epoch + 1 [evidence: test:tests/test_leadership_pass.py::test_handover_named]
- AC3: a handover without target picks the ready agent free the longest [evidence: test:tests/test_leadership_pass.py::test_handover_any]
- AC4: requests from a non-leader, with a stale epoch, to an unready target or with no peers are rejected with not_leader, stale_epoch, target_not_ready and no_peers [evidence: test:tests/test_leadership_pass.py::test_handover_rejections]
- AC5: a user request applies regardless of epoch and is a no-op when the target already leads [evidence: test:tests/test_leadership_pass.py::test_user_override]
- AC6: a gone leader, and a leader unready past the grace period, are replaced with a new epoch [evidence: test:tests/test_leadership_pass.py::test_lost_leader_fallback]
- AC7: two concurrent passes on one cluster produce one change [evidence: test:tests/test_leadership_pass.py::test_concurrent_passes_single_change]
- AC8: alone clusters get no leader row; every change sends NOTIFY leader_changed [evidence: test:tests/test_leadership_pass.py::test_alone_untouched_and_notify]
- AC9: dispatcher tests and lint pass [evidence: command:uv run pytest tests/test_dispatcher.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/leadership.py`
- `src/agent_orchestrator/dispatcher/loop.py`
- `tests/test_leadership_pass.py`
- `README.md`

## Interfaces

- Owns part `orch-leadership-pass` (cross-epic contract): `db/leadership.py` `leadership_pass(conn, cluster_id)`, NOTIFY `leader_changed`, `LEADER_GRACE_SECONDS`.

## Expected outcome

Each hive has one leader, changed only by valid requests or a lost leader, with every change announced.

## Steps

- Red: write `tests/test_leadership_pass.py` for AC1-AC8 (two connections for the concurrency case); run `uv run pytest tests/test_leadership_pass.py -q`: fails.
- Green: the pass and its drain wiring; run the verify command: passes.

## Notes

- Lock: `pg_try_advisory_xact_lock(_CLAIM_LOCK_NAMESPACE, hashtext(cluster_id))` (`db/queue.py:314-334`), taken by the pass itself because claim_and_pick takes it only for clusters with queued messages.
- `drain` at `dispatcher/loop.py:103-108`; NOTIFY listen list at `:36`.
