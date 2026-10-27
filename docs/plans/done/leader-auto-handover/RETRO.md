# leader auto handover retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| wrapper compacting event | 2 | 2 | 6 | 26 | 546295 | 881354 |
| compaction status projection | 3 | 3 | 7 | 323 | 996161 | 2641899 |
| leadership auto handover | 5 | 5 | 11 | 18 | 1836811 | 1400013 |
| scale down staying peer | 3 | 3 | 7 | 8 | 996161 | 1678149 |
| web scale hint | 1 | 1 | 4 | 2 | 662742 | 375407 |
| claim hold and handover wake | 3 | 3 | 7 | 6 | 996161 | 1449605 |
| reconciler leader pod hold | 2 | 2 | 6 | 5 | 546295 | 715063 |
| leader changed reason | 2 | 2 | 6 | 5 | 546295 | 591802 |
| web leader reason | 3 | 3 | 7 | 3 | 996161 | 679096 |
| wrapper release 0.3.0 | 1 | 1 | 4 | 16 | 662742 | 302582 |
| orch wrapper pin 0.3.0 | 1 | 1 | 4 | 7 | 662742 | 363796 |
| smoke scale below leader | 3 | 3 | 7 | 21 | 996161 | 694284 |
| kind e2e auto handover | 3 | 3 | 7 | 21 | 996161 | 795251 |
| helmfile deploy pin | 2 | 2 | 6 | 5 | 546295 | 386185 |
| helmfile apply smoke | 5 | 3 | 11 | 3 | 1836811 | 245900 |
| smoke step7 per-wait deadlines | 2 | 2 | 5 | 20 | 546295 | 715527 |
| orch eligibility single source | 3 | 3 | 6 | 15 | 963314 | 900392 |
| Total | 44 | 42 | 111 | 504 | 15333603 | 14816305 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| wrapper compacting event | 0 | 4.33 | 1.61 |
| compaction status projection | 0 | 46.14 | 2.65 |
| leadership auto handover | 0 | 1.64 | 0.76 |
| scale down staying peer | 0 | 1.14 | 1.68 |
| web scale hint | 0 | 0.50 | 0.57 |
| claim hold and handover wake | 0 | 0.86 | 1.46 |
| reconciler leader pod hold | 0 | 0.83 | 1.31 |
| leader changed reason | 0 | 0.83 | 1.08 |
| web leader reason | 0 | 0.43 | 0.68 |
| wrapper release 0.3.0 | 0 | 4.00 | 0.46 |
| orch wrapper pin 0.3.0 | 0 | 1.75 | 0.55 |
| smoke scale below leader | 0 | 3.00 | 0.70 |
| kind e2e auto handover | 0 | 3.00 | 0.80 |
| helmfile deploy pin | 0 | 0.83 | 0.71 |
| helmfile apply smoke | -2 | 0.27 | 0.13 |
| smoke step7 per-wait deadlines | 0 | 4.00 | 1.31 |
| orch eligibility single source | 0 | 2.50 | 0.93 |

- MdAPE points: 0.0%
- MdAPE minutes: 66.7%
- MdAPE tokens: 40.6%
<!-- retro:generated:end -->

## Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

| Went well | Went bad / could be improved |
|---|---|
| ... | ... |

## Improvements

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.
