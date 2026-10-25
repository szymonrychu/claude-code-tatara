---
title: deploy pin orch service port
status: done
repo: agents-helmfile
value: the deployed orchestrator serves the service port and the preset reuse field
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k \"not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-chart-services-port, orch-service-port-e2e, orch-service-port-docs, orch-preset-reuse-field, helmfile-service-token]
model: sonnet
review: ""
verified_head: 50c82d8
points: 1
expected_minutes: 5
expected_tokens: 703360
points_actual: 1
actual_minutes: 2
actual_tokens: 382565
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 230499, review 152066"
---

# deploy pin orch service port

## Requirement

Pin agents-helmfile to the agent-orchestrator build with the service port and the preset reuse field (design D10, D13, D17; precedent docs/plans/in-progress/agent-init-scripts/tasks/deploy-pin-init-scripts.md). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agent-orchestrator PR (service port, docs, e2e, `reuse_running_agent`) is merged to main and its CI published chart `0.1.0-main.<sha7>` and image `<sha7>` (`helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version 0.1.0-main.<sha7>`). The orchestrator writes `<sha7>` into this task with `ticket.py amend` once the PR merges; otherwise end `blocked`, whoCanClear "orchestrator: merge the agent-orchestrator PR of agents-webhook-microservice and wait for its main CI".

- `helmfile.yaml.gotmpl`: release `agent-orchestrator` version `0.1.0-main.<sha7>`; its `secrets:` list adds `values/agent-orchestrator/service-token-agents-webhook.secrets.yaml` after `default.secrets.yaml`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `<sha7>`; `serviceApi.port: 8002`. `ORCH_ALLOWED_CIDRS` stays `127.0.0.1/32`.
- `tests/test_orchestrator_release.py`: `test_orchestrator_pin_matches_image` for the new sha; `test_service_token_file_listed` (the release reads the token hash file); `test_allowed_cidrs_only_the_sidecar` unchanged and green.

## Acceptance conditions

- AC1: chart version and image tag agree on the orchestrator merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the orchestrator release reads the agents-webhook token hash file [evidence: test:tests/test_orchestrator_release.py::test_service_token_file_listed]
- AC3: the CIDR allowlist still admits only the sidecar [evidence: test:tests/test_orchestrator_release.py::test_allowed_cidrs_only_the_sidecar]
- AC4: the pinned chart and image exist in Harbor [evidence: judgement:the task notes quote helm show chart or docker manifest inspect for the pinned sha]
- AC5: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster" && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

- Consumes `orch-services-service`, `orch-service-tokens`, `preset-reuse-running-agent`.

## Expected outcome

agents-helmfile pins the orchestrator build that serves the service port and the reuse field.

## Steps

- Red: the release tests for the new sha; run them: fail.
- Green: the pin and values; run the verify command.

## Notes

- frontend-decoupling, cluster-scaling and configuration-improvements also pin this release; take the latest orchestrator main merge that contains this epic.

- 2026-10-25 in-progress: re-plan 2026-10-25: added; not started

- 2026-10-25 done
