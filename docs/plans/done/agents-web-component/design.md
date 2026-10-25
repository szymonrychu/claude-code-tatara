# agents-web component design

## Summary

One superrepo task creates the component `agents-web` for epic frontend-decoupling: `mise run component:add` makes the public GitHub repo `szymonrychu/agents-web` and the submodule `code/agents-web`, then the history of `agent-orchestrator/frontend` is merged in at the repo root. Everything else (vendored API types, runtime config, image, chart, CI, the orchestrator cleanup and the deploys) is frontend-decoupling.

## Intent and why

User decision for frontend-decoupling: the UI moves to a new component repo with its history, and creating that GitHub repo through workbench:component-add is an explicit task listed at the gate. ticket.py refuses an epic that mixes superrepo and component tasks and needs `code/agents-web` to exist before an agents-web task runs, so the creation is its own epic and blocks frontend-decoupling.

## Goals

- `gh repo view szymonrychu/agents-web` shows a public repo; `code/agents-web` is a submodule tracking main.
- Its main has the frontend history at the root and passes `npm test` and `npm run lint`; `MEMORY.md` names the imported agent-orchestrator commit.

## Non-goals

- No change to the moved code and no deletion in agent-orchestrator (frontend-decoupling).

## Anti-goals

- Losing the frontend's git history; creating any other repo.

## Constraints

- Runs after agent-init-scripts and cluster-scaling have merged (README blockers), so their UI moves too.
- component-add runs only through `mise run component:add`; `--confirm-forge` only because the gate approves the repo by name.

## Decisions

### D1: component-add scaffold, then a subtree-split merge
`mise run component:add -- --component agents-web:typescript --remote github --forge-owner szymonrychu --public --confirm-forge` scaffolds and pushes; `git subtree split --prefix=frontend` of agent-orchestrator main merged with `--allow-unrelated-histories` keeps every frontend commit, paths at the root. The import is pushed to the new repo's main directly (no CI exists yet). Alternatives: `component:add --path` on a pre-built checkout (needs `gh repo create` outside component-add); a later in-epic merge task (the task merge tool rebases, which would replay the imported history onto the scaffold and conflict). Serves G1.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery | ran: ../frontend-decoupling/discovery.md | component-add, history kept | fresh copy without history |
| others | skipped: one mechanical task | none | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| frontend-decoupling discovery reuse | workbench:component-add | create-agents-web-repo |
| frontend-decoupling discovery ideas | move frontend/ with history | create-agents-web-repo |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 component-add scaffold, then a subtree-split merge | create-agents-web-repo |

## Contracts

No in-epic shared part. Cross-epic: `agents-web-repo` (docs/plans/contracts.json), consumed by frontend-decoupling.

## Review focus

- Only `.gitmodules`, the gitlink and the AGENTS.md row change in the superrepo; the merge keeps the frontend tree byte-identical.

## Left to the builder

- Conflict resolution details of `.gitignore` beyond the union rule.

## Assumptions and unknowns

- `git subtree` is available (checked: `git subtree` prints its usage on this machine).

## Open questions

none

## Irreversible operations in scope

- Creating the public GitHub repo `szymonrychu/agents-web` and pushing its main: approved by name at the gate (frontend-decoupling gate).
