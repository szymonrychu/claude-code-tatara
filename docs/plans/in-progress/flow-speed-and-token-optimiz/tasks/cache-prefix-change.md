---
title: Cache prefix change
status: done
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
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/flow-speed-and-token-optimiz--cache-prefix-change
branch: flow-speed-and-token-optimiz--cache-prefix-change
verified_head: 0894fff7e69ea51fbcad51628ed425bb531f0465
run: flow-speed-and-token-optimiz
provides: []
acs_for_audit: [AC3]
process_gaps: ["TDD skipped without a listed exception; prove the tests catch the change - commit first, then for each changed non-test file: git show <merge-base>:<path> > <path>; run the test (must fail); git show HEAD:<path> > <path>; run again (must pass); paste both tails into tests.red and verification.evidence"]
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

- Uses `cache-probe-verdict` (cache-probe), as recorded by the orchestrator in design.md `## Cache probe result`.
- `implPrompt(t)` and `verifyPrompt(t, impl, prev)` in plan-execute.js keep their signatures.

## Expected outcome

The cache lever ships only when measured to save writes; otherwise the measurement and the no-op are on record and pinned.

## Steps

- Red: read the verdict; write `workflows/tests/plan-execute-prompt-prefix.test.mjs::prompt-order-follows-probe-verdict` for that verdict; run `cd plugins/workbench && node --test workflows/tests/plan-execute-prompt-prefix.test.mjs`; on `saving` expect a failure, on `none` it passes at once (the test pins existing behaviour; say so in `tests.note`).
- Green on `saving`: reorder both prompts. On `none`: no code change.
- Add the MEMORY.md entry; run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`; expect all green.

## Ruling

- 2026-10-22 accepted: run 2: cache-prefix-change (CACHE none, recorded no-op, pinning test) landed on main at e7533b8; TDD-skipped accepted: no behaviour change. Phase 5 remediation tasks follow.

## Notes

- The brief estimated -25% to -30% workflow cache-weighted tokens if 60% of each 17-28k prefix became a read; that estimate is the hypothesis the probe tests.
- Workflow agents start in the main conversation's cwd; the probe's `cwd` column confirms it, so no launch option changes.
- On `none` this task is a pinned no-op plus the record; that is the delivery D6 approves.
