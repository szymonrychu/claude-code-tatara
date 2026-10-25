---
title: e2e endpoint filters
status: done
repo: agents-webhook
value: "the real stack proves deny, allow, replace and preview end to end without the UI"
files: [tests/e2e/test_e2e_api.py, tests/e2e/conftest.py]
verify: "uv run pytest tests/e2e/test_e2e_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [ingest-applies-filters, api-endpoint-filters]
model: sonnet
review: ""
verified_head: 2616d24
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: 3
actual_minutes: 7
actual_tokens: 790550
actual_roles: impl 7
actual_role_tokens: impl 790550
---

# e2e endpoint filters

## Requirement

Prove endpoint filters end to end through the API only (design D5, D7, D10), and move the e2e stack off `WEBHOOK_ALLOWED_AUTHORS` ahead of its retirement. Paths are in code/agents-webhook.

- `tests/e2e/test_e2e_api.py`, new tests on the real stack (Postgres, the three processes, the fake orchestrator): an endpoint created with a deny rule ignores a matching delivery with `filter_denied: <field>` and runs a non-matching one (handled, one cluster); an endpoint with an author allow rule ignores a stranger with `filter_not_allowed: author`; `PUT /endpoints/{id}/filters` with empty lists makes the next equal delivery run; the preview reports `passed` and `reason` for the endpoint's rules; a Grafana endpoint denying `env=staging` ignores a staging alert and runs a production one.
- `tests/e2e/test_e2e_api.py::test_ignore_reasons_are_listed`: the `author_not_allowed` case is no longer accurate once `WEBHOOK_ALLOWED_AUTHORS` is retired (design D7); it becomes a `github-issue` endpoint created with `{"allow": [{"field": "author", "values": ["alice", "bob"]}]}` whose stranger delivery is `filter_not_allowed: author`.
- `tests/e2e/conftest.py`: the stack no longer sets `WEBHOOK_ALLOWED_AUTHORS`; `WEBHOOK_BOT_LOGINS` stays.

## Acceptance conditions

- AC1: a deny rule ignores a matching delivery with filter_denied and a non-matching delivery is handled [evidence: test:tests/e2e/test_e2e_api.py::test_deny_filter_ignores_and_others_run]
- AC2: an author allow rule ignores a stranger with filter_not_allowed: author [evidence: test:tests/e2e/test_e2e_api.py::test_allow_filter_ignores_stranger]
- AC3: replacing the filters through PUT makes the next equal delivery run [evidence: test:tests/e2e/test_e2e_api.py::test_put_filters_changes_the_outcome]
- AC4: a grafana-alert endpoint denying env=staging ignores the staging alert and runs the production one [evidence: test:tests/e2e/test_e2e_api.py::test_grafana_label_deny]
- AC5: the preview reports passed and reason for an endpoint's rules [evidence: test:tests/e2e/test_e2e_api.py::test_preview_reports_filter_outcome]
- AC6: the ignore-reasons test lists filter_not_allowed: author from an endpoint rule instead of author_not_allowed [evidence: test:tests/e2e/test_e2e_api.py::test_ignore_reasons_are_listed]
- AC7: the e2e stack no longer sets WEBHOOK_ALLOWED_AUTHORS [evidence: command:! grep -rn WEBHOOK_ALLOWED_AUTHORS tests/e2e]
- AC8: the e2e API suite and lint pass [evidence: command:uv run pytest tests/e2e/test_e2e_api.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `tests/e2e/test_e2e_api.py`
- `tests/e2e/conftest.py`

## Interfaces

- Consumes contract `webhook-api` (api-endpoint-filters) and the ingest behaviour of ingest-applies-filters; no production code changes. `tests/e2e/conftest.py:Stack.create_endpoint(type, **body)` already forwards extra body keys, so `filters=` passes through.

## Expected outcome

The API-only e2e suite proves deny, allow miss, pass, PUT replacement, Grafana label deny and the preview on the real stack, and nothing in it relies on `WEBHOOK_ALLOWED_AUTHORS`.

## Steps

- Write the five new tests, change `test_ignore_reasons_are_listed` and drop the env line from the conftest.
- Red, by mutation: temporarily make `filters.evaluate` return None (do not commit this), run `uv run pytest tests/e2e/test_e2e_api.py -q -k "filter or ignore_reasons or grafana_label"`: the new tests and the changed reasons test fail on the missing `filter_*` reason. Restore the function. Docker must be running.
- Green: run the verify: all pass, lint clean.

## Notes

- Test-only task: production behaviour came with ingest-applies-filters and api-endpoint-filters, so the red step is the mutation above; report it as such, with the failing output.
- The handled path needs the fake orchestrator to complete the turn, as `test_create_endpoint_receive_event_and_complete` does; reuse its waiting helpers.
- Payload builders are in `tests/payloads.py` (`gh_issues`, `gh_pull_request`, `grafana_alert(labels=...)`).

- 2026-10-25 done
