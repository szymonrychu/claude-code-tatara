---
title: web openapi vendor
status: done
repo: agents-web
value: "the UI's API types come from a recorded orchestrator commit inside its own repo"
files: [openapi/orchestrator.json, openapi/orchestrator.source, scripts/sync-api.mjs, scripts/sync-api.test.mjs, package.json, src/api/schema.d.ts, README.md]
verify: "npm ci --no-audit --no-fund && node --test scripts/sync-api.test.mjs && npm run check:api && npm run lint"
depends_on: []
model: ""
review: ""
verified_head: b2d2d30
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 1
actual_minutes: 2
actual_tokens: 267341
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 212819, review 54522"
---

# web openapi vendor

## Requirement

Vendor the orchestrator's OpenAPI document into agents-web and generate the UI types from that copy (design D5). Paths are in code/agents-web; `code/agents-web` was created by epic agents-web-component with `frontend/` of agent-orchestrator at its root.

- `openapi/orchestrator.json`: byte-identical to `openapi.json` of agent-orchestrator at the commit named in `openapi/orchestrator.source`.
- `openapi/orchestrator.source`: one line `agent-orchestrator <sha40>`.
- `scripts/sync-api.mjs` (node, no dependency), run as `npm run sync:api -- <backend-id> [--from <checkout>]`: `<backend-id>` names the vendored file (`orchestrator` maps to the agent-orchestrator repo); `--from` defaults to `../agent-orchestrator` (the workbench sibling). It refuses, exit 1 naming the path, when the source `openapi.json` has uncommitted changes in that checkout; it refuses an unknown backend id with exit 2; otherwise it copies `openapi.json` to `openapi/<id>.json`, writes `openapi/<id>.source` from `git -C <checkout> rev-parse HEAD`, and runs `gen:api`.
- `package.json` scripts: `gen:api` is `openapi-typescript openapi/orchestrator.json -o src/api/schema.d.ts`; `check:api` diffs a fresh generation from `openapi/orchestrator.json` against `src/api/schema.d.ts` (as today, temp file under `${TMPDIR:-/tmp}`); `sync:api` runs the script. No script references `../openapi.json`.
- `src/api/schema.d.ts` is regenerated and unchanged in meaning (a diff only if the vendored commit is newer than the import).
- `README.md` `## API types`: how a backend's document is vendored, the source line, and that every orchestrator route or schema change is followed by `npm run sync:api -- orchestrator` here (contract agents-web-openapi-vendor).

## Acceptance conditions

- AC1: sync copies the document, records the source commit and refuses a dirty source or an unknown backend [evidence: command:node --test scripts/sync-api.test.mjs]
- AC2: the generated types match the vendored document [evidence: command:npm run check:api]
- AC3: the vendored copy equals agent-orchestrator openapi.json at the recorded commit [evidence: command:read -r repo sha < openapi/orchestrator.source && test "$repo" = agent-orchestrator && curl -fsSL "https://raw.githubusercontent.com/szymonrychu/agent-orchestrator/$sha/openapi.json" | diff -q - openapi/orchestrator.json]
- AC4: no script reads the old sibling path [evidence: command:! grep -n '\.\./openapi.json' package.json]
- AC5: the README documents the vendoring rule [evidence: doc-section:README.md#API types]

## Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `scripts/sync-api.mjs`
- `scripts/sync-api.test.mjs`
- `package.json`
- `src/api/schema.d.ts`
- `README.md`

## Interfaces

- Owns contract `agents-web-openapi-vendor` (docs/plans/contracts.json): `openapi/<backend-id>.json` plus `openapi/<backend-id>.source` (`<repo> <sha40>`), `npm run sync:api -- <backend-id> [--from <checkout>]`, `npm run check:api`. Later backends (webhooks, schedules) add their id to the script's map.

## Expected outcome

`npm run check:api` passes against the vendored copy; `npm run sync:api -- orchestrator` refreshes it from the sibling checkout and records the commit.

## Steps

- Red: `scripts/sync-api.test.mjs` (node:test) builds a temp git repo holding an `openapi.json`, runs the script with `--from` and asserts the copy, the source line, exit 1 on a dirty file and exit 2 on an unknown id; `node --test scripts/sync-api.test.mjs` fails (no script).
- Green: write `scripts/sync-api.mjs` and the package scripts; run it once against agent-orchestrator main (`--from` the workbench `code/agent-orchestrator`, or a fresh clone of https://github.com/szymonrychu/agent-orchestrator at main).
- `npm run check:api`, `npm run lint`: pass.

## Notes

- The script must not run `gen:api` through a shell string built from the backend id (fixed map only).
- agent-orchestrator `/api/v1` is additive-only (README Versioning), so a UI built against an older copy keeps working.

- 2026-10-25 done
