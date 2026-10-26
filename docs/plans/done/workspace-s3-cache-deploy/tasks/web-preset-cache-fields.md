---
title: web preset cache fields
status: done
repo: agents-web
value: users turn the workspace cache on per preset and optionally name its key in the UI
files: [src/sessions/sessionSpecForm.ts, src/presets/PresetForm.tsx, src/presets/PresetForm.test.tsx, openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts]
verify: "npx vitest run src/presets/PresetForm.test.tsx && npm run lint && npm run check:api"
depends_on: []
model: opus
review: ""
verified_head: 5c7f9d1
points: 3
expected_minutes: 6
expected_tokens: 937864
points_actual: 3
actual_minutes: 6
actual_tokens: 1636854
actual_roles: "impl 5, review 1"
actual_role_tokens: "impl 1482123, review 154731"
---

# web preset cache fields

## Requirement

Add the workspace cache to the preset form (design D10; consumes contracts orch-session-spec-cache and orch-meta-cache). Runs after the epic orchestrator-rename-sessions lands and after task cache-key-on-create. Paths are in code/agents-web under the post-rename names (today's `src/clusters/clusterSpecForm.ts` is `src/sessions/sessionSpecForm.ts`; if that epic chose another name, the same symbols `stateFromPreset`, `validate`, `toPresetSpec` apply and the orchestrator amends this file list first).

- Sync the orchestrator API: `openapi/orchestrator.json` copied from `openapi.json` of the agents-orchestrator commit that carries task cache-key-on-create, `openapi/orchestrator.source` set to `agents-orchestrator <that sha>`, `npm run gen:api` regenerates `src/api/schema.d.ts`.
- `sessionSpecForm.ts`: form values `cacheEnabled` (boolean), `cacheKey` (string), `cacheExclude` (string, one glob per line); set key `cache`; `stateFromPreset` reads `spec.cache`; `validate`: the key matches `^[a-z0-9][a-z0-9._-]{0,62}$` (message "Cache key: lowercase letters, digits, '.', '_' and '-', at most 63"), at most 50 exclude lines, each at most 256 characters, not starting with `/`, no `..` segment; `toPresetSpec` writes `cache: {}` plus `key` when non-empty and `exclude` when non-empty, only when the set key `cache` is present and `cacheEnabled` is true; an untouched preset writes no `cache`, and switching the cache off on a stored preset removes it.
- `src/presets/PresetForm.tsx`: a "Workspace cache" section: a Switch "Cache the workspace in S3", a TextField "Cache key" with placeholder "derived from the preset" and helper "Same key, same cache: sessions sharing a key share the workspace (last save wins)", a multiline TextField "Exclude (one glob per line)". When `meta.cache.available` is false the section is disabled with the helper "Workspace cache is not configured on the orchestrator".
- Tests in `src/presets/PresetForm.test.tsx`.

Core tasks in epic workspace-s3-cache that this task depends on (covered by the epic blocker): cache-key-on-create.

## Acceptance conditions

- AC1: enabling the cache with an empty key saves cache {} [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "saves an empty cache when enabled without a key"]
- AC2: a key and exclude lines are saved as cache.key and cache.exclude [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "saves the cache key and excludes"]
- AC3: an invalid key or exclude line shows an inline error and blocks saving [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "rejects an invalid cache key"]
- AC4: the section is disabled with its note when meta.cache.available is false [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "disables the cache section when the orchestrator has no cache"]
- AC5: editing a preset loads its stored cache [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "loads a stored cache"]
- AC6: a preset saved without touching the cache carries no cache key [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "keeps presets without a cache sparse"]
- AC7: the generated API types match the synced spec [evidence: command:npm run check:api]
- AC8: lint passes [evidence: command:npm run lint]

## Files

- `src/sessions/sessionSpecForm.ts`
- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`
- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-26 done
