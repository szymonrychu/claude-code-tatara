---
title: Epic integration worktrees
blockers: []
stage: review
owner: Szymon Richert
repos: [workbench]
created: 2026-10-21
---

# Epic integration worktrees

## Project brief

What: Per-epic integration worktrees and <epic>-<task> task branches managed with plain git worktree
How: ticket.py creates the epic integration tree at claim, task trees fork from and land on it, plan-execute diffs against it, move done merges it to main and sweeps every tree
Why: tasks currently land straight on main, so dependents' diffs carry dependency text and the epic has no single tested unit to merge

## Description

The workbench flow should own its git worktrees with plain `git worktree` commands and give every epic its own integration worktree. Today every task forks from main and lands straight on main. The `<epic>` integration branch the docs describe is only created by hand in component mode and never in meta mode. Task trees are named `<epic>--<task>`, and nothing merges an epic back to main and cleans up as a single step.

Requested by the user on 2026-10-21:
1. Skills use `git worktree` commands, never the harness's built-in worktree feature.
2. When an epic starts, it creates its own integration worktree named `<epic>`. Task branches are named `<epic>-<task>`, start from the epic integration branch and merge back into it. Every agent working on a task shares that task's worktree.
3. Once the epic is delivered and fully tested, its integration worktree merges back to main, and then every epic and task worktree is cleaned up.

## Goals

- No skill, agent, workflow or generated harness file uses or instructs the harness built-in worktree feature (Claude Code `--worktree`, EnterWorktree/ExitWorktree, Agent `isolation: "worktree"`, WorktreeCreate/WorktreeRemove hooks); guard tests pin this.
- Starting an epic (`ticket.py move <epic> in-progress`) creates the integration worktree `<epic>` on branch `<epic>` in meta mode (superrepo) and component mode (one per repo in scope), with `git worktree`.
- Task worktrees and branches are named `<epic>-<task>`, fork from the `<epic>` branch, and land back on it; names cannot collide across epics.
- Every role on a task (implementer, fixers, verifier, reviewers, forward-merge) works in that task's one worktree.
- Verifier and reviewer diffs are taken against the epic branch, so a dependent's diff never contains its dependencies' text.
- When the epic passes review and the full suite, the integration branch merges into main (meta mode: rebase plus fast-forward locally; component mode: through the MR as today), and every epic and task worktree and branch is removed.
- Docs (README, plugin README, start-development and its references, worktree skills, harness fallback) describe exactly this lifecycle; every test that pinned the old naming or base is updated.

## Non-goals

- Changing the personal plugin at ~/Documents/claude-infra-plugin (template only).
- Changing where worktrees live (they stay under the resolved `<configdir>/worktrees/`).
- Pushing to remotes or opening MRs differently from today's phase 6.

## Time

Estimate: 1370 min | Actual: 0 min | Remaining estimate: 0 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-22)

Epic review, phase 5, over 35390a5..main (docs/plans and docs/research excluded).

- Scope audit (scope-auditor, sonnet): every approval A1-A4, Q1, Q2, V-A..V-I has evidence in the files; 120 test ACs located, 21 command ACs pass. Two gaps, both fixed: single-hyphen-names AC3 cited a removed test (929737a), duplicate LEGACY_SEP in ticket.py (close-entry-docs).
- Epic review (reviewer, sonnet): worktree-merger.md and worktree-merge SKILL.md offered a direct merge.py epic close that bypassed ticket.py close's gates; fixed in close-entry-docs. Duplicate LEGACY_SEP, same fix. No other cross-task drift.
- Security review (security-researcher, sonnet): no critical or high. MEDIUM Sweep trusted frontmatter branch/worktree (could delete main); LOW merge_back unvalidated --name; LOW unquoted land prompt flags. All fixed in sweep-guard, hand-verified on 0c24045 (TDD revert red then green, AC1-AC5 met).
- Full suite: mise run test and mise run lint green on main after every landing (last: 2647 assertions, all checks passed).
- Accepted rulings: fork-point-diffs and forward-merge-via-epic (false-positive parking flag on a state-describing comment), sweep-guard (verifier --prev-head unknown crash). Dropped duplicate discovered task on verifier timeouts (covered by epic flow-speed-and-token-optimiz).
