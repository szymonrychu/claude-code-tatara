# agents-schedule microservice record

## Asked

A separate agents-schedule microservice with its own Postgres database that maps 5-field cron schedules (IANA timezone, default Europe/Warsaw) to presets with a prompt, modelled on agents-webhook. A due schedule fires once, starts a session through the orchestrator service port (or posts to the schedule's still-running session when the preset sets reuse_running_agent), and the run is tracked to handled or failed. Missed runs collapse into one catch-up run, overlaps are recorded ignored, limits are 3 in progress and 1 per schedule. A documented /schedules/api/v1 with openapi.json and an API-only kind e2e; v0.1.0 released. The Schedules UI entry in the hamburger menu, deploy and live smoke were split to epic agents-schedule-deploy.

## Shipped

All 22 tasks done (18 planned plus 4 discovered). Epic review verdict: pass (2026-10-25). Whole-diff review: 2 medium (per-run fault isolation, private lock import); security review: 1 medium (uvicorn proxy_headers rewrote the client from X-Forwarded-For behind the sidecar) plus lows; scope audit clean. All acted-on findings became tasks and were reviewed.

Merged (agents-schedule):
- PR #1 merged as 6cfa955 (CI green, kind e2e 16 passed).
- Tag v0.1.0 on 6cfa955; chart 0.1.0 and image 6cfa955 in harbor.
- PR #2 (release notes) merged as 7651e29, main CI green.
- Superrepo submodule pointer at 2b27ff5.

Deploy: not in this epic; epic agents-schedule-deploy (helmfile, web UI, smoke, apply) is pending, held until shared files are free.

Evidence read: full suite 137 passed (README Review); PR #1 CI green with kind e2e 16 passed; main CI on 6cfa955 green. Not re-run by this record.

## Tasks

Status and verified head are from the task files (all `done`, all with a verified head, all present in `git log 61c412b..7651e29`). The orchestrator notes record fix rounds only for the five tasks marked 1 fix; for the rest no fix round is recorded, read as 0 fix rounds (not confirmed). Per-task verification tails were not in the notes: "unknown". Points are planned/actual.

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| scaffold-project-and-cli | done | 827b279 | no fix round recorded | unknown (1/1) |
| cron-expressions | done | 13b3e3c | no fix round recorded | unknown (1/1) |
| schedule-settings-model | done | 75df33c | no fix round recorded | unknown (1/1) |
| schema-migrations | done | c56df70 | no fix round recorded | unknown (1/1) |
| runs-repository | done | 587efb1 | 1 fix (partial unique index so a manual run never suppresses a scheduled fire) | unknown (1/2) |
| schedules-repository | done | 9655936 | no fix round recorded | unknown (1/1) |
| run-dispatcher | done | cb7d3ab | 1 fix (honest RunId types, rulings recorded in MEMORY) | unknown (1/3) |
| run-outcome-tracker | done | 6242361 | no fix round recorded | unknown (1/2) |
| scheduler-loop | done | 12de0cd | no fix round recorded | unknown (1/3) |
| ignored-runs-finished-at | done | adc6cf1 | no fix round recorded | unknown (1/1); discovered during scheduler-loop |
| schedules-api-routes | done | 0a5e309 | 1 fix (orchestrator_auth_failed for 401/403, LiteralString casts) | unknown (1/2) |
| runs-api-routes | done | 08a4b34 | no fix round recorded | unknown (1/1) |
| api-docs-and-openapi | done | 2b5ab47 | no fix round recorded; log has fix 6219372 (runs status filter accepts handled) not in the notes | unknown (1/2) |
| service-entrypoints | done | 200e17c | no fix round recorded | unknown (1/2) |
| dockerfile-and-ci | done | 7eb60e5 | no fix round recorded; head is a lint style commit after 370b1e3 | unknown (1/1) |
| helm-chart | done | 1504e82 | no fix round recorded | unknown (1/2) |
| chart-ingress-and-test-hook | done | e2b75eb | 1 fix (pinned, restricted helm test pod) | unknown (1/1) |
| kind-e2e-api | done | fc99d8c | 1 fix (settle runs before the two-worker snapshot) | unknown (1/3) |
| epic-review-fixes | done | d4f6a92 | no fix round recorded | unknown (2/2); phase 5 task |
| ci-image-checks-and-worker-t | done | 814ba20 | no fix round recorded | unknown (1/1); phase 5 task |
| e2e-two-worker-failure | done | 4d085b8 | no fix round recorded | unknown (2/2); phase 5 task |
| release-v0-1-0 | done | 7b17349 | no fix round recorded | unknown (1/1); AC3 evidence amended to peel the annotated tag (v0.1.0^{}); tag and main CI per Shipped |

Approvals ledger (approvals.json) at close: A1, A2, A3, A5, A6, A7, A8 all `approved` (no A4 entry).

## Rulings

- Plan amended before the run: agents-common pinned to v0.3.0 (session names), agents-orchestrator names, menu order Sessions 10, Webhooks 20, Schedules 30, Presets 40. Cost if wrong: re-pin and a small UI reorder.
- reuse_running_agent keyed by the schedule (D15, Q12 taken at its recommended answer). Cost if wrong: later runs of a schedule start new sessions or post to the wrong one.
- Epic split (user decision via the main session): 11 agents-helmfile and agents-web tasks moved to epic agents-schedule-deploy; 4 cross-epic depends_on dropped because the epic blocker covers them. Cost if wrong: ordering must be enforced by the blocker alone.
- Accepted deviations: SCHED_HTTP_PORT instead of SCHED_PORT (inherited from agents-common BaseServiceSettings); run_migrations package "agents_schedule"; schedule_disabled applies only to scheduled runs so run-now on a disabled schedule dispatches (D11). Cost if wrong: env name mismatch in deploy values; a disabled schedule can still be run by hand.
- Local test constraint: Docker VM disk full, so DB tests ran against the shared Postgres 127.0.0.1:55433 through an uncommitted, git-excluded root conftest.py override; docker build and kind e2e were verified only in PR CI. Cost if wrong: a local-only pass hiding a CI failure; CI was green.
- Phase 5 findings acted on as tasks: epic-review-fixes (per-run fault isolation, public fire_lock, proxy_headers=False, pinned uv image), ci-image-checks-and-worker-t, e2e-two-worker-failure (test race, not a product regression). Cost if wrong: the findings would have shipped in v0.1.0.
- Findings dropped (low): SHA-pinned actions and a base digest (sibling repos use tags); busybox tag only; pyright false positive at api/openapi.py:60; fake control route returns 500 instead of 404 on a non-numeric id; duplicated small sleep and wake helpers. Cost if wrong: minor hardening or cleanup debt.

## Discovered and blocked

- Deploy, Schedules UI page, service token, smoke and helmfile apply are not done: epic agents-schedule-deploy, held until shared files are free; the user or supervisor releases it.
- Docker VM disk full on the orchestrator host: the user clears it; until then DB tests need the git-excluded conftest override.
- Discovered tasks during the run: ignored-runs-finished-at, epic-review-fixes, ci-image-checks-and-worker-t, e2e-two-worker-failure (all done).
- Dropped lows above remain open as optional debt; the user decides.

## Not pushed

agents-schedule: nothing; `git log origin/main..main` is empty and main is at 7651e29 as merged on GitHub. Superrepo: the pointer commit 2b27ff5 and the ticket moves/retro (2e54149) are committed on main; whether the superrepo main is pushed was not checked (no `git log origin/main..main` run in the superrepo); pushing stays with the user.

## Lessons routed to

- Test race completing a fake-orchestrator message before the run recorded message_id: mechanical; the fix is in tests/e2e/test_e2e_kind.py (e2e-two-worker-failure); add a helper that waits for message_id before completing a turn.
- CI did not assert image uid 1000 or absence of dev deps: mechanical; added as the CI images job check (ci-image-checks-and-worker-t).
- Minute-boundary dependence in test_single_worker_fires: mechanical; fixed by a minute-independent test; add a lint or review check against wall-clock-dependent schedule tests.
- uvicorn proxy_headers default behind an SSO sidecar: mechanical; covered by a test in epic-review-fixes asserting proxy_headers=False in the runtime.
- Runs repository allowed a manual run to suppress a scheduled fire: mechanical; covered by a partial unique index and test (runs-repository).
- Docker VM disk full forced local DB tests onto a shared Postgres: judgement call; edit the epic-run or environment guidance to define a standard local DB fallback.
