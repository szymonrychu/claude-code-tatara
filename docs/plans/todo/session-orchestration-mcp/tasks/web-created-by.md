---
title: web created by
status: todo
repo: agents-web
value: the user sees which session created a session or a preset
files: [src/sessions/SessionsPage.tsx, src/sessions/SessionsPage.test.tsx, src/presets/PresetsPage.tsx, src/presets/PresetsPage.test.tsx]
verify: "npx vitest run src/sessions/SessionsPage.test.tsx src/presets/PresetsPage.test.tsx && npm run lint"
depends_on: [web-orchestration-switch]
model: sonnet
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

# web created by

## Requirement

README Goal G6, verbatim: "agents-web has the \"Session orchestration\" switch on the preset form (sessions take the flag from their preset), and shows \"created by <slug>\" on sessions, presets and schedules."

Open question Q7 (pending; the plan follows the recommended answer), verbatim: "agents-web shows 'created by <slug>' on sessions, presets and schedules?" recommended "yes".

Design D4, verbatim: "The public `SessionView` and `PresetView` gain `created_by_slug` (additive; null for objects the user made) so agents-web can show it (Q7; my call pending the gate)."

Scope (agents-web): `src/sessions/SessionsPage.tsx` and `src/presets/PresetsPage.tsx` show "created by <slug>" for rows whose `created_by_slug` is set and nothing for the others; their tests. Schedules are web-schedule-owner.

## Acceptance conditions

- ac1: the sessions list shows "created by <slug>" on a session with created_by_slug and nothing on one without [evidence: command:npx vitest run src/sessions/SessionsPage.test.tsx -t "created by"]
- ac2: the presets list shows "created by <slug>" on a preset with created_by_slug and nothing on one without [evidence: command:npx vitest run src/presets/PresetsPage.test.tsx -t "created by"]
- ac3: the sessions and presets tests and lint pass [evidence: command:npx vitest run src/sessions/SessionsPage.test.tsx src/presets/PresetsPage.test.tsx && npm run lint]

## Files

- `src/sessions/SessionsPage.tsx`
- `src/sessions/SessionsPage.test.tsx`
- `src/presets/PresetsPage.tsx`
- `src/presets/PresetsPage.test.tsx`

## Interfaces

- Reads `SessionView.created_by_slug` and `PresetView.created_by_slug` from the vendored types (web-orchestration-switch).

## Expected outcome

The user sees which session created a session or a preset.

## Steps

- Red: add one "created by" test to each page test; run them: fail.
- Green: render the label; run the task's verify. Quote the summary line.

## Notes

- Keep the label secondary text in the existing row layout; no new column needed.
