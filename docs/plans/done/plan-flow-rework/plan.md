---
title: Plan flow replaces epics and tasks
repos: []
created: 2026-10-31
owner: ""
rung: "3"
---

# Plan flow replaces epics and tasks

## What and why

What: replace the epic/task development flow of the `workbench` plugin with one `plan.md` and one
`implementation-plan.md` per improvement. Discovery subagents feed a plan-writer; plan.md carries a
scope ladder from the absolute MVP to the most complete delivery; one human gate picks the rung;
the implementation plan covers that rung only; one implementer (or a few sequential chunks) works
it in one git worktree; one reviewer checks the whole diff for under- and over-delivery and writes
`retro.md` when it passes; a worktree-merger lands it. Every project that uses the plugin gets the
new format, and `ticket.py migrate` converts old epics.

Why: the epic flow spends tokens and wall-clock on per-task files, per-task reviews, points,
estimates, a builder check, a scope audit, a record and a retro writer. Agents also ship features
nobody agreed to. The user wants fewer tokens, faster delivery, the orchestrator still only
orchestrating, git worktrees kept, no implementation without a human gate, and an explicit agreed
scope: what is discovered during implementation is recommended afterwards, never built.

## Scope ladder

Rungs are cumulative: each rung includes everything above it.

### Rung 1: MVP - new docs flow on the old scaffolding

- 1.1: start-development rewritten to discovery, plan.md with a scope ladder, one gate,
  implementation-plan.md, one implementer, one whole-diff reviewer, merge.
- 1.2: templates plan.md and implementation-plan.md; agents implementer and reviewer rewritten.

### Rung 2: retire the epic machinery

- 2.1: plan-run skill for the post-gate loop; plan-writer agent replaces planner.
- 2.2: epic-* skills, planner, record-writer, retro-writer and scope-auditor deleted with their
  tests; ticket.py task-level commands retired.

### Rung 3: complete (agreed)

- 3.1: ticket.py kept as scaffolding and adapted to plans: create from template with the
  duplicate check, path, rename, claim (move in-progress creates the worktree), move done,
  worktrees, close (rebase plus fast-forward), reap.
- 3.2: the reviewer writes retro.md (went well, went wrong or could improve, recommendations) when
  the review passes; the closing message relays the recommendations.
- 3.3: `ticket.py migrate` converts every old epic (todo, in-progress, done) to plan.md plus
  implementation-plan.md (plus retro.md when there was a retro or record), keeping its phase
  folder; run on the ros2-lerobot-sverve-platform repo and on this repo, committed there.
- 3.4: every reference to the old flow updated: AGENTS.md, CLAUDE.md, READMEs, docs/harnesses.md,
  kept skills, housekeeping rule (and the generated AGENTS.md block), the user's global rule
  `~/.claude/rules/workbench-flow.md`.
- 3.5: major version bump with a CHANGELOG section (release.py), installed plugin cache refreshed.

## Agreed scope

Rung 3, with the user's modifications at the gate (binding, 2026-10-31):

- Keep ticket.py as scaffolding, adapted to the plan format; retire the task-level machinery
  (tasks, task status, points and actuals, deltas, questions, amend, task lint, roadmap). Each
  retired command is listed with its reason under Decisions.
- Keep the retrospective as part of review: the reviewer writes retro.md when the review passes.
- No points, no token or minute estimates, no record.md, no builder check.
- Migrate every epic of ros2-lerobot-sverve-platform docs/plans through `ticket.py migrate`, not by
  hand, keeping todo/in-progress/done placement.
- Version bump (major), CHANGELOG entry, installed plugin cache refreshed.
- One gate message may batch several plans, a section each with its own ladder; each plan gets
  its own worktree and merges the moment it is green.

## Non-goals

- No second gate on implementation-plan.md.
- No per-step reviewer, no scope auditor, no record, no builder check, no estimates of any kind.
- No backward-compatibility shims: old-format plan dirs are refused with a pointer to
  `ticket.py migrate`, never read by the new commands.
- No change to hooks' behaviour beyond the usage-recorder marker (D9), to the PR skills, to
  git-submodules-*, to component-add/remove, init or template-update.
- No change to ros2-lerobot-sverve-platform code; only its docs/plans and one stale MEMORY.md
  pointer.
- The goals of the todo epic `ticket-py-and-flow-fixes-fro` are not delivered here (see
  Recommendations in retro.md once done).

## Design

Flow (start-development, then plan-run):

1. Discovery: `start-discovery` lanes as subagents; research lenses chosen by the orchestrator and
   listed in plan.md Research. The orchestrator keeps brief paths, not contents.
2. Plan: `ticket.py check --title`, `ticket.py new --title --repos`, then one `plan-writer` (opus)
   fills plan.md and commits it as `docs(plan): <plan> plan`.
3. Gate: one message, one section per plan: path, what and why in two lines, the rungs one line
   each with the recommended rung, open questions numbered with recommended answers, lenses run or
   skipped, irreversible operations. "Pick a rung per plan and answer, or tell me what to change."
4. Implementation plan: the same plan-writer, continued with the user's answer verbatim, records
   Agreed scope and the answers in plan.md, sets `rung`, writes implementation-plan.md for that
   rung only and commits. No second gate.
5. plan-run: `ticket.py move <plan> in-progress` (refused unless `rung` is set and
   implementation-plan.md exists) creates the worktree; one `implementer` per chunk, sequential, in
   that tree, committing per step; one `reviewer` (sonnet) on `git diff <base>...HEAD`; at most two
   fix rounds by continuing the same agents with SendMessage; on pass the reviewer writes retro.md;
   one `worktree-merger` runs `ticket.py close` (meta) or the MR (component), which moves the plan
   to done; one closing message relays retro.md's recommendations.

File layout (every project):

```
docs/plans/<phase>/<plan>/plan.md                 what and why, scope ladder, agreed scope, decisions
docs/plans/<phase>/<plan>/implementation-plan.md  agreed rung only, chunks of steps, final verify
docs/plans/<phase>/<plan>/retro.md                written by the reviewer when the review passes
docs/plans/<phase>/<plan>/close.json              written by ticket.py close (meta mode)
```

`<phase>` is todo, in-progress or done. Worktree and branch are both named `<plan>` at
`<configdir>/worktrees/<plan>[/<repo>]`, the same naming the epic integration trees used, so live
trees of migrated in-progress epics carry over.

Template headings:

- `templates/plan.md`: frontmatter `title`, `repos`, `created`, `owner`, `rung`; sections
  `# <title>`, `## What and why`, `## Scope ladder` (`### Rung <n>: <MVP|...|complete> - <name>`,
  items `- <n>.<m>: <item>`), `## Agreed scope`, `## Non-goals`, `## Design`, `## Decisions`,
  `## Open questions` (`- Q<n>: <question> [recommended: <answer>]`, after the gate
  `[answer: <text>]`), `## Research`, `## Irreversible operations`.
- `templates/implementation-plan.md`: `# <title> implementation plan`, `## Agreed rung`,
  `## Approach`, `## Chunk <k>: <name> (model: <sonnet|opus>)` with steps `### S<n>: <title>`
  (fields Files, Covers, Test first, Change, Verify), `## Files to delete`, `## Final verify`,
  `## After merge`.
- `templates/retro.md`: `# <title> retro`, `## Review`, `## What went well`,
  `## What went wrong or could improve`, `## Recommendations` (three lists: discovered and not
  built, out-of-scope ideas, impossible at planning time; "none" when empty).

## Decisions

- D1: Skill names: `start-development` stays the entry point; new `plan-run` holds the post-gate
  loop, written once there. (my call)
- D2: `plan-writer` (opus) writes plan.md and, continued after the gate, implementation-plan.md;
  it commits its own files as `docs(plan): <plan> <event>` in the main checkout, which release.py
  already omits from the CHANGELOG. (my call)
- D3: ticket.py subcommands kept: `slug`, `new` (was new-epic), `check` (title near duplicates
  only), `path` (plan, implementation, retro, close), `rename` (todo only), `move` (in-progress,
  done), `worktrees`, `close`, `reap`, `migrate` (rewritten). Retired, each because it only served
  tasks or estimates: `new-task`, `tasks`, `task`, `amend`, `questions` (questions live in
  plan.md and are answered at the gate), `lint` (task lint; template tests pin the structure),
  `stage` and `review` (the review verdict is retro.md's existence), `actuals`, `deltas`, `retro`
  (generated tables), `roadmap` (task and blocker driven), `index` and `existing` (task file
  indexes). The epic `blockers` key is retired; ordering between plans is the orchestrator's.
  (my call)
- D4: the gate is mechanical too: `move <plan> in-progress` refuses unless plan.md `rung` is set
  and implementation-plan.md exists; `close` and `move done` refuse unless retro.md exists.
- D5: the worktree-merger owns the merge: it runs `ticket.py close <plan> --verify '<final
  verify>'` in meta mode (resolving a rebase conflict in the plan tree and rerunning close) and the
  push, MR, watch and merge in component mode, then `ticket.py move <plan> done`. The orchestrator
  never merges. (my call)
- D6: the reviewer gains Write for exactly one file, retro.md at `ticket.py path <plan> retro` in
  the main checkout; ticket.py commits it with the move to done. (my call)
- D7: chunks: implementation-plan.md groups steps into `## Chunk` sections with a model each; a
  small plan has one chunk. Chunks run sequentially in the same tree; a fix round continues the
  implementer whose chunk owns the files, else the last one.
- D8: over-delivery is a reviewer finding like under-delivery: a change no step and no agreed item
  covers is removed in a fix round and may become a recommendation. Simplifying code a step
  already touches, behaviour unchanged, is not over-delivery.
- D9: the agent-usage-recorder hook stays (hooks are kept); its marker becomes
  `[wb <plan>/<role>]` with roles plan, impl, review, merge, and records carry `plan` and `role`.
  `scripts/lib/calibration.py` and the agent_usage backfill and aggregation used only by retired
  commands are deleted. (my call)
- D10: migrate mapping: README brief and description to What and why; README goals become one rung
  `Rung 1: agreed scope (migrated)`. In-progress and done plans get `rung: "1"` and an Agreed scope
  saying so. Todo plans get `rung: ""` and Agreed scope "not agreed yet", so each passes the new
  gate before it can be claimed (no implementation without a human gate); their migrated steps
  are a draft the plan-writer revises after the gate. Non-goals kept; design.md
  Decisions, Open questions, Research (plus Research inputs) and Irreversible operations mapped to
  their sections; every other README or design.md section kept verbatim under
  `## Migrated notes` as `### <file>: <heading>`, except README `## Time` (estimates are retired);
  approvals.json kept as a list there. Tasks become one chunk of steps in dependency order, each
  with its status, files, verify, verified head and every body section verbatim; rulings.json
  becomes `## Rulings (migrated)` in implementation-plan.md. RETRO.md's Retro table and
  Improvements map to retro.md's sections (its generated points tables are dropped); record.md is
  kept verbatim under `## Delivery record (migrated)` in retro.md. Old files are `git rm`ed in the
  same `chore(ticket): <plan> migrate` commit. close.json stays. (my call)
- D11: this repo's own old epics under docs/plans are migrated too, otherwise the new ticket.py
  refuses them. (my call)
- D12: after the ros2 migration commit, ros2 main is pushed, because that repo's CLAUDE.md
  mandates test, commit, push; this repo's main is never pushed (the user's call). (my call)
- D13: retirement pins assert on `git ls-files`, and one test pins that no plugin doc outside
  `references/tickets.md` and the CHANGELOG names the retired skills, agents or the word epic.
- D14: phases keep their numbers where kept skills cite them: phase 1 is discovery in every doc.

## Open questions

- Q1: Replace the epic flow with plan.md plus implementation-plan.md? [answer: yes, rung 3]
- Q2: Keep ticket.py? [answer: yes, as scaffolding adapted to plans; task machinery retired]
- Q3: Keep the retrospective? [answer: yes, written by the reviewer when the review passes]
- Q4: Migrate existing epics? [answer: every epic in ros2 docs/plans, via ticket.py migrate]
- Q5: Batch several plans in one gate? [answer: yes, a section and a worktree each]
- Q6: A session may still be running epic-run on ros2's in-progress epic
  `realsense-d435-head-switchov` when the migration runs. [recommended: the post-merge agent checks
  the tree is clean with no commit in the last 30 minutes, and stops to ask if not]

## Research

- start-discovery: skipped as subagents; the planner read the plugin source directly (ticket.py,
  ticket_cmds, every flow skill, agent and test, both repos' docs/plans). Findings are in this plan
  and the implementation plan.
- research-code-internal, research-code-external, research-papers, research-docs: skipped, the
  change reshapes the plugin's own docs and scripts with no new library or algorithm.
- Facts probed: `claude plugin marketplace update <name>` and `claude plugin update
  <plugin>@<marketplace>` exist (restart or `/reload-plugins` applies); release.py bumps
  plugin.json, marketplace.json and CHANGELOG and judges a deleted skill dir as major; ros2 tests
  exclude `docs/plans/**`; ros2 has 27 epics (5 todo, 3 in-progress, 19 done) in an older format
  (approvals.json, rulings.json, record.md, no RETRO.md); this repo has 10.

## Irreversible operations

- `git rm` of old epic files in both repos: recoverable from git history; dry-run first.
- Push of ros2 main after its migration (D12).
- Release tag v3.0.0 created locally; not pushed.
