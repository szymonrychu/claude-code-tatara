# parked epic stage retro

## Review

Migrated from the epic format.

### RETRO.md: Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

## What went well

- Small, clean first pass: one task, review clean in round 0, no rework (points estimate 3, actual 3)

## What went wrong or could improve

- Planner task files leave Steps empty; `ticket.py tasks` and `amend` refuse empty Steps, so the orchestrator had to fill 21 Steps sections
- README goals left empty for lean epics
- Minutes ran 5.33x the estimate (32 actual vs 6 expected; MdAPE minutes 81.2%)

## Recommendations

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.

- Code: none.
- Delivered differently than expected: the implementer also edited the EPIC_STAGES literal in tests/test_ticket_files.py, outside the task's `files:` list (judged accurate by the reviewer).
- Tech debt introduced: none.
- Workflow: make the planner write Steps at task creation (or have `ticket.py new-task` reject empty Steps), and let lean epics skip README goals in lint instead of leaving them empty.

## Delivery record (migrated)

### Asked

Let ticket.py park an in-progress epic so its unbuilt tasks stop reserving files in the cross-epic overlap check. Mechanism: a `parked` README stage set and cleared by `ticket.py stage`; `run_check` skips parked epics' tasks; lint and docs updated. Why: on 2026-10-27 the user put the incident and Matrix epics ahead of the parked slash-commands-from-chat epic, whose 18 unbuilt tasks blocked their new-task calls. README goals are empty (lean epic).

### Shipped

Meta mode, superrepo, base main, branch parked-epic-stage, closed by `ticket.py close`: 3bc9738e feat (4 files, +146/-5: ticket.py, test_ticket_park.py, tickets.md, test_ticket_files.py), 2965bf0d review pass, 02725c90 close. Epic review verdict: pass (2026-10-27); scope audit: all landed; whole-diff review equals the task review (one task). Close verify on main: `mise run test:plugin && mise run lint` passed. No MR/PR, no deploy (meta mode).

### Tasks

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| park-and-unpark-an-in-progre (sonnet, 3 points estimated, pointsActual 3) | done | 610c3b55b9a5d1797f767b19db8595c77f3b97e9 (not in the git log of main: the integration commits were squashed to 3bc9738e at close; not confirmable from git) | 0 (clean in round 0) | verify 41 passed; mise run test:plugin all green 2023 assertions; lint clean |

Files and notes agree on status, head and points. The implementer also updated the EPIC_STAGES literal in tests/test_ticket_files.py; the reviewer judged it accurate.

### Rulings

- Updating the EPIC_STAGES literal in tests/test_ticket_files.py (outside the task's `files:` list): accepted; the reviewer judged the test no longer accurate once `parked` became a stage. Cost if wrong: a test edited to pass would hide a regression in stage handling; low, the literal only mirrors the new stage list.
- Scope audit: all landed, no gap placed, no finding dropped. Cost if wrong: an unbuilt AC would ship unnoticed; low, ac1-ac7 are each pinned by a test or command.

### Discovered and blocked

none

### Not pushed

Everything is local-only on main: `git log --oneline origin/main..main` lists 133 commits, including 3bc9738e, 2965bf0d and 02725c90 of this epic and other epics' ticket commits. Branch parked-epic-stage no longer exists as a branch. The user pushes main (no push is part of a meta close).

### Lessons routed to

- Planner task files leave `## Steps` empty, and `ticket.py tasks` / `amend` refuse empty Steps (the orchestrator had to fill 21 Steps sections): add a check in `ticket.py new-task` (and its test) that fails or prompts when Steps is empty at creation; mechanical.
- Empty README goals for lean epics: add a lint rule in `ticket.py lint` that allows empty goals only when the epic has one task, or require a goals line at `new-epic`; mechanical.
- Verified head not resolvable after close (integration commits squashed): add to `ticket.py close` a check that records the verified heads and their mapping to the squashed commit in close.json; mechanical.
