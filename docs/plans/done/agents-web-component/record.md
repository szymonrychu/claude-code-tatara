# agents-web component record

## Asked

Create the public GitHub repo szymonrychu/agents-web via workbench:component-add as submodule code/agents-web, with the full history of agent-orchestrator/frontend at its repo root. `npm ci && npm test && npm run lint` must pass there. No change to the moved UI code, image, chart or CI, and no deletion of frontend/ in agent-orchestrator.

## Shipped

Repo szymonrychu/agents-web (public) created; code/agents-web is a submodule tracking main. The frontend was imported with history (git subtree split from agent-orchestrator b7906aa); agents-web main is bbeab79. 218 tests passed and lint is clean. Reviewer found all 6 ACs met. Scope audit clean. Closed into main as a191c36 by ticket.py close (integration and main verify: `mise run test && mise run lint` passed). No MR or PR (meta mode).

## Tasks

| task | status | verified head | review rounds | verification tail |
|---|---|---|---|---|
| create-agents-web-repo | done | ccba4c6 | 1 fix round (docs/architecture.md root label was written as the worktree dir name by component-add) | agents-web: 218 tests passed, lint clean; points 1 (actual 1), 12 min, 597313 tokens (impl 445096, review 152217) |

Step 1 (`mise run component:add`) was run by the orchestrator, because the auto-mode classifier refuses public repo creation inside subagents. The user approved an allow rule. The implementer did steps 2-6.

Approval G1 (create public repo agents-web, decision D1, task create-agents-web-repo): delivered.

## Rulings

- Orchestrator ran step 1 instead of the implementer. Why: the classifier refuses public repo creation in subagents; the user approved an allow rule. Cost if wrong: none beyond a deviation from the task text; the repo and submodule are the same artifacts either way.
- Fix round: docs/architecture.md root label was the worktree dir name; corrected to the workbench root name (600382a). Cost if wrong: a wrong label in docs only.
- First close attempt failed on a stale ignored plugins/workbench/skills/heartbeat/ cache dir left from before the template merge. Removed (it held only .pyc); the second close passed. Cost if wrong: none, ignored cache only.

## Discovered and blocked

- Task notes: after this epic closes, run `git submodule update --init code/agents-web` in the main checkout before frontend-decoupling starts (ticket.py treats a task repo without a code/<repo> checkout as a meta task). Who clears it: orchestrator.
- The gen:api and check:api scripts still point at ../openapi.json after the import; frontend-decoupling task web-openapi-vendor fixes them. Who clears it: that task.

## Not pushed

Main (a191c36) is closed locally. The agents-web main was pushed to origin as part of the task. Whether the workbench main is pushed is unknown; the user or orchestrator pushes it.

## Lessons routed to

- component-add writes the worktree dir name as the docs/architecture.md root label: add a check to the existing `lint:root` mise task that the label matches the workbench root name (mechanical).
- A stale ignored skill dir (plugins/workbench/skills/heartbeat/) made close fail: add a lint or close-time check that names ignored leftover skill dirs without a SKILL.md (mechanical).
- Public repo creation is refused inside subagents: edit the component-add and start-development skills to say the orchestrator runs it (judgement call).
