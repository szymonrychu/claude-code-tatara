---
title: web sync message priority
status: todo
repo: agents-web
value: "the web client's API types include the message priority"
files: [openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts]
verify: "npm run check:api && npx tsc -b && npm run lint"
depends_on: [orch-session-send-priority]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 632059
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web sync message priority

## Requirement

Design D16, verbatim: "The vendored orchestrator spec and `schema.d.ts` are re-synced first."

Design Constraints, verbatim: "Generated files are regenerated, never hand-edited: orchestrator `openapi.json` (`uv run python -m agents_orchestrator.api.openapi > openapi.json`), agents-web `src/api/schema.d.ts` (`npm run sync:api -- orchestrator`)."

Scope (agents-web): `openapi/orchestrator.json`, `openapi/orchestrator.source` (an agents-orchestrator commit whose `openapi.json` carries `priority`), `src/api/schema.d.ts` (generated).

## Acceptance conditions

- ac1: the vendored spec and the generated types agree [evidence: command:npm run check:api]
- ac2: PostMessage and MessageView carry priority in the vendored spec and the generated types [evidence: command:grep -q '"priority"' openapi/orchestrator.json && grep -q 'priority' src/api/schema.d.ts]
- ac3: the source pin names an agents-orchestrator commit whose openapi.json carries priority [evidence: command:git -C ../agents-orchestrator show "$(awk '{print $2}' openapi/orchestrator.source):openapi.json" | grep -q '"priority"']
- ac4: the app type-checks and lint passes [evidence: command:npx tsc -b && npm run lint]

## Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
