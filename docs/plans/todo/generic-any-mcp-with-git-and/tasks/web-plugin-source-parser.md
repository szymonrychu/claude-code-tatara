---
title: web plugin source parser
status: todo
repo: agents-web
value: the preset form can flag a malformed plugin source before saving
files: [src/presets/pluginSource.ts, src/presets/pluginSource.test.ts]
verify: "npx vitest run src/presets/pluginSource.test.ts && npm run build && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web plugin source parser

## Requirement

User request, verbatim: "In webUI add ability to provide links to such plugins (defined by repo, or dir in repo in git ref) (plus button, shows line textbox where it can be pasted- multiple plugins can be provided)." Goal G5 (epic README), verbatim: "The agents-web preset form edits the plugin sources: a "+" button adds a one-line text box per source, several sources allowed." Design D10, verbatim: "`src/presets/pluginSource.ts` mirrors D1 for the sources the orchestrator accepts (D8) with the same messages". Design D1 (the grammar) and D8 ("only `git::https://` and `github.com/` sources").

Scope (agents-web):
- New `src/presets/pluginSource.ts`: `pluginSourceError(text: string): string | undefined` (undefined when valid) over the trimmed text, applying design D1's rules to the forms D8 accepts: `git::https://<host>/<path>[//<subdir>][?ref=<ref>]` and `github.com/<owner>/<repo>[//<subdir>][?ref=<ref>]`; local paths, `git::ssh://`, `git::file://` and every form D1 refuses are refused, with a message naming the problem (the meaning of any-mcp's messages; byte equality across repos is not required).
- New `src/presets/pluginSource.test.ts` with the cases of the acceptance conditions.
- No text uses the word "cluster" (`src/nomenclature.test.ts`).

## Acceptance conditions

- ac1: git::https URLs with optional //subdir and ?ref= and the github.com/owner/repo shorthand are accepted [evidence: command:npx vitest run src/presets/pluginSource.test.ts -t 'accepts remote sources']
- ac2: local paths, git::ssh and git::file are refused with a message that only https git sources are allowed [evidence: command:npx vitest run src/presets/pluginSource.test.ts -t 'refuses local and non-https sources']
- ac3: query keys other than ref, empty refs, refs starting with - or containing .., subdirs with a leading /, an empty or a .. segment, and unrecognised forms are refused with a message naming the problem [evidence: command:npx vitest run src/presets/pluginSource.test.ts -t 'refuses malformed sources']
- ac4: surrounding whitespace is ignored and an empty line is refused as empty [evidence: command:npx vitest run src/presets/pluginSource.test.ts -t 'trims and refuses empty']
- ac5: the type check and build pass [evidence: command:npm run build]
- ac6: lint passes [evidence: command:mise run lint]

## Files

- `src/presets/pluginSource.ts`
- `src/presets/pluginSource.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
