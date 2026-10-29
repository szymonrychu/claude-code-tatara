---
title: orchestration live smoke
status: todo
repo: agents-helmfile
value: "the orchestration tools are live, proven from a flagged throwaway session, and mx-5 knows how to get them"
files: [MEMORY.md]
verify: "mise run lint && grep -q orchestration-smoke MEMORY.md"
depends_on: [helmfile-orchestration-pins, orchestration-smoke-script]
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

# orchestration live smoke

## Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Standing user rule (2026-10-27), verbatim from the lead: "Deploy whenever possible: live applies need no approval, so include the agents-helmfile values, apply and live smoke tasks in this epic."

Design D17, verbatim: "Every image tag and chart version is checked in Harbor before any apply (retro proposal). Apply order, `--selector` per release, `mise run diff` reviewed before each (`mise run apply` runs lint, test and check-pins first): agents-schedule (its migration 0002 runs in the init container; the relay listener comes up), agents-orchestrator (its migration 0013; the new plugins ref changes the rendered config hash, and the OnDelete rollout reconciler replaces each agent pod once it is idle, one per session, leaders last, mx-5 included: one line to mx-5 first), agents-web."

Design D19, verbatim: "After the deploy the orchestrator session sends mx-5 one line: flag mx-5's preset in the UI and recreate mx-5 to get the tools; it does not edit mx-5's preset or recreate mx-5 itself (recreating drops mx-5's context). The live smoke probes and records mx-5's preset name and whether the owner DM is bound to mx-5 (facts the repos do not hold)."

Open questions Q2 and Q8 (pending; the plan follows the recommended answers), verbatim: "Grant mx-5 by flagging its preset in the UI and recreating the session (spec stays immutable)?" recommended "yes"; "After the deploy you flag mx-5's preset in the UI and recreate mx-5 yourself (the orchestrator sends mx-5 one line and never edits mx-5's preset or recreates it, since that drops mx-5's context), and the epic closes on the throwaway-session live smoke without waiting for the grant?" recommended "yes".

Scope: run by the orchestrator session (live cluster, SOPS key); the only file written is agents-helmfile `MEMORY.md`.

## Acceptance conditions

- ac1: (orchestrator session) every new image tag and chart version (orchestrator, schedule, web) exists in Harbor before any apply [evidence: judgement:orchestrator records the registry check of each tag and chart version in the task Notes]
- ac2: (orchestrator session) after the applies in D17 order helmfile reports no pending change [evidence: command:mise run diff]
- ac3: (orchestrator session) the regular smoke passes on the new deployment [evidence: judgement:orchestrator quotes the final line of mise run smoke with exit 0 in the task Notes]
- ac4: (orchestrator session) mise run orchestration-smoke exits 0 and a GET of sessions, presets and schedules afterwards shows none of its objects [evidence: judgement:orchestrator quotes the step lines, the final OK line and the empty leftover check in the task Notes]
- ac5: (orchestrator session) mx-5's preset name and whether the owner DM is bound to mx-5 are probed live and recorded [evidence: judgement:orchestrator quotes GET /api/v1/sessions for mx-5 and the owner DM binding from the connector rooms API in the task Notes]
- ac6: (orchestrator session) mx-5 got one line before the orchestrator apply and one line after the smoke with the grant step of D19, and the epic does not wait for the grant [evidence: judgement:orchestrator quotes both message ids in the task Notes]
- ac7: agents-helmfile MEMORY.md records the live results, dated: the pins, the migrations applied, the orchestration-smoke result, mx-5's preset name and the owner DM binding [evidence: command:grep -q "orchestration-smoke" MEMORY.md]

## Files

- `MEMORY.md`

## Interfaces

- Live releases: agents-schedule, agents-orchestrator, agents-web in namespace agents.

## Expected outcome

The orchestration tools are live, proven by the smoke, and mx-5 knows how to get them.

## Steps

- Check every tag in Harbor (`crane digest` or `helm show chart`); stop and report a missing one.
- `mise run diff -- --selector name=agents-schedule`, review, `mise run apply -- --selector name=agents-schedule`; wait for the api and worker Ready (the init container ran the migration).
- Send mx-5 one line, then the same for agents-orchestrator; then agents-web.
- `mise run diff` (expect no change), `mise run smoke`, `mise run orchestration-smoke`; probe mx-5's preset and the owner DM binding; message mx-5 the grant line; write MEMORY.md.

## Notes

- helmfile MEMORY gotcha: a new or changed service Secret does not restart the orchestrator api pods; when the relay answers schedules_unconfigured or an upstream 401, run `kubectl rollout restart deploy/agents-orchestrator-api` (least destructive first), then rerun the smoke.
- Live and irreversible operations are listed in design.md (applies, both migrations, the relay token, the smoke objects). Standing rule: deploy whenever possible; live applies need no approval.
- Live apply and smoke tasks have run 3-4x over the minutes seed in past epics (retro); several runs are likely.
- Never edit mx-5's preset or recreate mx-5 (D19).

- 2026-10-29 amended: staleness refresh: D17 apply order cites check-pins, migrations 0002 and 0013 and the idle-only OnDelete rollout
