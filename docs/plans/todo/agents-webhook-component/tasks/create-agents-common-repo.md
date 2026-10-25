---
title: create agents-common repo
status: todo
repo: superrepo
value: "the shared trigger library has its own repo and submodule, ready for the agents-webhook-microservice tasks"
files: [.gitmodules, code/agents-common, AGENTS.md]
verify: "git config --file .gitmodules --get submodule.agents-common.branch && cd code/agents-common && mise run test && mise run lint"
depends_on: []
owns: []
uses: []
model: ""
estimate: 37
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# create agents-common repo

## Requirement

Create the component `agents-common` (Python) with `workbench:component-add`. Runs in the superrepo (meta mode). Outward-facing: it creates the public GitHub repo `szymonrychu/agents-common` (approved at the agents-webhook-microservice gate by name, approval A6) and pushes its main.

1. From the workbench root of this worktree: `mise run component:add -- --component agents-common:python --remote github --forge-owner szymonrychu --public --confirm-forge --role "agents-common=Python library shared by the trigger services (agents-webhook, agents-schedule): settings, Postgres pool, migrator, guarded queue transitions, orchestrator client, run tracker"`. It scaffolds `code/agents-common`, creates and pushes the GitHub origin and adds the submodule (`.gitmodules`, branch main).
2. In `code/agents-common`: `mise run test` and `mise run lint` pass on the scaffold.
3. Commit the superrepo changes (`.gitmodules`, the `code/agents-common` gitlink, the `AGENTS.md` components row component-add writes) on this task's branch; fill the role in the `AGENTS.md` project block if component-add left a placeholder.

No other repo is created and no file of another component changes. If the GitHub repo already exists, stop `blocked` with whoCanClear "user: confirm reuse of szymonrychu/agents-common" rather than overwriting it.

## Acceptance conditions

- AC1: the public GitHub repo szymonrychu/agents-common exists and its main is the local main [evidence: command:gh repo view szymonrychu/agents-common --json visibility -q .visibility | grep -qx PUBLIC && cd code/agents-common && git fetch -q origin && test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"]
- AC2: code/agents-common is a submodule of the workbench tracking main [evidence: command:git config --file .gitmodules --get submodule.agents-common.branch | grep -qx main && git ls-files --stage code/agents-common | grep -q '^160000']
- AC3: the scaffold passes its own test and lint [evidence: command:cd code/agents-common && mise run test && mise run lint]
- AC4: AGENTS.md lists agents-common with its role [evidence: command:grep -q "agents-common" AGENTS.md]
- AC5: no repo other than szymonrychu/agents-common was created and no other component changed [evidence: judgement:the task diff and the gh calls in the task notes reviewed against the requirement]

## Files

- `.gitmodules`
- `code/agents-common`
- `AGENTS.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
