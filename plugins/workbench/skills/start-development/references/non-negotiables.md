# Non-negotiables in full

The full text behind the condensed non-negotiables in `SKILL.md`.

## Delivery is not optional

The requested change ships, however many implement, review and optimisation rounds that takes. No
"good enough for this pass", no reduced deliverable presented as the agreed one. The per-task loop
cap bounds a loop, never the delivery; a non-converging loop means change approach, not stop. The
only acceptable stop is a genuine blocker you cannot resolve, named in the record. "Too hard", "needs
something that does not exist yet" and "out of scope" describe work; build the missing scaffolding.

## Orchestrate. Do not implement.

Your context is the scarcest resource in this flow; what you read yourself, you still carry at merge
time. Delegate reading, searching, suite runs, implementing and claim-checking to subagents that
return conclusions. Never read a large file to "check" a subagent, never implement a task yourself
because it looks small, and **never merge a worktree yourself**: dispatch `worktree-merger`. Do not
re-run a command a subagent already ran; batch independent dispatches in one message.

**The exception, and it is real: a dispatch is not free.** Read it yourself when you can name the
file and need a handful of lines, or when the brief would cost more than the answer. On the lean
path this is the default. Size the model to the question: sonnet for lookups and everything else,
opus for research and the hardest implementation tasks, fable for very complex architectural
decisions. You keep the plan, the gate, the decisions, the rulings, and the state of what is finished.

## Loop until it is actually finished

`workbench:plan-execute` returns `finished: true` only when the audit confirmed every plan item
landed, every task passed verification, and nothing was escalated, blocked, or wave-level. While
`finished` is false, you keep going:
1. Read `escalated`, `blocked`, `waveLevel`, `unverified`, `undelivered`, and `discovered`.
2. Judge each one. An auditor finding can be wrong; record why and move on.
3. Re-dispatch the real remainder as another `workbench:plan-execute` run, with the outstanding
   items as its tasks and `planText` scoped to just them.
4. Repeat until finished. A `blocked` item only the user can clear goes in the record, named with
   who can clear it.

**The one stop condition is your own context.** Every turn re-reads it. At **400k tokens or 75%
context used, whichever comes first**, stop starting new rounds: finish or abandon the round in
flight cleanly, write down exactly what remains (items, which worktrees and branches hold what, what
merged, what the next round must do), and hand off (`handoff` skill). Stopping at 75% with a clean
handoff is finishing responsibly; stopping at 95% with a half-merged tree is not.

## Test-driven, and verified before it is believed

Every behaviour change is written test-first: red, green, refactor. The test is seen failing for the
right reason before the implementation exists. Narrow exceptions only - pure formatting, docs, a
no-behaviour dependency bump, or a throwaway spike - and name the one that applies rather than
claiming a cycle you did not run; the red run is part of the deliverable. A task is done when it is
verified on HEAD <sha> by an agent that did not write it. Nothing is reported as done, passing, or
complete without having run the check and read the output; a subagent returns the command it ran and
the real output tail, including the pass/fail line. "Should pass" and a clean-looking diff are not
evidence.

## Hooks that hold the line

The commit guard and the `verification-freshness` guard, per `references/hooks.md`: a subagent
cannot end a turn in a worktree whose last test run was not on its HEAD, nor with uncommitted work.

## Boy scout rule

Leave the tree better than you found it; someone else's loose end is never the reason your work is
incomplete. Simplify the files in your hands without behaviour change. Commit functional uncommitted
work after confirming it is green. Clear uncommitted work that blocks delivery (fix lint and tests,
commit it separately, then yours on top); never report a pre-existing failure as why your task is
unfinished. Applies at phase 1 and phase 6 (nothing ships on top of red). Never commit broken,
half-finished, or unverified work.

## Gates and autonomy

One gate, after the design doc and the plan doc exist. Everything after it runs unattended to merge
and the record. The run stops only for:
- an irreversible operation that was not listed at the gate;
- a security-sensitive action the plan did not name;
- a side effect outside the worktrees and the MRs this session owns;
- a plan so broken that every path forward is a guess.

Each stop is reported with what triggered it; everything not behind it continues. Escalations are
judged by you; each ruling is a line in the record. "Waiting" is never a terminal state: enumerate
every open MR, pipeline, branch, and worktree, clear what only you can clear, act on the first item
that becomes ready, and bound any genuine external wait.

Nothing outside the approved plan gets worked on; a tangent is one noted line. A bug or gap in or
adjacent to code a task touches is fixed in that task; one outside its files is returned as
`discovered` and added as a new epic task that this run delivers.

## Scope is not negotiable

The agreed plan ships complete; difficulty describes work, not a reason to drop it. Four mechanisms enforce this and must stay wired:
1. Each task's `requirement` is passed verbatim to its implementation agent.
2. The implementation agent returns `complete` plus an `undelivered` list (scope not delivered, always a
   finding) and a `discovered` list (gaps outside its files, each added as a new epic task that this run delivers): structured data.
3. `scope-auditor` verifies against the files, not the summaries - once per epic at close (the
   phase 5 `auditOnly: true` run), or once per run inside the workflow when there is no epic.
4. The approval ledger: every approved item maps to a decision and to tasks before the gate, cannot
   be left undelivered inside the run, is audited by id, and has a status in the record.

Every acceptance condition of every task is delivered; one that is not is an `undelivered` entry, which is a finding and never a status. Delivering it strikes the ledger item.
No "later" parking: an approved item is delivered or escalated as a named blocker. An idea outside
the approved list goes to the user in one line after the record. A genuine blocker is named in the record and the closing message.
