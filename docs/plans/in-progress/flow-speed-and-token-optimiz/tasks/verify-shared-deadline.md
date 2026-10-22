---
title: Verify shared deadline
status: done
repo: workbench
value: "A verifier never dies at the 600 s Bash cap: one deadline covers every command a verify call runs"
files: [plugins/workbench/scripts/verify-task.py, plugins/workbench/scripts/tests/test_verify_bounded.py, plugins/workbench/agents/verifier.md, plugins/workbench/workflows/plan-execute.js]
verify: "cd plugins/workbench && pytest scripts/tests/test_verify_bounded.py -q && ruff check scripts"
depends_on: [audit-context-and-models, review-tiering, triage-one-call, flow-docs-update, cache-probe, cache-prefix-change]
owns: []
uses: []
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/flow-speed-and-token-optimiz--verify-shared-deadline
branch: flow-speed-and-token-optimiz--verify-shared-deadline
verified_head: cc58bb40abfa3b3357b353a66a33926094e99848
run: flow-speed-and-token-optimiz
provides: []
acs_for_audit: []
process_gaps: []
estimate_by: formula
---

# Verify shared deadline

## Requirement

Epic review finding (2026-10-22): verify-task.py gives each command its own 480 s timeout (verify-task.py:49, :801-806, :863, :889, :921), but the design's builder check answer says `--timeout` is ONE shared deadline (default 540 s) across every command a single call runs, so two runs plus triage finish inside the verifier's 600 s Bash call.

Deliver: `--timeout` is one shared deadline, default 540 s, measured from the start of the call, across the main verify run, every AC ref run, the tdd-revert base run and triage. Each command runs with the time remaining; when the deadline is reached the running command's process group is killed, the result carries `timeout: {command, seconds}` and `passed: false`, and every step not yet run is skipped and listed in a `skipped` array in the JSON. The `--timeout` help text, agents/verifier.md and the plan-execute.js comment next to the 600000 ms Bash timeout describe the shared deadline.

## Acceptance conditions

- AC1: with --timeout 3, a main command sleeping 2 s and a tdd-revert base run sleeping 2 s, the call returns in under 4 s with timeout set and passed false [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_shared_deadline_spans_main_and_tdd_runs]
- AC2: steps not run before the deadline are listed in skipped [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_steps_after_deadline_are_skipped]
- AC3: the default deadline is 540 s and the help text calls it a shared deadline [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_default_shared_deadline_is_540]

## Files

- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/scripts/tests/test_verify_bounded.py`
- `plugins/workbench/agents/verifier.md`
- `plugins/workbench/workflows/plan-execute.js`

## Interfaces

- `verify-task.py --timeout <seconds>`: shared deadline, default 540.
- Result JSON: `timeout: {command, seconds}` (existing) plus `skipped: [step names]` (new, empty list when nothing was skipped).

## Expected outcome

One verify-task.py call never runs longer than its --timeout in total, so the verifier's 600 s Bash call always returns a JSON result.

## Steps

1. Write the three tests in test_verify_bounded.py and see them fail.
2. Replace per-command timeouts with a deadline computed once; pass the remaining seconds to each command.
3. Record skipped steps; update help text, verifier.md and the plan-execute.js comment.
4. Run the verify command.

## Ruling

- 2026-10-22 accepted: run 3: verify-shared-deadline, launch-land-verify, full-suite-split-shared and shell-quote-refs verified clean (landing on main via c2-land). medium-only-hold rejected for one fix round: transitive hold through a chain.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
