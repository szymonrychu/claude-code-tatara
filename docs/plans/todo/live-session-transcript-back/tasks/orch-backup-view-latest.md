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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
