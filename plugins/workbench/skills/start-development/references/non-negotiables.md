# Non-negotiables in full

## Delivery is not optional

The agreed scope ships. The cap of two fix rounds bounds a loop, never the delivery: an escalated task gets a
sharper requirement or another approach, not a smaller deliverable. The only stop is a named genuine blocker.

## Orchestrate. Do not implement.

The orchestrator is the supervisor, responsible and accountable for all subagent work; it never writes code or
builds anything, however small (its own duties: rules/housekeeping.md). Delegate implementing, reviewing, auditing
and suite runs; never merge a worktree yourself (`ticket.py close`, the MR, or a `worktree-merger` for a conflict).
Set every model: sonnet by default, opus for planning and the hardest tasks, fable for one hard architecture question.

## Loop until it is actually finished

An epic is finished when every task is `done` on a verified head, the scope audit is clean, the full suite is
green and the epic is closed or merged. Until then, judge each escalated task, finding and gap and act on the real
ones. At 400k tokens or 75% context finish the dispatch in flight, write down what remains, hand off (`handoff`).

## Test-driven, and verified before it is believed

Every behaviour change is written test-first: red, green, refactor; the red run is part of the deliverable. Narrow
exceptions only (formatting, docs, a no-behaviour dependency bump, a deletion pinned by a retirement test), named.
A task is done when verified on HEAD <sha> by an agent that did not write it: the reviewer runs `verify` on HEAD
and checks every acceptance condition.

## Hooks that hold the line

The commit guard and verification-freshness guard (`references/hooks.md`): a subagent cannot end a turn in a
worktree whose last test run was not on its HEAD.

## Boy scout rule

Simplify what you touch; commit working uncommitted work separately once green; a pre-existing failure is never
why your task is unfinished.

## Gates and autonomy

One gate. After it the run stops only for an irreversible operation not listed at the gate, a security-sensitive
action the plan did not name, a side effect outside the epic's tree and MRs, or a plan so broken every path is a
guess. "Waiting" is never a terminal state. A tangent is one noted line.

## Scope is not negotiable

Each task's requirement goes verbatim to its implementer. Every acceptance condition is delivered; one that is not
is an `undelivered` entry, which is a finding, never a status. A gap outside the task's files is `discovered` and
becomes a new task in the same epic. One `scope-auditor` per epic checks the README goals and every acceptance
condition against the files, not the summaries. No "later" parking: delivered or escalated as a named blocker; an
idea outside scope goes to the user in one line.
