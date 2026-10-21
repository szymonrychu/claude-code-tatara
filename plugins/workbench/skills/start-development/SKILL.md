---
name: start-development
description: >
  Mandatory entry point for non-trivial development in this workbench - work
  across code/ submodules and meta-development of the workbench itself. Drives
  discovery, optional research steps, a design doc and a plan doc, then one
  approval gate; after it, runs autonomously to merge through a deterministic
  implement/review/audit workflow, and writes a record of what was built.
---

# start-development

Eight phases, **one approval gate**, sized to the work. Phase 0 picks the size; everything after it
is conditional on that choice. Work the phases in order and create a todo per phase.

```
0 size  ->  full:  1 discovery (+ research lenses on trigger) -> 2 design doc
                   -> 3 plan doc + tasks.json -> builder check (+ interrogate if contested)
                   -> [THE GATE: design + plan together] -> 4 execute -> 5 verify
                   -> 6 merge -> 7 record

            lean:  1L recon -> [THE GATE: design + plan in one message]
                   -> 4L implement -> 5L verify -> 6 merge -> 7 record (short form)
```

## Modes

- **Component mode** - the task changes code in `code/` submodules; full flow through merge, deploy.
- **Meta mode** - the task changes the workbench superrepo itself (`.claude/`, `docs/`, root
  configs, `CLAUDE.md`, `MEMORY.md`, `ROADMAP.md`) and no submodule. When the metarepo has an
  `origin` remote, meta work commits on a branch and lands like a component (PR or MR on that
  origin, then the record); with no `origin` remote it never commits, ending at reviewed,
  test-green edits plus the record.

A task spanning both runs as two passes, meta first unless a dependency says otherwise.

## Phase 0 - Size the work

The full flow costs several hundred thousand tokens before a line of code exists. Size the work, say
which path and why in one line, and proceed.

**Take the LEAN path when all of these hold:**
- one repo, and a file set you can name up front (roughly ten files or fewer)
- no new interface between repos, no schema or deployment-topology change
- nothing expensive to reverse: no data migration, secret rotation or irreversible destroy
- the constraints already determine the approach, so there is no real fork for a design gate

**Take the FULL path when any of these hold:**
- more than one `code/` submodule changes, or a cross-repo contract moves
- there is a genuine fork worth a human decision (two viable designs, or an expensive-to-reverse
  choice)
- the change touches authz, secrets, cluster exposure, or container privilege
- the codebase in scope is unfamiliar enough that you cannot name the files

When it is borderline, start lean; escalating costs one message.

**The path never downgrades the non-negotiables:** both are test-first, verify before reporting,
deliver the entire agreed scope, and stop for anything destructive.

### The lean path

1. **1L recon.** Refresh submodules, confirm the tree is clean and green, and read the files in
   scope yourself; one subagent for a specific question, not a fan-out.
2. **The gate.** One message with the design and the plan, the full gate below sized down.
3. **4L implement.** Work in the integration worktree directly, or dispatch a single `workbench:implementer`
   agent with the full requirement text. No worktree per task, no `workbench:plan-execute` workflow,
   no `worktree-merger`.
4. **5L verify.** The repo's own lint and tests, real output quoted, plus `start-review` over the
   diff; `security-researcher` only if the diff touches phase 5's security surface.
5. **6 merge.** Phase 6 as written, unchanged.
6. **7 record, short form.** A few lines of `templates/record.md` at `doc_path.sh record`: what
   changed, verification tail, MR URL, rulings.

## Phases 1-3 - Discovery, design, plan

Full detail: `references/phases-1-3.md`.
- **Phase 1 - Discovery.** Component mode first runs `git-submodules-refresh` (and `submodule-auditor`
  on a stale tree), then `start-discovery`; its brief ends in `Plan inputs` and becomes `contextPack`.
  Optional research lenses (`research-code-internal`, `research-code-external`, `research-papers`,
  `research-docs`) are each recorded as ran or skipped with a reason.
- **Phase 2 - Design doc.** `architect-researcher` when more than one approach is viable (`fable` only
  for consulting-shaped questions). Ask only what no probe can answer. The work is an epic under
  `docs/plans/{todo,in-progress,done}/<epic>/`, owned by `ticket.py`.
- **Phase 3 - Plan and tasks.** One `workbench:planner` writes the task files and the approval ledger.
  Lint with `node ${CLAUDE_PLUGIN_ROOT}/workflows/validate-tasks.mjs --epic <epic dir>` (must print
  `ok`), then the builder check (`references/builder-check.md`); `workbench:interrogate` when the
  design is contested or high-risk, with its verdict in the gate message (before the gate).

## The gate

One message, in this order:
1. The approval ledger at `<epic dir>/approvals.json` (a legacy dated-file run: `doc_path.sh
   approvals "<topic>"`): every item discussed, with its id, text, the decisions and the task slugs
   that deliver it. Approving this message approves every entry by id; an item you strike leaves the
   ledger, the design and the plan - it is never kept as later.
2. The epic README and design doc paths, the summary and the project brief (what, how, why).
3. The task table (id, title, value, files, owns/uses/dependsOn, model).
4. The research lenses that ran and the ones skipped, with the reason.
5. The builder check's remaining questions, one batch, preference calls only, numbered, each with a
   recommended answer, worded so that "yes" accepts it.
6. The `workbench:interrogate` verdict, when it ran.
7. Every irreversible operation the plan contains (terraform destroy, data deletion, secret
   rotation, force-push to a shared branch), so the approval covers each one by name.
8. The exit predicate: every task verified, audit clean, MRs merged, deploy green, record written.
9. "Approve, or tell me what to change."

One gate may approve several epics, each under its own heading; after it, one plan-execute run per
epic. `ticket.py questions` gathers the open questions of every todo epic into the gate's one batch;
`ticket.py decide` records each answer. `ticket.py` commits its own `docs/plans/` changes as `chore(ticket): <epic> <event>` (if the
user answers no at the gate, the orchestrator commits them).

`AskUserQuestion` for genuine option choices, prose otherwise. On changes, revise the docs and
tasks, re-lint, re-present. Do not proceed without approval.

**Everything after the gate runs unattended to merge.** The one exception is a safety interlock: an
irreversible operation not listed at the gate stops the run and is reported, with what it would
destroy.

## Phase 4 - Execute

Claim the epic (`ticket.py move <epic> in-progress`), create worktrees for the epic's repo subset
(`ticket.py worktrees <epic>`), then run the epic through `workbench:plan-execute`, never by
hand-dispatched implementers: one run per epic through a named copy built by `ticket.py args`. The
Workflow args block, review tiers and gate tags, relaunch commands, handback fields and the
`planText` rule are in `references/phase-4-execute.md`; the return is read per
`references/run-handback.md`.

`Workflow({ scriptPath: '<the printed path>', args: { ... } })` launches the run. On return,
`ticket.py apply-run <epic> <return.json>` writes results back into the task files; discovered work
becomes new tasks in the same epic. To wait on the run, arm `heartbeat.py --run <id>` (one Monitor);
on END read the return per references/run-handback.md. Relaunch with
`ticket.py continue <epic> --out-dir <dir> --accept <ids>`. Never merge a worktree yourself.

## Phases 5-7 - Verify, merge, record

Full detail: `references/phases-5-7.md`.
- **Phase 5.** `ticket.py stage <epic> review`, whole-diff review, one `auditOnly` plan-execute run,
  the one full-suite run, security and infra checks, then `ticket.py review <epic> --verdict ...`
  and `ticket.py move <epic> done`.
- **Phase 6.** Component mode: commit, push, update PRs, watch (`references/merge-hosts.md`), merge
  each PR the moment it is ready, watch the deploy, check post-deploy health.
- **Phase 7.** Dispatch `record-writer`; send the user ONE closing message, three lines at most.

## Non-negotiables

Full text: `references/non-negotiables.md`.
- **Delivery is not optional.** The requested change ships; a non-converging loop means change
  approach, not stop. The only stop is a genuine blocker, named in the record.
- **Orchestrate. Do not implement.** Delegate reading, searching, suites and implementing; never
  merge a worktree yourself (dispatch `worktree-merger`); size every subagent's model explicitly.
- **Loop until finished.** `workbench:plan-execute` returns `finished: true` only when the audit
  confirmed every item; while false, judge `escalated`, `blocked`, `waveLevel`, `unverified`,
  `undelivered`, `discovered` and re-dispatch the real remainder. The one stop condition is your own
  context: at 400k tokens or 75% used, finish the round cleanly and hand off (`handoff` skill).
- **Test-driven and verified.** Test first, red seen; nothing is reported done without the command
  run and its real output read; a task is done when verified on HEAD by an agent that did not write it.
- **Hooks hold the line** (`references/hooks.md`); **boy scout rule**: simplify what you touch, clear
  blocking uncommitted work in its own commit, never ship on red.
- **Gates and autonomy.** One gate; after it the run stops only for an unlisted irreversible
  operation, an unnamed security-sensitive action, a side effect outside the owned worktrees and
  MRs, or a plan so broken every path is a guess. "Waiting" is never a terminal state.
- **Scope is not negotiable.** The agreed plan ships complete: `requirement` passed verbatim,
  `undelivered` and `discovered` returned as data, `scope-auditor` checks files not summaries, and
  the approval ledger maps every approved item to tasks. No "later" parking.

## Notes

- The read-only agents (when each is dispatched, in which phase) are in `references/agents.md`.
- Mandatory for all non-trivial development here. Size every subagent's model and effort explicitly.
