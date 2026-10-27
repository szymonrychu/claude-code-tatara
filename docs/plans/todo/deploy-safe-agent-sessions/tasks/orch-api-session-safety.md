---
title: orch api session safety
status: todo
repo: agents-orchestrator
value: the API tells clients what a discard keeps and how long messages have waited
files: [src/agents_orchestrator/api/schemas.py, src/agents_orchestrator/api/sessions.py, src/agents_orchestrator/api/streams.py, src/agents_orchestrator/db/views.py, openapi.json, tests/test_api_session_safety.py, README.md]
verify: "uv run pytest -q tests/test_api_session_safety.py tests/test_readme_api.py tests/test_api_sessions.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-sessions-backup-restore]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch api session safety

## Requirement

Design D8, user decision verbatim: "Web: the discard dialog states exactly what is lost vs backed up (from the new status/meta fields); the chat shows an "agent unavailable" banner when messages are queued and no agent is idle/ready, with the age of the oldest queued message (orchestrator summary exposes oldest_queued_at; agent state `dead` is mapped in agentMarkState). Re-sync the vendored OpenAPI (npm run sync:api)."

Design D7 (part), verbatim: "Only when the session cache (spec.cache) is configured; otherwise nothing is backed up and the API/web say so. Status exposes the last sessions backup (finished_at, bytes)."

Design D8 (my call), verbatim: "API: `SessionSummary.oldest_queued_at` (null when none), also carried by the `message_status` stream frame so the banner stays live; `SessionView.backup` `{workdir: bool, transcripts: bool, reason: str|null, last_transcripts_backup: {finished_at, bytes}|null}`, where each flag is true only when the discard would really save it (spec.cache set, `cache_available`, its restore state allows the save) and `reason` names why not (`no_session_cache`, `cache_not_configured`, or the skip reason)."

Goal G7, verbatim: "The web discard dialog states what history is lost or backed up; the chat shows an agent-unavailable banner with the age of the oldest queued message."

Scope (agents-orchestrator):
- `db/views.py`: `_AGGREGATES` adds the oldest queued `created_at`; `summarize` returns `oldest_queued_at`.
- `api/schemas.py`: `SessionSummary.oldest_queued_at: datetime | None`; `SessionBackup` and `BackupRun` models; `SessionView.backup`.
- `api/sessions.py`: builds `backup` from `spec.cache`, `settings.cache_available` and `status.cache` (`restore`, `sessions_restore`, `sessions_save`), with the save rules of tasks orch-sessions-backup-save and orch-sessions-backup-restore (one shared rule, not a copy: reuse the runner's skip function).
- `api/streams.py`: the `message_status` frame carries `oldest_queued_at`.
- `openapi.json` regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`); README API sections document the fields.
- `tests/test_api_session_safety.py` (new).

Steps: tests first, seen failing; then the code; regenerate openapi.json; run the verify.

Notes: DB tests need Docker: PR CI is the evidence. The web consumes this through task web-sync-session-safety-api.

## Acceptance conditions

- AC1: summary.oldest_queued_at is the created_at of the oldest queued message and null when none is queued [evidence: test:tests/test_api_session_safety.py::test_summary_oldest_queued_at]
- AC2: the message_status stream frame carries oldest_queued_at [evidence: test:tests/test_api_session_safety.py::test_message_status_frame_carries_oldest_queued_at]
- AC3: with spec.cache, the cache available and restores that allow saving, backup.workdir and backup.transcripts are true [evidence: test:tests/test_api_session_safety.py::test_backup_view_when_cache_configured]
- AC4: without spec.cache both flags are false with reason no_session_cache; with the cache unavailable, reason cache_not_configured [evidence: test:tests/test_api_session_safety.py::test_backup_view_without_cache]
- AC5: a restore state that skips a save sets that flag false with the skip reason [evidence: test:tests/test_api_session_safety.py::test_backup_view_reports_skipped_save]
- AC6: backup.last_transcripts_backup carries finished_at and bytes of a finished sessions save [evidence: test:tests/test_api_session_safety.py::test_backup_view_last_transcripts_backup]
- AC7: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC8: README documents the new fields [evidence: command:grep -q "oldest_queued_at" README.md && grep -q "last_transcripts_backup" README.md]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/api/streams.py`
- `src/agents_orchestrator/db/views.py`
- `openapi.json`
- `tests/test_api_session_safety.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
