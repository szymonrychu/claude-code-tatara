# The approval ledger

Read from the gate and from Phase 4 of `start-development`. The ledger is the list of
everything the user approved at the gate, each item with an id, so the lint, the
workflow, the scope audit and the record all check the same items by id.

## Shape

A JSON array at `<epic dir>/approvals.json` (`ticket.py path <epic> approvals`), one entry per item
discussed:

```json
[
  {
    "id": "A",
    "text": "Approved means fully delivered: the record shows a status per item.",
    "decisions": ["D1", "D4"],
    "tasks": ["add-gateway", "write-docs"],
    "status": "approved"
  }
]
```

- `id` - short and stable; findings, the audit and the record name the item by it.
- `text` - what the user approved, in their terms, non-empty.
- `decisions` - the design doc's `### D<n>:` decisions that deliver it.
- `tasks` - the task slugs that deliver it (a task slug is its id).
- `status` - `approved`. Nothing else is planned.

`ticket.py decide <epic> <approval_id> <text> --tasks <slugs>` records a gate answer into the ledger and design:
it writes the approval entry and the design decision in one commit. Use it instead of editing both by hand.

## The gate writes it

Before the gate, write the ledger at `<epic dir>/approvals.json`. Gate item 1 shows it. Approving the gate message
approves every entry by id. An item the user strikes leaves the ledger, the design
and the plan; it is never kept as later.

## The lint

`validate-tasks.mjs --epic <epic dir>` must print `ok`; it reads the approvals ledger, the task
files and design.md from the epic dir. It fails with one line per
problem:

- `approvals: duplicate id <id>`
- `approvals: item <id> has empty text`
- `approvals: item <id> maps to no task`
- `approvals: item <id> names unknown task <task>`
- `approvals: item <id> has status <status>, only approved items are planned`
- `approvals: item <id> names no decision`
- `approvals: item <id> names unknown decision <D>`
- `approvals: design decision <D> is covered by no approved item`

A legacy dated-file run lints with the older `--approvals` flag instead. It also runs plan-execute's own validation of `{ id, text, tasks }`.

## What plan-execute does with it

Pass the entries this run delivers as `approvals: [ { id, text, tasks }, ... ]`.

- The implementer and every fixer of a mapped task see the item in their prompt. A
  `undelivered` entry on such a task is an `Approved item` finding: approved items cannot
  be left undelivered inside the run.
- An item can span several tasks. Each prompt says "Your share of it is your requirement
  below; the rest is delivered by tasks <other ids>. Do not list their parts in
  `undelivered`." An `undelivered` entry that names another task of the run, or a path
  another task owns, is not a finding: it moves to `misattributed` and the run goes on.
- The only accepted stop short is `blocked` on a deliverable: an external blocker no
  agent in the run can clear, with `reason` and `whoCanClear`. The run's `blocked`
  entries carry the `approvals` ids they hold up.
- The scope audit gets the ledger under `=== APPROVED ITEMS (the ledger) ===` and
  reports `{ id, landed, evidence }` per item; an item not landed is an `Approved item`
  gap on its tasks.
- The return carries `approvals[].status` per entry, worst first: `blocked` when a
  mapped task is blocked, `escalated` when one escalated, `unverified` when one has no
  verification on its HEAD, otherwise `delivered`. `finished` is true only when every
  entry is `delivered`.

## The record

`templates/record.md` puts an approvals table under `## Planned vs built`: id, text,
decisions, tasks, status, from the run's `approvals` return value. A `blocked` row names
who can clear it. An entry absent from the return is `unknown`.

## Orchestrator rules

- No "later" parking: an approved item is delivered or escalated as a named blocker.
  A status other than `delivered` is the first thing to act on when the run returns
  (`references/run-handback.md`).
- An idea outside the approved list goes to the user in one line, after the record.
- A struck item leaves every document: the ledger, the design and the plan.

## Statuses

| Status | Means |
|---|---|
| `delivered` | every mapped task verified on its HEAD, nothing blocked or escalated |
| `blocked` | a mapped task stopped on an external blocker; the record names `whoCanClear` |
| `escalated` | a mapped task escalated; judge it like any escalation |
| `unverified` | a mapped task has no verification on its HEAD; re-run it through a fresh verifier |
