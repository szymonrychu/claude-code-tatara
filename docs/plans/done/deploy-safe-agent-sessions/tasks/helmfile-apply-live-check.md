---
title: helmfile apply live check
status: done
repo: agents-helmfile
value: the fix runs live and the deploy is proven not to roll a busy agent
files: [MEMORY.md]
verify: mise run smoke
depends_on: [helmfile-deploy-pins]
model: sonnet
review: ""
verified_head: 2bc3ddd2228605a3c1d204bd502bffd3fbee1d54
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: 5
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile apply live check

## Requirement

Design D13, user decision verbatim: "Delivery: wrapper tag 0.3.2, orchestrator/web pins, agents-helmfile bump, apply, smoke, plus a live check after the deploy that no busy agent pod was replaced (reconciler logs / pod ages). Deploys and planned release tags are pre-approved."

Goal G10, verbatim: "Released and deployed: wrapper release tag, orchestrator and web pins, agents-helmfile bump, apply and smoke green, with a live check that the deploy did not roll a busy agent."

Design D2, user decision verbatim: ""A deploy never runs inside a pod that the same deploy rolls" is satisfied by D1: the deployer's pod is busy for the whole apply+smoke turn so it is not rolled until idle; an in-cluster Job runner is a non-goal. Add an orchestrator test that pins this (busy pod with outdated revision is not deleted across reconcile ticks)."

Live applies are run by the orchestrator session only, never by a subagent. Steps, after the agents-helmfile PR merges, in `code/agents-helmfile` on `main`, least destructive first:
1. Before: record every agent pod (namespace `agents`, StatefulSets `agent-*`) with uid, start time, its agent's state and leader flag (API), and the deployer's own pod name.
2. `mise run check-pins` green; `mise run diff`: only the orchestrator and agents-web chart versions and image tags and the agent image 0.3.2 change; anything else stops the task.
3. `mise run apply` (live; listed in design.md). The orchestrator applies the re-attach migration on start.
4. `mise run smoke` green, the session-continuity step included.
5. Live check: every agent StatefulSet is `OnDelete`; no pod whose agent was busy was deleted while busy (pod uids and start times against the step 1 record and the agent states, reconciler rollout log lines); the deployer's pod kept its uid through the apply and smoke turn; `status.rollout` drains to empty as agents go idle; no agent stays `dead`; a message to a rolled agent is answered.
6. MEMORY.md entry (containing the words `deploy-safe live check`) dated with the applied orchestrator chart and image, agents-web chart, wrapper image `0.3.2`, and the step 5 evidence.

Notes: never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25). Subagent `kubectl exec` is denied by the permission classifier; the whole task is orchestrator-run. `gh` must be authenticated in the deploying pod for check-pins.

## Acceptance conditions

- AC1: the smoke passes against the applied release, the session-continuity step included [evidence: command:mise run smoke]
- AC2: every agent StatefulSet is OnDelete live [evidence: command:test "$(kubectl -n agents get statefulset -o jsonpath='{range .items[*]}{.metadata.name}={.spec.updateStrategy.type}{"\n"}{end}' | grep '^agent-' | grep -vc '=OnDelete$')" = 0]
- AC3: MEMORY.md records the applied versions [evidence: command:grep -q "claude-code-wrapper:0.3.2" MEMORY.md]
- AC4: MEMORY.md records the live check that no busy agent pod was replaced and the deployer pod kept its uid [evidence: command:grep -q "deploy-safe live check" MEMORY.md]

## Files

- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `mise run smoke` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `mise run smoke` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done: applied 16:34Z by tatara-0 from main 030c93d; smoke OK incl. continuity; MEMORY entry PR #38 merged c9ba047; evidence .logs/deploy-safe-2026-10-28/live-check.md

- 2026-10-28 actuals: no agent records

- 2026-10-28 done

- 2026-10-28 actuals: no agent records
