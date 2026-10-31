---
title: "Superpowers-based plan flow replaces the workbench flow"
repos: [claude-code-tatara]
created: "2026-10-31"
owner: ""
rung: ""
---

# Superpowers-based plan flow replaces the workbench flow

## What and why

What: replace the development flow of this workbench (start-development, start-discovery, plan-run, epic-*,
interrogate, start-debugging, start-review in `plugins/workbench`) with a flow built on the superpowers skills
(brainstorming, writing-plans, subagent-driven-development, using-git-worktrees, requesting-code-review,
finishing-a-development-branch, ...), vendored into this marketplace and adapted to the same principles the
workbench v3 flow just landed: plan.md with a scope ladder MVP..complete, one human gate that picks the rung, an
implementation plan for the agreed rung only, one implementer and one whole-diff reviewer (under AND over delivery),
at most 2 fix rounds, retro.md with recommendations, the orchestrator only orchestrates, models pinned per role.
Why: user request (2026-10-31): "replace existing flows in ~/Documents/claude-code-tatara and ~/Documents/infrastructure.
Use 'superpowers' plugin as base of the workflow". This repo is the marketplace both repos would load the flow from
(see D1), so it goes first; `~/Documents/infrastructure` plan `superpowers-plan-flow` is blocked on it.

## Scope ladder

Rungs are cumulative. Recommended: **Rung 3**.

### Rung 1: MVP - core flow switch

- 1.1: `plugins/superpowers/` vendored from superpowers 7.0.0 (`~/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0`):
  skills brainstorming, writing-plans, subagent-driven-development (with its prompts and scripts), using-git-worktrees,
  requesting-code-review (with code-reviewer.md), finishing-a-development-branch; upstream LICENSE kept verbatim plus a
  NOTICE naming the upstream version and what was changed.
- 1.2: brainstorming adapted: discovery by subagents (research opus), questions batched at ONE gate, its output is
  plan.md from the template (What and why, scope ladder MVP..complete with a recommended rung, Non-goals, Design,
  Decisions with `(my call)`, open questions each with a recommended answer, Research, Irreversible operations);
  its HARD-GATE becomes "nothing is built until the user picks a rung and answers".
- 1.3: writing-plans adapted: writes implementation-plan.md for the agreed rung only (chunks with a pinned model,
  steps with Files, Covers, Test first, Change, Verify); no second gate; the "Native / Subagent-driven" execution
  choice is removed (the orchestrator never implements).
- 1.4: subagent-driven-development adapted: one implementer per chunk, sequential in one worktree; one whole-diff
  reviewer (sonnet) checking under-delivery against every agreed item and over-delivery of anything no step covers,
  then quality; at most 2 fix rounds by continuing the same agents (replaces 5 rounds with model escalation);
  implementer reports `undelivered` (a finding) and `discovered` (recommended, never built); on a pass the reviewer
  writes retro.md with Recommendations; models set explicitly per the AGENTS.md ground rule 2 table.
- 1.5: finishing-a-development-branch adapted: no options menu after the gate; meta mode rebases and fast-forwards
  local main, component mode pushes and merges the PR the moment it is green, mergeable and review-clean.
- 1.6: plan lifecycle reused, not rebuilt: `ticket.py` and the templates plan.md, implementation-plan.md, retro.md
  move from `plugins/workbench/skills/start-development/` into `plugins/superpowers/` (docs/plans/{todo,in-progress,
  done}/<slug>/ layout unchanged).
- 1.7: `.claude-plugin/marketplace.json` registers `superpowers`; `.claude/settings.json` enables
  `superpowers@claude-code-tatara-workbench` and sets `superpowers@claude-plugins-official` and
  `workbench@workbench-template` to false (today two plugins named `workbench` load here).
- 1.8: workbench flow entry skills retired from `plugins/workbench`: start-development, start-discovery, plan-run,
  epic-run, epic-create, epic-task-create, epic-move, epic-migrate, epic-worktrees-remove, interrogate, and agent
  plan-writer; a retirement test asserts `git ls-files` returns nothing for each path.
- 1.9: AGENTS.md ground rule 1, CLAUDE.md "Claude Code only" and every tracked reference to a retired skill
  (plugins/workbench agents reviewer, worktree-merger, reuse-hunter; research-*, start-research, worktree-merge,
  pullrequests-review-loop SKILL.md; README.md; docs/harnesses.md; docs/claude-cloud.md) point at the new flow.
- 1.10: structure tests (pytest, `mise run test`): each vendored skill has frontmatter, LICENSE and NOTICE exist,
  no tracked file names a retired skill.

### Rung 2: debugging and review flows on superpowers too

- 2.1: vendor and adapt systematic-debugging, test-driven-development, verification-before-completion,
  receiving-code-review, dispatching-parallel-agents; retire start-debugging, debug, start-review, review (and their
  tests, replaced by structure tests of the vendored skills).
- 2.2: vendor using-superpowers and its SessionStart hook, rewritten to name this flow's entry and the user's rules
  (2 fix rounds, one gate, scope ladder) so a fresh session routes to it.
- 2.3: migrate every in-flight plan (2 in-progress, 12 todo in the epic README/design/tasks format) to plan.md with
  `ticket.py migrate`, one `chore(ticket)` commit each.

### Rung 3: complete - harness parity, sync and docs

- 3.1: other harnesses: the AGENTS.md rules block, `mise run harness-setup` skill emission and the docs/harnesses.md
  support matrix cover the vendored skills (superpowers 7.0.0 ships .codex-plugin, .opencode and per-harness tool references to reuse).
- 3.2: `template-update` excludes the retired flow paths so a template pull never reintroduces them; test.
- 3.3: `plugins/superpowers/UPSTREAM.md` plus a `mise run superpowers-diff <version>` task that diffs the vendored
  skills against a newer upstream release and prints the changed files (report only, never auto-applies); test.
- 3.4: README.md, docs/architecture.md, plugins/superpowers/README.md and a dated MEMORY.md entry; marketplace
  versions bumped (plugins/workbench major, its marketplace.json entry corrected from 2.0.0).

## Agreed scope

not agreed yet

## Non-goals

- The runtime of agent pods: claude-code-wrapper (`README.md` example config) requires `workbench@szymonrychu-workbench`
  and disables `superpowers@claude-plugins-official`; component code is not touched here (see Q5).
- The tooling skills stay in `plugins/workbench`: git-submodules-*, git-worktrees-commit/push, worktree-create,
  worktree-merge, pullrequests-*, start-research and research-*, handoff, release, component-*, init, template-update,
  hooks and the diagnostic agents; the packs workbench-infra/observability/secrets are untouched.
- Moving docs/plans to superpowers' `docs/superpowers/{specs,plans}` paths (D3).
- Changing `~/Documents/workbench` (the template); this plan only diverges this project from it.
- brainstorming's Visual Companion and writing-skills (not part of the flow).

## Design

- Plugin layout: `plugins/superpowers/{.claude-plugin/plugin.json,LICENSE,NOTICE,README.md,skills/<name>/,hooks/,
  scripts/}`; skills keep upstream names so the cross references `superpowers:<skill>` inside them resolve unchanged.
- Flow mapping (workbench v3 phase -> vendored skill):
  discovery + plan + gate -> brainstorming (its "Size the Work" table kept: a quick task skips the flow);
  implementation plan -> writing-plans; run -> subagent-driven-development + using-git-worktrees;
  review -> requesting-code-review (code-reviewer.md gains the under/over-delivery checklist and retro.md);
  land -> finishing-a-development-branch.
- Kept from upstream as written: SDD "Rulings, not stalls" and its four stop conditions (plus: an irreversible
  operation not listed at the gate stops the run), brainstorming's builder check (replaces interrogate), writing-plans'
  file-structure and task right-sizing sections.
- Reuse: `plugins/workbench/skills/start-development/scripts/ticket.py` (new, path, move, close, migrate, reap) and
  its templates; `plugins/workbench/agents/reviewer.md` checklist text for the whole-diff review;
  `plugins/workbench/skills/start-development/templates/retro.md`.
- Settings precedence: project `.claude/settings.json` `enabledPlugins` overrides the user-scope entries for this repo.
- Repo state at discovery: branch main, clean, 1 commit ahead of origin (`2773c82a`, not pushed); GitHub PR forge.

## Decisions

- D1: one vendored fork in this marketplace, consumed by both repos. Alternatives: (a) enable upstream
  `superpowers@claude-plugins-official` per project plus a thin overlay skill in each repo: cheapest and tracks
  upstream, but the user's rules (2 fix rounds, rung gate, retro, no Native option, model table) would live only as
  prose fighting upstream text such as SDD's 5-round escalation graph; (b) a fork per repo: duplicated upkeep.
  Chosen: fork here, because this repo is already a published marketplace (Q1).
- D2: the vendored plugin keeps the name `superpowers` (id `superpowers@claude-code-tatara-workbench`) so upstream
  cross references and future diffs stay small; the official plugin is disabled at project scope. Alternative: a new
  name such as `flow`, which needs every `superpowers:` reference rewritten. (my call)
- D3: plans stay in `docs/plans/{todo,in-progress,done}/<slug>/` with plan.md / implementation-plan.md / retro.md,
  not `docs/superpowers/...`; writing-plans already says user preferences override its default path. (my call)
- D4: ticket.py moves with the flow instead of being rewritten. (my call)
- D5: licensing: superpowers is MIT (c) 2025 Jesse Vincent; copying whole skills is allowed when the copyright and
  permission notice ship with them, hence LICENSE verbatim plus NOTICE. This repo's own LICENSE is MIT too.

## Open questions

- Q1: Host the vendored superpowers fork in this repo's marketplace and have ~/Documents/infrastructure load it from
  here (github source `szymonrychu/claude-code-tatara`)? [recommended: yes]
- Q2: Retire the debugging and review flows too (start-debugging, debug, start-review, review), replaced by
  systematic-debugging and requesting/receiving-code-review (rung 2)? [recommended: yes]
- Q3: Add one carve-out line to `~/.claude/rules/workbench-flow.md` (outside both repos): "repos whose
  .claude/settings.json enables superpowers@claude-code-tatara-workbench use superpowers:* as their flow; the table
  below does not apply there"? Without it the global rule redirects superpowers names to workbench. [recommended: yes]
- Q4: Keep the entry point named `superpowers:brainstorming` rather than adding a `start-development` alias?
  [recommended: yes]
- Q5: Leave the agent pods (claude-code-wrapper config: workbench required, superpowers disabled) on the workbench
  flow for now? [recommended: yes]

## Research

- research-code-internal: ran (grep over plugins/, scripts/, docs/, root docs): 34 files outside the retired skill dirs name a retired skill; tests
  `plugins/workbench/scripts/tests/test_retired_epic_flow.py`, `hooks/tests/test_no_retired_words.py` already pin
  retirements and are the pattern to follow.
- research-code-external: ran on superpowers 7.0.0: SDD fix loop is 5 rounds with model escalation
  (`subagent-driven-development/SKILL.md:75`), final review "most capable model" (`executing-plans/SKILL.md:241`),
  plans path `docs/superpowers/plans` (`writing-plans/SKILL.md:16`), spec approval HARD-GATE
  (`brainstorming/SKILL.md:179`), user instructions take precedence (`using-superpowers/SKILL.md:63`).
- research-docs: skipped, Claude Code plugin settings precedence is already relied on by this repo's settings.json.
- research-papers: skipped, no algorithmic core.
- ideas: adopted SDD "Rulings, not stalls"; adopted brainstorming builder check in place of interrogate; rejected
  executing-plans "Native" mode (orchestrator never implements); rejected SDD per-task reviewer (one whole-diff
  reviewer per plan).

## Irreversible operations

none: skill deletions are git-reversible; Q3 edits a file outside the repo, shown as a diff before writing.
