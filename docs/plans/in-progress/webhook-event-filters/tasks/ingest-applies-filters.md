---
title: ingest applies filters
status: in-progress
repo: agents-webhook
value: "deliveries that fail an endpoint's filters are accepted and stored ignored with a reason instead of starting an agent"
files: [src/agents_webhook/ingest/app.py, tests/test_ingest_http.py, README.md, tests/test_readme_config.py, tests/test_event_store.py]
verify: "uv run pytest tests/test_ingest_http.py tests/test_readme_config.py tests/test_event_store.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [endpoint-filters-storage]
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

# ingest applies filters

## Requirement

Apply each endpoint's filters at ingest (design D1, D3, D5, D10). User decision: "A delivery that fails a filter is accepted and stored as ignored with a reason, not rejected." Gate Q2 working answer: the built-in rules run first. Paths are in code/agents-webhook.

- `ingest/app.py:_deliver`: after `normalize` and `classify`, when classify returns None, `reason = filters.evaluate(event, endpoint.filters)`. The delivery is recorded through `events.record(..., ignore_reason=reason)` exactly as other ignore reasons, answers 202 `{id, status: "ignored", reason}`, sends no NOTIFY and never reaches the queue. The order before it (429, 401, 413, ping, 400) is unchanged; `type_mismatch` and `unsupported_event` deliveries skip filters.
- Logs: the existing `ingest: recorded ... reason=...` line carries the filter reason; no rule, value or payload text is logged.
- README: `## Statuses and reasons` gains `filter_denied` (a deny rule of the endpoint matched; the reason names the field, `filter_denied: <field>`) and `filter_not_allowed` (an allow rule of the endpoint did not match, `filter_not_allowed: <field>`); `## Ingest` names the filter step after classify. A new `## Filters` section documents design D2-D4: the rule shape, deny-then-allow order, AND across allow rules and OR within values, absent fields, the case rules, RE2 search semantics and syntax limits (no backreferences or lookaround), Grafana `key=value`, the bounds, and the field table per type from design D3 including which fields do not apply to which type and why.
- `tests/test_readme_config.py`: `REASONS` gains `filter_denied` and `filter_not_allowed`; `test_sections_exist` gains `Filters`; a new test asserts every field of every type in `filters.FIELDS` appears in the `## Filters` section.
- `tests/test_event_store.py::test_record_ignore_reason_is_ignored_with_fields`: its sample reason `author_not_allowed` is replaced by `filter_not_allowed: author` (the store accepts any reason; this keeps the sample list on reasons that will still exist after retire-allowed-authors).

## Acceptance conditions

- AC1: a delivery matching an endpoint deny rule answers 202 ignored with reason filter_denied: <field> and is stored ignored [evidence: test:tests/test_ingest_http.py::test_deny_filter_ignores_delivery]
- AC2: a delivery failing an endpoint allow rule answers 202 ignored with reason filter_not_allowed: <field> [evidence: test:tests/test_ingest_http.py::test_allow_filter_miss_ignores_delivery]
- AC3: a delivery passing the filters is stored new and notified as before [evidence: test:tests/test_ingest_http.py::test_passing_filters_queues_delivery]
- AC4: a delivery the built-in rules ignore keeps its built-in reason even when a filter would also match [evidence: test:tests/test_ingest_http.py::test_builtin_reason_wins_over_filter]
- AC5: an unauthenticated request to an endpoint with filters is 401 before any filter runs [evidence: test:tests/test_ingest_http.py::test_filters_never_run_before_auth]
- AC6: README documents filter_denied and filter_not_allowed under Statuses and reasons [evidence: test:tests/test_readme_config.py::test_every_status_and_reason_is_documented]
- AC7: README has a Filters section naming every field of every type in filters.FIELDS [evidence: test:tests/test_readme_config.py::test_filters_section_lists_every_field]
- AC8: the record store test samples filter_not_allowed: author instead of author_not_allowed [evidence: test:tests/test_event_store.py::test_record_ignore_reason_is_ignored_with_fields]
- AC9: the ingest, README config and event store suites and lint pass [evidence: command:uv run pytest tests/test_ingest_http.py tests/test_readme_config.py tests/test_event_store.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/ingest/app.py`
- `tests/test_ingest_http.py`
- `README.md`
- `tests/test_readme_config.py`
- `tests/test_event_store.py`

## Interfaces

- `src/agents_webhook/ingest/app.py:create_ingest_app` behaviour: 202 `{id, status, reason}` with `reason` in `filter_denied: <field>` / `filter_not_allowed: <field>` (contract `webhook-ingest-url`, response shape unchanged).
- Uses `filters.evaluate` (filter-rules-engine) and `Endpoint.filters` from `endpoints.authenticate` (endpoint-filters-storage).

## Expected outcome

An endpoint with `{"deny": [{"field": "title", "match": "regex", "values": ["^WIP"]}]}` answers a `WIP: x` PR with 202 ignored `filter_denied: title`; the README explains every field and rule.

## Steps

- Red: add the five ingest tests (create the endpoint with filters through `endpoints.create`), the README tests and the store sample change. Run `uv run pytest tests/test_ingest_http.py tests/test_readme_config.py tests/test_event_store.py -q`: the new ingest tests fail (delivery stored new), the README tests fail (no reasons, no section). Docker must be running.
- Green: the evaluate call in `_deliver`, the README sections. Run the verify: all pass, lint clean.

## Notes

- `classify` still takes `allowed_authors` here; retire-allowed-authors removes it later. Do not touch it in this task.
- Keep the module docstring's step list accurate (it names the per-request order).
- The README field table is design D3's table; copy its applicability and the "not offered" list.
