---
title: orch chart ci rename
status: in-progress
repo: agents-orchestrator
value: "the chart, image and CI publish as agents-orchestrator"
files: [chart/, .github/workflows/ci.yaml, mise.toml, scripts/, e2e/, tests/]
verify: "uv run pytest -q tests/test_project_name.py tests/test_chart_ci.py tests/test_chart_config.py tests/test_chart_deployments.py tests/test_chart_rbac_ingress.py tests/test_chart_scaffold.py tests/test_chart_services_port.py && mise run lint:chart && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-package-rename]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch chart ci rename

## Requirement

Rename the chart, the image and the CI from agent-orchestrator to agents-orchestrator (design D1, D11; contract `agents-orchestrator-chart` / `-image`). Paths are in code/agents-orchestrator.

- `git mv chart/agent-orchestrator chart/agents-orchestrator`; `Chart.yaml` `name: agents-orchestrator`; every helper define `agent-orchestrator.*` becomes `agents-orchestrator.*` with every `include`, every `fail` message, NOTES.txt and `ci/lint-values.yaml`.
- `.github/workflows/ci.yaml`: image `harbor.szymonrichert.pl/containers/agents-orchestrator`, local tags `agents-orchestrator:ci`, `helm package chart/agents-orchestrator`, `helm push "agents-orchestrator-$VERSION.tgz"`, the published-version check `"$CHART_REPO/agents-orchestrator"` and every message naming the chart (OCI `oci://harbor.szymonrichert.pl/charts/agents-orchestrator`).
- `mise.toml`: `lint:chart` path, test image `agents-orchestrator-agent-test:e2e`; `scripts/chart-version.sh`; `scripts/e2e.sh` (release `agents-orchestrator`, images `agents-orchestrator:e2e` and `agents-orchestrator-agent-test:e2e`, the kind cluster name `agents-orchestrator-e2e`, the managed-by selector `app.kubernetes.io/managed-by=agents-orchestrator`); `e2e/` values and manifests.
- tests/: `tests/helm_render.py` and the chart tests use `chart/agents-orchestrator`; `tests/test_project_name.py` gains `test_old_chart_retired` (`git ls-files chart/agent-orchestrator` prints nothing) and `test_chart_and_ci_named` (Chart.yaml name, the CI image and chart names, and `git grep -n -E 'agent[-_]orchestrator'` over `chart/`, `.github/`, `mise.toml`, `scripts/`, `e2e/` and `tests/` finds nothing outside `tests/test_project_name.py` itself).
- No other behaviour change. Harbor creates the new repositories on the first push from main (D11).

## Acceptance conditions

- AC1: the old chart directory is gone from git [evidence: test:tests/test_project_name.py::test_old_chart_retired]
- AC2: chart, image, CI, mise, scripts and e2e carry the new name only [evidence: test:tests/test_project_name.py::test_chart_and_ci_named]
- AC3: the chart renders and lints under the new name [evidence: command:uv run pytest -q tests/test_chart_ci.py tests/test_chart_config.py tests/test_chart_deployments.py tests/test_chart_rbac_ingress.py tests/test_chart_scaffold.py tests/test_chart_services_port.py && mise run lint:chart]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `chart/`
- `.github/workflows/ci.yaml`
- `mise.toml`
- `scripts/`
- `e2e/`
- `tests/`

## Interfaces

- Chart `chart/agents-orchestrator`, name `agents-orchestrator`, defines `agents-orchestrator.*` (fullname drives every Service, Secret and Deployment name); OCI `oci://harbor.szymonrichert.pl/charts/agents-orchestrator`; image `harbor.szymonrichert.pl/containers/agents-orchestrator:<sha7>` (contracts `agents-orchestrator-chart`, `-image`).

## Expected outcome

Main CI publishes the chart and image under the new names; the chart renders and lints.

## Steps

- Red: add `test_old_chart_retired` and `test_chart_and_ci_named` to `tests/test_project_name.py`; they fail.
- Green: `git mv` the chart, rename defines and includes, CI, mise, scripts, e2e, tests' chart paths; the verify passes.

## Notes

- The CI's published-version check and image digest check must name the new repositories, or the first main build fails.
- `CLUSTER=` in scripts/e2e.sh is the kind cluster's name: keep the variable, change only its value.
