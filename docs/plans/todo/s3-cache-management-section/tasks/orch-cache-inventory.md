---
title: orch cache inventory
status: todo
repo: agents-orchestrator
value: "The reconciler keeps a fresh listing of every S3 cache object, so the Cache section shows the bucket without holding credentials"
files: [src/agents_orchestrator/settings.py, src/agents_orchestrator/db/cache.py, src/agents_orchestrator/reconciler/cache_inventory.py, src/agents_orchestrator/reconciler/loop.py, README.md, MEMORY.md, tests/test_cache_inventory.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_inventory.py tests/test_settings.py && mise run lint  # DB-backed tests need Docker: CI only here; the list_bucket and settings tests run locally"
depends_on: [orch-cache-tables, orch-cache-pins]
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

# orch cache inventory

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G1, verbatim: "agents-web has a Cache section in the orchestrator menu (beside Sessions and Presets) listing every object under the cache prefix with object name, kind (workspace or transcripts), class, size and last modified, filterable by class and searchable by name, paged."

README Goal G2, verbatim: "each object's class is current on every view: `in_use` (with the session slugs), `preset` (with the preset name), `legacy` (old `preset-*` copy, with how many live sessions copied it), `saved` or `other`; the object list itself is at most `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` old (default 900), shows when it was listed, and a Refresh lists again at once."

README Goal G4, verbatim: "S3 credentials stay on the reconciler only; the new routes are on the web port only (not the agent or service ports)."

Design D1 (Reconciler-owned inventory table), verbatim: "`cache_objects` (key, kind, size, etag, last_modified, generation), written only by the reconciler: a full `list_objects_v2` pass every `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` (default 900) or at once on a refresh request, in its own asyncio task off the session pass (`asyncio.to_thread`, botocore paginator); a pass writes a new generation and drops the old one in one transaction. Alternatives: on-demand listing per view (up to 100 S3 calls per page view, no history); a credentialed component (forbidden). User Q3."

Design anti-goal, verbatim: "A page view triggering a full bucket listing."

Design review focus, verbatim: "Inventory generation swap is atomic; listing failures keep the previous generation."

This task delivers D1 in agents-orchestrator:

- Setting `cache_inventory_interval_seconds` (`ORCH_CACHE_INVENTORY_INTERVAL_SECONDS`, default 900, 60 to 86400 (my call bounds)), documented in README `## Workspace cache` Settings.
- New `src/agents_orchestrator/db/cache.py`: the SQL of the listing tables and of the refresh requests (claim `queued->running`, complete `running->done|failed`, every update status-guarded).
- New `src/agents_orchestrator/reconciler/cache_inventory.py`: `list_bucket(settings)` lists every object under `cache_s3_prefix` through the botocore `list_objects_v2` paginator of the one `presign._client` (no second client or credential path), stripping the prefix and taking the kind from `cache.pins.object_kind`; and the inventory task.
- A pass: claims every queued `refresh` request, inserts a `running` listing, lists in `asyncio.to_thread`, then in one transaction writes the objects under the new generation, marks the listing `done` with its object and byte totals, drops every older generation, and drops from the new generation every key whose `delete` request finished `done` after the pass started (a delete that raced the listing stays deleted); the claimed refresh requests become `done`. A listing error marks the listing `failed` with a reason of the S3 error code and HTTP status (never a credential, signature or URL), keeps the previous generation current, and fails the claimed refresh requests with that reason.
- Schedule: a pass when the task starts, then whenever `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` has passed since the last pass started, and at once when a `refresh` request is queued (woken by NOTIFY `cache_requested`, with `ORCH_RECONCILE_POLL_SECONDS` as the polling fallback).
- `reconciler/loop.py`: `CHANNELS` gains `cache_requested`; `Reconciler.run` starts the inventory task only when `settings.cache_available`, wakes it on `cache_requested`, and cancels it on stop; `reconcile_once` never lists the bucket.
- README: the NOTIFY channels table gains `cache_requested` (`{request_id}`, sent by the api, heard by the reconciler); `## Workspace cache` gains `### Cache inventory`. MEMORY.md gains a dated entry with the why (only the reconciler holds S3 credentials; a page view never lists the bucket).

## Acceptance conditions

- AC1: list_bucket returns every object under the prefix across more than one listing page with name (prefix stripped), kind, size, etag and last_modified, and leaves out keys outside the prefix [evidence: test:tests/test_cache_inventory.py::test_list_bucket_pages_and_strips_prefix]
- AC2: a pass writes a new generation, marks its listing done with object and byte totals and drops every older generation in one transaction [evidence: test:tests/test_cache_inventory.py::test_pass_swaps_generation_atomically]
- AC3: a listing error marks the listing failed with a reason holding the S3 error code and status and no access key, secret or URL, and the previous generation stays current [evidence: test:tests/test_cache_inventory.py::test_listing_failure_keeps_previous_generation]
- AC4: a queued refresh request is claimed by the next pass and ends done (failed with the reason when the listing fails); a request in any other status is untouched [evidence: test:tests/test_cache_inventory.py::test_refresh_request_runs_a_pass]
- AC5: no second pass runs before ORCH_CACHE_INVENTORY_INTERVAL_SECONDS has passed, one runs after it, and a queued refresh runs one at once [evidence: test:tests/test_cache_inventory.py::test_interval_and_refresh_schedule_passes]
- AC6: an object whose delete request finished done after the pass started is not in the new generation [evidence: test:tests/test_cache_inventory.py::test_delete_during_pass_stays_deleted]
- AC7: CHANNELS holds cache_requested, Reconciler.run starts the inventory task only with the cache configured, and reconcile_once makes no S3 call [evidence: test:tests/test_cache_inventory.py::test_reconciler_runs_inventory_off_the_session_pass]
- AC8: ORCH_CACHE_INVENTORY_INTERVAL_SECONDS defaults to 900 and refuses values outside 60 to 86400 [evidence: test:tests/test_cache_inventory.py::test_inventory_interval_setting]
- AC9: every setting is documented in the README [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- AC10: README documents the channel and the inventory, MEMORY.md records it [evidence: command:grep -q "cache_requested" README.md && grep -q "### Cache inventory" README.md && grep -qi "cache inventory" MEMORY.md]
- AC11: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/db/cache.py`
- `src/agents_orchestrator/reconciler/cache_inventory.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `README.md`
- `MEMORY.md`
- `tests/test_cache_inventory.py`

## Interfaces

- `settings.py`: `cache_inventory_interval_seconds: int = Field(default=900, ge=60, le=86400)`.
- `src/agents_orchestrator/db/cache.py` (new): `Listing` (generation, state, reason, objects, bytes, started_at, finished_at), `ListedObject` (key, kind, size, etag, last_modified); `begin_listing(conn) -> int`, `finish_listing(conn, generation, objects: Sequence[ListedObject]) -> None` (one transaction: insert, mark done with totals, drop older generations, drop keys deleted since `started_at`), `fail_listing(conn, generation, reason) -> None`, `current_listing(conn) -> Listing | None` (newest `done`), `latest_listing(conn) -> Listing | None` (newest of any state), `claim_refreshes(conn) -> list[int]`, `complete_refreshes(conn, ids, status, reason) -> None`. Later tasks add the delete and api functions here.
- `src/agents_orchestrator/reconciler/cache_inventory.py` (new): `list_bucket(settings: Settings) -> list[ListedObject]` (synchronous), `class CacheInventory(pool, settings, clock=time.monotonic)` with `async run_once() -> None` and `async run(stop: asyncio.Event, wake: asyncio.Event) -> None`.
- `reconciler/loop.py`: `CHANNELS = ("session_changed", "cache_requested")`; `Reconciler.inventory` built when `settings.cache_available`.
- The ETag is stored exactly as S3 returns it (HEAD returns the same form), so the delete executor compares like with like.

## Expected outcome

With the cache configured, the reconciler keeps `cache_objects` at most `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` old, lists again at once on a refresh request, keeps the last good listing when S3 fails, and never lists from a page view or the session pass.

## Steps

- Read `cache/presign.py` (`_client`), `cache/pins.py` (`object_kind`), `reconciler/loop.py` (`CHANNELS`, `run`, `reconcile_once`), `reconciler/checks.py` (claim pattern), `db/queue.py` (`claim_check`, `complete_check`), `db/pool.py`, `settings.py` (cache fields), the new migration, `tests/test_cache_presign.py` (ThreadedMotoServer fixture, `_no_ambient_aws`) and `tests/test_checks.py` (pool env) in one pass.
- Red: write `tests/test_cache_inventory.py` with every test named in the acceptance conditions (moto server for the bucket, `pool` for the tables, an injected clock for the schedule); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_inventory.py`; expect failure on the missing modules (DB tests: on CI or a local Postgres; the list_bucket and settings tests run locally).
- Green: write the setting, `db/cache.py`, `reconciler/cache_inventory.py` and the loop wiring; rerun the verify; expect passed.
- Write the README rows and subsection and the MEMORY.md entry; `mise run lint`; expect exit 0.

## Notes

- Paging: set the paginator's page size small in the test (or create more than 1000 objects) so more than one page is proven.
- Write the rows in batches (`executemany` or COPY) inside the one transaction; the bucket allows 100000 objects.
- Inventory size well under 100000 rows and a pass under 60 s are assumptions (design "Assumptions"); log the pass duration and object count once per pass so the live check can confirm them.
- Per-task security check (retro, recurring): no credential, signature or presigned URL in any log line, listing reason or exception message that reaches the database.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
