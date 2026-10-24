---
title: Output spill to logs
status: done
repo: workbench
value: Capped command output lands in the gitignored .logs of the workbench root
files: [plugins/workbench/hooks/worktree_lib.py, plugins/workbench/hooks/bash-output-filter.py, plugins/workbench/hooks/tests/test_bash_output_filter.py, plugins/workbench/hooks/tests/test_output_filter_unwrap.py, plugins/workbench/skills/start-development/references/hooks.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [workbench-dirs, em-dash-commit-guard]
model: sonnet
review: ""
verified_head: 303f638
---

# Output spill to logs

## Requirement

User requirement (U1, verbatim): "all logs land in gitignored `.logs` in workbench root".

Design D6: the bash-output-filter spill file (the full output of a capped command, whose path the agent is told to read) is a log, so it lands in `<main checkout>/.logs/bash-output/` instead of `$TMPDIR`. `worktree_lib.wrap_output_filter` builds the wrapper with the spill directory resolved at hook time through `workbench.logs_dir` (cwd of the hook event), falling back to `${TMPDIR:-/tmp}` only when no main checkout is found; `unwrap_output_filter` recognises the wrapper for any spill directory, so verify-recorder and the commit guard still see the original command. Small outputs still delete their spill file. The docstrings and references/hooks.md name the new location.

## Acceptance conditions

- AC1: a capped command's full output is spilled under `<main checkout>/.logs/bash-output/` and the printed path points there [evidence: test:plugins/workbench/hooks/tests/test_bash_output_filter.py::test_spill_lands_in_logs_dir]
- AC2: with no main checkout (cwd outside git, no env) the spill falls back to TMPDIR [evidence: test:plugins/workbench/hooks/tests/test_bash_output_filter.py::test_spill_falls_back_to_tmpdir]
- AC3: a small output leaves no spill file behind [evidence: test:plugins/workbench/hooks/tests/test_bash_output_filter.py::test_small_output_spill_file_is_removed]
- AC4: `unwrap_output_filter(wrap_output_filter(cmd, n))` returns `cmd` for a logs-dir wrapper and a TMPDIR wrapper, and a non-wrapper is returned unchanged [evidence: test:plugins/workbench/hooks/tests/test_output_filter_unwrap.py::test_unwrap_any_spill_dir]
- AC5: hooks and start-development suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/hooks/worktree_lib.py`
- `plugins/workbench/hooks/bash-output-filter.py`
- `plugins/workbench/hooks/tests/test_bash_output_filter.py`
- `plugins/workbench/hooks/tests/test_output_filter_unwrap.py`
- `plugins/workbench/skills/start-development/references/hooks.md`

## Interfaces

- `hooks/worktree_lib.py:wrap_output_filter(command: str, cap_chars: int, spill_dir: str | None = None) -> str` (or an equivalent that takes the directory), `unwrap_output_filter(command: str) -> str` unchanged in signature.
- `workbench.logs_dir(start)` from workbench-dirs.

## Expected outcome

Every spilled command output an agent is pointed to sits in the gitignored `.logs/bash-output/` of the main checkout.

## Steps

1. List the files under Files, read them in one pass; update the spill tests (they set TMPDIR today) and add AC1, AC2, AC4; run `pytest hooks/tests/test_bash_output_filter.py hooks/tests/test_output_filter_unwrap.py -q` from plugins/workbench: they fail.
2. Implement; update the docstrings and hooks.md; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 3 points.
- WRAP_HEAD is a constant today (worktree_lib.py:36) and unwrap matches it literally; make the head a pattern with the directory as the only variable part, keeping "the hook that writes it and the code that unwraps it cannot drift apart".
- Quote the directory safely in the shell snippet (paths with spaces).
- Tests must clear WORKBENCH_ROOT and CLAUDE_PROJECT_DIR, or set them to a temp main checkout.

- 2026-10-25 done
