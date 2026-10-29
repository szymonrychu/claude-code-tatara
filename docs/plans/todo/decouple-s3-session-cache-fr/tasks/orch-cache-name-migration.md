---
title: orch cache name migration
status: todo
repo: agents-orchestrator
value: "Existing sessions keep their workspace and transcripts after rotation: their caches are copied to the new names and they are repointed"
files: [src/agents_orchestrator/reconciler/cache_migration.py, src/agents_orchestrator/reconciler/loop.py, src/agents_orchestrator/reconciler/cache.py, src/agents_orchestrator/cache/presign.py, tests/test_cache_migration.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_migration.py tests/test_cache_presign.py tests/test_cache_restore.py tests/test_cache_save.py tests/test_sessions_restore.py tests/test_sessions_backup.py && mise run lint"
depends_on: [orch-cache-name-on-create, orch-transcripts-follow-name, orch-cache-copy-if-absent]
model: opus
review: ""
verified_head: ""
points: 13
expected_minutes: 41
expected_tokens: 5903784
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

- Which sessions: `spec.cache` set, the cache configured (`settings.cache_available`), no `status.cache.migration` record or one in state `failed` (amended 2026-10-29, item 2 below), and either `status.cache.key` set without `status.cache.sessions_object` (pinned before this epic) or `spec.cache.key` equal to the pre-epic preset key of `preset_id` (`preset-` plus the first 16 hex digits of sha256(`workspace-cache:` + the preset id's 16 bytes)), a formula kept in this module only to recognise old sessions; or `preset_id` NULL with `preset_name` set and a key matching `preset-[0-9a-f]{16}` (amended 2026-10-29, item 6 below).
- New name: for a session on its pre-epic preset key, what a session created now from its source preset with its slug would get: the preset's current `spec.cache.key` template, or `naming.DEFAULT_CACHE_NAME_TEMPLATE` when it is empty, rendered with the preset's current name, `preset_id`, the slug and `created_by_service` (`""` when null); when the preset was deleted, the default rendered with the stored `preset_name`. Every other session keeps its current name (`status.cache.key`, else `spec.cache.key`).
- Copy (`cache.copy.copy_if_absent`, run off the event loop with `asyncio.to_thread`): the workspace object `<prefix><old name>.tar.zst` to `<prefix><new name>.tar.zst` when the names differ, and the transcripts object `<prefix>sessions/<slug>.tar.zst` to `<prefix>sessions/<new name>.tar.zst` when they differ. Copy only: nothing is moved, deleted or overwritten.
- Then repoint: `status.cache.key`, `status.cache.object` and `status.cache.sessions_object` take the new name, and `status.cache.migration` records `{state: done, from_key, workdir, sessions, finished_at}`, where `workdir` and `sessions` are each `copied`, `exists`, `source_missing` or `unchanged`.
- Failure: a render error records `migration` `{state: failed, reason}` once and keeps the old names (not retried in `_converge`; retried in `_discard`, amended 2026-10-29, item 2 below). A `CopyError` in `_converge` records `{state: failed, reason, failures, next_at}` (backoff `settings.retry_delay_seconds(failures)`, database clock), keeps the old names and retries after `next_at`. In `_discard` it repoints per target as in item 5 below (amended 2026-10-29; was: repoints anyway), records the failure and never holds the discard.
- README documents the migration and the `status.cache` fields (`key`, `object`, `sessions_object`, `migration`). MEMORY.md records the decisions (dated, with the why).

Amendment 2026-10-29 (interrogate verdict `/workdir/workdir/.scratchpad/s3-cache/interrogate.md` Act on 2-6; design D7 and D9 amendments), verbatim from design D7 and D9:

1. Eligibility (item 2): "no `status.cache.migration` yet" becomes "no `status.cache.migration` record, or one in state `failed`"; a `done` record is final. Otherwise a converge failure followed by a discard could skip the migration, save under the old name, and the recreated session would restore nothing: the timing trap this decision exists to close.
2. Discard retries (item 2): in `_discard` every record that is not `done` (none, or `failed` from a render or a copy) is retried at once, regardless of `next_at`, and then repointed or kept per target as below; the discard is still never held.
3. Transcripts while pending (item 3): "the old name has the same content" holds for the workspace only; before the migration a pre-epic session's transcripts live at `sessions/<slug>`, never at `sessions/<legacy key>`. While a session's migration is pending (eligible under D7 with no `done` record, including `failed`), the transcripts restore and save presign the legacy `<prefix>sessions/<slug>.tar.zst` and `status.cache.sessions_object` is not pinned; it is pinned only by the migration's repoint or, for a session that is not pre-epic, by the first restore. Once `sessions_object` is pinned, the sessions target presigns exactly that object.
4. Save in flight at deploy (item 4): the migration does nothing while a save run of either target is `running` (the save step advances it); when a save of a target has finished, the copy runs after it, from the object that save just wrote, so the new name never carries a stale or half-overwritten copy.
5. Repoint after a failed copy (item 5): in `_discard` the repoint is per target. The workspace target (`key`, `object`) and the transcripts target (`sessions_object`) each take the new name when their copy succeeded (`copied`, `exists`, `source_missing`, `unchanged`) or when `save_skip(settings.cache_available, status, target)` (`cache/save_rule.py`) is None, so their save lands under the new name; a target whose copy failed and whose save is skipped (`never_converged`, a failed restore, `not_configured`) keeps its old object, and the record is `failed` naming that target.
6. Deleted presets (item 6): `sessions.preset_id` is `ON DELETE SET NULL` (`0002_presets.sql:19`), so the pre-epic preset key of a deleted preset cannot be computed. A session with `preset_id` NULL, `preset_name` set and a key (`status.cache.key`, else `spec.cache.key`) matching `preset-[0-9a-f]{16}` counts as being on its pre-epic preset key; its new name is the default rendered with `slugify(preset_name)`.

## Acceptance conditions

- AC1: a live pre-epic session from preset `My Repo` (slug alpha, status.cache.key the pre-epic preset key, no sessions_object) gets `<prefix><old key>.tar.zst` copied to `<prefix>my-repo-alpha.tar.zst` and `<prefix>sessions/alpha.tar.zst` to `<prefix>sessions/my-repo-alpha.tar.zst`; status.cache key, object and sessions_object are repointed and migration is done [evidence: test:tests/test_cache_migration.py::test_live_preset_session_copied_and_repointed]
- AC2: after the migration the discard saves presign PUTs of the new workspace and transcripts objects, and a session created again from the same preset with the same slug restores those same objects (rotation) [evidence: test:tests/test_cache_migration.py::test_rotation_restores_the_migrated_cache]
- AC3: an existing destination object is never overwritten, the old objects still exist after the migration, and no delete or put request reaches S3 [evidence: test:tests/test_cache_migration.py::test_copy_only_never_overwrites_or_deletes]
- AC4: a missing source records source_missing for that object and the session is still repointed [evidence: test:tests/test_cache_migration.py::test_missing_source_repoints]
- AC5: the preset's current template decides the new name (template `{{ preset }}` gives `my-repo`), and a deleted preset falls back to the default with the stored preset name [evidence: test:tests/test_cache_migration.py::test_new_name_follows_current_preset_template]
- AC6: a raw-spec session with a literal key keeps its workspace name and only its transcripts are copied from sessions/<slug> to sessions/<key> [evidence: test:tests/test_cache_migration.py::test_raw_spec_session_copies_transcripts_only]
- AC7: a session whose sessions_object was pinned after this epic, and a session with a `done` migration record, are never migrated again [evidence: test:tests/test_cache_migration.py::test_new_and_migrated_sessions_skipped]
- AC8: a CopyError during converge records failed with failures and next_at, keeps the old names, and the migration retries once next_at has passed [evidence: test:tests/test_cache_migration.py::test_copy_error_in_converge_retries_with_backoff]
- AC9: a CopyError during discard on a target whose save_skip is None repoints that target to the new name, records failed, and the saves (under the new name) and the discard still complete [evidence: test:tests/test_cache_migration.py::test_copy_error_in_discard_never_holds]
- AC10: a pre-epic session that never converged (spec key the pre-epic preset key, no status.cache) is migrated before its first restore, which then reads the new names [evidence: test:tests/test_cache_migration.py::test_unconverged_pre_epic_session_migrated_before_restore]
- AC11: the migration module calls no delete or put [evidence: command:! grep -nE "delete_object|delete_objects|put_object" src/agents_orchestrator/reconciler/cache_migration.py]
- AC12: README documents status.cache.migration and MEMORY.md records the migration [evidence: command:grep -q "status.cache.migration" README.md && grep -q "cache.migration" MEMORY.md]
- AC13: lint passes [evidence: command:mise run lint]
- AC14: a pre-epic session whose preset was deleted (preset_id NULL, preset_name `My Repo`, key matching `preset-[0-9a-f]{16}`, both pinned and unconverged variants) is migrated to `my-repo-alpha` via the default rendered with the stored preset name [evidence: test:tests/test_cache_migration.py::test_deleted_preset_session_migrated_by_preset_name]
- AC15: converge failed, then discard: a session whose migration record is `failed` (a CopyError with next_at in the future, and a render failure) is retried at the discard regardless of next_at, its saves land under the new name, and a session recreated from the same preset with the same slug restores them [evidence: test:tests/test_cache_migration.py::test_failed_then_discard_migrates]
- AC16: while a save run of either target is `running` the migration copies and repoints nothing [evidence: test:tests/test_cache_migration.py::test_migration_waits_for_running_save]
- AC17: a discard whose workdir save finished under the old name before the migration ran copies that just-saved object, and the recreated session restores the saved content, never an older copy [evidence: test:tests/test_cache_migration.py::test_finished_save_copied_after_it]
- AC18: a CopyError during discard on a target whose save_skip returns a reason (never_converged, a failed restore) keeps that target's old object, records failed naming the target, and the discard completes [evidence: test:tests/test_cache_migration.py::test_copy_error_with_skipped_save_keeps_old_name]
- AC19: while a pre-epic session's migration is pending or failed, the transcripts restore and save presign `<prefix>sessions/<slug>.tar.zst` and status.cache.sessions_object stays unset; after a successful retry sessions_object is the new name and later runs presign it [evidence: test:tests/test_cache_migration.py::test_pending_migration_transcripts_use_legacy_slug]

## Files

- `src/agents_orchestrator/reconciler/cache_migration.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/cache/presign.py`
- `tests/test_cache_migration.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- `src/agents_orchestrator/reconciler/cache_migration.py` (new): a class or function the `Reconciler` calls with the session and a `during_discard: bool`, writing through the reconciler's `_write_status` (the reconciler is the only writer of `sessions.status`); `legacy_preset_key(preset_id: uuid.UUID) -> str` lives here only.
- `reconciler/loop.py`: `_converge` calls it before `self.cache.sessions_restore_step`; `_discard` calls it after `_quiesce` and before the workdir `save_step`; the session is reloaded after a repoint so the next step reads the new `status.cache`.
- Reads the source preset with `db/presets.get(conn, preset_id)` (read only; the api stays the only writer of `presets`).
- Uses `cache.naming.render_cache_name`, `cache.naming.DEFAULT_CACHE_NAME_TEMPLATE`, `spec.slugify`, `cache.copy.copy_if_absent`, `presign.object_name`, `presign.sessions_object_name`.
- `status.cache.migration`: `{state: "done"|"failed", from_key, workdir, sessions, finished_at, reason, failures, next_at}` (absent keys omitted). Contract change for `orch-session-status-cache` recorded by the orchestrator.
- Amended 2026-10-29 (interrogate Act on 3, 5): a sync predicate in `cache_migration` (for example `pending(session) -> bool`: eligible under the amended rule with no `done` record) needs no DB read, so `reconciler/cache.py` can call it. `CacheRunner._begin` does not pin `sessions_object` while it is true, and `_start` presigns the sessions target from the pinned `sessions_object` when set, else the legacy `<prefix>sessions/<slug>.tar.zst` while pending, else `sessions/<status.cache.key>` (pinning it). `presign.py` gains an entry point that presigns an exact object path (the builder's shape), so a per-target repoint (`object` and `sessions_object` independent) is honoured by both save steps.
- Amended 2026-10-29 (interrogate Act on 4): the migration reads `status.cache.save` and `status.cache.sessions_save` and returns without copying while either is `running`; in `_discard` the call stays before the workdir `save_step` and runs again before the sessions `save_step` until a record exists, so a finished save is copied after it.

## Expected outcome

After deploy, each live session that existed before the epic has its `preset-<hash>.tar.zst` object copied to `<preset>-<slug>.tar.zst` (and any `sessions/<slug>.tar.zst` to `sessions/<preset>-<slug>.tar.zst`), its `status.cache` repointed and a `migration` record; its discard saves under the new names and a session recreated from the same preset with the same slug restores them. No S3 object is moved, deleted or overwritten.

## Steps

- Read reconciler/loop.py (`_converge`, `_discard`, `_write_status`, `_reload`), reconciler/cache.py (`_begin`, `_start`, `save_step`, `_write`), cache/presign.py, cache/save_rule.py (`save_skip`), db/migrations/0002_presets.sql, cache/copy.py, cache/naming.py, db/presets.py, db/sessions.py (`Session` fields), settings.py (`retry_delay_seconds`), tests/test_cache_restore.py (`Env`) and tests/test_cache_save.py (`SaveEnv`) in one pass.
- Red: write tests/test_cache_migration.py with the tests named in the acceptance conditions (moto server for the bucket as in tests/test_cache_presign.py, the `Env` helpers for sessions and Jobs); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_migration.py`; expect failure on the missing module (DB tests: on CI or a local Postgres).
- Green: write cache_migration.py, wire it into loop.py, add the pending rule and the pinned `sessions_object` presign to reconciler/cache.py and presign.py; rerun the verify; expect passed, and the existing cache, presign and sessions suites unchanged.
- Document the migration and the `status.cache` fields in README `## Workspace cache`; add the MEMORY.md entry; `mise run lint`; expect exit 0.

## Notes

- Live facts (cartographer brief section 4, read-only probe 2026-10-29): 3 live sessions (cct2, claude-code-tatara, mx-34); bucket objects `preset-00f3b4fa52bbda02.tar.zst` 8.5 KB, `preset-55ab25edd7a675ed.tar.zst` 434 MB, `preset-5aa1667ff178f9ae.tar.zst` 18 B, `smoke-workspace-cache.tar.zst`, 14 `sessions/smoke-*` objects; no transcripts object of a live session. Which live session holds which key is unknown (no DB read was made).
- Timing trap the repoint closes: a live session saves to `status.cache.key`; copying without repointing would leave the fresh save under the old name and a recreated session restoring a stale copy.
- The copy is a blocking server-side CopyObject inside the reconciler tick (the largest object today is 434 MB); it runs once per pre-epic session. Run it with `asyncio.to_thread` so the event loop stays free.
- Copy only (leader constraint): grep the diff for `delete_object`, `delete_objects` and `put_object`; AC3 proves it against moto.
- Headline promise end to end (retro, recurring): AC2 must exercise migrate, discard save, recreate and restore in one test, not separate pieces; AC15 and AC17 do the same for the failed-then-discarded and save-in-flight paths.
- Deploy order (design Constraints): this task and orch-transcripts-follow-name ship in one release; the epic lands as one close.
- Sizing (2026-10-29): points raised from 8 to 13 and expected minutes and tokens refilled from calibration by hand (`ticket.py` has no points update), because the interrogate amendments add the pending transcripts rule, the per-target repoint, the save-in-flight wait and the deleted-preset rule.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate Act on 2-6 (/workdir/workdir/.scratchpad/s3-cache/interrogate.md): failed records eligible and retried at discard, legacy sessions/<slug> while pending, wait for a running save and copy after a finished one, per-target repoint gated by save_skip, deleted-preset rule; AC7 and AC9 changed, AC14-AC19 added; files (reconciler/cache.py, cache/presign.py), verify, points 8 to 13, Interfaces, Steps and Notes edited directly
