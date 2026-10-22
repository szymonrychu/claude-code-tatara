---
title: Continue launch
status: done
repo: workbench
value: "One command between runs: apply, auto-accept, land the clean tasks, print the launch"
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py, plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py]
verify: "cd plugins/workbench && pytest skills/start-development/tests/test_ticket_continue_launch.py skills/start-development/tests/test_ticket_continue.py -q && ruff check skills"
depends_on: []
owns: [continue-launch-lines]
uses: [merge-target-worktree]
model: sonnet
estimate: 5
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/flow-speed-and-token-optimiz--continue-launch
branch: flow-speed-and-token-optimiz--continue-launch
verified_head: e5ec85e53c596b77938b213c41f305bbfa2b2520
run: flow-speed-and-token-optimiz
provides: [continue-launch-lines]
acs_for_audit: []
process_gaps: []
estimate_by: formula
---

# Continue launch

## Requirement

Make `ticket.py continue` a one-shot relaunch and auto-accept the findings that need no judgement (design D3, D8).

- Auto-accept: after the return is applied, every task the return marks `verified: true` and either `processOnly: true` with `stopped` other than `review-shallow`, or `triageRejected: true`, whose status is not `done`, is accepted exactly as `--accept` does, with reason `auto-accepted: processOnly` or `auto-accepted: triageRejected`, and printed `<task>: auto-accepted (<why>)`. Rerunning continue records nothing twice. An unverified task is never auto-accepted.
- `--launch`: for each task the merge gate would print a `MERGE` line for (every done task not yet contained in `<epic>`), run `merge.py --name <recorded tree name> --base <epic> [--repo <repo>] --keep --no-suites --verify '<task verify>'` from the main checkout as a subprocess (`skills/worktree-merge/scripts/merge.py`). Exit 0 is a landing. A non-zero exit keeps that task's `MERGE` line; when any line remains, continue prints them and exits 2 exactly as today, leaving both trees as merge.py left them.
- With nothing left to land, `--launch` finishes the existing steps (worktrees refresh, facts, args and named copy) and prints exactly two final lines: `LAUNCH <named copy script path> <args json path>` and `ARM python3 <plugin root>/skills/heartbeat/scripts/heartbeat.py --run <runId> --total <open task count>`.
- Without `--launch`, output and exit codes are unchanged apart from the auto-accept lines.
- Relaunch scope: the args continue writes never contain a done task; they hold every escalated, blocked, dependency-failed (reset to todo) and unstarted task.

## Acceptance conditions

- AC1: continue auto-accepts a verified processOnly task with a ruling and prints the line once across reruns [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_continue_auto_accepts_process_only]
- AC2: continue auto-accepts a verified triageRejected task and never an unverified or review-shallow one [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_continue_auto_accepts_triage_rejected_only_when_verified]
- AC3: --launch lands each clean done task through merge.py and prints no MERGE line for it [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_lands_clean_tasks_itself]
- AC4: a failed landing keeps its MERGE line, exits 2 and leaves the task tree and the epic branch intact [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_keeps_merge_line_on_failure]
- AC5: --launch ends with one LAUNCH line and one ARM line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_launch_prints_launch_and_arm_lines]
- AC6: the relaunch args hold no done task and every escalated, dependency-failed and unstarted one [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py::test_relaunch_args_hold_only_open_tasks]
- AC7: the existing continue tests still pass [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_ticket_continue.py -q]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_continue_launch.py`

## Interfaces

- Owns `continue-launch-lines`: the auto-accept lines and the `LAUNCH` and `ARM` lines, defined in `ticket_cmds/continue_cmd.py`.
- Uses `merge-target-worktree` (epic integration worktrees): merge.py's CLI `--name --base --repo --keep --no-suites --verify`, exit 0 merged, 1 error or conflict, 4 verify or suite failure.

## Expected outcome

After a run returns, one command applies it, accepts what needs no judgement, lands what is clean and prints the one Workflow launch and the one heartbeat arm; only a conflict or a red verify still needs a worktree-merger.

## Steps

- Red: write `skills/start-development/tests/test_ticket_continue_launch.py` with AC1-AC6 on the real-git fixtures of `ticket_repo_helpers.py` (an epic branch, task trees, a return JSON); run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_continue_launch.py -q`; expect failures.
- Green: auto-accept after `_apply`, the `--launch` flag, the merge.py subprocess per gate line, the two final lines.
- Run the task verify; expect all passed.

## Notes

- continue_cmd.py was changed by epic integration worktrees (epic-base-wiring, epic-close-command): the merge gate lists every done task not on `<epic>` and the base is the epic branch. Read the landed code first.
- The recorded tree name is the last path component of the task's `worktree` (strip a trailing `/<repo>` in component mode), the rule the land step uses.
- Use the existing `_rule` path for auto-accepts so rulings.json and the task body match manual accepts.
