# Paste .env contents into the preset env editor implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: dotenv parser module

- Status: done
- Files: `src/sessions/dotenv.ts`, `src/sessions/dotenv.test.ts`
- Verify: `npm test -- src/sessions/dotenv.test.ts && npm run lint`
- Verified head: 99ef9225a93b31c27ce30887eb7535c9d73eeffc

#### Requirement

Add `parseDotenv(text: string): { pairs: { key: string; value: string }[]; errors: { line: number; message: string }[] }` in a new module src/sessions/dotenv.ts, the parser behind pasting .env file contents into the env editor. Rules (my call, the common dotenv subset): lines are split on \n with an optional trailing \r removed; blank lines and lines whose first non-space character is `#` are skipped; an optional leading `export ` is dropped; the key is the text before the first `=`, trimmed; a line with no `=` or an empty key is an error naming its 1-based line number; the value is the rest after `=`, trimmed. A value starting with `"` must end with an unescaped closing `"` and is unquoted with the escapes `\n`, `\t`, `\"` and `\\` decoded; a value starting with `'` must end with `'` and is taken literally between the quotes; an unterminated quote is an error for that line. In an unquoted value, a ` #` (space then hash) starts an inline comment that is removed with the value then trimmed again; text after a closing quote may only be whitespace or a ` #` comment, otherwise the line is an error. A key repeated in the text keeps the last value, at the position of its first occurrence. Keys are not validated here beyond being non-empty: the form's envKeyError judges them.

#### Acceptance conditions

- ac1: parseDotenv handles blank lines, full-line comments, the `export ` prefix, CRLF input, surrounding whitespace, unquoted values with and without ` #` comments, a `#` inside an unquoted value without a preceding space kept, double-quoted values with each escape decoded, single-quoted values kept literal (no escape decoding, `#` kept), an empty value (`KEY=`), a value containing `=`, and a repeated key keeping the last value at its first position [evidence: test:src/sessions/dotenv.test.ts]
- ac2: parseDotenv reports each error case with its 1-based line number (no `=`, empty key, unterminated double quote, unterminated single quote, text after a closing quote) while still returning the valid lines of the same text in `pairs` [evidence: test:src/sessions/dotenv.test.ts]
- ac3: the parser tests pass and lint is clean [evidence: command:npm test -- src/sessions/dotenv.test.ts && npm run lint]

#### Files

- `src/sessions/dotenv.ts`
- `src/sessions/dotenv.test.ts`

#### Interfaces

- New: `src/sessions/dotenv.ts:parseDotenv(text: string): { pairs: { key: string; value: string }[]; errors: { line: number; message: string }[] }`, exported, pure, no React or MUI imports.

#### Expected outcome

parseDotenv exists and returns the documented pairs and errors for every rule in the requirement; dotenv.test.ts is green and lint is clean.

#### Steps

- Red: write src/sessions/dotenv.test.ts covering every acceptance condition, run `npm test -- src/sessions/dotenv.test.ts`, expect it to fail because src/sessions/dotenv.ts does not exist.
- Green: write src/sessions/dotenv.ts, run `npm test -- src/sessions/dotenv.test.ts`, expect all tests passed.
- Run `npm run lint`, expect no output beyond the eslint banner (max-warnings 0).

#### Notes

- Repo: code/agents-web (TypeScript, vitest, eslint). Module and test sit beside src/sessions/sessionSpecForm.ts, which owns EnvRow and envKeyError; do not import from or change it.
- Error messages are short lowercase phrases, for example `missing =`, `empty key`, `unterminated quote`, `unexpected text after closing quote`; task 2 renders them as `line <n>: <message>`.
- No new dependency (no dotenv package): the parser is small and the rules are fixed by the requirement.
- (my call) `KEY= # c` parses to an empty value. In a double-quoted value an unknown escape such as `\x` is kept literally (backslash plus character), not an error.

- 2026-10-26 done

### S2: Paste .env control in the preset form

- Status: done
- Files: `src/presets/PresetForm.tsx`, `src/presets/PresetForm.test.tsx`
- Verify: `npm test -- src/presets && npm run lint`
- Verified head: 314b6bf05cbf0eb84c9ab3ad1fded0bd203cc6e4

#### Requirement

In the preset form env editor (src/presets/PresetForm.tsx), next to "Add env", add a "Paste .env" button that opens a multiline textbox (label "Paste .env contents") with "Apply" and "Cancel" buttons, so the user can paste .env file contents instead of clicking through rows. Apply runs parseDotenv (src/sessions/dotenv.ts) on the text. When it returns any error, nothing is applied, the textbox stays open with its text, and its helper text lists every error as `line <n>: <message>`. Otherwise the pairs are merged into the env rows: a pair whose key already has a row replaces that row's value in place, other pairs are appended as new rows in paste order, empty rows (key and value both empty) are dropped, the env field is marked set exactly as typing into a row does, and the textbox closes and clears. Apply with no pairs (only blanks or comments) changes nothing and closes. Cancel closes and clears without changing rows. The merged rows show the existing per-row key errors (envKeyError) like typed rows, so a pasted secret-looking or reserved key is flagged and blocks submit the same way.

#### Acceptance conditions

- ac1: pasting a multi-line .env text and applying it fills the env rows, replacing an existing key's value in place and appending new keys in paste order [evidence: test:src/presets/PresetForm.test.tsx]
- ac2: a paste with an invalid line applies nothing, keeps the textbox open with its text and shows `line <n>: <message>` [evidence: test:src/presets/PresetForm.test.tsx]
- ac3: Cancel closes the textbox and leaves the rows unchanged [evidence: test:src/presets/PresetForm.test.tsx]
- ac4: a pasted reserved or secret-looking key shows its row error and blocks submit exactly as a typed key does [evidence: test:src/presets/PresetForm.test.tsx]
- ac5: after a successful paste the submitted spec's `env` equals the merged rows [evidence: test:src/presets/PresetForm.test.tsx]
- ac6: the preset tests pass and lint is clean [evidence: command:npm test -- src/presets && npm run lint]

#### Files

- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`

#### Interfaces

- Uses `src/sessions/dotenv.ts:parseDotenv` (task dotenv-parser-module).
- Keeps `src/presets/PresetForm.tsx` props and the existing env row editor (labels `Env key <n>`, `Env value <n>`, `Remove env <n>`, button `Add env`) unchanged.
- Goes through the form's existing `set('env', rows)` so the env key is marked set exactly as typed edits do; validation stays `src/sessions/sessionSpecForm.ts:envKeyError`.

#### Expected outcome

The env editor shows a Paste .env button; pasting valid text and applying fills or updates rows, invalid text shows line errors and applies nothing, Cancel changes nothing; PresetForm tests and lint are green.

#### Steps

- Red: add the acceptance-condition tests to src/presets/PresetForm.test.tsx, run `npm test -- src/presets`, expect the new tests to fail because there is no Paste .env button.
- Green: implement the control in src/presets/PresetForm.tsx, run `npm test -- src/presets`, expect all tests passed.
- Run `npm run lint`, expect a clean eslint run.

#### Notes

- Repo: code/agents-web. The env editor lives at the `values.env.map(...)` block with the `Add env` button in PresetForm.tsx; follow its MUI style (small TextField and Button, Box with flex column gap 1).
- Merge semantics (my call): replace existing key values in place, append new keys in paste order, drop empty rows (both key and value empty), so pasting into a form with one blank starter row does not leave it behind.
- Existing tests in PresetForm.test.tsx show how the form is rendered and how the submitted spec is captured; reuse those helpers.
- The textbox holds the paste only; it is not part of FormValues and is never submitted.
- (my call) Pasted secret-looking or reserved keys are kept as rows and flagged by envKeyError, never silently dropped. When existing rows already hold a duplicate key, a pasted key replaces the value of the first matching row only. Apply with no pairs changes nothing (drop-empty runs only on a merge with pairs). The control appears wherever PresetForm's env editor renders.

- 2026-10-26 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
