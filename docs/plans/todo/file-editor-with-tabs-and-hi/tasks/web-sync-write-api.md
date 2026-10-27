---
title: web sync write api
status: todo
repo: agents-web
value: the web client can call the save route with typed requests and answers
files: [openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts, src/api/files.ts, src/api/files.test.ts]
verify: "mise exec -- npm run check:api && mise exec -- npx vitest run src/api/files.test.ts && mise exec -- npx tsc -b && mise run lint"
depends_on: [orch-file-write-route]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web sync write api

## Requirement

User decision U3, verbatim (the web client part): "new write route in the wrapper (PUT file content, UTF-8 text only, size cap = the existing file_preview_max_bytes, existing workspace path guards, optimistic concurrency via the mtime/size the editor loaded: a changed file answers 409 and the UI offers reload or overwrite) and an orchestrator forwarding route, then `npm run sync:api -- orchestrator`."

Design D8, verbatim: "after the orchestrator route lands, `npm run sync:api -- orchestrator` (vendors `openapi/orchestrator.json`, `openapi/orchestrator.source`, regenerates `src/api/schema.d.ts`), `npm run check:api` stays green, and `src/api/files.ts` gains `writeFile(sessionId, path, content, expected)` sending `PUT {base}/sessions/{id}/files/content?path=` with `{content, expected}` and answering `FileWritten`; its header comment stops saying read-only."

Scope (agents-web):
- Run `mise exec -- npm run sync:api -- orchestrator --from <agents-orchestrator tree at the commit of orch-file-write-route>` (the default `../agents-orchestrator` is the sibling integration tree; the script refuses an uncommitted `openapi.json`). Commit the three generated files as they come out; no hand edits.
- `src/api/files.ts`: `export type FileWritten`, `export type FileStamp` from the generated schema, and `writeFile(sessionId: string, path: string, content: string, expected: FileStamp | null): Promise<FileWritten>` through `request('PUT', ...)`; the header comment describes listing, reading, downloading and writing.
- `src/api/files.test.ts` (created by the download epic's web-download-icon): the new tests below.

## Acceptance conditions

- ac1: `openapi/orchestrator.source` names the agents-orchestrator commit that carries the write route, and the vendored document has the PUT operation and its schemas [evidence: command:grep -q '"put"' openapi/orchestrator.json && grep -q 'FileWritten' openapi/orchestrator.json && grep -q 'WriteFile' openapi/orchestrator.json && grep -q 'FileStamp' openapi/orchestrator.json]
- ac2: the generated types carry the PUT operation and the three schemas [evidence: command:grep -q 'FileWritten' src/api/schema.d.ts && grep -q 'WriteFile' src/api/schema.d.ts && grep -q 'FileStamp' src/api/schema.d.ts]
- ac3: the generated schemas match the vendored documents [evidence: command:mise exec -- npm run check:api]
- ac4: `writeFile('c1', 'src/a b.txt', 'x\n', {mtime, size})` sends `PUT` to the relative `${base()}/sessions/c1/files/content?path=src%2Fa+b.txt` with header `Content-Type: application/json` and body `{"content":"x\n","expected":{"mtime":...,"size":...}}`, and resolves to the parsed `FileWritten`; `expected: null` is sent as `null` (new) [evidence: command:mise exec -- npx vitest run src/api/files.test.ts -t 'writeFile sends']
- ac5: a 409 answer with code `file_changed` rejects with an `ApiError` whose `status` is 409 and `code` is `file_changed` (new) [evidence: command:mise exec -- npx vitest run src/api/files.test.ts -t 'writeFile conflict']
- ac6: the header comment of `src/api/files.ts` no longer says read-only [evidence: command:! grep -qi 'read-only' src/api/files.ts]
- ac7: the files API suite, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/api/files.test.ts && mise exec -- npx tsc -b && mise run lint]

## Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`
- `src/api/files.ts`
- `src/api/files.test.ts`

## Interfaces

- Generated: `openapi/orchestrator.json`, `openapi/orchestrator.source` (`agents-orchestrator <sha>`), `src/api/schema.d.ts` (`paths['/api/v1/sessions/{session_id}/files/content']['put']`, `components['schemas']['WriteFile' | 'FileStamp' | 'FileWritten']`).
- `src/api/files.ts`: `export type FileStamp = components['schemas']['FileStamp']`, `export type FileWritten = components['schemas']['FileWritten']`, `writeFile(sessionId: string, path: string, content: string, expected: FileStamp | null): Promise<FileWritten>`, sent with `request('PUT', ...)` to `/sessions/<id>/files/content?path=<rel>` with the body `{ content, expected }`.
- Kept: `listFiles`, `readFile`, `fileDownloadUrl` (download epic) unchanged.
- Consumed by web-file-tabs-state.

## Expected outcome

The web client's generated types match the orchestrator commit carrying the write route, `npm run check:api` is green, and `writeFile` saves through the relative base path.

## Steps

- Run `mise exec -- npm run sync:api -- orchestrator --from <agents-orchestrator tree at orch-file-write-route's commit>`: it prints the gen:api output and exits 0.
- Red: add the two `writeFile` tests to `src/api/files.test.ts` (fetch stubbed as the file already does for `fileDownloadUrl`, or `vi.stubGlobal('fetch', ...)` as `src/api/client.test.ts` does); run `mise exec -- npx vitest run src/api/files.test.ts`: fails (no export).
- Green: `writeFile` and the types; run the task's verify: passes, quote the vitest summary line.

## Notes

- The default `../agents-orchestrator` is the sibling integration tree; the script refuses an `openapi.json` with uncommitted changes.
- If the regenerated types break compilation elsewhere (drift since the download epic's sync), report it as a `discovered` entry; do not patch it here.
- No hand edits to generated files. `request` already sets `Content-Type: application/json` when a body is given (`src/api/client.ts:requestAt`).
