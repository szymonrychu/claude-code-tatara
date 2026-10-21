# Handle what the run hands back

Read from Phase 4 of `start-development`, every time a `workbench:plan-execute`
run returns.

Read these **when the run returns, before dispatching anything else**:

- `approvals` - one status per ledger item (`references/approvals.md`):
  `delivered`, `blocked`, `escalated` or `unverified`. Any status other than
  `delivered` is the first thing to act on. A `blocked` one goes in the record
  with who can clear it; an `escalated` one is judged like any escalation; an
  `unverified` one is re-run through a fresh verifier on its committed HEAD.
- `escalated` - tasks the loop stopped on (`round-cap`, `no-progress`,
  `gate-repeat`, `audit-gap-persisted`, `handoff-cap`, `review-shallow`) with
  the findings verbatim, each carrying its `reason` (its `tasks[]` entry carries `triageRejected` or `ruling` when one applies). A `handoff-cap` task hit the context ceiling on every continuation;
  its `handoff` names the WIP commit and the remaining acceptance conditions -
  split the remainder into smaller tasks rather than re-running it whole. Judge
  each finding: fix the real ones in a new run with a sharper requirement, drop
  the wrong ones and say why. Never just re-run the same task unchanged. When
  you cannot tell who is right - reviewer or fixer - run `workbench:interrogate`
  on that task once and act on its verdict instead of dispatching another fix
  round.
- `escalated` with `gate-repeat` - the same gate finding (its `gate` tag
  names the check: `verify-failed`, `ac-unmet`, `tests-changed`, ...) came back
  with the same key in two consecutive rounds, so the fixer could not clear a
  deterministic check. Another round would fail the same way: fix the cause by
  hand or re-plan the task with a sharper requirement.
- Mid-run release: a task that ends `escalated` still releases its dependents when its
  only findings are process-only (`no-red-evidence`, `tdd-skipped`), when the triage
  rejected them (the task's `tasks[]` entry carries `triageRejected: true`), or when you ruled it
  accepted mid-run with `ticket.py rule <epic> --accept <task> --reason ...` (the
  ruled-accepted case: the `tasks[]` entry carries `ruling` `{accept, reason}`). The run reads
  `<epic dir>/rulings.json` at each wave boundary; a ruling for an
  unknown or unverified task is ignored and listed in `rulingsIgnored`; a ruling on a clean task is applied. Such a task is
  still `escalated` and `finished` stays false.
- Relaunch: `ticket.py continue <epic> --out-dir <dir> [--run <runId> | --return <return.json>]
  [--accept <ids> --reason ...]` applies the last return, records your rulings, refreshes
  the trees and writes the next run's args and named copy. Use it instead of rebuilding the
  args by hand; `ticket.py rule` records rulings alone, also while a run is in flight.
- `reviewsSkippedGateOnly` - informational, per task and in total: fix rounds
  whose findings all came from the gates ran fixer, verifier and gates only,
  with no reviewer. A gate-only round still re-dispatches a scoped reviewer when
  the fix touched non-test files outside every finding's file.
- `escalated` with `review-shallow` - the reviewer twice did not read every
  non-test file the implementer changed (the `unread` list names them). The
  work was never judged, so it is neither clean nor rejected. The task still
  releases its dependents, but it is always in `escalated` and `finished` is
  false; only `no-red-evidence` and `tdd-skipped` process-only tasks leave a
  run finished. Review it alone
  on a stronger model, or run `workbench:interrogate` on the task; never
  accept it as clean.
- `blocked` - an external blocker with `whoCanClear`. If it is you (rebase,
  merge a PR this session owns), do it now. If it is the user, it is a genuine
  blocker: it goes in the record, named, with who can clear it, and the run
  continues with everything not behind it. A `blocked` entry carrying
  `approvals` holds up those approved items: tell the user which approved
  items wait on them, by id.
- `escalated` with an `Approved item` finding - a task listed part of an
  approved item as `undelivered`, or the audit found one not landed. Approved
  items are never parked: fix it in a new run, or name the external blocker and
  who can clear it. An `undelivered` entry on any task, approved or not, is a
  high `missing` finding; only `blocked {reason, whoCanClear}` stops a task
  short.
- `misattributed` - `[{taskId, ownerTaskId, what}]`: `undelivered` entries that named
  another task's share (a task id of the run, or a path that task owns). They are not
  findings and do not stall the task; check that the owner task delivered the part.
- `discovered` - top-level array of gaps tasks found outside their own files,
  each with its `taskId`. They are never findings. Run
  `ticket.py apply-run <epic> <return.json> [--run-dir <transcript dir>]` (the dir adds task
  actuals from agent timestamps): it turns each entry into a todo
  task in the same epic. The epic cannot close while that task is open, so a
  discovered gap is tracked work, not a note.
- `escalated` with a `Tests changed in a fix round` finding - a fixer modified
  or deleted an existing test that no finding and no `tests.added` named. Judge
  whether the test edit was legitimate (the test itself was wrong); if not, the
  fixer weakened a test to get green: restore it and re-run the fix.
- `waveLevel` - gaps that belong to no single task (landing branches, a shared
  baseline). They are yours to place, never a task implementer's.
- `duplicates` - the same part built in more than one task, found by the
  audit's cross-task sweep. Before merging, keep one implementation (the
  owner's, or the more general one), fold the other's coverage into it, delete
  the copy, keep every test pointed at the kept code, and add a test that the
  behaviour applies once (two readers granting the same ability double it).
  A fix to another task's part is not a duplicate; a parallel rebuild is.
- `escalated` with `dependency-failed` - a task that never started because a
  dependency in `waitingOn` did not finish clean. Fix the dependency first,
  then re-run the dependent.
- `provides` - unplanned shared parts implementers built. Add them to the
  shared-parts map so the next round's plan reuses them.
- `processGaps` - bookkeeping the reviewers noticed (a missing MEMORY.md or
  status.md note, an unrun sweep or ratchet, an approval line), returned per
  task with `taskId`, `what` and `where`. They are not findings and never went
  to a fixer. Place each one yourself in Phase 5: do it, or write it into the
  record with why it was not done.
- `declined` - behaviour a reviewer chose not to judge, each with `what` and
  `why`. Nobody has judged it yet: judge it yourself, or route it to
  `start-review` over that task's diff in Phase 5. Never read it as clean.
- `cannotVerify` - requirements the diff and the tree cannot show (live
  behaviour, an external system). Verify each one in Phase 5, or write it into
  the record as unverified with what would show it.
- `forwardMerged` - informational: which finished dependent (`into`) received
  which remediation fix (`from`, `branch`), and the `head` it was re-verified
  on. Nothing to do; the record lists it.
- `escalated` with `forward-merge-failed` - a remediation fix could not be
  merged into a finished dependent: the merge agent hit a conflict or a red
  verify in the dependent's tree (`merge` carries its result). Dispatch
  `worktree-merger` to land the merge by hand, or re-plan the dependent on top
  of the fixed dependency.
- `escalated` with `land-failed` - an epic run with `mainCheckout` could not
  land the released task on the epic branch: merge.py hit a conflict or a red
  verify, or the land agent returned nothing (`land` carries its result). The
  epic branch stays at its prior head and the task's dependents are
  `dependency-failed`. Fix the cause in the task tree and land it through the
  continue gate's MERGE line. `landed` lists every task that did land, with
  its epic `head`.
- `escalated` with `verify-agent-died` - the independent verifier returned
  nothing, so the task has no verification on its HEAD. Re-run the task's
  `verify` through a fresh agent on the committed HEAD; never accept the
  implementer's claim in its place.
- `escalated` with `agent-output-invalid` - an agent's structured output
  failed the runtime retry cap (the task result carries `agentError`, at most
  300 chars). Only that task stopped; re-dispatch it, or split it if its
  report is too large to fit the schema.
- `escalated` with `impl-agent-died`, `fix-agent-died` or `review-agent-died` -
  that agent returned nothing or threw. Only that task stopped; re-run it
  through a fresh agent. A run-level `auditError` means an audit agent threw;
  the run still returned, so re-dispatch the audit.
- `selfVerification` vs `verification` - `selfVerification` is the
  implementer's own claim; `verification` is the independent verifier's
  result, with the `head` SHA it ran on. Only `verification` counts, and the
  record uses that one. A task whose `verification` has no `head` is
  unverified.
- `tests.red` - the red evidence every implementer returns: the test command
  and its failing output from before the implementation existed. A task with
  `wroteTestFirst: true` and no `tests.red` came back with a `No red evidence`
  finding; one with `wroteTestFirst: false` and no listed exception in
  `tests.note` came back with a `TDD skipped` finding, whose fix carries the
  revert recipe. The record carries the red run.

Every ruling you make on any of these - dropped finding, re-scoped task,
interrogate verdict acted on - is one line in the record's rulings.

## Reply short

`rules/concise-orchestrator.md`, applied to everything you send after the run
returns:

- A progress update is one line: `<what moved> - <next> - <decision needed, if any>`.
- Never paste logs, tables, JSON or diffs unless asked; cite a path instead.
  Never restate what a notification already says.
- A finished task is three lines at most: what landed, verified how (the one
  summary line of the real output), what is next.
- Subagent reports are capped (a word limit in the prompt); read their files,
  not their transcripts.
- Detail only when the user asks for it, or when a decision needs it.
