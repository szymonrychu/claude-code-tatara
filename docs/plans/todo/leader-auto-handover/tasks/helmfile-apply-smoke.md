---
title: helmfile apply smoke
status: todo
repo: agents-helmfile
value: the auto-handover release runs live and passes smoke
files: [MEMORY.md]
verify: mise run smoke
depends_on: [helmfile-deploy-pin]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1836811
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile apply smoke

## Requirement

Goal G6, verbatim: "released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader." Live applies are run by the orchestrator session only, never by a subagent.

Steps, run by the orchestrator session after the agents-helmfile PR merges, in `code/agents-helmfile` on `main`, least destructive first:
1. `mise run diff`: the change is the orchestrator and agents-web chart versions and image tags and the agent image 0.3.0; anything else stops the task.
2. `mise run apply` (live namespace; listed in design.md). The orchestrator applies migration 0006 on start.
3. `mise run smoke` green, including the scale-down below the leader (task smoke-scale-below-leader).
4. First real message (retro agents-matrix-connector-depl): in a live 2-agent hive created from a preset, make pod-1 leader, scale to 1, then post an untargeted message; it is dispatched to the new leader (pod-0) and answered (message `sent`, an assistant reply in the events). Discard the session afterwards.
5. MEMORY.md entry (containing the words `leader-auto-handover live reply`) dated with the applied orchestrator chart, orchestrator image, agents-web chart, wrapper image `0.3.0`, the step 4 session and message ids, and, when a live hive has compacted since the apply, whether a `compacting` event was recorded (design.md assumption on real Claude Code PreCompact).

Notes: never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25). Subagent `kubectl exec` is denied by the permission classifier; the whole task is orchestrator-run. Existing sessions keep their snapshotted agent image; only new sessions get 0.3.0.

## Acceptance conditions

- AC1: the smoke script passes against the applied release, including the scale-down below the leader [evidence: command:mise run smoke]
- AC2: MEMORY.md records the applied versions [evidence: command:grep -q "claude-code-wrapper:0.3.0" MEMORY.md]
- AC3: MEMORY.md records the live first-message proof after a scale-down handover [evidence: command:grep -q "leader-auto-handover live reply" MEMORY.md]

## Files

- `MEMORY.md`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Orchestrator session only: `mise run diff`; stop unless it shows only the chart versions, image tags and the agent image.
- `mise run apply`: succeeds.
- `mise run smoke`: exits 0, including the scale-down below the leader.
- The live first-message proof (Requirement step 4), then the MEMORY.md entry; commit it through the agents-helmfile PR flow.

## Notes

See the Requirement and the acceptance conditions above.
