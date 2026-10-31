# agents matrix connector retro

## Review

Migrated from the epic format.

## What went well

- 27 tasks delivered; 16 closed without a fix round, 11 needed one or two (reply tracker, matrix sync loop, api rules and settings, dispatch worker, mxc openapi and readme (2 rounds), mxc service entrypoints, mxc chart workloads, mxc operations docs, mxc chart network, and others).
- Whole-diff review PASS (182 then 188 passed, lint/chart/lock green) and scope audit found no gaps.
- Security and scope-audit findings were turned into tasks (matrix identity spoofing guards, review cleanups) and reviewed clean; drops were explicit and reasoned (RuleExists noqa N818, first-turn-only preamble per D8, chart SSO/NetworkPolicy).
- Revision R1 (connector reuses the Hermes identity) and the split into agents-matrix-connector-depl (G1, G5 and the live half of G6 moved) kept the core epic to the service.
- Time came in far under estimate: 140 min vs 291 total; many tasks at 0.14-0.30x (room and event discovery 2 vs 14, inbound queue repository 2 vs 14). Points MdAPE 0.0%.
- Pointer-level points matched except two re-scores: mxc common session names 2 to 1, mxc e2e api 8 to 5.

## What went wrong or could improve

- Fix rounds were mostly structure and hygiene (helpers moved to conftest, run_rows moved to db/inbound.py, restored ci/lint-values.yaml, plain MigrateSettings), not behaviour: mxc openapi and readme needed 2 rounds (source grep instead of reason constants, duplicate SESSION_GONE).
- The security review found a HIGH (facebook-id spoof via foreign-server ghost ids) and a MEDIUM (unverified canonical alias) that 25 per-task reviews missed; they became task matrix identity spoofing guards (10 min vs 6, tokens 2845183 vs 937864, 3.03x).
- Review cleanups (duplicate utcnow in worker.py, tracker.py, sync.py; upstream text in 502 bodies; Dockerfile uv:latest and floating base) were avoidable defects: 8 min vs 5, tokens 1.49x.
- R1 changed the plan mid-epic; discovered task sync limited timeline backfill (7 min vs 6, tokens 1.68x) came from a sync loop gap (pre-join history skipped, lost filter) found in review.
- Estimate error is skewed: minutes MdAPE 166.7%, tokens 40.5%; matrix sync loop 18 vs 14 min (1.29x), matrix identity spoofing guards 1.67x, review cleanups 1.60x, mxc schema migrations tokens 1.63x. Totals: tokens 28357104 vs 25796058.
- Tooling friction: ticket.py truncated the slug to 28 characters (matrix-identity-spoofing-gua, sync-limited-timeline-backfi) and new-task dropped the non-Requirement sections, so task briefs lost content.
- Testcontainers could not run (Docker disk full); the whole suite ran only against a shared Postgres fixture override, so the real fixture path was never exercised locally.
- Main CI was red for hours: HARBOR_USERNAME/HARBOR_PASSWORD missing on szymonrychu/agents-matrix-connector (gh secret list empty 2026-10-26; set on agents-schedule and agents-webhook). Neither component-add nor planning flagged them as a user step; core epic close stayed gated.

## Recommendations

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

## Delivery record (migrated)

### Asked

New Python microservice agents-matrix-connector (own repo, own CNPG database) that logs in to the live Synapse as a bot user, auto-discovers Messenger rooms, users and members bridged by mautrix-meta, applies default-deny allow/deny rules, batches allowed messages per room into one agents-orchestrator session per room and posts each turn's final text back. Plus a UI API under /matrix/api/v1. Request of 2026-10-25. Deploy and the agents-web Chats page moved to epic agents-matrix-connector-depl by the split.

### Shipped

27 tasks (25 planned, 2 added from review: matrix-identity-spoofing-gua, review-cleanups; sync-limited-timeline-backfi was discovered during matrix-sync-loop) on branch agents-matrix-connector, base c41fd50, merged to main as 038b4f9 via https://github.com/szymonrychu/agents-matrix-connector/pull/1 (43 commits in the repo log). Epic review verdict: PASS (2026-10-25); full suite 188 passed, lint, lint:chart, test:chart, uv lock --check green. Deploy outcome: main CI run 40238165803 first failed because the Harbor secrets were not set; re-run green after the user set them; image harbor.szymonrichert.pl/charts/agents-matrix-connector:0.1.0-main.038b4f9. Live deploy is in the depl epic.

### Tasks

Status of all 27 is done; every verified head below appears in `git log` of the epic. Review rounds are fix rounds from the orchestrator notes; tasks not named in the notes have none recorded. The per-task verification tail was not kept in the notes; the epic-level tail is "188 passed" (full suite, local Postgres override; Docker disk full so testcontainers not exercised locally).

| Task | Status | Verified head | Fix rounds |
|---|---|---|---|
| mxc-scaffold-and-cli | done | 936fea8 | 0 recorded |
| access-policy-engine | done | 60ec1f6 | 0 recorded |
| matrix-client-and-fake-hs | done | f136e44 | 0 recorded |
| mxc-common-session-names | done | f136e44 | 0 recorded |
| mxc-schema-migrations | done | f60b8d0 | 0 recorded |
| mxc-settings-model | done | ded949c | 0 (one finding dropped) |
| room-and-event-discovery | done | 7a88b5e | 0 recorded |
| directory-repository | done | 60cb4a7 | 0 recorded |
| inbound-queue-repository | done | a9ff63e | 0 recorded |
| rules-and-settings-repo | done | 88b5ca0 | 0 recorded |
| runs-and-outbound-repo | done | 073464c | 0 recorded |
| api-rooms-and-users | done | 93f1c0c | 0 recorded |
| chat-prompt-render | done | fb28795 | 0 recorded |
| matrix-sync-loop | done | 6e83f49 | 1 (pre-join history skipped, lost filter recreated) |
| sync-limited-timeline-backfi | done | 3a43978 | 0 recorded |
| reply-tracker | done | 301300a | 1 (poisoned run/row isolation) |
| api-rules-and-settings | done | 3822342 | 1 (test helpers to conftest/api_helpers, noqa removed) |
| dispatch-worker | done | 8912681 | 1 (run_rows moved to db/inbound.py) |
| mxc-openapi-and-readme | done | 3af4f6e | 2 (reason constants; single SESSION_GONE) |
| mxc-service-entrypoints | done | f9e1156 | 1 (plain MigrateSettings) |
| mxc-chart-workloads | done | 77b1f81 | 1 (restored ci/lint-values.yaml) |
| mxc-dockerfile-and-ci | done | 433e873 | 0 (finding dropped) |
| mxc-e2e-api | done | 79230b4 | 0 recorded |
| mxc-operations-docs | done | 645f6d5 | 1 (README body storage per D7, MEMORY appservice reasons per D2) |
| mxc-chart-network | done | 5b43a59 | 1 (ingress.denySourceRanges for the depl consumer) |
| matrix-identity-spoofing-gua | done | 3157bce | 0 recorded (added by security review) |
| review-cleanups | done | 04b8172 | 0 recorded (added by scope audit and security review) |

Notes and files agree; no row contradicts.

### Rulings

- mxc-settings-model: reviewer flagged api_networks() as extra; dropped. Why: agents-webhook api/app.py:73 feeds it to SourceAllowlist and api-rooms-and-users mirrors that allowlist. Cost if wrong: an unused setting in the model.
- reply-tracker: first-run NotFound becomes message_failed plus a notice. Why: a lost first run must not retry forever. Cost if wrong: a user sees a failure notice for a transient miss.
- mxc-dockerfile-and-ci: dropped the e2e, tag and refuse-existing-version CI jobs as acceptable. Why: spec lists main only; e2e runs in the test job via plain pytest. Cost if wrong: no tag-release or duplicate-version guard in CI.
- Epic review: RuleExists noqa N818 dropped. Why: the task spec fixes the name RuleExists, accepted in its task review. Cost if wrong: one lint suppression stays.
- Security review: HIGH facebook-id spoof and MEDIUM alias spoof turned into task matrix-identity-spoofing-gua; LOW 502 str(exc) and Dockerfile pins plus the scope-audit duplicate utcnow() (worker.py:57, tracker.py:53, sync.py:78) turned into review-cleanups. Cost if wrong: n/a, both done.
- Security review dropped: untrusted-input preamble on first turn only (D8 by design); no oauth2-proxy sidecar or NetworkPolicy in the chart (SSO via pod annotations from depl task helmfile-matrix-releases, CIDR allowlist fails closed). Cost if wrong: chart exposed without SSO if the depl annotations are not applied.
- Scope audit: no gaps; G1, G5 and the live half of G6 placed in agents-matrix-connector-depl by the split. Cost if wrong: those goals ship late.

### Discovered and blocked

- Epic frontmatter lists blocker webhook-event-filters (another epic); owner of that epic clears it.
- Docker disk full locally, so testcontainers tests were not run locally; CI ran them. The user clears local disk.
- Main CI Harbor secrets (HARBOR_USERNAME/HARBOR_PASSWORD) were missing on szymonrychu/agents-matrix-connector; the user set them, CI re-run green. Cleared.
- Depl follow-ups noted: service-token file under values/agents-orchestrator/ must be added to test_values_dir_moved exact list; apply-smoke-matrix request must say the services Secret changed. Owner: depl epic.

### Not pushed

Nothing in code/agents-matrix-connector: main equals origin/main (038b4f9). The workbench superrepo commits (ticket moves, submodule pointer) were not checked here; the user or orchestrator pushes them.

### Lessons routed to

- Missing CI secrets surfaced only on the first main run: add a check to the component deploy preflight (gh secret list must show the registry secrets before merge).
- Review findings of the same shape recurred (test helpers in wrong place, noqa suppressions, duplicated constants/clock): add a lint rule or a test for no duplicate reason constants and no `noqa` on fixture reimports.
- Spoofing via foreign-server ids found only in the security review: add a test in the policy suite asserting ids are bound to the bridge server (done in matrix-identity-spoofing-gua); the judgement call to run a security review per epic stays in start-development.
