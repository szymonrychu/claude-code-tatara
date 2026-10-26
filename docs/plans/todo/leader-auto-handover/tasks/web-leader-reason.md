---
title: web leader reason
status: todo
repo: agents-web
value: the user sees that leadership moved because of a compaction or a scale-down
files: [src/api/stream.ts, src/api/stream.test.ts, src/ribbon/useSessions.ts, src/chat/AgentsStrip.tsx, src/chat/AgentsStrip.test.tsx, src/chat/ChatView.tsx]
verify: "npx tsc -b && npx vitest run src/api/stream.test.ts src/chat/AgentsStrip.test.tsx && npm run lint"
depends_on: [leader-changed-reason]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web leader reason

## Requirement

Goal G5, verbatim: "the UI, API and stream show automatic handovers with their reason (compaction, scale-down)".

Design D11, verbatim: agents-web reads `reason` from the `leader_changed` frame into the session's `leader_reason`; the leader badge's tooltip names the epoch and the reason, and for the automatic reasons a caption next to the badge reads "after compaction" or "after scale-down".

Scope:
- `src/api/stream.ts`: the `leader_changed` status event carries `reason: string | null` (from `d.reason`, null when absent).
- `src/ribbon/useSessions.ts`: the `leader_changed` case also sets the session's `leader_reason` from the frame.
- `src/chat/ChatView.tsx`: passes the session's `leader_reason` into AgentsStrip's `hive` prop.
- `src/chat/AgentsStrip.tsx`: `hive` gains `leaderReason: string | null`; the leader badge's `title` names the epoch and the reason (for example `leader epoch 3, reason compaction`); when the reason is `compaction` or `scale_down` a caption next to the badge reads `after compaction` or `after scale-down`; other reasons show no caption.
- Tests: `src/api/stream.test.ts` (the frame's reason is parsed, a missing one is null) and `src/chat/AgentsStrip.test.tsx` (badge title and the two captions; no caption for `user`, `initial`, `leader_lost`, `lease_expired`, `handover: ...`).

Notes: the orchestrator adds `reason` to the frame in task leader-changed-reason; the session view's `leader_reason` already exists in `src/api/schema.d.ts`, so no `npm run sync:api` is needed. Use the word "session", never "cluster" (`src/nomenclature.test.ts`). Retro: web tasks run `npx tsc -b` and the full `npm test` before handing back.

## Acceptance conditions

- AC1: the `leader_changed` frame's reason is parsed and a missing reason reads null [evidence: command:npx vitest run src/api/stream.test.ts]
- AC2: the leader badge names the epoch and reason, and shows "after compaction" or "after scale-down" only for those reasons [evidence: command:npx vitest run src/chat/AgentsStrip.test.tsx]
- AC3: types check [evidence: command:npx tsc -b]
- AC4: the full web suite passes [evidence: command:npm test]
- AC5: lint passes [evidence: command:npm run lint]

## Files

- `src/api/stream.ts`
- `src/api/stream.test.ts`
- `src/ribbon/useSessions.ts`
- `src/chat/AgentsStrip.tsx`
- `src/chat/AgentsStrip.test.tsx`
- `src/chat/ChatView.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
