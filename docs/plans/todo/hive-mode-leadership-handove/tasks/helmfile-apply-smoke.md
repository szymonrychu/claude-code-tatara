---
title: helmfile apply smoke
status: todo
repo: agents-helmfile
value: the hive release runs live and passes smoke
files: [MEMORY.md]
verify: mise run smoke
depends_on: [helmfile-deploy-pin]
owns: []
uses: []
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

# helmfile apply smoke

## Requirement

Deploy and smoke the release (the user asked for helmfile bump, apply and smoke as explicit work). After the agents-helmfile PR merges, in `code/agents-helmfile` on `main`:

1. `mise run diff`: the change is the chart version, the image pins, the agents Service and the new settings; anything else stops the task.
2. `mise run apply` (live namespace; listed in design.md; existing agent clusters roll their pods once because the pod env and rendered config change).
3. `mise run smoke` green.
4. Live check: a 2-replica cluster shows a leader in `GET /api/v1/clusters/{id}` and its agent pod reaches `/agent/v1/me` with 200.
5. MEMORY.md entry dated with the applied chart, orchestrator image, wrapper image and any-mcp ref.

## Acceptance conditions

- AC1: the smoke script passes against the applied release [evidence: command:mise run smoke]
- AC2: the live 2-replica cluster has a leader and its agent pod gets 200 from /agent/v1/me [evidence: judgement:]
- AC3: MEMORY.md records the applied versions [evidence: command:grep -q "0.1.0-main" MEMORY.md]

## Files

- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
