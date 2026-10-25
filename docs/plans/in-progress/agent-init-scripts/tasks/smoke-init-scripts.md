---
title: smoke init scripts
status: in-progress
repo: agents-helmfile
value: the deployed smoke proves init scripts run once and are visible
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: []
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

# smoke init scripts

## Requirement

Extend the deployed smoke to prove init scripts end to end (user decisions C1, X2; design D7). Paths are in code/agents-helmfile.

- `scripts/smoke.sh`: the smoke cluster body becomes `{slug, spec: {replicas: 1, init_scripts: ["echo smoke-init"]}}` (still a raw spec, no preset). Pick the agent pod by name, `pod/agent-${SLUG}-0`, instead of the first pod of the cluster label selector: the init Job pod carries the same cluster label and must never be taken for the agent. After the pod is Ready and any-mcp is checked, poll `GET /api/v1/clusters/${CLUSTER_ID}/init-scripts` within the remaining `SMOKE_TIMEOUT_S` until `.status.state` is `succeeded` (fail fast on `failed`, printing `.status.reason`, `.status.exit_code` and `.status.log_tail`), assert `.status.log_tail` contains `smoke-init` and `.scripts == ["echo smoke-init"]`, and log each step. Cleanup, strict mode, bounded waits and the trap stay as they are.
- `tests/test_smoke_script.py`: the fake API and fake kubectl serve the init-scripts route and a Job pod listed before the agent pod; tests for the happy path (init succeeded, the agent pod chosen by name even when the Job pod is listed first), init failed exits non-zero with the reason and still cleans up, and init never finishing within the timeout fails and cleans up. Existing tests keep passing; the shellcheck test stays green.
- README `## Operating` smoke line mentions the init scripts check.

## Acceptance conditions

- AC1: the happy path exits 0, creates the cluster with init_scripts, picks agent-<slug>-0 even when the init Job pod is listed first, and sees init succeeded with smoke-init in the log tail [evidence: test:tests/test_smoke_script.py::test_init_scripts_succeed]
- AC2: a failed init exits non-zero printing the reason and exit code and deletes the cluster [evidence: test:tests/test_smoke_script.py::test_init_scripts_failed_fails_and_cleans_up]
- AC3: an init that never finishes within the timeout fails and deletes the cluster [evidence: test:tests/test_smoke_script.py::test_init_scripts_timeout_fails_and_cleans_up]
- AC4: the existing smoke tests, the strict-mode test and shellcheck pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

## Interfaces

- Consumes `GET /api/v1/clusters/{id}/init-scripts` and `status.init` (contracts orch-cluster-init-scripts-api, orch-cluster-status-init).

## Expected outcome

`mise run smoke` creates its cluster with an init script and fails unless the init run succeeds and is visible through the API.

## Steps

- Red: add the three smoke tests with the fake API and kubectl; `uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py` fails.
- Green: update `scripts/smoke.sh`; run the verify command: all pass, shellcheck clean.

## Notes

- Today the pod is the first of `kubectl get pods -l agents.szymonrichert.pl/cluster=<slug>` (`scripts/smoke.sh`, step 3); the init Job pod matches that label.
