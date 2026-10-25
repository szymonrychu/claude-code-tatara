---
title: deploy pin orch service port
status: todo
repo: agents-helmfile
value: "the live orchestrator runs the build with the service port and accepts the webhook service's token"
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k \"not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-chart-services-port, orch-service-port-e2e, orch-service-port-docs, helmfile-service-token]
owns: []
uses: [orch-services-service]
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

# deploy pin orch service port

## Requirement

Pin agents-helmfile to the agent-orchestrator build with the service port (design D10, D13; precedent docs/plans/in-progress/agent-init-scripts/tasks/deploy-pin-init-scripts.md). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agent-orchestrator PR is merged to main and its CI published chart `0.1.0-main.<sha7>` and image `<sha7>` (`helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version 0.1.0-main.<sha7>`). The orchestrator writes `<sha7>` into this task with `ticket.py amend` once the PR merges; otherwise end `blocked`, whoCanClear "orchestrator: merge the agent-orchestrator PR of agents-webhook-microservice and wait for its main CI".

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
