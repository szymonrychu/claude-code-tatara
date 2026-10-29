---
title: web discard latest backup
status: todo
repo: agents-web
value: The discard dialog tells the user when the transcripts were last backed up and that a final backup follows
files: [src/sessions/DiscardSessionDialog.tsx, src/sessions/DiscardSessionDialog.test.tsx, src/api/schema.d.ts, openapi/orchestrator.json, openapi/orchestrator.source]
verify: "npm ci --no-audit --no-fund && npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run check:api && npm run lint"
depends_on: [orch-backup-view-latest]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web discard latest backup

## Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G4, verbatim: "the API's `last_transcripts_backup` and the discard dialog show the latest successful backup, live or final, and the live backup state is visible in `status.cache`."

Design D7 (the web part), verbatim: "The discard dialog (`agents-web/src/sessions/DiscardSessionDialog.tsx:105,136-139`) says the transcripts were last backed up at that time and that the discard writes a final backup. openapi.json and the web's vendored schema follow."

Design D7 planner detail (2026-10-29, my call), verbatim: "the naming field is `BackupRun.kind`, `"final"` (from `sessions_save` in state `saved`) or `"live"` (from `sessions_backup.last_saved`); the newer by `finished_at` wins, a tie goes to `final`."

Wording (planner, my call): when `backup.transcripts` is true and `last_transcripts_backup` is set, the dialog shows `Claude transcripts last backed up at <finished_at> (<live backup|final backup>, <formatBytes(bytes)>); the discard writes a final backup.` This replaces `The last transcripts backup finished at <finished_at> (<bytes>); a new one replaces it.`

Tests no longer accurate and changed: src/sessions/DiscardSessionDialog.test.tsx `states what is backed up when the session cache is configured` (its `last_transcripts_backup` fixture lacks the now required `kind`, and it matches the removed `last transcripts backup finished` wording); the `NO_BACKUP` fixture type follows the regenerated schema.

## Acceptance conditions

- AC1: with last_transcripts_backup kind live the dialog says the Claude transcripts were last backed up at its finished_at by a live backup, with its size, and that the discard writes a final backup [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the latest live backup"]
- AC2: with kind final the dialog names a final backup with the same sentence [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the latest final backup"]
- AC3: the old wording is gone from src [evidence: command:! grep -rn "a new one replaces it" src]
- AC4: openapi/orchestrator.json, openapi/orchestrator.source and src/api/schema.d.ts are synced from the orchestrator commit carrying BackupRun.kind and agree [evidence: command:grep -q '"kind"' openapi/orchestrator.json && npm run check:api]
- AC5: the whole dialog suite, the type check of the build and lint pass [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run build && npm run lint]

## Files

- `src/sessions/DiscardSessionDialog.tsx`
- `src/sessions/DiscardSessionDialog.test.tsx`
- `src/api/schema.d.ts`
- `openapi/orchestrator.json`
- `openapi/orchestrator.source`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
