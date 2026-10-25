# agents-webhook microservice record

## Asked

A separate agents-webhook microservice with its own Postgres database: per-webhook public endpoints https://lab.szymonrichert.pl/webhook/<suffix> (one type, one required preset, basic auth each) for GitHub/GitLab PR/MR and issue events and Grafana alerts. Events go into a FIFO queue with per-endpoint dedup and limits, start agent clusters from presets through the orchestrator API, and (opt-in per preset, reuse_running_agent) route later events to the agent still running for the item. A Webhooks UI entry between Clusters and Presets manages endpoints and shows recent events. Shared library agents-common and the web trigger UI kit are built for agents-schedule-microservice.

## Shipped

All 51 tasks done. Epic review verdict: pass (2026-10-25); scope audit CLEAN (all 10 user requirements delivered, no duplicates); whole-diff review of agents-webhook found 3 medium findings and the security review 2 medium findings, all fixed by tasks added in phase 5 and reviewed PASS; review of agent-orchestrator, agents-common, agents-web and agents-helmfile found nothing.

Merged:
- agents-webhook PR #1 (squash ed3ea7e), #3 (883958c), #4 (cc0f706); #2 closed, superseded.
- agents-helmfile PR #21 (3dc5488).
- agents-web PR #6 (18f5132).
- agent-orchestrator: main a3c1b9d.
- agents-common v0.1.0 and v0.2.0 tags.

Live (agents namespace): agents-webhook 0.1.0-main.cc0f706, agents-webhook-db, agent-orchestrator a3c1b9d and agents-web 18f5132 applied. Post-apply diff: "No affected releases". Smoke: "smoke: OK" including the webhook endpoint checks (logs: .logs/apply-webhook-fixes-postdiff.log, .logs/apply-webhook-fixes-smoke.log).

Suites read: agents-helmfile `mise run test` 116 passed, lint clean; agents-webhook main CI cc0f706 green (500 passed on Linux); agent-orchestrator and agents-web main CI green; agents-web vitest src/webhooks src/presets 58 passed.

## Tasks

Status and verified head are from the task files (all `done`, all with a verified head). Review rounds and per-task verification tails were not in the files I was given: "unknown". Points are planned/actual.

| Task | Status | Verified head | Rounds | Verification tail |
|---|---|---|---|---|
| apply-smoke-webhook | done | 3bfc1dc | unknown | live: postdiff "No affected releases", smoke OK (2/2) |
| common-db-helpers | done | cf6e8e8 | unknown | unknown (1/1) |
| common-orchestrator-client | done | bfebd85 | unknown | unknown (1/1) |
| common-release-v0-1-0 | done | df9cb19 | unknown | unknown (1/1) |
| common-release-v0-2-0 | done | 205c467 | unknown | unknown (2/2); tag content equals HEAD per review |
| common-reuse-running | done | cfaee0c | unknown | unknown (3/3) |
| common-run-tracker | done | 7ae9231 | unknown | unknown (1/2) |
| common-scaffold | done | d551af5 | unknown | unknown (1/1) |
| common-settings-runtime | done | 442b1cf | unknown | unknown (1/2) |
| deploy-pin-orch-service-port | done | 50c82d8 | unknown | unknown (1/1) |
| events-retention-prune | done | 8669596 | unknown | unknown (2/2) |
| helmfile-drop-source-secrets | done | ff483ac | unknown | unknown (2/2) |
| helmfile-service-token | done | 4f572d6 | unknown | unknown (1/1) |
| helmfile-web-webhooks-entry | done | 58f6006 | unknown | unknown (1/1) |
| helmfile-webhook-releases | done | 6b148a0 | unknown | unknown (1/1) |
| ignored-payload-cap | done | 2a7c246 | unknown | unknown (1/1) |
| orch-chart-services-port | done | aa094e8 | unknown | unknown (1/1) |
| orch-preset-reuse-field | done | 6cf0614 | unknown | unknown (2/2) |
| orch-service-port-auth | done | db35508 | unknown | unknown (1/2) |
| orch-service-port-docs | done | 0f45a86 | unknown | unknown (1/1) |
| orch-service-port-e2e | done | 52eb949 | unknown | unknown (1/1) |
| settings-per-subcommand | done | d8d1322 | unknown | unknown (2/2) |
| smoke-webhook-check | done | 6d2a9e0 | unknown | unknown (1/2) |
| web-preset-reuse-row | done | 71d849e | unknown | unknown (2/2) |
| web-trigger-ui-kit | done | ac2d642 | unknown | unknown (1/1) |
| web-webhook-api-client | done | 7619087 | unknown | unknown (1/1) |
| web-webhook-endpoints | done | a2c9c86 | unknown | unknown (5/5) |
| web-webhook-events-page | done | 969c76b | unknown | unknown (1/1) |
| web-webhook-menu-entry | done | bf34a4a | unknown | unknown (1/1) |
| webhook-api-e2e | done | d3bace8 | unknown | unknown (5/3) |
| webhook-api-source-allowlist | done | 60c3fdc | unknown | PASS (security fix; 2/2) |
| webhook-chart-network | done | 1f676e1 | unknown | unknown (1/2) |
| webhook-chart-probe-port | done | 7369648 | unknown | merged as 883958c (1/1) |
| webhook-chart-workloads | done | 5e4a480 | unknown | unknown (1/2) |
| webhook-ci-images | done | 82525c9 | unknown | unknown (1/1) |
| webhook-cli-entrypoints | done | f72f27e | unknown | unknown (1/1) |
| webhook-dispatch-worker | done | 5bafbda | unknown | unknown (1/2) |
| webhook-docs-memory | done | 9b070e3 | unknown | unknown (1/2) |
| webhook-endpoints-repo | done | 0b2d909 | unknown | unknown (3/3) |
| webhook-epic-review-fixes | done | a6557a5 | unknown | PASS (3 review findings; 3/3) |
| webhook-event-store | done | 6c068c7 | unknown | unknown (5/5) |
| webhook-ingest-http | done | 28c0dbf | unknown | unknown (5/5) |
| webhook-normalize | done | 8ae0a33 | unknown | unknown (1/1) |
| webhook-openapi-readme | done | caaa41a | unknown | unknown (1/2) |
| webhook-prompt-render | done | 45f0a93 | unknown | unknown (1/3) |
| webhook-reuse-routing | done | 480e053 | unknown | unknown (5/5) |
| webhook-scaffold | done | 533b527 | unknown | unknown (1/1) |
| webhook-schema-settings | done | e1fd2c4 | unknown | unknown (1/1) |
| webhook-template-memory-cap | done | 379f315 | unknown | PASS (security fix; Linux CI test passes; 2/2) |
| webhook-ui-api | done | 16aac8f | unknown | unknown |

Approvals ledger (approvals.json) at close: A1, A2, A5, A6, A8, A9, A10 `approved`; A3, A4, A7, A11, A12 still `pending` in the file (ledger not updated at close, although their tasks are done; scope audit found all 10 requirements delivered).

## Rulings

- Squash merge for agents-webhook PR #1 (ed3ea7e): GitGuardian flagged two test-fixture strings in old branch commits (since fixed). Squash keeps them out of main history without a force-push. Cost if wrong: the incidents stay on the GitGuardian dashboard until the user marks them false positive; main history is clean.
- Clean fix branches: the review and deploy fixes went on fresh branches from main (PR #3, #4; #2 closed and superseded) rather than extending the flagged branch. Cost if wrong: one extra closed PR.
- Probe-port rollback and its fix: the first helmfile apply rolled back cleanly (Deployment agents-webhook-api not ready, release uninstalled by rollback-on-failure, after 759s) because the oauth2-proxy sidecar rename broke the probe port name. Fixed by webhook-chart-probe-port (numeric probe port, 883958c); second apply succeeded. Cost if wrong: a failed rollout in the live agents namespace; rollback left no residue.
- Copied SOPS db file: values/agents-webhook-db/default.secrets.yaml is a byte copy of values/agent-orchestrator-db/default.secrets.yaml (only backups.s3.accessKey/secretKey plus sops metadata, checked by key name), because the guard hook blocks decryption and the helper cannot copy values; same S3 credentials, separate backup path in common.yaml. Cost if wrong: the webhook DB backups fail; visible in the CNPG ScheduledBackup status.
- trustedProxies as the /32 list: ingress-nginx runs hostNetwork on flannel, so the ingest pod sees the controller node IP or that node's flannel.1/cni0 address; trusted: the 5 node IPs (192.168.1.26-.29, .65) and 10.244.N.0/32 plus 10.244.N.1/32 for N 0..4, never 10.244.0.0/16 (any pod could spoof X-Forwarded-For). Cost if wrong: a node or podCIDR change makes all forges share one rate-limit key until the list is updated.
- Security and review fixes added as tasks in phase 5: webhook-epic-review-fixes (3 medium: lossy draft/changed context, non-UUID preset_id gave 503, 408 body shape), webhook-api-source-allowlist (api reachable in-cluster on the sidecar http-insecure port without SSO), webhook-template-memory-cap (unbounded Jinja filter allocation). Cost if wrong: the findings would ship to the live service.
- Gate Q23: limits (in-progress overall, per endpoint, queue cap, body cap) configurable through chart values, defaults 3, 1, 500, 5 MiB.
- Prompt template: sandboxed Jinja2 with from_json filter, POST /webhooks/api/v1/templates/preview, reason template_error.
- Findings dropped (below medium, declined by reviewers): unused getEvent/getMeta exports and double endpoint fetch in agents-web; duplicate CHANNEL constant; retention keyed on updated_at; hard-coded probe port 8000; claim/release churn when orchestrator is unavailable. Cost if wrong: minor cleanup or edge-case behaviour.

## Discovered and blocked

- GitGuardian incidents for two test-fixture strings remain open on the dashboard: the user marks them false positive.
- Not verifiable by reviewers: orchestrator pytest (needs Docker/testcontainers), that the SOPS service-token hash equals sha256 of the token (secrets not decrypted); both settled by the live smoke (webhook checks OK).
- Approvals ledger shows A3, A4, A7, A11, A12 `pending` though delivered: the supervisor can update the ledger.
- The `.venv` editable install of agents_webhook still points at the removed worktree path (warning printed by ticket.py): the user or supervisor can reinstall.

## Not pushed

none known. The superrepo pins (a0f66e0) and ticket moves (8685b1b) are committed on main; main is not pushed; pushing the superrepo main stays with the user.

## Lessons routed to

- A chart probe referencing a port name that another template (sidecar injection) can rename broke the first live apply: add a chart test asserting probe ports are numeric (done in webhook-chart-probe-port).
- Test fakes returned 404 where the real orchestrator service port returns 403, hiding the non-UUID preset bug: add a contract test in agents-webhook that runs the client against the real route allowlist responses.
- Error body shape drift (408): add a test asserting every error response matches `{"error":{"code","message"}}`.
- Test-fixture strings tripping GitGuardian: add a pre-commit secret scan (gitguardian/ggshield hook) to new public repos.
- Ledger left `pending` at close: add a check in `ticket.py close` that fails on non-terminal approval statuses.
