# agents-schedule deploy retro

## Review

Migrated from the epic format.

## What went well

- 11 tasks delivered; 9 closed without a fix round, 2 needed one (web schedule form, web schedules page).
- Both PRs merged green: agents-web #10 (586344d, npm test 373 passed), agents-helmfile #24 (2ad2d86, mise run test 155 passed, lint clean).
- Live apply of e16b726 reached smoke: OK; the test guard stopped the first request (0826571) before any harm.
- Tokens came in under budget (6604458 vs 7464380); points MdAPE 0.0% on the estimate side of the delta, tokens MdAPE 31.6%.
- Drops were explicit and reasoned: http-insecure 8080 security medium (app allowlist checks the socket peer), NetworkPolicy backstop, shared S3 backup credentials (same practice as webhook), TLS Secret reuse.
- Briefs were tightened after the fix rounds: web tasks now require `npx tsc -b` and full `npm test`.

## What went wrong or could improve

- Both fix rounds were web type/test breaks a full local check would have caught: web schedule form (tsc error on Stack justifyContent, Intl.supportedValuesOf fallback), web schedules page ("agent cluster" wording broke the nomenclature test, plus a type cast).
- agents-helmfile has no CI beyond GitGuardian, so PR #24 was verified only by the local run.
- The first apply request was blocked by a stale test (test_values_dir_moved), and the first smoke failed 503 because orchestrator api pods do not restart when the services Secret changes; fixed by a manual rollout restart, root fix owned by the main session.
- Post-delivery points 15 vs 11 estimated (+1 on smoke schedule check, web schedule form, web schedules page, deploy schedule). Minutes MdAPE 61.5%: helmfile schedule release took 19 min vs 5 (3.80x), smoke schedule check 13 vs 5 (2.60x, tokens 910137).
- web schedules page used 992696 tokens (1.46x) and deploy schedule 799550 (1.18x) against a flat 678580 seed.

## Recommendations

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

## Delivery record (migrated)

### Asked

The agents-helmfile and agents-web half of agents-schedule-microservice: deploy the agents-schedule service (CNPG database, release, SOPS service token), a live smoke schedule step, and the agents-web Schedules page (typed client, form, runs list, page) with its hamburger menu entry between Webhooks and Presets. Then apply and smoke.

### Shipped

All 11 tasks done (11 planned, none discovered). Epic review verdict: pass (2026-10-26).

- agents-web PR #10 merged as 586344d (CI green, npm test 373 passed per notes): vendored schedules OpenAPI (v0.1.0), typed client, ScheduleForm, ScheduleRuns, SchedulesPage, menu entry at order 30.
- agents-helmfile PR #24 merged as 2ad2d86: agents-schedule-db and agents-schedule releases (chart 0.1.0, image 6cfa955), generalised bootstrap_service_token plus token SOPS files, smoke schedule step, schedules backend in agents-web values, pin to 586344d. Repo has no CI beyond GitGuardian; local `mise run test` 155 passed, lint clean (README Review and notes).
- Deploy: the main session applied e16b726. Revisions: agents-schedule rev 1, agents-schedule-db rev 1, agents-web rev 8 (0.1.0-main.586344d), agents-orchestrator rev 2. First apply request (0826571) was stopped by the test guard (stale test_values_dir_moved), fixed in e16b726. First smoke gave 503 (orchestrator 401: api pods do not restart when the services Secret changes); after `kubectl rollout restart deploy/agents-orchestrator-api` smoke: OK (.logs/sched-deploy-smoke2.log).

Evidence read, not re-run by this record.

### Tasks

Status and verified head from the task files; all `done`, all with a verified head, all present in the git logs (agents-helmfile f07eb98..2ad2d86, agents-web 5a8d6c8..586344d). Review rounds: the notes record fix rounds only for web-schedule-form and web-schedules-page; the rest read as 0 fix rounds (not confirmed). Per-task verification tails were not in the notes: "unknown". Points are planned/actual.

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| helmfile-schedule-db-release | done | 0ccc714 | no fix round recorded | unknown (1/1); head is a ruff format commit after 1bd477f |
| schedule-service-token | done | fd8696f | no fix round recorded; review: full | unknown (1/1) |
| smoke-schedule-check | done | 392e1a3 | no fix round recorded | unknown (1/2); log has lint fix 70cd4cc and format 0ccc714 not in the notes |
| web-config-schedules-backend | done | ead1cde | no fix round recorded | unknown (1/1) |
| web-schedules-api-client | done | 10581e4 | no fix round recorded | unknown (1/1) |
| helmfile-schedule-release | done | 0c4b1f6 | no fix round recorded | unknown (1/1) |
| web-schedule-form | done | 79d015f | 1 fix (tsc error on Stack justifyContent, Intl.supportedValuesOf fallback) | unknown (1/2) |
| web-schedule-runs-list | done | 31166c9 | no fix round recorded | unknown (1/1) |
| web-schedules-page | done | c8fb37f | 1 fix ("agent cluster" wording broke the nomenclature test, type cast) | unknown (1/2) |
| web-schedules-menu-entry | done | 41e6249 | no fix round recorded | unknown (1/1) |
| deploy-schedule | done | e16b726 | no fix round recorded; guard failure at 0826571 fixed by e16b726 | unknown (1/2); live smoke: OK after rollout restart |

Totals from the retro: 11 planned points, 15 actual; 55 expected minutes, 66 actual.

### Rulings

- Dropped (security medium): SSO bypass via http-insecure 8080. The app allowlist checks only the socket peer (proxy_headers=False, tested against a real uvicorn server in agents-schedule). Cost if wrong: unauthenticated access to schedule routes through the insecure port.
- Dropped: NetworkPolicy backstop for the namespace (cross-service, not this epic). Cost if wrong: no network-level second layer.
- Dropped: shared S3 backup credentials with agents-webhook-db (byte-copied SOPS file, same accepted practice as webhook). Cost if wrong: one leaked credential covers both backups.
- Dropped: TLS Secret reuse (per the URL layout). Cost if wrong: coupled certificate lifecycle.
- Dropped: scope audit claim that menu.ts drops onOpenSession; wrong, menu.ts:10 passes it. Cost if wrong: session link in runs list would not open.
- Briefs now require `npx tsc -b` and the full `npm test` for web tasks (process change after the two fix rounds). Cost if wrong: type errors reach review again.

### Discovered and blocked

- Orchestrator api pods do not restart when the services Secret changes (caused the first smoke 503). Workaround: manual rollout restart. Root fix is owned by the main session in agents-orchestrator; a task orch-services-secret-checksu exists in epic workspace-s3-cache. The main session clears it.
- test_values_dir_moved had a stale expected list and blocked the apply guard; fixed in e16b726.

### Not pushed

agents-helmfile and agents-web: nothing; main is level with origin/main (merged as 2ad2d86 and 586344d). Superrepo: 93 commits on main not on origin/main (includes the submodule pointer commit f6a6453, the epic's ticket moves and the retro a270194, and other epics' ticket commits); the user pushes.

### Lessons routed to

- Stale expected-file list in test_values_dir_moved blocked the apply guard: mechanical; make the test derive the expected list from the values directory, or add a check that fails when a values file is added without updating it.
- Services Secret change does not restart the orchestrator api pods: mechanical; add a checksum annotation on the Deployment (task orch-services-secret-checksu) and a helm template test asserting it.
- Web tasks failed on tsc and the nomenclature test only at review: mechanical; web task verify commands include `npx tsc -b` and the full `npm test` (already in briefs); add them to the task `verify` field default for repo agents-web.
- Wording "agent cluster" in UI copy: mechanical; the existing nomenclature test caught it, no new check needed.
