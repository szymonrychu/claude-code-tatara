# agents-schedule microservice retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| scaffold project and cli | 1 | 1 | 6 | 2 | 750000 | 396283 |
| cron expressions | 1 | 1 | 5 | 2 | 750000 | 232787 |
| schedule settings model | 1 | 1 | 5 | 2 | 750000 | 319893 |
| schema migrations | 1 | 1 | 6 | 2 | 750000 | 388304 |
| runs repository | 1 | 2 | 5 | 4 | 750000 | 911884 |
| schedules repository | 1 | 1 | 5 | 2 | 750000 | 243936 |
| run dispatcher | 1 | 3 | 5 | 8 | 750000 | 2348483 |
| run outcome tracker | 1 | 2 | 5 | 3 | 750000 | 805886 |
| scheduler loop | 1 | 3 | 5 | 4 | 750000 | 683531 |
| ignored runs finished at | 1 | 1 | 5 | 1 | 673202 | 202047 |
| schedules api routes | 1 | 2 | 6 | 4 | 750000 | 1046729 |
| runs api routes | 1 | 1 | 6 | 2 | 750000 | 451307 |
| api docs and openapi | 1 | 2 | 6 | 3 | 750000 | 854267 |
| service entrypoints | 1 | 2 | 5 | 3 | 750000 | 575230 |
| dockerfile and ci | 1 | 1 | 6 | 2 | 750000 | 429054 |
| helm chart | 1 | 2 | 6 | 2 | 750000 | 432388 |
| chart ingress and test hook | 1 | 1 | 6 | 2 | 750000 | 420519 |
| kind e2e api | 1 | 3 | 6 | 6 | 750000 | 1908072 |
| epic review fixes | 2 | 2 | 6 | 5 | 494911 | 544297 |
| ci image checks and worker test flake | 1 | 1 | 5 | 4 | 671138 | 297736 |
| e2e two worker failure | 2 | 2 | 5 | 5 | 502921 | 1326060 |
| release v0.1.0 | 1 | 1 | 5 | 8 | 750000 | 300650 |
| Total | 24 | 36 | 120 | 76 | 15842172 | 15119343 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| scaffold project and cli | 0 | 0.33 | 0.53 |
| cron expressions | 0 | 0.40 | 0.31 |
| schedule settings model | 0 | 0.40 | 0.43 |
| schema migrations | 0 | 0.33 | 0.52 |
| runs repository | +1 | 0.80 | 1.22 |
| schedules repository | 0 | 0.40 | 0.33 |
| run dispatcher | +2 | 1.60 | 3.13 |
| run outcome tracker | +1 | 0.60 | 1.07 |
| scheduler loop | +2 | 0.80 | 0.91 |
| ignored runs finished at | 0 | 0.20 | 0.30 |
| schedules api routes | +1 | 0.67 | 1.40 |
| runs api routes | 0 | 0.33 | 0.60 |
| api docs and openapi | +1 | 0.50 | 1.14 |
| service entrypoints | +1 | 0.60 | 0.77 |
| dockerfile and ci | 0 | 0.33 | 0.57 |
| helm chart | +1 | 0.33 | 0.58 |
| chart ingress and test hook | 0 | 0.33 | 0.56 |
| kind e2e api | +2 | 1.00 | 2.54 |
| epic review fixes | 0 | 0.83 | 1.10 |
| ci image checks and worker test flake | 0 | 0.80 | 0.44 |
| e2e two worker failure | 0 | 1.00 | 2.64 |
| release v0.1.0 | 0 | 1.60 | 0.40 |

- MdAPE points: 0.0%
- MdAPE minutes: 83.3%
- MdAPE tokens: 70.8%
<!-- retro:generated:end -->

## Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

| Went well | Went bad / could be improved |
|---|---|
| ... | ... |

## Improvements

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.
