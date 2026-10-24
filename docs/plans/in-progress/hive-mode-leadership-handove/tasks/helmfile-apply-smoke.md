---
title: helmfile apply smoke
status: in-progress
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
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/hive-mode-leadership-handove-helmfile-apply-smoke/agents-helmfile
branch: hive-mode-leadership-handove-helmfile-apply-smoke
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

- Runs the agents-helmfile mise tasks `diff`, `apply`, `smoke` against the live namespace.

## Expected outcome

The hive release runs live, smoke is green and a live hive has a leader.

## Steps

- `mise run diff`: only the expected changes.
- `mise run apply`: succeeds.
- `mise run smoke`: exits 0.
- Live check of a 2-replica cluster's leader and `/agent/v1/me`; write the MEMORY entry.

## Notes

- Least destructive first: stop after `diff` if it shows anything beyond the pins, the Service and the settings.
