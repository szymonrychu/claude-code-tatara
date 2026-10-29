---
title: web cache client
status: todo
repo: agents-web
value: agents-web has a typed client for the orchestrator cache routes
files: [openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts, src/api/client.ts, src/api/client.test.ts]
verify: "npm ci --no-audit --no-fund && npx vitest run src/api/client.test.ts && npm run check:api && npm run build && npm run lint"
depends_on: [orch-cache-api]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web cache client

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

Design D5 (API on the web port only), verbatim: "`GET /api/v1/cache` (available, prefix, listed_at, listing state, totals, quota), `GET /api/v1/cache/objects` (`class`, `q`, `after`, `limit<=500`, ordered by key), `POST /api/v1/cache/deletions {object, etag}` 202 (404 not listed, 409 `in_use`, 503 `cache_not_configured`), `POST /api/v1/cache/refresh` 202, `GET /api/v1/cache/requests/{id}`. Not in `service_auth.ALLOWED_ROUTES`, not on the agent port. README route table, `openapi.json`, web `sync:api`."

This task delivers the agents-web side of D5's `sync:api`: `npm run sync:api -- orchestrator` from the agents-orchestrator commit that carries the cache routes (openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts), and typed functions in `src/api/client.ts` for the five routes with exported types `CacheSummary`, `CacheObjectView`, `CacheObjectsPage`, `CacheRequestView`, `DeleteCacheObject` and `CacheClass`. Errors come back as the existing `ApiError` with status and code (for example 409 `in_use`, 404 `not_listed`, 503 `cache_not_configured`).

## Acceptance conditions

- AC1: the vendored schema carries the cache routes and agrees with src/api/schema.d.ts [evidence: command:grep -q '"/api/v1/cache/objects"' openapi/orchestrator.json && npm run check:api]
- AC2: getCache, listCacheObjects (class, q, after, limit as query parameters), requestCacheDeletion (POST body object and etag), refreshCache and getCacheRequest call the orchestrator base with the right method, path and body [evidence: test:src/api/client.test.ts::cache_routes_paths_and_bodies]
- AC3: a 409 in_use, 404 not_listed or 503 cache_not_configured answer throws ApiError with that status and code [evidence: test:src/api/client.test.ts::cache_errors_carry_status_and_code]
- AC4: the client suite, the type check of the build and lint pass [evidence: command:npx vitest run src/api/client.test.ts && npm run build && npm run lint]

## Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`
- `src/api/client.ts`
- `src/api/client.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
