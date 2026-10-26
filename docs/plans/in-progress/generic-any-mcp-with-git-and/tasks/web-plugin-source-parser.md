---
title: web plugin source parser
status: done
repo: agents-web
value: the preset form can flag a malformed plugin source before saving
files: [src/presets/pluginSource.ts, src/presets/pluginSource.test.ts]
verify: "npx vitest run src/presets/pluginSource.test.ts && npm run build && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: 2095c1af53fe2a7d30e39dc033c3422e34235546
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: 2
actual_minutes: 36
actual_tokens: 1136702
actual_roles: "impl 36, review 34"
actual_role_tokens: "impl 971978, review 164724"
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

- `src/presets/pluginSource.ts`: `export function pluginSourceError(text: string): string | undefined` (undefined when valid; the caller stores the trimmed text).
- Consumed by `src/sessions/sessionSpecForm.ts` in task web-preset-plugin-sources.

## Expected outcome

The web app refuses, with a readable reason, every source the orchestrator would refuse under design D1 and D8, and accepts every one it would accept.

## Steps

- Red: write `src/presets/pluginSource.test.ts` with the four `describe`/`it` groups named in the acceptance conditions as tables of accepted and refused strings; run `npx vitest run src/presets/pluginSource.test.ts`: fails on the missing module.
- Green: write `src/presets/pluginSource.ts`; run the task's verify: passes.

## Notes

- Rulings and their pin tests: only `git::https://` and `github.com/` forms are valid (refuses local and non-https sources; gate Q1 recommended answer); `?depth=` is refused naming `depth` (refuses malformed sources).
- Mirror the accept and reject cases of any-mcp `tests/test_sources.py` (task anymcp-source-parser) for the forms D8 keeps; messages need the same meaning, not the same bytes.
- Test names must contain the `-t` strings of the acceptance conditions.
- No text uses the word "cluster" (`src/nomenclature.test.ts`); `npm run build` runs `tsc -b`.

- 2026-10-26 done

- 2026-10-27 done
