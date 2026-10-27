---
title: web discard backup notice
status: in-progress
repo: agents-web
value: the user sees exactly what a discard deletes and what is kept before confirming
files: [src/sessions/DiscardSessionDialog.tsx, src/sessions/DiscardSessionDialog.test.tsx, MEMORY.md]
verify: "npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run lint && npx tsc -b"
depends_on: [web-sync-session-safety-api]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 940114
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web discard backup notice

## Requirement

Design D8, user decision verbatim: "Web: the discard dialog states exactly what is lost vs backed up (from the new status/meta fields); the chat shows an "agent unavailable" banner when messages are queued and no agent is idle/ready, with the age of the oldest queued message (orchestrator summary exposes oldest_queued_at; agent state `dead` is mapped in agentMarkState). Re-sync the vendored OpenAPI (npm run sync:api)."

Goal G7, verbatim: "The web discard dialog states what history is lost or backed up; the chat shows an agent-unavailable banner with the age of the oldest queued message."

Design D8 (my call), verbatim: "API: `SessionSummary.oldest_queued_at` (null when none), also carried by the `message_status` stream frame so the banner stays live; `SessionView.backup` `{workdir: bool, transcripts: bool, reason: str|null, last_transcripts_backup: {finished_at, bytes}|null}`, where each flag is true only when the discard would really save it (spec.cache set, `cache_available`, its restore state allows the save) and `reason` names why not (`no_session_cache`, `cache_not_configured`, or the skip reason)."

This task is the discard dialog: "the discard dialog states exactly what is lost vs backed up (from the new status/meta fields)".

Scope (agents-web):
- `src/sessions/DiscardSessionDialog.tsx`: two lists from `session.backup`: "Deleted" (agents, the workspace PVC, the chat history, the Claude transcripts unless backed up, the workspace files unless backed up) and "Backed up" (workspace files to the S3 cache under its key, Claude transcripts to the S3 cache, both restored when a session with the same slug is created), or a line "Nothing is backed up: <reason in words>". The existing hook line (history export) and the hook-failed alert stay. The typed-slug confirm stays.
- `src/sessions/DiscardSessionDialog.test.tsx`: tests named "states what is backed up when the session cache is configured", "states nothing is backed up without a session cache", "names the reason a backup is skipped"; existing tests keep passing (the static "Everything is deleted" body changes only where backups now apply: a test asserting that body is no longer accurate and is updated, naming it).
- MEMORY.md (agents-web): dated entry on D8.

Steps: tests first, seen failing; then the component; run the verify.

Notes: on the first full-suite failure, save the failing test name and output tail before any rerun (retro, recurring vitest load flake). No em dashes. Depends on web-sync-session-safety-api for the types.

## Acceptance conditions

- AC1: with the session cache configured the dialog lists workspace files and Claude transcripts as backed up and restored on recreating the same slug, and the rest as deleted [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "states what is backed up when the session cache is configured"]
- AC2: without a session cache the dialog says nothing is backed up and why [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "states nothing is backed up without a session cache"]
- AC3: a skipped backup names its reason [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the reason a backup is skipped"]
- AC4: every dialog test passes [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx]
- AC5: MEMORY.md records the decision [evidence: command:grep -q "backed up" MEMORY.md]
- AC6: lint and typecheck pass [evidence: command:npm run lint && npx tsc -b]

## Files

- `src/sessions/DiscardSessionDialog.tsx`
- `src/sessions/DiscardSessionDialog.test.tsx`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run lint && npx tsc -b"` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run lint && npx tsc -b"` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
