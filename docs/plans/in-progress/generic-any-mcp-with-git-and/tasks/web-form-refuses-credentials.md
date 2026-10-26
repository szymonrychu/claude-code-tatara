---
title: Web form refuses credentials in plugin source URLs
status: done
repo: agents-web
value: The form rejects plugin sources with embedded tokens before saving
files: [src/presets/pluginSource.ts, src/presets/pluginSource.test.ts]
verify: "npx vitest run src/presets/pluginSource.test.ts && npm run build && mise run lint"
depends_on: [web-preset-plugin-sources]
model: sonnet
review: ""
verified_head: cd1eb81203bc605fc11d0e08a78d2d6a7ba7120f
points: 1
expected_minutes: 4
expected_tokens: 656478
points_actual: 1
actual_minutes: 1
actual_tokens: 255191
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 195083, review 60108"
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

- Same message form as the existing source checks; parity between orchestrator (spec.py remote_source_problem) and web (pluginSource.ts).

## Expected outcome

A source with credentials in its URL is refused with a redacted message.

## Steps

- Red: add the test; run the task's verify; expect failure.
- Green: add the check; run the task's verify on the committed HEAD.

## Notes

- From the phase-5 security review (sonnet), LOW finding accepted as a fix. any-mcp v0.5.0 itself still accepts userinfo for local use; a later any-mcp release may align (noted, not in scope).
- Keep the word cluster out of new text.

- 2026-10-27 done
