---
title: ticket.py and flow fixes from tatara sessions
blockers: []
stage: build
owner: ""
repos: [workbench]
created: 2026-10-25
---

# ticket.py and flow fixes from tatara sessions

## Project brief

What: Fix the ticket.py, lint, hook, watch and verify-guidance issues three claude-code-tatara sessions hit on 2026-10-25.
How: ticket.py subcommands and lint changes test-first, a port of tatara 316e340, and reviewer, implementer and planner guidance edits.
Why: Each issue cost a manual workaround (hand-copied task bodies, git revert of a claim, dropped cross-epic deps, unread exit codes) in a real run.

## Description



## Goals

- Port claude-code-tatara 316e340: the ticket.py overlap check compares (repo, path) pairs, meta counts as the superrepo, so pyproject.toml, uv.lock, openapi.json no longer collide across repos.
- Epic slugs are no longer silently truncated at 28 chars mid-word ("-depl"): raise the cap or cut at a word boundary, and print a warning naming the final slug.
- new-task takes every body section from files (Requirement, AC, Interfaces, Expected outcome, Steps, Notes), so no template placeholder survives; tasks and amend no longer fail with "empty Steps" on a fresh task.
- amend can replace every body section and the frontmatter fields (value, files, depends_on, model), and commits the result itself.
- A move-task command moves a task between epics with its full body, re-lints both epics and commits.
- lint accepts depends_on and Decision coverage rows naming a task in another epic (qualified epic/task), so an epic can be split without dropping deps.
- A command edits an epic README frontmatter (repos, blockers) and its Goals / Non-goals; after a split, move no longer reuses integration trees for repos the epic no longer lists.
- An unclaim command returns an in-progress epic to todo without a manual git revert.
- `ticket.py tasks` reports todo vs in-progress per task correctly right after a claim.
- ticket.py stops printing stale-worktree warnings for done epics on every call (once, or only from a dedicated command).
- ticket.py writes no zeroed "Time" lines into tracked files.
- pullrequests-watch --deploy sees a GitHub push run that is in progress (no "no pipeline launched" within the grace window).
- Verify commands keep pytest's count line: the planner and lint reject a `-q` that doubles a `-q` in addopts, and reviewer and implementer guidance requires quoting the "N passed" summary line.
- Reviewer and implementer guidance captures exit codes portably (zsh has no PIPESTATUS): `cmd; echo exit=$?` or `set -o pipefail`, never PIPESTATUS.
- lint flags `\b` inside `git grep -E` AC evidence (vacuous on macOS) and the planner uses `git grep -w` instead.

## Non-goals

- Component-specific issues reported by the same sessions: agents_common pytest11 double registration, testcontainers on a full Docker disk, a stale editable .pth in a component .venv.
- Relaxing the guard hook's block on file-scoped `git restore`: it is deliberate.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
