---
title: orch cache api
status: todo
repo: agents-orchestrator
value: "The web port serves a classified, paged cache object list with quota and listing state, and accepts delete and refresh requests"
files: [src/agents_orchestrator/api/cache.py, src/agents_orchestrator/api/app.py, src/agents_orchestrator/api/schemas.py, src/agents_orchestrator/db/cache.py, src/agents_orchestrator/settings.py, README.md, openapi.json, tests/test_api_cache_section.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_api_cache_section.py tests/test_readme_api.py tests/test_settings.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint  # DB-backed tests need Docker: CI only here; readme, openapi, settings, gate and layering tests run locally"
depends_on: [orch-cache-pins, orch-cache-inventory, orch-cache-requests]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1919629
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch cache api

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goals, verbatim:
- G1: "agents-web has a Cache section in the orchestrator menu (beside Sessions and Presets) listing every object under the cache prefix with object name, kind (workspace or transcripts), class, size and last modified, filterable by class and searchable by name, paged."
- G2: "each object's class is current on every view: `in_use` (with the session slugs), `preset` (with the preset name), `legacy` (old `preset-*` copy, with how many live sessions copied it), `saved` or `other`; the object list itself is at most `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` old (default 900), shows when it was listed, and a Refresh lists again at once."
- G3: "a user deletes one object after typing its name; the orchestrator's reconciler refuses an object pinned by any session row (live, starting or discarding) or rewritten since it was listed, and the outcome (done, refused with reason, failed with reason) is shown."
- G4: "S3 credentials stay on the reconciler only; the new routes are on the web port only (not the agent or service ports)."

Design D4 (Classes computed at read time), verbatim: "`in_use` (session slugs; not deletable), `preset` (named by a preset whose template renders without the session variables; preset name; deletable: the D11 repair, user Q5), `legacy` (`preset-[0-9a-f]{16}.tar.zst`; "copied by N live sessions" from `migration` records in state `done`; deletable, user Q2), `saved` (other names in the scheme, usually a discarded session restorable on recreate; deletable), `other` (outside the scheme: smoke objects, strays; deletable)."

Design D5 (API on the web port only), verbatim: "`GET /api/v1/cache` (available, prefix, listed_at, listing state, totals, quota), `GET /api/v1/cache/objects` (`class`, `q`, `after`, `limit<=500`, ordered by key), `POST /api/v1/cache/deletions {object, etag}` 202 (404 not listed, 409 `in_use`, 503 `cache_not_configured`), `POST /api/v1/cache/refresh` 202, `GET /api/v1/cache/requests/{id}`. Not in `service_auth.ALLOWED_ROUTES`, not on the agent port. README route table, `openapi.json`, web `sync:api`."

Design D7 (Quota settings), verbatim: "`ORCH_CACHE_QUOTA_BYTES` and `ORCH_CACHE_QUOTA_OBJECTS` (default unset, gauge hidden), set in agents-helmfile values from the OBC quota (100G, 100000). User Q4."

Design anti-goals, verbatim: "S3 credentials in the api, web or any new component (workspace-s3-cache D2, decouple anti-goal)." "A page view triggering a full bucket listing." "Cache routes reachable from agent or service tokens."

Cartographer plan input (fix-as-ac), verbatim: "README route table + `openapi.json` regen; `ALLOWED_ROUTES` stays without cache routes unless decided".

This task delivers D5, the read side of D4 and the settings of D7 in agents-orchestrator, new router module `src/agents_orchestrator/api/cache.py` included by `api/app.py`:

- `GET /api/v1/cache` -> `CacheSummary`: `available` (`settings.cache_available`), `prefix`, `listed_at` (finish time of the newest `done` listing, else null), `listing` (the newest listing's `state` (`none` when there is none), `reason`, `started_at`, `finished_at`), `refresh_pending` (a refresh request queued or running), `totals` (`objects`, `bytes` of the current generation), `quota` (`bytes`, `objects` from the settings, null when unset). Without a bucket: `available` false, zero totals, null quota.
- `GET /api/v1/cache/objects` -> `CacheObjectsPage` (`items`, `next_after`): the current generation ordered by key, `class` filter (one of the five classes, else 422), `q` case-insensitive substring of the object name (at most 256 characters), `after` exclusive key cursor, `limit` 1 to 500 (default 100, else 422). Each item: `object`, `kind`, `class`, `size`, `etag`, `last_modified`, `sessions` (pinning slugs, empty unless `in_use`), `preset` (name for `preset`, else null), `copied_by` (count for `legacy`, else null). Classes are computed on every request from the current session rows and presets through `cache.pins` (no relisting).
- `POST /api/v1/cache/deletions` body `DeleteCacheObject {object (1 to 1024 characters), etag (1 to 256)}`: 503 `cache_not_configured` without a bucket; 404 `not_listed` when the object is not in the current generation; 409 `in_use` (advisory, the message names the slugs) when `cache.pins` names it; else inserts a `queued` delete request with the object, the etag and the listed size, notifies `cache_requested` with `{request_id}`, and answers 202 with `CacheRequestView`.
- `POST /api/v1/cache/refresh`: 503 `cache_not_configured` without a bucket; answers 202 with the queued or running refresh request when one exists, else inserts one, notifies `cache_requested` and answers 202 with it (my call: no pile-up of refreshes).
- `GET /api/v1/cache/requests/{request_id}` -> `CacheRequestView` (`id`, `kind`, `object`, `etag`, `size`, `status`, `reason`, `created_at`, `started_at`, `finished_at`); 404 `not_found`.
- Settings `cache_quota_bytes` and `cache_quota_objects` (`ORCH_CACHE_QUOTA_BYTES`, `ORCH_CACHE_QUOTA_OBJECTS`, default unset, at least 1), documented in README `## Workspace cache` Settings.
- The routes stay out of `service_auth.ALLOWED_ROUTES` and off the agent port; the api makes no S3 call.
- README `## API` gains one `### <METHOD> <path>` entry per route; `openapi.json` regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`).

Review fix (interrogate 2026-10-29, act on 3: class rule in two places): the SQL class filter of `GET /api/v1/cache/objects` carries no pattern of its own. The `legacy`, `saved` and `other` key patterns are `cache.pins` constants (`LEGACY_RE`, `SAVED_RE`, written in the regex subset Python `re` and Postgres share and passed as parameters to `~`), and `in_use` and `preset` come from the `cache.pins` name maps; `cache.pins.classify` uses the same constants. One test runs the same key set (every class, including scheme-shaped smoke names, `sessions/` names, keys outside the scheme and pinned or preset-named legacy keys) through the SQL filter and through `classify` and asserts they agree for every class.

## Acceptance conditions

- AC1: GET /api/v1/cache reports available, prefix, listed_at of the newest done listing, the newest listing's state and reason, refresh_pending, the current generation's totals and the quota settings [evidence: test:tests/test_api_cache_section.py::test_cache_summary_reports_listing_totals_and_quota]
- AC2: without a bucket GET /api/v1/cache answers available false with zero totals, and deletions and refresh answer 503 cache_not_configured [evidence: test:tests/test_api_cache_section.py::test_cache_not_configured]
- AC3: GET /api/v1/cache/objects gives each object its kind and class with the pinning slugs for in_use, the preset name for preset and copied_by for legacy, plus saved and other [evidence: test:tests/test_api_cache_section.py::test_objects_carry_kind_class_and_details]
- AC4: a session created or discarded after the listing changes the object's class on the next GET without a new listing [evidence: test:tests/test_api_cache_section.py::test_class_follows_session_rows_without_relisting]
- AC5: class filter, case-insensitive name search, after cursor and limit page the list in key order; limit above 500 or an unknown class answers 422 [evidence: test:tests/test_api_cache_section.py::test_objects_filter_search_and_page]
- AC6: POST /api/v1/cache/deletions inserts one queued delete request with the object, etag and listed size, notifies cache_requested and answers 202 with the request [evidence: test:tests/test_api_cache_section.py::test_deletion_queued_and_notified]
- AC7: a deletion of an object not in the current generation answers 404 not_listed and of a pinned object 409 in_use naming the slugs, and neither inserts a row [evidence: test:tests/test_api_cache_section.py::test_deletion_refusals]
- AC8: POST /api/v1/cache/refresh inserts one refresh request and notifies; a second call while it is queued or running returns the same request [evidence: test:tests/test_api_cache_section.py::test_refresh_queued_once]
- AC9: GET /api/v1/cache/requests/{request_id} returns the request and 404 not_found for an unknown id [evidence: test:tests/test_api_cache_section.py::test_request_view]
- AC10: no cache route is in ALLOWED_ROUTES, the service port refuses them with a valid token, and the agent port does not serve them [evidence: test:tests/test_api_cache_section.py::test_cache_routes_web_port_only]
- AC11: ORCH_CACHE_QUOTA_BYTES and ORCH_CACHE_QUOTA_OBJECTS default to unset and refuse values below 1 [evidence: test:tests/test_api_cache_section.py::test_quota_settings]
- AC12: the api cache module makes no S3 call [evidence: command:! grep -nE "presign|_client|boto" src/agents_orchestrator/api/cache.py]
- AC13: every route is documented in the README [evidence: test:tests/test_readme_api.py::test_every_route_documented]
- AC14: the README documents no route the app lacks [evidence: test:tests/test_readme_api.py::test_no_stale_route_in_readme]
- AC15: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC16: the api imports nothing from k8s or the reconciler [evidence: test:tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper]
- AC17: every setting is documented in the README [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- AC18: lint passes [evidence: command:mise run lint]
- AC19: for one key set covering every class, the SQL class filter of GET /api/v1/cache/objects returns for each class exactly the keys cache.pins.classify puts in that class, and api/cache.py holds no class key pattern of its own (interrogate act on 3) [evidence: test:tests/test_api_cache_section.py::test_sql_class_filter_agrees_with_classify]

## Files

- `src/agents_orchestrator/api/cache.py`
- `src/agents_orchestrator/api/app.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/db/cache.py`
- `src/agents_orchestrator/settings.py`
- `README.md`
- `openapi.json`
- `tests/test_api_cache_section.py`

## Interfaces

- `src/agents_orchestrator/api/cache.py` (new): `router = APIRouter(prefix="/api/v1/cache")`; errors through `ApiError(status, code, message)`.
- `api/schemas.py`: `CacheQuota`, `CacheTotals`, `CacheListing`, `CacheSummary`, `CacheObjectView` (the JSON field `class`, a Python alias), `CacheObjectsPage`, `DeleteCacheObject`, `CacheRequestView`. These schema names are what agents-web imports after `sync:api` (task web-cache-client).
- `db/cache.py` gains `enqueue_delete(conn, object, etag, size) -> CacheRequest`, `enqueue_refresh(conn) -> CacheRequest` (returns the open one when present), `get_request(conn, id) -> CacheRequest | None`, `listed_object(conn, key) -> ListedObject | None` (current generation), `list_objects(conn, ...)` and `totals(conn)`; inserts notify `cache_requested` with `{request_id}` through `db.pool.notify` in the same transaction.
- `settings.py`: `cache_quota_bytes: int | None = Field(default=None, ge=1)`, `cache_quota_objects: int | None = Field(default=None, ge=1)`.
- Reads session rows with `sessions.list_sessions` and presets with `presets.list_presets`, classifies with `cache.pins` (`pins_by_object`, `preset_objects`, `legacy_copies`, `classify`).

## Expected outcome

The web port serves a classified, paged, searchable view of the inventory, the quota and listing state, and accepts delete and refresh requests the reconciler executes; nothing new is reachable from agent or service tokens and the api still holds no S3 credential.

## Steps

- Read `api/app.py`, `api/messages.py` (the checks routes: insert plus notify, 202), `api/streams.py` (`EventsPage` paging), `api/schemas.py`, `api/errors.py`, `api/service_auth.py`, `api/allowlist.py` (`PortGate`), `db/cache.py`, `db/sessions.py`, `db/presets.py`, `cache/pins.py`, `settings.py`, README `## API` and `## Workspace cache`, `tests/test_api_sessions.py` (`client_for`, `make_settings`, `assert_error`), `tests/test_service_port.py` and `tests/test_agent_port.py` in one pass.
- Red: write `tests/test_api_cache_section.py` with every test named in the acceptance conditions (rows inserted into `cache_listings`/`cache_objects` directly, as the reconciler writes them); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_api_cache_section.py tests/test_readme_api.py`; expect failures on the missing routes (DB tests: on CI or a local Postgres; the route-gate, settings, README and openapi tests run locally).
- Green: write the router, schemas, `db/cache.py` functions and settings; add the README route entries and settings rows; regenerate `openapi.json`; rerun the verify; expect passed.
- `mise run lint`; expect exit 0.

## Notes

- Keep a page bounded: filter by class and name in SQL over the current generation (the `in_use` and `preset` names are small arrays from `cache.pins`; `legacy`, `saved` and `other` are key patterns), reading at most `limit + 1` rows per request; never load the whole table for one page (the bucket allows 100000 objects).
- `test_api_cache.py` belongs to decouple-s3-session-cache-fr; this task's tests live in `tests/test_api_cache_section.py`.
- The 409 `in_use` check is advisory: the reconciler re-checks at execution (task orch-cache-requests).
- Per-task security check (retro, recurring): bound every user input (object 1024, etag 256, q 256, limit 500); the object is never a path; error messages name slugs but never a credential or URL; confirm the gate test hits the service port with a valid token.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate 2026-10-29 act on 3
