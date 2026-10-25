---
title: e2e endpoint filters
status: todo
repo: agents-webhook
value: "the real stack proves deny, allow, replace and preview end to end without the UI"
files: [tests/e2e/test_e2e_api.py, tests/e2e/conftest.py]
verify: "uv run pytest tests/e2e/test_e2e_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [ingest-applies-filters, api-endpoint-filters]
model: sonnet
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
