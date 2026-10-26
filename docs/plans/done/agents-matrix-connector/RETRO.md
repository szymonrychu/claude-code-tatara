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

| Went well | Went bad / could be improved |
|---|---|
| 27 tasks delivered; 16 closed without a fix round, 11 needed one or two (reply tracker, matrix sync loop, api rules and settings, dispatch worker, mxc openapi and readme (2 rounds), mxc service entrypoints, mxc chart workloads, mxc operations docs, mxc chart network, and others). | Fix rounds were mostly structure and hygiene (helpers moved to conftest, run_rows moved to db/inbound.py, restored ci/lint-values.yaml, plain MigrateSettings), not behaviour: mxc openapi and readme needed 2 rounds (source grep instead of reason constants, duplicate SESSION_GONE). |
| Whole-diff review PASS (182 then 188 passed, lint/chart/lock green) and scope audit found no gaps. | The security review found a HIGH (facebook-id spoof via foreign-server ghost ids) and a MEDIUM (unverified canonical alias) that 25 per-task reviews missed; they became task matrix identity spoofing guards (10 min vs 6, tokens 2845183 vs 937864, 3.03x). |
| Security and scope-audit findings were turned into tasks (matrix identity spoofing guards, review cleanups) and reviewed clean; drops were explicit and reasoned (RuleExists noqa N818, first-turn-only preamble per D8, chart SSO/NetworkPolicy). | Review cleanups (duplicate utcnow in worker.py, tracker.py, sync.py; upstream text in 502 bodies; Dockerfile uv:latest and floating base) were avoidable defects: 8 min vs 5, tokens 1.49x. |
| Revision R1 (connector reuses the Hermes identity) and the split into agents-matrix-connector-depl (G1, G5 and the live half of G6 moved) kept the core epic to the service. | R1 changed the plan mid-epic; discovered task sync limited timeline backfill (7 min vs 6, tokens 1.68x) came from a sync loop gap (pre-join history skipped, lost filter) found in review. |
| Time came in far under estimate: 140 min vs 291 total; many tasks at 0.14-0.30x (room and event discovery 2 vs 14, inbound queue repository 2 vs 14). Points MdAPE 0.0%. | Estimate error is skewed: minutes MdAPE 166.7%, tokens 40.5%; matrix sync loop 18 vs 14 min (1.29x), matrix identity spoofing guards 1.67x, review cleanups 1.60x, mxc schema migrations tokens 1.63x. Totals: tokens 28357104 vs 25796058. |
| Pointer-level points matched except two re-scores: mxc common session names 2 to 1, mxc e2e api 8 to 5. | Tooling friction: ticket.py truncated the slug to 28 characters (matrix-identity-spoofing-gua, sync-limited-timeline-backfi) and new-task dropped the non-Requirement sections, so task briefs lost content. |
| | Testcontainers could not run (Docker disk full); the whole suite ran only against a shared Postgres fixture override, so the real fixture path was never exercised locally. |
| | Main CI was red for hours: HARBOR_USERNAME/HARBOR_PASSWORD missing on szymonrychu/agents-matrix-connector (gh secret list empty 2026-10-26; set on agents-schedule and agents-webhook). Neither component-add nor planning flagged them as a user step; core epic close stayed gated. |

## Improvements

- Code:
  - agents-matrix-connector worker.py:57, tracker.py:53, sync.py:78: utcnow() was duplicated (fixed in review cleanups); keep one shared helper.
  - agents-matrix-connector matrix identity handling: keep tests pinning the foreign-server ghost id and unverified alias rejections so the spoof guards cannot regress.
  - agents-matrix-connector api layer: error bodies must not carry str(exc) from upstream (fixed in review cleanups); keep a test asserting generic 502 text.
  - agents-matrix-connector Dockerfile: uv and base image pinned in review cleanups; digest-pin if stricter supply-chain policy is wanted.
- Delivered differently:
  - Revision R1: the connector reuses the Hermes identity instead of a new one, decided mid-epic.
  - The epic was split: G1, G5 and the live half of G6 moved to agents-matrix-connector-depl by user decision.
  - Two tasks beyond the plan: matrix identity spoofing guards and review cleanups (security and scope-audit findings), plus discovered sync limited timeline backfill.
  - mxc dockerfile and ci omitted e2e, tag and refuse-existing-version jobs: the spec lists main only and e2e runs in the test job via plain pytest.
  - ingress.denySourceRanges added to the chart for the depl consumer.
- Tech debt:
  - Chart has no oauth2-proxy sidecar or NetworkPolicy (agents-matrix-connector chart): SSO comes from pod annotations in depl helmfile-matrix-releases and the CIDR allowlist fails closed; a NetworkPolicy would remove the dependency.
  - Untrusted-input preamble only on the first turn (D8, by design): revisit if per-turn injection becomes a concern.
  - Local DB tests rely on the shared Postgres fixture override instead of testcontainers: remove once the Docker disk is cleared or a documented env switch exists.
  - Core epic close is gated on Harbor repo secrets: set HARBOR_USERNAME/HARBOR_PASSWORD on szymonrychu/agents-matrix-connector.
- Workflow:
  - recurring (agents-schedule-microservice, agents-schedule-deploy): flat seeds with post-delivery points and minutes far off (minutes MdAPE 166.7% here, 83.3% and 61.5% there; tokens 40.5%, 70.8%, 31.6%). Change: planning should vary the seed per task by kind (repository and docs tasks short, sync loop, dispatch and security tasks long) and calibrate minutes from the previous epics' actuals.
  - recurring (agents-schedule-microservice, test-temp-dirs-outside-the-c): defects missed by per-task reviews surfaced at whole-diff or security review (here: HIGH facebook-id spoof, MEDIUM alias spoof, duplicate utcnow, str(exc) in 502 bodies). Change: add to the per-task reviewer checklist trust boundaries on external identifiers, no upstream text in responses and shared helpers; keep the whole-diff and security review mandatory.
  - recurring (agents-schedule-microservice): Docker VM disk full blocked testcontainers and led to shared Postgres overrides. Change: epic-run preflight check of Docker disk before dispatch, with a documented committed shared-Postgres switch.
  - ticket.py: slug truncation to 28 characters (also seen as agents-schedule-microservice style slugs: test-temp-dirs-outside-the-c) and new-task dropping non-Requirement sections; change: keep full slugs or truncate at a word boundary, and make new-task keep every section of the template.
  - component-add and planning: no step lists user-owned repo secrets (Harbor credentials) for a new repo; change: component-add emits a checklist of required repo secrets and the plan records them as a user step gating CI and epic close.
