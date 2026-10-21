---
title: Land in run
status: todo
repo: workbench
value: "Dependents build on the epic branch and every review diff shows only the task's own change"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-land.test.mjs, plugins/workbench/workflows/tests/plan-execute-verify.test.mjs, plugins/workbench/workflows/tests/plan-execute-rulings.test.mjs]
verify: "mise run test && mise run lint"
depends_on: [plan-execute-epic-names, merge-target-worktree, epic-base-wiring]
owns: [land-step]
uses: [merge-target-worktree, epic-run-args]
model: opus
estimate: 90
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Land in run

## Requirement

Land each task on the epic integration branch inside the plan-execute run, and start dependents from the updated epic branch (user decision U2, design D4, D9, D10; gate question Q1).

- New arg `mainCheckout` (absolute path, documented in the header). Landing is on exactly when `args.epic` and `args.mainCheckout` are both set and the run is not `auditOnly`; every other run behaves exactly as today.
- Land step: when a task becomes released (clean and verified, process-only, triage-rejected, or released by an accept ruling) and before any dependent counts it as released, the run dispatches one agent. It has label `<name>:land:<short>`, phase `Land`, agentType `workbench:worktree-merger`, model `sonnet` and a `LAND` schema `{landed, head, conflict, verification: {command, passed, evidence}, notes}`. Its prompt runs, from the main checkout by absolute path, `python3 <pluginRoot>/skills/worktree-merge/scripts/merge.py --name <epic>-<id> --base <baseRef> [--repo <repo>] --keep --no-suites --verify <task verify>`, with `--repo` only for a component tree `<...>/<repo>`. The agent relays the script output and never runs `git checkout` in the main checkout.
- Landings are serialised: at most one land agent runs at a time in a run.
- Success (`landed` true and `verification.passed` true): the task's verification head becomes the landed head, and the return carries `landed: [{id, head}]`.
- Failure: the task ends `clean: false` with reason `land-failed` (an escalation reason) and carries the land result; its dependents end `dependency-failed`.
- Tasks that escalate or are blocked never get a land agent.
- A task released mid-run by an accept ruling lands before its dependents start.
- `dependencyLines` in landing mode: same-repo dependencies give one line: first, before anything else, run `mergeCommand(t, <baseRef>)`, which merges the epic branch that carries every landed dependency, and list the dependencies it carries. Cross-repo dependencies keep the "lands with the integration" line.
- The verifier `--base` and the reviewer merge-base diff use `baseRef`; with `baseRef` `epic-x` both prompts name `epic-x`.
- Every role prompt of a task (implement, review, fix, verify, land) names that task's one worktree path; the land prompt also names the main checkout.
- Tests: new `plan-execute-land.test.mjs`, plus added cases in `plan-execute-verify.test.mjs` and `plan-execute-rulings.test.mjs`. Existing tests stay unchanged and green.

## Acceptance conditions

- AC1: a clean verified task in an epic run with mainCheckout gets one land agent running merge.py with the epic base, keep, no-suites and the task verify [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-dispatches-merge-into-epic]
- AC2: a dependent starts only after its dependency landed and merges the epic branch instead of the dependency branch [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-dependent-merges-epic-branch]
- AC3: two released tasks never land at the same time [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-serialised-one-at-a-time]
- AC4: a failed landing escalates the task as land-failed and fails its dependents [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-failure-escalates-and-fails-dependents]
- AC5: an escalated task gets no land agent [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-skips-escalated-tasks]
- AC6: a successful landing sets the verification head and the return lists it under landed [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-records-landed-head]
- AC7: runs without epic or without mainCheckout dispatch no land agent and keep dependency-branch merges [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-off-without-epic-or-main-checkout]
- AC8: every role prompt of a task names its one worktree [evidence: test:plugins/workbench/workflows/tests/plan-execute-land.test.mjs::land-every-role-shares-the-task-tree]
- AC9: the verifier and reviewer diff against the epic baseRef [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify.test.mjs::verify-and-review-use-epic-base-ref]
- AC10: a task released by an accept ruling lands before its dependents start [evidence: test:plugins/workbench/workflows/tests/plan-execute-rulings.test.mjs::ruled-task-lands-before-dependents]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-land.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-verify.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-rulings.test.mjs`

## Interfaces

- Uses `merge.py --verify` and target-tree landing (the `merge-target-worktree` part) and the run args `baseRef` and `mainCheckout` (the `epic-run-args` part).
- New in plan-execute.js: the `LAND` schema, the land step and its serialising queue (the `land-step` part, consumed by forward-merge-via-epic), the return field `landed`, the reason `land-failed` in `ESCALATE`.

## Expected outcome

In an epic run the integration branch advances task by task as each lands, dependents build on it, and every diff a reviewer or verifier reads is the task's own change against `<epic>`.

## Steps

- Red: write `plugins/workbench/workflows/tests/plan-execute-land.test.mjs` on the existing harness (`workflows/tests/harness.mjs`) and the two added cases; run `cd plugins/workbench && node --test workflows/tests/plan-execute-land.test.mjs`; expect failures.
- Green: add the land step in `runTasks` (between settle and release), the queue, the dependency line and the return field.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

## Notes

- Reuse `repoDir`, `mergeCommand`, `OWN_CHECKOUT_ONLY`, `verifyCommand`, `shq`, `safeAgent`; follow the forwardMerge pattern for replacing the verification head.
- A subagent's `cd` does not persist between Bash calls, so the land prompt is one `cd <mainCheckout> && python3 ...` command with absolute paths.
- The hooks treat the integration tree as an agent tree; if the merger resolves a conflict in the task tree it reruns the task verify there before re-running merge.py, or the commit guard fires once on the stale record.
- `model: opus` because this changes the run's scheduling core (release, rulings, escalation).
