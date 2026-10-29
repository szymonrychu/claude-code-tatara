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

- `src/sessions/DiscardSessionDialog.tsx`: the effective name is `session.status.cache?.key` when it is a non-empty string, else `session.spec.cache?.key`; `status` is `Record<string, unknown>` in the schema, so narrow the type before use.

## Expected outcome

Discarding a migrated session whose spec still says `preset-0123456789abcdef` and whose `status.cache.key` is `my-repo-alpha` shows that both the workspace files and the Claude transcripts are saved under `my-repo-alpha` and restored by the next session with the same cache name (by default the same preset and slug).

## Steps

- Read src/sessions/DiscardSessionDialog.tsx and src/sessions/DiscardSessionDialog.test.tsx (`existing`, `wrap`) in one pass.
- `npm ci --no-audit --no-fund`.
- Red: rewrite `states what is backed up when the session cache is configured` for the new wording and add the two tests named in the acceptance conditions; run `npx vitest run src/sessions/DiscardSessionDialog.test.tsx`; expect them to fail.
- Green: change DiscardSessionDialog.tsx; rerun; expect all passed.
- `npm run lint`; expect exit 0.

## Notes

- The orchestrator pins `status.cache.key` at the first restore and the migration repoints it for pre-epic sessions (tasks orch-transcripts-follow-name, orch-cache-name-migration); the spec key of a pre-epic session stays the old `preset-*` literal because the api owns `spec`.
- No schema sync is needed: `status` is free-form.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; `npm test` had 6 test files failing to import `@codemirror/*` because node_modules was stale, so the verify runs `npm ci --no-audit --no-fund` first.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring vitest load flake in PresetForm).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
