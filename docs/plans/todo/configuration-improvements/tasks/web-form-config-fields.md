---
title: web form config fields
status: todo
repo: agents-web
value: "users set hooks, idle compact, lease and autoclose in the preset editor"
files: [openapi/agent-orchestrator.json, src/api/schema.d.ts, src/clusters/clusterSpecForm.ts, src/presets/PresetForm.tsx, src/presets/PresetForm.test.tsx]
verify: "npx vitest run src/presets/PresetForm.test.tsx && npm run lint && npm run check:api"
depends_on: [config-cluster-views]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web form config fields

## Requirement

Let users set every new field in the preset editor of agents-web (design D8, D12; approvals A1, A3, A4, A8).

- Sync the vendored orchestrator API description `openapi/agent-orchestrator.json` from agent-orchestrator main after config-cluster-views merged (recording the orchestrator commit it came from, per agents-web's sync convention) and regenerate `src/api/schema.d.ts`.
- `src/clusters/clusterSpecForm.ts`: form values and the spec mapping for `leader_lease_seconds`, `autoclose_after_seconds` and `wrapper` (auto-compact idle seconds, instructions and min context tokens; system append; restart continue prompt; turn stall seconds; max restarts; turn max seconds; agent commands; permissions allow and deny as comma lists; hooks, MCP servers and plugins as JSON text). Empty inputs stay unset so presets stay sparse; a stored preset spec loads back into the same values.
- `src/presets/PresetForm.tsx`: number inputs for the numeric fields, text inputs for the text fields, a multi-select for agent commands (compact, context, mcp, reload-plugins, reload-skills), JSON text areas for hooks, MCP servers and plugins (the existing any-mcp pattern: invalid JSON or a non-object shows an error and blocks save), and the leader lease input shown only when the spec is a hive (max replicas above 1). Help text says autoclose counts from creation with a 300 s minimum and that command hooks run with the agent's credentials. Server 422 messages show as today.

## Acceptance conditions

- AC1: the vendored orchestrator openapi copy and the generated types match [evidence: command:npm run check:api]
- AC2: every new input maps to its spec key, empty inputs stay unset, and a stored preset loads back into the same values [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "config fields"]
- AC3: invalid JSON in hooks, MCP servers or plugins blocks save with an error, and the lease input shows only for hive specs [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "config validation"]
- AC4: lint passes [evidence: command:npm run lint]

## Files

- `openapi/agent-orchestrator.json`
- `src/api/schema.d.ts`
- `src/clusters/clusterSpecForm.ts`
- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`

## Interfaces

Builds part `web-orch-schema-config` (`src/api/schema.d.ts` with the new spec and view fields); uses `orch-cluster-config-api`.

## Expected outcome

The preset editor in agents-web has inputs for every new field, saves a sparse spec and reloads it unchanged.

## Steps

- Sync `openapi/agent-orchestrator.json` from orchestrator main and run `npm run gen:api`, then `npm run check:api`: exits 0.
- Red: add the `config fields` and `config validation` tests to `src/presets/PresetForm.test.tsx`; `npx vitest run src/presets/PresetForm.test.tsx`: fails.
- Green: add the form values, mapping and inputs; run the verify command: passes.

## Notes

Paths assume frontend-decoupling moved `frontend/` to agents-web with its layout; if its plan names other paths, this task is amended with `ticket.py amend` before the run (design D12).
