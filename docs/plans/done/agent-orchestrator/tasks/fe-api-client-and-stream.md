---
title: fe api client and stream
status: done
repo: agent-orchestrator
value: "Typed access to every API route the UI uses, generated from the server's OpenAPI, with a resilient live-event stream."
files: [frontend/package.json, frontend/src/api/schema.d.ts, frontend/src/api/client.ts, frontend/src/api/stream.ts, frontend/src/api/stream.test.ts]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/api/stream.test.ts && npm run lint"
depends_on: [fe-scaffold, readme-api-and-openapi]
model: ""
review: ""
verified_head: 6e19b7dc55a4ef20bf7c1d7b6fb975a5a6fcf60c
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 5
actual_tokens: 669602
actual_roles: "impl 3, review 2"
actual_role_tokens: "impl 464471, review 205131"
---

# fe api client and stream

## Requirement

The API layer of the UI (D12, D14).

package.json scripts:
- `gen:api`: `openapi-typescript ../openapi.json -o src/api/schema.d.ts`.
- `check:api`: regenerate to a temporary file and fail when it differs from the committed schema.

`src/api/schema.d.ts` is generated and committed.

`src/api/client.ts` has typed functions for every route the UI uses:
- clusters: list, get, create, patch, delete (the discard; no purge parameter); agents
- messages: post, list, get, cancel, retry
- agent commands; events page; meta
- A non-2xx response throws `ApiError {status, code, message}`, parsed from the error shape.

`src/api/stream.ts`, `openStream(url, {onEvent, onOpen, onError, afterId})`:
- Wraps EventSource and tracks the last event id.
- Each error closes the source and reconnects after a backoff: 1 s, doubled up to 30 s, reset by the first received event.
- A reconnect resumes with `?after_id=<last id>`.
- `close()` stops for good.
- The EventSource constructor is injectable for tests.

## Acceptance conditions

- AC1: the stream reconnects with exponential backoff capped at 30 s [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/api/stream.test.ts -t 'reconnects with capped exponential backoff']
- AC2: the backoff resets after the first received event [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/api/stream.test.ts -t 'resets backoff after first event']
- AC3: a reconnect resumes after the last seen event id [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/api/stream.test.ts -t 'resumes after last event id']
- AC4: close stops reconnecting [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/api/stream.test.ts -t 'close stops reconnecting']
- AC5: the generated types match openapi.json [evidence: command:cd frontend && npm ci --no-audit --no-fund && npm run check:api]

## Files

- `frontend/package.json`
- `frontend/src/api/schema.d.ts`
- `frontend/src/api/client.ts`
- `frontend/src/api/stream.ts`
- `frontend/src/api/stream.test.ts`

## Interfaces

- `frontend/src/api/client.ts` (contract `fe-api`): `listClusters`, `getCluster`, `createCluster`, `patchCluster`, `deleteCluster`, `listAgents`, `postMessage`, `listMessages`, `getMessage`, `cancelMessage`, `retryMessage`, `agentCommand`, `pageEvents`, `getMeta`, `ApiError`
- `frontend/src/api/stream.ts:openStream`

## Expected outcome

Components call typed functions and subscribe to resumable streams; a server API change without regeneration fails CI.

## Steps

- Write src/api/stream.test.ts with the four named tests, using a fake EventSource and fake timers. Run `npx vitest run src/api/stream.test.ts`; expect failures.
- Add the scripts, run `npm run gen:api`, then write client.ts and stream.ts.
- Rerun; expect `4 passed`.
- Run `npm run check:api` and `npm run lint`.

## Notes

Port the backoff logic from ros2 agent/agentSocket.ts (1-30 s, reset on first frame), retargeted from WebSocket to EventSource. The server's SSE also honours Last-Event-ID, but a manual reconnect after close() has to pass after_id.

- 2026-10-23 run agent-orchestrator: dependency-failed on readme-api-and-openapi
