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

- Commands only, the epic-migrate skill's sequence with the integration tree's ticket.py: `WT=<integration tree>`, `TK="python3 $WT/plugins/workbench/skills/start-development/scripts/ticket.py"`, run from the main checkout (`--root` defaults to main's docs/plans there).
- Writes, on main only: docs/plans/done/<epic>/tasks/*.md and docs/plans/done/<epic>/RETRO.md of the six done epics, in `chore(ticket): <epic> migrate` and `chore(ticket): <epic> retro` commits; `.logs/agents` records (gitignored).

## Expected outcome

The six done epics are on the points scheme with a filled RETRO.md each, `deltas --all --buckets` shows calibrated buckets, and a rerun changes nothing.

## Steps

1. Orchestrator, main checkout, clean tree: `$TK migrate --all --dry-run`; read the plan per epic (points, expected, actuals only where a legacy number, Notes line or matched transcript exists; folded roles per Q1's answer). On a refusal, stop and report the problems.
2. `$TK migrate --all`; note the `retro-writer: <epic>` lines (expected: the five old epics; the bootstrap epic's Retro is already filled).
3. Per listed epic: dispatch a general-purpose agent on sonnet told to follow `$WT/plugins/workbench/agents/retro-writer.md` (the `workbench:retro-writer` type loads only after /reload-plugins on main) with the epic slug and its record.md; then `$TK retro <epic>`, which commits the filled RETRO.md.
4. `$TK deltas --all --buckets`; record which buckets left the seed.
5. Run AC1 to AC7 from the integration tree, then the verify `mise run test && mise run lint` there; quote each summary line.

## Notes

- Estimate: 5 points: no code, but six epics, five retro-writer dispatches and a full-suite verify.
- Writer rule (references/tickets.md): only the orchestrator writes tickets, only through ticket.py, only in the main checkout; the commits land on main like every ticket commit during an epic, while the code stays on the integration branch until close. Open question Q2 in design.md confirms this at the gate.
- `files` lists the six epic dirs because the task rewrites every task file and the RETRO.md under each.
- approvals.json, rulings.json, record.md, close.json, README.md and design.md must stay unchanged (migrate-command AC4); check `git show --stat` of each migrate commit.
- housekeeping-rules-estimates RETRO.md: its Retro and Improvements stay byte for byte; only its generated block changes (points and expected values filled).
- The verify is the full gate on purpose: this is the epic's last task.
