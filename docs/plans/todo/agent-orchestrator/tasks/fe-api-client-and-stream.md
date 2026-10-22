---
title: fe api client and stream
status: todo
repo: agent-orchestrator
value: "Typed access to every API route the UI uses, generated from the server's OpenAPI, with a resilient live-event stream."
files: [frontend/package.json, frontend/src/api/schema.d.ts, frontend/src/api/client.ts, frontend/src/api/stream.ts, frontend/src/api/stream.test.ts]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/api/stream.test.ts && npm run lint"
depends_on: [fe-scaffold, readme-api-and-openapi]
owns: [fe-api]
uses: [openapi-v1]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# fe api client and stream

## Requirement

The API layer of the UI (D12, D14).

package.json scripts:
- `gen:api`: `openapi-typescript ../openapi.json -o src/api/schema.d.ts`.
- `check:api`: regenerate to a temporary file and fail when it differs from the committed schema.

`src/api/schema.d.ts` is generated and committed.

`src/api/client.ts` has typed functions for every route the UI uses:
- clusters: list, get, create, patch, delete with purge; agents
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

- AC1: the stream reconnects with exponential backoff capped at 30 s [evidence: test:frontend/src/api/stream.test.ts::reconnects with capped exponential backoff]
- AC2: the backoff resets after the first received event [evidence: test:frontend/src/api/stream.test.ts::resets backoff after first event]
- AC3: a reconnect resumes after the last seen event id [evidence: test:frontend/src/api/stream.test.ts::resumes after last event id]
- AC4: close stops reconnecting [evidence: test:frontend/src/api/stream.test.ts::close stops reconnecting]
- AC5: the generated types match openapi.json [evidence: command:cd frontend && npm ci --no-audit --no-fund && npm run check:api]

## Files

- `frontend/package.json`
- `frontend/src/api/schema.d.ts`
- `frontend/src/api/client.ts`
- `frontend/src/api/stream.ts`
- `frontend/src/api/stream.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
