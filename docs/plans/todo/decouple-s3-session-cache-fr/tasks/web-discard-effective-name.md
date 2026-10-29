---
title: web discard effective name
status: todo
repo: agents-web
value: The discard dialog tells the user the real cache name the session saves to and when it comes back
files: [src/sessions/DiscardSessionDialog.tsx, src/sessions/DiscardSessionDialog.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run lint"
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

# web discard effective name

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D12 (session side) in agents-web: the discard dialog names the session's effective cache name, `status.cache.key` (pinned by the reconciler at the first restore), falling back to `spec.cache.key` before that, for both the workspace files and the Claude transcripts, and says they are restored by the next session whose cache name is the same (by default a session from the same preset with the same slug). This replaces the wrong `restored when a session with the same slug is created`.

Test no longer accurate, rewritten: src/sessions/DiscardSessionDialog.test.tsx `states what is backed up when the session cache is configured` (it pins the removed wording).

## Acceptance conditions

- AC1: with status.cache.key `my-repo-alpha` and spec.cache.key `preset-0123456789abcdef` the dialog names `my-repo-alpha` for the workspace files and the transcripts, with the new restore wording [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the effective cache name"]
- AC2: without status.cache.key the dialog names spec.cache.key [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "falls back to the spec cache name before the first restore"]
- AC3: the old wording is gone from src [evidence: command:! grep -rn "restored when a session with the same slug is created" src]
- AC4: the whole dialog suite and lint pass [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run lint]

## Files

- `src/sessions/DiscardSessionDialog.tsx`
- `src/sessions/DiscardSessionDialog.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
