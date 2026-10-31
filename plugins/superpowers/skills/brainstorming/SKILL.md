---
name: brainstorming
description: "You MUST use this before any creative work - creating features, building components, adding functionality, modifying behavior, or planning anything new. Discovery by subagents, plan.md with a scope ladder from MVP to complete, then ONE gate where the user picks a rung and answers the open questions."
---

# Brainstorming

You are very good at building. You build what you believe your human
partner wants, and that belief is usually thinner than it feels. This
skill is for finding out what they actually want, and why, before
anything gets built.

In this flow the finding out is done by subagents and written down in one
file, plan.md, and your human partner is asked once, at ONE gate, with
every question batched into that single message. You orchestrate: you
never write the plan, the code or the research yourself.

`ticket.py` below is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py`, run
from the main checkout. When you hand it to a subagent, resolve
`${CLAUDE_PLUGIN_ROOT}` first and pass the absolute path: a subagent's own
plugin root is another plugin's. It owns every file under `docs/plans/`
and commits its own changes as `chore(ticket): <plan> <event>`. Details:
`${CLAUDE_PLUGIN_ROOT}/references/tickets.md`.

## First: What Do You Actually Know?

Before you reply, ask yourself: what do I know about what they want, and
why?

- **Everything that matters is in the request** ("make the icon cornflower
  blue"). This is a quick, clear task. Do it, and say what you did.
- **Something non-trivial is missing.** Size the work, then run the flow
  below.

## Size the Work

Pick a size and say it in plain words. They can override it.

| Size | The full description | Then |
|------|----------------------|------|
| A quick, clear task | the request itself | do it |
| A small change | in chat | build it through the normal workflow |
| A project with a written design | plan.md | the flow below, then superpowers:writing-plans |

If it grows mid-task, stop, say so, and step up a size.

If this is really several independent projects, say so: each is its own
plan, and one gate may batch several plans, a section each.

**Modes.** Component mode: code in `code/` submodules; the plan ends in a
pull request from its integration branch. Meta mode: the workbench
superrepo itself, no submodule; the plan closes by rebase plus
fast-forward of the local main. Work spanning both is two plans, meta
first unless a dependency says otherwise.

## Discovery

Discovery is read-only and runs as subagents, all lanes in one message so
they run concurrently. Set the model on every dispatch; research lanes
run on opus. Component mode first runs `git-submodules-refresh` and
finishes it.

- `workbench:codebase-cartographer` (opus), one per repo in scope: shape,
  entrypoints, boundaries, conventions, the LSP symbol sweep where a
  language server exists.
- `workbench:start-research` (a general-purpose subagent on opus running
  that skill) for prior art and external facts, with the lenses you chose.
- The reuse hunt: `research-code-internal` (opus) when the plan adds a
  helper, reader, parser, schema field or subsystem, or a repo has more
  than about 200 source files.
- Run each repo's lint and tests now and keep the commands verbatim; the
  tree state is never skipped.

Choose the research lenses on purpose and record each in plan.md's
Research section as ran, or skipped with the reason: a lens nobody decided
on is a gap. Run `research-code-external` when the change has known
analogues or an open fork, `research-papers` for a scientific or
algorithmic core, `research-docs` for a library or platform API used in a
new way, upgraded, or touched in three or more call sites.

Every brief ends in `## Plan inputs`: four lists, "none" when empty, one
line per entry: `reuse` (name - file:symbol - which plan items need it),
`do-not-build` (item - what provides it instead - source), `fix-as-ac`
(anti-pattern - where - the step's Verify or Test first that pins the
fix), `ideas` (adopted / rejected, one line each, with the source). You
keep the brief paths, never their contents; the plan-writer places every
entry.

**Ground to cover.** This is territory for discovery and the plan, not a
script to read out:

- what kind of thing this is, and what makes it special
- why now, and what success looks like to them
- goals, non-goals, and anti-goals (what would make this a failure even
  if it technically works)
- prior art: what they've seen elsewhere, loved or hated
- current state: what exists now, what they've tried
- the details they care about

**How it gets made.** When there's existing work, build on what it
already uses. Any choice the plan makes that they did not state goes in
the Decisions as `(my call)`, never as something they agreed to.

**Think wide privately.** Several viable approaches or a costly-to-reverse
choice: one `workbench:architect-researcher` (opus), or `fable` only for
one framed consulting question. The plan shows the comparison in its
Decisions.

## The Plan

1. `ticket.py check --title "<title>"` lists near duplicates; extend one
   rather than start a twin.
2. `ticket.py new --title "<title>" --repos <a,b>` creates plan.md from
   `${CLAUDE_PLUGIN_ROOT}/templates/plan.md` in `docs/plans/todo/<plan>/`.
3. One general-purpose subagent on opus, briefed by
   [plan-writer-prompt.md](plan-writer-prompt.md) in plan mode with
   `{plan, briefs[], ticket}` (`ticket` is the absolute ticket.py path),
   fills plan.md and commits it as `docs(plan): <plan> plan`: What and why,
   a scope ladder from the absolute MVP (rung 1) to the most complete
   delivery with a recommended rung, Non-goals, Design, Decisions with
   unstated defaults marked `(my call)`, open questions each with a
   recommended answer, Research and Irreversible operations. Keep its
   agent id: the same agent writes the implementation plan after the
   gate.

**Builder check:** dispatch a fresh subagent with
[builder-check-prompt.md](builder-check-prompt.md) on the committed
plan.md. Don't present the gate until the check is back. Sort what the
builder asks into three piles:

- **Answered already** by discovery or the project: the plan-writer puts
  the answer in plan.md.
- **Minor:** a sensible builder could settle it without changing what gets
  built. The plan-writer settles it as a Decision marked `(my call)`.
- **Theirs:** only your human partner can answer it, and the answer changes
  what gets built. The plan-writer adds it as an open question with a
  recommended answer.

Continue the plan-writer once with the piles; it revises and commits
plan.md. Ask your human partner only what no probe can answer: a fact is
settled by a read-only probe, a preference is theirs.

## The Gate

ONE gate: one message, every question batched into it, one section per
plan:

1. The plan.md path, and what and why in two lines.
2. The rungs, one line each, with the recommended rung.
3. The open questions, numbered, each with a recommended answer, worded so
   that "yes" accepts it.
4. The research lenses that ran and the ones skipped, with the reason;
   what the builder check raised.
5. Every irreversible operation in scope (destroy, data deletion, secret
   rotation, shared force-push), by name.
6. "Pick a rung per plan and answer, or tell me what to change."

On changes, the plan-writer revises plan.md and the gate is presented
again: the same single message, never a trickle of questions.

<HARD-GATE>
Nothing is built until the user picks a rung and answers the open
questions. Building includes writing product code, scaffolding,
installing dependencies, creating projects, claiming the plan, and
invoking an implementation skill. Discovery, reading and exploring are
fine.

The user's answer at the gate is the only approval, and it covers
everything after it: the implementation plan, the run and the merge go
unattended. An irreversible operation not listed at the gate stops the
run.

After the gate, the next step is superpowers:writing-plans and no other
skill.
</HARD-GATE>

## Red Flags

| Thought | Reality |
|---------|---------|
| "I'll ask this one question now and the rest later" | Every question waits for the ONE gate, batched. |
| "I'll fill in sensible defaults" | Good. Mark them `(my call)` in Decisions. A default they never saw is one they couldn't reject. |
| "I'll write plan.md myself, it is quicker" | You orchestrate. The plan-writer writes it. |
| "They said 'sounds good' to the idea" | Approval is a picked rung and answered questions at the gate, nothing less. |
| "Discovery can be skipped, I know this repo" | The lanes run, or plan.md says why one was skipped. |
