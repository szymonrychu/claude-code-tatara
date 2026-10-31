---
title: agents-web component
repos: []
created: 2026-10-25
owner: Szymon Richert
rung: 1
---

# agents-web component

## What and why

What: Create the agents-web component repo with the frontend history
How: workbench:component-add makes the public GitHub repo and submodule, then the agent-orchestrator frontend history is merged in at the repo root
Why: frontend-decoupling moves the UI into its own TypeScript component; its tasks need code/agents-web to exist before they run

Split out of frontend-decoupling (2026-10-25) because ticket.py refuses an epic that mixes superrepo (meta) and component tasks, and every agents-web task of frontend-decoupling needs `code/agents-web` to exist before its run starts. User decision (frontend-decoupling): creating the GitHub repo agents-web via workbench:component-add is an outward-facing operation, an explicit task listed at the gate.

User request (2026-10-25), verbatim, from frontend-decoupling: "## frontend decoupling
  * decouple frontend from orchestrator microservice"

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: The public GitHub repo szymonrychu/agents-web exists, created by `mise run component:add`, and is the submodule `code/agents-web` of the workbench.
- 1.2: Its main carries the full history of `code/agent-orchestrator/frontend` (moved to the repo root) on top of the component scaffold, and `npm ci && npm test && npm run lint` pass there.

## Agreed scope

Rung 1, migrated from the epic format: the epic's goals were its agreed scope.

## Non-goals

- No change to the moved UI code, its API client, image, chart or CI (frontend-decoupling tasks).
- No deletion of `frontend/` from agent-orchestrator (frontend-decoupling task orch-drop-frontend-build).

## Design

Migrated from the epic format; the design sections without a plan.md heading are under Migrated notes.

## Decisions

### D1: component-add scaffold, then a subtree-split merge
`mise run component:add -- --component agents-web:typescript --remote github --forge-owner szymonrychu --public --confirm-forge` scaffolds and pushes; `git subtree split --prefix=frontend` of agent-orchestrator main merged with `--allow-unrelated-histories` keeps every frontend commit, paths at the root. The import is pushed to the new repo's main directly (no CI exists yet). Alternatives: `component:add --path` on a pre-built checkout (needs `gh repo create` outside component-add); a later in-epic merge task (the task merge tool rebases, which would replay the imported history onto the scaffold and conflict). Serves G1.

## Open questions

none

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery | ran: ../frontend-decoupling/discovery.md | component-add, history kept | fresh copy without history |
| others | skipped: one mechanical task | none | none |

### Research inputs

| Source | Entry | Lands in |
|---|---|---|
| frontend-decoupling discovery reuse | workbench:component-add | create-agents-web-repo |
| frontend-decoupling discovery ideas | move frontend/ with history | create-agents-web-repo |

## Irreversible operations

- Creating the public GitHub repo `szymonrychu/agents-web` and pushing its main: approved by name at the gate (frontend-decoupling gate).

## Migrated notes

### README.md: Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

Evidence: reviewer all 6 ACs met (1 fix round: architecture.md root label from component-add run in a worktree), scope audit clean, superrepo mise run test all green, lint clean.
Orchestrator ran step 1 (component:add) itself: the classifier refuses public repo creation inside subagents; user approved the allow rule.

### design.md: Summary

One superrepo task creates the component `agents-web` for epic frontend-decoupling: `mise run component:add` makes the public GitHub repo `szymonrychu/agents-web` and the submodule `code/agents-web`, then the history of `agent-orchestrator/frontend` is merged in at the repo root. Everything else (vendored API types, runtime config, image, chart, CI, the orchestrator cleanup and the deploys) is frontend-decoupling.

### design.md: Intent and why

User decision for frontend-decoupling: the UI moves to a new component repo with its history, and creating that GitHub repo through workbench:component-add is an explicit task listed at the gate. ticket.py refuses an epic that mixes superrepo and component tasks and needs `code/agents-web` to exist before an agents-web task runs, so the creation is its own epic and blocks frontend-decoupling.

### design.md: Goals

- `gh repo view szymonrychu/agents-web` shows a public repo; `code/agents-web` is a submodule tracking main.
- Its main has the frontend history at the root and passes `npm test` and `npm run lint`; `MEMORY.md` names the imported agent-orchestrator commit.

### design.md: Non-goals

- No change to the moved code and no deletion in agent-orchestrator (frontend-decoupling).

### design.md: Anti-goals

- Losing the frontend's git history; creating any other repo.

### design.md: Constraints

- Runs after agent-init-scripts and cluster-scaling have merged (README blockers), so their UI moves too.
- component-add runs only through `mise run component:add`; `--confirm-forge` only because the gate approves the repo by name.

### design.md: Decision coverage

| Decision | Tasks |
|---|---|
| D1 component-add scaffold, then a subtree-split merge | create-agents-web-repo |

### design.md: Contracts

No in-epic shared part. Cross-epic: `agents-web-repo` (docs/plans/contracts.json), consumed by frontend-decoupling.

### design.md: Review focus

- Only `.gitmodules`, the gitlink and the AGENTS.md row change in the superrepo; the merge keeps the frontend tree byte-identical.

### design.md: Left to the builder

- Conflict resolution details of `.gitignore` beyond the union rule.

### design.md: Assumptions and unknowns

- `git subtree` is available (checked: `git subtree` prints its usage on this machine).

### approvals.json

- G1: Create the public GitHub repo szymonrychu/agents-web via workbench:component-add (outward-facing, approved by name) as submodule code/agents-web, with the agent-orchestrator frontend history at its root. [decisions: D1] [tasks: create-agents-web-repo] [status: approved]
