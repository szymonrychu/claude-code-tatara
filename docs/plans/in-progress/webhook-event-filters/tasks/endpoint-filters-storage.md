---
title: endpoint filters storage
status: in-progress
repo: agents-webhook
value: each endpoint keeps its filters and ingest gets them from the auth query it already runs
files: [src/agents_webhook/migrations/0004_endpoint_filters.sql, src/agents_webhook/db/endpoints.py, tests/test_endpoints_repo.py]
verify: "uv run pytest tests/test_endpoints_repo.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [filter-rules-engine]
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

# endpoint filters storage

## Requirement

Store each endpoint's filters and load them with the endpoint (design D1). User decision: "Filters are per webhook endpoint and cover every supported type." Paths are in code/agents-webhook.

- Migration `src/agents_webhook/migrations/0004_endpoint_filters.sql`: `ALTER TABLE endpoints ADD COLUMN filters jsonb NOT NULL DEFAULT '{"allow": [], "deny": []}'::jsonb;` with a header comment that the api stays the only writer of `endpoints` (create, rotate credentials, replace filters, delete). Existing rows get empty filters. 0001-0003 are not edited.
- `db/endpoints.py`: `Endpoint` gains `filters: dict` (the canonical form of `filters.validate`); `_COLUMNS` includes `filters` and `authenticate` keeps `password_hash` as the last selected column, so its single compare-and-verify path is unchanged. `EndpointIn` gains `filters: Any = None`; `create` stores `filters.validate(data.type, data.filters)` (None stores `filters.EMPTY`) and lets its `ValueError` propagate with the `filters...` path, before any hashing or insert.
- New `set_filters(conn, id: int, data: Any) -> Endpoint | None`: in one transaction reads the endpoint's type (`FOR UPDATE`), validates `data` against it (`ValueError` propagates, nothing written), writes the canonical JSON and returns the updated `Endpoint`; None when the endpoint does not exist.
- `get`, `get_by_suffix`, `list_all` and `authenticate` return `filters`.

## Acceptance conditions

- AC1: a migrated database has endpoints.filters, and an endpoint created without filters reads back {"allow": [], "deny": []} [evidence: test:tests/test_endpoints_repo.py::test_filters_default_empty]
- AC2: create stores the canonical filters and get, list_all and authenticate return them [evidence: test:tests/test_endpoints_repo.py::test_create_stores_filters]
- AC3: create with invalid filters raises ValueError starting with the filters path and inserts no row [evidence: test:tests/test_endpoints_repo.py::test_create_invalid_filters_inserts_nothing]
- AC4: set_filters replaces the filters and returns the updated endpoint; None for a missing id [evidence: test:tests/test_endpoints_repo.py::test_set_filters_replaces]
- AC5: set_filters validates against the endpoint's own type and writes nothing on a ValueError [evidence: test:tests/test_endpoints_repo.py::test_set_filters_validates_against_type]
- AC6: authenticate still returns None identically for an unknown suffix and a wrong password with the new column [evidence: test:tests/test_endpoints_repo.py::test_authenticate_failures_unchanged_with_filters]
- AC7: the endpoints repo suite and lint pass [evidence: command:uv run pytest tests/test_endpoints_repo.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/migrations/0004_endpoint_filters.sql`
- `src/agents_webhook/db/endpoints.py`
- `tests/test_endpoints_repo.py`

## Interfaces

- `src/agents_webhook/db/endpoints.py` (contract `webhook-endpoints`): `Endpoint.filters: dict`, `EndpointIn.filters: Any = None`, `create(...)` unchanged signature, new `set_filters(conn, id, data) -> Endpoint | None`. Consumed by ingest-applies-filters (`authenticate` returns filters) and api-endpoint-filters (create, set_filters).
- Uses `filters.validate`, `filters.EMPTY` (filter-rules-engine).
- Schema: `endpoints.filters jsonb NOT NULL` (migration 0004).

## Expected outcome

Every endpoint row carries its filters; the repo validates them on create and on replace; ingest gets them from the one `authenticate` query it already runs.

## Steps

- Red: add the six tests to `tests/test_endpoints_repo.py` (they use the existing `db` fixture with migrations applied). Run `uv run pytest tests/test_endpoints_repo.py -q`: the new tests fail (no column, no `set_filters`). Docker must be running (testcontainers Postgres).
- Green: the migration, the dataclass fields, `_COLUMNS`, `create`, `set_filters`. Run the verify: all pass, lint clean.

## Notes

- `Endpoint(*row[:-1])` in `authenticate` is positional over `_COLUMNS`; put `filters` in `_COLUMNS` (and in the dataclass at the same position) so the slice still drops only `password_hash`. `expected_username = row[5]` indexes the username: keep `username` at index 5 or update the index.
- Write JSON with `psycopg.types.json.Jsonb` (as `db/events.py` does).
- `Endpoint` is frozen; a `dict` field is fine for reading. Callers never mutate it.
- The row-level writer rule (api only) is unchanged: ingest still only reads.
