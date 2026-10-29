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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
