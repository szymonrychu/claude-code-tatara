---
title: apply smoke init scripts
status: blocked
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
actual: 1
actual_roles: "impl 1, verify 1"
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-init-scripts-apply-smoke-init-scripts/agents-helmfile
branch: agent-init-scripts-apply-smoke-init-scripts
verified_head: f161544b29e6212610ab174496076d93f64fc477
run: agent-init-scripts
provides: []
acs_for_audit: [AC4]
process_gaps: []
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

- `mise run diff|apply|smoke` in code/agents-helmfile.

## Expected outcome

The live agents namespace runs the pinned build and the smoke, including the init scripts check, is green.

## Steps

- `mise run diff`: only the orchestrator chart version and image tag change (exit 2 means changes; quote the output).
- `mise run apply`: exits 0.
- `mise run diff`: exits 0.
- `mise run smoke`: exits 0; quote its last log line into MEMORY.md and the task notes.

## Ruling

- 2026-10-25 accepted: applied by the orchestrator after user allowed mise run apply: helm rev 11 chart 0.1.0-main.22cf283; post-apply diff 'No affected releases'; mise run smoke 'smoke: OK' incl init scripts succeeded; MEMORY via agents-helmfile PR #15 merged

## Notes

- No TDD cycle applies: this task runs an apply and writes one MEMORY.md line (doc edit exception).
- Never bypass the kube-context guard.

- 2026-10-25 run agent-init-scripts: dependency-failed on deploy-pin-init-scripts
