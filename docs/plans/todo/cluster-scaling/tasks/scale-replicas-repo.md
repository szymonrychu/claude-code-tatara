---
title: scale replicas repo
status: todo
repo: agent-orchestrator
value: "one guarded writer changes a running cluster's agent count without rolling pods"
files: [src/agent_orchestrator/db/clusters.py, tests/test_clusters_repo.py, MEMORY.md]
verify: "uv run --frozen pytest -q tests/test_clusters_repo.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [scale-replicas-write]
uses: []
model: ""
estimate: 5
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
