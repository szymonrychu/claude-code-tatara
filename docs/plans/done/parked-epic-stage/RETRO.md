# parked epic stage retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| park and unpark an in-progress epic | 3 | 3 | 6 | 32 | 940114 | 694281 |
| Total | 3 | 3 | 6 | 32 | 940114 | 694281 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| park and unpark an in-progress epic | 0 | 5.33 | 0.74 |

- MdAPE points: 0.0%
- MdAPE minutes: 81.2%
- MdAPE tokens: 35.4%
<!-- retro:generated:end -->

## Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

| Went well | Went bad / could be improved |
|---|---|
| Small, clean first pass: one task, review clean in round 0, no rework (points estimate 3, actual 3) | Planner task files leave Steps empty; `ticket.py tasks` and `amend` refuse empty Steps, so the orchestrator had to fill 21 Steps sections |
| | README goals left empty for lean epics |
| | Minutes ran 5.33x the estimate (32 actual vs 6 expected; MdAPE minutes 81.2%) |

## Improvements

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.

- Code: none.
- Delivered differently than expected: the implementer also edited the EPIC_STAGES literal in tests/test_ticket_files.py, outside the task's `files:` list (judged accurate by the reviewer).
- Tech debt introduced: none.
- Workflow: make the planner write Steps at task creation (or have `ticket.py new-task` reject empty Steps), and let lean epics skip README goals in lint instead of leaving them empty.
