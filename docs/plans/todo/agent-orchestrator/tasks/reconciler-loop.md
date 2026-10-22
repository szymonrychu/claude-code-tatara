---
title: reconciler loop
status: todo
repo: agent-orchestrator
value: "Keeps Kubernetes equal to the clusters table: create, scale, edit and discard clusters without drift after a crash."
files: [src/agent_orchestrator/k8s/kube.py, tests/fakes/fake_kube.py, src/agent_orchestrator/reconciler/__init__.py, src/agent_orchestrator/reconciler/loop.py, src/agent_orchestrator/db/agents.py, tests/test_reconciler.py, README.md]
verify: "uv run pytest tests/test_reconciler.py -q && mise run lint"
depends_on: [k8s-object-renderer, dispatch-queue-sql]
owns: [kube-api, agents-repo]
uses: [k8s-render, queue-sql, schema-v1, pg-fixture, cluster-spec]
model: opus
estimate: 6
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

# reconciler loop

## Requirement

The level-triggered reconcile loop (D6, D9).

- `KubeApi` protocol:
  - `apply(obj)`: server-side apply, field manager `agent-orchestrator`, force
  - `list_objects(kind, namespace, selector)` (never called for Secrets), `get_object(kind, namespace, name)` (never called for Secrets), `delete(kind, namespace, name)`
  - `list_pods(namespace, selector)`, `delete_pod`
  - `create_job`, `get_job`, `read_pod_log(namespace, name, tail_lines)`
- `LightkubeApi` implements KubeApi with the lightkube AsyncClient; it uses in-cluster config, else kubeconfig.
- `tests/fakes/fake_kube.py:FakeKube` is an in-memory KubeApi that simulates the production Role: it raises `Forbidden` for get, list and watch on Secrets and for any call outside the clusters namespace (D26). It records applies and deletes, simulates pods for a StatefulSet (names `<sts>-<i>`, controllable `ready`), and can inject failures for one object.
- `db/agents.py` (reconciler is the writer):
  - `upsert_agent(conn, cluster_id, ordinal, pod_name, url, pod_phase, ready)`
  - `mark_gone(conn, agent_id)`
  - `set_session(conn, agent_id, session_id, created_at)`, `clear_session`
  - `list_agents(conn, cluster_id)`
  - `upsert_agent` creates the `agent_status` row with state unknown the first time.
- `Reconciler.reconcile_once()`. For every non-purged cluster that is not yet deleted (level-triggered):
  - every call targets `settings.clusters_namespace`, never `settings.namespace` (D26)
  - render the objects; before applying a StatefulSet, Service, ConfigMap or PVC, `get_object` it: when it exists without both labels, refuse to apply over it and record the cluster status error `foreign_object <kind>/<name>` (D26)
  - apply each
  - list labelled StatefulSets, Services, ConfigMaps and PVCs, and delete every one not in the desired set; a deleting cluster's desired set is empty. Only objects carrying both labels are ever deleted.
  - Secrets are never listed or read (the Role has only create, patch and delete on secrets, D26): the cluster's Secret is applied with the rest and deleted by its deterministic name `agent-<slug>-ccw` (not-found tolerated) when the cluster is deleting or purged
  - list pods and upsert agents (url = per-pod DNS in the clusters namespace, port `settings.wrapper_port`)
  - mark agents gone whose pod vanished with an ordinal at or above replicas
  - write `status {phase: pending|ready|degraded|deleting|error, ready, replicas, message}` and `observed_generation`
  - when a deleting cluster has no objects left, `mark_deleted`
  - an error in one cluster goes into its status message and never stops the others
- Restart commands: `claim_command(['restart'])`, then delete that agent's pod and complete the command.
- `Reconciler.run(stop)`: reconcile every `settings.reconcile_poll_seconds` and immediately on NOTIFY `cluster_changed`.
- README.md gains `## Kubernetes permissions`: the verbs of D9 in the clusters namespace (`ORCH_CLUSTERS_NAMESPACE`), with secrets limited to create, patch and delete (no get, list, watch), bound only to the reconciler's ServiceAccount, never pods/exec, and why the clusters live in their own namespace (D26).

## Acceptance conditions

- AC1: a new cluster applies PVC, Secret, ConfigMap, Service and StatefulSet with the field manager [evidence: test:tests/test_reconciler.py::test_create_applies_five_objects]
- AC2: scaling down marks the removed ordinals gone [evidence: test:tests/test_reconciler.py::test_scale_down_marks_gone]
- AC3: prune deletes undesired labelled objects and never touches unlabelled ones [evidence: test:tests/test_reconciler.py::test_prune_removes_undesired_labelled_only]
- AC4: a deleting cluster loses every object including the PVC, then is marked deleted [evidence: test:tests/test_reconciler.py::test_delete_removes_everything_including_pvc_then_marks_deleted]
- AC5: pods are observed into agents with per-pod URLs and readiness [evidence: test:tests/test_reconciler.py::test_observe_pods_upserts_agents]
- AC6: a restart command deletes the agent's pod and completes [evidence: test:tests/test_reconciler.py::test_restart_command_deletes_pod]
- AC7: an apply error in one cluster is recorded and other clusters still reconcile [evidence: test:tests/test_reconciler.py::test_error_in_one_cluster_does_not_block_others]
- AC8: NOTIFY cluster_changed triggers a reconcile before the poll interval [evidence: test:tests/test_reconciler.py::test_notify_triggers_immediate_reconcile]
- AC9: README documents the required Kubernetes permissions, secrets limited to create, patch and delete [evidence: doc-section:README.md#Kubernetes permissions]
- AC10: an existing unlabelled object with an object name is not applied over and the cluster status records foreign_object [evidence: test:tests/test_reconciler.py::test_unlabelled_foreign_object_not_applied_over]
- AC11: the reconciler never gets, lists or watches Secrets: FakeKube raises Forbidden for those verbs and reconcile still succeeds [evidence: test:tests/test_reconciler.py::test_secrets_only_created_patched_deleted]
- AC12: deleting a cluster deletes its Secret by name and tolerates not-found [evidence: test:tests/test_reconciler.py::test_delete_removes_secret_by_name]
- AC13: every Kubernetes call targets the clusters namespace and none the orchestrator namespace [evidence: test:tests/test_reconciler.py::test_all_calls_target_clusters_namespace]

## Files

- `src/agent_orchestrator/k8s/kube.py`
- `tests/fakes/fake_kube.py`
- `src/agent_orchestrator/reconciler/__init__.py`
- `src/agent_orchestrator/reconciler/loop.py`
- `src/agent_orchestrator/db/agents.py`
- `tests/test_reconciler.py`
- `README.md`

## Interfaces

- `agent_orchestrator.k8s.kube:KubeApi`, `LightkubeApi` (contract `kube-api`); `tests/fakes/fake_kube.py:FakeKube`
- `agent_orchestrator.db.agents` (contract `agents-repo`)
- `agent_orchestrator.reconciler.loop:Reconciler(pool, kube, settings, wrapper_factory)` with `reconcile_once()` and `run(stop: asyncio.Event)`

## Expected outcome

Cluster rows drive Kubernetes objects and agents rows, idempotently, with discard removing everything labelled.

## Steps

- Write tests/fakes/fake_kube.py and tests/test_reconciler.py with the twelve named tests; run `uv run pytest tests/test_reconciler.py -q`; expect failures.
- Implement kube.py, db/agents.py and reconciler/loop.py.
- Rerun; expect `12 passed`.
- Add the README section; run `mise run lint`.

## Notes

`wrapper_factory` is accepted now and used by session-bootstrap. Jobs are pruned only for deleting clusters, by check-jobs. lightkube generic resources: use `lightkube.generic_resource` or the typed models in `lightkube.resources`; apply with `field_manager='agent-orchestrator', force=True`.
