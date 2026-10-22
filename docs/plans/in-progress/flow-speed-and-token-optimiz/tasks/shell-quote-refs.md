---
title: Shell quote refs
status: todo
repo: workbench
value: No ref or path from args or an earlier run reaches a verifier shell command unquoted
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-shell-quoting.test.mjs]
verify: "cd plugins/workbench && node --test workflows/tests/plan-execute-shell-quoting.test.mjs && bash scripts/run-tests.sh --only workflows"
depends_on: [verify-shared-deadline]
owns: []
uses: []
model: sonnet
estimate: ""
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Shell quote refs

## Requirement

Security review finding (2026-10-22, MEDIUM and LOW): plan-execute.js builds verifier shell commands with values that are neither quoted nor validated: `diffBase(t)` returns `forkPointOf(t) || BASE_REF` and is embedded raw as `--base ${diffBase(t, true)}` (plan-execute.js:127, verifyTaskCommand :1119, forward-merge :2607); `forkPoint` comes from ARGS.tasks[].forkPoint (fed from an earlier run's landed return) and BASE_REF from ARGS.baseRef. repoDir (:845-848) embeds t.worktree and t.repo inside double quotes, where `$` and backticks expand.

Deliver: a forkPoint that does not match SHA_RE is ignored (the base ref is used and the run logs `forkPoint ignored: not a sha`); every diffBase value placed in a shell command goes through shq; repoDir quotes the worktree and repo with shq instead of double quotes. Existing prompt text otherwise unchanged.

## Acceptance conditions

- AC1: a task whose forkPoint is `abc; touch pwned` gets a verify command that uses the quoted base ref and contains no `touch pwned` [evidence: test:plugins/workbench/workflows/tests/plan-execute-shell-quoting.test.mjs]
- AC2: a baseRef containing a space and `$(x)` appears single-quoted in the verify and forward-merge commands [evidence: test:plugins/workbench/workflows/tests/plan-execute-shell-quoting.test.mjs]
- AC3: repoDir output single-quotes a worktree path containing `$HOME` and a backtick [evidence: test:plugins/workbench/workflows/tests/plan-execute-shell-quoting.test.mjs]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-shell-quoting.test.mjs`

## Interfaces

- `shq` and `SHA_RE` in plan-execute.js are reused, not redefined.
- `diffBase(t, quoted)` keeps its call sites; quoting happens where the value enters a shell string.

## Expected outcome

Hostile or malformed refs and paths in args or run data cannot execute in a verifier's shell.

## Steps

1. Write plan-execute-shell-quoting.test.mjs and see it fail.
2. Validate forkPoint with SHA_RE; shq the base in the three command builders; shq in repoDir.
3. Run the verify command.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
