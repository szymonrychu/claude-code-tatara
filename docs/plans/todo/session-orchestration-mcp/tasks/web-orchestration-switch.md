---
title: web orchestration switch
status: todo
repo: agents-web
value: the user can flag a preset for session orchestration in the UI
files: [src/presets/PresetForm.tsx, src/sessions/sessionSpecForm.ts, src/presets/PresetForm.test.tsx, openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts]
verify: "npx vitest run src/presets && npm run lint"
depends_on: [orch-schedule-relay]
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

# web orchestration switch

## Requirement

README Goal G6, verbatim: "agents-web has the \"Session orchestration\" switch on the preset form (sessions take the flag from their preset), and shows \"created by <slug>\" on sessions, presets and schedules."

Design D1, verbatim: "Settable only through the public API or UI (preset, or spec at create)."

Architect discovery, verbatim: "The \"Superleader\" switch lives in `src/presets/PresetForm.tsx:288` and `src/sessions/sessionSpecForm.ts:181,403`. `kube_access` follows the same pattern, so a new flag needs the same switch."

Needs a merged upstream: agents-orchestrator main carrying orch-schedule-relay (the final orchestrator API of this epic: `session_orchestration`, `created_by_slug`).

Scope (agents-web): `src/presets/PresetForm.tsx` (a "Session orchestration" switch next to Superleader with a help text naming what it grants), `src/sessions/sessionSpecForm.ts` (value, load and sparse save), `src/presets/PresetForm.test.tsx`, `openapi/orchestrator.json` and `openapi/orchestrator.source` (`npm run sync:api -- orchestrator`), `src/api/schema.d.ts`.

Tests no longer accurate (named): `src/presets/PresetForm.test.tsx` "session options default off and stay sparse" and "session options save and round-trip" cover the sibling switches; they are extended with session_orchestration.

## Acceptance conditions

- ac1: the preset form shows a "Session orchestration" switch, off by default with its help text, and an untouched switch leaves session_orchestration out of the saved spec (extended) [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "session options default off and stay sparse"]
- ac2: switched on, the preset saves session_orchestration true, and a stored true loads on and round-trips (extended) [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "session options save and round-trip"]
- ac3: the vendored orchestrator OpenAPI document and the generated types match, orchestrator.source names an agents-orchestrator main commit, and the document carries session_orchestration and created_by_slug [evidence: command:npm run check:api && grep -q '^agents-orchestrator [0-9a-f]\{40\}$' openapi/orchestrator.source && grep -q session_orchestration openapi/orchestrator.json && grep -q created_by_slug openapi/orchestrator.json]
- ac4: the preset tests and lint pass [evidence: command:npx vitest run src/presets && npm run lint]

## Files

- `src/presets/PresetForm.tsx`
- `src/sessions/sessionSpecForm.ts`
- `src/presets/PresetForm.test.tsx`
- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

## Interfaces

- `sessionSpecForm.ts`: value key `sessionOrchestration: boolean`; `spec.session_orchestration = true` only when set and on.

## Expected outcome

The user can flag a preset for session orchestration in the UI; sessions created from it get the tools.

## Steps

- Confirm agents-orchestrator main carries orch-schedule-relay; stop and report if not.
- Red: extend the two tests; run `npx vitest run src/presets/PresetForm.test.tsx`: fails.
- Green: `npm run sync:api -- orchestrator`, the switch, the mapping; run the task's verify. Quote the summary line.

## Notes

- The help text says the session's leader may create, change and delete presets, sessions and schedules it created, on the user's request.
- Retro: PresetForm tests are load-sensitive (name_rules_default_name_and_pvc timed out at 5 s once); the extended tests keep their 15000 ms timeouts. On a first-run failure save the failing test name and output tail before any rerun.
