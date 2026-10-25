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

| Went well | Went bad / could be improved |
|---|---|
| 22 tasks delivered; 17 closed without a fix round, and only 5 needed one (runs repository, run dispatcher, schedules api routes, chart ingress and test hook, kind e2e api), each with one round. | Fix rounds hit the highest-risk tasks: runs repository (manual run could suppress a scheduled fire, fixed with a partial unique index), run dispatcher (dishonest RunId types), schedules api routes (401/403 mapping to orchestrator_auth_failed). |
| Scope audit was clean; PR #1 merged with CI green and kind e2e 16 passed, v0.1.0 tagged, chart and image published. | Phase 5 reviews found real defects that 22 per-task reviews missed: per-run fault isolation, a private lock import, and a security medium (uvicorn proxy_headers default rewrote the client from X-Forwarded-For behind the sidecar). Three of these became or fed task epic-review-fixes. |
| Plan amendments before the run (agents-common v0.3.0 pin, D15 reuse key, menu order) and the user split of 11 agents-helmfile/agents-web tasks into agents-schedule-deploy kept this epic to the service. | Four tasks were discovered mid-run (ignored runs finished at, epic review fixes, ci image checks and worker test flake, e2e two worker failure); the last two were CI-only failures, visible only after push because the Docker VM disk was full locally. |
| Total minutes (76 vs 120) and tokens (15119343 vs 15842172) landed within budget in aggregate. | Every task was estimated at 1 point (2 for two), yet post-delivery points total 36 vs 24; run dispatcher (+2), scheduler loop (+2), kind e2e api (+2) were far larger. Minutes MdAPE 83.3%, tokens MdAPE 70.8%; run dispatcher used 3.13x tokens (2348483), e2e two worker failure 2.64x, kind e2e api 2.54x. |
| Drops were explicit: SHA-pinned actions, busybox tag, pyright false positive, fake control route 500, duplicated sleep helpers; accepted deviations (SCHED_HTTP_PORT, D11 run-now on disabled schedule) recorded. | Local verification was partial: DB tests ran against a shared Postgres through an uncommitted, git-excluded root conftest.py override; docker build and kind e2e were verified only in PR CI. |
| | release v0.1.0 took 8 min vs 5 expected; release-v0-1-0 AC3 evidence had to be amended to peel the annotated tag (v0.1.0^{}). |

## Improvements

- Code:
  - agents-schedule scheduler loop (dispatch path): per-run fault isolation was missing until epic-review-fixes; keep a test that one failing run does not stop the others.
  - agents-schedule uvicorn launch (service entrypoints): proxy_headers default was trusted behind the sidecar; keep a test pinning the setting.
  - agents-schedule scheduler: private lock import replaced at whole-diff review; avoid reintroducing private imports from agents-common.
  - Duplicated small sleep and wake helpers across tests (dropped as low); share one helper.
- Delivered differently:
  - Env var is SCHED_HTTP_PORT, not SCHED_PORT, because it is inherited from agents-common BaseServiceSettings.
  - run_migrations package is "agents_schedule" rather than the design name, accepted.
  - schedule_disabled applies only to scheduled runs, so run-now on a disabled schedule dispatches (D11).
  - 11 agents-helmfile and agents-web tasks moved to epic agents-schedule-deploy by user decision; 4 cross-epic depends_on dropped.
  - Four discovered tasks were added beyond the plan (ignored runs finished at, epic review fixes, ci image checks and worker test flake, e2e two worker failure).
- Tech debt:
  - GitHub actions not SHA-pinned and base image not digest-pinned (.github workflows, Dockerfile in agents-schedule): pin by SHA and digest.
  - Chart test pod uses a busybox tag only: pin by digest.
  - Fake control route returns 500 instead of 404 (agents-schedule test fakes): return 404.
  - pyright false positive at api/openapi.py:60: suppress with a targeted ignore or fix the typing.
  - Local DB tests depend on an uncommitted conftest.py override: remove once the Docker VM has disk or a documented shared-Postgres env switch exists.
- Workflow:
  - recurring (test-temp-dirs-outside-the-c, epic-and-task-migration-skil, lean-development-flow): defects that per-task reviews missed surfaced only at the whole-diff review (there: mktemp critical, done epic with no RETRO.md; here: fault isolation, private import, uvicorn proxy_headers security medium). Change: add cross-cutting checks to the per-task reviewer checklist (one failing item must not abort a loop, no private imports across packages, framework defaults that trust forwarded headers) and keep the whole-diff and security review mandatory for every epic.
  - Estimates: every task seeded at 1 point while post-delivery points reached 3 on dispatcher, loop and e2e tasks; minutes and tokens MdAPE 83.3% and 70.8%. Change: planning should point tasks that combine external orchestrator calls, concurrency or kind e2e at 3, not default to 1. Not recurring on this exact kind in history (earlier epics show pessimistic seeds on minutes/tokens), so a note only.
  - Local verification gaps (full Docker VM disk) pushed docker build and kind e2e to PR CI and caused two discovered CI tasks; add a preflight disk check to epic-run before dispatching tasks that need docker. Single occurrence, not recurring.
