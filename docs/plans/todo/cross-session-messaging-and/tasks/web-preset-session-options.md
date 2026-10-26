---
title: web preset session options
status: todo
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
- `src/presets/PresetForm.tsx`: two switch rows like "Reuse running agent": "Cross-session messaging" with a helper that the leader can message the leaders of other sessions with this option on and receive their messages; "Kubernetes access" with a helper that agents get full read-write access to every namespace and resource. When `meta.kube_access.available` is false the Kubernetes access switch is disabled with the helper "Not configured on this orchestrator" (precedent: the cache fieldset, PresetForm.tsx:95, 260). Add both keys to the `text()` key exclusion type.
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
