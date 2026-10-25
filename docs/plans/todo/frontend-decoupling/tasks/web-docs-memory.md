---
title: web docs memory
status: todo
repo: agents-web
value: developers of later services learn from agents-web alone how to add a backend
files: [README.md, AGENTS.md, MEMORY.md]
verify: "grep -q '^## Runtime config' README.md && grep -q '^## Backends and menu' README.md && grep -q '^## URL layout' README.md && grep -q react-resizable-panels MEMORY.md"
depends_on: [web-backend-menu, web-ci-release]
owns: []
uses: [backend-registry, url-layout]
model: ""
estimate: 5
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

# web docs memory

## Requirement

Document agents-web and carry its UI lessons over (design D1, D2, D3). Paths are in code/agents-web. Doc-only.

- `README.md`: what the component is (the web UI of the agents system, the only TypeScript component); `## Development` (`npm ci`, `npm run dev`, the `AGENTS_WEB_PROXY_<ID>` proxy targets, list `http://localhost:5173` in the orchestrator's `ORCH_ALLOWED_ORIGINS` for terminal sockets); `## Runtime config` (the `config.json` schema and rules, default, set by the chart's `backends`); `## Backends and menu` (how a backend registers menu entries in `src/backends/registry.ts`, the order slots 10 Clusters, 20 Webhooks, 30 Schedules, 40 Presets); `## URL layout` (the contract rule, pointing at the chart README); links to `## API types`, `## Image`, `## Release` written by the other tasks.
- `AGENTS.md`: the commands (`mise run test`, `lint`, `fmt`, `test:chart`, `lint:chart`, `smoke:image`, `npm run sync:api -- orchestrator`) and the rule that the UI calls backends only through relative paths from `config.json`.
- `MEMORY.md`: the UI lessons from agent-orchestrator `MEMORY.md` (the react-resizable-panels `Separator` flex-basis pitfall, the FilesPanel polling decision, and every other UI-only entry present at the import), each with its original date and "moved from agent-orchestrator MEMORY.md".
- `ROADMAP.md` is not touched (human-owned).

## Acceptance conditions

- AC1: the README documents runtime config [evidence: doc-section:README.md#Runtime config]
- AC2: the README documents backends and menu [evidence: doc-section:README.md#Backends and menu]
- AC3: the README documents the URL layout [evidence: doc-section:README.md#URL layout]
- AC4: the README documents development [evidence: doc-section:README.md#Development]
- AC5: the UI lessons are in MEMORY.md [evidence: command:grep -q react-resizable-panels MEMORY.md && grep -q FilesPanel MEMORY.md && grep -q "moved from agent-orchestrator" MEMORY.md]
- AC6: AGENTS.md lists the commands [evidence: command:grep -q "sync:api" AGENTS.md && grep -q "smoke:image" AGENTS.md]

## Files

- `README.md`
- `AGENTS.md`
- `MEMORY.md`

## Interfaces

- Documents contracts `agents-web-backends-config`, `agents-web-backend-registry`, `agents-web-url-layout`. Uses `backend-registry`.

## Expected outcome

A developer of a later service learns from agents-web's README alone how to add a backend, its menu entries and its path prefix.

## Steps

- Write the sections; run the AC commands; all pass.

## Notes

- No TDD cycle applies: doc edit exception.
