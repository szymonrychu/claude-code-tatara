---
title: web api layer sessions
status: todo
repo: agents-web
value: the UI talks to the renamed orchestrator API with session types and routes
files: [scripts/sync-api.mjs, scripts/sync-api.test.mjs, openapi/orchestrator.json, openapi/orchestrator.source, src/]
verify: "npx tsc -b && npx vitest run && node --test scripts/sync-api.test.mjs && npm run check:api && npm run lint"
depends_on: [orch-agent-api-sessions]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 14
expected_tokens: 1883475
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web api layer sessions

## Requirement

Re-vendor the orchestrator API from agents-orchestrator and rename the UI's API layer to sessions (design D2, D11, D15; user decision: cluster is renamed session throughout (API, UI, docs), with the web UI fixed to match; contract `orch-sessions-api` and `agents-web-openapi-vendor`). Paths are in code/agents-web.

- `scripts/sync-api.mjs`: backend `orchestrator` reads repo `agents-orchestrator` from sibling `../agents-orchestrator`; `scripts/sync-api.test.mjs` expects `openapi/orchestrator.source` to read `agents-orchestrator <sha>`.
- `npm run sync:api -- orchestrator` against the orchestrator integration tree after orch-agent-api-sessions: `openapi/orchestrator.json`, `openapi/orchestrator.source`; `npm run gen:api` regenerates `src/api/schema.d.ts` (never hand-edited).
- `src/api/client.ts`: types `SessionView`, `SessionSummary`, `SessionSpec`, `CreateSession`; `listSessions`, `getSession`, `createSession`, `deleteSession` and every `/sessions/...` path; every `clusterId` parameter `sessionId`. `src/api/stream.ts`: SSE types `session_status`, `session_removed`. `src/api/files.ts`, `src/api/terminals.ts`: `session_id`, `sessionId`. Error code `session_deleting`.
- Every importer in src/ updated mechanically to the renamed types, functions and fields so `tsc -b` passes; visible labels and component names are the next tasks' work (web-sessions-pages, web-workspace-sessions).
- Tests first: `src/api/client.test.ts` "session routes" (every call uses `/api/v1/sessions...`, none `/clusters`), `src/api/stream.test.ts` "session events" (session_status and session_removed are handled), and the other tests touched by the type rename.

## Acceptance conditions

- AC1: the client calls only /api/v1/sessions routes [evidence: test:src/api/client.test.ts::session routes]
- AC2: the stream handles session_status and session_removed [evidence: test:src/api/stream.test.ts::session events]
- AC3: the vendored openapi comes from agents-orchestrator and the generated types match it [evidence: command:node --test scripts/sync-api.test.mjs && grep -q '^agents-orchestrator ' openapi/orchestrator.source && npm run check:api]
- AC4: the UI type-checks, its tests and lint pass [evidence: command:npx tsc -b && npx vitest run && npm run lint]

## Files

- `scripts/sync-api.mjs`
- `scripts/sync-api.test.mjs`
- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
