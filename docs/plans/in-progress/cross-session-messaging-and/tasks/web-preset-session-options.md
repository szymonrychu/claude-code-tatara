---
title: web preset session options
status: in-progress
repo: agents-web
value: users can turn both options on in the preset form
files: [openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts, src/sessions/sessionSpecForm.ts, src/presets/PresetForm.tsx, src/presets/PresetForm.test.tsx]
verify: "npx vitest run src/presets/PresetForm.test.tsx && npm run build && npm run check:api && mise run lint"
depends_on: [orch-session-options-spec, orch-agent-session-messaging]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 977684
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web preset session options

## Requirement

Goal G4 (epic README), verbatim: "Both options are editable in the agents-web preset form, and received cross-session messages are shown with their sender session in the chat." User decision 2026-10-26, verbatim: "Both options are per-session spec fields, settable on presets." Design D14.

Scope (agents-web):
- Sync the orchestrator API: `npm run sync:api -- orchestrator` (pass `--from <the epic's agents-orchestrator tree>` when the default `../agents-orchestrator` is not it) after task orch-agent-session-messaging is committed there; this rewrites `openapi/orchestrator.json`, `openapi/orchestrator.source` and `src/api/schema.d.ts` (generated, never hand-edited).
- `src/sessions/sessionSpecForm.ts`: `FormValues` gains `sessionMessaging: boolean` and `kubeAccess: boolean` (blank `false`); `stateFromPreset` loads `session_messaging` and `kube_access`; `toPresetSpec` writes each only when true (sparse, never `false` or null).
- `src/presets/PresetForm.tsx`: two switch rows like "Reuse running agent": "Superleader" with the helper "superleader: can message the leaders of all sessions" (spec `session_messaging`, design D7, D14); "Kubernetes access" with a helper that agents get full read-write access to every namespace and resource. When `meta.kube_access.available` is false the Kubernetes access switch is disabled with the helper "Not configured on this orchestrator" (precedent: the cache fieldset, PresetForm.tsx:95, 260). Add both keys to the `text()` key exclusion type.
- `src/presets/PresetForm.test.tsx`: tests in the acceptance conditions (template: the reuse switch tests, l.570-606).
- No text uses the word "cluster" (`src/nomenclature.test.ts`).

## Acceptance conditions

- ac1: both switches start off and saving an untouched preset sends neither session_messaging nor kube_access [evidence: test:src/presets/PresetForm.test.tsx::session options default off and stay sparse]
- ac2: turning each switch on saves it as true, and a preset that has both loads with both switches on [evidence: test:src/presets/PresetForm.test.tsx::session options save and round-trip]
- ac3: with meta kube_access.available false the Kubernetes access switch is disabled and shows the not-configured helper, and with it true the switch is enabled [evidence: test:src/presets/PresetForm.test.tsx::kube access disabled when unavailable]
- ac4: the vendored orchestrator schema has both spec fields and meta kube_access, and the generated types match it [evidence: command:grep -q '"kube_access"' openapi/orchestrator.json && grep -q '"session_messaging"' openapi/orchestrator.json && npm run check:api]
- ac5: the type check and build pass [evidence: command:npm run build]
- ac6: the whole web test suite, including the nomenclature guard, passes [evidence: command:npm test]
- ac7: lint passes [evidence: command:mise run lint]

## Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`
- `src/sessions/sessionSpecForm.ts`
- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`

## Interfaces

- `SessionSpec.session_messaging?: boolean | null`, `SessionSpec.kube_access?: boolean | null`, `Meta.kube_access.available: boolean` from the regenerated `src/api/schema.d.ts`.
- `sessionSpecForm.ts:FormValues.sessionMessaging`, `FormValues.kubeAccess`; `toPresetSpec` emits `session_messaging: true` / `kube_access: true` only when set.

## Expected outcome

A user can turn either option on for a preset, the preset saves sparsely, and the Kubernetes access switch explains itself when the orchestrator is not configured for it.

## Steps

- Red: sync the API, then add the three tests named in the acceptance conditions; run `npx vitest run src/presets/PresetForm.test.tsx`: fails.
- Green: edit `sessionSpecForm.ts` and `PresetForm.tsx`; run the task's verify: passes.
- Run ac4 to ac7 commands: pass.

## Notes

- Rulings and their pin tests: sparse save, no `false` written (ac1); disabled-with-helper when unavailable (ac3); a stored `kube_access: true` preset still loads with the switch on even when unavailable, matching the server's stored exemption (add to ac3's test).
- `npm run sync:api` refuses an uncommitted orchestrator `openapi.json`; it must be the committed one from task orch-agent-session-messaging or later.
- `npm run build` runs `tsc -b`, the only type check (retro agents-schedule-deploy: web briefs that skipped it cost fix rounds).
- MUI only; module docstring line at the top of each file; plain functions.

- 2026-10-26 amended: gate 2026-10-26: one-sided superleader messaging (tools for every session, target_not_superleader), Q1 no orchestrator kubectl install, Q2 yes
