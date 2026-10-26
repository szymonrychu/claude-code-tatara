---
title: Web form refuses credentials in plugin source URLs
status: todo
repo: agents-web
value: The form rejects plugin sources with embedded tokens before saving
files: [src/presets/pluginSource.ts, src/presets/pluginSource.test.ts]
verify: "npx vitest run src/presets/pluginSource.test.ts && npm run build && mise run lint"
depends_on: [web-preset-plugin-sources]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 656478
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Web form refuses credentials in plugin source URLs

## Requirement

Security review finding (LOW, accepted as a fix 2026-10-27): the preset form's plugin source check (src/presets/pluginSource.ts) accepts a remote source with credentials in the URL, such as `git::https://user:token@github.com/o/r.git`. Refuse any remote source whose URL carries userinfo (a `@` before the host), with the message `plugin source '<text>': credentials in the URL are not allowed`, redacting everything before `@` in the echoed text, so the web matches the orchestrator's rule.

## Acceptance conditions

- ac1: sources with `user@`, `user:pass@` or `:token@` before the host are refused with the credentials message and the message does not contain the secret part [evidence: test:src/presets/pluginSource.test.ts]
- ac2: the parser tests, build and lint pass [evidence: command:npx vitest run src/presets/pluginSource.test.ts && npm run build && mise run lint]

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
