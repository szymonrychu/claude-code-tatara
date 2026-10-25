# <Topic> retro

<!-- retro:generated:begin -->
## Tasks

Written by `ticket.py retro <epic>`: one row per task in delivery order (the `task <slug> done` commits, oldest first; tasks never marked done follow in dependency order) with points (estimate), points (post-delivery), minutes (expected), minutes (actual), tokens (expected), tokens (actual), and a totals line. A value the task file and the `.logs/agents` records do not give reads `not recorded`.

## Deltas

Written by `ticket.py retro <epic>`: per task the points difference (post-delivery - estimate) and the minutes and tokens ratios (actual / expected), then the MdAPE per metric.
<!-- retro:generated:end -->

## Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

| Went well | Went bad / could be improved |
|---|---|
| ... | ... |

## Improvements

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.
