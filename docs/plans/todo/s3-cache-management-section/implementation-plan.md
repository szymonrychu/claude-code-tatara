# S3 cache management section implementation plan

## Agreed rung

Not agreed yet: a draft migrated from the epic's tasks; the plan-writer revises it after the gate.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: orch cache pins

- Status: todo
- Files: `src/agents_orchestrator/cache/pins.py`, `tests/test_cache_pins.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_pins.py && mise run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G2, verbatim: "each object's class is current on every view: `in_use` (with the session slugs), `preset` (with the preset name), `legacy` (old `preset-*` copy, with how many live sessions copied it), `saved` or `other`; the object list itself is at most `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` old (default 900), shows when it was listed, and a Refresh lists again at once."

Design D3 (One pin rule, `cache.pins`), verbatim: "A pure module importable by the api and the reconciler (like `save_rule.py`): a session row pins its `status.cache.key`/`object`/`sessions_object`, the names it will pin from `spec.cache.key`, and, while its decouple migration is pending, the legacy `sessions/<slug>` and `from_key` sources; any row saving, backing up, restoring or migrating pins its object. Rows of every `desired` state count until purged."

Design D4 (Classes computed at read time), verbatim: "`in_use` (session slugs; not deletable), `preset` (named by a preset whose template renders without the session variables; preset name; deletable: the D11 repair, user Q5), `legacy` (`preset-[0-9a-f]{16}.tar.zst`; "copied by N live sessions" from `migration` records in state `done`; deletable, user Q2), `saved` (other names in the scheme, usually a discarded session restorable on recreate; deletable), `other` (outside the scheme: smoke objects, strays; deletable)."

Design anti-goal, verbatim: "The list badge and the reconciler's refusal disagreeing (two copies of the pin rule)."

This task delivers D3 and the class rule of D4 in agents-orchestrator as the new pure module `src/agents_orchestrator/cache/pins.py`. It imports nothing from `agents_orchestrator.reconciler`, `k8s`, `db` or `api` (the api may import `cache.*`; the legacy preset key formula stays in `reconciler/cache_migration.py`).

- Object names are relative to `cache_s3_prefix`, as the inventory stores them: a workspace object `<name>.tar.zst`, a transcripts object `sessions/<name>.tar.zst`. A `status.cache` value that carries the prefix is compared without it.
- A session row, in every `desired` state until purged, pins: `status.cache.object` and `status.cache.sessions_object`; `<k>.tar.zst` and `sessions/<k>.tar.zst` for `k` = `status.cache.key`; while `status.cache.key` is absent, the same two names for `spec.cache.key` (the names it will pin at its first restore); while `status.cache.sessions_object` is unset (decouple keeps it unset while the session's migration is pending, decouple design D7 amendment item 3), the legacy `sessions/<slug>.tar.zst`; while `status.cache.migration` exists and is not in state `done`, `<from_key>.tar.zst` of its `from_key`. A row saving, backing up, restoring or migrating pins its object through these same fields.
- Classes, first match wins: `in_use` (pinned by at least one row; carries the sorted slugs of every pinning row), `preset` (the workspace or transcripts name of a preset whose `spec.cache` template, or `naming.DEFAULT_CACHE_NAME_TEMPLATE` when its key is empty, renders the same name for any `session` and `created_by`; carries the preset name; a preset whose template fails to render names nothing), `legacy` (fullmatch `preset-[0-9a-f]{16}\.tar\.zst`; carries the number of session rows whose `status.cache.migration` is in state `done` with that `from_key`), `saved` (any other `<k>.tar.zst` or `sessions/<k>.tar.zst` with `k` matching `spec.CACHE_KEY_RE`), `other` (every other key).
- Kind: `transcripts` for a name under `sessions/`, else `workspace`.

#### Acceptance conditions

- AC1: a live row pins status.cache.object, status.cache.sessions_object, and the workspace and transcripts names of status.cache.key [evidence: test:tests/test_cache_pins.py::test_session_row_pins_every_cache_field]
- AC2: spec.cache.key names are pinned while status.cache.key is absent and no longer once status.cache.key names another object (a repointed pre-epic session no longer pins its old preset-* object) [evidence: test:tests/test_cache_pins.py::test_spec_key_pins_before_first_restore_only]
- AC3: the legacy sessions/<slug>.tar.zst is pinned while status.cache.sessions_object is unset, and <from_key>.tar.zst while the migration record is not done; neither once sessions_object is set and the record is done [evidence: test:tests/test_cache_pins.py::test_pending_migration_pins_legacy_sources]
- AC4: rows in desired active and deleting pin alike, and pins_by_object maps each object to the sorted slugs of every pinning row [evidence: test:tests/test_cache_pins.py::test_pins_by_object_counts_every_row_state]
- AC5: status values carrying the prefix are compared without it [evidence: test:tests/test_cache_pins.py::test_prefixed_status_values_are_stripped]
- AC6: presets with a literal key or `{{ preset }}` name their workspace and transcripts objects; presets with the default template, a `{{ session }}` or `{{ created_by }}` template, no cache, or a template that fails to render name none [evidence: test:tests/test_cache_pins.py::test_preset_objects_only_for_session_independent_templates]
- AC7: classify applies in_use, preset, legacy, saved, other in that order, including a preset-named or legacy object that a row pins reading in_use [evidence: test:tests/test_cache_pins.py::test_classify_precedence]
- AC8: legacy_copies counts the rows whose migration record is done with that from_key, ignoring failed records [evidence: test:tests/test_cache_pins.py::test_legacy_copies_count_done_migrations]
- AC9: object_kind is transcripts under sessions/ and workspace otherwise [evidence: test:tests/test_cache_pins.py::test_object_kind]
- AC10: the module imports nothing from reconciler, k8s, db or api [evidence: command:! grep -nE "agents_orchestrator\.(reconciler|k8s|db|api)|from \.\.(reconciler|k8s|db|api)" src/agents_orchestrator/cache/pins.py]
- AC11: lint passes [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/cache/pins.py`
- `tests/test_cache_pins.py`

#### Interfaces

- `src/agents_orchestrator/cache/pins.py` (new, pure, synchronous):
  - `ObjectKind = Literal["workspace", "transcripts"]`, `CacheClass = Literal["in_use", "preset", "legacy", "saved", "other"]`, `LEGACY_RE` (fullmatch `preset-[0-9a-f]{16}\.tar\.zst`) and `SAVED_RE` (fullmatch `(sessions/)?<k>\.tar\.zst` with `<k>` the body of `spec.CACHE_KEY_RE`), both written in the regex subset Python `re` and Postgres share, used by `classify` and by the api's SQL filter (review fix, interrogate act on 3; task orch-cache-api AC19).
  - `class PinRow(Protocol)`: `slug: str`, `spec` (a `SessionSpec`: `spec.cache` is None or has `.key`), `status: Mapping[str, Any]`; `db.sessions.Session` satisfies it, so callers pass rows from `sessions.list_sessions` unchanged.
  - `object_kind(name: str) -> ObjectKind`.
  - `session_pins(row: PinRow, prefix: str) -> frozenset[str]`.
  - `pins_by_object(rows: Iterable[PinRow], prefix: str) -> dict[str, tuple[str, ...]]` (object name -> sorted slugs).
  - `preset_objects(presets: Iterable[PresetLike]) -> dict[str, str]` (object name -> preset name), `PresetLike` having `id`, `name`, `spec` (`db.presets.Preset` satisfies it); trial-renders each template with `cache.naming.render_cache_name` twice with different `session` and `created_by` values (`preset=spec.slugify(name)`, `preset_id=str(id)`), equal output = a fixed name.
  - `legacy_copies(rows: Iterable[PinRow]) -> dict[str, int]` (`<from_key>.tar.zst` -> count).
  - `classify(name: str, pins: Mapping[str, tuple[str, ...]], presets: Mapping[str, str]) -> CacheClass`.
- Consumers: `reconciler/cache_requests.py` (task orch-cache-requests) and `api/cache.py` (task orch-cache-api).

#### Expected outcome

One importable rule decides which objects session rows pin and which class every object name has; the api badge and the reconciler refusal both call it, so they cannot disagree.

#### Steps

- Read `cache/save_rule.py` (the pure-module shape), `cache/naming.py`, `cache/presign.py` (`object_name`, `sessions_object_name`), `reconciler/cache_migration.py` (the `migration` record and the pending rule), `reconciler/cache.py` (where `key`, `object`, `sessions_object` are pinned), `spec.py` (`CACHE_KEY_RE`, `slugify`, `WorkspaceCache`), `db/sessions.py` (`Session`) and `db/presets.py` (`Preset`) in one pass.
- Red: write `tests/test_cache_pins.py` with every test named in the acceptance conditions (plain `Session`/`Preset` instances, no database); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_pins.py`; expect collection to fail on the missing module.
- Green: write `cache/pins.py`; rerun; expect all passed.
- `mise run lint`; expect exit 0.

#### Notes

- (my call) The class rule is structural: smoke objects whose names fit the scheme (for example `smoke-workspace-cache.tar.zst`, `sessions/smoke-123.tar.zst`) read `saved`; only keys outside the scheme read `other` (former open question Q7, settled as my call after the interrogate review; design Assumptions).
- Over-pinning is safe (a refusal), under-pinning loses data: when a field's shape is ambiguous, pin.
- No database read, no S3 call, no clock: everything comes in as arguments.
- These tests need no Postgres, so they run locally.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S2: orch cache tables

- Status: todo
- Files: `src/agents_orchestrator/db/migrations`, `tests/test_migrations.py`, `README.md`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_migrations.py && mise run lint  # DB-backed tests need Docker: CI only here`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

Design D1 (Reconciler-owned inventory table), verbatim: "`cache_objects` (key, kind, size, etag, last_modified, generation), written only by the reconciler: a full `list_objects_v2` pass every `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` (default 900) or at once on a refresh request, in its own asyncio task off the session pass (`asyncio.to_thread`, botocore paginator); a pass writes a new generation and drops the old one in one transaction. Alternatives: on-demand listing per view (up to 100 S3 calls per page view, no history); a credentialed component (forbidden). User Q3."

Design D2 (Delete and refresh requests through a guarded queue), the table part, verbatim: "`cache_requests` (id, kind `delete|refresh`, object, etag, size, status `queued|running|done|refused|failed`, reason, timestamps): the api inserts `queued` rows and notifies a new channel `cache_requested` [...]"

Design constraint, verbatim: "One SQL migration, numbered `<MIGRATION>` = next free at build time (expected 0016, after 0015 of decouple-s3-session-cache-fr; 0010 and 0012 are slash's, 0013 session-orchestration-mcp's, 0014 immediate-message-delivery-w's)."

User decision, verbatim: "Builds after both blockers land on main; the SQL migration number is the placeholder <MIGRATION>, resolved at build time exactly as /workdir/workdir/docs/plans/in-progress/hive-decoupling does".

This task delivers the schema of D1 and D2 in agents-orchestrator: one new SQL migration `src/agents_orchestrator/db/migrations/<MIGRATION>_cache_section.sql`, additive and idempotent like the earlier migrations, creating:

- `cache_listings` (my call: the listing state `GET /api/v1/cache` reports): `generation` bigserial primary key, `state` text NOT NULL CHECK in (`running`, `done`, `failed`), `reason` text, `objects` bigint, `bytes` bigint, `started_at` timestamptz NOT NULL DEFAULT now(), `finished_at` timestamptz. Written only by the reconciler.
- `cache_objects`: `generation` bigint NOT NULL REFERENCES `cache_listings` ON DELETE CASCADE, `key` text NOT NULL (the object name without `cache_s3_prefix`), `kind` text NOT NULL CHECK in (`workspace`, `transcripts`), `size` bigint NOT NULL CHECK >= 0, `etag` text NOT NULL, `last_modified` timestamptz NOT NULL, primary key (`generation`, `key`). Written only by the reconciler.
- `cache_requests`: `id` bigserial primary key, `kind` text NOT NULL CHECK in (`delete`, `refresh`), `object` text, `etag` text, `size` bigint, `status` text NOT NULL DEFAULT `queued` CHECK in (`queued`, `running`, `done`, `refused`, `failed`), `reason` text, `created_at` timestamptz NOT NULL DEFAULT now(), `started_at` timestamptz, `finished_at` timestamptz, and a CHECK that a `delete` row has `object` and `etag` and a `refresh` row has neither. The api inserts; the reconciler changes rows only through status-guarded updates.

README `## Data model` lists the three tables with their writers.

`<MIGRATION>` is a placeholder: before this task starts, the orchestrator session reads the highest migration number on agents-orchestrator main (after both blockers landed) and amends this task with the next free number through `ticket.py amend`, as hive-decoupling did. The migration test is named without the number.

Tests no longer accurate because they pin the applied migration list and a new migration exists; each gains the new version: tests/test_migrations.py::test_fresh_database_gets_all_tables (also gains the three tables), ::test_presets_migration_on_existing_sessions, ::test_concurrent_migrate_serialises and ::test_0005_renames_clusters_to_sessions.

#### Acceptance conditions

- AC1: the migration `<MIGRATION>_cache_section.sql` creates cache_listings, cache_objects and cache_requests with the columns, defaults and keys of the Requirement [evidence: test:tests/test_migrations.py::test_cache_section_migration]
- AC2: the constraints refuse a delete request without object or etag, a refresh request with an object, an unknown status or kind, an unknown object kind and a negative size, and deleting a listing cascades to its objects [evidence: test:tests/test_migrations.py::test_cache_section_constraints]
- AC3: running the migration SQL again changes nothing [evidence: test:tests/test_migrations.py::test_cache_section_migration_idempotent]
- AC4: a fresh database gets every migration including the new one and the three tables [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- AC5: README Data model lists the three tables [evidence: command:grep -q '`cache_listings`' README.md && grep -q '`cache_objects`' README.md && grep -q '`cache_requests`' README.md]
- AC6: lint passes [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/db/migrations`
- `tests/test_migrations.py`
- `README.md`

#### Interfaces

- `src/agents_orchestrator/db/migrations/<MIGRATION>_cache_section.sql` (new; `<MIGRATION>` amended to the next free number on main before the task starts).
- Tables and columns exactly as the Requirement; index choices are the builder's (a partial index on `cache_requests (kind, id) WHERE status IN ('queued', 'running')` suits the claims).
- Writers (README Data model): `cache_listings` and `cache_objects` the reconciler only; `cache_requests` inserted by the api, status changed only by the reconciler through `WHERE status = ...` updates.

#### Expected outcome

`orch migrate` on a database at the blockers' schema adds the three tables; a second run changes nothing; the following tasks have their schema.

#### Steps

- Read `db/migrate.py`, the newest migrations on main (including the blockers'), `db/migrations/0001_init.sql` (the `checks` table, the queue pattern) and `tests/test_migrations.py` (`run_migrations`, `empty_dsn`, the tmp_path copy pattern of `test_drop_feed_cursor_migration`) in one pass; confirm `<MIGRATION>` was amended to a number and is still the next free one.
- Red: add the three new tests named in the acceptance conditions and the new version (and tables) to the four list-pinning tests named in the Requirement; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_migrations.py`; expect failures on the missing migration (DB tests: on CI or a local Postgres).
- Green: write the SQL file and the README Data model rows; rerun; expect passed.
- `mise run lint`; expect exit 0.

#### Notes

- If `<MIGRATION>` still reads as a placeholder when the task starts, stop and return it as a question; never pick a number yourself.
- The migration only creates tables: no data, no S3, nothing irreversible.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
- (my call) Builder check Q2: the orchestrator session amends `<MIGRATION>` to the next free number on agents-orchestrator main through `ticket.py amend`, after both blockers landed and before this task is dispatched.

- 2026-10-29 amended: design constraint quote follows the design: expected 0016 (mx-34 #469/#470)

### S3: orch cache inventory

- Status: todo
- Files: `src/agents_orchestrator/settings.py`, `src/agents_orchestrator/cache/presign.py`, `src/agents_orchestrator/db/cache.py`, `src/agents_orchestrator/reconciler/cache_inventory.py`, `src/agents_orchestrator/reconciler/loop.py`, `README.md`, `MEMORY.md`, `tests/test_cache_inventory.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_inventory.py tests/test_cache_presign.py tests/test_settings.py && mise run lint  # DB-backed tests need Docker: CI only here; the list_bucket, presign and settings tests run locally`
- Verified head: none

#### Requirement

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

Review fix (interrogate 2026-10-29, act on 1: refresh request stuck `running`): a pass also takes every `refresh` request already `running` when it starts (left by a previous process or a pass stopped mid-listing; one active reconciler holds `advisory_singleton(dsn, "reconciler")`, so no other pass owns it), re-runs the listing for it and completes it `done` or `failed` exactly like a freshly claimed one, as the delete runner does for `running` deletes (orch-cache-requests AC7). A refresh request never stays `running` past the next pass, so `refresh_pending` clears and Refresh works again after a reconciler restart.

Review fix (interrogate 2026-10-29, act on 2: S3 errors and hangs): the S3 client is bounded. `presign._client` builds its botocore `Config` with `connect_timeout=S3_CONNECT_TIMEOUT_SECONDS` (5), `read_timeout=S3_READ_TIMEOUT_SECONDS` (30) and `retries={"mode": "standard", "total_max_attempts": S3_MAX_ATTEMPTS}` (2), module constants in `cache/presign.py` (my call values; presigning makes no network call, so presigned URLs are unchanged); the listing and the delete executor (orch-cache-requests) both use this one client. Every listing pass is wrapped: a `ClientError` fails the listing with `<Error.Code> <HTTP status>` as above, and any other exception (a connection error, a read timeout, anything else) fails the listing with the exception class name as reason (for example `EndpointConnectionError`, `ReadTimeoutError`), keeps the previous generation current and fails the claimed refresh requests with that reason. `CacheInventory.run` never ends on a pass error (only on stop or cancellation): it logs and runs the next pass on schedule.

#### Acceptance conditions

- AC1: list_bucket returns every object under the prefix across more than one listing page with name (prefix stripped), kind, size, etag and last_modified, and leaves out keys outside the prefix [evidence: test:tests/test_cache_inventory.py::test_list_bucket_pages_and_strips_prefix]
- AC2: a pass writes a new generation, marks its listing done with object and byte totals and drops every older generation in one transaction [evidence: test:tests/test_cache_inventory.py::test_pass_swaps_generation_atomically]
- AC3: a listing error marks the listing failed with a reason holding the S3 error code and status and no access key, secret or URL, and the previous generation stays current [evidence: test:tests/test_cache_inventory.py::test_listing_failure_keeps_previous_generation]
- AC4: a queued refresh request is claimed by the next pass and ends done (failed with the reason when the listing fails); a request already done or failed is untouched [evidence: test:tests/test_cache_inventory.py::test_refresh_request_runs_a_pass]
- AC5: no second pass runs before ORCH_CACHE_INVENTORY_INTERVAL_SECONDS has passed, one runs after it, and a queued refresh runs one at once [evidence: test:tests/test_cache_inventory.py::test_interval_and_refresh_schedule_passes]
- AC6: an object whose delete request finished done after the pass started is not in the new generation [evidence: test:tests/test_cache_inventory.py::test_delete_during_pass_stays_deleted]
- AC7: CHANNELS holds cache_requested, Reconciler.run starts the inventory task only with the cache configured, and reconcile_once makes no S3 call [evidence: test:tests/test_cache_inventory.py::test_reconciler_runs_inventory_off_the_session_pass]
- AC8: ORCH_CACHE_INVENTORY_INTERVAL_SECONDS defaults to 900 and refuses values outside 60 to 86400 [evidence: test:tests/test_cache_inventory.py::test_inventory_interval_setting]
- AC9: every setting is documented in the README [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- AC10: README documents the channel and the inventory, MEMORY.md records it [evidence: command:grep -q "cache_requested" README.md && grep -q "### Cache inventory" README.md && grep -qi "cache inventory" MEMORY.md]
- AC11: lint passes [evidence: command:mise run lint]
- AC12: a refresh request left running by a stopped pass (refresh_pending true) is re-run by the next pass of a new CacheInventory and ends done, or failed with the reason when the listing fails, and refresh_pending reads false after it (interrogate act on 1) [evidence: test:tests/test_cache_inventory.py::test_running_refresh_resumed_by_next_pass]
- AC13: a connection error and a hang (an endpoint that accepts and never answers, timeouts lowered in the test) during the listing end the listing failed with the exception class name as reason within the client's bound, keep the previous generation current, fail the claimed refresh requests, and the inventory task runs its next pass (interrogate act on 2) [evidence: test:tests/test_cache_inventory.py::test_listing_connection_error_and_hang_fail_the_pass]
- AC14: presign._client builds its S3 client with connect_timeout S3_CONNECT_TIMEOUT_SECONDS, read_timeout S3_READ_TIMEOUT_SECONDS and at most S3_MAX_ATTEMPTS total attempts (interrogate act on 2) [evidence: test:tests/test_cache_inventory.py::test_s3_client_has_bounded_timeouts_and_retries]

#### Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/cache/presign.py`
- `src/agents_orchestrator/db/cache.py`
- `src/agents_orchestrator/reconciler/cache_inventory.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `README.md`
- `MEMORY.md`
- `tests/test_cache_inventory.py`

#### Interfaces

- `settings.py`: `cache_inventory_interval_seconds: int = Field(default=900, ge=60, le=86400)`.
- `src/agents_orchestrator/db/cache.py` (new): `Listing` (generation, state, reason, objects, bytes, started_at, finished_at), `ListedObject` (key, kind, size, etag, last_modified); `begin_listing(conn) -> int`, `finish_listing(conn, generation, objects: Sequence[ListedObject]) -> None` (one transaction: insert, mark done with totals, drop older generations, drop keys deleted since `started_at`), `fail_listing(conn, generation, reason) -> None`, `current_listing(conn) -> Listing | None` (newest `done`), `latest_listing(conn) -> Listing | None` (newest of any state), `claim_refreshes(conn) -> list[int]` (claims every `queued` refresh `queued->running` and returns those ids plus every refresh already `running`, left by a previous process; review fix, interrogate act on 1), `complete_refreshes(conn, ids, status, reason) -> None`. Later tasks add the delete and api functions here.
- `src/agents_orchestrator/reconciler/cache_inventory.py` (new): `list_bucket(settings: Settings) -> list[ListedObject]` (synchronous), `class CacheInventory(pool, settings, clock=time.monotonic)` with `async run_once() -> None` and `async run(stop: asyncio.Event, wake: asyncio.Event) -> None`.
- `reconciler/loop.py`: `CHANNELS = ("session_changed", "cache_requested")`; `Reconciler.inventory` built when `settings.cache_available`.
- `cache/presign.py`: `S3_CONNECT_TIMEOUT_SECONDS = 5`, `S3_READ_TIMEOUT_SECONDS = 30`, `S3_MAX_ATTEMPTS = 2`, used in the `_client` `Config` (review fix, interrogate act on 2); tests lower them and call `_client.cache_clear()`.
- The ETag is stored exactly as S3 returns it (HEAD returns the same form), so the delete executor compares like with like.

#### Expected outcome

With the cache configured, the reconciler keeps `cache_objects` at most `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` old, lists again at once on a refresh request, keeps the last good listing when S3 fails, and never lists from a page view or the session pass.

#### Steps

- Read `cache/presign.py` (`_client`), `cache/pins.py` (`object_kind`), `reconciler/loop.py` (`CHANNELS`, `run`, `reconcile_once`), `reconciler/checks.py` (claim pattern), `db/queue.py` (`claim_check`, `complete_check`), `db/pool.py`, `settings.py` (cache fields), the new migration, `tests/test_cache_presign.py` (ThreadedMotoServer fixture, `_no_ambient_aws`) and `tests/test_checks.py` (pool env) in one pass.
- Red: write `tests/test_cache_inventory.py` with every test named in the acceptance conditions (moto server for the bucket, `pool` for the tables, an injected clock for the schedule); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_inventory.py`; expect failure on the missing modules (DB tests: on CI or a local Postgres; the list_bucket and settings tests run locally).
- Green: write the setting, `db/cache.py`, `reconciler/cache_inventory.py` and the loop wiring; rerun the verify; expect passed.
- Write the README rows and subsection and the MEMORY.md entry; `mise run lint`; expect exit 0.

#### Notes

- Paging: set the paginator's page size small in the test (or create more than 1000 objects) so more than one page is proven.
- Write the rows in batches (`executemany` or COPY) inside the one transaction; the bucket allows 100000 objects.
- Inventory size well under 100000 rows and a pass under 60 s are assumptions (design "Assumptions"); log the pass duration and object count once per pass so the live check can confirm them.
- Per-task security check (retro, recurring): no credential, signature or presigned URL in any log line, listing reason or exception message that reaches the database.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate 2026-10-29 act on 1, 2
- (my call) Builder check Q9: keep the `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` bounds at 60 to 86400.

### S4: orch cache requests

- Status: todo
- Files: `src/agents_orchestrator/reconciler/cache_requests.py`, `src/agents_orchestrator/db/cache.py`, `src/agents_orchestrator/reconciler/loop.py`, `README.md`, `MEMORY.md`, `tests/test_cache_requests.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_requests.py && mise run lint  # DB-backed tests need Docker: CI only here`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G3, verbatim: "a user deletes one object after typing its name; the orchestrator's reconciler refuses an object pinned by any session row (live, starting or discarding) or rewritten since it was listed, and the outcome (done, refused with reason, failed with reason) is shown."

README Goal G4, verbatim: "S3 credentials stay on the reconciler only; the new routes are on the web port only (not the agent or service ports)."

Design D2 (Delete and refresh requests through a guarded queue), verbatim: "`cache_requests` (id, kind `delete|refresh`, object, etag, size, status `queued|running|done|refused|failed`, reason, timestamps): the api inserts `queued` rows and notifies a new channel `cache_requested` (added to the reconciler's `CHANNELS`); the reconciler claims `queued->running` and executes inside its sequential pass, so no restore, save, backup or migration Job it starts can begin between check and delete: (1) refuse `in_use` per `cache.pins` over every existing session row; (2) HEAD: 404 -> `done/gone`, ETag differs -> `refused/changed`; (3) `delete_object(Key, IfMatch=etag)`, 412 -> `refused/changed`; success removes the inventory row, then `done`. An S3 403 or other error -> `failed` with the reason. The api's own 409 `in_use` check is advisory. If-Match is a backup guard (RGW release unknown; HEAD plus ETag under the single-writer reconciler is the real one). User Q1, Q6."

Design D8 (Relation to the cleanup epic), verbatim: "This epic lists old copies and deletes them one at a time on explicit action. The cleanup epic keeps bulk deletion of proven-copied objects (it needs a durable copy record, because migration records vanish with discarded rows) and will run its deletes as `cache_requests` rows: one executor, one refusal rule. User Q2."

Design anti-goal, verbatim: "Deleting an object a session row pins (live, starting, unconverged or discarding), or one rewritten since the user saw it."

Cartographer plan input (fix-as-ac), verbatim: "deleting an object pinned by a live session (`status.cache.key/object/sessions_object`) or mid-save (`save`/`sessions_save`/`sessions_backup` running) must be refused by the reconciler at execution time."

Open questions Q1 and Q6 are planned on their recommended answers (user decision: "Q1-Q6 in design.md are open; plan on the recommended answers").

This task delivers the executor of D2 in agents-orchestrator, new module `src/agents_orchestrator/reconciler/cache_requests.py`:

- `CacheRequestRunner.run_once()` runs inside `Reconciler.reconcile_once`, right after `self.checks.run_once()` and before the session loop, only when `settings.cache_available`. It first finishes any `delete` request left `running` by a pass that stopped mid-request, then claims queued `delete` requests one at a time, oldest first, `queued->running` with a status-guarded update, until none is left.
- Per request: (1) read every existing session row (`sessions.list_sessions`, every `desired`) and refuse with reason `in_use: <sorted slugs>` when `cache.pins.pins_by_object` names the object; (2) HEAD `<prefix><object>`: 404 -> `done` with reason `gone` and the object's inventory rows removed; an ETag different from the request's -> `refused` with reason `changed`; (3) `delete_object(Bucket, Key, IfMatch=etag)`: 412 -> `refused` with reason `changed`; success removes the object's inventory rows, then `done`. Any other S3 error, including 403 -> `failed` with reason `<Error.Code> <HTTP status>`. No reason or log line holds a credential, signature or URL.
- S3 calls run with `asyncio.to_thread` through the one `presign._client`; no other module calls `delete_object`.
- Every completion is `UPDATE ... WHERE id = %s AND status = 'running'`.
- README `## Workspace cache` gains `### Cache deletes` (the refusal rules and outcomes, and that the cleanup epic reuses this executor); MEMORY.md gains a dated entry (why deletes run in the reconciler pass; HEAD plus ETag as the guard, If-Match as backup).

Review fix (interrogate 2026-10-29, act on 2: S3 errors and hangs block the whole reconcile pass): every request is wrapped. Any exception while executing a request (a connection error, a read timeout, an error from `cache.pins` or from reading the session rows, anything other than cancellation) ends that request `failed` with the exception class name as reason (for example `EndpointConnectionError`, `ReadTimeoutError`); a `ClientError` keeps the `<Error.Code> <HTTP status>` reason above. `CacheRequestRunner.run_once` never raises out of the runner (only `asyncio.CancelledError` propagates): a failure outside a request is logged and the runner returns, so `reconcile_once` always reaches the session loop in the same pass. HEAD and `delete_object` use the bounded client of `presign._client` (connect and read timeouts and a retry bound, added by orch-cache-inventory), so a hung RGW ends the request `failed` within that bound instead of stalling every pass.

#### Acceptance conditions

- AC1: a delete is refused in_use, naming the slug, for an object pinned by a live row's status.cache.key, object or sessions_object, by spec.cache.key of a row never restored, by a row in desired deleting, and by a row whose save, sessions_save or sessions_backup run is running; the object is still in the bucket [evidence: test:tests/test_cache_requests.py::test_pinned_objects_refused_at_execution]
- AC2: an object whose ETag differs from the request's is refused changed and kept [evidence: test:tests/test_cache_requests.py::test_changed_object_refused]
- AC3: an object already gone ends done with reason gone and its inventory row removed [evidence: test:tests/test_cache_requests.py::test_missing_object_done_gone]
- AC4: an unpinned, unchanged object is deleted from the bucket with IfMatch set to the request's ETag, its inventory row removed, and the request ends done [evidence: test:tests/test_cache_requests.py::test_unpinned_object_deleted]
- AC5: a 412 from delete_object ends refused changed [evidence: test:tests/test_cache_requests.py::test_if_match_failure_refused_changed]
- AC6: a 403 or other S3 error ends failed with a reason naming the error code and status and holding no access key, secret or URL [evidence: test:tests/test_cache_requests.py::test_s3_error_fails_without_secrets]
- AC7: a delete request left running is executed by the next pass, completes exactly once, and a request no longer running is never completed again [evidence: test:tests/test_cache_requests.py::test_running_request_resumed_and_completed_once]
- AC8: reconcile_once executes queued deletes before converging any session, and does nothing with the cache unconfigured [evidence: test:tests/test_cache_requests.py::test_reconcile_pass_executes_deletes_first]
- AC9: only the reconciler's request module calls delete_object [evidence: command:test "$(grep -rl delete_object src/agents_orchestrator)" = "src/agents_orchestrator/reconciler/cache_requests.py"]
- AC10: the refusal uses cache.pins and carries no second copy of the pin fields [evidence: command:grep -q "pins_by_object" src/agents_orchestrator/reconciler/cache_requests.py && ! grep -nE "sessions_object|from_key" src/agents_orchestrator/reconciler/cache_requests.py]
- AC11: README documents the deletes and MEMORY.md records the guard [evidence: command:grep -q "### Cache deletes" README.md && grep -qE "If-Match|IfMatch" MEMORY.md]
- AC12: lint passes [evidence: command:mise run lint]
- AC13: a connection error and a hang (an endpoint that accepts and never answers, timeouts lowered in the test) on HEAD or delete_object end the request failed with the exception class name as reason, and the session loop still converges a session in the same reconcile_once pass (interrogate act on 2) [evidence: test:tests/test_cache_requests.py::test_s3_connection_error_and_hang_fail_request_and_pass_continues]
- AC14: any other exception while executing a request (for example raised by cache.pins) ends it failed with the exception class name as reason, the next queued request still runs, and run_once does not raise (interrogate act on 2) [evidence: test:tests/test_cache_requests.py::test_any_request_exception_ends_failed_without_raising]

#### Files

- `src/agents_orchestrator/reconciler/cache_requests.py`
- `src/agents_orchestrator/db/cache.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `README.md`
- `MEMORY.md`
- `tests/test_cache_requests.py`

#### Interfaces

- `src/agents_orchestrator/reconciler/cache_requests.py` (new): `class CacheRequestRunner(pool, settings)` with `async run_once() -> None`; reasons `in_use: <slugs>`, `changed`, `gone`, `<Error.Code> <HTTP status>`, and the exception class name for any other exception (review fix, interrogate act on 2); `run_once` never raises except `asyncio.CancelledError`.
- `db/cache.py` gains `CacheRequest` (id, kind, object, etag, size, status, reason, created_at, started_at, finished_at), `running_deletes(conn) -> list[CacheRequest]`, `claim_delete(conn) -> CacheRequest | None` (`UPDATE ... SET status='running', started_at=now() WHERE id = (SELECT id ... WHERE kind='delete' AND status='queued' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED) AND status='queued' RETURNING ...`), `complete_request(conn, id, status, reason) -> bool` (guarded on `running`), `drop_object(conn, key) -> None` (every generation's row of that key).
- `reconciler/loop.py`: `Reconciler.cache_requests` built when `settings.cache_available`; `reconcile_once` calls it after `self.checks.run_once()`.
- Uses `cache.pins.pins_by_object(rows, settings.cache_s3_prefix)` and `presign._client(...)`; never imports from `api`.

#### Expected outcome

A queued delete request is executed by the reconciler within one pass: refused when any session row pins the object or it changed since listing, done when deleted or already gone, failed with the S3 reason otherwise; the cleanup epic can queue its deletes into the same table and get the same rules.

#### Steps

- Read `reconciler/loop.py` (`reconcile_once`, wiring), `reconciler/checks.py` (`CheckRunner` claim and observe), `reconciler/cache_inventory.py`, `db/cache.py`, `db/sessions.py` (`list_sessions`), `cache/pins.py`, `cache/presign.py` (`_client`), `cache/copy.py` (ClientError handling of HEAD), `tests/test_cache_presign.py` and `tests/test_cache_inventory.py` (moto and pool fixtures) in one pass.
- Red: write `tests/test_cache_requests.py` with every test named in the acceptance conditions (moto server for the bucket; `botocore.stub.Stubber` or a patched client for the 412 and 403 cases; rows inserted as the api will insert them); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_requests.py`; expect failure on the missing module (DB tests: on CI or a local Postgres).
- Green: write the module, the `db/cache.py` functions and the loop wiring; rerun the verify; expect passed.
- Write README `### Cache deletes` and the MEMORY.md entry; `mise run lint`; expect exit 0.

#### Notes

- The bucket keeps no versions: a delete is permanent (design Constraints, Q1). Under-refusing is the failure to avoid; when unsure, refuse.
- `head_object` raises `botocore.exceptions.ClientError`; read `error.response["Error"]["Code"]` and `ResponseMetadata.HTTPStatusCode`; 404 is `"404"`/`NoSuchKey`. HEAD answers 403 instead of 404 without `s3:ListBucket`; that is `failed`, never `gone`.
- moto 5.2.4 honours `IfMatch` on DeleteObject (architecture sources); the deployed RGW release may ignore it, which is why the HEAD comparison is the real guard.
- Accepted race (architecture): a session the api creates between the check and the delete restores `miss` and starts empty.
- Per-task security check (retro, recurring): the object name comes from a user; it is used only as `<prefix><object>` in a Key parameter (never a path or a shell), and no credential, signature or URL reaches a reason, a log line or an exception stored in the database.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate 2026-10-29 act on 2
- (my call) Builder check Q8: treat the reconciler as one active process: `orch reconciler` runs inside `advisory_singleton(dsn, "reconciler")` with extra replicas as hot standbys (agents-orchestrator README.md:105), so a `running` delete at pass start was left by a previous process; the guarded completion keeps a double run safe anyway (HEAD 404 -> `done/gone`).

### S5: orch cache api

- Status: todo
- Files: `src/agents_orchestrator/api/cache.py`, `src/agents_orchestrator/api/app.py`, `src/agents_orchestrator/api/schemas.py`, `src/agents_orchestrator/db/cache.py`, `src/agents_orchestrator/settings.py`, `README.md`, `openapi.json`, `tests/test_api_cache_section.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_api_cache_section.py tests/test_readme_api.py tests/test_settings.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint  # DB-backed tests need Docker: CI only here; readme, openapi, settings, gate and layering tests run locally`
- Verified head: none

#### Requirement

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

#### Acceptance conditions

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

#### Files

- `src/agents_orchestrator/api/cache.py`
- `src/agents_orchestrator/api/app.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/db/cache.py`
- `src/agents_orchestrator/settings.py`
- `README.md`
- `openapi.json`
- `tests/test_api_cache_section.py`

#### Interfaces

- `src/agents_orchestrator/api/cache.py` (new): `router = APIRouter(prefix="/api/v1/cache")`; errors through `ApiError(status, code, message)`.
- `api/schemas.py`: `CacheQuota`, `CacheTotals`, `CacheListing`, `CacheSummary`, `CacheObjectView` (the JSON field `class`, a Python alias), `CacheObjectsPage`, `DeleteCacheObject`, `CacheRequestView`. These schema names are what agents-web imports after `sync:api` (task web-cache-client).
- `db/cache.py` gains `enqueue_delete(conn, object, etag, size) -> CacheRequest`, `enqueue_refresh(conn) -> CacheRequest` (returns the open one when present), `get_request(conn, id) -> CacheRequest | None`, `listed_object(conn, key) -> ListedObject | None` (current generation), `list_objects(conn, ...)` and `totals(conn)`; inserts notify `cache_requested` with `{request_id}` through `db.pool.notify` in the same transaction.
- `settings.py`: `cache_quota_bytes: int | None = Field(default=None, ge=1)`, `cache_quota_objects: int | None = Field(default=None, ge=1)`.
- Reads session rows with `sessions.list_sessions` and presets with `presets.list_presets`, classifies with `cache.pins` (`pins_by_object`, `preset_objects`, `legacy_copies`, `classify`).

#### Expected outcome

The web port serves a classified, paged, searchable view of the inventory, the quota and listing state, and accepts delete and refresh requests the reconciler executes; nothing new is reachable from agent or service tokens and the api still holds no S3 credential.

#### Steps

- Read `api/app.py`, `api/messages.py` (the checks routes: insert plus notify, 202), `api/streams.py` (`EventsPage` paging), `api/schemas.py`, `api/errors.py`, `api/service_auth.py`, `api/allowlist.py` (`PortGate`), `db/cache.py`, `db/sessions.py`, `db/presets.py`, `cache/pins.py`, `settings.py`, README `## API` and `## Workspace cache`, `tests/test_api_sessions.py` (`client_for`, `make_settings`, `assert_error`), `tests/test_service_port.py` and `tests/test_agent_port.py` in one pass.
- Red: write `tests/test_api_cache_section.py` with every test named in the acceptance conditions (rows inserted into `cache_listings`/`cache_objects` directly, as the reconciler writes them); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_api_cache_section.py tests/test_readme_api.py`; expect failures on the missing routes (DB tests: on CI or a local Postgres; the route-gate, settings, README and openapi tests run locally).
- Green: write the router, schemas, `db/cache.py` functions and settings; add the README route entries and settings rows; regenerate `openapi.json`; rerun the verify; expect passed.
- `mise run lint`; expect exit 0.

#### Notes

- Keep a page bounded: filter by class and name in SQL over the current generation (the `in_use` and `preset` names are small arrays from `cache.pins`; `legacy`, `saved` and `other` are key patterns taken from the `cache.pins` constants `LEGACY_RE` and `SAVED_RE`, never written in `api/cache.py`; review fix, interrogate act on 3), reading at most `limit + 1` rows per request; never load the whole table for one page (the bucket allows 100000 objects).
- `test_api_cache.py` belongs to decouple-s3-session-cache-fr; this task's tests live in `tests/test_api_cache_section.py`.
- The 409 `in_use` check is advisory: the reconciler re-checks at execution (task orch-cache-requests).
- Per-task security check (retro, recurring): bound every user input (object 1024, etag 256, q 256, limit 500); the object is never a path; error messages name slugs but never a credential or URL; confirm the gate test hits the service port with a valid token.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate 2026-10-29 act on 3
- (my call) Builder check Q7 is superseded by interrogate act on 3: the SQL filter uses the `cache.pins` patterns as Postgres `~` parameters, and AC19 pins its agreement with `classify`; there is no second Python-only path.

### S6: orch chart cache quota

- Status: todo
- Files: `chart/agents-orchestrator/values.yaml`, `chart/agents-orchestrator/templates/configmap.yaml`, `chart/agents-orchestrator/README.md`, `tests/test_chart_cache.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_chart_cache.py && mise run lint:chart && mise run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G5, verbatim: "a quota gauge shows bytes and objects against the bucket quota set in agents-helmfile; released and deployed, and proven live by listing the bucket and deleting one disposable object."

Design D7 (Quota settings), verbatim: "`ORCH_CACHE_QUOTA_BYTES` and `ORCH_CACHE_QUOTA_OBJECTS` (default unset, gauge hidden), set in agents-helmfile values from the OBC quota (100G, 100000). User Q4."

Architecture brief, verbatim: "Quota: settings `ORCH_CACHE_QUOTA_BYTES`, `ORCH_CACHE_QUOTA_OBJECTS` (chart default null, gauge hidden), set in agents-helmfile next to the OBC."

This task delivers the chart part of D7 in agents-orchestrator: chart values `cache.quota.bytes` and `cache.quota.objects` (default null); the settings ConfigMap renders `ORCH_CACHE_QUOTA_BYTES` and `ORCH_CACHE_QUOTA_OBJECTS` as exact integer strings only when each is set and the bucket is set (the ConfigMap reaches every component, so the api reads them); the chart README documents both values; the S3 credentials stay on the reconciler container only.

tests/test_chart_cache.py::test_readme_documents_cache_values lists every documented cache value, so it gains `cache.quota.bytes` and `cache.quota.objects` (extended, not weakened).

#### Acceptance conditions

- AC1: with cache.quota.bytes and cache.quota.objects set, the settings ConfigMap carries ORCH_CACHE_QUOTA_BYTES and ORCH_CACHE_QUOTA_OBJECTS and the api Deployment reads that ConfigMap [evidence: test:tests/test_chart_cache.py::test_configmap_cache_quota_env]
- AC2: with the quota unset, or without a bucket, neither variable is rendered [evidence: test:tests/test_chart_cache.py::test_no_quota_no_env]
- AC3: a quota of 100000000000 bytes renders as the exact string "100000000000", never a float or an exponent [evidence: test:tests/test_chart_cache.py::test_quota_renders_large_integers]
- AC4: the S3 credentials are still on the reconciler container only [evidence: test:tests/test_chart_cache.py::test_credentials_only_on_reconciler]
- AC5: the chart README documents the cache values including cache.quota.bytes and cache.quota.objects [evidence: test:tests/test_chart_cache.py::test_readme_documents_cache_values]
- AC6: chart lint and lint pass [evidence: command:mise run lint:chart && mise run lint]

#### Files

- `chart/agents-orchestrator/values.yaml`
- `chart/agents-orchestrator/templates/configmap.yaml`
- `chart/agents-orchestrator/README.md`
- `tests/test_chart_cache.py`

#### Interfaces

- `chart/agents-orchestrator/values.yaml`: under `cache`, `quota: {bytes: null, objects: null}` with comments (bucket total quota shown by the web Cache section gauge; null hides the gauge).
- `chart/agents-orchestrator/templates/configmap.yaml`: inside the existing `cache.s3.bucket` block, `ORCH_CACHE_QUOTA_BYTES: {{ .quota.bytes | int64 | toString | quote }}` when set, same for objects.
- Settings consumed: `cache_quota_bytes`, `cache_quota_objects` (task orch-cache-api).

#### Expected outcome

agents-helmfile can set the quota through `cache.quota` values, and the api's `GET /api/v1/cache` reports it; an unset quota renders nothing and the gauge stays hidden.

#### Steps

- Read `chart/agents-orchestrator/values.yaml` (cache block), `templates/configmap.yaml`, `templates/deployment.yaml` (envFrom per component), the chart README and `tests/test_chart_cache.py` (`render`, `_settings`, `_deployments`) in one pass.
- Red: add `test_configmap_cache_quota_env`, `test_no_quota_no_env` and `test_quota_renders_large_integers`; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_chart_cache.py`; expect the three to fail.
- Green: add the values, the template lines and the README rows; rerun; expect passed; `mise run lint:chart && mise run lint`; expect exit 0.

#### Notes

- Retro (matrix-connector-agent-initi): a chart value that reaches only some containers passed every test and failed live; AC1 asserts the api Deployment actually reads the settings ConfigMap.
- Helm reads large YAML integers as float64; `int64 | toString` is the existing pattern (`ORCH_CACHE_MAX_BYTES`).
- These tests render with the local helm binary and need no Postgres, so they run locally.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S7: web cache client

- Status: todo
- Files: `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts`, `src/api/client.ts`, `src/api/client.test.ts`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/api/client.test.ts && npm run check:api && npm run build && npm run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

Design D5 (API on the web port only), verbatim: "`GET /api/v1/cache` (available, prefix, listed_at, listing state, totals, quota), `GET /api/v1/cache/objects` (`class`, `q`, `after`, `limit<=500`, ordered by key), `POST /api/v1/cache/deletions {object, etag}` 202 (404 not listed, 409 `in_use`, 503 `cache_not_configured`), `POST /api/v1/cache/refresh` 202, `GET /api/v1/cache/requests/{id}`. Not in `service_auth.ALLOWED_ROUTES`, not on the agent port. README route table, `openapi.json`, web `sync:api`."

This task delivers the agents-web side of D5's `sync:api`: `npm run sync:api -- orchestrator` from the agents-orchestrator commit that carries the cache routes (openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts), and typed functions in `src/api/client.ts` for the five routes with exported types `CacheSummary`, `CacheObjectView`, `CacheObjectsPage`, `CacheRequestView`, `DeleteCacheObject` and `CacheClass`. Errors come back as the existing `ApiError` with status and code (for example 409 `in_use`, 404 `not_listed`, 503 `cache_not_configured`).

#### Acceptance conditions

- AC1: the vendored schema carries the cache routes and agrees with src/api/schema.d.ts [evidence: command:grep -q '"/api/v1/cache/objects"' openapi/orchestrator.json && npm run check:api]
- AC2: getCache, listCacheObjects (class, q, after, limit as query parameters), requestCacheDeletion (POST body object and etag), refreshCache and getCacheRequest call the orchestrator base with the right method, path and body [evidence: test:src/api/client.test.ts::cache_routes_paths_and_bodies]
- AC3: a 409 in_use, 404 not_listed or 503 cache_not_configured answer throws ApiError with that status and code [evidence: test:src/api/client.test.ts::cache_errors_carry_status_and_code]
- AC4: the client suite, the type check of the build and lint pass [evidence: command:npx vitest run src/api/client.test.ts && npm run build && npm run lint]

#### Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`
- `src/api/client.ts`
- `src/api/client.test.ts`

#### Interfaces

- `src/api/client.ts`: `type CacheSummary = S['CacheSummary']`, `CacheObjectView`, `CacheObjectsPage`, `CacheRequestView`, `DeleteCacheObject`, `type CacheClass = 'in_use' | 'preset' | 'legacy' | 'saved' | 'other'`; `getCache(): Promise<CacheSummary>`, `listCacheObjects(params: { class?: CacheClass; q?: string; after?: string; limit?: number }): Promise<CacheObjectsPage>`, `requestCacheDeletion(object: string, etag: string): Promise<CacheRequestView>`, `refreshCache(): Promise<CacheRequestView>`, `getCacheRequest(id: number): Promise<CacheRequestView>`; all through the existing `request` and `query` helpers.
- Schema names come from agents-orchestrator `api/schemas.py` (task orch-cache-api).

#### Expected outcome

agents-web has a typed client for the cache routes, generated from the orchestrator's committed openapi.json, ready for the Cache section.

#### Steps

- Read `scripts/sync-api.mjs`, `src/api/client.ts` and `src/api/client.test.ts` in one pass; confirm `../agents-orchestrator` (the integration tree) is at the commit carrying the cache routes.
- `npm ci --no-audit --no-fund`; `npm run sync:api -- orchestrator`; expect openapi/orchestrator.json, openapi/orchestrator.source and src/api/schema.d.ts to change and `npm run check:api` to exit 0.
- Red: add `cache_routes_paths_and_bodies` and `cache_errors_carry_status_and_code` to `src/api/client.test.ts`; run `npx vitest run src/api/client.test.ts`; expect failures on the missing functions.
- Green: add the types and functions; rerun; expect passed; `npm run build && npm run lint`; expect exit 0.

#### Notes

- Retro (matrix-connector-agent-initi, deploy-safe-agent-sessions): `openapi/orchestrator.source` pinned an epic-branch commit twice, and the orchestrator PR then had to merge with a merge commit so that sha stayed reachable. Sync from the orchestrator commit that will be on main (merge the agents-orchestrator PR first when possible); otherwise record in the task Notes that the orchestrator PR must merge with a merge commit.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main; both edit `src/sessions/DiscardSessionDialog.tsx`, the openapi files and `src/api/schema.d.ts` before this epic. Read the landed files first.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring; agents-web has a known load-dependent vitest timeout in PresetForm `name_rules_default_name_and_pvc`).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes, no colour literals, decorative Unicode or off-grid spacing (`layout/designRules.ts`), never the word "cluster" (`nomenclature.test.ts`). No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
- (my call) Builder check Q4: the agents-orchestrator epic PR merges to main first; `sync:api` runs from that main sha, never from the epic integration branch, so no merge-commit requirement arises.

### S8: web cache section

- Status: todo
- Files: `src/backends/registry.ts`, `src/backends/registry.test.ts`, `src/cache/CachePage.tsx`, `src/cache/DeleteCacheObjectDialog.tsx`, `src/cache/CachePage.test.tsx`, `src/layout/formatBytes.ts`, `src/layout/formatBytes.test.ts`, `src/sessions/DiscardSessionDialog.tsx`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/cache src/backends/registry.test.ts src/layout/formatBytes.test.ts src/sessions/DiscardSessionDialog.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && npm run build && npm run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goals, verbatim:
- G1: "agents-web has a Cache section in the orchestrator menu (beside Sessions and Presets) listing every object under the cache prefix with object name, kind (workspace or transcripts), class, size and last modified, filterable by class and searchable by name, paged."
- G2: "each object's class is current on every view: `in_use` (with the session slugs), `preset` (with the preset name), `legacy` (old `preset-*` copy, with how many live sessions copied it), `saved` or `other`; the object list itself is at most `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` old (default 900), shows when it was listed, and a Refresh lists again at once."
- G3: "a user deletes one object after typing its name; the orchestrator's reconciler refuses an object pinned by any session row (live, starting or discarding) or rewritten since it was listed, and the outcome (done, refused with reason, failed with reason) is shown."
- G5 (the gauge): "a quota gauge shows bytes and objects against the bucket quota set in agents-helmfile; [...]"

Design D6 (Web Cache section), verbatim: "`BACKEND_MENUS.orchestrator` gains Cache at order 50 (`registry.test.ts` exact list updated). Summary bar (quota gauge when known, "listed <age>", Refresh); class filter chips and name search; table Object, Kind, Class, Size, Last modified, Delete (disabled for `in_use`, with a tooltip); `ConfirmDialog` with typed object name, size, "cannot be undone" and "a later session with this name starts empty"; the request is polled every 5 s (`usePoll`) to its outcome; `formatBytes` moves from `DiscardSessionDialog.tsx:45` to a shared module."

Design D8, verbatim: "This epic lists old copies and deletes them one at a time on explicit action. [...]" Non-goal, verbatim: "Bulk or multi-select deletion, and automatic deletion of old copies (the clean-up-old-s3-session-cach epic)."

Open questions Q1, Q5 and Q6 are planned on their recommended answers (user decision: "Q1-Q6 in design.md are open; plan on the recommended answers").

This task delivers D6 in agents-web:

- `src/backends/registry.ts`: `BACKEND_MENUS.orchestrator` gains `{ id: 'cache', label: 'Cache', order: 50 }` rendering `CachePage` with `onBack`; the reserved-orders header gains `50 Cache`.
- New `src/cache/CachePage.tsx`: summary bar with a quota gauge for bytes and for objects against `quota` when it is set (hidden when null), "listed <age>" from `listed_at` (and the listing's failure reason when the newest listing failed), and a Refresh button that calls `refreshCache` and polls the request to its end, then reloads the list; class filter chips (all five classes) and a name search; a table with Object, Kind, Class (the slugs for `in_use`, the preset name for `preset`, "copied by N live sessions" for `legacy`), Size (`formatBytes`), Last modified and Delete; Delete is disabled for `in_use` with a tooltip naming the sessions; "Load more" pages with `next_after`; when `available` is false the page says no S3 cache is configured and shows no table.
- New `src/cache/DeleteCacheObjectDialog.tsx` on `layout/ConfirmDialog.tsx`: the object name, its size, "cannot be undone" and "a later session with this name starts empty"; the confirm button stays disabled until the typed text equals the object name; confirm calls `requestCacheDeletion(object, etag)` and the request is polled every 5 s with `usePoll` (`triggers/usePoll.ts`) until `done`, `refused` or `failed`, showing the outcome and its reason; an api 409 `in_use` shows as refused with its message; on `done` the list reloads.
- `formatBytes` moves from `src/sessions/DiscardSessionDialog.tsx` to the new `src/layout/formatBytes.ts`, imported by both; no private copy remains.
- One object at a time: no bulk or multi-select.

Tests no longer accurate because each pins the exact orchestrator menu list, which now ends with `cache`: src/backends/registry.test.ts `default_orchestrator_has_sessions_at_10_and_presets_at_40` (renamed `default_orchestrator_has_sessions_10_presets_40_cache_50`), `webhooks_sits_between_sessions_and_presets_only_when_configured`, `schedules order`, `lists Chats only with the matrix backend`, `filters_by_configured_backends`, `orders_by_order_then_label` and `warns_once_for_unregistered_id`.

#### Acceptance conditions

- AC1: the default orchestrator menu is sessions 10, presets 40, cache 50 [evidence: test:src/backends/registry.test.ts::default_orchestrator_has_sessions_10_presets_40_cache_50]
- AC2: the cache entry is labelled Cache, belongs to the orchestrator backend and renders CachePage with onBack [evidence: test:src/backends/registry.test.ts::cache_entry_renders_cache_page]
- AC3: the page lists each object with object name, kind, class with its slugs, preset name or copied-by count, size and last modified [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "lists objects with kind class size and age"]
- AC4: class chips and the name search reload the list with class and q [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "filters by class and searches by name"]
- AC5: Load more fetches the next page with after set to next_after [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "loads the next page"]
- AC6: the quota gauge shows bytes and objects against the quota when set and is absent when the quota is null; listed <age> is shown [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "shows the quota gauge only with a quota"]
- AC7: Refresh requests a listing, polls it to done and reloads the list [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "refresh requests a listing and reloads when done"]
- AC8: Delete is disabled for in_use objects with a tooltip naming the sessions [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "delete is disabled for objects in use"]
- AC9: the confirm dialog shows the object name, size, cannot be undone and a later session with this name starts empty, and confirm stays disabled until the typed name matches [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "confirm requires the typed object name and warns"]
- AC10: after confirm the request is polled every 5 s to done, refused or failed and the outcome with its reason is shown [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "polls the delete request to its outcome"]
- AC11: an api 409 in_use on confirm shows as refused with its message [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "shows refused when the api answers in use"]
- AC12: with available false the page says no S3 cache is configured and shows no table [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "says no S3 cache is configured"]
- AC13: formatBytes is shared and formats as before [evidence: test:src/layout/formatBytes.test.ts::formats_bytes_to_one_decimal]
- AC14: the discard dialog has no private formatBytes and its suite still passes [evidence: command:! grep -n "function formatBytes" src/sessions/DiscardSessionDialog.tsx && npx vitest run src/sessions/DiscardSessionDialog.test.tsx]
- AC15: no bulk or multi-select in the section [evidence: command:! grep -rniE "checkbox|multi-?select|selectAll" src/cache]
- AC16: the section, registry, design-rule and nomenclature suites, the type check of the build and lint pass [evidence: command:npx vitest run src/cache src/backends/registry.test.ts src/layout/formatBytes.test.ts src/layout/designRules.test.ts src/nomenclature.test.ts && npm run build && npm run lint]

#### Files

- `src/backends/registry.ts`
- `src/backends/registry.test.ts`
- `src/cache/CachePage.tsx`
- `src/cache/DeleteCacheObjectDialog.tsx`
- `src/cache/CachePage.test.tsx`
- `src/layout/formatBytes.ts`
- `src/layout/formatBytes.test.ts`
- `src/sessions/DiscardSessionDialog.tsx`

#### Interfaces

- `src/backends/registry.ts`: orchestrator entry `{ id: 'cache', label: 'Cache', order: 50, backend: 'orchestrator', render: (onBack) => createElement(CachePage, { onBack }) }`.
- `src/cache/CachePage.tsx` (new): `export function CachePage({ onBack }: { onBack: () => void })`.
- `src/cache/DeleteCacheObjectDialog.tsx` (new): props `open`, `object: CacheObjectView`, `onClose`, `onDone`.
- `src/layout/formatBytes.ts` (new): `export function formatBytes(bytes: number): string` (the body moved unchanged from `DiscardSessionDialog.tsx`).
- Uses `getCache`, `listCacheObjects`, `requestCacheDeletion`, `refreshCache`, `getCacheRequest` from `src/api/client.ts` (task web-cache-client), `usePoll`, `ConfirmDialog`.

#### Expected outcome

Users with the orchestrator backend see a Cache entry after Presets; it lists every cache object with kind, class, size and age, filters and searches, shows the quota gauge and listing age, refreshes on demand and deletes one object after a typed-name confirm, showing the reconciler's outcome.

#### Steps

- Read `src/backends/registry.ts`, `src/backends/registry.test.ts`, `src/App.tsx` (how a menu view renders), `src/presets/PresetsPage.tsx` and its test (page shape, `vi.mock('../api/client')`), `src/webhooks/WebhooksPage.tsx` and `EventsTable.tsx` (usePoll, table, paging), `src/layout/ConfirmDialog.tsx`, `src/sessions/DiscardSessionDialog.tsx` and its test (typed confirmation, formatBytes), `src/triggers/usePoll.ts`, `src/layout/designRules.ts` and `src/api/client.ts` in one pass.
- Red: update the registry tests named in the Requirement and add `cache_entry_renders_cache_page`; write `src/cache/CachePage.test.tsx` (`// @vitest-environment jsdom`, mocked client, fake timers for the 5 s poll) with every test named in the acceptance conditions and `src/layout/formatBytes.test.ts`; run `npx vitest run src/cache src/backends/registry.test.ts src/layout/formatBytes.test.ts`; expect failures on the missing modules and entry.
- Green: write formatBytes.ts (and switch DiscardSessionDialog.tsx to it), CachePage.tsx, DeleteCacheObjectDialog.tsx and the registry entry; rerun the verify; expect passed; `npm run build && npm run lint`; expect exit 0.

#### Notes

- The gauge is MUI `LinearProgress` per quota dimension (architecture section 5); colours come from the theme, never literals.
- "listed <age>": a relative age from `listed_at`; show "never listed" when null.
- The request poll stops at a terminal status; a refused outcome shows the reason the reconciler wrote (`in_use: <slugs>`, `changed`), a failed one its S3 reason.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main; both edit `src/sessions/DiscardSessionDialog.tsx`, the openapi files and `src/api/schema.d.ts` before this epic. Read the landed files first.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring; agents-web has a known load-dependent vitest timeout in PresetForm `name_rules_default_name_and_pvc`).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes, no colour literals, decorative Unicode or off-grid spacing (`layout/designRules.ts`), never the word "cluster" (`nomenclature.test.ts`). No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S9: helmfile cache pins

- Status: todo
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `values/agents-web/common.yaml`, `tests/test_orchestrator_release.py`, `tests/test_web_release.py`, `tests/test_workspace_cache.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py tests/test_workspace_cache.py && mise run lint`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G5, verbatim: "a quota gauge shows bytes and objects against the bucket quota set in agents-helmfile; released and deployed, and proven live by listing the bucket and deleting one disposable object."

Design D7 (Quota settings), verbatim: "`ORCH_CACHE_QUOTA_BYTES` and `ORCH_CACHE_QUOTA_OBJECTS` (default unset, gauge hidden), set in agents-helmfile values from the OBC quota (100G, 100000). User Q4."

Design D9 (Deploy and live check), verbatim: "Release orchestrator and web, pin in agents-helmfile with the quota values, apply under the deploy lease; the live check lists the bucket in the section and deletes one disposable object created for the check (a smoke object, never a session's cache) (my call)."

User decision (repos), verbatim: "Repos: agents-orchestrator, agents-web, agents-helmfile (quota values, image pins, and a live check after the apply under the deploy lease [...])".

Scope (agents-helmfile): pin agents-orchestrator to the merge commit `<ORCH_SHA>` of its epic PR (chart `0.1.0-main.<ORCH_SHA>` in helmfile.yaml.gotmpl, `image.tag` `<ORCH_SHA>` in values/agents-orchestrator/common.yaml) and agents-web to the merge commit `<WEB_SHA>` of its epic PR (chart `0.1.0-main.<WEB_SHA>`, `image.tag` `<WEB_SHA>` in values/agents-web/common.yaml), after each main CI run for those shas is green including chart and image publish. Set `cache.quota.bytes: 100000000000` and `cache.quota.objects: 100000` in values/agents-orchestrator/common.yaml, the quota of raw/workspace-cache-bucket.pre.yaml (`maxSize: 100G`, `maxObjects: "100000"`), with a test that keeps the two equal. Keep every other pin and value unchanged. Update tests/test_orchestrator_release.py and tests/test_web_release.py to the new pins. `mise run check-pins` must pass. Never run an apply. `<ORCH_SHA>` and `<WEB_SHA>` are placeholders: the orchestrator replaces them with the real 7-character merge shas through `ticket.py amend` before this task starts.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the orchestrator merge sha `<ORCH_SHA>` [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the agents-web chart version and image tag agree on the agents-web merge sha `<WEB_SHA>` [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the pins name the merge shas [evidence: command:grep -q "0.1.0-main.<ORCH_SHA>" helmfile.yaml.gotmpl && grep -q "0.1.0-main.<WEB_SHA>" helmfile.yaml.gotmpl]
- AC4: the orchestrator cache.quota values equal the bucket claim's maxSize (as a Kubernetes quantity, 100G = 100000000000 bytes) and maxObjects [evidence: test:tests/test_workspace_cache.py::test_orchestrator_cache_quota_matches_bucket_claim]
- AC5: every pin's main CI is green [evidence: command:mise run check-pins]
- AC6: the release and cache test files and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py tests/test_workspace_cache.py && mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`
- `tests/test_workspace_cache.py`

#### Interfaces

- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.<ORCH_SHA>`, agents-web chart `0.1.0-main.<WEB_SHA>`.
- `values/agents-orchestrator/common.yaml`: `image.tag` `<ORCH_SHA>`; under `cache`, `quota: {bytes: 100000000000, objects: 100000}` (chart values from task orch-chart-cache-quota). `values/agents-web/common.yaml`: `image.tag` `<WEB_SHA>`. No other value changes.

#### Expected outcome

agents-helmfile main pins the orchestrator and web releases of this epic with the bucket quota set, ready for the apply in helmfile-cache-live-check.

#### Steps

- Read helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, raw/workspace-cache-bucket.pre.yaml, tests/test_orchestrator_release.py, tests/test_web_release.py, tests/test_workspace_cache.py and tests/conftest.py (`layered_values`) in one pass; confirm `<ORCH_SHA>` and `<WEB_SHA>` were amended to real shas.
- Red: change the pin assertions to the amended shas and add `test_orchestrator_cache_quota_matches_bucket_claim` (parse maxSize as a Kubernetes quantity: decimal suffixes k, M, G, T and binary Ki, Mi, Gi, Ti); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py tests/test_workspace_cache.py`; expect the pin and quota tests to fail.
- Green: change the pins and add the quota values; rerun the verify; expect passed and lint exit 0; `mise run check-pins`; expect every pin green.

#### Notes

- `<ORCH_SHA>` and `<WEB_SHA>` mean the 7-character short merge sha (the pin tests require `[0-9a-f]{7}`). If either still reads as a placeholder, stop and return it as a question. Never pin an epic-branch commit.
- (my call) Rook reads `maxSize: 100G` as a Kubernetes quantity, so 100G is 100000000000 bytes (decimal), not 100 GiB; the test parses the claim rather than restating the number.
- Retro (file-editor-with-tabs-and-hi, generic-any-mcp-with-git-and): Harbor prunes sha7 image tags; the live check verifies the pinned tags exist before the apply.
- Chart-pull tests blocked by a container network policy may be deselected locally (precedent); they run unblocked before the apply.
- Never run an apply in this task. `gh` must be authenticated for check-pins.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
- (my call) Builder check Q5: this task starts only after the orchestrator and web PRs are merged with main CI, chart and image publish green, and after the orchestrator session amended `<ORCH_SHA>` and `<WEB_SHA>` to their merge shas.

### S10: helmfile cache live check

- Status: todo
- Files: `MEMORY.md`
- Verify: `mise run lint && grep -q 's3 cache section live check' MEMORY.md`
- Verified head: none

#### Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G5, verbatim: "a quota gauge shows bytes and objects against the bucket quota set in agents-helmfile; released and deployed, and proven live by listing the bucket and deleting one disposable object."

Design D9 (Deploy and live check), verbatim: "Release orchestrator and web, pin in agents-helmfile with the quota values, apply under the deploy lease; the live check lists the bucket in the section and deletes one disposable object created for the check (a smoke object, never a session's cache) (my call)."

User decision, verbatim: "Repos: agents-orchestrator, agents-web, agents-helmfile (quota values, image pins, and a live check after the apply under the deploy lease Lease agents/agents-helmfile-apply: kubectl create -f, holderIdentity, acquireTime, leaseDurationSeconds 3600; stale after 60 min, message the holder via the superleader before deleting; delete only your own; kubeconfig from the pod SA, context in-cluster-sa). The live check deletes only one disposable object it created, never a session's cache."

Live applies are run by the orchestrator session only, never by a subagent. Steps, after the agents-helmfile PR of helmfile-cache-pins merged, in `code/agents-helmfile` on `main`, least destructive first:
1. Claim the deploy Lease: `kubectl --context in-cluster-sa -n agents create -f <lease.yaml>` for Lease `agents-helmfile-apply` with `holderIdentity` (the session's own ccw address), `acquireTime` (now) and `leaseDurationSeconds: 3600`. If it already exists: an `acquireTime` under 60 minutes old means wait; a stale one (60 minutes or more) means message its holder via the superleader first and delete it only after that; never delete a Lease that is not your own otherwise.
2. Check that the pinned orchestrator and web image tags and chart versions exist in Harbor.
3. Render every release with `helmfile template` and read `mise run diff` in full: only the agents-orchestrator and agents-web chart versions and image tags change, plus the two `ORCH_CACHE_QUOTA_*` settings in the orchestrator settings ConfigMap and the settings checksum annotation that follows them; anything else stops the task (Lease released).
4. Write a handoff checkpoint naming the remaining steps before the apply (the apply may roll agent pods, the deployer's included).
5. `mise run apply -- --selector name=agents-orchestrator`, then `mise run apply -- --selector name=agents-web` (orchestrator first).
6. `mise run diff` shows no pending change; `mise run smoke` green.
7. Live check, through the orchestrator API on the web port (port-forward as the smoke does):
   a. `GET /api/v1/cache`: `available` true and `quota` `{bytes: 100000000000, objects: 100000}`; `POST /api/v1/cache/refresh`, poll the request to `done`; `listed_at` is after the apply; record the listing's object and byte totals and the reconciler's logged pass duration.
   b. `GET /api/v1/cache/objects`: each live session's workspace object reads `in_use` with its slug.
   c. Advisory refusal, nothing deleted: `POST /api/v1/cache/deletions` for one `in_use` object answers 409 `in_use`; after a refresh the object is still listed.
   d. The disposable object: create a session `smoke-cache-del-<ts>` with a raw spec whose literal cache key is `smoke-cache-del-<ts>`, wait until its restore ran (`miss`), discard it and wait until its row is purged; refresh; the object `smoke-cache-del-<ts>.tar.zst` is listed with class `saved`; `POST /api/v1/cache/deletions` with its object and etag; poll the request to `done`; after a refresh the object is no longer listed. This is the only object deleted.
   e. The web serves the release with the Cache section (the served bundle holds the `/cache/objects` path).
8. Delete your own Lease.
9. MEMORY.md entry containing the words `s3 cache section live check`, dated, with the applied orchestrator and web charts and images, the step 7 values (quota, totals, pass duration, the 409 answer, the disposable object's request id and outcome).

#### Acceptance conditions

- AC1: (orchestrator session) the deploy Lease agents/agents-helmfile-apply was created with this session as holderIdentity before the apply and deleted by it after the live check, and no other holder's Lease was deleted without messaging the holder via the superleader [evidence: judgement:orchestrator quotes the Lease holderIdentity, acquireTime and the delete in the task Notes]
- AC2: (orchestrator session) the pinned orchestrator and web image tags and chart versions exist in Harbor before the apply, and the pre-apply diff showed only the pins and the quota settings [evidence: judgement:orchestrator records the registry check and the diff summary in the task Notes]
- AC3: after the applies helmfile reports no pending change [evidence: command:mise run diff]
- AC4: the smoke passes against the applied release [evidence: command:mise run smoke]
- AC5: (orchestrator session) GET /api/v1/cache reports available true, the quota 100000000000 bytes and 100000 objects, and a listing done after the apply [evidence: judgement:orchestrator quotes the GET /api/v1/cache body and the refresh request in the task Notes]
- AC6: (orchestrator session) live sessions' objects read in_use with their slugs, and a deletion of one answers 409 in_use and leaves it listed [evidence: judgement:orchestrator quotes the objects page and the 409 body in the task Notes]
- AC7: (orchestrator session) the disposable object smoke-cache-del-<ts>.tar.zst created for the check was listed as saved, its delete request ended done and it is no longer listed; no other object was deleted [evidence: judgement:orchestrator quotes the request, its final status and the listings before and after in the task Notes]
- AC8: MEMORY.md records the live check and the applied versions [evidence: command:grep -q "s3 cache section live check" MEMORY.md]

#### Files

- `MEMORY.md`

#### Interfaces

- None new; uses `kubectl --context in-cluster-sa` (kubeconfig from the pod service account), `helmfile template`, `mise run diff`, `mise run apply`, `mise run smoke`, and the orchestrator API on the web port (port-forward as `scripts/smoke.sh` does).
- Lease manifest: `apiVersion: coordination.k8s.io/v1`, `kind: Lease`, `metadata: {name: agents-helmfile-apply, namespace: agents}`, `spec: {holderIdentity: <own ccw address>, acquireTime: <now, RFC 3339 micro>, leaseDurationSeconds: 3600}`, written under the workbench `.scratchpad`.

#### Expected outcome

The orchestrator and web releases of this epic run live with the quota set; the Cache section lists the bucket, refuses an in-use object and deleted exactly one disposable object created for the check; the deploy Lease is released.

#### Steps

- Orchestrator session only: steps 1-9 of the Requirement, in order; stop at step 3 if the diff shows more than allowed (release the Lease first).
- Write the handoff checkpoint (step 4) before the apply; after a roll, resume from it.
- Record each result in the task Notes as it happens (Lease holder and times, Harbor check, diff summary, smoke tail, the step 7 bodies), then the MEMORY.md entry; commit it through the agents-helmfile PR flow; `mise run lint`; expect exit 0.

#### Notes

- Never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25). Subagent `kubectl exec` is denied by the permission classifier; the whole task is orchestrator-run, and a builder subagent stops after helmfile-cache-pins.
- (my call) The disposable object comes through the product path (a session with a unique literal cache key, discarded so its save writes the object and its row is purged), because agents hold no S3 credential. Its discard also writes `sessions/smoke-cache-del-<ts>.tar.zst`; that transcripts object stays, like the existing `sessions/smoke-*` objects, because the user decision allows deleting only one object.
- Never delete a session's cache, and never send a deletion for any object other than the disposable one; the step 7c request must be refused, so pick an object `GET /api/v1/cache/objects` reports `in_use`.
- Assumption to confirm (design): the OBC key has DeleteObject. If the disposable delete ends `failed` with a 403, stop: that is a defect for a new task (bucket policy in agents-helmfile), never a hand fix.
- Retro (matrix-connector-agent-initi, recurring): a live apply surfaced defects tests missed; render every release with `helmfile template` and read the full diff before the apply. Live apply and proof tasks run several times their seed; a defect found live becomes a new task.
- `gh` must be authenticated in the deploying pod for check-pins.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
- (my call) Builder check Q6: confirmed orchestrator-session only; a builder stops after helmfile-cache-pins and never takes this task.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
