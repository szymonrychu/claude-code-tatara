---
title: web docs names
status: todo
repo: agents-web
value: "agents-web's docs and chart say session and agents-orchestrator, guarded"
files: [README.md, chart/agents-web/README.md, chart/agents-web/values.yaml, MEMORY.md, src/nomenclature.test.ts]
verify: "npx vitest run src/nomenclature.test.ts && npm run test:chart && npm run lint:chart && npm run lint"
depends_on: [web-webhooks-session-fields]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web docs names

## Requirement

Finish the rename in agents-web's docs and chart and guard the whole repo (design D1, D2, D12). Paths are in code/agents-web.

- `README.md`, `chart/agents-web/README.md`, `chart/agents-web/values.yaml` comments: agents-orchestrator owns `/api`; `npm run sync:api -- orchestrator` reads `../agents-orchestrator`; session for the unit.
- `MEMORY.md`: a dated 2026-10-25 line: the UI says session everywhere, menu entry id `sessions`, saved layouts under old keys dropped once, no aliases; earlier dated lines keep their history.
- `src/nomenclature.test.ts`: guard every tracked file (`git ls-files`), allowlisting only the D12 Kubernetes phrases (for example "cluster-internal" in chart docs) and the dated-history files.

## Acceptance conditions

- AC1: no tracked file names the unit cluster or the project agent-orchestrator outside the allowlist and dated history [evidence: command:npx vitest run src/nomenclature.test.ts]
- AC2: MEMORY.md records the UI rename [evidence: command:grep -q 'sessions' MEMORY.md]
- AC3: chart tests, chart lint and lint pass [evidence: command:npm run test:chart && npm run lint:chart && npm run lint]

## Files

- `README.md`
- `chart/agents-web/README.md`
- `chart/agents-web/values.yaml`
- `MEMORY.md`
- `src/nomenclature.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
