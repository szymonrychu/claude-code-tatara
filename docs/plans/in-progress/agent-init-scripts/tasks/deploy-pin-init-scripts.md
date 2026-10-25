---
title: deploy pin init scripts
status: in-progress
repo: agents-helmfile
value: the agents namespace is pinned to the orchestrator build with init scripts
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k \"not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [init-job-runner, init-scripts-public-api, init-scripts-agent-api, init-scripts-kind-e2e, fe-preset-init-scripts, fe-cluster-init-dialog]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-init-scripts-deploy-pin-init-scripts/agents-helmfile
branch: agent-init-scripts-deploy-pin-init-scripts
verified_head: ""
run: ""
provides: []
---

# deploy pin init scripts

## Requirement

Pin agents-helmfile to the agent-orchestrator build that contains this epic (design D7; precedent docs/plans/done/cluster-presets/tasks/deploy-pin-presets.md). Paths are in code/agents-helmfile.

Release path: this epic changes no chart version and no any-mcp or wrapper pin (hive owns those bumps). The release is the merge of this epic's agent-orchestrator PR to main, after which CI publishes chart `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>`. Precondition, checked first: `git -C ../agent-orchestrator fetch origin main` and the main commit that merges this epic exists and `docker manifest inspect harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (or `helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version 0.1.0-main.<sha7>`) succeeds. The orchestrator writes `<sha7>` into this task with `ticket.py amend` once the PR merges; if the merge or the published artifacts do not exist yet, end `blocked` with whoCanClear "orchestrator: merge the agent-orchestrator PR of agent-init-scripts and wait for its main CI".

- `helmfile.yaml.gotmpl`: release `agent-orchestrator` chart version `0.1.0-main.<sha7>`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `<sha7>`. Wrapper image pins, any-mcp settings, ORCH_ALLOWED_ORIGINS and ingress settings stay as they are.
- `tests/test_orchestrator_release.py`: `test_orchestrator_pin_matches_image` asserts the chart version and the image tag both carry `<sha7>`, reading the files as text (runs offline).

## Acceptance conditions

- AC1: chart version and image tag agree on the orchestrator merge sha and the test runs offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the pinned chart version and image exist in Harbor [evidence: judgement:the task notes quote the helm show chart or docker manifest inspect output for the pinned sha]
- AC3: only the orchestrator chart version and image tag change [evidence: judgement:the task diff reviewed against the requirement]
- AC4: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster" && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

- Consumes the published chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (contracts agent-orchestrator-chart, agent-orchestrator-image).

## Expected outcome

`helmfile diff` shows only the agent-orchestrator chart version and image tag changing to this epic's merge.

## Steps

- Check the precondition (merge commit and published artifacts); otherwise end blocked as the requirement says.
- Red: update the pin test to the new sha; it fails on the old pins.
- Green: bump the chart version and image tag; run the verify command: pass.

## Notes

- cluster-scaling and hive pin the same two lines; take the sha of the latest orchestrator main merge that contains this epic.
