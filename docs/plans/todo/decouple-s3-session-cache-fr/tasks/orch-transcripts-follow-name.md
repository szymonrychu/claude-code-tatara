---
title: orch transcripts follow name
status: todo
repo: agents-orchestrator
value: "A session's Claude transcripts are saved and restored under its cache name, so one name covers its whole backup"
files: [src/agents_orchestrator/cache/presign.py, src/agents_orchestrator/reconciler/cache.py, tests/test_sessions_restore.py, tests/test_sessions_backup.py, MEMORY.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_restore.py tests/test_sessions_backup.py tests/test_cache_restore.py tests/test_cache_save.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 967422
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch transcripts follow name

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D5 in agents-orchestrator: one cache name per session names both of its S3 objects. The workspace archive stays `<prefix><name>.tar.zst`; the Claude transcripts object becomes `<prefix>sessions/<name>.tar.zst` (it was `<prefix>sessions/<slug>.tar.zst`).

- The first restore of either target (`reconciler/cache.py:CacheRunner._begin`; the transcripts restore runs first) pins `status.cache.key` (the session's `spec.cache.key`), `status.cache.object` and the new `status.cache.sessions_object`. Every later restore and save of both targets presigns from the pinned `status.cache.key`.
- `presign.sessions_object_name(settings, name)` and `presign.target_object_name(settings, target, name)` take the cache name for both targets; `CacheRunner._start` passes the pinned name for the sessions target instead of the slug.
- `_begin` pins the name for every run (restore or save, either target) when `status.cache.key` is absent, so no restore or save of the transcripts ever uses the slug.
- MEMORY.md records the decision (dated, with the why).

Tests no longer accurate and rewritten, because the transcripts object now follows the cache name (design D5): tests/test_sessions_restore.py::test_sessions_restore_job_render and tests/test_sessions_backup.py::test_discard_saves_sessions_after_workdir (both assert `/workspace-cache/sessions/alpha.tar.zst`, the slug), and tests/test_sessions_backup.py::test_sessions_save_job_render and ::test_sessions_object_name_distinct_from_cache_keys where they pass the slug as the name.

## Acceptance conditions

- AC1: the transcripts restore Job presigns a GET of `<prefix>sessions/<spec.cache.key>.tar.zst`, and the first restore pins status.cache key, object and sessions_object [evidence: test:tests/test_sessions_restore.py::test_sessions_restore_uses_cache_name]
- AC2: the transcripts save Job presigns a PUT of `<prefix>sessions/<status.cache.key>.tar.zst` [evidence: test:tests/test_sessions_backup.py::test_sessions_save_uses_cache_name]
- AC3: once pinned, a different spec.cache.key moves neither object: restore and save of both targets use status.cache.key [evidence: test:tests/test_sessions_backup.py::test_pinned_name_wins_over_spec]
- AC4: sessions_object_name(settings, "my-repo-alpha") is `workspace-cache/sessions/my-repo-alpha.tar.zst` and never equals object_name of any valid key [evidence: test:tests/test_sessions_backup.py::test_sessions_object_name_distinct_from_cache_keys]
- AC5: MEMORY.md records that the transcripts object follows the cache name [evidence: command:grep -q "sessions_object" MEMORY.md]
- AC6: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/cache/presign.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_sessions_restore.py`
- `tests/test_sessions_backup.py`
- `MEMORY.md`

## Interfaces

- `cache/presign.py`: `sessions_object_name(settings, name: str) -> str` returns `<prefix>sessions/<name>.tar.zst`; `target_object_name(settings, target, name)` and `presign(settings, method, name, target)` take the cache name for both targets.
- `reconciler/cache.py:CacheRunner._begin` pins `status.cache.key`, `object` and `sessions_object` for every run when `key` is absent; `_start` presigns the sessions target from `cache["key"]`; a run without a key fails `no_cache_key` for both targets.
- Contract change (docs/plans/contracts.json, updated by the orchestrator): `orch-session-status-cache` gains `sessions_object`.

## Expected outcome

A new cache-enabled session with cache name `my-repo-alpha` restores and saves its transcripts at `workspace-cache/sessions/my-repo-alpha.tar.zst`, and `status.cache` carries `key`, `object` and `sessions_object` from its first restore on.

## Steps

- Read cache/presign.py, reconciler/cache.py (`_begin`, `_start`, `sessions_restore_step`, `save_step`), cache/save_rule.py, tests/test_sessions_restore.py, tests/test_sessions_backup.py and the MEMORY.md 2026-10-28 transcript entries in one pass.
- Red: add the tests named in the acceptance conditions and rewrite the tests named in the Requirement to expect `sessions/<cache name>`; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_sessions_restore.py tests/test_sessions_backup.py`; expect the new assertions to fail (DB tests: on CI or a local Postgres).
- Green: change presign.py and reconciler/cache.py; rerun the verify; expect passed.
- Add the MEMORY.md entry (dated, why: one name per session covers its whole backup, user Q1); `mise run lint`; expect exit 0.

## Notes

- The test fixtures use slug `alpha` and a cache key different from the slug, so a test that still passes with the slug proves nothing; assert the key path.
- `SESSIONS_EXCLUDE`, the save rule and the Job rendering do not change; only the object name and the pinned fields do.
- Sessions sharing a cache name now share their transcripts too (design D5, open question Q1); the bootstrapper resumes a stopped session with a transcript, so a recreated session resumes the last conversation saved under that name.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
