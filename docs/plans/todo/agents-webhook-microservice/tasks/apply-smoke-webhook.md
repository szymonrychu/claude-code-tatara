---
title: apply smoke webhook
status: todo
repo: agents-helmfile
value: "the webhook service, its database, the orchestrator service port and the Webhooks UI are live and proven by the smoke"
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [smoke-webhook-check, helmfile-service-token, deploy-pin-orch-service-port, helmfile-webhook-releases, helmfile-web-webhooks-entry]
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

# apply smoke webhook

## Requirement

Apply to the live `agents` namespace and prove it (design D13; user decision: releases, pin bumps, CNPG database and helmfile apply plus smoke are tasks of this epic). Paths are in code/agents-helmfile.

- `mise run diff` first; keep its output in the task notes. Expected: new releases `agents-webhook-db` and `agents-webhook`; agent-orchestrator chart version, image tag, the `-services` Service and `ORCH_SERVICE_TOKENS`; agents-web version, image tag and the webhooks backend. Anything else stops the task `blocked` with the diff, whoCanClear "user".
- `mise run apply` (lint, test and the kube-context guard run first; never bypass the guard or set EXPECTED_KUBE_CONTEXT).
- `mise run diff` again: no drift.
- `mise run smoke`: exit 0, including the webhook checks.
- `MEMORY.md`: a dated line: applied agents-webhook `0.1.0-main.<sha7>` with its CNPG database, orchestrator `0.1.0-main.<sha7>` with the service port, agents-web `0.1.0-main.<sha7>` with Webhooks; the public ingest URLs; smoke green (quote its last log line).
- No other file changes. A failing apply is not retried blindly: read the helm error and report it with its tail.

## Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC2: the smoke passes, including the webhook checks [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied versions and the smoke result [evidence: command:grep -q "agents-webhook" MEMORY.md && grep -q "smoke" MEMORY.md]
- AC4: the pre-apply diff showed only the expected changes [evidence: judgement:the diff output quoted in the task notes]

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
