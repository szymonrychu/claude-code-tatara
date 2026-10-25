---
title: smoke webhook filters
status: todo
repo: agents-helmfile
value: "the live smoke proves filters are stored, evaluated and replaceable without starting a cluster"
files: [scripts/smoke.sh, tests/test_smoke_script.py]
verify: "uv run pytest tests/test_smoke_script.py -q && mise run lint"
depends_on: [api-endpoint-filters]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 9
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# smoke webhook filters

## Requirement

Extend the live smoke with an endpoint filter check that cannot start a cluster (design D9). Paths are in code/agents-helmfile.

- `scripts/smoke.sh` step 8c: the temporary github-issue endpoint is created with `filters: {"deny": [{"field": "title", "match": "regex", "values": ["^smoke-deny"]}]}`; the create answer must echo that rule (`.filters.deny[0].field == "title"`), else fail `webhook: endpoint create did not store the filters`.
- New step after 8e: `POST /webhooks/api/v1/templates/preview` with `{type: "github-issue", example: <an opened issue titled "smoke-deny check">, filters: <the same rule>}` must answer `.filters.passed == false and .filters.reason == "filter_denied: title"` and `.prompt == null`; then `PUT /webhooks/api/v1/endpoints/<id>/filters` with `{"allow": [], "deny": []}` must answer `.filters.deny == []`. Each failure is a named `fail`. Log lines name each check.
- The existing closed-issue delivery stays the only ingested delivery (still `ignored/action_ignored`: built-in rules run before filters). No step ingests a delivery the built-in rules would pass, so a broken filter can never start a cluster. The trap still deletes the temporary endpoint on every exit path, including a failure in the new steps.
- `tests/test_smoke_script.py`: the fake API answers the new calls; the happy path asserts the new log lines; the failure table gains the filter-not-stored, preview-passed and PUT-not-applied cases, each asserting the endpoint is still deleted.

## Acceptance conditions

- AC1: the happy path creates the endpoint with the deny rule, checks the preview reason and the PUT, and logs each check [evidence: test:tests/test_smoke_script.py::test_webhook_checks_happy_path]
- AC2: a create answer without the filters, a preview that passes, and a PUT that does not clear the rules each fail with a named message and still delete the endpoint [evidence: test:tests/test_smoke_script.py::test_webhook_filter_check_failures]
- AC3: the smoke still ingests only the closed-issue delivery [evidence: test:tests/test_smoke_script.py::test_webhook_smoke_ingests_only_the_closed_issue]
- AC4: the smoke prints no secret [evidence: test:tests/test_smoke_script.py::test_webhook_smoke_prints_no_secret]
- AC5: the smoke tests, shellcheck and lint pass [evidence: command:uv run pytest tests/test_smoke_script.py -q && mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
