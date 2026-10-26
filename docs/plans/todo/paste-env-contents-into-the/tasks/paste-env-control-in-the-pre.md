---
title: Paste .env control in the preset form
status: todo
repo: agents-web
value: Users paste .env contents to fill env rows instead of adding each row by hand
files: [src/presets/PresetForm.tsx, src/presets/PresetForm.test.tsx]
verify: "npm test -- src/presets && npm run lint"
depends_on: [dotenv-parser-module]
model: sonnet
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

# Paste .env control in the preset form

## Requirement

In the preset form env editor (src/presets/PresetForm.tsx), next to "Add env", add a "Paste .env" button that opens a multiline textbox (label "Paste .env contents") with "Apply" and "Cancel" buttons, so the user can paste .env file contents instead of clicking through rows. Apply runs parseDotenv (src/sessions/dotenv.ts) on the text. When it returns any error, nothing is applied, the textbox stays open with its text, and its helper text lists every error as `line <n>: <message>`. Otherwise the pairs are merged into the env rows: a pair whose key already has a row replaces that row's value in place, other pairs are appended as new rows in paste order, empty rows (key and value both empty) are dropped, the env field is marked set exactly as typing into a row does, and the textbox closes and clears. Apply with no pairs (only blanks or comments) changes nothing and closes. Cancel closes and clears without changing rows. The merged rows show the existing per-row key errors (envKeyError) like typed rows, so a pasted secret-looking or reserved key is flagged and blocks submit the same way.

## Acceptance conditions

- test: src/presets/PresetForm.test.tsx pastes a multi-line .env text and asserts the env rows (key and value fields) after Apply, including one key that replaced an existing row's value in place and new keys appended in order.
- test: src/presets/PresetForm.test.tsx asserts that a paste with an invalid line applies nothing, keeps the textbox open and shows `line <n>: ...`.
- test: src/presets/PresetForm.test.tsx asserts Cancel leaves the rows unchanged, and that a pasted reserved or secret-looking key shows its row error and the submitted spec is blocked as for a typed key.
- test: src/presets/PresetForm.test.tsx asserts the submitted spec's `env` equals the merged rows after a successful paste.
- command: `npm test -- src/presets` passes and `npm run lint` is clean.

## Files

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
