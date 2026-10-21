---
title: Fork point diffs
status: in-progress
repo: workbench
value: Reviews and verifies of a landed task still show exactly its own change
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs]
verify: "mise run test && mise run lint"
depends_on: [land-outcomes]
owns: [fork-point]
uses: [land-step]
model: sonnet
estimate: 60
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--fork-point-diffs
branch: epic-integration-worktrees--fork-point-diffs
verified_head: ""
run: ""
provides: []
---

# Fork point diffs

## Requirement

Take every diff of a task from its recorded fork point once it has landed. After landing, `merge-base(HEAD, <epic>)` is the task's own HEAD, so that diff is empty (interrogate verdict G; design D14).

- The `LAND` schema gains `base`: the `baseBefore` SHA that merge.py reports, which is the `<epic>` commit the task was rebased onto and fast-forwarded from. On a successful landing the run records it as the task's fork point. A contained landing keeps the fork point the task already had.
- New optional task arg `forkPoint` (a SHA, documented in the header) seeds the fork point for a task that landed in an earlier run.
- One helper `diffBase(t)` produces every diff base in a task's prompts: the fork point when one is recorded, else `$(git merge-base HEAD <baseRef>)` as today. It feeds:
  - the reviewer diff (plan-execute.js:933);
  - the verifier `--base` (:1016);
  - the TDD `git show <merge-base>:<path>` instruction (:1204);
  - remediation and audit re-review prompts;
  - the forward-merge re-verify.
- The return carries `landed: [{id, head, forkPoint}]` and `tasks[].forkPoint` whenever a fork point is set.
- Runs with no landing and no `forkPoint` args are unchanged; existing tests stay unchanged and green.
- Every new test title is a single kebab token.

## Acceptance conditions

- AC1: a landed task's remediation review diffs from its fork point, not the merge-base [evidence: test:plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs::fork-point-remediation-review-diffs-from-fork-point]
- AC2: the verifier base of a landed task is its fork point [evidence: test:plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs::fork-point-verifier-base-after-landing]
- AC3: a task with forkPoint in its args uses it in every role prompt [evidence: test:plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs::fork-point-arg-seeds-diff-base]
- AC4: the return lists the fork point of each landed task [evidence: test:plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs::fork-point-in-landed-return]
- AC5: without landing or a forkPoint arg the diff base stays the merge-base with baseRef [evidence: test:plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs::fork-point-absent-keeps-merge-base]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs`

## Interfaces

- `LAND` schema field `base` and task arg `forkPoint` (the `fork-point` part, consumed by fork-point-record and forward-merge-via-epic).
- New `diffBase(t)` in plan-execute.js; return fields `landed[].forkPoint` and `tasks[].forkPoint`.

## Expected outcome

After a task lands, every later diff of it (remediation, audit re-review, forward-merge re-verify) shows exactly its own change from the `<epic>` commit it forked or was last rebased from.

## Steps

- Red: write `plugins/workbench/workflows/tests/plan-execute-fork-point.test.mjs` with the five cases; run `cd plugins/workbench && node --test workflows/tests/plan-execute-fork-point.test.mjs`; expect failures.
- Green: add `base` to `LAND`, the fork-point state, `diffBase(t)` at every diff site, and the return fields.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

## Notes

- merge.py reports `baseBefore` (merge-target-worktree); the land agent relays it as `base`.
- `git merge-base HEAD <sha>` is `<sha>` when the fork point is an ancestor of HEAD, so passing the SHA as `--base` to the verifier needs no verifier change.
