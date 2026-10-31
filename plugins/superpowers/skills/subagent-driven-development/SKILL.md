---
name: subagent-driven-development
description: "Use after writing-plans to run one agreed plan unattended: claim it, run its chunks through one workbench:implementer each, sequential in one plan tree, review the whole diff once with one workbench:reviewer, at most two fix rounds, retro.md on a pass, then finishing-a-development-branch."
---

# Subagent-Driven Development

Run one agreed plan by dispatching one implementer per chunk, sequential in one plan tree, then one reviewer on the whole diff, at most two fix rounds, and land it.

**Why subagents:** You delegate work to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed. They should never inherit your session's context or history - you construct exactly what they need. This also preserves your own context for coordination work. You orchestrate: you never implement a step, never fix a finding and never merge a tree yourself.

**Core principle:** one implementer per chunk + one whole-diff review + at most two fix rounds = the agreed rung, nothing more and nothing less.

`ticket.py` below is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py`, always run from the main checkout; a subagent gets its absolute path (its own `${CLAUDE_PLUGIN_ROOT}` is another plugin's). `<plan>` is the plan slug. Hand agents paths, never file contents; every agent call, fix rounds included, runs in the background, and you keep only each agent's capped report.

**Narration:** between tool calls, narrate at most one short line - the ledger and the tool results carry the record.

**Continuous execution:** Do not pause to check in with your human partner. The gate in brainstorming approved the whole run to merge. Execute every chunk without stopping. The only reasons to stop are the ones named below, or the plan has landed. "Should I continue?" prompts and progress summaries waste their time.

**Rulings, not stalls.** A running plan does not wait on a human. Conflicts, ambiguities, plan defects - decide them. plan.md's agreed scope is the binding authority, implementation-plan.md is its argument, and your judgment settles what neither answers. Record every decision in the ledger as `Ruling: <what you decided> - <why> - <what it costs if wrong>`, and keep going. A wrong ruling costs rework your human partner can see and undo; a session parked on a question costs their whole day and buys nothing. A ruling never shrinks the agreed rung: a smaller deliverable is not a ruling, it is under-delivery.

Four things stop you, and only these: an irreversible or destructive operation; a security-sensitive action; a side effect outside this worktree that norms say you ask about first (a push to a shared branch, a publish) and that the gate did not cover; and a plan so broken that every path forward is a guess. Of the first kind, one rule is absolute: an irreversible operation not listed at the gate stops the run. For those, stop and ask.

## Entry Conditions

Stop and report the refusal if any fails:

- plan.md `rung` is set and implementation-plan.md exists next to it (`ticket.py move` enforces both).
- The plan is in `todo` or `in-progress` (a repeat claim reuses the tree).
- Main is clean and green.

## Setup

1. Claim: `ticket.py move <plan> in-progress` claims the plan and creates the tree on branch `<plan>` (superpowers:using-git-worktrees; it is the one way a plan tree is made). Note the base: `git -C <tree> merge-base main HEAD`.
2. Workspace: run `bash ${CLAUDE_PLUGIN_ROOT}/skills/subagent-driven-development/scripts/sdd-workspace <plan file>` from the tree; it prints the plan's git-ignored directory (under `<tree>/.superpowers/sdd/`), home to every artifact of THIS plan: ledger, chunk briefs, reports, review packages.
3. Ledger: `<workspace>/progress.md`, first line `# SDD ledger - plan: <plan file path>`. Conversation memory does not survive compaction; the ledger and `git log` do. A chunk whose steps all have a commit titled `S<n>` in `git -C <tree> log` is done: never re-dispatch it, resume at the first chunk with an uncommitted step.
4. Read implementation-plan.md once and create a todo per chunk. Before the first dispatch, scan it once for steps that contradict each other or the agreed rung, and for anything a step mandates that the review would call a defect; write the table to the ledger and rule on each finding before execution begins.

## Model Selection

**Always specify the model explicitly when dispatching a subagent.** An omitted model inherits your session's model - often the most capable and most expensive. The models follow AGENTS.md ground rule 2:

| Role | Model |
|------|-------|
| implementer | the model from the chunk header, `## Chunk <k>: <name> (model: <sonnet|opus>)` |
| reviewer, re-review | sonnet |
| security-researcher | sonnet |
| worktree-merger | sonnet; opus when a rebase conflict is predicted |

The model never changes between fix rounds: a round continues the same agent.

## The Chunk Loop

Chunks run sequential, in the order of implementation-plan.md, in one tree. Never dispatch two implementers at once.

1. **Brief:** `bash ${CLAUDE_PLUGIN_ROOT}/skills/subagent-driven-development/scripts/task-brief <plan file> <k>` extracts chunk `<k>` to a file and prints its path.
2. **Dispatch:** one `workbench:implementer` per chunk, with the model from the chunk header, using [implementer-prompt.md](implementer-prompt.md): the plan path, the chunk number, the brief path, the tree, the absolute ticket.py path, and the report contract. Never paste history from earlier chunks into a later dispatch. Record the agent id: fix rounds continue it.
3. **Report:** the implementer returns `complete`, `commits`, `undelivered`, `discovered`, `questions`, `tests` and `verification`. Answer `questions` by continuing the same agent, never by guessing for it. `complete: false` with a `handoff` gets a fresh implementer on the same chunk with the handoff.
4. **Ledger:** `Chunk <k>: complete (commits <base7>..<head7>)`, then the next chunk.

`undelivered` and `discovered` are data, never a reason to stop: `undelivered` is a finding, sent back in a fix round; `discovered` is recommended and never built, and goes to retro.md's Recommendations.

## The Review

After the last chunk, one reviewer: one `workbench:reviewer` (sonnet), dispatched through superpowers:requesting-code-review with its `code-reviewer.md`, on the whole diff `git diff <base>...HEAD`. Package the diff first: `bash ${CLAUDE_PLUGIN_ROOT}/skills/subagent-driven-development/scripts/review-package <plan file> <base> HEAD` prints the file the reviewer reads in one call.

It reviews in this order: clean tree at HEAD, every step's Verify and the Final verify on HEAD, under-delivery against every agreed item and step, over-delivery of any change no step covers, debt markers, then quality. Over-delivery is a finding: the change is removed in a fix round.

A diff touching secrets, SOPS, RBAC, ingress, privilege, CI vars, image pins or hooks also gets one `security-researcher` (sonnet) on the same package; its findings join the reviewer's. Terraform or charts: `tf-planner` / `helmfile-differ` when the `workbench-infra` pack is enabled.

## The Fix Rounds

Findings go back in at most two fix rounds, by continuing the same agents (SendMessage):

1. Continue the same implementer (the one whose chunk owns the files, else the last) with the open findings verbatim, nothing else. It fixes test-first, re-runs the covering Verify, commits, and returns the same report shape.
2. Package the fix range (`review-package <plan file> <fix base> HEAD`, where the fix base is the head the review saw) and continue the same reviewer with [re-review-prompt.md](re-review-prompt.md).
3. Ledger: `Fix round <r>/2 (<x> addressed, <y> open - <one-liners>; commits <a7>..<b7>)`.

Never fix findings yourself: your context stays clean for coordination, and your fixes skip review.

Open findings after the second round are yours to judge, and every judgement is a ledger `Ruling:` line: a reviewer finding that is wrong is dropped with the reason; a real one gets a sharper instruction or another approach through the same agents; never a smaller deliverable. Only the four stop conditions above stop you here.

## On a Pass

A clean review (Verify green on HEAD, no `undelivered`, no over-delivery, no open findings): the reviewer writes retro.md from `${CLAUDE_PLUGIN_ROOT}/templates/retro.md` at `ticket.py path <plan> retro`, in the main checkout, and nothing else. Its Recommendations carry every `discovered` entry, ideas beyond the plan, and facts only implementation could reveal.

## Finish

Collect every ledger line containing `Ruling:` into the closing message's input, in order, each with what it costs if wrong: a ruling that dies with the workspace was a decision made in secret. Then delete this plan's workspace (`rm -rf <workspace>`); sibling directories belong to other plans.

Use superpowers:finishing-a-development-branch to land the plan.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Close enough on the agreed rung" | An unmet item is `undelivered`, a finding. Fix it in a round. |
| "I'll fix it myself, dispatching is overhead" | Controller fixes pollute your context and skip review. Continue the implementer. |
| "A third round will converge" | Two rounds is the cap. Judge what is open and rule; never a third round. |
| "The implementer built a useful extra" | Over-delivery is a finding. It is removed in a fix round, and recommended in retro.md if it is worth having. |
| "This finding is obviously wrong, I'll drop it" | Drop it with a ledger `Ruling:` line saying why. Silent discards are forbidden. |
| "The fix was small, skip the re-review" | Every round ends with the same reviewer on the new HEAD. |
| "Ledger bookkeeping is overhead" | The ledger is what survives compaction. |
| "The implementer spawned its own reviewer - free extra assurance" | It's a duplicate seat; the whole-diff review is the gate. |
