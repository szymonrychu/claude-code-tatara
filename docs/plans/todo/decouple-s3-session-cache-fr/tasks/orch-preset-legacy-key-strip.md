---
title: orch preset legacy key strip
status: todo
repo: agents-orchestrator
value: Presets that stored their own preset-derived key get the default per-session name instead of staying coupled
files: [src/agents_orchestrator/db/migrations, tests/test_migrations.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_migrations.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch preset legacy key strip

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D10 in agents-orchestrator: a new SQL migration `src/agents_orchestrator/db/migrations/<NNNN>_preset_cache_default_name.sql`, where `<NNNN>` is the next free number on the base branch when the task is built (0010 on main today; the blocking epics add 0010 or 0011), removes `cache.key` from every preset whose stored key equals its own pre-epic derived key (`'preset-' || left(encode(sha256(convert_to('workspace-cache:', 'UTF8') || uuid_send(id)), 'hex'), 16)`), so that preset gets the default cache name. Every other preset, including other literal keys, is unchanged. Idempotent and safe to re-run, like the earlier migrations.

Tests no longer accurate because they pin the migration list and a new migration exists; each gains the new version: tests/test_migrations.py::test_fresh_database_gets_all_tables, ::test_presets_migration_on_existing_sessions, ::test_concurrent_migrate_serialises and ::test_0005_renames_clusters_to_sessions.

## Acceptance conditions

- AC1: a preset storing its own derived key loses cache.key and keeps cache.exclude; a preset with key `mine` and a preset storing another preset's derived key are unchanged [evidence: test:tests/test_migrations.py::test_preset_cache_default_name_strips_own_derived_key]
- AC2: re-running the migration changes nothing [evidence: test:tests/test_migrations.py::test_preset_cache_default_name_idempotent]
- AC3: the SQL formula gives `preset-4660fe5f5bc805e5` for the preset id uuid int 1, the value the removed Python default_cache_key pinned [evidence: test:tests/test_migrations.py::test_preset_cache_default_name_matches_pinned_key]
- AC4: a fresh database gets every migration including the new one [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- AC5: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/db/migrations`
- `tests/test_migrations.py`

## Interfaces

- `src/agents_orchestrator/db/migrations/<NNNN>_preset_cache_default_name.sql` (new; `<NNNN>` the next free number on the base branch at build time).
- Writes only `presets.spec` of presets whose `spec->'cache'->>'key'` equals their own pre-epic derived key; `jsonb` edit `spec #- '{cache,key}'` (or equivalent) keeps the rest of `cache`.

## Expected outcome

After `orch migrate`, a preset that stored `preset-<its own hash>` has `spec.cache` without `key` (so its sessions get the default `<preset>-<session>`); every other preset is byte-for-byte unchanged; a second run changes nothing.

## Steps

- Read db/migrate.py, db/migrations/0002_presets.sql and 0009_created_by_service.sql, and tests/test_migrations.py (`run_migrations`, `empty_dsn`, the tmp_path copy pattern of `test_0009_created_by_service_column`) in one pass; check the base branch for the highest migration number.
- Red: add the three new tests named in the acceptance conditions and add the new version to the four list-pinning tests named in the Requirement; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_migrations.py`; expect failures on the missing migration (DB tests: on CI or a local Postgres).
- Green: write the SQL file; rerun; expect passed.
- `mise run lint`; expect exit 0.

## Notes

- `sha256(bytea)` exists in Postgres 11 and later; `uuid_send(id)` gives the 16 bytes Python's `uuid.UUID.bytes` gives. AC3 pins the formula against `preset-4660fe5f5bc805e5` for `uuid.UUID(int=1)`, the value tests/test_api_cache.py pinned before this epic.
- Whether any live preset stores its own derived key is unknown (no DB read was made); the migration is correct either way.
- The blocking epics (hive decoupling: 0011_drop_feed_cursor; slash commands from chat) add migrations too; rebase onto the base branch first and take the next number then.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
