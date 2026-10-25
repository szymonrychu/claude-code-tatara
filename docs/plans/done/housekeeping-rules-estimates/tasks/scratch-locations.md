---
title: Scratch locations
status: done
repo: workbench
value: ".scratchpad and .logs are the only scratch and log locations the tooling names, pinned by a test"
files: [plugins/workbench/skills/start-debugging/references/loops.md, plugins/workbench-observability/skills/kubectl-logs-query/SKILL.md, plugins/workbench/agents/planner.md, plugins/workbench/skills/start-development/tests/test_planner_agent.py, scripts/tests/test_scratch_and_log_dirs.py]
verify: "mise run test:scripts && bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only start-debugging && mise run test:pack-observability && mise run lint"
depends_on: [output-spill-to-logs, test-logs-dir, agent-discipline]
model: sonnet
review: ""
verified_head: fd6600a
points_actual: 3
actual_minutes: 45
actual_tokens: 723362
actual_roles: "impl 39, review 6"
actual_role_tokens: "impl 590769, review 132593"
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

- `scripts/tests/test_scratch_and_log_dirs.py`: an `ALLOW` mapping of path to reason; the scan uses `git ls-files` (reuse `scripts/check_personal.py:_tracked`/`_text`).

## Expected outcome

The only scratch and log locations named anywhere in the tracked tooling are `.scratchpad` and `.logs` of the workbench root, and a test keeps it that way.

## Steps

1. List the files under Files, read them in one pass; write the pin test and the planner assertion; run `pytest scripts/tests/test_scratch_and_log_dirs.py -q`: it fails on loops.md, kubectl-logs-query and planner.md.
2. Amend the three texts; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 3 points.
- Fix-as-ac (brief): planner.md:67 says "the scratchpad" generically and test_planner_agent.py:74 pins the word "scratchpad"; keep the word, add the location.
- Depends on output-spill-to-logs and test-logs-dir so their fallbacks exist before the allowlist pins them.
- Exclude tests directories (they legitimately use tmp_path and TMPDIR) and CHANGELOG files.

- 2026-10-25 done

- 2026-10-25 done
