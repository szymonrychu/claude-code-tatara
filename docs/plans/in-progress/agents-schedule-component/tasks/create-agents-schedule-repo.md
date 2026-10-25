---
title: create agents-schedule repo
status: in-progress
repo: superrepo
value: "the schedule service has its own public repo with CI secrets, ready for its code, image and chart"
files: [.gitmodules, code/agents-schedule, AGENTS.md]
verify: "git config --file .gitmodules --get submodule.agents-schedule.branch && cd code/agents-schedule && pytest tests/test_smoke.py -q && ruff check ."
depends_on: []
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

# create agents-schedule repo

## Requirement

Create the component `agents-schedule` (Python) with `workbench:component-add`. Runs in the superrepo (meta mode). Outward-facing: it creates the public GitHub repo `szymonrychu/agents-schedule` (approved at the gate by name), pushes its main and sets two repo secrets. Serves agents-schedule-microservice approvals A1 and A7 (design D1 there).

1. From the workbench root of this worktree: `mise run component:add -- --component agents-schedule:python --remote github --forge-owner szymonrychu --public --confirm-forge --role "agents-schedule=Python microservice mapping cron schedules to presets; fires agent clusters through the orchestrator API; own database"`. It scaffolds `code/agents-schedule` (AGENTS, CLAUDE, MEMORY, ROADMAP, README, `.mise.toml`, `.gitignore`, `tests/test_smoke.py`), creates and pushes the GitHub origin and adds the submodule (`.gitmodules`, branch main).
2. In `code/agents-schedule`: README gets a `## What this is` paragraph (a Python microservice with its own Postgres database that maps 5-field cron schedules with an IANA timezone to orchestrator presets and a prompt, and on each fire starts a cluster from the preset through the orchestrator API and sends the prompt); MEMORY.md gets a dated 2026-10-25 entry naming why the component exists and that it consumes the agents-common library and the orchestrator service tokens from agents-webhook-microservice. Commit and push main (fast-forward of the scaffold commit).
3. Set the CI secrets `HARBOR_USERNAME` and `HARBOR_PASSWORD` on the repo with `gh secret set -R szymonrychu/agents-schedule`, values on stdin, never echoed. If the values are not available to the agent, end `blocked` with whoCanClear "user: gh secret set HARBOR_USERNAME and HARBOR_PASSWORD -R szymonrychu/agents-schedule".
4. Commit the superrepo changes (`.gitmodules`, the `code/agents-schedule` gitlink, the `AGENTS.md` components row component-add writes) on this task's branch. Fill the role in the `AGENTS.md` project block if component-add left a placeholder.

Do not touch any other component.

## Acceptance conditions

- AC1: the public GitHub repo szymonrychu/agents-schedule exists and its main is the local main [evidence: command:gh repo view szymonrychu/agents-schedule --json visibility -q .visibility | grep -qx PUBLIC && cd code/agents-schedule && git fetch -q origin && test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"]
- AC2: code/agents-schedule is a submodule of the workbench tracking main [evidence: command:git config --file .gitmodules --get submodule.agents-schedule.branch | grep -qx main && git ls-files --stage code/agents-schedule | grep -q '^160000']
- AC3: both Harbor CI secrets are set on the repo [evidence: command:gh secret list -R szymonrychu/agents-schedule | grep -q HARBOR_USERNAME && gh secret list -R szymonrychu/agents-schedule | grep -q HARBOR_PASSWORD]
- AC4: the scaffold smoke test and lint pass in the component [evidence: command:cd code/agents-schedule && pytest tests/test_smoke.py -q && ruff check .]
- AC5: README says what the component is and MEMORY records why it exists [evidence: command:grep -q '^## What this is' code/agents-schedule/README.md && grep -q '2026-10-25' code/agents-schedule/MEMORY.md && grep -q agents-common code/agents-schedule/MEMORY.md]
- AC6: AGENTS.md lists agents-schedule in the components table [evidence: command:grep -q '| agents-schedule |' AGENTS.md]
- AC7: no other component changed and no repo other than szymonrychu/agents-schedule was created [evidence: judgement:the task diff and the gh calls reviewed against the requirement]

## Files

- `.gitmodules`
- `code/agents-schedule`
- `AGENTS.md`

## Interfaces

- `code/agents-schedule`: submodule, branch main, origin `https://github.com/szymonrychu/agents-schedule` (public). agents-schedule-microservice needs it to exist before its run starts (`ticket.py:_integration_plan`).
- Repo secrets `HARBOR_USERNAME`, `HARBOR_PASSWORD`, read by the CI workflow agents-schedule-microservice task `dockerfile-and-ci` adds.

## Expected outcome

`code/agents-schedule` is a submodule with a public GitHub origin and CI secrets; its README and MEMORY say what it is; the superrepo AGENTS.md lists it.

## Steps

- `git ls-remote https://github.com/szymonrychu/agents-schedule` fails before the task (repo absent).
- Run the component-add command of the requirement; AC1 and AC2 commands exit 0.
- Write README `## What this is` and the MEMORY entry; `cd code/agents-schedule && pytest tests/test_smoke.py -q && ruff check .`: `1 passed`, clean; push main.
- `gh secret set HARBOR_USERNAME -R szymonrychu/agents-schedule` and `HARBOR_PASSWORD` (values on stdin); AC3 exits 0.
- Commit `.gitmodules`, the gitlink and AGENTS.md on this task's branch.

## Notes

- Same shape as agents-web-component `create-agents-web-repo` and the agents-webhook D15 step; all new components are public like agent-orchestrator (probed: `gh repo view szymonrychu/agent-orchestrator` is PUBLIC).
- `mise run component:add` refuses with staged changes in the workbench; start from a clean tree.
- `scripts/init_engine/scaffold.py:write` writes no pyproject, Dockerfile, CI or chart; agents-schedule-microservice adds them.
- Never echo secret values.
