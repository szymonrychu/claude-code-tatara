---
title: smoke scale check
status: todo
repo: agents-helmfile
value: the live smoke proves scaling works on the deployed orchestrator
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md]
verify: "uv run --frozen pytest -q tests/test_smoke_script.py && mise run lint"
depends_on: [public-scale-route]
owns: []
uses: [orch-cluster-scale-api]
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

# smoke scale check

## Requirement

Extend the live smoke to prove scaling on the deployed orchestrator (design D6; user S1, S2, X2). In `scripts/smoke.sh` the smoke cluster is created with `{replicas: 1, max_replicas: 2}`; after the existing any-mcp checks it records pod-0's uid, posts `POST /api/v1/clusters/{id}/scale {replicas: 2}` (expects 202), waits for pod-1 Ready within `SMOKE_TIMEOUT_S`, posts `{replicas: 1}`, waits until pod-1 is gone, and fails with a named message when a step times out, a scale answer is not 202, or pod-0's uid changed. Cleanup stays in the existing trap. `tests/test_smoke_script.py`: the fake API and fake kubectl serve the scale route and the pod-1 lifecycle; tests for the happy path, a refused scale, and pod-0 restarted. README smoke section names the scale step.

## Acceptance conditions

- AC1: the happy path scales 1 to 2 to 1, keeps pod-0's uid and exits 0 with cleanup [evidence: test:tests/test_smoke_script.py::test_happy_path_exits_zero_and_cleans_up]
- AC2: a scale answer other than 202 fails with a named message and cleans up [evidence: test:tests/test_smoke_script.py::test_scale_refused_fails]
- AC3: a changed pod-0 uid after scaling fails with a named message [evidence: test:tests/test_smoke_script.py::test_pod0_restart_fails]
- AC4: the script stays strict, bounded and shellcheck clean [evidence: test:tests/test_smoke_script.py::test_script_is_shellcheck_clean]
- AC5: lint passes [evidence: command:mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

## Interfaces

- Consumes `POST /api/v1/clusters/{cluster_id}/scale` (part `orch-cluster-scale-api`) and `max_replicas` on the raw spec create.

## Expected outcome

`mise run smoke` against the live namespace scales its cluster 1 to 2 to 1 and confirms pod-0 was never restarted.

## Steps

- Red: extend the fakes and add `test_scale_refused_fails` and `test_pod0_restart_fails`; run `uv run --frozen pytest -q tests/test_smoke_script.py`: fails.
- Green: add the scale step to `scripts/smoke.sh`; run the verify command.

## Notes

- Keep every curl and wait bounded by the existing timeout variables; `test_script_is_strict_bounded_and_traps` must stay green.
- The smoke runs against the live API only after deploy-pin-scaling applies the release.
