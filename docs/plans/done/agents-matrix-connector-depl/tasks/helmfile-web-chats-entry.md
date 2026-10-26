---
title: helmfile web chats entry
status: done
repo: agents-helmfile
value: "the live UI shows the Chats page, pinned to the agents-web build that has it"
files: [helmfile.yaml.gotmpl, values/agents-web/common.yaml, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_web_release.py -k \"not helmfile_build\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [helmfile-matrix-releases, web-chats-menu-entry]
model: sonnet
review: ""
verified_head: 72b381eacc60f7e69aad8fe14cdac586e90bb639
points: 1
expected_minutes: 5
expected_tokens: 678580
points_actual: 1
actual_minutes: 7
actual_tokens: 343679
actual_roles: "impl 7, review 1"
actual_role_tokens: "impl 258759, review 84920"
---

# helmfile web chats entry

## Requirement

Configure the matrix backend in agents-web and pin its build (design D12, D13; contracts `agents-web-backends-config`, `agents-web-chart`). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agents-web PR is merged to main and chart `oci://harbor.szymonrichert.pl/charts/agents-web` `0.1.0-main.<sha7>` and its image exist; the orchestrator amends `<sha7>` in. Otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-web PR of agents-matrix-connector and wait for its main CI".

- `values/agents-web/common.yaml`: `backends` gains `{id: matrix, label: Chats, basePath: /matrix/api/v1}` after the existing entries; `image.tag <sha7>`.
- `helmfile.yaml.gotmpl`: release `agents-web` version `0.1.0-main.<sha7>`; `needs` includes `agents/agents-matrix-connector`.
- `tests/test_web_release.py`: the matrix backend is configured with that basePath and label; the agents-web pin and image tag agree.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: agents-web lists the matrix backend at /matrix/api/v1 labelled Chats [evidence: test:tests/test_web_release.py::test_matrix_backend_configured]
- AC2: the agents-web chart and image pins agree on the merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the offline release tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_web_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-web/common.yaml`
- `tests/test_web_release.py`

## Interfaces

- `values/agents-web/common.yaml` `backends` (contract `agents-web-backends-config`).

## Expected outcome

The live UI shows the Chats entry once applied.

## Steps

- Red: add `test_matrix_backend_configured` (and adjust the pin test only if it names the old sha). Fails: no backend.
- Green: edit values and helmfile. Run the verify.

## Notes

- Same shape as agents-webhook-microservice task helmfile-web-webhooks-entry.

- 2026-10-26 done
