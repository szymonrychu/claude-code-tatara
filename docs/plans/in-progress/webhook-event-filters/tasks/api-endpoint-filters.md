---
title: api endpoint filters
status: in-progress
repo: agents-webhook
value: "filters are set on create, replaced later and previewed against an example through the documented API"
files: [src/agents_webhook/api/schemas.py, src/agents_webhook/api/routes.py, tests/test_api.py, README.md, openapi.json]
verify: "uv run pytest tests/test_api.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [endpoint-filters-storage, ingest-applies-filters]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 14
expected_tokens: 1860143
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# api endpoint filters

## Requirement

Expose endpoint filters in the UI API (design D6, D10). User decision: "Configurable in the endpoints API and the agents-web Webhooks UI, including in the existing example-JSON preview flow if cheap: show whether the example passes the filters." Paths are in code/agents-webhook.

- `api/schemas.py`: `FilterRule {field: str, match: "equals" | "regex" = "equals", values: list[str]}`, `Filters {allow: list[FilterRule] = [], deny: list[FilterRule] = []}`, `FilterResult {passed: bool, reason: str | None}`. `EndpointIn.filters: Filters | None = None`; `EndpointView.filters: Filters` (always present, so `EndpointCreated` carries it too); `PreviewIn.template: str | None = None` and `PreviewIn.filters: Filters | None = None`; `PreviewOut {prompt: str | None, filters: FilterResult | None}`; `Meta.filter_fields: dict[str, list[str]]`.
- `POST /webhooks/api/v1/endpoints`: passes `filters` to `endpoints.create`; a `ValueError` from validation is 422 `invalid_request` with the message naming the rule path (as other field errors).
- New `PUT /webhooks/api/v1/endpoints/{id}/filters` with body `Filters`: `endpoints.set_filters`; 200 `EndpointView`; 404 `not_found` for an unknown id; 422 `invalid_request` naming the rule path. Logs `api: endpoint filters replaced id=<id>` without the rules.
- `POST /webhooks/api/v1/templates/preview`: `template` and `filters` are each optional, at least one is required (else 422 `invalid_request`, message `template or filters: required`). When `filters` is given it is validated against `type` (422 naming the path) and evaluated with `filters.evaluate` on the normalized example: `filters = {passed: reason is None, reason}`; when absent, `filters` is null. When `template` is given the prompt renders as today; when absent, `prompt` is null. Nothing is stored.
- `GET /webhooks/api/v1/meta`: `filter_fields` is `filters.FIELDS` as lists, keyed by type.
- README `## API`: the `filters` body field and the `filters` view field, a `### PUT /webhooks/api/v1/endpoints/{id}/filters` section with a curl example, the new preview body and response, and `filter_fields` in meta. `openapi.json` regenerated with `uv run python -m agents_webhook.api.openapi > openapi.json`.

## Acceptance conditions

- AC1: POST /endpoints with filters stores them and the 201 answer and GET /endpoints show them; without filters they show empty lists [evidence: test:tests/test_api.py::test_create_endpoint_with_filters]
- AC2: POST /endpoints with an invalid rule is 422 invalid_request naming the rule path and creates nothing [evidence: test:tests/test_api.py::test_create_endpoint_invalid_filters_422]
- AC3: PUT /endpoints/{id}/filters replaces the filters and returns the endpoint view [evidence: test:tests/test_api.py::test_put_filters_replaces]
- AC4: PUT /endpoints/{id}/filters is 404 not_found for an unknown id and 422 naming the path for a rule that does not apply to the type [evidence: test:tests/test_api.py::test_put_filters_errors]
- AC5: preview with filters only returns prompt null and filters {passed, reason} for a passing and a denied example, storing nothing [evidence: test:tests/test_api.py::test_preview_reports_filters]
- AC6: preview with neither template nor filters is 422 invalid_request [evidence: test:tests/test_api.py::test_preview_requires_template_or_filters]
- AC7: meta reports filter_fields equal to filters.FIELDS [evidence: test:tests/test_api.py::test_meta_reports_filter_fields]
- AC8: every route, including the PUT, is documented with a curl example and openapi.json has no drift [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC9: the API suite and lint pass [evidence: command:uv run pytest tests/test_api.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/api/schemas.py`
- `src/agents_webhook/api/routes.py`
- `tests/test_api.py`
- `README.md`
- `openapi.json`

## Interfaces

- Contract `webhook-api` (README `## API`, `openapi.json`), extended: `EndpointIn.filters`, `EndpointView.filters`, `PUT /webhooks/api/v1/endpoints/{id}/filters` (body `Filters`, 200 `EndpointView`, 404, 422), `PreviewIn {template?, type, example, filters?}`, `PreviewOut {prompt: str | null, filters: {passed, reason} | null}`, `Meta.filter_fields`. Consumed by web-vendor-filters-api, smoke-webhook-filters, e2e-endpoint-filters.
- Uses `endpoints.create`, `endpoints.set_filters` (endpoint-filters-storage), `filters.validate`, `filters.evaluate`, `filters.FIELDS` (filter-rules-engine).

## Expected outcome

`curl -X PUT -d '{"deny":[{"field":"labels","values":["env=staging"]}]}' $API/endpoints/3/filters` on a grafana-alert endpoint returns its view with the rule; the preview tells whether an example passes.

## Steps

- Red: add the seven tests to `tests/test_api.py`. Run `uv run pytest tests/test_api.py -q`: they fail (no field, no route, preview requires template). Docker must be running.
- Green: schemas, routes, README API sections, regenerate `openapi.json`. Run the verify: all pass, `tests/test_readme_api.py` green (route documented, curl example, no drift), lint clean.

## Notes

- Validate filters in the route with the endpoint type; pass the pydantic model as `model_dump()` into the repo, which validates again (single source `filters.validate`).
- Existing preview tests send `template`; they must keep passing unchanged (the response gains `filters: null`, `prompt` stays a string).
- `FilterRule.field` stays a plain `str` in the schema; the per-type check is `filters.validate`'s, so the error names the type.
