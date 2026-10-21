---
title: Verify scope wiring
status: todo
repo: workbench
value: "Every verify runs targeted tests, at most two suites contend per repo, long chains start first"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs, plugins/workbench/workflows/tests/plan-execute-verify.test.mjs]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only workflows"
depends_on: [verify-task-bounded-runs]
owns: []
uses: [verify-task-cli, land-step]
model: opus
estimate: 5
actual: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Verify scope wiring

## Requirement

Wire plan-execute to the bounded verifier and schedule verifies (design D1, D12). `plugins/workbench/workflows/plan-execute.js`.

- `verifyCommand(t)` is `t.verify` and never `impl.verification.command`. With no `t.verify` the verifier prompt passes `--targeted` and no `--cmd`. The forward-merge prompt's verify step follows the same rule (with no `t.verify` it runs the verifier's verify-task `--targeted` invocation).
- `--prev-head` is passed only when the previous head matches `/^[0-9a-f]{7,40}$/`, quoted with `shq`; otherwise it is omitted.
- verifyPrompt tells the agent to run the command in ONE Bash call with `timeout: 600000`.
- At most 2 verifier agents run at once per repo: `independentVerify` waits on a per-repo FIFO queue and the next queued verify starts the moment one ends. Other roles are not limited. A queued verify always starts eventually (no deadlock when tasks of one repo wait on each other).
- When several tasks become ready in the same pump, they begin in descending order of their count of transitive dependents, ties in input order (plan-execute reads no estimate).
- The land step keeps `--no-suites --verify <task verify>`: the full suite runs once at epic close (blocker D5), never per task. A test pins the land command.
- Existing tests that expected the implementer-command fallback are updated.

## Acceptance conditions

- AC1: the verifier never runs the implementer's own command [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::verify-never-uses-implementer-command]
- AC2: a task without verify gets --targeted and no --cmd [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::verify-without-task-verify-passes-targeted]
- AC3: --prev-head is passed only as a quoted sha [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::prev-head-passed-only-as-quoted-sha]
- AC4: the verifier prompt sets the 600000 ms Bash timeout [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::verify-prompt-sets-bash-timeout]
- AC5: at most two verifiers run at once per repo and every queued one starts [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::at-most-two-verifies-per-repo]
- AC6: ready tasks start in descending order of transitive dependents [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::ready-tasks-start-in-critical-path-order]
- AC7: the land command keeps the task verify and --no-suites [evidence: test:plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs::land-command-keeps-task-verify-and-no-suites]
- AC8: the workflows suite is green [evidence: command:cd plugins/workbench && bash scripts/run-tests.sh --only workflows]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-verify-scope.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-verify.test.mjs`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
