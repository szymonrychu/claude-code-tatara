---
title: kind e2e
status: todo
repo: agent-orchestrator
value: "End-to-end proof on a real Kubernetes: a 2-agent cluster is created, round-robins three messages, merges their events, and is discarded cleanly."
files: [tests/e2e/test_e2e_kind.py, e2e/kind-config.yaml, e2e/manifests/postgres.yaml, e2e/manifests/orchestrator.yaml, e2e/manifests/rbac.yaml, scripts/e2e.sh, mise.toml, .github/workflows/ci.yaml]
verify: "mise run test:e2e && mise run lint"
depends_on: [container-images-ci, entrypoints-and-singleton, fake-wrapper-contract]
owns: []
uses: [agent-image, fake-wrapper]
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

# kind e2e

## Requirement

The kind e2e (D19, D9).

`scripts/e2e.sh` (called by `mise run test:e2e`; mise.toml adds the `kind` and `kubectl` tools):
- Create a kind cluster from `e2e/kind-config.yaml`.
- Build the orchestrator image and the test agent image: `e2e/agent-test.Dockerfile` on top of the agent image, with fake_claude.
- Load both with `kind load`.
- Make ReadWriteMany PVCs bind: use local-path-provisioner's shared-filesystem mode, or a hostPath StorageClass. Probe which one works.
- Apply namespaces `agents` and `agents-clusters` (the clusters namespace, `ORCH_CLUSTERS_NAMESPACE`), `e2e/manifests/postgres.yaml` (a plain postgres:18 Deployment and Service), the master-key Secret and a dummy `agent-orchestrator-claude` Secret in `agents-clusters` (secrets are namespace-local; the agent pods read it there).
- Apply `e2e/manifests/rbac.yaml`: ServiceAccount `agent-orchestrator-reconciler` in `agents`, and a Role in `agents-clusters` with exactly the verbs of D9 (secrets: create, patch, delete only) plus its RoleBinding to that ServiceAccount.
- Apply `e2e/manifests/orchestrator.yaml`: the four Deployments, each with a migrate initContainer; only the reconciler uses the SA. The settings env sets `ORCH_CLUSTERS_NAMESPACE=agents-clusters`, `ORCH_ALLOWED_CIDRS=127.0.0.0/8` (the port-forward arrives from loopback; pod-network callers are refused) and `ORCH_AGENT_IMAGES` with the test agent image.
- Port-forward the api, then run `uv run pytest -m e2e tests/e2e`.
- Delete the kind cluster on exit.

`tests/e2e/test_e2e_kind.py` (marker e2e):
- Create a cluster with replicas 2 and peers on through the API. Wait for 2 ready agents with sessions.
- Send 3 messages.
- The first two go to different agents in `free_since` order; the third goes to the agent that freed first.
- `GET /clusters/{id}/events` returns events of both agents interleaved in id order.
- Each agent's rendered config registers any-mcp, and `/opt/any-mcp/bin/any-mcp --help` succeeds in an agent pod. The test checks this with kubectl exec; the orchestrator itself never execs.
- `DELETE` the cluster. Within 120 s no StatefulSet, Service, ConfigMap, Secret, PVC or pod labelled with the cluster remains in `agents-clusters`.
- `kubectl auth can-i` as the reconciler ServiceAccount in `agents-clusters`: `create secrets` yes, `get secrets`, `list secrets` and `create pods/exec` no.
- A throwaway pod in the cluster calling the api Service gets 403 `forbidden`, while the port-forwarded caller succeeds (D22).

CI gains a job `e2e` after `images`, on ubuntu-latest, running `mise run test:e2e`.

## Acceptance conditions

- AC1: messages round-robin by free_since across two agents on kind [evidence: test:tests/e2e/test_e2e_kind.py::test_round_robin_by_free_since]
- AC2: the cluster event stream merges both agents in id order [evidence: test:tests/e2e/test_e2e_kind.py::test_merged_event_stream]
- AC3: any-mcp is preinstalled and registered in every agent [evidence: test:tests/e2e/test_e2e_kind.py::test_any_mcp_preinstalled]
- AC4: discarding the cluster removes every labelled object including the PVC [evidence: test:tests/e2e/test_e2e_kind.py::test_delete_removes_all_labelled_objects]
- AC5: the reconciler works with exactly the D9 Role and no pods/exec [evidence: command:! grep -q 'pods/exec' e2e/manifests/rbac.yaml && mise run test:e2e]
- AC7: mise.toml defines the task `test:e2e` and it runs scripts/e2e.sh [evidence: command:mise tasks | grep -q 'test:e2e' && grep -q 'scripts/e2e.sh' mise.toml]
- AC6: CI runs the e2e job [evidence: command:grep -q 'mise run test:e2e' .github/workflows/ci.yaml]
- AC8: the reconciler ServiceAccount can create but not get or list Secrets in the clusters namespace and cannot exec [evidence: test:tests/e2e/test_e2e_kind.py::test_reconciler_role_cannot_read_secrets]
- AC9: a pod inside the cluster is refused by the api source allowlist while the port-forward works [evidence: test:tests/e2e/test_e2e_kind.py::test_in_cluster_pod_refused_by_allowlist]
- AC10: the cluster's objects live in the clusters namespace and none in the orchestrator namespace [evidence: test:tests/e2e/test_e2e_kind.py::test_cluster_objects_live_in_clusters_namespace]

## Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/kind-config.yaml`
- `e2e/manifests/postgres.yaml`
- `e2e/manifests/orchestrator.yaml`
- `e2e/manifests/rbac.yaml`
- `scripts/e2e.sh`
- `mise.toml`
- `.github/workflows/ci.yaml`

## Interfaces

- `scripts/e2e.sh` (exit 0 on pass); marker `e2e`

## Expected outcome

`mise run test:e2e` proves create, round-robin, merged history, any-mcp and discard on a real cluster, locally and in CI.

## Steps

- Write tests/e2e/test_e2e_kind.py with the seven named tests. Run `mise run test:e2e`; expect failures, since nothing is deployed yet.
- Write kind-config, manifests, rbac and e2e.sh, and add the mise tools.
- Rerun `mise run test:e2e`; expect `7 passed`.
- Add the CI job; run `mise run lint`.

## Notes

The scaffold-repo-and-cli task creates a plain `test:e2e` (`uv run pytest -m e2e tests/e2e`); this task owns redefining `[tasks."test:e2e"]` in mise.toml to run `scripts/e2e.sh` (kind cluster up, image load, manifests, pytest, teardown) and adds the `kind` and `kubectl` tools; if mise.toml has no `test:e2e` when this task starts, it adds it. Docker is available locally (29.8.2) and kind is installed through mise. The fake claude completes turns deterministically. Make the turn duration configurable in `e2e/agent-test.config.yaml`, so the ordering of the third message is deterministic. The production Role lives in the deploy epic's chart; this manifest proves the verb list is sufficient.
