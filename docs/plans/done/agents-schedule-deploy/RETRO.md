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

| Went well | Went bad / could be improved |
|---|---|
| 11 tasks delivered; 9 closed without a fix round, 2 needed one (web schedule form, web schedules page). | Both fix rounds were web type/test breaks a full local check would have caught: web schedule form (tsc error on Stack justifyContent, Intl.supportedValuesOf fallback), web schedules page ("agent cluster" wording broke the nomenclature test, plus a type cast). |
| Both PRs merged green: agents-web #10 (586344d, npm test 373 passed), agents-helmfile #24 (2ad2d86, mise run test 155 passed, lint clean). | agents-helmfile has no CI beyond GitGuardian, so PR #24 was verified only by the local run. |
| Live apply of e16b726 reached smoke: OK; the test guard stopped the first request (0826571) before any harm. | The first apply request was blocked by a stale test (test_values_dir_moved), and the first smoke failed 503 because orchestrator api pods do not restart when the services Secret changes; fixed by a manual rollout restart, root fix owned by the main session. |
| Tokens came in under budget (6604458 vs 7464380); points MdAPE 0.0% on the estimate side of the delta, tokens MdAPE 31.6%. | Post-delivery points 15 vs 11 estimated (+1 on smoke schedule check, web schedule form, web schedules page, deploy schedule). Minutes MdAPE 61.5%: helmfile schedule release took 19 min vs 5 (3.80x), smoke schedule check 13 vs 5 (2.60x, tokens 910137). |
| Drops were explicit and reasoned: http-insecure 8080 security medium (app allowlist checks the socket peer), NetworkPolicy backstop, shared S3 backup credentials (same practice as webhook), TLS Secret reuse. | web schedules page used 992696 tokens (1.46x) and deploy schedule 799550 (1.18x) against a flat 678580 seed. |
| Briefs were tightened after the fix rounds: web tasks now require `npx tsc -b` and full `npm test`. | |

## Improvements

- Code:
  - agents-helmfile bootstrap_service_token (generalised from webhook): keep one test per consumer (webhook, schedule) so the generalisation cannot regress either.
  - agents-helmfile test_values_dir_moved was stale and stopped the first apply: make it derive the path instead of hard-coding it.
- Delivered differently:
  - Epic was split out of agents-schedule-microservice on 2026-10-25 (11 helmfile and web tasks) by user decision.
  - The session link in the schedule runs list is an onOpenSession callback wired to the menu's show, not a route.
  - Smoke needed a manual `kubectl rollout restart deploy/agents-orchestrator-api` after the services Secret changed; the design assumed pods pick it up.
- Tech debt:
  - agents-orchestrator api pods do not restart on services Secret change (agents-orchestrator chart): add a checksum annotation or a reloader; owned by the main session.
  - Shared S3 backup credentials are a byte-copied SOPS file (agents-helmfile): per-service credentials would remove it; same practice as webhook.
  - No NetworkPolicy backstop for the schedule service (agents-helmfile): add one if the socket-peer allowlist is judged insufficient.
  - agents-helmfile has no CI beyond GitGuardian: add a CI job running `mise run test` and lint.
- Workflow:
  - recurring (agents-schedule-microservice): every task seeded at 1 point and a flat token seed (678580 here, 750000 there) while post-delivery points exceeded the estimate (15 vs 11 here, 36 vs 24 there) and minutes MdAPE stayed high (61.5% here, 83.3% there). Change: planning should score tasks touching live deploy, smoke, multi-form UI pages or chart releases at 2-3 and vary the seed per task instead of defaulting to 1.
  - Web task briefs lacked the type check and full test run, costing two fix rounds; already fixed by requiring `npx tsc -b` and `npm test` in briefs, so a note only, not recurring.
