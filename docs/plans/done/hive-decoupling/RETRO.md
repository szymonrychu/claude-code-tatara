# hive decoupling retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| orch activity route | 3 | 3 | 6 | 26 | 936557 | 1392753 |
| orch hive feed removal | 5 | 5 | 8 | 72 | 1828146 | 3139018 |
| orch drop feed cursor | 3 | 3 | 6 | 57 | 936557 | 1492783 |
| helmfile orch slice1 pin | 1 | 1 | 4 | 41 | 634927 | 749152 |
| orch handover due note | 5 | 5 | 8 | 50 | 1828146 | 3225989 |
| orch handover outcome note | 3 | 3 | 6 | 50 | 936557 | 2104782 |
| helmfile orch slice2 pin | 1 | 1 | 4 | 39 | 634927 | 340130 |
| plugin activity tool | 3 | 3 | 6 | 12 | 936557 | 1786852 |
| plugins release 0.4.0 | 2 | 2 | 5 | 2 | 544297 | 227917 |
| orch plugins pin 0.4.0 | 2 | 2 | 5 | 34 | 544297 | 502616 |
| orch hive tools activity | 2 | 2 | 5 | 46 | 544297 | 710729 |
| orch e2e hive activity | 3 | 2 | 6 | 35 | 936557 | 754219 |
| helmfile smoke activity | 3 | 3 | 6 | 44 | 936557 | 2108178 |
| helmfile deploy pin | 2 | 2 | 5 | 34 | 544297 | 705757 |
| orch flaky push after decision | 2 | 2 | 5 | 88 | 544297 | 3907799 |
| helmfile apply live proof | 8 | 2 | 14 | not recorded | 3155191 | not recorded |
| plugin advice threshold floor | 1 | 1 | 4 | not recorded | 632059 | not recorded |
| helmfile orch flaky fix pin | 1 | 1 | 4 | not recorded | 632059 | not recorded |
| orch feed dead code and compact helper | 2 | 2 | 6 | not recorded | 546295 | not recorded |
| helmfile orch cleanup pin | 1 | 1 | 4 | not recorded | 632059 | not recorded |
| Total | 53 | 46 | 117 | 630 (15 of 20 tasks) | 18864636 | 23148674 (15 of 20 tasks) |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| orch activity route | 0 | 4.33 | 1.49 |
| orch hive feed removal | 0 | 9.00 | 1.72 |
| orch drop feed cursor | 0 | 9.50 | 1.59 |
| helmfile orch slice1 pin | 0 | 10.25 | 1.18 |
| orch handover due note | 0 | 6.25 | 1.76 |
| orch handover outcome note | 0 | 8.33 | 2.25 |
| helmfile orch slice2 pin | 0 | 9.75 | 0.54 |
| plugin activity tool | 0 | 2.00 | 1.91 |
| plugins release 0.4.0 | 0 | 0.40 | 0.42 |
| orch plugins pin 0.4.0 | 0 | 6.80 | 0.92 |
| orch hive tools activity | 0 | 9.20 | 1.31 |
| orch e2e hive activity | -1 | 5.83 | 0.81 |
| helmfile smoke activity | 0 | 7.33 | 2.25 |
| helmfile deploy pin | 0 | 6.80 | 1.30 |
| orch flaky push after decision | 0 | 17.60 | 7.18 |
| helmfile apply live proof | -6 | not recorded | not recorded |
| plugin advice threshold floor | 0 | not recorded | not recorded |
| helmfile orch flaky fix pin | 0 | not recorded | not recorded |
| orch feed dead code and compact helper | 0 | not recorded | not recorded |
| helmfile orch cleanup pin | 0 | not recorded | not recorded |

- MdAPE points: 0.0%
- MdAPE minutes: 88.0%
- MdAPE tokens: 41.8%
<!-- retro:generated:end -->

## Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

| Went well | Went bad / could be improved |
|---|---|
| ... | ... |

## Improvements

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.
