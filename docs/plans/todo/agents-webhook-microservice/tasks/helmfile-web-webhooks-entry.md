---
title: helmfile web webhooks entry
status: todo
repo: agents-helmfile
value: "the live UI shows the Webhooks page, pinned to the agents-web build that has it"
files: [helmfile.yaml.gotmpl, values/agents-web/common.yaml, tests/test_web_release.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_web_release.py -k \"not test_web_release_chart\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [helmfile-webhook-releases, web-webhook-menu-entry]
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

# helmfile web webhooks entry

## Requirement

Configure the webhooks backend in agents-web and pin its build (design D11, D13; contracts `agents-web-backends-config`, `agents-web-chart`). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agents-web PR is merged to main and chart `oci://harbor.szymonrichert.pl/charts/agents-web` `0.1.0-main.<sha7>` and its image exist; the orchestrator amends `<sha7>` in. Otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-web PR of agents-webhook-microservice and wait for its main CI".

- `values/agents-web/common.yaml`: `backends` gains `{id: webhooks, label: Webhooks, basePath: /webhooks/api/v1}` after the orchestrator entry; `image.tag <sha7>`.
- `helmfile.yaml.gotmpl`: release `agents-web` version `0.1.0-main.<sha7>`; `needs` includes `agents/agents-webhook`.
- `tests/test_web_release.py`: the webhooks backend is configured with that basePath; the agents-web pin and image tag agree.

## Acceptance conditions

- AC1: agents-web lists the webhooks backend at /webhooks/api/v1 [evidence: test:tests/test_web_release.py::test_webhooks_backend_configured]
- AC2: the agents-web chart and image pins agree on the merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_web_release.py -k "not test_web_release_chart" && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-web/common.yaml`
- `tests/test_web_release.py`

## Interfaces

- Uses `agents-web-backends-config` (`backends[]` value) and `agents-web-chart`.

## Expected outcome

After apply, the menu shows Webhooks.

## Steps

- Check the precondition.
- Red: tests; run: fail. Green: values and pin; run the verify command.

## Notes

- frontend-decoupling task deploy-pin-web created `values/agents-web/common.yaml` and `tests/test_web_release.py`; keep its tests green (the pin test name may differ: follow the file).
