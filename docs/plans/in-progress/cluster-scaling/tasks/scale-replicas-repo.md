---
title: scale replicas repo
status: in-progress
repo: agent-orchestrator
value: "one guarded writer changes a running cluster's agent count without rolling pods"
files: [src/agent_orchestrator/db/clusters.py, tests/test_clusters_repo.py, MEMORY.md]
verify: "uv run --frozen pytest -q tests/test_clusters_repo.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [scale-replicas-write]
uses: [orch-spec-cap-static, orch-hive-tables, orch-spec-runtime-mutable]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/cluster-scaling-scale-replicas-repo/agent-orchestrator
branch: cluster-scaling-scale-replicas-repo
verified_head: ""
run: ""
provides: []
---

# scale replicas repo

## Requirement

Add the one writer of the runtime replica count (design D1; user S2, S3, Q4; foundation D4). In `src/agent_orchestrator/db/clusters.py` add `ScaleRefused(Exception)` with a `code` attribute, a frozen `ScaleOutcome(cluster_id, replicas, previous_replicas, max_replicas)` and `async def set_replicas(conn, cluster_id, replicas, *, caller_agent_id: uuid.UUID | None = None) -> ScaleOutcome`. In one transaction: lock the cluster row (`SELECT ... FOR UPDATE`); a missing row raises the existing `ClusterNotFound`; then refuse in this order: `desired != 'active'` -> `cluster_deleting`; `caller_agent_id` given and not the `agent_id` of the cluster's `cluster_leaders` row (hive migration 0003, read only here) -> `not_leader`; `spec.static` -> `static_cluster`; `replicas` outside `1..spec.max_replicas` -> `out_of_range`; a current leader whose agent `ordinal >= replicas` -> `leader_would_leave`. An unchanged value returns the outcome with no UPDATE and no NOTIFY. Otherwise `UPDATE clusters SET spec = jsonb_set(spec, '{replicas}', to_jsonb(%s))` guarded by `desired = 'active'`, leaving `generation` and `observed_generation` unchanged and every other spec key byte-identical, then NOTIFY `cluster_changed` in the same transaction. The stored spec still loads as `ClusterSpec`. Add a dated MEMORY.md entry (2026-10-24): `spec.replicas` is scale-writable in place by the api only, no generation bump, refusal codes and why (the hash invariant keeps a replica change off the pod template; Q4 forbids removing the leader).

## Acceptance conditions

- AC1: set_replicas writes spec.replicas, keeps generation, observed_generation and every other spec key, and notifies cluster_changed [evidence: test:tests/test_clusters_repo.py::test_set_replicas_updates_spec_without_generation_bump]
- AC2: deleting, static and out-of-range (0 and max_replicas + 1) requests raise ScaleRefused with cluster_deleting, static_cluster and out_of_range and write nothing [evidence: test:tests/test_clusters_repo.py::test_set_replicas_refusals]
- AC3: a caller that is not the leader gets not_leader, a scale that would remove the leader's ordinal gets leader_would_leave, and a cluster with no leader row scales freely [evidence: test:tests/test_clusters_repo.py::test_set_replicas_leader_rules]
- AC4: an unchanged value returns the outcome without UPDATE or NOTIFY [evidence: test:tests/test_clusters_repo.py::test_set_replicas_unchanged_is_noop]
- AC5: the writer exists in the clusters repo [evidence: symbol:src/agent_orchestrator/db/clusters.py::set_replicas]
- AC6: MEMORY.md records the in-place replica write and leader_would_leave [evidence: command:grep -q "leader_would_leave" MEMORY.md]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/clusters.py`
- `tests/test_clusters_repo.py`
- `MEMORY.md`

## Interfaces

- Builds `src/agent_orchestrator/db/clusters.py::set_replicas`, `ScaleRefused` (codes `cluster_deleting`, `not_leader`, `static_cluster`, `out_of_range`, `leader_would_leave`), `ScaleOutcome` (part `scale-replicas-write`).
- Consumes from hive-mode-leadership-handove: `ClusterSpec.max_replicas`, `static` (F3, `spec.py`), table `cluster_leaders` (F5, `db/migrations/0003_hive.sql`, written by the dispatcher only; read here), writer rule "`spec.replicas` mutable in place, no generation bump" (README `## API` Versioning, written by hive).

## Expected outcome

The api process can change `clusters.spec.replicas` of an active cluster under the leader and cap rules, and the reconciler picks it up through `cluster_changed`.

## Steps

- Red: add the four tests to `tests/test_clusters_repo.py` (insert `cluster_leaders` and `agents` rows directly); run `uv run --frozen pytest -q tests/test_clusters_repo.py -k set_replicas`: they fail on the missing import.
- Green: implement `set_replicas`; rerun: passes. Add the MEMORY.md entry; run the verify command.

## Notes

- `jsonb_set` keeps every other key; assert byte equality of the other spec keys by loading the row before and after.
- Lock order: the cluster row first (`FOR UPDATE`), then read `cluster_leaders` joined to `agents` for the leader ordinal; never write `cluster_leaders` or `agents` (single writer: dispatcher and reconciler).
- Reuse `_fetch`, `_notify` and `ClusterNotFound` in the same module.
