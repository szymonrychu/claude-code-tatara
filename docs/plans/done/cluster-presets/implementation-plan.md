# cluster presets implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: presets table and repo

- Status: done
- Files: `src/agent_orchestrator/db/migrations/0002_presets.sql`, `src/agent_orchestrator/db/presets.py`, `tests/test_migrations.py`, `tests/test_presets_repo.py`, `README.md`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_migrations.py tests/test_presets_repo.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 233ff924f80b0f6e4ae4174d5b786adc77ad259f

#### Requirement

Add the presets table, the cluster provenance columns and the presets repository (design D1, user Q5, Q6, Q8), test-first.

- New `src/agent_orchestrator/db/migrations/0002_presets.sql`, every statement idempotent (`CREATE TABLE IF NOT EXISTS`, `CREATE UNIQUE INDEX IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`):
  - `presets`: `id uuid PRIMARY KEY`, `name text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 40)`, `spec jsonb NOT NULL DEFAULT '{}'`, `is_default boolean NOT NULL DEFAULT false`, `created_at timestamptz NOT NULL DEFAULT now()`, `updated_at timestamptz NOT NULL DEFAULT now()`; unique index on `lower(name)`; partial unique index on `(is_default) WHERE is_default` (at most one default).
  - seed: `INSERT INTO presets (id, name, spec, is_default) VALUES ('00000000-0000-0000-0000-000000000001', 'Default', '{"replicas": 1}', true) ON CONFLICT DO NOTHING`.
  - `clusters` gains `preset_id uuid REFERENCES presets (id) ON DELETE SET NULL` and `preset_name text`, both nullable.
- New `src/agent_orchestrator/db/presets.py` (part `presets-repo`; the api is its only caller and `presets` has the api as its only writer):
  - `validate_preset_name(name)`: 1 to 40 characters of letters, digits, spaces, dots, dashes and underscores, no leading or trailing space (rejected, never trimmed: the API passes names through untouched); raises `ValueError` with a readable message.
  - `Preset` frozen dataclass (`id`, `name`, `spec: dict[str, Any]`, `is_default`, `created_at`, `updated_at`); exceptions `PresetExists`, `PresetNotFound`, `PresetDefault`, `LastPreset`.
  - `list_presets(conn)` (default first, then `lower(name)`), `get(conn, preset_id)`, `get_for_share(conn, preset_id)` (`SELECT ... FOR SHARE`, for cluster create), `create(conn, name, spec) -> Preset` (validates the name, new uuid, `PresetExists` on the unique index), `update(conn, preset_id, name, spec) -> Preset` (sets `updated_at = now()`; `PresetNotFound`, `PresetExists`, `PresetDefault` when the default's name changes), `delete(conn, preset_id)` (`PresetNotFound`; `PresetDefault` for the default; `LastPreset` when it is the only row, decided under a lock so two concurrent deletes cannot remove the last two rows).
  - The repository stores `spec` exactly as given; it never fills defaults.
- `tests/test_migrations.py`: `TABLES` gains `presets`; `versions == ["0001", "0002"]`; `test_concurrent_migrate_serialises` expects `[0, 2]`; new tests for the seed and its idempotency, and for the provenance columns.
- New `tests/test_presets_repo.py` for the repository.
- README `## Data model`: a `presets` row and the `clusters` row naming `preset_id` and `preset_name`; README `### Single-writer interpretation of "no shared state"` table: `presets | api`.

#### Acceptance conditions

- AC1: a fresh database has the presets table and versions 0001 and 0002, and two concurrent migrates apply 2 and 0 [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- AC2: the Default preset is seeded once with spec {"replicas": 1} and is_default true [evidence: test:tests/test_migrations.py::test_default_preset_seeded]
- AC3: re-applying 0002 after its schema_migrations row is removed succeeds and keeps an edited default [evidence: test:tests/test_migrations.py::test_presets_migration_reapply_keeps_edited_default]
- AC4: deleting a preset sets clusters.preset_id to null and keeps preset_name [evidence: test:tests/test_migrations.py::test_preset_delete_keeps_cluster_provenance]
- AC5: create, get, list order and update round-trip the stored spec exactly, and update bumps updated_at [evidence: test:tests/test_presets_repo.py::test_crud_round_trip_and_order]
- AC6: names are unique case-insensitively and validate_preset_name enforces 1 to 40 allowed characters and rejects leading or trailing spaces [evidence: test:tests/test_presets_repo.py::test_name_rules_and_unique]
- AC7: the default cannot be renamed or deleted and the last preset cannot be deleted [evidence: test:tests/test_presets_repo.py::test_default_and_last_preset_guards]
- AC8: README Data model and single-writer table name presets and the provenance columns [evidence: judgement:README.md Data model and Single-writer sections reviewed]
- AC9: the targeted tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_migrations.py tests/test_presets_repo.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/db/migrations/0002_presets.sql`
- `src/agent_orchestrator/db/presets.py`
- `tests/test_migrations.py`
- `tests/test_presets_repo.py`
- `README.md`

#### Interfaces

- Tables: `presets(id, name, spec, is_default, created_at, updated_at)`; `clusters.preset_id`, `clusters.preset_name`.
- `db/presets.py` (part `presets-repo`): `validate_preset_name`, `Preset`, `PresetExists`, `PresetNotFound`, `PresetDefault`, `LastPreset`, `list_presets`, `get`, `get_for_share`, `create`, `update`, `delete`. Consumed by preset-routes and create-cluster-from-preset.
- Default preset id `00000000-0000-0000-0000-000000000001`, name `Default`, spec `{"replicas": 1}`.

#### Expected outcome

After `orch migrate` every database has a Default 1-pod preset, a presets repository the api can call, and clusters able to record where they came from.

#### Steps

- Update `tests/test_migrations.py` (TABLES, versions, concurrent count, the three new tests) and write `tests/test_presets_repo.py`; run `uv run pytest -q -p no:cacheprovider tests/test_migrations.py tests/test_presets_repo.py`: fails.
- Write `0002_presets.sql` and `db/presets.py`; add the README rows; run the verify command: passes.

#### Notes

- `db/migrate.py:run_migrations` records versions and skips applied ones, so the re-apply test deletes the `0002` row from `schema_migrations` first; every statement must then succeed again.
- Follow `db/clusters.py` for row mapping (`dict_row`), `Jsonb` dumps and exception translation from `psycopg.errors.UniqueViolation`.
- The repository does not NOTIFY; nothing listens for preset changes.
- Review tier is full (migration path).
- Builder check ruling 4 (2026-10-23): names with leading or trailing spaces are rejected (422 on the API, inline error in the form); the API never trims. The copy name's source part is cut to fit 40 characters and right-trimmed before " copy".

- 2026-10-23 amended: builder check ruling 4: leading/trailing space rejected, never trimmed (AC6 rewritten)

### S2: slug from name

- Status: done
- Files: `src/agent_orchestrator/spec.py`, `src/agent_orchestrator/bench/runner.py`, `tests/test_slugs.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_slugs.py tests/test_bench.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: eac3b59b3cd94534dff90ae9d44a175617504ddd

#### Requirement

Add the shared slug helper (part `slugify-helper`, design D4, user Q1 and Q8) to `src/agent_orchestrator/spec.py`, test-first in a new `tests/test_slugs.py`.

- `slugify(text: str, max_len: int = SLUG_MAX) -> str`: lowercase; every run of characters outside `[a-z0-9]` becomes one `-`; leading and trailing `-` stripped; cut to `max_len` and trailing `-` stripped again; returns `""` when nothing usable remains.
- `generated_slug(name: str, rand: Callable[[], str] | None = None) -> str`: `<base>-<suffix>`, where `suffix` is 4 random lowercase ASCII letters (`secrets.choice(string.ascii_lowercase)`; `rand` returns the 4 letters, injected by tests) and `base` is `slugify(name, SLUG_MAX - 5)`, or `cluster` when that is empty. A base equal to `orchestrator` or starting with `orchestrator-` gets the prefix `p-` and is re-cut to `SLUG_MAX - 5`. The result always passes `validate_slug` and is at most `SLUG_MAX` (40) characters.
- `bench/runner.py:arm_slug` uses `slugify` for its body instead of its own regex; its output for every input stays the same (the existing `tests/test_bench.py` stays green).

#### Acceptance conditions

- AC1: slugify maps names to their DNS-1123 form, collapses separators, strips edge dashes and respects max_len [evidence: test:tests/test_slugs.py::test_slugify_dns_1123_form]
- AC2: generated_slug returns base, a dash and 4 lowercase letters, at most 40 characters, valid for validate_slug, also for an 80-character name [evidence: test:tests/test_slugs.py::test_generated_slug_shape_and_length]
- AC3: a name whose base is orchestrator or orchestrator-* gets the p- prefix and passes validate_slug [evidence: test:tests/test_slugs.py::test_generated_slug_avoids_reserved_prefix]
- AC4: a name with no usable characters falls back to the cluster base [evidence: test:tests/test_slugs.py::test_generated_slug_fallback_base]
- AC5: arm_slug output is unchanged and its body comes from slugify [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_bench.py]
- AC6: the targeted tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_slugs.py tests/test_bench.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/spec.py`
- `src/agent_orchestrator/bench/runner.py`
- `tests/test_slugs.py`

#### Interfaces

- `spec.slugify(text: str, max_len: int = SLUG_MAX) -> str` and `spec.generated_slug(name: str, rand: Callable[[], str] | None = None) -> str` (part `slugify-helper`, consumed by create-cluster-from-preset).
- `bench/runner.py:arm_slug(arm, run)` keeps its signature and output.

#### Expected outcome

Any preset name maps to a valid, short, non-reserved cluster slug with a random suffix, from one helper the bench also uses.

#### Steps

- Write `tests/test_slugs.py` with the four tests named in the AC refs; run `uv run pytest -q -p no:cacheprovider tests/test_slugs.py`: fails on the missing functions.
- Implement `slugify` and `generated_slug` in `spec.py`, switch `arm_slug` to `slugify`; run the verify command: passes.

#### Notes

- `validate_slug` (spec.py) is the oracle: DNS-1123 label, at most `SLUG_MAX` 40, `orchestrator` and `orchestrator-*` reserved.
- Reuse map: `arm_slug` sanitising is the adopted prior art (discovery/reuse.md ideas).

### S3: preset routes

- Status: done
- Files: `src/agent_orchestrator/api/presets.py`, `src/agent_orchestrator/api/app.py`, `src/agent_orchestrator/api/schemas.py`, `src/agent_orchestrator/api/clusters.py`, `tests/test_api_presets.py`, `README.md`, `openapi.json`, `frontend/src/api/schema.d.ts`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_presets.py tests/test_api_clusters.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .`
- Verified head: dde2170bcce0ebb5903fb981507d343100e24880

#### Requirement

Expose presets through `/api/v1` (design D2, D3; user Q5, Q7, Q8; headless parity), test-first in a new `tests/test_api_presets.py` (ASGI client against the real test database, like `tests/test_api_clusters.py:http`).

- `api/clusters.py`: `_check_spec` becomes the public `check_spec(spec, settings, stored=None)` (part `check-spec-public`; same behaviour, callers updated; `stored` stays for the preset PUT and is not dropped by retire-cluster-patch-route or retire-spec-update-repo).
- `api/schemas.py`: `PresetIn {name: str, spec: ClusterSpec = ClusterSpec()}` and `CopyPreset {name: str | None = None}`, both `extra="forbid"`; `PresetView {id, name, is_default, spec: dict[str, Any], created_at, updated_at}`.
- New `api/presets.py` router (`APIRouter(prefix="/api/v1")`), registered in `api/app.py:create_app` beside the clusters router:
  - `GET /presets`: list of `PresetView`, default first, then by name.
  - `POST /presets`: 201. Name checked with `validate_preset_name` (422 `invalid_request`; leading or trailing spaces are rejected and the API never trims); spec checked with `check_spec` against current settings (422 `invalid_request`), the filled result discarded; stored spec is `body.spec.model_dump(mode="json", exclude_unset=True)`, so only the keys the caller sent are kept; name taken is 409 `conflict`.
  - `GET /presets/{preset_id}`: 200, 404 `not_found`.
  - `PUT /presets/{preset_id}`: full replace of name and spec with the same rules; renaming the default is 409 `preset_default`; 404. `check_spec` gets the stored preset spec as `stored`, so a stored model, effort or image that is no longer in the settings lists is accepted only when unchanged from the stored preset; changing to an unknown value is 422.
  - `DELETE /presets/{preset_id}`: 204; the default is 409 `preset_default`; the only preset is 409 `last_preset`; 404. Clusters made from it keep their spec; their `preset_id` becomes null by the foreign key.
  - `POST /presets/{preset_id}/copy`: optional body `CopyPreset`; 201 with a new non-default preset holding the source's stored spec verbatim; the name is `body.name` or `<source name> copy`, then `<source name> copy 2`, `copy 3` and so on until free, the source part cut to fit 40 characters and right-trimmed before ` copy`; an explicit name that is taken is 409 `conflict`; 404 for an unknown source.
- README `## API`: one `### \`METHOD /api/v1/presets...\`` section per route with body, response and errors; the error codes list gains `preset_default` (409) and `last_preset` (409).
- `openapi.json` regenerated (`uv run python -m agent_orchestrator.api.openapi > openapi.json`) and `frontend/src/api/schema.d.ts` (`mise x node@24.20.0 -- npm --prefix frontend run gen:api`).

#### Acceptance conditions

- AC1: GET /presets returns the seeded Default first with spec {"replicas": 1} [evidence: test:tests/test_api_presets.py::test_list_has_seeded_default]
- AC2: POST stores and returns only the spec keys the caller sent, nested resources included [evidence: test:tests/test_api_presets.py::test_create_stores_only_set_fields]
- AC3: invalid names (including leading or trailing spaces, never trimmed) are 422 and a taken name (any case) is 409 conflict [evidence: test:tests/test_api_presets.py::test_name_rules_and_unique_409]
- AC4: a spec against current settings (model outside ORCH_MODELS, replicas above the cap, image outside the allowlist) is 422 on POST and PUT [evidence: test:tests/test_api_presets.py::test_save_validates_spec_against_settings]
- AC5: PUT replaces name and spec; the default can be edited but renaming it is 409 preset_default; unknown id is 404 [evidence: test:tests/test_api_presets.py::test_put_replaces_and_default_not_renamed]
- AC6: DELETE is 204, the default is 409 preset_default, the last preset is 409 last_preset, unknown id is 404 [evidence: test:tests/test_api_presets.py::test_delete_guards]
- AC7: copy without a name gives "<name> copy" then "<name> copy 2" within 40 characters (source part cut and right-trimmed), copies the stored spec verbatim, is never default, and a taken explicit name is 409 [evidence: test:tests/test_api_presets.py::test_copy_default_name_and_verbatim_spec]
- AC8: check_spec is public and the clusters routes use it [evidence: symbol:src/agent_orchestrator/api/clusters.py::check_spec]
- AC9: README, openapi.json and schema.d.ts match the app [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC10: targeted tests, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_presets.py tests/test_api_clusters.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]
- AC11: PUT accepts a stored model, effort or image no longer in the settings lists when unchanged, changing it to an unknown value is 422, and POST of such a value is 422 [evidence: test:tests/test_api_presets.py::test_put_accepts_unchanged_out_of_list_value]

#### Files

- `src/agent_orchestrator/api/presets.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/api/clusters.py`
- `tests/test_api_presets.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

#### Interfaces

- Routes: `GET|POST /api/v1/presets`, `GET|PUT|DELETE /api/v1/presets/{preset_id}`, `POST /api/v1/presets/{preset_id}/copy` (part `orch-presets-api`, defined in README.md).
- `api/clusters.py:check_spec(spec, settings, stored=None) -> ClusterSpec` (part `check-spec-public`).
- `schemas.PresetIn`, `schemas.CopyPreset`, `schemas.PresetView`.
- Error codes `preset_default` (409), `last_preset` (409), plus the existing `conflict`, `not_found`, `invalid_request`.

#### Expected outcome

A headless client can list, create, read, replace, copy and delete presets, with the same validation the cluster create applies, and the README and OpenAPI describe it.

#### Steps

- Write `tests/test_api_presets.py` with the eight tests named in the AC refs (reuse `make_settings`, `client_for`, `assert_error` by importing them from `test_api_clusters` or a small local copy); run `uv run pytest -q -p no:cacheprovider tests/test_api_presets.py`: fails with 404s.
- Rename `_check_spec`, add schemas, `api/presets.py` and the router registration; run the test file: passes.
- Add the README sections and error codes; regenerate `openapi.json` and `schema.d.ts`; run the verify command: passes.

#### Notes

- `exclude_unset=True` must be applied to the parsed request model, not to a re-validated copy, or every default reappears.
- `check_spec` is called for its validation; the filled spec it returns is not stored here.
- DELETE answers 204 with no body; keep `response_model=None` so OpenAPI stays clean.
- Builder check ruling 2 (2026-10-23): PUT of a preset accepts a stored model, effort or image that is no longer in the settings lists only when that value is unchanged from the stored preset (the legacy rule PATCH used); changing to an unknown value is 422. validate_spec keeps its `stored` parameter (and check_spec its `stored` parameter) for this; retire-spec-update-repo must not delete it, it still deletes update_spec and ClusterDeleting if unused. Scheduling always validates fully (no `stored`) and returns 422 with the reason and the preset name. The editor's Model/Effort select shows a stored out-of-list value as an extra option labelled "<value> (not available)".
- Builder check ruling 4 (2026-10-23): names with leading or trailing spaces are rejected (422 on the API, inline error in the form); the API never trims. The copy name's source part is cut to fit 40 characters and right-trimmed before " copy".

- 2026-10-23 amended: builder check rulings 2, 4: PUT keeps unchanged out-of-list values via stored; no trimming, copy name cut and right-trimmed (AC3, AC7 rewritten, AC11 added)

### S4: create cluster from preset

- Status: done
- Files: `src/agent_orchestrator/api/clusters.py`, `src/agent_orchestrator/api/schemas.py`, `src/agent_orchestrator/db/clusters.py`, `tests/test_api_create_from_preset.py`, `README.md`, `openapi.json`, `frontend/src/api/schema.d.ts`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_create_from_preset.py tests/test_api_clusters.py tests/test_clusters_repo.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .`
- Verified head: de2e84784c44399af9c4527956e14425db6917fd

#### Requirement

Let `POST /api/v1/clusters` schedule a cluster from a preset and snapshot its spec (design D4; user Q1, Q2, Q3; headless parity), test-first in a new `tests/test_api_create_from_preset.py`.

- `api/schemas.py`: `CreateCluster` becomes `{slug: str | None = None, spec: ClusterSpec | None = None, preset_id: uuid.UUID | None = None}`, `extra="forbid"` (part `orch-cluster-create-api`). Exactly one of `spec` and `preset_id`, else 422 `invalid_request` ("exactly one of spec or preset_id"); with `spec` the slug is required (422 "slug is required with spec"). `ClusterView` gains `preset_id: uuid.UUID | None` and `preset_name: str | None`.
- `db/clusters.py`: `Cluster` gains `preset_id` and `preset_name` (read by `_from_row`); `create(conn, slug, spec, preset_id=None, preset_name=None)` inserts them.
- `api/clusters.py:create_cluster`, preset path: inside the existing transaction after `pg_advisory_xact_lock(_CREATE_LOCK)` and the `max_clusters` check, read the preset with `presets.get_for_share` (404 `not_found` "preset not found"); run `check_spec(ClusterSpec.model_validate(preset.spec), settings)` against current settings, a 422 message prefixed `preset '<name>': `; the filled spec is the cluster's own spec (the snapshot). On this preset path only, when the preset leaves `replicas` unset the schedule-time fill sets it from `settings.default_replicas`, alongside the write-time fills (the raw-spec path is unchanged; the seeded Default stores replicas 1 explicitly, so it schedules 1). Slug: `body.slug` checked with `validate_slug`, or `generated_slug(preset.name)` retried with a fresh suffix up to 5 times on `ClusterExists`; an explicit slug clash stays 409 `conflict`, and after the 5th generated-slug clash the answer is 409 `conflict` too, never 500. Insert with `preset_id` and `preset_name`. `_view` fills the two new fields.
- Raw spec path unchanged apart from the exactly-one rule; its clusters have null `preset_id` and `preset_name`.
- No code path changes a cluster's `spec` or `generation` when a preset is edited or deleted.
- README `### POST /api/v1/clusters` documents both bodies, the generated slug, the snapshot, 404 for an unknown preset and the preset-named 422; `### GET /api/v1/clusters/{cluster_id}` lists `preset_id` and `preset_name`. `openapi.json` and `frontend/src/api/schema.d.ts` regenerated.

#### Acceptance conditions

- AC1: POST {preset_id: Default} is 201 with a slug matching ^default-[a-z]{4}$, spec replicas 1 with resources filled from the current defaults, preset_id and preset_name set [evidence: test:tests/test_api_create_from_preset.py::test_create_from_default_preset_generates_slug]
- AC2: an explicit slug is used, a clashing explicit slug is 409 conflict, and a generated slug clash is retried [evidence: test:tests/test_api_create_from_preset.py::test_explicit_slug_and_generated_retry]
- AC3: both spec and preset_id, neither, or spec without slug are 422 invalid_request [evidence: test:tests/test_api_create_from_preset.py::test_exactly_one_of_spec_or_preset_id]
- AC4: a preset that became invalid under current settings is 422 with a message naming the preset [evidence: test:tests/test_api_create_from_preset.py::test_preset_revalidated_at_schedule]
- AC5: editing and then deleting the preset leaves the cluster spec and generation unchanged; after the delete preset_id is null and preset_name is kept [evidence: test:tests/test_api_create_from_preset.py::test_snapshot_survives_preset_edit_and_delete]
- AC6: an unknown preset_id is 404 not_found and creates nothing [evidence: test:tests/test_api_create_from_preset.py::test_unknown_preset_404]
- AC7: a preset without resources gets the resource defaults current at schedule time, so a settings change reaches the next cluster [evidence: test:tests/test_api_create_from_preset.py::test_defaults_filled_at_schedule]
- AC8: README, openapi.json and schema.d.ts match the app [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC9: targeted tests, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_create_from_preset.py tests/test_api_clusters.py tests/test_clusters_repo.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]
- AC10: a preset that leaves replicas unset schedules settings.default_replicas, the Default schedules its stored 1, and a raw spec POST without replicas is unchanged [evidence: test:tests/test_api_create_from_preset.py::test_replicas_filled_from_settings_at_schedule]
- AC11: after the 5th generated-slug clash the answer is 409 conflict, never 500 [evidence: test:tests/test_api_create_from_preset.py::test_generated_slug_exhausted_409]

#### Files

- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/db/clusters.py`
- `tests/test_api_create_from_preset.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

#### Interfaces

- `POST /api/v1/clusters` body `{"slug"?, "spec"?, "preset_id"?}` (part `orch-cluster-create-api`, defined in README.md; cross-epic contract of the same name, consumer agents-helmfile smoke).
- `ClusterView.preset_id`, `ClusterView.preset_name`; `db/clusters.Cluster.preset_id`, `.preset_name`; `db/clusters.create(conn, slug, spec, preset_id=None, preset_name=None)`.
- Uses `spec.generated_slug` (slugify-helper), `db/presets.get_for_share` (presets-repo), `check_spec` (check-spec-public).

#### Expected outcome

A cluster can be scheduled with nothing but a preset id; it owns a full copy of the preset's spec as filled at that moment and remembers the preset's id and name.

#### Steps

- Write `tests/test_api_create_from_preset.py` with the nine tests named in the AC refs; run `uv run pytest -q -p no:cacheprovider tests/test_api_create_from_preset.py`: fails.
- Change `CreateCluster`, `ClusterView`, `Cluster`, `create` and `create_cluster`; run the file and `tests/test_api_clusters.py tests/test_clusters_repo.py`: pass.
- Update README, regenerate `openapi.json` and `schema.d.ts`; run the verify command: passes.

#### Notes

- `repo.create` opens a nested transaction (a savepoint), so a generated-slug clash can be retried inside the outer creation transaction without losing the advisory lock.
- A preset deleted between the read and the insert is impossible while it is held `FOR SHARE`.
- `tests/factories.py:insert_cluster` keeps working because the new columns are nullable.
- `orch bench`, `scripts/smoke.sh` and the kind e2e send `{"slug", "spec"}` and stay valid.
- Builder check ruling 1 (2026-10-23): on the preset path only, the schedule-time fill sets replicas from settings.default_replicas when the preset leaves replicas unset (alongside the existing write-time fills). The raw-spec POST path is unchanged. The seeded Default stores replicas 1 explicitly, so it schedules 1.
- Builder check ruling 3 (2026-10-23): after the 5th generated-slug clash the API answers 409 conflict (the existing conflict code), never 500.

- 2026-10-23 amended: builder check rulings 1, 3: preset-path replicas fill from settings.default_replicas; 409 after the 5th slug clash (AC10, AC11)

### S5: fe new cluster dialog

- Status: done
- Files: `frontend/src/api/client.ts`, `frontend/src/clusters/NewClusterDialog.tsx`, `frontend/src/clusters/NewClusterDialog.test.tsx`, `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `frontend/src/layout/TopBar.tsx`, `frontend/src/layout/TopBar.test.tsx`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/clusters/NewClusterDialog.test.tsx src/App.test.tsx src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build && mise x node@24.20.0 -- npm --prefix frontend run check:api`
- Verified head: 9a4609272559b15fff2c9f4b82883eb5a08375ef

#### Requirement

Schedule clusters from a preset in the UI and show where a cluster came from (design D6; user Q1, Q9), test-first. Builds on the merged web-ui-cluster-tabs-with-fil `App.tsx`, `TopBar.tsx` and their tests.

- `frontend/src/api/client.ts` (part `fe-preset-client`): type aliases `PresetView`, `PresetIn`, `CopyPreset` from `./schema`; `listPresets()`, `getPreset(id)`, `createPreset(body)`, `updatePreset(id, body)`, `deletePreset(id)`, `copyPreset(id, body?)` on `/presets`; `createCluster` takes a body typed as the regenerated `CreateCluster` (exactly one of `spec` or `preset_id` at runtime); `ClusterForm` create mode, still in the tree, keeps compiling against it; every task leaves `npm run build` and `npm run check:api` green.
- New `frontend/src/clusters/NewClusterDialog.tsx`: `NewClusterDialog({open, onClose, onCreated})`. On open it loads `listPresets()`; a preset `Select` (label "Preset") lists every preset by name with the default preselected; an optional "Slug" field with helper text saying an empty slug is generated from the preset name; a non-empty slug longer than `MAX_SLUG` blocks Create. Create posts `{preset_id}` plus `slug` only when non-empty, then calls `onCreated(cluster)`. There is no other field. A server error (404, 409, 422, the 422 naming the preset) shows in an outlined Alert and the dialog stays open.
- `frontend/src/App.tsx`: New cluster opens `NewClusterDialog` instead of `ClusterForm mode="create"`; on create the new cluster's tab is selected.
- `frontend/src/layout/TopBar.tsx`: a cluster tab shows `preset_name` as a caption under the slug when it is set; no marker shows that the preset changed after create (Q9).
- Tests: new `frontend/src/clusters/NewClusterDialog.test.tsx`; `frontend/src/App.test.tsx` `create_and_discard_from_top_bar` drives the new dialog; `frontend/src/layout/TopBar.test.tsx` gains `tab_shows_preset_name`. All pass `designRules`.

#### Acceptance conditions

- AC1: the dialog lists presets with the default preselected and has no field besides Preset and Slug [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/NewClusterDialog.test.tsx -t preselects_default_and_only_preset_and_slug]
- AC2: Create sends only preset_id when the slug is empty and preset_id with slug when given, then calls onCreated [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/NewClusterDialog.test.tsx -t sends_preset_id_and_optional_slug]
- AC3: a server 422 naming the preset is shown and the dialog stays open; an over-long slug blocks Create [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/NewClusterDialog.test.tsx -t shows_server_error_and_blocks_long_slug]
- AC4: New cluster in the top bar opens the preset dialog and selects the created cluster; Discard still opens the discard dialog [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t create_and_discard_from_top_bar]
- AC5: a cluster tab shows its preset_name caption [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/layout/TopBar.test.tsx -t tab_shows_preset_name]
- AC6: the preset client functions call the documented routes [evidence: symbol:frontend/src/api/client.ts::listPresets]
- AC7: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/clusters/NewClusterDialog.test.tsx src/App.test.tsx src/layout/TopBar.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC8: createCluster takes the regenerated CreateCluster body, ClusterForm create mode still compiles, and build and check:api pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend run build && mise x node@24.20.0 -- npm --prefix frontend run check:api]

#### Files

- `frontend/src/api/client.ts`
- `frontend/src/clusters/NewClusterDialog.tsx`
- `frontend/src/clusters/NewClusterDialog.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/layout/TopBar.tsx`
- `frontend/src/layout/TopBar.test.tsx`

#### Interfaces

- `api/client.ts` (part `fe-preset-client`): `PresetView`, `PresetIn`, `CopyPreset`, `listPresets`, `getPreset`, `createPreset`, `updatePreset`, `deletePreset`, `copyPreset`; consumed by fe-preset-form and fe-presets-page.
- `NewClusterDialog({open, onClose, onCreated: (cluster: ClusterView) => void})`.
- `TopBar` props unchanged; the tab label reads `cluster.preset_name`.

#### Expected outcome

Clicking New cluster asks for a preset (Default preselected) and an optional slug, creates the cluster and opens its tab; every tab shows which preset it came from.

#### Steps

- Write `NewClusterDialog.test.tsx` (`// @vitest-environment jsdom`, stub `window.matchMedia`, `vi.mock('../api/client')` like the other tests; titles as in the AC refs), update `App.test.tsx` and add `tab_shows_preset_name` to `TopBar.test.tsx`; run `mise x node@24.20.0 -- npm --prefix frontend test -- src/clusters/NewClusterDialog.test.tsx src/App.test.tsx src/layout/TopBar.test.tsx`: fails.
- Add the client functions, the dialog, the App wiring and the tab caption; run the verify command: passes.

#### Notes

- `schema.d.ts` already carries the preset and create schemas (tasks preset-routes and create-cluster-from-preset); never hand-edit it.
- `ClusterForm` stays in the tree until fe-preset-form; App simply stops opening it.
- The tab caption must fit the phone top bar (tabs scroll); use `Typography variant="caption"`.
- Builder check ruling 9 (2026-10-23): createCluster takes a body typed as the regenerated CreateCluster (exactly one of spec or preset_id at runtime); ClusterForm create mode keeps compiling; every task leaves `npm run build` and `npm run check:api` green.

- 2026-10-23 amended: builder check ruling 9: createCluster typed as CreateCluster, build and check:api green (AC8 added)

### S6: fe preset form

- Status: done
- Files: `frontend/src/clusters/ClusterForm.tsx`, `frontend/src/presets/PresetForm.tsx`, `frontend/src/clusters/ClusterForm.test.tsx`, `frontend/src/presets/PresetForm.test.tsx`, `frontend/src/clusters/clusterSpecForm.ts`, `frontend/src/clusters/DiscardClusterDialog.test.tsx`, `frontend/src/api/client.ts`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetForm.test.tsx src/clusters/DiscardClusterDialog.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: 9fb81a85a04f4768958d33369b46120fdeaa0b70

#### Requirement

Turn the cluster form into the preset editor and remove the cluster edit path (design D2, D5, D6; user Q4, Q5, Q7, Q8), test-first.

- `git mv frontend/src/clusters/ClusterForm.tsx frontend/src/presets/PresetForm.tsx` and rewrite it as `PresetForm({open, preset?, copyOf?, onClose, onSaved})` (part `fe-preset-form`): new (neither prop), edit (`preset`) and copy (`copyOf`, name prefilled `<source name> copy` with the source part cut to fit 40 characters and right-trimmed, saved as a new preset). A "Name" field replaces Slug, checked client-side with the Q8 rules (1 to 40 characters of letters, digits, spaces, dots, dashes, underscores; leading or trailing spaces give an inline error and are never trimmed); the default preset's name is read-only in edit. PVC size is editable and optional in every mode. Save: new and copy call `createPreset`, edit calls `updatePreset`; a 409 or 422 shows in an outlined Alert.
- Sparse saving (Q7) in `frontend/src/clusters/clusterSpecForm.ts`: `FormValues.name` replaces `slug`; a form state built from /meta and a stored preset spec shows the stored value for every stored key and the /meta default (`blankValues(meta)`) for every other field, and records which fields are set (stored keys, plus every field the user changes); clearing a field always means unset: the key is omitted from the stored spec, never stored as null, and numbers like replicas or max_attempts fall back to defaults at schedule; the Model and Effort selects show a stored value that is not in the /meta lists as an extra option labelled `<value> (not available)`; `toPresetSpec(values, setKeys)` returns only the set fields as ClusterSpec keys. `validate(values, meta)` loses its `mode` parameter (name rules instead of slug; PVC size not required). `MAX_SLUG` stays exported (NewClusterDialog uses it). Remove what only the cluster create and edit modes used.
- Retire the cluster edit path: `patchCluster` and the `PatchCluster` alias leave `frontend/src/api/client.ts`; no `mode` prop or `'edit'` path remains.
- Tests: `git mv frontend/src/clusters/ClusterForm.test.tsx frontend/src/presets/PresetForm.test.tsx`, rewritten for the preset editor; its `DiscardClusterDialog` tests (re-read from `ClusterForm.test.tsx` as merged by web-ui-cluster-tabs-with-fil; the Ribbon-created cases are already gone there) move unchanged to a new `frontend/src/clusters/DiscardClusterDialog.test.tsx`. The retirement test runs `git ls-files src/clusters/ClusterForm.tsx src/clusters/ClusterForm.test.tsx` with `node:child_process` from the frontend dir and expects empty output, and reads `src/api/client.ts` to assert it contains neither `patchCluster` nor `PatchCluster`.

#### Acceptance conditions

- AC1: a new preset shows every /meta default and saving untouched sends only the name and an empty spec; a changed field is sent [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t new_preset_prefills_defaults_saves_only_set_fields]
- AC2: editing shows stored values and defaults for the rest, keeps stored keys and PUTs through updatePreset [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t edit_round_trips_stored_fields]
- AC3: copy prefills from the source with the name "<source> copy" (source part cut to fit 40 characters and right-trimmed) and creates a new preset [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t copy_prefills_from_source]
- AC4: the default preset's name is read-only, name rules are validated (a leading or trailing space gives an inline error), PVC size is editable [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t name_rules_default_name_and_pvc]
- AC5: a server 409 or 422 is shown in an Alert [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t shows_server_errors]
- AC6: ClusterForm.tsx and ClusterForm.test.tsx are gone from git ls-files and client.ts has no patchCluster or PatchCluster [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t cluster_edit_path_retired]
- AC7: the discard dialog tests pass from their new file [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/DiscardClusterDialog.test.tsx]
- AC8: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetForm.test.tsx src/clusters/DiscardClusterDialog.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC9: a stored model or effort outside the /meta lists shows as an extra option "<value> (not available)" and round-trips unchanged [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t edit_shows_unavailable_stored_value]
- AC10: clearing a field omits its key from the saved spec and never sends null [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t clearing_a_field_unsets_it]

#### Files

- `frontend/src/clusters/ClusterForm.tsx`
- `frontend/src/presets/PresetForm.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`
- `frontend/src/presets/PresetForm.test.tsx`
- `frontend/src/clusters/clusterSpecForm.ts`
- `frontend/src/clusters/DiscardClusterDialog.test.tsx`
- `frontend/src/api/client.ts`

#### Interfaces

- `PresetForm({open, preset?: PresetView, copyOf?: PresetView, onClose, onSaved: (preset: PresetView) => void})` in `frontend/src/presets/PresetForm.tsx` (part `fe-preset-form`, consumed by fe-presets-page).
- `clusterSpecForm.ts`: `FormValues.name`, `blankValues(meta)`, the preset form-state builder, `toPresetSpec(values, setKeys)`, `validate(values, meta)`, `MAX_SLUG`.
- `api/client.ts` without `patchCluster` and `PatchCluster`.

#### Expected outcome

The form that used to create and edit clusters now creates, edits and copies presets, saving only what the user set, and nothing in the frontend can edit a running cluster.

#### Steps

- `git mv` the form and its test, write the preset tests and the retirement test (titles as in the AC refs), move the discard tests to `DiscardClusterDialog.test.tsx`; run `mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetForm.test.tsx src/clusters/DiscardClusterDialog.test.tsx`: fails.
- Rewrite `PresetForm.tsx` and `clusterSpecForm.ts`, drop `patchCluster` and `PatchCluster` from `client.ts`; run the verify command: passes.

#### Notes

- Deletion of the edit path is pinned by `cluster_edit_path_retired` (deletion pinned by a retirement test).
- Keep the Model and Effort selects, env rows, any-mcp JSON and resource fields from cluster-form-defaults-and-ga; only the slug, mode and PATCH parts change.
- Clearing a field always means unset (ruling 5): the key is omitted, never stored as null; this replaces the earlier nullable-key choice.
- Builder check ruling 2 (2026-10-23): PUT of a preset accepts a stored model, effort or image that is no longer in the settings lists only when that value is unchanged from the stored preset (the legacy rule PATCH used); changing to an unknown value is 422. validate_spec keeps its `stored` parameter (and check_spec its `stored` parameter) for this; retire-spec-update-repo must not delete it, it still deletes update_spec and ClusterDeleting if unused. Scheduling always validates fully (no `stored`) and returns 422 with the reason and the preset name. The editor's Model/Effort select shows a stored out-of-list value as an extra option labelled "<value> (not available)".
- Builder check ruling 4 (2026-10-23): names with leading or trailing spaces are rejected (422 on the API, inline error in the form); the API never trims. The copy name's source part is cut to fit 40 characters and right-trimmed before " copy".
- Builder check ruling 5 (2026-10-23): clearing a field always means unset: the key is omitted from the stored spec, never stored as null; numbers like replicas or max_attempts cleared fall back to defaults at schedule.
- Builder check ruling 8 (2026-10-23): re-read ClusterForm.test.tsx as merged by web-ui-cluster-tabs-with-fil and move the discard-dialog tests; the Ribbon-created cases are already gone there.

- 2026-10-23 amended: builder check rulings 2, 4, 5, 8: not-available option, name spaces, clear means unset, discard tests from merged file (AC3, AC4 rewritten, AC9, AC10 added)

### S7: fe presets page

- Status: done
- Files: `frontend/src/presets/PresetsPage.tsx`, `frontend/src/presets/PresetsPage.test.tsx`, `frontend/src/App.tsx`, `frontend/src/App.test.tsx`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetsPage.test.tsx src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: 477e2f527b67d15d63d335c98e433b6103a09883

#### Requirement

Add Presets as the first settings category and its page (design D7; user Q5, Q10), test-first.

- New `frontend/src/presets/PresetsPage.tsx`: `PresetsPage({onBack})`, a full main-area view: a "Presets" heading, a "Back" button calling `onBack`, a "New preset" button, and the preset list from `listPresets()` (default first, marked with a "Default" chip). Each row offers Edit, Copy and Delete; the default row has no Delete. New, Edit and Copy open `PresetForm` (new, `preset`, `copyOf`); Delete asks through `ConfirmDialog` and then calls `deletePreset`; the list reloads after every save or delete; a server error (409 `preset_default`, `last_preset`, `conflict`) shows in an outlined Alert.
- `frontend/src/App.tsx`: passes `settingsCategories=[{id: 'presets', label: 'Presets', onOpen}]` through `TopBar` to `SessionsMenu` (cross-epic contract `orch-settings-menu`); `onOpen` replaces the main-area content with `PresetsPage` (App `view` state `cluster` or `presets`, no router); Back, or choosing a session in the menu, returns to the cluster view. The top bar stays visible.
- Tests: new `frontend/src/presets/PresetsPage.test.tsx`; `frontend/src/App.test.tsx` gains `presets_from_settings_menu`. All pass `designRules`.

#### Acceptance conditions

- AC1: the page lists presets with the default marked and without a Delete action on it [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetsPage.test.tsx -t lists_presets_default_marked_without_delete]
- AC2: New preset, Edit and Copy open the preset form in the matching mode and the list reloads after save [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetsPage.test.tsx -t new_edit_copy_open_form_and_reload]
- AC3: Delete confirms, calls deletePreset and reloads; a 409 is shown [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetsPage.test.tsx -t delete_confirms_and_shows_conflict]
- AC4: Back calls onBack [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetsPage.test.tsx -t back_calls_on_back]
- AC5: the hamburger menu's Settings section lists Presets, which shows the page in the main area, and Back returns to the cluster tab [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t presets_from_settings_menu]
- AC6: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetsPage.test.tsx src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

#### Files

- `frontend/src/presets/PresetsPage.tsx`
- `frontend/src/presets/PresetsPage.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`

#### Interfaces

- `PresetsPage({onBack: () => void})` in `frontend/src/presets/PresetsPage.tsx`.
- Uses `SessionsMenu` `settingsCategories: {id, label, onOpen}[]` through `TopBar` (cross-epic contract `orch-settings-menu`), `PresetForm` (fe-preset-form), the preset client functions (fe-preset-client), `ConfirmDialog` (`layout/ConfirmDialog.tsx`).

#### Expected outcome

Opening the hamburger menu shows Presets under Settings; it opens a page listing every preset where the user creates, copies, edits and deletes presets, and Back returns to the cluster tabs.

#### Steps

- Write `PresetsPage.test.tsx` and add `presets_from_settings_menu` to `App.test.tsx` (titles as in the AC refs); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetsPage.test.tsx src/App.test.tsx`: fails.
- Build the page and the App view switch; run the verify command: passes.

#### Notes

- web-ui-cluster-tabs-with-fil passes an empty `settingsCategories` from App; this task supplies the one entry.
- Delete is offered only for non-default presets, but the page still shows a 409 from the server (for example `last_preset`).

### S8: retire cluster patch route

- Status: done
- Files: `src/agent_orchestrator/api/clusters.py`, `src/agent_orchestrator/api/schemas.py`, `tests/test_api_clusters.py`, `README.md`, `MEMORY.md`, `openapi.json`, `frontend/src/api/schema.d.ts`
- Verify: `mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_clusters.py tests/test_api_presets.py tests/test_api_create_from_preset.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && mise x node@24.20.0 -- npm --prefix frontend run build && uv run ruff check . && uv run ruff format --check .`
- Verified head: 97af5310b0335f47c62c74b8a20674460e70dce4

#### Requirement

Retire live cluster edit from the API (design D5; user Q4 and N2), test-first; the frontend stopped calling it in fe-preset-form.

- `api/clusters.py`: delete `patch_cluster`; `check_spec(spec, settings, stored=None)` keeps its `stored` parameter, which the preset PUT uses (builder check ruling 2).
- `api/schemas.py`: delete `PatchCluster`.
- `tests/test_api_clusters.py`: delete `test_patch_bumps_generation`, `test_patch_keeps_stored_legacy_model_and_effort` and the PATCH calls in `test_delete_is_discard_without_purge`; `test_spec_hardening_enforced_on_create_and_patch` becomes create-only; `test_write_fills_default_resources_per_key` and `test_patch_high_request_without_limit` keep their write-time fill coverage through POST. Add the retirement test `test_patch_cluster_retired_405`: `PATCH /api/v1/clusters/{id}` on an existing cluster answers 405, the app has no PATCH route under `/api/v1`, and `openapi.json` has no `patch` operation.
- README: the `### PATCH /api/v1/clusters/{cluster_id}` section is removed; every other README mention of editing a running cluster is removed or rewritten (a spec is fixed at create; to change it, discard and schedule again from a preset); the `Versioning` paragraph keeps "additive only" and adds a documented exception dated 2026-10-23 naming the PATCH removal and the create body that needs exactly one of `spec` and `preset_id`, with the why (a live edit rolled every agent pod; clusters now snapshot their preset).
- `MEMORY.md`: a dated (2026-10-23) entry for the exception and why.
- `openapi.json` and `frontend/src/api/schema.d.ts` regenerated; `npm run build` stays green (client.ts no longer names `PatchCluster`).

#### Acceptance conditions

- AC1: PATCH on an existing cluster answers 405, no PATCH route exists under /api/v1, and openapi.json has no patch operation [evidence: test:tests/test_api_clusters.py::test_patch_cluster_retired_405]
- AC2: the spec hardening and write-time fill tests pass through POST only [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_api_clusters.py]
- AC3: patch_cluster and PatchCluster are gone from the api package [evidence: command:! grep -rnE 'patch_cluster|PatchCluster' src/agent_orchestrator/api]
- AC4: README documents the additive-only exception with date and why, and no PATCH section remains [evidence: doc-section:README.md#API]
- AC5: MEMORY.md records the exception with the date and why [evidence: judgement:MEMORY.md entry dated 2026-10-23 reviewed]
- AC6: README, openapi.json and schema.d.ts match the app and the frontend builds [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC7: targeted tests and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_clusters.py tests/test_api_presets.py tests/test_api_create_from_preset.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `tests/test_api_clusters.py`
- `README.md`
- `MEMORY.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

#### Interfaces

- `check_spec(spec, settings) -> ClusterSpec` (part `check-spec-public`, final signature).
- `PATCH /api/v1/clusters/{cluster_id}` no longer exists; GET and DELETE on the path are unchanged.

#### Expected outcome

The API cannot change a running cluster's spec any more; README, MEMORY and OpenAPI say so and why.

#### Steps

- Add `test_patch_cluster_retired_405` and rewrite the PATCH-based tests to POST; run `uv run pytest -q -p no:cacheprovider tests/test_api_clusters.py`: the retirement test fails.
- Delete the route and schema, edit README and MEMORY, regenerate `openapi.json` and `schema.d.ts`; run the verify command: passes.

#### Notes

- Deletion pinned by a retirement test (`test_patch_cluster_retired_405`).
- FastAPI answers 405 for a known path with an unknown method; `api/errors.py` maps it to `bad_request`, which the test may assert.
- `cluster_deleting` stays: messages and checks still return it.
- fe-preset-form already removed `PatchCluster` from `client.ts`, so `npm run build` stays green after the schema regen.
- Builder check ruling 2 (2026-10-23): PUT of a preset accepts a stored model, effort or image that is no longer in the settings lists only when that value is unchanged from the stored preset (the legacy rule PATCH used); changing to an unknown value is 422. validate_spec keeps its `stored` parameter (and check_spec its `stored` parameter) for this; retire-spec-update-repo must not delete it, it still deletes update_spec and ClusterDeleting if unused. Scheduling always validates fully (no `stored`) and returns 422 with the reason and the preset name. The editor's Model/Effort select shows a stored out-of-list value as an extra option labelled "<value> (not available)".

- 2026-10-23 amended: builder check ruling 2: check_spec keeps stored for the preset PUT (AC3 grep narrowed)

### S9: kind e2e presets

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`, `e2e/values-kind.yaml`
- Verify: `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: a7b8b4a57173b226cd35ba808218ca707fc4608d

#### Requirement

Prove presets end to end through the public API on kind (design D8; headless parity, user Q1 to Q4), in `tests/e2e/test_e2e_kind.py` (marker `e2e`, run by `mise run test:e2e` and the PR CI `e2e` job). Only `/api/v1` over the port-forward is used; kubectl only for the existing pod and label assertions.

- The module `cluster` fixture creates a preset through `POST /presets` (`replicas: 2`, `peers: true`, `env: FAKE_TURN_ENV`) and schedules the shared cluster with `POST /clusters {"preset_id", "slug": SLUG}`; the view carries `preset_id` and `preset_name`; the rest of the module is unchanged.
- Teardown: every test deletes each cluster it creates; check `e2e/values-kind.yaml` and raise `ORCH_MAX_CLUSTERS` there only if needed. The generated-slug cluster is 1 replica.
- The Default preset is never edited in e2e; edit and delete act on the test's own preset or a copy.
- `test_default_preset_listed`: `GET /presets` lists the seeded default, asserts it exists, is `is_default`, and its spec `replicas` is 1.
- `test_preset_edit_and_delete_leave_cluster_unchanged`: after the cluster is ready, `PUT` the preset (`replicas: 1`) and then `POST .../copy`; the cluster's `spec` and `generation` are unchanged and its pod names and pod uids stay the same; then `DELETE` the source preset (204): the cluster's `preset_id` is null, `preset_name` is kept, `spec` and `generation` unchanged. Runs after the round-robin tests so their pods are not disturbed, and deletes the copy at the end.
- `test_schedule_default_preset_generated_slug`: `POST /clusters {"preset_id": <default id>}` is 201 with a slug matching `^default-[a-z]{4}$` and `spec.replicas == 1`; the test discards that cluster at once and waits until its row is gone.
- `test_patch_cluster_retired`: `PATCH /clusters/{id}` answers 405.
- `test_delete_default_preset_refused`: `DELETE /presets/{default id}` is 409 `preset_default`.

#### Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: the tests cover preset listing, schedule from a preset with explicit and generated slug, edit, copy and delete leaving the cluster unchanged, the default delete refusal and PATCH 405, through the public API only [evidence: judgement:tests/e2e/test_e2e_kind.py reviewed against the requirement; executed by the PR CI e2e job]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]
- AC4: test_default_preset_listed asserts the Default exists, is_default is true and its spec replicas is 1; no e2e test edits the Default [evidence: test:tests/e2e/test_e2e_kind.py::test_default_preset_listed]
- AC5: every cluster an e2e test creates is deleted in that test's teardown [evidence: judgement:tests/e2e/test_e2e_kind.py teardown reviewed; executed by the PR CI e2e job]

#### Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/values-kind.yaml` (only if `ORCH_MAX_CLUSTERS` needs raising, ruling 6)

#### Interfaces

- Uses `/api/v1/presets` routes (part `orch-presets-api`) and the preset create body (part `orch-cluster-create-api`).
- Existing fixtures `api`, `baseline`, `cluster`, `round_robin` and helpers `wait_for`, `agents_of`, `kubectl` in `tests/e2e/test_e2e_kind.py`.

#### Expected outcome

The PR CI e2e job shows on a real kind cluster that presets drive scheduling and that preset changes never touch a running cluster.

#### Steps

- Change the `cluster` fixture and add the five tests; run `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`: the new tests are listed.
- Run the verify command: passes. The full run happens in CI (no cluster access here).

#### Ruling

- 2026-10-24 accepted: kind e2e cannot run in this container (no cluster); verified by collection and lint here; the PR CI e2e job runs it on kind

#### Notes

- Order the new tests after the round-robin and before the discard test (the module runs in file order and shares one cluster).
- The generated-slug cluster costs one more reconcile; discard it immediately and wait only for its row to disappear, bounded like the existing discard wait.
- Pod uids come from `kubectl get pods -l agents.szymonrichert.pl/cluster=<SLUG> -o jsonpath`.
- Builder check ruling 6 (2026-10-23): tests delete every cluster they create in teardown; the builder checks e2e/values-kind.yaml and raises ORCH_MAX_CLUSTERS there only if needed; the generated-slug cluster is 1 replica.
- Builder check ruling 7 (2026-10-23): never edit the Default in e2e; edit and delete a copy. test_default_preset_listed asserts the Default exists, is_default, and its spec replicas is 1.

- 2026-10-23 amended: builder check rulings 6, 7: teardown deletes clusters, Default never edited (AC4, AC5 added)

### S10: presets review fixes

- Status: done
- Files: `tests/test_migrations.py`, `frontend/src/presets/PresetForm.tsx`, `frontend/src/presets/PresetForm.test.tsx`, `README.md`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_migrations.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check . && mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build`
- Verified head: 27eeef96b9d6d9dd20c548a257f080e77eb3d124

#### Requirement

Close the cluster-presets epic review findings (2026-10-24).

1. Upgrade path test: tests/test_migrations.py gains a test that applies only 0001 (run_migrations against a directory holding 0001 alone), inserts a cluster row, then applies the full migrations directory, and asserts the existing cluster keeps its spec, has preset_id and preset_name null, and the Default preset exists.
2. PresetForm loses early edits: frontend/src/presets/PresetForm.tsx rebuilds the form when /meta resolves and drops what the user typed before. Either keep the fields disabled until /meta has loaded or merge the meta-derived defaults under the user's already-set keys; edits made before /meta arrives must never be lost.
3. README writers table (README.md Data model single-writer rows): note that clusters.preset_id is also set to null by the ON DELETE SET NULL cascade when the api deletes a preset (an api-originated write, design D1).

#### Acceptance conditions

- AC1: 0002 applied on top of a 0001 database with a cluster keeps the cluster and leaves preset_id and preset_name null [evidence: test:tests/test_migrations.py::test_presets_migration_on_existing_clusters]
- AC2: a field edited before /meta resolves keeps its value after /meta arrives [evidence: command:mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetForm.test.tsx -t "keeps edits made before meta loads"]
- AC3: the README single-writer rows mention the preset delete cascade on clusters.preset_id [evidence: doc-section:README.md#data-model]

#### Files

- `tests/test_migrations.py`
- `frontend/src/presets/PresetForm.tsx`
- `frontend/src/presets/PresetForm.test.tsx`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The migration upgrade path is tested, early PresetForm edits survive /meta loading, and the README writers table is accurate.

#### Steps

- Write the AC1 and AC2 tests and run the verify command: they fail.
- Implement the fixes and the README note.
- Run the verify command: all pass.

#### Ruling

- 2026-10-24 accepted: AC3 note present at README.md:313 (doc-section anchor check misfired); red shown by orchestrator: PresetForm early-edit test fails against the pre-fix component (1 failed) and passes on HEAD; migration upgrade test is a characterization test of already-safe SQL

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S11: retire spec update repo

- Status: done
- Files: `src/agent_orchestrator/db/clusters.py`, `src/agent_orchestrator/spec.py`, `tests/test_clusters_repo.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_clusters_repo.py tests/test_api_clusters.py tests/test_api_messages.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 79cc4d6836fbbe378c988ce7cd24ffdcd5b4950d

#### Requirement

Remove the dead code live edit leaves behind (design D5; user N2), test-first.

- `src/agent_orchestrator/db/clusters.py`: delete `update_spec` and `ClusterDeleting` (its only user); the module docstring stays accurate.
- `src/agent_orchestrator/spec.py`: `validate_spec(spec, settings, stored=None)` keeps its `stored` parameter, which the preset PUT uses (a stored model or effort outside the settings lists is accepted only when unchanged); it is not deleted and the docstring says why it stays.
- `tests/test_clusters_repo.py`: delete `test_update_bumps_generation_and_notifies` and the `update_spec`/`ClusterDeleting` lines of `test_delete_marks_deleting`; add the retirement test `test_live_edit_code_retired`: `agent_orchestrator.db.clusters` has no `update_spec` and no `ClusterDeleting`, and `inspect.signature(validate_spec)` still has the `stored` parameter; add `test_validate_spec_stored_exception_kept`: an unchanged stored model outside the settings list passes and a changed one is rejected.
- No `update_spec` or `ClusterDeleting` reference remains in `src/` or `tests/`, and no cluster route passes a stored spec to `validate_spec` (only the preset PUT does).

#### Acceptance conditions

- AC1: update_spec and ClusterDeleting are gone and validate_spec keeps its stored parameter [evidence: test:tests/test_clusters_repo.py::test_live_edit_code_retired]
- AC2: validate_spec accepts a model or effort outside the settings lists only when unchanged from stored, and rejects a changed one [evidence: test:tests/test_clusters_repo.py::test_validate_spec_stored_exception_kept]
- AC3: no reference to the removed symbols remains [evidence: command:! grep -rnE 'update_spec|ClusterDeleting' src tests --include=*.py]
- AC4: targeted tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_clusters_repo.py tests/test_api_clusters.py tests/test_api_messages.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/db/clusters.py`
- `src/agent_orchestrator/spec.py`
- `tests/test_clusters_repo.py`

#### Interfaces

- `spec.validate_spec(spec: ClusterSpec, settings: Settings, stored: ClusterSpec | None = None) -> None` (unchanged signature).
- `db/clusters.py` without `update_spec` and `ClusterDeleting`.

#### Expected outcome

The repository and spec module carry no code that only live edit used.

#### Steps

- Add `test_live_edit_code_retired` and `test_validate_spec_stored_exception_kept`, drop the update tests; run `uv run pytest -q -p no:cacheprovider tests/test_clusters_repo.py`: the retirement test fails.
- Delete `update_spec` and `ClusterDeleting`; run the verify command: passes.

#### Notes

- Deletion pinned by a retirement test (`test_live_edit_code_retired`).
- The api no longer passes `stored` from a cluster route after retire-cluster-patch-route; the preset PUT does (ruling 2).
- Builder check ruling 2 (2026-10-23): PUT of a preset accepts a stored model, effort or image that is no longer in the settings lists only when that value is unchanged from the stored preset (the legacy rule PATCH used); changing to an unknown value is 422. validate_spec keeps its `stored` parameter (and check_spec its `stored` parameter) for this; retire-spec-update-repo must not delete it, it still deletes update_spec and ClusterDeleting if unused. Scheduling always validates fully (no `stored`) and returns 422 with the reason and the preset name. The editor's Model/Effort select shows a stored out-of-list value as an extra option labelled "<value> (not available)".

- 2026-10-23 amended: builder check ruling 2: validate_spec keeps stored (AC1, AC2 rewritten)

### S12: deploy pin presets

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agent-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `mise x -- uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster" && uv run ruff check . && uv run ruff format --check .`
- Verified head: de32698be99231c41560c1da2f6eebb9d216b343

#### Requirement

Pin agents-helmfile to this epic's merged agent-orchestrator build (design D9; precedent `docs/plans/done/cluster-form-defaults-and-ga/tasks/deploy-pin-d5a7738.md`; web-ui-cluster-tabs-with-fil task deploy-pin set the current pins).

The value is `9ab0d60`: agent-orchestrator main merge of szymonrychu/agent-orchestrator#5 (full `9ab0d60e9e4675d4314c6b6b8ed3e0e29de74b50`). The agents-helmfile integration branch for this epic must start from agents-helmfile main `78299cc` (the web-ui deploy pin).

- `helmfile.yaml.gotmpl`: release `agent-orchestrator` chart version `0.1.0-main.9ab0d60`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `9ab0d60`. The wrapper image pins, `ORCH_ALLOWED_ORIGINS` and the ingress settings stay as they are.
- `tests/test_orchestrator_release.py`: `test_orchestrator_pin_matches_image` asserts the chart version and the image tag both carry `9ab0d60`, reading `helmfile.yaml.gotmpl` as text (no `helmfile build`, so it runs without pulling charts).
- Nothing else changes. `scripts/smoke.sh` keeps its raw spec create (Q2). `helmfile apply` and `mise run smoke` are run by the user after the epic.

#### Acceptance conditions

- AC1: chart version and image tag agree on the orchestrator sha and the test runs offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: only the orchestrator chart version and image tag change; the wrapper pins and ORCH_ALLOWED_ORIGINS stay [evidence: judgement:the task diff reviewed against the requirement]
- AC3: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster" && uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

- Consumes the published chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (contracts `agent-orchestrator-chart`, `agent-orchestrator-image`).

#### Expected outcome

`helmfile diff` shows only the agent-orchestrator chart version and image tag changing to this epic's merge.

#### Steps

- Update `test_orchestrator_pin_matches_image` to the new sha and to read `helmfile.yaml.gotmpl` as text; run `uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k test_orchestrator_pin_matches_image`: fails.
- Change the two pins; run the verify command: passes.

#### Notes

- Check the chart and image exist before pinning when credentials allow (`helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version 0.1.0-main.<sha7>`).
- `test_release_chart_version_and_needs` and `test_db_secret_matches_rendered_cnpg_cluster` build the helmfile and pull charts; they fail here on network policy and are deselected in the verify, not changed.
- Apply and smoke are not this task's verify; the user runs them.
- Builder check ruling 10 (2026-10-23): excluded from the build run; it runs after the orchestrator PR merges, its sha filled with ticket.py amend, same as web-ui's deploy-pin.

- 2026-10-24 run cluster-presets: dependency-failed on kind-e2e-presets

- 2026-10-24 amended: orchestrator PR #5 merged as 9ab0d60

### S13: spa method not allowed

- Status: done
- Files: `src/agent_orchestrator/api/spa.py`, `tests/test_spa.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_spa.py tests/test_api_clusters.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: c97945194b58d4115086891a6888cc8fcce1ba33

#### Requirement

CI e2e (kind, real image) failure on PR szymonrychu/agent-orchestrator#5: tests/e2e/test_e2e_kind.py::test_patch_cluster_retired gets 404 {"error":{"code":"not_found","message":"not found"}} instead of 405. Cause: the image sets ORCH_STATIC_DIR, so api/app.py mounts SpaStaticFiles at "/"; Starlette prefers the mount's full match over the /api/v1/clusters/{id} route's partial (method) match, and SpaStaticFiles.get_response (api/spa.py) answers every `api/` path with 404 before any method check. The unit tests never mount the SPA, so they see FastAPI's 405.

Fix in src/agent_orchestrator/api/spa.py: a request whose method is not GET or HEAD is answered 405 Method Not Allowed (with an Allow: GET, HEAD header, as plain StaticFiles does) before the `api/` 404 branch; GET/HEAD to an unknown `api/` path still answers 404. Add unit tests that build the app with a static_dir (a temp dir with an index.html) and assert: PATCH /api/v1/clusters/<uuid> answers 405; GET /api/v1/unknown answers 404; GET / still serves index.html.

#### Acceptance conditions

- AC1: with the SPA mounted, PATCH /api/v1/clusters/{id} answers 405 [evidence: test:tests/test_spa.py::test_patch_cluster_405_with_spa_mounted]
- AC2: with the SPA mounted, GET of an unknown api path still answers 404 and GET / serves index.html [evidence: test:tests/test_spa.py::test_unknown_api_get_404_and_index_served]

#### Files

- `src/agent_orchestrator/api/spa.py`
- `tests/test_spa.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The kind e2e test_patch_cluster_retired passes in CI: PATCH on a cluster answers 405 with the SPA mounted.

#### Steps

- Write the AC tests in tests/test_spa.py and run the verify command: AC1 fails with 404.
- Answer non-GET/HEAD with 405 in SpaStaticFiles before the api/ 404 branch.
- Run the verify command: all pass.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none

## Rulings (migrated)

- kind-e2e-presets: accept true, at 2026-10-24T03:00:28Z: kind e2e cannot run in this container (no cluster); verified by collection and lint here; the PR CI e2e job runs it on kind
- presets-review-fixes: accept true, at 2026-10-24T03:16:50Z: AC3 note present at README.md:313 (doc-section anchor check misfired); red shown by orchestrator: PresetForm early-edit test fails against the pre-fix component (1 failed) and passes on HEAD; migration upgrade test is a characterization test of already-safe SQL
