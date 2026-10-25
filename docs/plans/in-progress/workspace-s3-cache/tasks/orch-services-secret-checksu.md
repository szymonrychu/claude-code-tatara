---
title: orch services secret checksum
status: todo
repo: agents-orchestrator
value: a new service token works without a manual restart
files: [chart/agents-orchestrator/templates/deployment.yaml, tests/test_chart_deployments.py]
verify: "uv run pytest -q -o addopts='-m \"not integration and not e2e\"' tests/test_chart_deployments.py && uv run ruff check ."
depends_on: [cache-save-allowlist]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 669602
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch services secret checksum

## Requirement

Discovered in the agents-schedule-deploy apply 2026-10-26: adding a service token hash changed only the agents-orchestrator-services Secret, the api pods did not restart, and the orchestrator kept answering 401 to the new token until a manual `kubectl rollout restart deploy/agents-orchestrator-api`. In the agents-orchestrator chart, every Deployment whose container reads ORCH_SERVICE_TOKENS (or any other value from the services Secret) carries a pod-template annotation with the checksum of that Secret's rendered data (the same pattern the chart already uses for the settings ConfigMap, if it does), so a token change rolls those pods on apply. Test the render: the annotation exists and changes when serviceApi.tokenHashes changes.

## Acceptance conditions

- AC1: the pods reading the services Secret carry a checksum annotation that changes with the token hashes [evidence: test:tests/test_chart_deployments.py::test_services_secret_checksum_rolls_api]
- AC2: chart lint and tests pass [evidence: command:mise run lint]

## Files

- `chart/agents-orchestrator/templates/deployment.yaml`
- `tests/test_chart_deployments.py`

## Interfaces

See the Requirement; no new cross-repo contract.

## Expected outcome

Every acceptance condition holds on the committed HEAD.

## Steps

- Red: write the AC tests; run the task verify: they fail.
- Green: implement the Requirement; rerun the verify: they pass.
- Run the repo's full suite and lint: green.

## Notes

- See the Requirement and the epic design.md.
