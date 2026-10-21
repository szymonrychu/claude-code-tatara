---
name: plan-execute
description: Run an approved epic task by task with your own subagents - worktree per task, test-first implementation, committed-HEAD verification, review, bounded fix rounds, one scope audit - driving ticket.py and the approvals ledger. Use in harnesses without the Claude Code workflow runtime.
---

# plan-execute (fallback, no workflow runtime)

The Claude Code workflow `workbench:plan-execute` runs this loop as a script. This harness has
no workflow runtime, so you run the same phases yourself, spawning subagents where your harness
supports them and working sequentially where it does not. All state lives in the epic's ticket
files, read and written through `ticket.py`, and in one return file you write by hand.

`ticket.py` below is `${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py`, run with
`python3` from the main checkout. Input: an approved epic in `docs/plans/in-progress/<epic>/`
(README.md, design.md, `tasks/<task>.md`, `approvals.json`), claimed with
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py move <epic> in-progress`.
The claim creates the epic integration worktree and branch `<epic>`; task trees are
`<epic>-<task>` and land on `<epic>`, never on main. Use plain `git worktree` through
`ticket.py` and `merge.py`, never the harness's built-in worktree feature. An epic claimed
before this change (legacy `<epic>--<task>` trees, no `<epic>` branch) runs
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py worktrees <epic> --integration`
first; a recorded legacy tree is still accepted.

## Start of a run

1. **Tasks.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py tasks <epic> --out <scratchpad dir>/<epic>-tasks.json`
   writes every task with its id (the task slug), requirement, files, verify command, owns,
   uses, dependsOn and worktree. A task whose file says `status: done` is finished: skip it.
2. **Approvals ledger.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py path <epic> approvals`
   prints the path of `approvals.json`: one entry per item the user approved, each with `id`,
   `text` and the `tasks` that deliver it. Every implementer and fixer of a mapped task gets
   the item's id and text in its prompt; where an item spans several tasks, each prompt names
   the other tasks that deliver the rest.
3. **Worktrees.** `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py worktrees <epic>`
   forks one git worktree and branch `<epic>-<task>` per open task from `<epic>` and records
   the path in the task file.
4. **Return file.** Create `<scratchpad dir>/<epic>-return.json` (schema below) with an empty
   `tasks` list. It is this run's only state outside the ticket files: update it after every
   phase of every task.

## Phases, per task (respect task dependencies; independent tasks may run in parallel)

1. **Worktree.** Merge `<epic>` (which already carries the finished dependencies) into the task worktree first, not the dependency branches. Work only inside
   that worktree by absolute path.
2. **Implement test-first.** A subagent (or you) writes the failing test, runs it and sees it
   fail for the right reason, then implements until it passes, then cleans up. Commit on the
   task branch. No TODOs standing in for work; the whole requirement is delivered, and an
   approved item mapped to the task is never left undelivered.
3. **Verify.** On the committed HEAD of the task branch run
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify-task.py` (plus the task's targeted verify
   command). Read the real output; never report a pass you did not observe. A dirty tree or a
   failing run sends the task back to implement. Record the HEAD it ran on as
   `verification.head`.
4. **Review.** A separate reviewer subagent reads the diff against the requirement and the
   approved items mapped to the task, and returns findings. Judge each: fix the real ones, drop
   the wrong ones with a stated reason.
5. **Fix rounds.** At most three fix rounds (fix, re-verify, re-review). The third round is
   the cap; the return file records a capped task with reason `round-cap` (schema below).
6. **Merge.** From the main checkout land the green task branch on the epic branch:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/worktree-merge/scripts/merge.py --name <epic>-<task> --base <epic> --keep --verify '<verify>'`,
   resolving conflicts so both sides' intent survives.
7. **Record.** Update the task's entry in the return file, then apply it:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py apply-run <epic> <scratchpad dir>/<epic>-return.json`.
   It writes status, branch and verified head into each task file and commits its own
   `docs/plans/` change. It is safe to re-run on the same file.

## The return file

The same schema the workflow returns, so `apply-run` and `continue` read it unchanged:

```json
{
  "run": "<epic>-fallback-1",
  "finished": false,
  "tasks": [
    {
      "id": "<task slug>",
      "branch": "<task branch>",
      "verified": true,
      "clean": true,
      "stopped": null,
      "processOnly": false,
      "verification": {"head": "<sha verify-task.py passed on>"},
      "acsForAudit": [],
      "processGaps": []
    }
  ],
  "approvals": [{"id": "A", "status": "delivered"}],
  "escalated": [],
  "blocked": [],
  "discovered": [
    {"taskId": "<task slug>", "what": "<gap outside the task>", "where": "<file>", "why": "<reason>"}
  ],
  "provides": []
}
```

- A task is `done` when `verified` and `clean` are true and `stopped` is null; with no verified
  head it stays `in-progress`.
- `escalated`: `{"id", "reason", "findings"}` per stopped task (`round-cap`, `no-progress`,
  `dependency-failed` with `waitingOn`); `blocked`: `{"id", "reason", "whoCanClear",
  "approvals"}` for an external blocker no agent can clear.
- `approvals`: one status per ledger entry, worst first - `blocked` when a mapped task is
  blocked, `escalated` when one escalated, `unverified` when one has no verified head, else
  `delivered`. `finished` is true only when every entry is `delivered`.
- `discovered`: gaps a task found outside its own files; `provides`: `{"taskId", "name",
  "where"}` for unplanned shared parts.
- Every task id must have a file in `tasks/`; `apply-run` rejects any other id.

## Once, over the whole run

8. **Scope audit.** After every task is merged, one scope audit over the whole run: compare the
   plan's requirements and every `approvals.json` entry against the integrated diff, as
   `{id, landed, evidence}` per item, and list anything undelivered or built twice. Fix gaps, or
   escalate genuine blockers; set each `approvals[].status` from the result and apply the
   return once more.
9. Run the full test suite and lint once on the integrated branch before declaring done.
10. **Continue.** While the epic has open tasks (an escalation you judged, a discovered task):
    `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py continue <epic> --out-dir <scratchpad dir> --return <scratchpad dir>/<epic>-return.json [--accept <ids> --reason ...]`
    applies the return, records your rulings, refreshes the worktrees and writes
    `<scratchpad dir>/<epic>-args.json` with the open tasks and the ledger entries they still
    deliver. When it prints `MERGE <task>` lines and exits 2, merge those tasks and run it
    again. Its last lines name a script for the Claude workflow runtime (and it exits non-zero
    when `node` is missing, after the args JSON is written); ignore them and start the next
    pass from the args JSON with a fresh return file and a new `run` name.

## Close

Close order for the epic, once every task is done:

1. Every done task is landed on `<epic>`: `ticket.py continue` prints no `MERGE` line.
2. In meta mode run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py close <epic> --verify '<full suite and lint>'`.
   It rebases `<epic>` onto main in the integration tree, runs the full suite and lint on the
   rebased tip, fast-forwards main only when green, runs the full suite on main, and records
   main's pre-fast-forward SHA in the close summary. Main never moves onto an untested tip.
3. Then `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py move <epic> done`,
   which checks that the epic reached main and removes every tree and branch.

## Waits and questions

- Every wait is bounded: state its maximum (10 minutes unless a tool sets a shorter one), then
  re-check and report what resolved and what did not.
- A question for the user is a numbered prose question with its options and a recommended
  answer. Only an irreversible operation the gate did not list stops the run.

## What you lose against the Claude workflow

- **Script-held state.** The workflow keeps round counters and results in code. Here they live
  in your context and the return file: write the file after each phase and apply it after
  each task, so the task files always show where the run is.
- **Resume.** The workflow can resume an interrupted run from its saved state. Here you resume
  by re-running `ticket.py tasks <epic>` (task files carry status, branch and verified head),
  re-reading the return file and checking the git branches.
- **Fan-out caps.** The workflow caps parallel agents and pins models per role. Here you set
  concurrency and models yourself; keep parallelism small and use cheaper models for mechanical
  work.
