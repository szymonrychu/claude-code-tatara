---
title: web env paste fix
status: todo
repo: agents-web
value: "Pasted .env values, secret-named keys included, are kept when a preset is created or saved"
files: [src/presets/PresetForm.tsx, src/sessions/sessionSpecForm.ts, src/presets/PresetForm.test.tsx]
verify: "npx vitest run src/presets/PresetForm.test.tsx && npm run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 8
expected_tokens: 1003544
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web env paste fix

## Requirement

User report (verbatim): "When I try to paste .env and I don't hit "apply", create preset like this, it's not keeping the secret. When I attempt to paste .env and hit apply envs with TOKEN and PASSWORD are flagged as something that doesn't belong to envs."

User decisions (mx-34 #386, 2026-10-29), verbatim: "auto-apply a pending paste on Create, refuse on parse errors, no secret-key check and no warning."

Scope (agents-web):
- src/presets/PresetForm.tsx: when the "Paste .env" textbox is open with text, `submit()` (Create for a new preset, Save when editing) first runs the same parse and merge as `applyPaste` and submits the merged env rows. If the pending paste has any parse error, nothing is submitted, the paste box shows the line errors exactly as Apply does, and the form stays open. An open but empty or whitespace-only paste box submits as before. Factor the parse+merge into one helper used by both Apply and submit (no duplicated merge). The submit button's disabled state must not block a submit merely because the pending paste is unapplied; keys arriving from a pending paste are judged by the same envKeyError rules as typed keys (reserved names, name shape, duplicates) and a resulting error blocks the submit with the rows applied and visible.
- src/sessions/sessionSpecForm.ts: remove the SECRET_KEY regex and its check from `envKeyError`; no replacement warning. Reserved-name, name-shape and duplicate checks stay unchanged.
- src/presets/PresetForm.test.tsx: the tests 'validates env keys, webhook url and any-mcp json' (asserts API_TOKEN is flagged as a secret) and 'a pasted reserved or secret key shows its error and blocks submit' no longer match the required behaviour: change them to assert that API_TOKEN and PASSWORD-style keys are accepted (no error, Create enabled) while the reserved-key assertions stay. Add tests for the auto-apply on Create, auto-apply on Save of an existing preset, and refusal on a parse error.
Test-first: write the new tests, see them fail, then change the code.

## Acceptance conditions

- AC1: Create with a pending unapplied paste `FOO=1\nAPI_TOKEN=secret` sends a spec whose env holds FOO and API_TOKEN with their values [evidence: test:src/presets/PresetForm.test.tsx::Paste .env > Create applies a pending paste]
- AC2: Save of an existing preset with a pending paste sends the merged env (existing key replaced in place, new key appended) [evidence: test:src/presets/PresetForm.test.tsx::Paste .env > Save applies a pending paste]
- AC3: a pending paste with a parse error sends nothing and shows the line error in the paste box [evidence: test:src/presets/PresetForm.test.tsx::Paste .env > a pending paste with a parse error blocks submit]
- AC4: keys containing TOKEN, SECRET, PASSWORD, CREDENTIAL, API_KEY, PRIVATE_KEY, ACCESS_KEY show no error and leave Create enabled, typed or pasted [evidence: test:src/presets/PresetForm.test.tsx::Paste .env > secret-named keys are accepted]
- AC5: reserved keys (CCW_X) are still flagged and block submit [evidence: test:src/presets/PresetForm.test.tsx::Paste .env > a pasted reserved key shows its error and blocks submit]
- AC6: no secret-key rule remains in the web source [evidence: command:! grep -rn "SECRET_KEY\|Looks like a secret" src --include=*.ts --include=*.tsx]
- AC7: the full web suite and lint pass [evidence: command:mise run test && mise run lint]

## Files

- `src/presets/PresetForm.tsx`
- `src/sessions/sessionSpecForm.ts`
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
