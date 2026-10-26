---
title: dotenv parser module
status: todo
repo: agents-web
value: Turns pasted .env text into key/value pairs or per-line errors
files: [src/sessions/dotenv.ts, src/sessions/dotenv.test.ts]
verify: "npm test -- src/sessions/dotenv.test.ts && npm run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 6
expected_tokens: 559738
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# dotenv parser module

## Requirement

Add `parseDotenv(text: string): { pairs: { key: string; value: string }[]; errors: { line: number; message: string }[] }` in a new module src/sessions/dotenv.ts, the parser behind pasting .env file contents into the env editor. Rules (my call, the common dotenv subset): lines are split on \n with an optional trailing \r removed; blank lines and lines whose first non-space character is `#` are skipped; an optional leading `export ` is dropped; the key is the text before the first `=`, trimmed; a line with no `=` or an empty key is an error naming its 1-based line number; the value is the rest after `=`, trimmed. A value starting with `"` must end with an unescaped closing `"` and is unquoted with the escapes `\n`, `\t`, `\"` and `\\` decoded; a value starting with `'` must end with `'` and is taken literally between the quotes; an unterminated quote is an error for that line. In an unquoted value, a ` #` (space then hash) starts an inline comment that is removed with the value then trimmed again; text after a closing quote may only be whitespace or a ` #` comment, otherwise the line is an error. A key repeated in the text keeps the last value, at the position of its first occurrence. Keys are not validated here beyond being non-empty: the form's envKeyError judges them.

## Acceptance conditions

- test: src/sessions/dotenv.test.ts covers blank lines, full-line comments, `export ` prefix, CRLF input, surrounding whitespace, unquoted values with and without ` #` comments, a `#` inside an unquoted value without a preceding space kept, double-quoted values with each escape, single-quoted values kept literal (no escape decoding, `#` kept), an empty value (`KEY=`), a value containing `=`, and a repeated key keeping the last value at its first position.
- test: src/sessions/dotenv.test.ts covers the error cases with their 1-based line numbers: no `=`, empty key, unterminated double and single quote, trailing garbage after a closing quote; valid lines in the same text are still returned in `pairs`.
- command: `npm test -- src/sessions/dotenv.test.ts` passes and `npm run lint` is clean.

## Files

- `src/sessions/dotenv.ts`
- `src/sessions/dotenv.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
