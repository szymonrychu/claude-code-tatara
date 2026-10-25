---
title: deploy pin webhook filters
status: done
repo: agents-helmfile
value: the helmfile pins the filter-capable builds and stops setting the retired env var
files: [helmfile.yaml.gotmpl, values/agents-webhook/common.yaml, values/agents-web/common.yaml, tests/test_webhook_release.py, tests/test_web_release.py]
verify: "uv run pytest tests/test_webhook_release.py tests/test_web_release.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [retire-allowed-authors, e2e-endpoint-filters, web-create-endpoint-filters, web-edit-endpoint-filters]
model: sonnet
review: ""
verified_head: 5ee3612
points: 2
expected_minutes: 9
expected_tokens: 546295
points_actual: 2
actual_minutes: 3
actual_tokens: 399415
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 317342, review 82073"
---

# deploy pin webhook filters

## Requirement

Pin agents-helmfile to the agents-webhook and agents-web builds that carry endpoint filters, and drop the retired env var (design D7, D9). Brief: "agents-helmfile deploys it. The deploy task is pin bumps plus an apply and smoke." Paths are in code/agents-helmfile.

Precondition, checked first: the agents-webhook and agents-web PRs of this epic are merged to main and chart `oci://harbor.szymonrichert.pl/charts/agents-webhook` `0.1.0-main.<webhook sha7>` with image tag `<webhook sha7>`, and chart `oci://harbor.szymonrichert.pl/charts/agents-web` `0.1.0-main.<web sha7>` with image tag `<web sha7>`, exist in Harbor. Otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-webhook and agents-web PRs of webhook-event-filters and wait for their main CI".

- `helmfile.yaml.gotmpl`: `agents-webhook` version `0.1.0-main.<webhook sha7>`, `agents-web` version `0.1.0-main.<web sha7>`.
- `values/agents-webhook/common.yaml`: `image.tag <webhook sha7>`; the `WEBHOOK_ALLOWED_AUTHORS` env entry removed and the comment above `env` updated (author allowlists are per-endpoint filters now); `WEBHOOK_BOT_LOGINS` stays.
- `values/agents-web/common.yaml`: `image.tag <web sha7>`.
- `tests/test_webhook_release.py`: `SHA` is the new webhook sha7; a new test asserts the values set no `WEBHOOK_ALLOWED_AUTHORS`. `tests/test_web_release.py::test_web_pin_matches_image`: the expected tag is the new web sha7 (the old pin is no longer accurate).

## Acceptance conditions

- AC1: the agents-webhook chart version and image tag agree on the new webhook sha [evidence: test:tests/test_webhook_release.py::test_webhook_pin_and_needs]
- AC2: the agents-web chart version and image tag agree on the new web sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the agents-webhook values no longer set WEBHOOK_ALLOWED_AUTHORS and still set WEBHOOK_BOT_LOGINS [evidence: test:tests/test_webhook_release.py::test_allowed_authors_not_set]
- AC4: the pinned charts and images exist in Harbor [evidence: judgement:the task notes quote helm show chart or docker manifest inspect output for both pinned shas]
- AC5: the release tests and lint pass [evidence: command:uv run pytest tests/test_webhook_release.py tests/test_web_release.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-webhook/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_webhook_release.py`
- `tests/test_web_release.py`

## Interfaces

- Consumes contracts `agents-webhook-chart`, `agents-webhook-image` (agents-webhook main CI) and the agents-web chart and image; `webhook-settings-env` without `WEBHOOK_ALLOWED_AUTHORS` (retire-allowed-authors).

## Expected outcome

`mise run diff` would show only the two version bumps, the two image tags and the removed env entry.

## Steps

- Precondition: `git -C ../agents-webhook log origin/main -1` and `git -C ../agents-web log origin/main -1` contain this epic's merges; `helm show chart oci://harbor.szymonrichert.pl/charts/agents-webhook --version 0.1.0-main.<sha7>` and the same for agents-web succeed; quote them in the notes.
- Red: set the new shas in the two tests and add `test_allowed_authors_not_set`. Run `uv run pytest tests/test_webhook_release.py tests/test_web_release.py -q`: the pin tests and the new test fail.
- Green: the helmfile versions and the values. Run the verify: all pass, lint clean.

## Notes

- Take the latest agents-webhook and agents-web main merges that contain this epic (another epic may have merged after).
- The migration 0004 runs in the migrate initContainer on apply (additive column, approved at the gate).
- Never run `mise run apply`; apply-smoke-webhook-filters and the orchestrator do.

- 2026-10-25 done
