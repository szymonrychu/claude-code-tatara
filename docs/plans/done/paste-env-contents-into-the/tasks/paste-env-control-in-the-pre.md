---
title: Paste .env control in the preset form
status: done
repo: agents-web
value: Users paste .env contents to fill env rows instead of adding each row by hand
files: [src/presets/PresetForm.tsx, src/presets/PresetForm.test.tsx]
verify: "npm test -- src/presets && npm run lint"
depends_on: [dotenv-parser-module]
model: sonnet
review: ""
verified_head: 314b6bf05cbf0eb84c9ab3ad1fded0bd203cc6e4
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: 3
actual_minutes: 3
actual_tokens: 458846
actual_roles: "impl 3, review 2"
actual_role_tokens: "impl 343133, review 115713"
---

# Paste .env control in the preset form

## Requirement

In the preset form env editor (src/presets/PresetForm.tsx), next to "Add env", add a "Paste .env" button that opens a multiline textbox (label "Paste .env contents") with "Apply" and "Cancel" buttons, so the user can paste .env file contents instead of clicking through rows. Apply runs parseDotenv (src/sessions/dotenv.ts) on the text. When it returns any error, nothing is applied, the textbox stays open with its text, and its helper text lists every error as `line <n>: <message>`. Otherwise the pairs are merged into the env rows: a pair whose key already has a row replaces that row's value in place, other pairs are appended as new rows in paste order, empty rows (key and value both empty) are dropped, the env field is marked set exactly as typing into a row does, and the textbox closes and clears. Apply with no pairs (only blanks or comments) changes nothing and closes. Cancel closes and clears without changing rows. The merged rows show the existing per-row key errors (envKeyError) like typed rows, so a pasted secret-looking or reserved key is flagged and blocks submit the same way.

## Acceptance conditions

- ac1: pasting a multi-line .env text and applying it fills the env rows, replacing an existing key's value in place and appending new keys in paste order [evidence: test:src/presets/PresetForm.test.tsx]
- ac2: a paste with an invalid line applies nothing, keeps the textbox open with its text and shows `line <n>: <message>` [evidence: test:src/presets/PresetForm.test.tsx]
- ac3: Cancel closes the textbox and leaves the rows unchanged [evidence: test:src/presets/PresetForm.test.tsx]
- ac4: a pasted reserved or secret-looking key shows its row error and blocks submit exactly as a typed key does [evidence: test:src/presets/PresetForm.test.tsx]
- ac5: after a successful paste the submitted spec's `env` equals the merged rows [evidence: test:src/presets/PresetForm.test.tsx]
- ac6: the preset tests pass and lint is clean [evidence: command:npm test -- src/presets && npm run lint]

## Files

- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`

## Interfaces

- Uses `src/sessions/dotenv.ts:parseDotenv` (task dotenv-parser-module).
- Keeps `src/presets/PresetForm.tsx` props and the existing env row editor (labels `Env key <n>`, `Env value <n>`, `Remove env <n>`, button `Add env`) unchanged.
- Goes through the form's existing `set('env', rows)` so the env key is marked set exactly as typed edits do; validation stays `src/sessions/sessionSpecForm.ts:envKeyError`.

## Expected outcome

The env editor shows a Paste .env button; pasting valid text and applying fills or updates rows, invalid text shows line errors and applies nothing, Cancel changes nothing; PresetForm tests and lint are green.

## Steps

- Red: add the acceptance-condition tests to src/presets/PresetForm.test.tsx, run `npm test -- src/presets`, expect the new tests to fail because there is no Paste .env button.
- Green: implement the control in src/presets/PresetForm.tsx, run `npm test -- src/presets`, expect all tests passed.
- Run `npm run lint`, expect a clean eslint run.

## Notes

- Repo: code/agents-web. The env editor lives at the `values.env.map(...)` block with the `Add env` button in PresetForm.tsx; follow its MUI style (small TextField and Button, Box with flex column gap 1).
- Merge semantics (my call): replace existing key values in place, append new keys in paste order, drop empty rows (both key and value empty), so pasting into a form with one blank starter row does not leave it behind.
- Existing tests in PresetForm.test.tsx show how the form is rendered and how the submitted spec is captured; reuse those helpers.
- The textbox holds the paste only; it is not part of FormValues and is never submitted.
- (my call) Pasted secret-looking or reserved keys are kept as rows and flagged by envKeyError, never silently dropped. When existing rows already hold a duplicate key, a pasted key replaces the value of the first matching row only. Apply with no pairs changes nothing (drop-empty runs only on a merge with pairs). The control appears wherever PresetForm's env editor renders.

- 2026-10-26 done
