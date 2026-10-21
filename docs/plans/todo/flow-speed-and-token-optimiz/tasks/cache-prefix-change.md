---
title: Cache prefix change
status: todo
repo: workbench
value: "The cache lever ships only when measured to save; otherwise the no-op is on record"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-prompt-prefix.test.mjs, MEMORY.md]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only workflows"
depends_on: [cache-probe, audit-context-and-models]
owns: []
uses: [cache-probe-verdict]
model: sonnet
estimate: 5
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Cache prefix change

## Requirement

Apply or decline the prompt-cache change according to the recorded probe (design D6).

- Precondition: design.md (the run's `designDoc`) has a `## Cache probe result` section with the probe JSON and a verdict line. If it is absent, return `blocked` with reason `cache probe not run` and whoCanClear `orchestrator: run hook-probe.js with args.probe cache, then hook-evidence.py --cache, and record the result in design.md`.
- Verdict `CACHE saving`: reorder `implPrompt` and `verifyPrompt` static-first like `reviewPrompt`: every block identical across tasks first, then a task marker line, then the task-specific lines (worktree, repo, task id, requirement, files, notes, ACs, dependencies). The test pins that the prompts of two different tasks are byte-identical up to the marker and that no line before it names a task.
- Verdict `CACHE none`: change no prompt. The test pins the current order (implPrompt's first line is the worktree line), so a later reorder is a deliberate decision.
- Either way, root `MEMORY.md` gets a dated entry headed `prompt-cache probe` with the measured creation and read numbers per agent, the verdict and the decision taken.

## Acceptance conditions

- AC1: MEMORY.md records the probe numbers, the verdict and the decision [evidence: command:grep -q 'prompt-cache probe' MEMORY.md]
- AC2: a test pins the prompt order the verdict chose [evidence: test:plugins/workbench/workflows/tests/plan-execute-prompt-prefix.test.mjs::prompt-order-follows-probe-verdict]
- AC3: the prompt change, or its absence, matches the recorded verdict [evidence: judgement:]
- AC4: the workflows suite is green [evidence: command:cd plugins/workbench && bash scripts/run-tests.sh --only workflows]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-prompt-prefix.test.mjs`
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
