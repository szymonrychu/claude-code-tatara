# deploy-safe agent sessions retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| helmfile pin check | 5 | 5 | 8 | 22 | 1828146 | 2535829 |
| helmfile smoke continuity | 5 | 5 | 8 | 31 | 1828146 | 3058400 |
| orch dead agent ineligible | 3 | 3 | 6 | 37 | 940114 | 1862484 |
| orch e2e main failure | 3 | 3 | 6 | 22 | 936557 | 1504839 |
| orch ingester reattach | 5 | 5 | 8 | 67 | 1828146 | 7999692 |
| orch onstart nonfatal | 2 | 2 | 5 | 20 | 544297 | 820107 |
| orch sessions backup save | 5 | 5 | 8 | 40 | 1828146 | 6393804 |
| web ci publish gate | 1 | 1 | 4 | 5 | 641999 | 250789 |
| wrapper shutdown turn resume | 5 | 5 | 8 | 211 | 1828146 | 12569789 |
| orch ci publish gate | 2 | 2 | 5 | 19 | 544297 | 556633 |
| orch default continue prompt | 2 | 2 | 5 | 19 | 544297 | 1172307 |
| orch sessions backup restore | 5 | 5 | 8 | 42 | 1828146 | 7308288 |
| orch api session safety | 3 | 3 | 6 | 31 | 936557 | 3378333 |
| wrapper patch release | 1 | 1 | 4 | 17 | 641999 | 247269 |
| orch rollout replacer | 8 | 8 | 14 | 83 | 3155191 | 10288310 |
| orch wrapper pin patch | 2 | 3 | 5 | 69 | 544297 | 2223518 |
| orch e2e rollout mid turn | 5 | 5 | 8 | 104 | 1828146 | 15410029 |
| web sync session safety api | 1 | 1 | 4 | 8 | 641999 | 306882 |
| web agent unavailable banner | 5 | 3 | 8 | 9 | 1828146 | 868989 |
| web discard backup notice | 3 | 3 | 6 | 13 | 940114 | 965826 |
| web-review-fixes | 3 | 2 | 6 | 6 | 950968 | 644127 |
| orch-rollout-dispatch-reservation | 3 | 2 | 6 | 18 | 950968 | 1029725 |
| orch-sessions-save-unconverged | 3 | 3 | 6 | 10 | 950968 | 1555464 |
| orch-security-hardening | 3 | 2 | 6 | 57 | 950968 | 1883710 |
| helmfile-pin-check-attempts | 2 | 2 | 5 | 5 | 556633 | 435637 |
| helmfile deploy pins | 2 | 2 | 5 | 11 | 544297 | 564830 |
| helmfile apply live check | 5 | 5 | 8 | not recorded | 1828146 | not recorded |
| Total | 92 | 88 | 176 | 976 (26 of 27 tasks) | 32369834 | 85835610 (26 of 27 tasks) |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| helmfile pin check | 0 | 2.75 | 1.39 |
| helmfile smoke continuity | 0 | 3.88 | 1.67 |
| orch dead agent ineligible | 0 | 6.17 | 1.98 |
| orch e2e main failure | 0 | 3.67 | 1.61 |
| orch ingester reattach | 0 | 8.38 | 4.38 |
| orch onstart nonfatal | 0 | 4.00 | 1.51 |
| orch sessions backup save | 0 | 5.00 | 3.50 |
| web ci publish gate | 0 | 1.25 | 0.39 |
| wrapper shutdown turn resume | 0 | 26.38 | 6.88 |
| orch ci publish gate | 0 | 3.80 | 1.02 |
| orch default continue prompt | 0 | 3.80 | 2.15 |
| orch sessions backup restore | 0 | 5.25 | 4.00 |
| orch api session safety | 0 | 5.17 | 3.61 |
| wrapper patch release | 0 | 4.25 | 0.39 |
| orch rollout replacer | 0 | 5.93 | 3.26 |
| orch wrapper pin patch | +1 | 13.80 | 4.09 |
| orch e2e rollout mid turn | 0 | 13.00 | 8.43 |
| web sync session safety api | 0 | 2.00 | 0.48 |
| web agent unavailable banner | -2 | 1.12 | 0.48 |
| web discard backup notice | 0 | 2.17 | 1.03 |
| web-review-fixes | -1 | 1.00 | 0.68 |
| orch-rollout-dispatch-reservation | -1 | 3.00 | 1.08 |
| orch-sessions-save-unconverged | 0 | 1.67 | 1.64 |
| orch-security-hardening | -1 | 9.50 | 1.98 |
| helmfile-pin-check-attempts | 0 | 1.00 | 0.78 |
| helmfile deploy pins | 0 | 2.20 | 1.04 |
| helmfile apply live check | 0 | not recorded | not recorded |

- MdAPE points: 0.0%
- MdAPE minutes: 73.9%
- MdAPE tokens: 51.5%
<!-- retro:generated:end -->

## Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

| Went well | Went bad / could be improved |
|---|---|
| ... | ... |

## Improvements

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.
