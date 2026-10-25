---
title: apply smoke orch no spa
status: in-progress
repo: agents-helmfile
value: "the live orchestrator is API-only and the UI keeps working, proven by the smoke"
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [deploy-pin-orch-no-spa]
model: ""
review: ""
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

# apply smoke orch no spa

## Requirement

Apply the orchestrator without the UI to the live `agents` namespace and prove it (design D8; user-approved: releases, pin bumps and the helmfile apply plus smoke are tasks of this epic). Paths are in code/agents-helmfile.

- `mise run diff` first, quoted in the notes. Expected: only the agent-orchestrator chart version and image tag (and what the chart renders from them); anything else stops the task `blocked` with the diff, whoCanClear "user".
- `mise run apply` (lint, test and kube-context guard; never bypass it).
- `mise run diff` again: exit 0.
- `mise run smoke`: exit 0.
- Live checks, quoted in the notes: through `kubectl -n agents port-forward deploy/agent-orchestrator-api 18001:8000`, `GET /` answers 404 with a JSON body and `GET /api/v1/openapi.json` 200; `https://lab.szymonrichert.pl/` still redirects to Keycloak.
- `MEMORY.md`: a dated line: applied agent-orchestrator `0.1.0-main.<sha7>` without the UI, smoke green (quote the smoke's last line).

## Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile [evidence: command:mise run diff]
- AC2: the smoke passes against the API-only orchestrator and the agents-web UI [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied orchestrator release without the UI [evidence: command:grep -q "without the UI" MEMORY.md]
- AC4: the pre-apply diff showed only the orchestrator chart version and image tag, and the api answers / with a JSON 404 [evidence: judgement:the diff and curl output quoted in the task notes]

## Files

- `MEMORY.md`

## Interfaces

- `mise run diff|apply|smoke` in code/agents-helmfile.

## Expected outcome

The live orchestrator is API-only and the UI keeps working from agents-web.

## Steps

- `mise run diff`: quote it.
- `mise run apply`: exit 0.
- `mise run diff`: exit 0.
- `mise run smoke`: exit 0; quote the last line into MEMORY.md and the notes.
- The port-forward checks.

## Notes

- No TDD cycle applies: an apply and one MEMORY.md line (doc edit exception).
