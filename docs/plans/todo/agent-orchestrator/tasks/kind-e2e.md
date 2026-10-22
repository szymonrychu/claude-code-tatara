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
- Apply namespace `agents`, `e2e/manifests/postgres.yaml` (a plain postgres:18 Deployment and Service), the master-key Secret and a dummy `agent-orchestrator-claude` Secret.
- Apply `e2e/manifests/rbac.yaml`: ServiceAccount `agent-orchestrator-reconciler`, and a Role with exactly the verbs of D9 plus its RoleBinding.
- Apply `e2e/manifests/orchestrator.yaml`: the four Deployments, each with a migrate initContainer; only the reconciler uses the SA.
- Port-forward the api, then run `uv run pytest -m e2e tests/e2e`.
- Delete the kind cluster on exit.

`tests/e2e/test_e2e_kind.py` (marker e2e):
- Create a cluster with replicas 2 and peers on through the API. Wait for 2 ready agents with sessions.
- Send 3 messages.
- The first two go to different agents in `free_since` order; the third goes to the agent that freed first.
- `GET /clusters/{id}/events` returns events of both agents interleaved in id order.
- Each agent's rendered config registers any-mcp, and `/opt/any-mcp/bin/any-mcp --help` succeeds in an agent pod. The test checks this with kubectl exec; the orchestrator itself never execs.
- `DELETE` the cluster. Within 120 s no StatefulSet, Service, ConfigMap, Secret, PVC or pod labelled with the cluster remains.

CI gains a job `e2e` after `images`, on ubuntu-latest, running `mise run test:e2e`.

## Acceptance conditions

- AC1: messages round-robin by free_since across two agents on kind [evidence: test:tests/e2e/test_e2e_kind.py::test_round_robin_by_free_since]
- AC2: the cluster event stream merges both agents in id order [evidence: test:tests/e2e/test_e2e_kind.py::test_merged_event_stream]
- AC3: any-mcp is preinstalled and registered in every agent [evidence: test:tests/e2e/test_e2e_kind.py::test_any_mcp_preinstalled]
- AC4: discarding the cluster removes every labelled object including the PVC [evidence: test:tests/e2e/test_e2e_kind.py::test_delete_removes_all_labelled_objects]
- AC5: the reconciler works with exactly the D9 Role and no pods/exec [evidence: command:! grep -q 'pods/exec' e2e/manifests/rbac.yaml && mise run test:e2e]
- AC6: CI runs the e2e job [evidence: command:grep -q 'mise run test:e2e' .github/workflows/ci.yaml]

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
