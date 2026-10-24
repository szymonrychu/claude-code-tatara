---
name: epic-run
description: "Execute one planned epic: claim it, run its tasks in dependency order through one implementer and one reviewer each with at most two fix rounds, audit scope, close. Use after the gate of start-development or to run an epic planned in another session."
---

Runs the loop of start-development phase 4 (`../start-development/SKILL.md`, read it first; the loop is not
restated here). `<epic>` is the epic slug and `ticket.py` is
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py`, always run from the main checkout.

## Entry conditions

Stop and report the refusal if any fails:
- `ticket.py lint <epic>` prints ok.
- The epic is in `todo` or `in-progress` (a repeat claim reuses the tree).
- Main is clean and green.

## Run

1. Claim: `ticket.py move <epic> in-progress`; it creates the integration tree on branch `<epic>`.
2. List the order: `ticket.py tasks <epic>`. For each task, one at a time, dependencies first, note the tree HEAD
   (`git -C <tree> rev-parse HEAD`), then dispatch in the background:
   - `workbench:implementer` (model from the task file): the task file verbatim, the tree path, and the
     instruction that every command starts with `cd <tree>`.
   - On its return, `workbench:reviewer` (sonnet): the task file, the tree path, and the commit range
     `<start-head>..HEAD`.
3. Unmet conditions or findings: continue the same implementer with `SendMessage` (the findings, nothing else),
   then the same reviewer. At most two fix rounds.
4. Status after each task, from the main checkout:
   - clean: `ticket.py task <epic> <task> --status done --verified-head <head>`
   - open after the cap: `ticket.py task <epic> <task> --status escalated --note "<open findings>"`, then continue
     with tasks that do not depend on it.

## What comes back

- `undelivered` is a finding: send it back in a fix round.
- `discovered` becomes a new task in the same epic: `ticket.py new-task`, then lint again.
- `escalated` is yours to judge: sharpen the requirement (`ticket.py amend`) and run it again, or
  `workbench:interrogate` once. The epic cannot close while a task is not `done`.
- Never implement a task yourself and never merge a tree yourself.

## Exit

After the last task, hand back to start-development phases 5 to 7 (review, close or merge, record). End with
one closing message of three lines: what landed, how it was verified, what is next.
