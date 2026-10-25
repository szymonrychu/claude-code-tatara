---
title: Migrate this repo
status: todo
repo: workbench
value: "This repository's done epics carry the points scheme and a retro, so new estimates calibrate from real history"
files: [docs/plans/done/epic-integration-worktrees, docs/plans/done/flow-speed-and-token-optimiz, docs/plans/done/init-leaves-a-green-tree, docs/plans/done/lean-development-flow, docs/plans/done/template-update-skill-and-in, docs/plans/done/housekeeping-rules-estimates]
verify: "mise run test && mise run lint"
depends_on: [epic-migrate-skill, deltas-legacy-retired]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 57
expected_tokens: 3750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Migrate this repo

## Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

Constraint (verbatim): "Include a final task that runs the migration for real on this repository's docs/plans (all six done epics), commits via the skill's commands, and whose acceptance conditions check `ticket.py lint` ok, `ticket.py deltas --all --buckets` showing at least one bucket with source history or refit, and a RETRO.md in every done epic; its verify is the full `mise run test && mise run lint`. Note that the retro-writer agent type loads only after /reload-plugins; the task may use a general-purpose sonnet agent instructed to follow agents/retro-writer.md."

User decision (verbatim): "Q1 Scope: every epic under docs/plans (todo, in-progress, done); today that is the five old done epics plus the bootstrap epic housekeeping-rules-estimates; the two todo epics have no tasks yet."

User decision (verbatim): "Q8 RETRO.md for every old done epic: `ticket.py retro <epic>` for the measured tables, retro-writer (sonnet) fills Retro and Improvements from record.md and the deltas; the skill runs this per epic."

Design D13: The real run on this repository (my call; open question Q2 below) (verbatim):

The last task migrates this repository's docs/plans. Since only the orchestrator writes tickets and only
in the main checkout, the orchestrator runs it there with the integration tree's ticket.py
(`python3 <integration tree>/plugins/workbench/skills/start-development/scripts/ticket.py migrate --all
--root <main>/docs/plans`, after the dry run), the same way ticket commits land on main during any epic.
The retro-writer agent type loads only after `/reload-plugins` on main, so each retro-writer step is a
general-purpose sonnet agent told to follow the integration tree's agents/retro-writer.md. The task's
acceptance conditions run against main's docs/plans; its verify is the full `mise run test && mise run
lint`.

## Acceptance conditions

- AC1: `ticket.py lint` over main's docs/plans prints `lint: ok` [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; python3 plugins/workbench/skills/start-development/scripts/ticket.py lint --root "$P" | grep -qx 'lint: ok']
- AC2: `ticket.py deltas --all --buckets` over main's docs/plans shows at least one bucket with source history or refit [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; python3 plugins/workbench/skills/start-development/scripts/ticket.py deltas --all --buckets --root "$P" | grep -Eq '^\| [0-9]+ \| [0-9]+ \| [0-9]+ \| [0-9]+ \| (history|refit) \|$']
- AC3: every done epic on main has a tracked RETRO.md [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; for d in "$P"/done/*/; do git -C "$P" ls-files --error-unmatch "${d}RETRO.md" >/dev/null || exit 1; done]
- AC4: no done epic's RETRO.md still holds the template's Retro or Improvements placeholder [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; ! grep -l 'Filled by retro-writer' "$P"/done/*/RETRO.md]
- AC5: the migration is complete and idempotent: a dry run over main's docs/plans prints `migrate: nothing to change` [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; python3 plugins/workbench/skills/start-development/scripts/ticket.py migrate --all --dry-run --root "$P" | grep -qx 'migrate: nothing to change']
- AC6: main carries a `chore(ticket): <epic> migrate` commit for each of the six done epics [evidence: command:test "$(git log main --format=%s | grep -E '^chore\(ticket\): (epic-integration-worktrees|flow-speed-and-token-optimiz|init-leaves-a-green-tree|lean-development-flow|template-update-skill-and-in|housekeeping-rules-estimates) migrate$' | sort -u | wc -l | tr -d ' ')" -eq 6]
- AC7: main's docs/plans has no uncommitted change [evidence: command:P="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")/docs/plans"; test -z "$(git -C "$P" status --porcelain -- .)"]
- AC8: the full suite and lint pass [evidence: command:mise run test && mise run lint]

## Files

- `docs/plans/done/epic-integration-worktrees`
- `docs/plans/done/flow-speed-and-token-optimiz`
- `docs/plans/done/init-leaves-a-green-tree`
- `docs/plans/done/lean-development-flow`
- `docs/plans/done/template-update-skill-and-in`
- `docs/plans/done/housekeeping-rules-estimates`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
