---
title: apply smoke webhook
status: done
repo: agents-helmfile
value: "the webhook service, its database, the orchestrator service port and the UI are live and proven by the smoke"
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [smoke-webhook-check, helmfile-service-token, helmfile-drop-source-secrets, deploy-pin-orch-service-port, helmfile-webhook-releases, helmfile-web-webhooks-entry]
model: sonnet
review: ""
verified_head: 3bfc1dc
points: 2
expected_minutes: 13
expected_tokens: 542616
points_actual: 2
actual_minutes: 27
actual_tokens: 453019
actual_roles: impl 27
actual_role_tokens: impl 453019
---

# apply smoke webhook

## Requirement

Apply to the live `agents` namespace and prove it (design D13; user decision: releases, pin bumps, CNPG database and helmfile apply plus smoke are tasks of this epic; live-deploy fact 2026-10-25: the orchestrator runs live applies itself, the classifier refuses them in subagents). Paths are in code/agents-helmfile.

- Implementer, before the apply: `mise run diff`; keep its output in the task notes. Expected: new releases `agents-webhook-db` and `agents-webhook`; agent-orchestrator chart version, image tag, the `-services` Service and `ORCH_SERVICE_TOKENS`; agents-web version, image tag and the webhooks backend. Anything else stops the task `blocked` with the diff, whoCanClear "user". Then end the implementer round with "ready for apply".
- Orchestrator (main session, never a subagent): `mise run apply` in code/agents-helmfile (lint, test and the kube-context guard run first; never bypass the guard or set EXPECTED_KUBE_CONTEXT); a failing apply is not retried blindly: read the helm error and report it with its tail.
- After the apply, implementer: `mise run diff` again (no drift) and `mise run smoke` (exit 0, including the webhook checks); `MEMORY.md`: a dated line: applied agents-webhook `0.1.0-main.<sha7>` with its CNPG database, orchestrator `0.1.0-main.<sha7>` with the service port and `reuse_running_agent`, agents-web `0.1.0-main.<sha7>` with Webhooks and the preset reuse switch; the public ingest URL prefix `https://lab.szymonrichert.pl/webhook/`; smoke green (quote its last log line).
- No other file changes.

## Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC2: the smoke passes, including the webhook checks [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied versions and the smoke result [evidence: command:grep -q "agents-webhook" MEMORY.md && grep -q "smoke" MEMORY.md]
- AC4: the pre-apply diff showed only the expected changes [evidence: judgement:the diff output quoted in the task notes]

## Files

- `MEMORY.md`

## Interfaces

- Consumes every release of this epic; writes only MEMORY.md.

## Expected outcome

The live namespace runs agents-webhook with its database, the orchestrator service port and the Webhooks UI, and the smoke is green.

## Steps

- `mise run diff`: only the expected changes; quote it in the notes.
- The orchestrator runs `mise run apply` in the main session.
- `mise run diff`: no drift; `mise run smoke`: exit 0; add the MEMORY.md line.

## Notes

- No TDD cycle applies: this task runs a deploy check and writes one MEMORY.md line (doc edit exception).
- The CNPG cluster creation and the public ingest path were approved at the gate (A7, A8); `mise run apply` never appears in AC evidence.

- 2026-10-25 in-progress: re-plan 2026-10-25: added; not started

- 2026-10-25 done
