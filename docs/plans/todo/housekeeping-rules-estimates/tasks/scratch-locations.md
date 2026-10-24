---
title: Scratch locations
status: todo
repo: workbench
value: ".scratchpad and .logs are the only scratch and log locations the tooling names, pinned by a test"
files: [plugins/workbench/skills/start-debugging/references/loops.md, plugins/workbench-observability/skills/kubectl-logs-query/SKILL.md, plugins/workbench/agents/planner.md, plugins/workbench/skills/start-development/tests/test_planner_agent.py, scripts/tests/test_scratch_and_log_dirs.py]
verify: "mise run test:scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-debugging && mise run test:pack-observability && mise run lint"
depends_on: [output-spill-to-logs, test-logs-dir, agent-discipline]
model: sonnet
review: ""
verified_head: ""
---

# Scratch locations

## Requirement

User requirement (U1, verbatim):

- all scratchpads edits land under `.scratchpad` in workbench root, use it as the only scratchpad dir
- all logs land in gitignored `.logs` in workbench root

Design D6: every skill, agent and script that names a scratch or log location names `<workbench root>/.scratchpad` or `<workbench root>/.logs`: start-debugging's `references/loops.md` pristine copy (`cp f /tmp/pristine-f`) moves to `.scratchpad`, kubectl-logs-query's "to the scratchpad" names `<workbench root>/.scratchpad`, and planner.md's "written under the scratchpad" names `<workbench root>/.scratchpad` (resolved with `workbench.py scratchpad`). A new tree-wide pin test `scripts/tests/test_scratch_and_log_dirs.py` scans the tracked non-test files of plugins/, scripts/ and mise-tasks/ (CHANGELOG excluded) and fails on `/tmp/`, `TMPDIR`, `mktemp` or a bare "the scratchpad" outside an explicit allowlist in the test, each entry with its reason: transient temp files created and removed within one run (suite-lock.sh lock dir, mise-tasks/lint/secrets staging, scripts/probes/claude-plugin-load.sh) and the no-main-checkout fallbacks in run-tests.sh, flake-hunt.sh and worktree_lib.py.

## Acceptance conditions

- AC1: no tracked non-test file names `/tmp/`, `TMPDIR`, `mktemp` or a bare "the scratchpad" outside the allowlist, and every allowlist entry carries a reason and still matches a real hit [evidence: test:scripts/tests/test_scratch_and_log_dirs.py::test_scratch_and_log_locations]
- AC2: planner.md names `.scratchpad` as where task bodies and input files are written [evidence: test:plugins/workbench/skills/start-development/tests/test_planner_agent.py::test_planner_rules]
- AC3: loops.md and kubectl-logs-query SKILL.md name `.scratchpad` [evidence: command:grep -n "\.scratchpad" plugins/workbench/skills/start-debugging/references/loops.md plugins/workbench-observability/skills/kubectl-logs-query/SKILL.md]
- AC4: root scripts, start-development, start-debugging and observability pack suites and lint pass [evidence: command:mise run test:scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-debugging && mise run test:pack-observability && mise run lint]

## Files

- `plugins/workbench/skills/start-debugging/references/loops.md`
- `plugins/workbench-observability/skills/kubectl-logs-query/SKILL.md`
- `plugins/workbench/agents/planner.md`
- `plugins/workbench/skills/start-development/tests/test_planner_agent.py`
- `scripts/tests/test_scratch_and_log_dirs.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
