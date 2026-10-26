---
title: dotenv parser module
status: done
repo: agents-web
value: Turns pasted .env text into key/value pairs or per-line errors
files: [src/sessions/dotenv.ts, src/sessions/dotenv.test.ts]
verify: "npm test -- src/sessions/dotenv.test.ts && npm run lint"
depends_on: []
model: sonnet
review: ""
verified_head: 99ef9225a93b31c27ce30887eb7535c9d73eeffc
points: 2
expected_minutes: 6
expected_tokens: 559738
points_actual: 2
actual_minutes: 1
actual_tokens: 147955
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 88688, review 59267"
---

# dotenv parser module

## Requirement

Add `parseDotenv(text: string): { pairs: { key: string; value: string }[]; errors: { line: number; message: string }[] }` in a new module src/sessions/dotenv.ts, the parser behind pasting .env file contents into the env editor. Rules (my call, the common dotenv subset): lines are split on \n with an optional trailing \r removed; blank lines and lines whose first non-space character is `#` are skipped; an optional leading `export ` is dropped; the key is the text before the first `=`, trimmed; a line with no `=` or an empty key is an error naming its 1-based line number; the value is the rest after `=`, trimmed. A value starting with `"` must end with an unescaped closing `"` and is unquoted with the escapes `\n`, `\t`, `\"` and `\\` decoded; a value starting with `'` must end with `'` and is taken literally between the quotes; an unterminated quote is an error for that line. In an unquoted value, a ` #` (space then hash) starts an inline comment that is removed with the value then trimmed again; text after a closing quote may only be whitespace or a ` #` comment, otherwise the line is an error. A key repeated in the text keeps the last value, at the position of its first occurrence. Keys are not validated here beyond being non-empty: the form's envKeyError judges them.

## Acceptance conditions

- ac1: parseDotenv handles blank lines, full-line comments, the `export ` prefix, CRLF input, surrounding whitespace, unquoted values with and without ` #` comments, a `#` inside an unquoted value without a preceding space kept, double-quoted values with each escape decoded, single-quoted values kept literal (no escape decoding, `#` kept), an empty value (`KEY=`), a value containing `=`, and a repeated key keeping the last value at its first position [evidence: test:src/sessions/dotenv.test.ts]
- ac2: parseDotenv reports each error case with its 1-based line number (no `=`, empty key, unterminated double quote, unterminated single quote, text after a closing quote) while still returning the valid lines of the same text in `pairs` [evidence: test:src/sessions/dotenv.test.ts]
- ac3: the parser tests pass and lint is clean [evidence: command:npm test -- src/sessions/dotenv.test.ts && npm run lint]

## Files

- `src/sessions/dotenv.ts`
- `src/sessions/dotenv.test.ts`

## Interfaces

- New: `src/sessions/dotenv.ts:parseDotenv(text: string): { pairs: { key: string; value: string }[]; errors: { line: number; message: string }[] }`, exported, pure, no React or MUI imports.

## Expected outcome

parseDotenv exists and returns the documented pairs and errors for every rule in the requirement; dotenv.test.ts is green and lint is clean.

## Steps

- Red: write src/sessions/dotenv.test.ts covering every acceptance condition, run `npm test -- src/sessions/dotenv.test.ts`, expect it to fail because src/sessions/dotenv.ts does not exist.
- Green: write src/sessions/dotenv.ts, run `npm test -- src/sessions/dotenv.test.ts`, expect all tests passed.
- Run `npm run lint`, expect no output beyond the eslint banner (max-warnings 0).

## Notes

- Repo: code/agents-web (TypeScript, vitest, eslint). Module and test sit beside src/sessions/sessionSpecForm.ts, which owns EnvRow and envKeyError; do not import from or change it.
- Error messages are short lowercase phrases, for example `missing =`, `empty key`, `unterminated quote`, `unexpected text after closing quote`; task 2 renders them as `line <n>: <message>`.
- No new dependency (no dotenv package): the parser is small and the rules are fixed by the requirement.
- (my call) `KEY= # c` parses to an empty value. In a double-quoted value an unknown escape such as `\x` is kept literally (backslash plus character), not an error.

- 2026-10-26 done
