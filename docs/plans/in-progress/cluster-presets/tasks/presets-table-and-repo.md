---
title: presets table and repo
status: done
repo: agent-orchestrator
value: presets are stored durably with a Default 1-pod preset that always exists
files: [src/agent_orchestrator/db/migrations/0002_presets.sql, src/agent_orchestrator/db/presets.py, tests/test_migrations.py, tests/test_presets_repo.py, README.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_migrations.py tests/test_presets_repo.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [presets-repo]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: 5
actual_roles: "impl 3, verify 2, review 1, land 1"
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/cluster-presets-presets-table-and-repo/agent-orchestrator
branch: "current worktree branch (commit e4aabae)"
verified_head: 233ff924f80b0f6e4ae4174d5b786adc77ad259f
run: cluster-presets
provides: [presets-repo]
acs_for_audit: [AC8]
process_gaps: []
fork_point: eac3b59b3cd94534dff90ae9d44a175617504ddd
---

# presets table and repo

## Requirement

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

## Acceptance conditions

- AC1: a fresh database has the presets table and versions 0001 and 0002, and two concurrent migrates apply 2 and 0 [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- AC2: the Default preset is seeded once with spec {"replicas": 1} and is_default true [evidence: test:tests/test_migrations.py::test_default_preset_seeded]
- AC3: re-applying 0002 after its schema_migrations row is removed succeeds and keeps an edited default [evidence: test:tests/test_migrations.py::test_presets_migration_reapply_keeps_edited_default]
- AC4: deleting a preset sets clusters.preset_id to null and keeps preset_name [evidence: test:tests/test_migrations.py::test_preset_delete_keeps_cluster_provenance]
- AC5: create, get, list order and update round-trip the stored spec exactly, and update bumps updated_at [evidence: test:tests/test_presets_repo.py::test_crud_round_trip_and_order]
- AC6: names are unique case-insensitively and validate_preset_name enforces 1 to 40 allowed characters and rejects leading or trailing spaces [evidence: test:tests/test_presets_repo.py::test_name_rules_and_unique]
- AC7: the default cannot be renamed or deleted and the last preset cannot be deleted [evidence: test:tests/test_presets_repo.py::test_default_and_last_preset_guards]
- AC8: README Data model and single-writer table name presets and the provenance columns [evidence: judgement:README.md Data model and Single-writer sections reviewed]
- AC9: the targeted tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_migrations.py tests/test_presets_repo.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/migrations/0002_presets.sql`
- `src/agent_orchestrator/db/presets.py`
- `tests/test_migrations.py`
- `tests/test_presets_repo.py`
- `README.md`

## Interfaces

- Tables: `presets(id, name, spec, is_default, created_at, updated_at)`; `clusters.preset_id`, `clusters.preset_name`.
- `db/presets.py` (part `presets-repo`): `validate_preset_name`, `Preset`, `PresetExists`, `PresetNotFound`, `PresetDefault`, `LastPreset`, `list_presets`, `get`, `get_for_share`, `create`, `update`, `delete`. Consumed by preset-routes and create-cluster-from-preset.
- Default preset id `00000000-0000-0000-0000-000000000001`, name `Default`, spec `{"replicas": 1}`.

## Expected outcome

After `orch migrate` every database has a Default 1-pod preset, a presets repository the api can call, and clusters able to record where they came from.

## Steps

- Update `tests/test_migrations.py` (TABLES, versions, concurrent count, the three new tests) and write `tests/test_presets_repo.py`; run `uv run pytest -q -p no:cacheprovider tests/test_migrations.py tests/test_presets_repo.py`: fails.
- Write `0002_presets.sql` and `db/presets.py`; add the README rows; run the verify command: passes.

## Notes

- `db/migrate.py:run_migrations` records versions and skips applied ones, so the re-apply test deletes the `0002` row from `schema_migrations` first; every statement must then succeed again.
- Follow `db/clusters.py` for row mapping (`dict_row`), `Jsonb` dumps and exception translation from `psycopg.errors.UniqueViolation`.
- The repository does not NOTIFY; nothing listens for preset changes.
- Review tier is full (migration path).
- Builder check ruling 4 (2026-10-23): names with leading or trailing spaces are rejected (422 on the API, inline error in the form); the API never trims. The copy name's source part is cut to fit 40 characters and right-trimmed before " copy".

- 2026-10-23 amended: builder check ruling 4: leading/trailing space rejected, never trimmed (AC6 rewritten)
