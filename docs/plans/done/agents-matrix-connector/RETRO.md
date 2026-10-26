# agents matrix connector retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| mxc scaffold and cli | 2 | 2 | 8 | 2 | 542616 | 436547 |
| access policy engine | 3 | 3 | 14 | 8 | 895472 | 434368 |
| matrix client and fake hs | 5 | 5 | 14 | 7 | 1883475 | 1326880 |
| mxc common session names | 2 | 1 | 8 | 1 | 535073 | 158341 |
| mxc schema migrations | 2 | 2 | 8 | 7 | 542616 | 886861 |
| mxc settings model | 2 | 2 | 8 | 2 | 542616 | 365053 |
| room and event discovery | 3 | 3 | 14 | 2 | 895472 | 219920 |
| directory repository | 3 | 3 | 14 | 3 | 895472 | 538798 |
| inbound queue repository | 3 | 3 | 14 | 2 | 895472 | 456181 |
| rules and settings repo | 2 | 2 | 8 | 2 | 542616 | 367266 |
| runs and outbound repo | 3 | 3 | 14 | 2 | 895472 | 565477 |
| api rooms and users | 3 | 3 | 14 | 4 | 895472 | 1146154 |
| chat prompt render | 1 | 1 | 5 | 1 | 689196 | 203559 |
| matrix sync loop | 5 | 5 | 14 | 18 | 1883475 | 2841808 |
| sync limited timeline backfill | 3 | 3 | 6 | 7 | 849076 | 1427934 |
| reply tracker | 5 | 5 | 14 | 8 | 1883475 | 2555962 |
| api rules and settings | 3 | 3 | 14 | 4 | 895472 | 1003544 |
| dispatch worker | 5 | 5 | 14 | 8 | 1883475 | 2561179 |
| mxc openapi and readme | 2 | 2 | 8 | 4 | 542616 | 1311502 |
| mxc service entrypoints | 3 | 3 | 14 | 5 | 895472 | 1275430 |
| mxc chart workloads | 3 | 3 | 14 | 6 | 895472 | 942728 |
| mxc dockerfile and ci | 2 | 2 | 8 | 2 | 542616 | 368146 |
| mxc e2e api | 8 | 5 | 18 | 11 | 2172985 | 1989244 |
| mxc operations docs | 1 | 1 | 5 | 3 | 689196 | 694036 |
| mxc chart network | 2 | 2 | 8 | 3 | 542616 | 641082 |
| matrix identity spoofing guards | 3 | 3 | 6 | 10 | 937864 | 2845183 |
| review cleanups | 2 | 2 | 5 | 8 | 531208 | 793921 |
| Total | 81 | 77 | 291 | 140 | 25796058 | 28357104 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| mxc scaffold and cli | 0 | 0.25 | 0.80 |
| access policy engine | 0 | 0.57 | 0.49 |
| matrix client and fake hs | 0 | 0.50 | 0.70 |
| mxc common session names | -1 | 0.12 | 0.30 |
| mxc schema migrations | 0 | 0.88 | 1.63 |
| mxc settings model | 0 | 0.25 | 0.67 |
| room and event discovery | 0 | 0.14 | 0.25 |
| directory repository | 0 | 0.21 | 0.60 |
| inbound queue repository | 0 | 0.14 | 0.51 |
| rules and settings repo | 0 | 0.25 | 0.68 |
| runs and outbound repo | 0 | 0.14 | 0.63 |
| api rooms and users | 0 | 0.29 | 1.28 |
| chat prompt render | 0 | 0.20 | 0.30 |
| matrix sync loop | 0 | 1.29 | 1.51 |
| sync limited timeline backfill | 0 | 1.17 | 1.68 |
| reply tracker | 0 | 0.57 | 1.36 |
| api rules and settings | 0 | 0.29 | 1.12 |
| dispatch worker | 0 | 0.57 | 1.36 |
| mxc openapi and readme | 0 | 0.50 | 2.42 |
| mxc service entrypoints | 0 | 0.36 | 1.42 |
| mxc chart workloads | 0 | 0.43 | 1.05 |
| mxc dockerfile and ci | 0 | 0.25 | 0.68 |
| mxc e2e api | -3 | 0.61 | 0.92 |
| mxc operations docs | 0 | 0.60 | 1.01 |
| mxc chart network | 0 | 0.38 | 1.18 |
| matrix identity spoofing guards | 0 | 1.67 | 3.03 |
| review cleanups | 0 | 1.60 | 1.49 |

- MdAPE points: 0.0%
- MdAPE minutes: 166.7%
- MdAPE tokens: 40.5%
<!-- retro:generated:end -->

## Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

| Went well | Went bad / could be improved |
|---|---|
| ... | ... |

## Improvements

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.
