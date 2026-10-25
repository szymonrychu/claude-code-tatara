# agents-helmfile retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| scaffold repo | 1 | not recorded | 6 | not recorded | 750000 | not recorded |
| helmfile base | 1 | not recorded | 6 | not recorded | 750000 | not recorded |
| hook missing namespace | 1 | not recorded | 5 | 7 | 750000 | 1654691 |
| mise tasks | 1 | not recorded | 5 | not recorded | 750000 | not recorded |
| secrets bootstrap | 1 | not recorded | 6 | not recorded | 750000 | not recorded |
| db release | 1 | not recorded | 5 | 4 | 750000 | 560910 |
| orchestrator release | 1 | not recorded | 5 | 10 | 750000 | 1982025 |
| smoke script | 1 | not recorded | 5 | 7 | 750000 | 854683 |
| apply guard and hygiene | 1 | not recorded | 6 | 3 | 750000 | 462557 |
| db secret name from cnpg | 1 | not recorded | 6 | 3 | 750000 | 394558 |
| api allowlist pod gateways | 1 | not recorded | 5 | 3 | 750000 | 312768 |
| smoke session mcp check | 1 | not recorded | 5 | 6 | 750000 | 235329 |
| Total | 12 | not recorded | 65 | 43 (8 of 12 tasks) | 9000000 | 6457521 (8 of 12 tasks) |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| scaffold repo | not recorded | not recorded | not recorded |
| helmfile base | not recorded | not recorded | not recorded |
| hook missing namespace | not recorded | 1.40 | 2.21 |
| mise tasks | not recorded | not recorded | not recorded |
| secrets bootstrap | not recorded | not recorded | not recorded |
| db release | not recorded | 0.80 | 0.75 |
| orchestrator release | not recorded | 2.00 | 2.64 |
| smoke script | not recorded | 1.40 | 1.14 |
| apply guard and hygiene | not recorded | 0.50 | 0.62 |
| db secret name from cnpg | not recorded | 0.50 | 0.53 |
| api allowlist pod gateways | not recorded | 0.60 | 0.42 |
| smoke session mcp check | not recorded | 1.20 | 0.31 |

- MdAPE points: not recorded
- MdAPE minutes: 39.3%
- MdAPE tokens: 62.2%
<!-- retro:generated:end -->

## Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

| Went well | Went bad / could be improved |
|---|---|
| ... | ... |

## Improvements

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.
