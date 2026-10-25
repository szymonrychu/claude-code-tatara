---
title: create agents-webhook repo
status: todo
repo: superrepo
value: "the webhook service has its own repo and submodule, ready for the agents-webhook-microservice tasks"
files: [.gitmodules, code/agents-webhook, AGENTS.md]
verify: "git config --file .gitmodules --get submodule.agents-webhook.branch && cd code/agents-webhook && mise exec -- pytest tests/test_smoke.py -q && mise run lint"
depends_on: [create-agents-common-repo]
model: ""
review: full
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# create agents-webhook repo

## Requirement

Create the component `agents-webhook` (Python) with `workbench:component-add`. Runs in the superrepo (meta mode). Outward-facing: it creates the public GitHub repo `szymonrychu/agents-webhook` (approved at the agents-webhook-microservice gate by name, approval A6) and pushes its main.

1. From the workbench root of this worktree: `mise run component:add -- --component agents-webhook:python --remote github --forge-owner szymonrychu --public --confirm-forge --role "agents-webhook=Python microservice with its own Postgres database that receives GitHub/GitLab PR, issue and comment webhooks and Grafana alerts, queues them FIFO with dedup and limits, and starts agent clusters from presets through the orchestrator API"`. It scaffolds `code/agents-webhook`, creates and pushes the GitHub origin and adds the submodule (`.gitmodules`, branch main).
2. In `code/agents-webhook`: `mise exec -- pytest tests/test_smoke.py -q` (the scaffold's smoke test) and `mise run lint` pass.
3. Commit the superrepo changes (`.gitmodules`, the `code/agents-webhook` gitlink, the `AGENTS.md` components row component-add writes) on this task's branch; fill the role in the `AGENTS.md` project block if component-add left a placeholder.

No other repo is created and no file of another component changes. If the GitHub repo already exists, stop `blocked` with whoCanClear "user: confirm reuse of szymonrychu/agents-webhook" rather than overwriting it.

## Acceptance conditions

- AC1: the public GitHub repo szymonrychu/agents-webhook exists and its main is the local main [evidence: command:gh repo view szymonrychu/agents-webhook --json visibility -q .visibility | grep -qx PUBLIC && cd code/agents-webhook && git fetch -q origin && test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"]
- AC2: code/agents-webhook is a submodule of the workbench tracking main [evidence: command:git config --file .gitmodules --get submodule.agents-webhook.branch | grep -qx main && git ls-files --stage code/agents-webhook | grep -q '^160000']
- AC3: the scaffold passes its smoke test and lint [evidence: command:cd code/agents-webhook && mise exec -- pytest tests/test_smoke.py -q && mise run lint]
- AC4: AGENTS.md lists agents-webhook with its role [evidence: command:grep -q "agents-webhook" AGENTS.md]
- AC5: no repo other than szymonrychu/agents-webhook was created and no other component changed [evidence: judgement:the task diff and the gh calls in the task notes reviewed against the requirement]

## Files

- `.gitmodules`
- `code/agents-webhook`
- `AGENTS.md`

## Interfaces

- Provides `code/agents-webhook` with origin https://github.com/szymonrychu/agents-webhook, the precondition of agents-webhook-microservice task webhook-scaffold.

## Expected outcome

`code/agents-webhook` is a workbench submodule whose scaffold is green on its smoke test and `mise run lint`.

## Steps

- `mise run component:add -- ...` as in the requirement; confirm with `gh repo view szymonrychu/agents-webhook`.
- `mise exec -- pytest tests/test_smoke.py -q && mise run lint` in `code/agents-webhook`: pass.
- Commit the superrepo changes; run the AC commands.

## Notes

- No TDD cycle applies: repository creation with no behaviour change (the scaffold's own smoke test is the check).
- After this epic closes, the orchestrator runs `git submodule update --init code/agents-webhook` in the main checkout before agents-webhook-microservice starts: ticket.py treats a task repo without a `code/<repo>` checkout as a meta task.
- Precedent: docs/plans/todo/agents-web-component/tasks/create-agents-web-repo.md.
