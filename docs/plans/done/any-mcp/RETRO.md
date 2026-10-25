# any-mcp retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| Scaffold | 1 | not recorded | 6 | 4 | 750000 | 671337 |
| Core types | 1 | not recorded | 5 | 3 | 750000 | 435175 |
| uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships. | not recorded | not recorded | not recorded | 1 | not recorded | 209475 |
| Config model | 1 | not recorded | 5 | 2 | 750000 | 214114 |
| HTTP binding | 1 | not recorded | 5 | 3 | 750000 | 505489 |
| Response shaping | 1 | not recorded | 5 | 1 | 750000 | 174195 |
| Schemas and validation | 1 | not recorded | 5 | 7 | 750000 | 845523 |
| Plugin ABC | 1 | not recorded | 6 | 6 | 750000 | 1394817 |
| Plugin discovery | 1 | not recorded | 5 | 3 | 750000 | 592706 |
| Registry | 1 | not recorded | 5 | 6 | 750000 | 1281899 |
| Call pipeline | 1 | not recorded | 5 | 5 | 750000 | 998614 |
| FastMCP adapter | 1 | not recorded | 5 | 14 | 750000 | 9981430 |
| Input-required core | 1 | not recorded | 6 | 3 | 750000 | 546527 |
| CLI stdio | 1 | not recorded | 6 | 6 | 750000 | 1012044 |
| Testing harness | 1 | not recorded | 5 | 20 | 750000 | 1293647 |
| Examples small medium | 1 | not recorded | 6 | 3 | 750000 | 532682 |
| HTTP transport | 1 | not recorded | 5 | 7 | 750000 | 1842320 |
| OpenAPI plugin | 1 | not recorded | 6 | 3 | 750000 | 751328 |
| Docs reference | 1 | not recorded | 5 | 4 | 750000 | 733697 |
| Examples big group | 1 | not recorded | 6 | 3 | 750000 | 576382 |
| Input-required adapter | 1 | not recorded | 5 | 8 | 750000 | 1998267 |
| openapi credential hosts | 1 | not recorded | 5 | 2 | 750000 | 443299 |
| bounded upstream bodies | 1 | not recorded | 6 | 4 | 750000 | 822315 |
| Docs authoring | 1 | not recorded | 5 | 6 | 750000 | 1168965 |
| Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http. | not recorded | not recorded | not recorded | 8 | not recorded | 1111288 |
| Docs README concepts | 1 | not recorded | 5 | 4 | 750000 | 880389 |
| http auth on non loopback | 1 | not recorded | 6 | 4 | 750000 | 639211 |
| error redaction and cleanup | 1 | not recorded | 6 | 9 | 750000 | 1218095 |
| Release | 1 | not recorded | 5 | 9 | 750000 | 661202 |
| workflow hardening | 1 | not recorded | 5 | 3 | 750000 | 323876 |
| Total | 28 (28 of 30 tasks) | not recorded | 150 (28 of 30 tasks) | 161 | 21000000 (28 of 30 tasks) | 33860308 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| Scaffold | not recorded | 0.67 | 0.90 |
| Core types | not recorded | 0.60 | 0.58 |
| uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships. | not recorded | not recorded | not recorded |
| Config model | not recorded | 0.40 | 0.29 |
| HTTP binding | not recorded | 0.60 | 0.67 |
| Response shaping | not recorded | 0.20 | 0.23 |
| Schemas and validation | not recorded | 1.40 | 1.13 |
| Plugin ABC | not recorded | 1.00 | 1.86 |
| Plugin discovery | not recorded | 0.60 | 0.79 |
| Registry | not recorded | 1.20 | 1.71 |
| Call pipeline | not recorded | 1.00 | 1.33 |
| FastMCP adapter | not recorded | 2.80 | 13.31 |
| Input-required core | not recorded | 0.50 | 0.73 |
| CLI stdio | not recorded | 1.00 | 1.35 |
| Testing harness | not recorded | 4.00 | 1.72 |
| Examples small medium | not recorded | 0.50 | 0.71 |
| HTTP transport | not recorded | 1.40 | 2.46 |
| OpenAPI plugin | not recorded | 0.50 | 1.00 |
| Docs reference | not recorded | 0.80 | 0.98 |
| Examples big group | not recorded | 0.50 | 0.77 |
| Input-required adapter | not recorded | 1.60 | 2.66 |
| openapi credential hosts | not recorded | 0.40 | 0.59 |
| bounded upstream bodies | not recorded | 0.67 | 1.10 |
| Docs authoring | not recorded | 1.20 | 1.56 |
| Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http. | not recorded | not recorded | not recorded |
| Docs README concepts | not recorded | 0.80 | 1.17 |
| http auth on non loopback | not recorded | 0.67 | 0.85 |
| error redaction and cleanup | not recorded | 1.50 | 1.62 |
| Release | not recorded | 1.80 | 0.88 |
| workflow hardening | not recorded | 0.60 | 0.43 |

- MdAPE points: not recorded
- MdAPE minutes: 50.0%
- MdAPE tokens: 37.8%
<!-- retro:generated:end -->

## Retro

Filled by retro-writer from the reviewer tails, the rulings and the deltas, one row per point:

| Went well | Went bad / could be improved |
|---|---|
| ... | ... |

## Improvements

Filled by retro-writer: potential improvements in the code, things delivered in a different way than expected, tech debt introduced anyway, and workflow improvement proposals for items recurring in `ticket.py retro --history`; "none" where a list is empty.
