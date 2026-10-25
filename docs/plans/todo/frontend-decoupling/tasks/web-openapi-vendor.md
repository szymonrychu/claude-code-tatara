---
title: web openapi vendor
status: todo
repo: agents-web
value: "the UI's API types come from a recorded orchestrator commit inside its own repo"
files: [openapi/orchestrator.json, openapi/orchestrator.source, scripts/sync-api.mjs, scripts/sync-api.test.mjs, package.json, src/api/schema.d.ts, README.md]
verify: "npm ci --no-audit --no-fund && node --test scripts/sync-api.test.mjs && npm run check:api && npm run lint"
depends_on: []
owns: [openapi-vendor]
uses: []
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
