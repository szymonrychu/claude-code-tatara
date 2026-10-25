---
title: create agents-schedule repo
status: todo
repo: agents-schedule
value: "the agents-schedule component exists with a GitHub origin, CI secrets and its role written down"
files: [AGENTS.md, README.md, MEMORY.md, ROADMAP.md, .mise.toml, tests/test_smoke.py]
verify: "pytest tests/test_smoke.py -q && ruff check ."
depends_on: []
owns: [agents-schedule-repo]
uses: []
model: ""
estimate: 6
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

# create agents-schedule repo

## Requirement

Create the component `agents-schedule` (design D1; approvals A1, A7). This is the epic's one outward-facing repo creation and is listed at the gate.

- Pre-run step, done by the orchestrator in the superrepo main checkout right after the gate and before the epic's first plan-execute run (the integration tree needs `code/agents-schedule` to exist): `mise run component:add -- --component agents-schedule:python --remote github --forge-owner szymonrychu --public --confirm-forge --role agents-schedule="Python microservice mapping cron schedules to presets; fires agent clusters through the orchestrator API, own database"`. The engine scaffolds AGENTS, CLAUDE, MEMORY, ROADMAP, README, `.mise.toml`, `.gitignore`, `tests/test_smoke.py`, creates `github.com/szymonrychu/agents-schedule`, adds the submodule under `code/agents-schedule` and commits it in the superrepo.
- In the run, this task completes the component side: README `## What this is` paragraph (from design.md Summary), MEMORY.md first entry (2026-10-25, why the component exists and that it consumes agents-common from agents-webhook-microservice), AGENTS.md pointing at mise test/lint like the other components, ROADMAP.md left with the scaffold's human-owned header only.
- CI secrets `HARBOR_USERNAME` and `HARBOR_PASSWORD` are set on the new repo with `gh secret set -R szymonrychu/agents-schedule` from the operator environment. If the values are not available to the agent, the task is `blocked` with whoCanClear = the user (one `gh secret set` per secret).
- The superrepo AGENTS.md components table carries an `agents-schedule` row (python, the role above, build `mise run --cd code/agents-schedule test`); the engine writes it, the orchestrator fixes a placeholder role in the same pre-run step.

## Acceptance conditions

- AC1: the GitHub repo exists and is public [evidence: command:test "$(gh repo view szymonrychu/agents-schedule --json visibility -q .visibility)" = PUBLIC]
- AC2: the origin answers on main [evidence: command:git ls-remote --exit-code https://github.com/szymonrychu/agents-schedule refs/heads/main]
- AC3: both Harbor CI secrets are set on the repo [evidence: command:gh secret list -R szymonrychu/agents-schedule | grep -q HARBOR_USERNAME && gh secret list -R szymonrychu/agents-schedule | grep -q HARBOR_PASSWORD]
- AC4: the scaffold smoke test passes [evidence: test:tests/test_smoke.py::test_smoke]
- AC5: README states what the component is [evidence: doc-section:README.md#What this is]
- AC6: MEMORY.md records why the component exists and what it consumes [evidence: judgement:MEMORY.md first entry dated 2026-10-25 names agents-common and the orchestrator API]

## Files

- `AGENTS.md`
- `README.md`
- `MEMORY.md`
- `ROADMAP.md`
- `.mise.toml`
- `tests/test_smoke.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
