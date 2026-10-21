# Phase 4: execute

Detail for phase 4 of `SKILL.md`: grouping, the Workflow args block, review tiers and gates.

## Phase 4 - Execute

**Per epic.** `epic-move` (`ticket.py move <epic> in-progress`) claims it, and `move in-progress` creates
the integration tree and branch `<epic>` (no hand-run `git-worktrees-create`). Component mode: the MR comes
off the integration branch. Meta mode: tasks land on `<epic>` and the epic closes into the local main
(`references/phases-5-7.md`). An epic claimed before this change gets its integration tree from
`ticket.py worktrees <epic> --integration`, and its live legacy double-hyphen trees keep running.

**Group the plan into execution units before creating any worktree**: disjoint file sets, a
`dependsOn` where a unit builds on another's code, all in ONE workflow run. Concatenate requirement
text verbatim when merging items; grouping may never drop an acceptance condition. Then `ticket.py
worktrees <epic>` calls `worktree-create` once per open task (a `<epic>-<task>` branch forked from
`<epic>`) and records each path in the task file, so it reaches the run through `ticket.py tasks`. Naming,
`--assess` sizing of the `worktree-merger` and the sub-subagent rules are in
`references/worktrees.md`. Never merge a worktree yourself. Sub-subagents do not get worktrees.
Nesting is allowed where it delivers faster at the same quality.

Then run the epic through `workbench:plan-execute`, never by hand-dispatched implementers: one run per
epic, named by the epic slug through a named copy (`meta.name` must be a literal):

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py tasks <epic> --out <scratchpad dir>/<epic>-tasks.json
# ticket.py args <epic> --out-dir <scratchpad dir> builds the args JSON and the named copy (prints its path);
# by hand: node ${CLAUDE_PLUGIN_ROOT}/workflows/named-copy.mjs plan-execute <epic> <scratchpad dir> --args <args.json>

Workflow({
  scriptPath: '<the printed path>',   // resume with the same scriptPath
  args: {
    epic: '<epic>',   // args.epic; task ids are task slugs
    name: '<epic>',   // must equal args.epic; labels become <epic>:<role>:<task slug>
    brief: { what: '...', how: '...', why: '...' },   // the plan's Project brief
    tasks: [ { id, title, repo, worktree, requirement, value, files, notes, verify,
               owns, uses, dependsOn, size, sizeReason }, ... ],
    approvals: [ { id, text, tasks }, ... ],   // the ledger entries this run delivers
    planText: '<THIS run\'s scope - see below>',
    contextPack: '<path to the phase 1 brief>',
    designDoc: '<ticket.py path <epic> design>',
    planDoc: '<ticket.py path <epic> readme>',   // the epic README
    existing: [ { name, where }, ... ],   // Plan inputs `reuse`, as name + file:symbol
    doNotBuild: [ { name, reason }, ... ], // Plan inputs `do-not-build`, as item + what provides it
    lenses: ['correctness', 'requirements-coverage'],
    baseRef: '<epic>',   // the epic branch task branches forked from; the verifier diffs against it
    mainCheckout: '<main checkout path>',   // the run lands each released task on the epic branch from here
    verifierAgent: 'workbench:verifier',   // null runs the verifier as a plain prompt role
  },
})
```

Landing happens in the run: each released task is merged onto `<epic>`, and `land-failed` is an
escalation reason. Your ruling on an escalated task lands it through `continue`'s `MERGE ... --base <epic>`
lines, which you hand to a `worktree-merger`.

On return, `ticket.py apply-run <epic> <return.json>` writes results back into the task files;
discovered work becomes new tasks in the same epic.

To wait on the run, arm `heartbeat.py --run <id>` (one Monitor; keepalive off by default; costs in
skills/heartbeat/SKILL.md); on END read the return per references/run-handback.md.
**Relaunch:** `ticket.py continue <epic> --out-dir <dir> --accept <ids>` applies the return, records
rulings and rebuilds the args; `ticket.py rule <epic> --accept|--reject <ids> --reason ...` accepts
mid-run; `ticket.py reap --epic <epic> --task <id>` after a task merges; `ticket.py amend` for a
mid-epic scope change; `ticket.py facts` after merges. Parallel epics: `references/multi-epic.md`. Read `approvals`,
`escalated`, `blocked`, `waveLevel`, `duplicates`, `provides`, `processGaps`, `declined`,
`cannotVerify` and `forwardMerged` first.

After each implementer and fixer an **independent verifier** (`agents/verifier.md`, `haiku`,
`maxTurns`-capped) runs `scripts/verify-task.py` on the committed HEAD (clean tree, `verify` exit,
debt, parking, ACs, tier hint, TDD revert): that is the `verification` (`verification.head`), never
`selfVerification`. Review and fix loop to clean and verified, then ONE scope audit, a remediation
per gapped task, and a **forward-merge** of each fix into finished dependents before re-audit.
- **Gate findings** carry a `gate` tag: `ac-unmet` (undecided: the audit), `No red evidence`
  (no `tests.red`), `TDD skipped` (`wroteTestFirst: false`), `Tests changed in a fix round`.
- **Tiers** `skip`, `light`, `full`, `panel`: explicit `review` wins, risky paths at least `full`,
  small, finding-free, evidenced is `skip`, else `light`; a verifier hint only raises it. `light`
  reviews once, `full` loops, `panel` adds `interrogate`. Sonnet reviewers read one `git diff`
  (`diffRead`), else rerun once, then `review-shallow`; they list `declined`, `cannotVerify`.
- **3 review rounds** at most (uncapped loops ran 9 and 5). After a clean review a gate-only round
  skips the reviewer (`reviewsSkippedGateOnly`) unless non-test files outside the findings changed.
  A gate finding twice in a row escalates as `gate-repeat`; repeated reviewer findings: one `haiku` triage.
- **Work-gate fixes** (`debt-marker`, `ac-unmet`, `undelivered`, `approved-item`) are re-reviewed, scoped.
- **`undelivered`** is always a finding (`Approved item`); only `blocked` (`whoCanClear`) stops
  short; `approvals[].status` is each item's fate. **`discovered`** (outside the task) is added as a new epic task that this run delivers. **`processOnly`** (verified, only `no-red-evidence`, `tdd-skipped`, `review-shallow` open)
  releases dependents (`review-shallow` still escalates); `processGaps` never go to a fixer. **2 continuations** past the ceiling;
  escalations add `forward-merge-failed`, `verify-agent-died`; agents run the targeted `verify`.
- **Prose stays out of the review loop**: docs are ACs of a code task; a prose task is `review: false`.

### `planText` describes THIS run's tasks, and nothing else

The scope auditor audits against `planText`; the whole plan with a subset of tasks once made 78%
of a run's spend remediation. State THIS round's scope at the top, list what is done ("do not re-audit, do not rebuild") and what is still open; a known gap is a `planText` defect.
