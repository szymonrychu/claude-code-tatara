# agents-matrix-connector record

## Asked

New Python microservice agents-matrix-connector (own repo, own CNPG database) that logs in to the live Synapse as a bot user, auto-discovers Messenger rooms, users and members bridged by mautrix-meta, applies default-deny allow/deny rules, batches allowed messages per room into one agents-orchestrator session per room and posts each turn's final text back. Plus a UI API under /matrix/api/v1. Request of 2026-10-25. Deploy and the agents-web Chats page moved to epic agents-matrix-connector-depl by the split.

## Shipped

27 tasks (25 planned, 2 added from review: matrix-identity-spoofing-gua, review-cleanups; sync-limited-timeline-backfi was discovered during matrix-sync-loop) on branch agents-matrix-connector, base c41fd50, merged to main as 038b4f9 via https://github.com/szymonrychu/agents-matrix-connector/pull/1 (43 commits in the repo log). Epic review verdict: PASS (2026-10-25); full suite 188 passed, lint, lint:chart, test:chart, uv lock --check green. Deploy outcome: main CI run 40238165803 first failed because the Harbor secrets were not set; re-run green after the user set them; image harbor.szymonrichert.pl/charts/agents-matrix-connector:0.1.0-main.038b4f9. Live deploy is in the depl epic.

## Tasks

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

## Rulings

- mxc-settings-model: reviewer flagged api_networks() as extra; dropped. Why: agents-webhook api/app.py:73 feeds it to SourceAllowlist and api-rooms-and-users mirrors that allowlist. Cost if wrong: an unused setting in the model.
- reply-tracker: first-run NotFound becomes message_failed plus a notice. Why: a lost first run must not retry forever. Cost if wrong: a user sees a failure notice for a transient miss.
- mxc-dockerfile-and-ci: dropped the e2e, tag and refuse-existing-version CI jobs as acceptable. Why: spec lists main only; e2e runs in the test job via plain pytest. Cost if wrong: no tag-release or duplicate-version guard in CI.
- Epic review: RuleExists noqa N818 dropped. Why: the task spec fixes the name RuleExists, accepted in its task review. Cost if wrong: one lint suppression stays.
- Security review: HIGH facebook-id spoof and MEDIUM alias spoof turned into task matrix-identity-spoofing-gua; LOW 502 str(exc) and Dockerfile pins plus the scope-audit duplicate utcnow() (worker.py:57, tracker.py:53, sync.py:78) turned into review-cleanups. Cost if wrong: n/a, both done.
- Security review dropped: untrusted-input preamble on first turn only (D8 by design); no oauth2-proxy sidecar or NetworkPolicy in the chart (SSO via pod annotations from depl task helmfile-matrix-releases, CIDR allowlist fails closed). Cost if wrong: chart exposed without SSO if the depl annotations are not applied.
- Scope audit: no gaps; G1, G5 and the live half of G6 placed in agents-matrix-connector-depl by the split. Cost if wrong: those goals ship late.

## Discovered and blocked

- Epic frontmatter lists blocker webhook-event-filters (another epic); owner of that epic clears it.
- Docker disk full locally, so testcontainers tests were not run locally; CI ran them. The user clears local disk.
- Main CI Harbor secrets (HARBOR_USERNAME/HARBOR_PASSWORD) were missing on szymonrychu/agents-matrix-connector; the user set them, CI re-run green. Cleared.
- Depl follow-ups noted: service-token file under values/agents-orchestrator/ must be added to test_values_dir_moved exact list; apply-smoke-matrix request must say the services Secret changed. Owner: depl epic.

## Not pushed

Nothing in code/agents-matrix-connector: main equals origin/main (038b4f9). The workbench superrepo commits (ticket moves, submodule pointer) were not checked here; the user or orchestrator pushes them.

## Lessons routed to

- Missing CI secrets surfaced only on the first main run: add a check to the component deploy preflight (gh secret list must show the registry secrets before merge).
- Review findings of the same shape recurred (test helpers in wrong place, noqa suppressions, duplicated constants/clock): add a lint rule or a test for no duplicate reason constants and no `noqa` on fixture reimports.
- Spoofing via foreign-server ids found only in the security review: add a test in the policy suite asserting ids are bound to the bridge server (done in matrix-identity-spoofing-gua); the judgement call to run a security review per epic stays in start-development.
