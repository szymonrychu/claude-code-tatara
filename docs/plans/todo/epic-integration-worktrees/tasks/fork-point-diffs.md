---
title: Fork point diffs
status: todo
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
worktree: ""
branch: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
