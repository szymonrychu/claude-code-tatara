---
title: orch backup view latest
status: todo
repo: agents-orchestrator
value: "The API shows when a session's transcripts were last backed up, live or final"
files: [src/agents_orchestrator/api/sessions.py, src/agents_orchestrator/api/schemas.py, openapi.json, README.md, MEMORY.md, tests/test_api_session_safety.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_api_session_safety.py tests/test_readme_api.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint"
depends_on: [orch-sessions-live-backup, orch-discard-stops-backup]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 8
expected_tokens: 1003544
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch backup view latest

## Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G4, verbatim: "the API's `last_transcripts_backup` and the discard dialog show the latest successful backup, live or final, and the live backup state is visible in `status.cache`."

Design D7 (the API part), verbatim: "`SessionView.backup.last_transcripts_backup` (`api/sessions.py:64-90`) becomes the newer saved record of `sessions_save` and `sessions_backup`, with a field naming which (`final` or `live`). [...] openapi.json and the web's vendored schema follow."

Design D7 planner detail (2026-10-29, my call), verbatim: "the naming field is `BackupRun.kind`, `"final"` (from `sessions_save` in state `saved`) or `"live"` (from `sessions_backup.last_saved`); the newer by `finished_at` wins, a tie goes to `final`."

Brief fix-as-ac, verbatim: "`last_transcripts_backup` must reflect live backups (today reads only `sessions_save`)."

Test no longer accurate and changed: tests/test_api_session_safety.py::test_backup_view_last_transcripts_backup asserts `set(last) == {"finished_at", "bytes"}`; `BackupRun` gains `kind` by design D7, so the expected key set gains `kind` (value `final` for that test's `sessions_save`).

## Acceptance conditions

- AC1: with sessions_save saved and sessions_backup.last_saved both present, last_transcripts_backup is the one with the later finished_at, kind `live` or `final` accordingly, and a tie gives `final` [evidence: test:tests/test_api_session_safety.py::test_last_transcripts_backup_newest_of_live_and_final]
- AC2: a live session with only a live backup shows it (kind live, its finished_at and bytes), also while its latest run is running, failed or skipped (last_saved kept) [evidence: test:tests/test_api_session_safety.py::test_last_transcripts_backup_live_only]
- AC3: with neither a saved sessions_save nor a last_saved it is null, and a final-only backup carries kind final [evidence: test:tests/test_api_session_safety.py::test_backup_view_last_transcripts_backup]
- AC4: openapi.json is regenerated and matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC5: the api still imports neither reconciler nor k8s [evidence: test:tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper]
- AC6: README documents kind and the live source of last_transcripts_backup, MEMORY.md records it, and lint passes [evidence: command:grep -q "sessions_backup.last_saved" README.md && grep -q "BackupRun.kind" MEMORY.md && mise run lint]

## Files

- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/api/schemas.py`
- `openapi.json`
- `README.md`
- `MEMORY.md`
- `tests/test_api_session_safety.py`

## Interfaces

- `api/schemas.py:BackupRun`: `finished_at: datetime`, `bytes: int`, `kind: Literal["final", "live"]` (required).
- `api/sessions.py:_backup`: `last_transcripts_backup` is the newer by `finished_at` of `status.cache.sessions_save` in state `saved` (`kind="final"`) and `status.cache.sessions_backup.last_saved` (`kind="live"`); a tie gives `final`; neither gives null. Malformed or non-dict values read as absent, as `_last_backup` does today.
- `openapi.json` regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json`.
- The api reads `status` only; it never imports `reconciler` or `k8s`.

## Expected outcome

`GET /api/v1/sessions/<id>` for a live session that had a live backup shows `backup.last_transcripts_backup` `{finished_at, bytes, kind: "live"}` instead of null; after the discard's final save the view (while the row exists) shows the final one.

## Steps

- Read `api/sessions.py` (`_last_backup`, `_backup`), `api/schemas.py` (`BackupRun`, `SessionBackup`), `tests/test_api_session_safety.py` (`_backup`, `SAVED`, `RESTORED`, `CACHED`), `tests/test_readme_api.py::test_openapi_json_matches_app`, README (the `backup` paragraph of the session view and `## Workspace cache`) and MEMORY.md (the 2026-10-28 API session safety entry) in one pass.
- Red: add the tests named in AC1 and AC2 and change `test_backup_view_last_transcripts_backup` as the Requirement names; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_api_session_safety.py`; expect them to fail (DB tests: on CI, `DockerException` locally).
- Green: change `BackupRun` and `_backup`; regenerate openapi.json; rerun the verify; expect every test passed on CI, and `tests/test_readme_api.py` and the import guard passed locally.
- Update README (the session view `backup` paragraph and the transcripts paragraph: `kind`, the live source `status.cache.sessions_backup.last_saved`) and the MEMORY.md entry (dated, `BackupRun.kind`, why the newer of the two); `mise run lint`; expect exit 0.

## Notes

- The MEMORY.md line of 2026-10-28 says `last_transcripts_backup` is `sessions_save` only; add a dated entry that supersedes it rather than rewriting history.
- After the orchestrator PR merges, agents-web syncs the schema from the merge commit (task web-discard-latest-backup); pinning an epic-branch commit instead forced a merge commit in matrix-connector-agent-initi (retro).
- Base: this epic builds after decouple-s3-session-cache-fr, hive decoupling and slash commands from chat have landed on main; rebase onto main first and use the decouple names as they landed (`presign.sessions_object_name`, `status.cache.sessions_object`, the `cache_migration` pending predicate, `CacheRunner._begin` pinning). No SQL migration is planned; if one proves necessary it takes the next free number on main at build time (`<MIGRATION>`), and the builder raises it as a question first.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST); it is not a regression.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Per-task security check (retro, recurring): S3 is reached only through one presigned URL per Job, signed by the reconciler; no credential or presigned query string in a log line, a status `reason` or an error message; the api imports neither `reconciler` nor `k8s`.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.
