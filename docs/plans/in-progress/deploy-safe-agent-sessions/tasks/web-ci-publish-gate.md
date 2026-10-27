---
title: web ci publish gate
status: in-progress
repo: agents-web
value: a red agents-web main build is never pushed or published
files: [.github/workflows/ci.yaml, scripts/ci.test.mjs]
verify: node --test scripts/ci.test.mjs
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 641999
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web ci publish gate

## Requirement

Design D9, user decision verbatim: "Red builds: agents-orchestrator CI pushes images and publishes charts only after lint, test and e2e pass (split the push out of `images` or gate a retag; e2e must not need the pushed image if that is how it works today, check); agents-web image push and chart-publish need the `web` job. agents-helmfile gets a pin check (gh api check-runs, or reuse plugins/workbench/skills/_lib/scm.py reducers) for every pinned main-built commit (orchestrator, web, webhook, schedule, matrix-connector charts; wrapper release tag resolved to its commit) that apply depends on; no override flag. Its tests use fakes like tests/test_smoke_script.py."

Goal G8, verbatim: "No red main build is published or deployed: CI publish jobs need e2e/tests, and the agents-helmfile apply refuses pins whose commit checks are not green."

This task is the agents-web part: "agents-web image push and chart-publish need the `web` job."

Scope (agents-web):
- `.github/workflows/ci.yaml`: the `images` job (whose main-only step pushes to Harbor) gets `needs: [web]`; `chart-publish` needs `chart`, `images` and `web`. The build and smoke steps stay unconditional; the push and login stay main-only. `chart-publish-tag` is unchanged (it requires an image a passing main build pushed).
- `scripts/ci.test.mjs`: test no longer accurate, to update: "chart-publish: main only, needs chart and images, versions and pushes" asserts `needs` is exactly `[chart, images]`; it now asserts `[chart, images, web]`. A new test asserts `images` needs `web`. "exactly the five jobs" stays true.

Steps: change the tests first and see them fail; then the workflow; run `node --test scripts/ci.test.mjs`.

Notes: run with `node --test scripts/ci.test.mjs` (vitest only includes `src/**`). No em dashes.

## Acceptance conditions

- AC1: the images job, which pushes the image on main, needs the web job [evidence: command:node --test --test-name-pattern "images job needs web" scripts/ci.test.mjs]
- AC2: chart-publish needs chart, images and web [evidence: command:node --test --test-name-pattern "chart-publish" scripts/ci.test.mjs]
- AC3: every workflow test passes [evidence: command:node --test scripts/ci.test.mjs]

## Files

- `.github/workflows/ci.yaml`
- `scripts/ci.test.mjs`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `node --test scripts/ci.test.mjs` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `node --test scripts/ci.test.mjs` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
