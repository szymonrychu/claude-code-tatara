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

- `src/api/client.ts`: `type CacheSummary = S['CacheSummary']`, `CacheObjectView`, `CacheObjectsPage`, `CacheRequestView`, `DeleteCacheObject`, `type CacheClass = 'in_use' | 'preset' | 'legacy' | 'saved' | 'other'`; `getCache(): Promise<CacheSummary>`, `listCacheObjects(params: { class?: CacheClass; q?: string; after?: string; limit?: number }): Promise<CacheObjectsPage>`, `requestCacheDeletion(object: string, etag: string): Promise<CacheRequestView>`, `refreshCache(): Promise<CacheRequestView>`, `getCacheRequest(id: number): Promise<CacheRequestView>`; all through the existing `request` and `query` helpers.
- Schema names come from agents-orchestrator `api/schemas.py` (task orch-cache-api).

## Expected outcome

agents-web has a typed client for the cache routes, generated from the orchestrator's committed openapi.json, ready for the Cache section.

## Steps

- Read `scripts/sync-api.mjs`, `src/api/client.ts` and `src/api/client.test.ts` in one pass; confirm `../agents-orchestrator` (the integration tree) is at the commit carrying the cache routes.
- `npm ci --no-audit --no-fund`; `npm run sync:api -- orchestrator`; expect openapi/orchestrator.json, openapi/orchestrator.source and src/api/schema.d.ts to change and `npm run check:api` to exit 0.
- Red: add `cache_routes_paths_and_bodies` and `cache_errors_carry_status_and_code` to `src/api/client.test.ts`; run `npx vitest run src/api/client.test.ts`; expect failures on the missing functions.
- Green: add the types and functions; rerun; expect passed; `npm run build && npm run lint`; expect exit 0.

## Notes

- Retro (matrix-connector-agent-initi, deploy-safe-agent-sessions): `openapi/orchestrator.source` pinned an epic-branch commit twice, and the orchestrator PR then had to merge with a merge commit so that sha stayed reachable. Sync from the orchestrator commit that will be on main (merge the agents-orchestrator PR first when possible); otherwise record in the task Notes that the orchestrator PR must merge with a merge commit.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main; both edit `src/sessions/DiscardSessionDialog.tsx`, the openapi files and `src/api/schema.d.ts` before this epic. Read the landed files first.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring; agents-web has a known load-dependent vitest timeout in PresetForm `name_rules_default_name_and_pvc`).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes, no colour literals, decorative Unicode or off-grid spacing (`layout/designRules.ts`), never the word "cluster" (`nomenclature.test.ts`). No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
- (my call) Builder check Q4: the agents-orchestrator epic PR merges to main first; `sync:api` runs from that main sha, never from the epic integration branch, so no merge-commit requirement arises.
