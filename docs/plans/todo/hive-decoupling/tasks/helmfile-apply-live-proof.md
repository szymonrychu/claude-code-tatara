---
title: helmfile apply live proof
status: todo
repo: agents-helmfile
value: members run unstreamed live and a real leader hands over after briefing its successor
files: [MEMORY.md]
verify: "mise run lint && grep -q 'hive-decoupling live handoff' MEMORY.md"
depends_on: [helmfile-deploy-pin]
model: sonnet
review: ""
verified_head: ""
points: 8
expected_minutes: 14
expected_tokens: 3155191
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile apply live proof

## Requirement

User request (2026-10-27), verbatim: "Maybe leader could get a signal to pass on its session details to another agent when it hits a limit and both could talk to each other about details for handoff?"

README Goal G5, verbatim: "Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof."

Design D11, verbatim: "After the apply the orchestrator session runs a live proof in a throwaway 2-agent hive with `auto_compact_pct` 20 (threshold 5%, which a fresh leader already exceeds): the leader receives `handover_due`, briefs the named successor over ccw, the handover is applied with reason `handover: context`, the ex-leader receives `leadership_request`, and no member receives an unkeyed orchestrator note after the apply. Results go to agents-helmfile MEMORY.md. Standing rule (user): deploy whenever possible; live applies need no approval."

Steps, run by the orchestrator session (never a subagent: subagent `kubectl exec` is denied), in `code/agents-helmfile` on `main` after the helmfile PR merged, least destructive first:
1. Check the orchestrator image tag and chart version exist in Harbor.
2. `mise run diff -- --selector name=agents-orchestrator`: the change is the chart version, the image tag and `ORCH_ANY_MCP_PLUGINS_REF`; anything else stops the task.
3. `mise run apply -- --selector name=agents-orchestrator` (live; listed in design.md). The orchestrator applies the feed_cursor migration on start; agent pods of running sessions roll (config hash).
4. `mise run diff` shows no pending change; `mise run smoke` green, including steps 4a and 6a (task helmfile-smoke-activity).
5. Read-only checks: `session_leaders` has no `feed_cursor` column; live leaders report a non-null `context_pct` after the roll (F1 re-check).
6. Live proof: a throwaway 2-agent hive from the default preset with `auto_compact_pct: 20`; post one untargeted message (a short read-only task) so the leader's gauge is set; confirm a `note_received` event with key `handover_due` on the leader; post one more untargeted message so the leader acts on it; confirm a peer turn on the successor carrying the brief, a handover with `leader_reason` `handover: context`, and a `note_received` event with key `leadership_request` on the ex-leader; confirm no `note_received` event with a null key on either agent. Discard the session afterwards. A leader that does not follow the note within two user turns is a finding (a sharper note text becomes a new task), not a pass.
7. MEMORY.md entry containing the words `hive-decoupling live handoff`, dated, with the applied chart, image, plugins ref, the step 6 session id, request id and the event ids, and the F1 values.

Notes: never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25).

## Acceptance conditions

- ac1: (orchestrator session) the orchestrator image tag and chart version exist in Harbor before the apply [evidence: judgement:orchestrator records the registry check in the task Notes]
- ac2: after the apply helmfile reports no pending change [evidence: command:mise run diff]
- ac3: the smoke passes against the applied release, including the activity steps [evidence: command:mise run smoke]
- ac4: (orchestrator session) the live database has no session_leaders.feed_cursor column and live leaders report a non-null context_pct [evidence: judgement:orchestrator quotes the two read-only psql results in the task Notes]
- ac5: (orchestrator session) in the throwaway hive the leader received handover_due, briefed the successor over ccw, leadership moved with reason "handover: context" and the ex-leader received leadership_request [evidence: judgement:orchestrator quotes the session id, event ids, request id and leader_reason in the task Notes]
- ac6: (orchestrator session) no agent of the throwaway hive received an unkeyed note after the apply [evidence: judgement:orchestrator quotes the count of note_received events with a null key]
- ac7: MEMORY.md records the live handoff and the applied versions [evidence: command:grep -q "hive-decoupling live handoff" MEMORY.md]

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

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
