---
title: kind e2e
status: in-progress
repo: agent-orchestrator
value: "End-to-end proof on a real Kubernetes: the published-to-be chart installs, a 2-agent cluster round-robins three messages with any-mcp installed by onStart, and a discard removes everything without touching the orchestrator."
files: [tests/e2e/test_e2e_kind.py, e2e/kind-config.yaml, e2e/manifests/postgres.yaml, e2e/values-kind.yaml, scripts/e2e.sh, mise.toml, .github/workflows/ci.yaml]
verify: "mise run test:e2e && mise run lint"
depends_on: [helm-chart-ci-publish, entrypoints-and-singleton, fake-wrapper-contract, discard-hook-and-export, ambiguous-send-verifier]
owns: []
uses: [fake-wrapper, agent-orchestrator-chart, wrapper-on-start-hook, any-mcp-cli]
model: opus
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-kind-e2e/agent-orchestrator
branch: agent-orchestrator-kind-e2e
verified_head: ""
run: agent-orchestrator
provides: []
acs_for_audit: []
process_gaps: []
---

# kind e2e

## Requirement

The kind e2e (D19, D9, D26, D28). It installs this repo's chart into the one namespace `agents`.

`scripts/e2e.sh` (called by `mise run test:e2e`; mise.toml adds the `kind` and `kubectl` tools, and helm comes from helm-chart-scaffold):
- Create a kind cluster from `e2e/kind-config.yaml`.
- Build the orchestrator image (root Dockerfile) and the test agent image `e2e/agent-test.Dockerfile` (fake-wrapper-contract: the claude-code-wrapper image plus fake_claude), then load both with `kind load`.
- Make ReadWriteMany PVCs bind: use local-path-provisioner's shared-filesystem mode, or a hostPath StorageClass. Probe which one works, and set it through `ORCH_PVC_STORAGE_CLASS`.
- Create namespace `agents` and apply `e2e/manifests/postgres.yaml` (a plain postgres:18 Deployment and Service) into it.
- `helm install agent-orchestrator chart/agent-orchestrator -n agents -f e2e/values-kind.yaml --wait`. The values set:
  - `postgres.url` to the e2e Postgres
  - `masterKey.value` and a dummy `claude.token`
  - `image` to the loaded orchestrator image
  - `agentImage` to the test agent image
  - `env`: `ORCH_ALLOWED_CIDRS=127.0.0.0/8` (the port-forward arrives from loopback; pod-network callers are refused), `ORCH_AGENT_IMAGES` with the test agent image, `ORCH_IMAGE_PULL_SECRET=""` (kind has no regcred), the RWX storage class, and short `ORCH_RETRY_BACKOFF_*`
- Then run `helm test agent-orchestrator -n agents`.
- Port-forward the api Service, then run `uv run pytest -m e2e tests/e2e`.
- Delete the kind cluster on exit.

`tests/e2e/test_e2e_kind.py` (marker e2e):
- Create a cluster with replicas 2 and peers on through the API, with a deterministic fake turn duration passed in `spec.env`. Wait for 2 ready agents with sessions.
- Send 3 messages. The first two go to different agents in `free_since` order; the third goes to the agent that freed first.
- `GET /clusters/{id}/events` returns events of both agents interleaved in id order.
- any-mcp was installed by the rendered onStart hook. In each agent pod, `/opt/any-mcp/.ref` holds `ORCH_ANY_MCP_REF` and `/opt/any-mcp/bin/any-mcp --help` succeeds; the test checks this with kubectl exec, and the orchestrator itself never execs. The rendered config registers the any-mcp stdio server and disables AskUserQuestion.
- `DELETE` the cluster. Within 180 s no StatefulSet, Service, ConfigMap, Secret, PVC or pod labelled with the cluster remains in `agents`, and `GET /clusters/{id}` and its events are 404. The chart's own Deployments, Service, ConfigMap, Secrets and the Postgres stay untouched.
- `kubectl auth can-i` as the reconciler ServiceAccount in `agents`: `create secrets` yes; `get secrets`, `list secrets` and `create pods/exec` no.
- A throwaway pod in `agents` calling the api Service gets 403 `forbidden`, while the port-forwarded caller succeeds (D22).

CI gains a job `e2e` after `images` and `chart`, on ubuntu-latest, running `mise run test:e2e`.

## Acceptance conditions

- AC1: messages round-robin by free_since across two agents on kind [evidence: test:tests/e2e/test_e2e_kind.py::test_round_robin_by_free_since]
- AC2: the cluster event stream merges both agents in id order [evidence: test:tests/e2e/test_e2e_kind.py::test_merged_event_stream]
- AC3: any-mcp is installed by the onStart hook at the pinned ref and registered in every agent [evidence: test:tests/e2e/test_e2e_kind.py::test_any_mcp_installed_by_on_start]
- AC4: discarding the cluster removes every labelled object including the PVC, and its history [evidence: test:tests/e2e/test_e2e_kind.py::test_discard_removes_objects_and_history]
- AC5: the chart's Role has no pods/exec, and the reconciler works with exactly that Role [evidence: command:! grep -q 'pods/exec' chart/agent-orchestrator/templates/role.yaml && mise run test:e2e]
- AC6: CI runs the e2e job [evidence: command:grep -q 'mise run test:e2e' .github/workflows/ci.yaml]
- AC7: mise.toml defines the task test:e2e and it runs scripts/e2e.sh [evidence: command:mise tasks | grep -q 'test:e2e' && grep -q 'scripts/e2e.sh' mise.toml]
- AC8: the reconciler ServiceAccount can create but not get or list Secrets in agents and cannot exec [evidence: test:tests/e2e/test_e2e_kind.py::test_reconciler_role_cannot_read_secrets]
- AC9: a pod inside the cluster is refused by the api source allowlist while the port-forward works [evidence: test:tests/e2e/test_e2e_kind.py::test_in_cluster_pod_refused_by_allowlist]
- AC10: the orchestrator's own objects in the shared namespace survive a cluster create and discard [evidence: test:tests/e2e/test_e2e_kind.py::test_shared_namespace_leaves_orchestrator_objects]
- AC11: the chart installs with helm install --wait and helm test passes on kind [evidence: test:tests/e2e/test_e2e_kind.py::test_chart_installed_and_helm_test_passes]

## Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/kind-config.yaml`
- `e2e/manifests/postgres.yaml`
- `e2e/values-kind.yaml`
- `scripts/e2e.sh`
- `mise.toml`
- `.github/workflows/ci.yaml`

## Interfaces

- `scripts/e2e.sh` (exit 0 on pass); marker `e2e`
- consumes the chart values of contract `agent-orchestrator-chart` and the test image `e2e/agent-test.Dockerfile` of fake-wrapper-contract

## Expected outcome

`mise run test:e2e` proves the following on a real cluster, locally and in CI: the chart installs, and create, round-robin, merged history, the any-mcp onStart install, and a discard that deletes everything except the orchestrator itself.

## Steps

- Write tests/e2e/test_e2e_kind.py with the eight named tests. Run `mise run test:e2e` and expect failures, since nothing is deployed yet.
- Write kind-config, the postgres manifest, values-kind.yaml and e2e.sh, and add the mise tools.
- Rerun `mise run test:e2e` and expect `8 passed`.
- Add the CI job, then run `mise run lint`.

## Notes

The scaffold-repo-and-cli task creates a plain `test:e2e` (`uv run pytest -m e2e tests/e2e`). This task owns redefining `[tasks."test:e2e"]` in mise.toml to run `scripts/e2e.sh` (kind cluster up, image load, chart install, pytest, teardown), and adds the `kind` and `kubectl` tools. If mise.toml has no `test:e2e` when this task starts, it adds it.

Docker is available locally (29.8.2), and kind is installed through mise. The fake claude completes turns deterministically. The onStart hook pip-installs any-mcp from GitHub, so the kind nodes need egress; ubuntu-latest has it.

The Role is the chart's (helm-chart-rbac-and-ingress). There is no hand-written e2e RBAC or orchestrator manifest any more, so the e2e proves the production chart.

- 2026-10-22 amended at the gate: one namespace (Q14), chart install instead of hand manifests (5.4), any-mcp by onStart (Q8), and discard deletes history (Q4).

- 2026-10-23 run agent-orchestrator: dependency-failed on helm-chart-ci-publish, entrypoints-and-singleton, discard-hook-and-export, ambiguous-send-verifier
