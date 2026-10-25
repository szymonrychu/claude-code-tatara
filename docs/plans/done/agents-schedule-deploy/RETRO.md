# agents-schedule deploy retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| helmfile schedule db release | 1 | 1 | 5 | 5 | 678580 | 387346 |
| schedule service token | 1 | 1 | 5 | 4 | 678580 | 265212 |
| smoke schedule check | 1 | 2 | 5 | 13 | 678580 | 910137 |
| web config schedules backend | 1 | 1 | 5 | 1 | 678580 | 226517 |
| web schedules api client | 1 | 1 | 5 | 3 | 678580 | 555608 |
| helmfile schedule release | 1 | 1 | 5 | 19 | 678580 | 875939 |
| web schedule form | 1 | 2 | 5 | 5 | 678580 | 865307 |
| web schedule runs list | 1 | 1 | 5 | 2 | 678580 | 468088 |
| web schedules page | 1 | 2 | 5 | 5 | 678580 | 992696 |
| web schedules menu entry | 1 | 1 | 5 | 2 | 678580 | 258058 |
| deploy schedule | 1 | 2 | 5 | 7 | 678580 | 799550 |
| Total | 11 | 15 | 55 | 66 | 7464380 | 6604458 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| helmfile schedule db release | 0 | 1.00 | 0.57 |
| schedule service token | 0 | 0.80 | 0.39 |
| smoke schedule check | +1 | 2.60 | 1.34 |
| web config schedules backend | 0 | 0.20 | 0.33 |
| web schedules api client | 0 | 0.60 | 0.82 |
| helmfile schedule release | 0 | 3.80 | 1.29 |
| web schedule form | +1 | 1.00 | 1.28 |
| web schedule runs list | 0 | 0.40 | 0.69 |
| web schedules page | +1 | 1.00 | 1.46 |
| web schedules menu entry | 0 | 0.40 | 0.38 |
| deploy schedule | +1 | 1.40 | 1.18 |

- MdAPE points: 0.0%
- MdAPE minutes: 61.5%
- MdAPE tokens: 31.6%
<!-- retro:generated:end -->

## Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

| Went well | Went bad / could be improved |
|---|---|
| ... | ... |

## Improvements

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.
