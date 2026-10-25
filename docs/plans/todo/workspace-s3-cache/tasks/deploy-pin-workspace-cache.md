---
title: deploy pin workspace cache
status: todo
repo: agents-helmfile
value: the deployment pins the orchestrator and web builds that carry the workspace cache
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_orchestrator_release.py, tests/test_web_release.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py tests/test_workspace_cache.py -k \"not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [cache-docs, web-preset-cache-fields, helmfile-cache-bucket]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# deploy pin workspace cache

## Requirement

Pin agents-helmfile to the agents-orchestrator and agents-web builds that carry the workspace cache (design D9; precedent docs/plans/done/agent-init-scripts/tasks/deploy-pin-init-scripts.md). Runs after the epic orchestrator-rename-sessions lands (release `agents-orchestrator`, values in `values/agents-orchestrator/`). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agents-orchestrator PR and agents-web PR are merged to main and their CI published chart `0.1.0-main.<sha7>` and image `<sha7>` for each (`helm show chart oci://harbor.szymonrichert.pl/charts/agents-orchestrator --version 0.1.0-main.<sha7>`, the same for `agents-web`). The orchestrator writes both `<sha7>` values into this task with `ticket.py amend` once the PRs merge; otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-orchestrator and agents-web PRs of workspace-s3-cache and wait for their main CI".

- `helmfile.yaml.gotmpl`: release `agents-orchestrator` version `0.1.0-main.<orchestrator sha7>`; release `agents-web` version `0.1.0-main.<web sha7>`.
- `values/agents-orchestrator/common.yaml`: `image.tag` `<orchestrator sha7>`.
- `values/agents-web/common.yaml`: `image.tag` `<web sha7>`.
- `tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image` and `tests/test_web_release.py::test_web_pin_matches_image` stay the pin checks (update them only if they hard-code a sha).

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the agents-web chart version and image tag agree on the merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the pinned charts and images exist in Harbor [evidence: judgement:the task notes quote helm show chart for both pinned versions]
- AC4: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py tests/test_workspace_cache.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart" && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
