---
title: web agent unavailable banner
status: in-progress
repo: agents-web
value: a hung session is visible at once instead of looking like silent queueing
files: [src/chat/AgentUnavailableBanner.tsx, src/chat/AgentUnavailableBanner.test.tsx, src/chat/ChatView.tsx, src/ribbon/stateMark.tsx, src/ribbon/stateMark.test.ts, src/api/stream.ts, src/api/stream.test.ts, src/ribbon/useSessions.ts]
verify: "npx vitest run src/chat/AgentUnavailableBanner.test.tsx src/ribbon/stateMark.test.ts src/api/stream.test.ts && npm run lint && npx tsc -b"
depends_on: [web-sync-session-safety-api]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web agent unavailable banner

## Requirement

Design D8, user decision verbatim: "Web: the discard dialog states exactly what is lost vs backed up (from the new status/meta fields); the chat shows an "agent unavailable" banner when messages are queued and no agent is idle/ready, with the age of the oldest queued message (orchestrator summary exposes oldest_queued_at; agent state `dead` is mapped in agentMarkState). Re-sync the vendored OpenAPI (npm run sync:api)."

Goal G7, verbatim: "The web discard dialog states what history is lost or backed up; the chat shows an agent-unavailable banner with the age of the oldest queued message."

Design D8 (my call), verbatim: "`agentMarkState('dead', ready)` returns `error`. The banner shows when `summary.queued > 0` and no agent is ready and `idle` (Q2 asks whether busy-only hives should show it)."

Q2 answer (my call, design.md Open questions): "The banner shows when messages are queued and either no agent is ready and alive (none ready, or all `dead`), or the oldest queued message is older than 10 minutes. A queue behind a busy leader is normal and stays quiet; a stuck busy agent still surfaces after 10 minutes."

Scope (agents-web):
- `src/chat/AgentUnavailableBanner.tsx` (new): an MUI Alert "Agent unavailable: N messages queued, oldest <age> ago" when `summary.queued > 0` and either no agent is `ready` with a state other than `dead`, or the oldest queued message is older than 10 minutes; the age from `summary.oldest_queued_at` through `formatAge`/`useNow` (`src/chat/agentAge.ts`); hidden otherwise.
- `src/chat/ChatView.tsx`: renders it above QueueStrip.
- `src/ribbon/stateMark.tsx`: `agentMarkState` maps `dead` to `error`; `src/ribbon/stateMark.test.ts` (new).
- `src/api/stream.ts` and `src/api/stream.test.ts`: the `message_status` event carries `oldestQueuedAt` (from `oldest_queued_at`); `src/ribbon/useSessions.ts` applies it to the session summary so the banner stays live.
- `src/chat/AgentUnavailableBanner.test.tsx`: tests named "shows when messages are queued and no agent is alive", "shows when the oldest queued message is older than 10 minutes", "hidden when a ready agent is busy and the queue is younger than 10 minutes", "hidden when an agent is ready and idle", "hidden when nothing is queued", "updates the age from the status stream".

Steps: tests first, seen failing; then the code; run the verify.

Notes: on the first full-suite failure, save the failing test name and output tail before any rerun (retro). Depends on web-sync-session-safety-api for the types.

## Acceptance conditions

- AC1: the banner shows with the queued count and the oldest message's age when messages are queued and no agent is ready and alive [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx -t "shows when messages are queued and no agent is alive"]
- AC2: the banner shows when the oldest queued message is older than 10 minutes even with a ready busy agent [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx -t "shows when the oldest queued message is older than 10 minutes"]
- AC3: the banner is hidden when a ready agent is busy and the oldest queued message is younger than 10 minutes [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx -t "hidden when a ready agent is busy and the queue is younger than 10 minutes"]
- AC4: the banner is hidden when an agent is ready and idle [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx -t "hidden when an agent is ready and idle"]
- AC5: the banner is hidden when nothing is queued [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx -t "hidden when nothing is queued"]
- AC6: the age follows oldest_queued_at from the message_status frame [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx src/api/stream.test.ts]
- AC7: agentMarkState maps dead to error [evidence: command:npx vitest run src/ribbon/stateMark.test.ts]
- AC8: lint and typecheck pass [evidence: command:npm run lint && npx tsc -b]

## Files

- `src/chat/AgentUnavailableBanner.tsx`
- `src/chat/AgentUnavailableBanner.test.tsx`
- `src/chat/ChatView.tsx`
- `src/ribbon/stateMark.tsx`
- `src/ribbon/stateMark.test.ts`
- `src/api/stream.ts`
- `src/api/stream.test.ts`
- `src/ribbon/useSessions.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests named in the requirement; run the verify, expect them to fail.
- Green: implement the banner, the stateMark mapping and the stream field; run the verify, expect all passed.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-27 amended: Q2 settled: narrowed banner rule
