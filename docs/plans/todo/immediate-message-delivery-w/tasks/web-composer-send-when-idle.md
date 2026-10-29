---
title: web composer send when idle
status: todo
repo: agents-web
value: "a user can send a message that waits for the agent to finish, while the default reaches it at once"
files: [src/chat/Composer.tsx, src/chat/QueueStrip.tsx, src/chat/Composer.test.tsx]
verify: "npx vitest run src/chat/Composer.test.tsx src/layout/designRules.test.ts && npx tsc -b && npm run lint"
depends_on: [web-sync-message-priority]
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

# web composer send when idle

## Requirement

User scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Goal G2 (README), verbatim: "each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool."

Design D16, verbatim: "agents-web `Composer.tsx` gains a "Send when idle" toggle (off by default) beside the target select; when on, `postMessage` sends `priority: "idle"`, when off it sends no `priority` (the server default), so the existing `{ text }` call shapes stay. `QueueStrip.tsx` adds "waits until idle" to a queued `idle` message's detail. The vendored orchestrator spec and `schema.d.ts` are re-synced first."

Scope (agents-web): `src/chat/Composer.tsx`, `src/chat/QueueStrip.tsx`, `src/chat/Composer.test.tsx` (the composer and queue strip tests live there).

## Acceptance conditions

- ac1: with "Send when idle" on, Enter posts { text, priority: "idle" } (with target_agent_id when an agent is chosen) (new) [evidence: command:npx vitest run src/chat/Composer.test.tsx -t "send when idle posts idle priority"]
- ac2: the toggle is off by default and a send posts { text } with no priority, so the existing call-shape tests stay unchanged [evidence: command:npx vitest run src/chat/Composer.test.tsx -t "enter sends to any agent|sends to chosen agent|send when idle is off by default"]
- ac3: the queue strip shows "waits until idle" for a queued idle message and nothing new for an immediate one (new) [evidence: command:npx vitest run src/chat/Composer.test.tsx -t "queue strip shows waits until idle"]
- ac4: the design rules and nomenclature guards stay green [evidence: test:src/layout/designRules.test.ts]
- ac5: targeted tests, type-check and lint pass [evidence: command:npx vitest run src/chat/Composer.test.tsx src/layout/designRules.test.ts && npx tsc -b && npm run lint]

## Files

- `src/chat/Composer.tsx`
- `src/chat/QueueStrip.tsx`
- `src/chat/Composer.test.tsx`

## Interfaces

- `Composer`: a MUI toggle (Switch or Checkbox with label "Send when idle", `aria-label` "Send when idle") beside the target `Select`; state resets to off on session change; body `chosen === ANY ? { text } : { text, target_agent_id }` plus `priority: 'idle'` only when on.
- `QueueStrip.detail(m)`: for `m.status === 'queued' && m.priority === 'idle'` the detail includes "waits until idle" (combined with the attempt text when both apply).

## Expected outcome

A user can send a message that waits for the agent to finish its turn; by default messages reach a busy agent at once, and the queue shows which messages are waiting on purpose.

## Steps

- Read `src/chat/Composer.tsx`, `src/chat/QueueStrip.tsx`, `src/chat/Composer.test.tsx`, `src/api/client.ts` (`postMessage`, `PostMessage`), `src/layout/designRules.ts` and `src/theme.ts` in one pass.
- Red: add the tests named in ac1 to ac3; run `npx vitest run src/chat/Composer.test.tsx`; expect them to fail.
- Green: add the toggle and the queue strip detail; run the task's verify; expect all passed. Quote the summary line.

## Notes

- Design rules: no colour literals outside `theme.ts`, no arrows or decorative Unicode, fontWeight 400/500.
- The full web suite has load-dependent timeouts (PresetForm, ScheduleForm, Endpoints, FiltersEditor); run only the files in the verify.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun; a named load-dependent flake becomes a reported finding, not a silent rerun (retro).

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
