# agent-orchestrator record

## Summary

Asked: agent-orchestrator, a web UI and headless /api/v1 that define, run, message and discard clusters of claude-code-wrapper pods (round-robin dispatch, peer messaging, shared RWX workspace, any-mcp via onStart hook, own Helm chart, bench CLI, Harbor image and chart CI).
Shipped: all 50 planned tasks built and landed on the epic branch; PR https://github.com/szymonrychu/agent-orchestrator/pull/1 merged as ccb7c04 with all PR CI green. Final tip: unit 394 passed, integration against the real wrapper 8 passed, kind e2e 8 passed, chart tests, lint, chart lint, frontend lint/test (90)/build green.
Verdict: pass with one open item. The main-branch CI run after merge (39910755074) FAILED at "Login to Harbor" in the images job: HARBOR_PASSWORD was empty. The Harbor secrets were set afterwards (username from GitLab, password by the user); no green main run publishing the image and chart has been observed. chart-publish-tag, e2e and chart-publish were skipped in that run.

## Planned vs built

50 planned, 50 present with a verifier head. Source: the last return in which each task is complete (returns 1-10 under run-agent-orchestrator), the task files and the PR log. "rounds" and "red" describe the last run that touched the task: a later fix round overwrites the first-round `tests.red`, so "none this run" does not mean the first round had no red. Task files carry `actual: ""` for every task, so actual minutes are unknown. No `tdd-revert` result is quoted as red evidence. Returns 1-4 listed tasks as `unverified` (9, 5, 6, 20 entries); the final returns list none. Return 1 `finished: false`, returns 5-10 `finished: true`; `scopeAudit` is null in every return and `audit` is "off", so the A1-A27 scope audit was done by the orchestrator review, not by the workflow.

| task | status | rounds (last run) | return | files | verifier head | verification (passed; command) | red (implementer tests.red, last run) | est min | actual |
|---|---|---|---|---|---|---|---|---|---|
| ambiguous-fail-releases-agen | built, verified | 1 | 6 | 3 | 165785929 | pass; uv run pytest tests/test_ambiguous_verify.py tests/test_dispatch_queue | yes | 5 | unknown |
| ambiguous-send-verifier | built, verified | 2 | 2 | 0 | 3589f407d | pass; uv run pytest tests/test_ambiguous_verify.py -q && mise run lint | none this run | 6 | unknown |
| api-clusters-and-agents | built, verified | 1 | 1 | 8 | 8d361062e | pass; uv run pytest tests/test_api_clusters.py -q && mise run lint | yes | 6 | unknown |
| api-events-and-streams | built, verified | 2 | 1 | 2 | 77697b02f | pass; uv run pytest tests/test_api_streams.py -q && mise run lint | yes | 6 | unknown |
| api-messages-and-commands | built, verified | 1 | 1 | 5 | 9e2081381 | pass; uv run pytest tests/test_api_messages.py -q && mise run lint | yes | 6 | unknown |
| bench-cli | built, verified | 1 | 5 | 13 | 503cf0d19 | pass; uv run pytest tests/test_bench.py -q && mise run lint | yes | 6 | unknown |
| chatlog-trim-test-fast | built, verified | 1 | 9 | 3 | 5c862fc25 | pass; cd frontend && npx vitest run src/chat && npm run lint | none this run | 5 | unknown |
| check-jobs | built, verified | 1 | 5 | 6 | 2f18e52c6 | pass; uv run pytest tests/test_checks.py -q && mise run lint | yes | 6 | unknown |
| cluster-token-derivation | built, verified | 2 | 1 | 1 | dc7d65767 | pass; uv run pytest tests/test_tokens.py -q && mise run lint | none this run | 5 | unknown |
| clusters-repository | built, verified | 3 | 1 | 2 | a6ea51602 | pass; uv run pytest tests/test_clusters_repo.py -q && mise run lint | yes | 5 | unknown |
| container-images-ci | built, verified | 1 | 3 | 5 | e9df1b422 | pass; uv run pytest tests/test_images.py -q && mise run lint | yes | 6 | unknown |
| contract-test-5xx-mapping | built, verified | 2 | 7 | 1 | 54bd9178f | pass; uv run pytest tests/test_fake_wrapper_contract.py tests/test_wrapper_c | yes | 5 | unknown |
| discard-hook-and-export | built, verified | 1 | 5 | 5 | e00e08167 | pass; uv run pytest tests/test_discard_hook.py -q && mise run lint | yes | 6 | unknown |
| discard-quiesce-before-expor | built, verified | 2 | 6 | 1 | 6e26b8993 | pass; uv run pytest tests/test_discard_hook.py tests/test_reconciler.py -q & | none this run | 6 | unknown |
| dispatch-queue-sql | built, verified | 2 | 1 | 2 | 0b871e064 | pass; uv run pytest tests/test_dispatch_queue.py -q && mise run lint | yes | 5 | unknown |
| dispatcher-loop | built, verified | 3 | 2 | 1 | d1399d0ae | pass; uv run pytest tests/test_dispatcher.py -q && mise run lint | none this run | 5 | unknown |
| entrypoints-and-singleton | built, verified | 1 | 5 | 6 | fab4fae6c | pass; uv run pytest tests/test_entrypoints.py -q && mise run lint | none this run | 6 | unknown |
| events-store | built, verified | 1 | 1 | 2 | 75f4dffcf | pass; uv run pytest tests/test_events_store.py -q && mise run lint | yes | 5 | unknown |
| fake-wrapper-contract | built, verified | 2 | 1 | 1 | 41eb3b9ed | pass; uv run pytest tests/test_fake_wrapper_contract.py -q && mise run lint | yes | 6 | unknown |
| fe-api-client-and-stream | built, verified | 1 | 2 | 6 | 6e19b7dc5 | pass; cd frontend && npm ci --no-audit --no-fund && npx vitest run src/api/s | yes | 6 | unknown |
| fe-chat-log-paging | built, verified | 2 | 2 | 2 | c36facd7a | pass; cd frontend && npm ci --no-audit --no-fund && npx vitest run src/chat/ | yes | 6 | unknown |
| fe-chat-model | built, verified | 2 | 2 | 2 | f414e585a | pass; cd frontend && npm ci --no-audit --no-fund && npx vitest run src/chat/ | yes | 5 | unknown |
| fe-cluster-form | built, verified | 2 | 2 | 2 | a9f12d05d | pass; cd frontend && npm ci --no-audit --no-fund && npx vitest run src/clust | none this run | 6 | unknown |
| fe-composer-and-queue-strip | built, verified | 2 | 2 | 1 | bf7f8d672 | pass; cd frontend && npm ci --no-audit --no-fund && npx vitest run src/chat/ | none this run | 6 | unknown |
| fe-context-gauge | built, verified | 0 | 1 | 2 | 004aeb059 | pass; cd frontend && npm ci --no-audit --no-fund && npx vitest run src/ribbo | yes | 5 | unknown |
| fe-scaffold | built, verified | 1 | 1 | 10 | 56a20e95d | pass; cd frontend && npm ci --no-audit --no-fund && npx vitest run src/App.t | none this run | 6 | unknown |
| fe-shell-and-ribbon | built, verified | 1 | 2 | 10 | 44990c5d4 | pass; cd frontend && npm ci --no-audit --no-fund && npx vitest run src/ribbo | yes | 6 | unknown |
| fe-theme-port | built, verified | 3 | 1 | 0 | 272fd0d1b | pass; cd frontend && npm ci --no-audit --no-fund && npx vitest run src/layou | yes | 6 | unknown |
| fixtures-not-secret-shaped | built, verified (gate-repeat, ruled) | 2 | 8 | 0 | e147d5a19 | pass; uv run pytest tests/test_chart_config.py -q -p no:cacheprovider && mis | yes | 5 | unknown |
| frontend-api-types-regen | built, verified | 2 | 10 | 2 | 48a230596 | pass; cd frontend && npm run check:api && cd .. && uv run pytest tests/test_ | none this run | 5 | unknown |
| helm-chart-ci-publish | built, verified | 2 | 3 | 1 | d85839940 | pass; uv run pytest tests/test_chart_ci.py -q && mise run lint | none this run | 6 | unknown |
| helm-chart-config-postgres | built, verified | 1 | 1 | 8 | e24181155 | pass; uv run pytest tests/test_chart_config.py -q && mise run lint && mise r | none this run | 6 | unknown |
| helm-chart-deployments | built, verified | 1 | 1 | 7 | bb95fe6db | pass; uv run pytest tests/test_chart_deployments.py -q && mise run lint && m | yes | 6 | unknown |
| helm-chart-rbac-and-ingress | built, verified | 2 | 1 | 1 | 5e75aee1e | pass; uv run pytest tests/test_chart_rbac_ingress.py -q && mise run lint &&  | none this run | 6 | unknown |
| helm-chart-scaffold | built, verified | 1 | 1 | 8 | dcbbab0f2 | pass; uv run pytest tests/test_chart_scaffold.py -q && mise run lint && mise | none this run | 6 | unknown |
| images-test-precision | built, verified | 1 | 6 | 3 | a27c8c3b7 | pass; uv run pytest tests/test_images.py -q && mise run lint | yes | 5 | unknown |
| ingester | built, verified | 1 | 2 | 4 | c551093a9 | pass; uv run pytest tests/test_ingester.py -q && mise run lint | yes | 6 | unknown |
| ingress-node-denylist | built, verified | 1 | 6 | 4 | 23ffc2376 | pass; uv run pytest tests/test_chart_rbac_ingress.py -q && mise run lint &&  | yes | 6 | unknown |
| k8s-object-renderer | built, verified (land-failed, ruled) | 1 | 2 | 7 | 1ad933b | pass; uv run pytest tests/test_render.py -q && mise run lint | none this run | 6 | unknown |
| kind-e2e | built, verified | 3 | 5 | 2 | 56e5443e4 | pass; mise run test:e2e && mise run lint | yes | 6 | unknown |
| migrations-and-schema | built, verified | 2 | 1 | 1 | 25a8811ae | pass; uv run pytest tests/test_migrations.py -q && mise run lint | yes | 6 | unknown |
| readme-api-and-openapi | built, verified (gate-repeat, ruled) | 2 | 1 | 1 | 87131ab81 | pass; uv run pytest tests/test_readme_api.py -q && mise run lint | none this run | 6 | unknown |
| reconciler-loop | built, verified (gate-repeat, ruled) | 3 | 3 | 1 | ab3e57ca8 | pass; uv run pytest tests/test_reconciler.py -q && mise run lint | none this run | 6 | unknown |
| scaffold-repo-and-cli | built, verified | 1 | 1 | 11 | e1743b1b7 | pass; uv run pytest tests/test_cli.py -q && mise run lint | yes | 6 | unknown |
| session-bootstrap | built, verified (gate-repeat, ruled) | 2 | 4 | 2 | e91ee1a75 | pass; uv run pytest tests/test_session_bootstrap.py -q && mise run lint | none this run | 6 | unknown |
| settings-model | built, verified | 2 | 2 | 2 | b5365cc8c | pass; uv run pytest tests/test_settings.py -q && mise run lint | none this run | 5 | unknown |
| spa-serving-and-dockerfile | built, verified | 1 | 2 | 6 | 094626829 | pass; uv run pytest tests/test_spa.py -q && mise run lint | yes | 6 | unknown |
| stored-session-resume | built, verified | 2 | 6 | 1 | 45da3af02 | pass; uv run pytest tests/test_session_bootstrap.py -q && mise run lint | none this run | 5 | unknown |
| wrapper-5xx-ambiguous | built, verified | 3 | 6 | 0 | dbc07550d | pass; uv run pytest tests/test_wrapper_client.py tests/test_dispatcher.py -q | yes | 5 | unknown |
| wrapper-client-and-sse | built, verified | 2 | 1 | 2 | 7844dd22f | pass; uv run pytest tests/test_wrapper_client.py -q && mise run lint | none this run | 6 | unknown |

Approvals (ledger `approvals.json`, all 27 entries `approved`; status from the latest return that names the id):

| id | text | decisions | tasks | status |
|---|---|---|---|---|
| A1 | Left ribbon lists the active pods and clusters, each with an indicator: waiting or working, how many agent pods run, and | D13, D11 | fe-context-gauge, fe-shell-and-ribbon, api-clusters-and-agents, ingester | delivered (return 2) |
| A2 | Main view is a chat with smart message loading showing agent activity: past inputs, outputs, thinking and tool calls. | D5, D14 | wrapper-client-and-sse, events-store, ingester, api-events-and-streams, fe-chat-model, fe-chat-log-paging, fe-composer-and-queue-strip, chatlog-trim-test-fast | delivered (return 9) |
| A3 | The web UI theme matches the ros2-lerobot-sverve-platform web UI. | D12 | fe-scaffold, fe-theme-port, fe-api-client-and-stream | delivered (return 2) |
| A4 | Pods and groups of pods (clusters) can be defined with their config and discarded. | D6, D8, D15 | clusters-repository, k8s-object-renderer, reconciler-loop, session-bootstrap, api-clusters-and-agents, fe-cluster-form, discard-hook-and-export | delivered (return 5) |
| A5 | A headless API orchestrates and communicates with the sessions and is the unified router for future use at scale (tatara | D1, D11 | api-clusters-and-agents, api-messages-and-commands, api-events-and-streams, readme-api-and-openapi, frontend-api-types-regen | delivered (return 10) |
| A6 | Messages to a cluster go round-robin: the agent that has been free the longest receives the message. | D2, D4 | dispatch-queue-sql, dispatcher-loop, api-messages-and-commands | delivered (return 2) |
| A7 | Agents in a cluster can communicate with each other. | D7, D8 | cluster-token-derivation, k8s-object-renderer | escalated (last return 2); landed per orchestrator rulings and scope audit, not re-evaluated by a later return |
| A8 | A cluster's agents share a PVC on RWX rook-ceph CephFS. | D6 | k8s-object-renderer, reconciler-loop | escalated (last return 3); landed per orchestrator rulings and scope audit, not re-evaluated by a later return |
| A9 | Every new session starts with any-mcp preinstalled: no derived agent image; a per-cluster rendered onStart hook pip-inst | D8, D16 | settings-model, k8s-object-renderer, kind-e2e | delivered (return 5) |
| A10 | The setup lets the user test whether round-robin plus multiple agents plus inter-agent messaging speeds up thinking and  | D10, D18 | check-jobs, bench-cli | delivered (return 5) |
| A11 | Decentralised microservices coordinating only through a Postgres queue (CNPG), with the orchestrator calling the Kuberne | D1, D2, D3, D20 | scaffold-repo-and-cli, settings-model, migrations-and-schema, clusters-repository, events-store, entrypoints-and-singleton | delivered (return 5) |
| A12 | Integration with claude-code-wrapper is verified against the real wrapper, not only a fake. | D19 | wrapper-client-and-sse, fake-wrapper-contract, session-bootstrap | escalated (last return 4); landed per orchestrator rulings and scope audit, not re-evaluated by a later return |
| A13 | Delivered as a new component code/agent-orchestrator with public GitHub origin szymonrychu/agent-orchestrator, CI, the o | D9, D17, D19, D21 | scaffold-repo-and-cli, settings-model, reconciler-loop, spa-serving-and-dockerfile, container-images-ci, kind-e2e, images-test-precision, fixtures-not-secret-shaped | delivered (return 8) |
| A14 | In-cluster callers cannot reach the API: it enforces a direct-peer source allowlist (ORCH_ALLOWED_CIDRS, health routes e | D22 | scaffold-repo-and-cli, settings-model, clusters-repository, api-clusters-and-agents, k8s-object-renderer, entrypoints-and-singleton, container-images-ci, readme-api-and-openapi, kind-e2e, ingress-node-denylist | delivered (return 6) |
| A15 | A failed send never wedges round-robin and is retried automatically: the reservation is released on every non-accept out | D23, D24 | migrations-and-schema, dispatch-queue-sql, wrapper-client-and-sse, fake-wrapper-contract, ingester, dispatcher-loop, clusters-repository, ambiguous-send-verifier, fe-composer-and-queue-strip, ambiguous-fail-releases-agen, wrapper-5xx-ambiguous, contract-test-5xx-mapping | delivered (return 7) |
| A16 | Two dispatchers never double-dispatch under READ COMMITTED: the claim writes agents.last_dispatched_at and the pick read | D23 | migrations-and-schema, dispatch-queue-sql | delivered (return 1) |
| A17 | Singleton failover is fast and loud: libpq keepalives and tcp_user_timeout on the lock connection, a lock-held heartbeat | D25 | settings-model, entrypoints-and-singleton | delivered (return 5) |
| A18 | A slow or ambiguous send is never sent twice: a send timeout well below the dispatching stale cutoff, a heartbeat on the | D24 | settings-model, migrations-and-schema, wrapper-client-and-sse, fake-wrapper-contract, dispatch-queue-sql, dispatcher-loop, api-messages-and-commands, ambiguous-send-verifier | delivered (return 2) |
| A19 | Everything lives in namespace agents and clusters are told apart by labels (no ORCH_CLUSTERS_NAMESPACE): object names us | D26 | settings-model, clusters-repository, k8s-object-renderer, reconciler-loop, check-jobs, kind-e2e, helm-chart-rbac-and-ingress | delivered (return 5) |
| A20 | The reconciler cannot read Secrets: secrets verbs are create, patch and delete only, in namespace agents; cluster Secret | D26, D9 | reconciler-loop, kind-e2e, helm-chart-rbac-and-ingress | delivered (return 5) |
| A21 | Session adoption is correct: adopt only creating, ready or busy sessions, resume stopped or failed sessions that have a  | D27 | wrapper-client-and-sse, fake-wrapper-contract, dispatcher-loop, dispatch-queue-sql, migrations-and-schema, session-bootstrap, stored-session-resume | delivered (return 6) |
| A22 | Sessions and check Jobs use one rendered workdir path (/workdir/<spec.workdir>), pinned by a test in each of the rendere | D27 | k8s-object-renderer, session-bootstrap, check-jobs | delivered (return 5) |
| A23 | A targeted message never blocks the queue: the claim skips a message whose target is busy and fails one whose target is  | D23 | dispatch-queue-sql, api-messages-and-commands | delivered (return 1) |
| A24 | Dispatch is FIFO per cluster under concurrent dispatchers, enforced by a per-cluster transaction-level advisory lock in  | D23 | dispatch-queue-sql, dispatcher-loop | delivered (return 2) |
| A25 | Discard deletes everything: the cluster's Kubernetes objects, its PVC and its whole chat history (messages, events, turn | D15, D3 | migrations-and-schema, settings-model, clusters-repository, reconciler-loop, discard-hook-and-export, api-clusters-and-agents, fe-cluster-form, bench-cli, kind-e2e, discard-quiesce-before-expor | delivered (return 6) |
| A26 | AskUserQuestion is disabled in the rendered wrapper config; agents get an appended system prompt instructing them to ask | D8 | k8s-object-renderer | escalated (last return 2); landed per orchestrator rulings and scope audit, not re-evaluated by a later return |
| A27 | agent-orchestrator ships its own Helm chart chart/agent-orchestrator, started from helm create: the four component Deplo | D28, D17, D9 | helm-chart-scaffold, helm-chart-config-postgres, helm-chart-deployments, helm-chart-rbac-and-ingress, helm-chart-ci-publish, kind-e2e | delivered (return 5) |

## Deviations and rulings

- Branch values: implementers returned descriptive branch strings; rewritten to the task branches. Why: the land step needs real refs. Cost if wrong: a task lands from the wrong ref; each task's `verified_head` was read back, so low.
- 21 tasks had missing owner dependencies; added. Why: the dependency graph under-declared owners, causing dependency-failed cascades in returns 1-4. Cost if wrong: wrong wave order, caught by dependency-failed rather than a silent merge.
- k8s-object-renderer: land-failed (rebase conflict from dependency commits duplicated under other SHAs, in settings.py and tests/test_settings.py). Ruling: its own commits 8624fe8/55dbb33 were cherry-picked onto the epic tip as fcd7210/1ad933b and fast-forwarded; verified there with test_render.py + test_settings.py 40 passed, lint clean. Cost if wrong: a dropped renderer change; reduced because ledger A7/A26 were later checked by the scope audit.
- Parking-wording false-positive gate-repeats accepted (rulings.json): readme-api-and-openapi (ROADMAP.md:5 describes the bench experiment delivered by bench-cli), reconciler-loop (loop.py:118 documents the seam the discard-hook-and-export task fills), session-bootstrap (loop.py:168/348, sessions.py:6/12 restate required retry-on-next-tick). Cost if wrong: real deferred work hidden behind wording; each was verified true on the cited SHA (ab3e57c, e91ee1a).
- Pre-implementation design review (fable, opus, sonnet; interrogate-verdict.md, 2026-10-22): 11 Act-on items. Taken: in-cluster source allowlist and ClusterSpec hardening, release of the dispatch reservation on non-accept outcomes, double-dispatch fix via agents.last_dispatched_at plus a forced-interleaving test, singleton keepalives and heartbeat, ambiguous sends never auto-retried, reserved agent-<slug> object prefix and refusal to touch unlabelled objects, secrets verbs create/patch/delete only, session adoption rules, one workdir path, head-of-line skip and target_gone, per-cluster advisory lock for FIFO. The separate-namespace "Consider" went to the user and was decided as one namespace `agents` with labels (A19). Cost if wrong: the dismissed NetworkPolicy fix would not have worked on flannel.
- Post-implementation panel review (fable, opus, sonnet), acted on: ingress SNAT bypass (node-IP denylist at the ingress, chart allow/denySourceRanges, README boundary; task ingress-node-denylist), stored dead sessions resumed or replaced (stored-session-resume), ambiguous-deadline reservation released (ambiguous-fail-releases-agen), wrapper 500/502 routed through the verifier (wrapper-5xx-ambiguous, contract-test-5xx-mapping), discard quiesces agents before export (discard-quiesce-before-expor). Other design-review items verified implemented.
- Merge-time rulings: GitGuardian flagged two fake fixtures; the user resolved the incidents and fixtures were made non-secret-shaped (e147d5a, task fixtures-not-secret-shaped). Frontend CI timed out on a slow runner; the trim window was injected (5c862fc, chatlog-trim-test-fast). Generated API types were stale; regenerated and pinned (fc25bf1, 48a2305, frontend-api-types-regen). Harbor CI secrets set (username from GitLab, password by the user). Cost if wrong: the fixture change could hide a real secret pattern check (it is test data only); the regen is pinned by an unconditional exact-match test.
- forwardMerged: none in any return. declined: per-task `declined` entries (findings the implementers or triage judged wrong, e.g. ambiguous-send-verifier "no code change") were not escalated; none open.

## Duplicates reconciled

none reported by the workflow (`duplicates` empty in all returns). Overlap seen in the git log: commits e7830e6 and 75f4dff are both "events repository with idempotent insert, gap rows and keyset paging" (events-store); the later one is the landed tip. Renderer commits were duplicated under other SHAs via dependency branches and reconciled by the cherry-pick ruling above.

## Discovered and blocked

- Main CI images job fails at "Login to Harbor" (HARBOR_PASSWORD empty at run 39910755074, 2026-10-23). Secrets set afterwards. Clearing: re-run the main workflow (repo owner/orchestrator) and confirm the image and chart publish; cannot be confirmed from the files. chart-publish, chart-publish-tag and e2e did not run on main.
- Process gaps recorded by the workflow: TDD red missing or after the fact for api-events-and-streams, dispatcher-loop (14 tests written after code; a malformed --exclude-ref made one independent verification fail), fake-wrapper-contract, fe-theme-port, helm-chart-config-postgres, wrapper-5xx-ambiguous (red reproduced by hand), fixtures-not-secret-shaped (gate tdd-skipped). Accepted by the orchestrator; cleared by nobody further.
- Ledger A7, A8, A12, A26: the last return naming them says `escalated`; the cause was dependency-failed cascades and the renderer land-failure, since landed. No later return re-evaluated them; the orchestrator scope audit reports A1-A27 landed with 354 AC refs resolving. Treat as delivered but not workflow-confirmed.
- No-auth API (LAN-only by decision) and `POST /checks` running shell on a cluster PVC are noted risks, acceptable behind the source allowlist; owner is the user. Helmfile release and SOPS secrets are the separate epic agents-helmfile.

## Research that changed the plan

- Lead checks for the design review: workdir.py:103-106 (empty mode resolves /workdir/<name>) led to the single rendered workdir path (A22); session.py:195-231 and config.py:189 (child env is an allow-list, passthrough_env) led to the renderer setting claude.passthrough_env; manager.py:1020-1034 (resume needs a transcript) led to the adoption/resume rules (A21); cluster CNI is flannel with no NetworkPolicy enforcement, so NetworkPolicy was dismissed and a source-address allowlist (A14) used instead.
- Convergent finding of all three panelists on the READ COMMITTED reservation race produced A16 and the forced-interleaving test.

## Cost

Orchestrator ran plan-execute 10 times (1 initial plus 9 resumptions/continuations; continue1-5 logs exist). Rounds per task in the last run: see the table (0-3). Roles: implementers (sonnet, opus on hard tasks per task `model`), independent verifier per task, triage (3 calls per return; token counts in `triageUsage`), panel review by fable/opus/sonnet twice (design, implementation). Workflow `audit` was off. Wall-clock: unknown. Token and dollar totals: unknown.

Estimate vs actual: README Time estimate 284 agent-min (sum of task estimates also 284), critical path 82 min, expected wall 6.3 h; Actual 0 min in README and `actual: ""` in all 50 task files, so actual per task is unknown. Per-task estimates are in the table above.

## MRs and deploy

- PR https://github.com/szymonrychu/agent-orchestrator/pull/1 merged as ccb7c04; the last PR run (39910208427) was green, two earlier PR runs failed (GitGuardian, frontend timeout, stale types, fixed as above).
- Main push run 39910755074: failure (images / Login to Harbor, empty password); lint, test, chart, frontend jobs green.
- Deploy: not done and not in scope (helmfile release is epic agents-helmfile). Image and chart publication to Harbor is unconfirmed.

## Lessons routed to

- Mechanical: a CI step that logs in with a secret should fail the PR pipeline when the secret is unset (add a pre-merge check that asserts the required repo secrets exist, or run the login step in the PR workflow with --no-push). The first publish only ran on main, after merge.
- Mechanical: the verify-task `--exclude-ref` must reject non-ref values; add an argument check/test in verify-task.py (dispatcher-loop's independent verification failed on a pasted worktree description).
- Mechanical: a lint/test check that fixtures are not secret-shaped (GitGuardian) before push.
- Mechanical: enforce owner dependencies at plan time: a ticket.py lint that fails when a task uses a symbol provided by a task not in `depends_on` (21 tasks needed edits, causing dependency-failed cascades).
- Mechanical: land step should refuse or auto-handle dependency commits duplicated under different SHAs (renderer land-failed); add a test for rebase over cherry-picked duplicates in merge.py.
- Judgement: the parking-wording gate flagged three accurate comments; edit the plan-execute gate guidance on when documenting a planned seam is not parking.
- Judgement: record `actual` minutes per task in task files; plan-execute does not populate them (README Actual stays 0), so edit the start-development skill step that closes tasks.
