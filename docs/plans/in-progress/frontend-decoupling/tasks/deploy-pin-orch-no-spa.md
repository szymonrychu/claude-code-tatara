---
title: deploy pin orch no spa
status: in-progress
repo: agents-helmfile
value: the agents namespace is pinned to the API-only orchestrator build
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py -k \"not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [apply-smoke-web-cutover, orch-drop-frontend-build, orch-drop-spa-mount]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# deploy pin orch no spa

## Requirement

Pin agents-helmfile to the agent-orchestrator build without the UI (design D8, D10). Paths are in code/agents-helmfile.

Precondition, checked first: the agent-orchestrator PR of this epic (tasks orch-drop-spa-mount and orch-drop-frontend-build) is merged to main and its CI published chart `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>`. The orchestrator writes `<sha7>` into this task with `ticket.py amend` once the PR merges; otherwise end `blocked` with whoCanClear "orchestrator: merge the agent-orchestrator PR of frontend-decoupling and wait for its main CI".

- `helmfile.yaml.gotmpl`: release `agent-orchestrator` chart version `0.1.0-main.<sha7>`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `<sha7>`. Nothing else changes.
- `tests/test_orchestrator_release.py`: `test_orchestrator_pin_matches_image` asserts the new `<sha7>` on both.

## Acceptance conditions

- AC1: chart version and image tag agree on the orchestrator merge sha and the test runs offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the pinned chart and image exist in Harbor [evidence: judgement:the task notes quote helm show chart or docker manifest inspect for the pinned sha]
- AC3: only the orchestrator chart version and image tag change [evidence: judgement:the task diff reviewed against the requirement]
- AC4: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart" && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

- Consumes `agent-orchestrator-chart` and `agent-orchestrator-image` at the merge of this epic; uses `orch-no-ui`.

## Expected outcome

`helmfile diff` shows only the agent-orchestrator chart version and image tag changing.

## Steps

- Check the precondition; otherwise end blocked.
- Red: update the pin test to the new sha; it fails on the old pins.
- Green: bump chart version and image tag; run the AC4 command: pass.

## Notes

- Same shape as agent-init-scripts deploy-pin-init-scripts; take the sha of the orchestrator main merge that contains this epic.
