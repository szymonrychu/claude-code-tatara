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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
