---
title: ticket.py and flow fixes from tatara sessions
repos: [workbench]
created: 2026-10-25
owner: ""
rung: ""
---

# ticket.py and flow fixes from tatara sessions

## What and why

What: Fix the ticket.py, lint, hook, watch and verify-guidance issues three claude-code-tatara sessions hit on 2026-10-25.
How: ticket.py subcommands and lint changes test-first, a port of tatara 316e340, and reviewer, implementer and planner guidance edits.
Why: Each issue cost a manual workaround (hand-copied task bodies, git revert of a claim, dropped cross-epic deps, unread exit codes) in a real run.

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: Port claude-code-tatara 316e340: the ticket.py overlap check compares (repo, path) pairs, meta counts as the superrepo, so pyproject.toml, uv.lock, openapi.json no longer collide across repos.
- 1.2: Epic slugs are no longer silently truncated at 28 chars mid-word ("-depl"): raise the cap or cut at a word boundary, and print a warning naming the final slug.
- 1.3: new-task takes every body section from files (Requirement, AC, Interfaces, Expected outcome, Steps, Notes), so no template placeholder survives; tasks and amend no longer fail with "empty Steps" on a fresh task.
- 1.4: amend can replace every body section and the frontmatter fields (value, files, depends_on, model), and commits the result itself.
- 1.5: A move-task command moves a task between epics with its full body, re-lints both epics and commits.
- 1.6: lint accepts depends_on and Decision coverage rows naming a task in another epic (qualified epic/task), so an epic can be split without dropping deps.
- 1.7: A command edits an epic README frontmatter (repos, blockers) and its Goals / Non-goals; after a split, move no longer reuses integration trees for repos the epic no longer lists.
- 1.8: An unclaim command returns an in-progress epic to todo without a manual git revert.
- 1.9: `ticket.py tasks` reports todo vs in-progress per task correctly right after a claim.
- 1.10: ticket.py stops printing stale-worktree warnings for done epics on every call (once, or only from a dedicated command).
- 1.11: ticket.py writes no zeroed "Time" lines into tracked files.
- 1.12: pullrequests-watch --deploy sees a GitHub push run that is in progress (no "no pipeline launched" within the grace window).
- 1.13: Verify commands keep pytest's count line: the planner and lint reject a `-q` that doubles a `-q` in addopts, and reviewer and implementer guidance requires quoting the "N passed" summary line.
- 1.14: Reviewer and implementer guidance captures exit codes portably (zsh has no PIPESTATUS): `cmd; echo exit=$?` or `set -o pipefail`, never PIPESTATUS.
- 1.15: lint flags `\b` inside `git grep -E` AC evidence (vacuous on macOS) and the planner uses `git grep -w` instead.

## Agreed scope

not agreed yet

## Non-goals

- Component-specific issues reported by the same sessions: agents_common pytest11 double registration, testcontainers on a full Docker disk, a stale editable .pth in a component .venv.
- Relaxing the guard hook's block on file-scoped `git restore`: it is deliberate.

## Design

none recorded in the epic format

## Decisions

none recorded in the epic format

## Open questions

none

## Research

none recorded in the epic format

## Irreversible operations

none

## Migrated notes

### README.md: Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
