---
title: web script tests wired
status: todo
repo: agents-web
value: "agents-web's node:test script tests (ci.test.mjs, sync-api.test.mjs, then next_version.test.mjs) run in mise test and CI instead of nowhere"
files: [package.json, .mise.toml, .github/workflows/ci.yaml, scripts/ci.test.mjs]
verify: "mise run lint && mise exec -- npm run test:scripts"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web script tests wired

## Requirement

Decision given for this epic (verbatim): "Script: one stdlib-only Python script, byte-identical in the five repos, tested in each repo's own test runner (pytest in the Python repos; agents-web: its own runner spawning python3, read its package.json); no third-party version action (research: supply-chain risk in a contents: write job)."

Epic README Goal (verbatim): "Tests that pin the CI layout are updated to the new layout, and each repo's lint and tests pass."

design.md D10 (verbatim): "agents-web gets the npm script `\"test:scripts\": \"node --test 'scripts/*.test.mjs'\"`; the `web` CI job runs `npm run test:scripts` after `npm test`; `.mise.toml`'s `test` task runs `npm test` then `npm run test:scripts`. This wires the orphaned `scripts/ci.test.mjs` (13 tests, run by nothing today) and `scripts/sync-api.test.mjs`, and later `scripts/next_version.test.mjs`."

Discovery (verbatim): "`scripts/ci.test.mjs` (node:test, 13 tests) ... ORPHANED: not run by `npm test` (vitest include is `src/**/*.test.{ts,tsx}`, `vite.config.ts`), `test:chart` (`chart/tests/*.test.mjs`), mise or CI."

## Acceptance conditions

- ac1: package.json has the script `"test:scripts": "node --test 'scripts/*.test.mjs'"` with `"test"` still `vitest run`, the `web` job runs `npm run test:scripts` after `npm test`, and `.mise.toml`'s `test` task runs `npm test` then `npm run test:scripts`, all asserted by `test_scripts_tests_are_wired` in scripts/ci.test.mjs [evidence: command:mise exec -- node --test --test-name-pattern=test_scripts_tests_are_wired scripts/ci.test.mjs]
- ac2: `npm run test:scripts` runs scripts/ci.test.mjs and scripts/sync-api.test.mjs and reports fail 0 [evidence: command:mise exec -- npm run test:scripts]
- ac3: Lint passes [evidence: command:mise run lint]

## Files

- `package.json`
- `.mise.toml`
- `.github/workflows/ci.yaml`
- `scripts/ci.test.mjs`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
