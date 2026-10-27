---
title: web sync orchestrator api
status: in-progress
repo: agents-web
value: "the web client's generated types know the download route and the listing target_type"
files: [openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts]
verify: "mise exec -- npm run check:api && mise exec -- npx tsc -b && mise run lint"
depends_on: [orch-file-download-route]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 656326
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web sync orchestrator api

## Requirement

User decision U4, verbatim: "After the orchestrator route lands, regenerate the web client schema with `npm run sync:api -- orchestrator` and keep `npm run check:api` green."

Design D8, verbatim: "after the orchestrator route lands, `npm run sync:api -- orchestrator` (vendors `openapi/orchestrator.json`, `openapi/orchestrator.source`, regenerates `src/api/schema.d.ts`) and `npm run check:api` stays green. The sync takes everything between the current pin (ff54218) and the orchestrator head."

Scope (agents-web): run `mise exec -- npm run sync:api -- orchestrator --from <agents-orchestrator tree at the commit of orch-file-download-route>` (the default `../agents-orchestrator` is the sibling integration tree; the script refuses an uncommitted `openapi.json`). Commit exactly the three generated files. No hand edits.

## Acceptance conditions

- ac1: `openapi/orchestrator.source` names the agents-orchestrator commit that carries the download route, and the vendored document has it [evidence: command:grep -q '/api/v1/sessions/{session_id}/files/download' openapi/orchestrator.json && grep -q 'target_type' openapi/orchestrator.json]
- ac2: the generated types carry the route and `FileEntry.target_type` [evidence: command:grep -q 'files/download' src/api/schema.d.ts && grep -q 'target_type' src/api/schema.d.ts]
- ac3: the generated schemas match the vendored documents [evidence: command:mise exec -- npm run check:api]
- ac4: the type check and lint pass [evidence: command:mise exec -- npx tsc -b && mise run lint]

## Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

## Interfaces

- Generated: `openapi/orchestrator.json`, `openapi/orchestrator.source` (`agents-orchestrator <sha>`), `src/api/schema.d.ts` (`paths['/api/v1/sessions/{session_id}/files/download']`, `components['schemas']['FileEntry']['target_type']`).
- Consumed by web-download-icon.

## Expected outcome

The web client's generated types match the orchestrator commit carrying the download route, and `npm run check:api` is green.

## Steps

- Run `mise exec -- npm run sync:api -- orchestrator --from <agents-orchestrator tree at orch-file-download-route's commit>`: it prints the gen:api output and exits 0.
- Run the task's verify: passes. Commit exactly the three generated files.

## Notes

- The default `../agents-orchestrator` is the sibling integration tree; the script refuses an `openapi.json` with uncommitted changes.
- If the regenerated types break compilation elsewhere (drift since ff54218), report it as a `discovered` entry; do not patch it here.
- No hand edits to generated files.
