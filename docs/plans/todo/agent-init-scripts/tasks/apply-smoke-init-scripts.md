---
title: apply smoke init scripts
status: todo
repo: agents-helmfile
value: init scripts are live in the agents namespace and proven by the smoke
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [deploy-pin-init-scripts, smoke-init-scripts]
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

# apply smoke init scripts

## Requirement

Apply the pinned release to the live `agents` namespace and prove it with the smoke (design D7; user-approved scope: releases, bumps and helmfile apply plus smoke are tasks of this epic). Paths are in code/agents-helmfile. Runs only after tasks deploy-pin-init-scripts and smoke-init-scripts are done.

- `mise run diff` first and keep its output in the task notes (expected change: the agent-orchestrator chart version and image tag only; anything else stops the task as `blocked` with the diff, whoCanClear "user").
- `mise run apply` (it runs lint, test and the kube-context guard first; never bypass the guard or set EXPECTED_KUBE_CONTEXT).
- `mise run diff` again: exit 0 (no drift).
- `mise run smoke`: exit 0, including the init scripts check.
- `MEMORY.md`: a dated 2026-10-24 line: applied agent-orchestrator `0.1.0-main.<sha7>` with init scripts, smoke green (quote the smoke's last log line).
- No other file changes. A failing apply is not retried blindly: read the helm error, report it with its tail.

## Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC2: the smoke passes against the live orchestrator, including the init scripts check [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied version and the smoke result [evidence: command:grep -q "0.1.0-main" MEMORY.md && grep -q "init scripts" MEMORY.md]
- AC4: the pre-apply diff showed only the orchestrator chart version and image tag changing [evidence: judgement:the diff output quoted in the task notes]

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
