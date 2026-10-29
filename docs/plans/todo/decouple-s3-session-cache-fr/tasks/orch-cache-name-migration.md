---
title: orch cache name migration
status: todo
repo: agents-orchestrator
value: "Existing sessions keep their workspace and transcripts after rotation: their caches are copied to the new names and they are repointed"
files: [src/agents_orchestrator/reconciler/cache_migration.py, src/agents_orchestrator/reconciler/loop.py, tests/test_cache_migration.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_migration.py tests/test_cache_restore.py tests/test_cache_save.py tests/test_sessions_restore.py tests/test_sessions_backup.py && mise run lint"
depends_on: [orch-cache-name-on-create, orch-transcripts-follow-name, orch-cache-copy-if-absent]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 16
expected_tokens: 3197775
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch cache name migration

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D7 and D9 in agents-orchestrator: the reconciler copies the caches of the sessions that existed before this epic to their new names and repoints them, so a session discarded and recreated with the same slug from the same preset (rotation) restores its workspace and transcripts. New module `src/agents_orchestrator/reconciler/cache_migration.py`, called from `reconciler/loop.py` once per tick per session: in `_converge` before the transcripts restore step, and in `_discard` before the workdir save.

- Which sessions: `spec.cache` set, the cache configured (`settings.cache_available`), no `status.cache.migration` record yet, and either `status.cache.key` set without `status.cache.sessions_object` (pinned before this epic) or `spec.cache.key` equal to the pre-epic preset key of `preset_id` (`preset-` plus the first 16 hex digits of sha256(`workspace-cache:` + the preset id's 16 bytes)), a formula kept in this module only to recognise old sessions.
- New name: for a session on its pre-epic preset key, what a session created now from its source preset with its slug would get: the preset's current `spec.cache.key` template, or `naming.DEFAULT_CACHE_NAME_TEMPLATE` when it is empty, rendered with the preset's current name, `preset_id`, the slug and `created_by_service` (`""` when null); when the preset was deleted, the default rendered with the stored `preset_name`. Every other session keeps its current name (`status.cache.key`, else `spec.cache.key`).
- Copy (`cache.copy.copy_if_absent`, run off the event loop with `asyncio.to_thread`): the workspace object `<prefix><old name>.tar.zst` to `<prefix><new name>.tar.zst` when the names differ, and the transcripts object `<prefix>sessions/<slug>.tar.zst` to `<prefix>sessions/<new name>.tar.zst` when they differ. Copy only: nothing is moved, deleted or overwritten.
- Then repoint: `status.cache.key`, `status.cache.object` and `status.cache.sessions_object` take the new name, and `status.cache.migration` records `{state: done, from_key, workdir, sessions, finished_at}`, where `workdir` and `sessions` are each `copied`, `exists`, `source_missing` or `unchanged`.
- Failure: a render error records `migration` `{state: failed, reason}` once and keeps the old names (not retried). A `CopyError` in `_converge` records `{state: failed, reason, failures, next_at}` (backoff `settings.retry_delay_seconds(failures)`, database clock), keeps the old names and retries after `next_at`. In `_discard` it repoints anyway (the save then writes the live workdir under the new name), records the failure and never holds the discard.
- README documents the migration and the `status.cache` fields (`key`, `object`, `sessions_object`, `migration`). MEMORY.md records the decisions (dated, with the why).

## Acceptance conditions

- AC1: a live pre-epic session from preset `My Repo` (slug alpha, status.cache.key the pre-epic preset key, no sessions_object) gets `<prefix><old key>.tar.zst` copied to `<prefix>my-repo-alpha.tar.zst` and `<prefix>sessions/alpha.tar.zst` to `<prefix>sessions/my-repo-alpha.tar.zst`; status.cache key, object and sessions_object are repointed and migration is done [evidence: test:tests/test_cache_migration.py::test_live_preset_session_copied_and_repointed]
- AC2: after the migration the discard saves presign PUTs of the new workspace and transcripts objects, and a session created again from the same preset with the same slug restores those same objects (rotation) [evidence: test:tests/test_cache_migration.py::test_rotation_restores_the_migrated_cache]
- AC3: an existing destination object is never overwritten, the old objects still exist after the migration, and no delete or put request reaches S3 [evidence: test:tests/test_cache_migration.py::test_copy_only_never_overwrites_or_deletes]
- AC4: a missing source records source_missing for that object and the session is still repointed [evidence: test:tests/test_cache_migration.py::test_missing_source_repoints]
- AC5: the preset's current template decides the new name (template `{{ preset }}` gives `my-repo`), and a deleted preset falls back to the default with the stored preset name [evidence: test:tests/test_cache_migration.py::test_new_name_follows_current_preset_template]
- AC6: a raw-spec session with a literal key keeps its workspace name and only its transcripts are copied from sessions/<slug> to sessions/<key> [evidence: test:tests/test_cache_migration.py::test_raw_spec_session_copies_transcripts_only]
- AC7: a session whose sessions_object was pinned after this epic, and a session with a migration record, are never migrated again [evidence: test:tests/test_cache_migration.py::test_new_and_migrated_sessions_skipped]
- AC8: a CopyError during converge records failed with failures and next_at, keeps the old names, and the migration retries once next_at has passed [evidence: test:tests/test_cache_migration.py::test_copy_error_in_converge_retries_with_backoff]
- AC9: a CopyError during discard repoints, records failed, and the saves and the discard still complete [evidence: test:tests/test_cache_migration.py::test_copy_error_in_discard_never_holds]
- AC10: a pre-epic session that never converged (spec key the pre-epic preset key, no status.cache) is migrated before its first restore, which then reads the new names [evidence: test:tests/test_cache_migration.py::test_unconverged_pre_epic_session_migrated_before_restore]
- AC11: the migration module calls no delete or put [evidence: command:! grep -nE "delete_object|delete_objects|put_object" src/agents_orchestrator/reconciler/cache_migration.py]
- AC12: README documents status.cache.migration and MEMORY.md records the migration [evidence: command:grep -q "status.cache.migration" README.md && grep -q "cache.migration" MEMORY.md]
- AC13: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/reconciler/cache_migration.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `tests/test_cache_migration.py`
- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
