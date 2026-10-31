# Non-negotiables in full

## Delivery is not optional

The agreed scope ships. The cap of two fix rounds bounds a loop, never the delivery: an open finding after
the cap gets another approach from the orchestrator, not a smaller deliverable. The only stop is a named blocker.

## Orchestrate. Do not implement.

The orchestrator is the supervisor, responsible and accountable for all subagent work; it never writes code or
builds anything, however small (its own duties: rules/housekeeping.md). Delegate planning, implementing,
reviewing and suite runs; never merge a worktree yourself (the `worktree-merger` runs `ticket.py close` or the MR).
Set every model: sonnet by default, opus for planning and the hardest chunks, fable for one hard architecture
question.

## Loop until it is actually finished

A plan is finished when every step is delivered on a verified head, the reviewer passed the whole diff and wrote
retro.md, the full suite is green and the plan is closed or merged. Until then, act on the real findings. At 400k
tokens or 75% context finish the dispatch in flight, write down what remains, hand off (`handoff`).

## Test-driven, and verified before it is believed

Every behaviour change is written test-first: red, green, refactor; the red run is part of the deliverable. Narrow
exceptions only (formatting, docs, a no-behaviour dependency bump, a deletion pinned by a retirement test), named.
A plan is done when verified on HEAD <sha> by an agent that did not write it: the reviewer runs every step's
Verify and the Final verify on HEAD.

## Hooks that hold the line

The commit guard and verification-freshness guard (`references/hooks.md`): a subagent cannot end a turn in a worktree whose last test run was not on its HEAD.

## Boy scout rule

Simplify what you touch; commit working uncommitted work separately once green; a pre-existing failure never excuses unfinished work.

## Gates and autonomy

One gate. After it the run stops only for an irreversible operation not listed at the gate, a security-sensitive
action the plan did not name, a side effect outside the plan's tree and MRs, or a plan so broken every path is a
guess. "Waiting" is never a terminal state. A tangent is one noted line.

## Scope is not negotiable

The agreed rung is the scope: every item and step of it is delivered, and nothing else is built. A step that is not
delivered is an `undelivered` entry, which is a finding, never a status. A change no step and no agreed item covers
is over-delivery, also a finding: it is removed in a fix round. Simplifying code a step already touches, behaviour
unchanged, is not over-delivery. A gap outside the steps is `discovered`: recommended, never built, and relayed in
retro.md's Recommendations. No "later" parking: delivered, or stopped as a named blocker.
