---
title: init scripts kind e2e
status: todo
repo: agent-orchestrator
value: the whole init scripts flow is proven on a real cluster through the API only
files: [tests/e2e/test_e2e_kind.py]
verify: "uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [init-job-runner, init-scripts-agent-api]
owns: []
uses: [orch-cluster-status-init, orch-init-workdir-files, orch-cluster-init-scripts-api, orch-agent-init-scripts-api]
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

# init scripts kind e2e

## Requirement

API-only kind e2e for init scripts (user decisions X2, C1, C2, C3; design D8). Path: code/agent-orchestrator/tests/e2e/test_e2e_kind.py. Every step goes through the public API or, for the agent routes, `kubectl exec` into `agent-<slug>-0` with `$ORCH_AGENT_URL` and `$ORCH_AGENT_TOKEN` from the pod env (the pattern of hive's `test_agent_api_identity`; the fake claude cannot call MCP tools).

Tests (each deletes every cluster and preset it creates in its teardown; the Default preset is never edited):
- `test_init_scripts_run_once`: create a preset with `init_scripts: ["echo e2e-init > e2e-init.txt"]`, schedule a 2-replica cluster from it; poll the cluster until `status.init.state == "succeeded"` and every agent has a session; `kubectl exec` in each pod shows `<workdir>/e2e-init.txt` and `.agent-init/init.sh` and `.agent-init/init.log`; there is exactly one Job pod history for `agent-<slug>-init` (the Job is gone after the outcome, so assert status.init.started_at is stable over two reconcile intervals and no `agent-<slug>-init` Job exists).
- `test_init_scripts_edit_writes_cluster_and_preset_without_roll`: PUT `/api/v1/clusters/{id}/init-scripts` with a new list; GET shows it with `edited_since_run: true`; the preset GET shows the new list; agent pod UIDs and `status.init.started_at` are unchanged after two reconcile intervals; then the same through the agent route from inside the pod (`curl -X PUT $ORCH_AGENT_URL/agent/v1/init-scripts -H "Authorization: Bearer $ORCH_AGENT_TOKEN" -H "X-Orch-Cluster: $ORCH_CLUSTER_ID"`), and a GET from the pod returns it.
- `test_init_scripts_failure_starts_sessions_degraded`: a raw-spec cluster with `init_scripts: ["exit 3"]` reaches `status.init.state == "failed"`, `exit_code == 3`, phase `degraded` with `init failed` in the message, and its agent still gets a session.
- `test_cluster_without_init_scripts_skipped`: the shared 1-replica `cluster` fixture shows `status.init.state == "skipped"`.

Kind e2e cannot run inside the task container; verification is collection and lint here, and the PR CI e2e job (or `mise run test:e2e`) runs it.

## Acceptance conditions

- AC1: the four init e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py -k "init_scripts"]
- AC2: the tests cover run once with files in every pod, edit through the public and the agent route writing cluster and preset with no pod roll and no re-run, failure starting sessions degraded, and skipped, through the API and kubectl exec only [evidence: judgement:tests/e2e/test_e2e_kind.py reviewed against the requirement; executed by the PR CI e2e job]
- AC3: every cluster and preset a new test creates is deleted in its teardown and the Default preset is never edited [evidence: judgement:teardown reviewed]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/test_e2e_kind.py`

## Interfaces

- Public routes `GET|PUT /api/v1/clusters/{id}/init-scripts`, agent routes `GET|PUT /agent/v1/init-scripts`, `status.init`.

## Expected outcome

Four API-only e2e tests cover run once, edit without roll or re-run, failure and skipped; they are collected locally and run in PR CI.

## Steps

- Add the four tests and their teardown; run `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py -k init_scripts`: four tests listed.
- Run the verify command: collection and lint pass.

## Notes

- Check `e2e/values-kind.yaml` `ORCH_MAX_CLUSTERS` against the extra clusters; raise it there only if needed (that file then joins this task's diff).
- Kind e2e cannot run in the task container; verified by collection and lint, run by the PR CI e2e job.
