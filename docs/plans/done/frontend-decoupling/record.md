# frontend decoupling record

## Asked

Decouple the web frontend from the orchestrator microservice: the UI ships and runs on its own (`agents-web`, nginx-unprivileged image, own chart and CI), talks to the orchestrator only through its HTTP API, one host with path routing (`/` UI, `/api` orchestrator), runtime `config.json` backends. The orchestrator becomes API-only. Released and deployed in two live steps.

## Shipped

Epic review verdict: pass (whole diff). All 16 tasks done. Live: agents-web `0.1.0-main.cedcbbc` on `/`, agent-orchestrator `0.1.0-main.a4be86b` (API-only) on `/api`; smoke OK after each apply and after the final re-pin.
PRs merged: agents-web #1 #2 #3 #4, agent-orchestrator #13, agents-helmfile #18 #19 (all github.com/szymonrychu/<repo>/pull/<n>).
Commits since base: agents-web bbeab79..cedcbbc (19 commits), agent-orchestrator b7906aa..a4be86b (3), agents-helmfile 8a11c0b..cc33dd2 (11).

## Tasks

Verified head = `verified_head` in the task file; this record was written without the plan-execute return value, so independent-verifier heads, red evidence, `declined`, `cannotVerify` and `forwardMerged` were not available (unknown). Verification tail (summary line) is unknown for every row: not in the notes given. Rounds = fix rounds after the first review, from the orchestrator notes (one implementer + one sonnet reviewer each).

| Task | Repo | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|---|
| web-openapi-vendor | agents-web | done | b2d2d30 | 0 fix | unknown |
| web-runtime-config | agents-web | done | 37e5a1b | 0 fix | unknown |
| web-backend-menu | agents-web | done | 61c1def | 1 fix (menu entries memoised) | unknown |
| web-nginx-image | agents-web | done | 42dd178 | 0 fix | unknown |
| web-chart-workload | agents-web | done | 77a42eb | 0 fix | unknown |
| web-chart-config-ingress | agents-web | done | d9aefa2 | 2 fix (test:chart glob; helm test pod pinned and hardened) | unknown |
| web-ci-release | agents-web | done | d071d6e | 0 fix | unknown |
| web-docs-memory | agents-web | done | e20b79d | 0 fix | unknown |
| orch-drop-spa-mount | agent-orchestrator | done | 9b5d3ae | 0 fix | unknown |
| orch-drop-frontend-build | agent-orchestrator | done | 2dec27b | 0 fix | unknown |
| smoke-web-ui | agents-helmfile | done | 024e352 | 0 fix (2 live bugs fixed after cutover, see Rulings) | unknown |
| deploy-pin-web | agents-helmfile | done | 46ef967 | 0 fix (re-pinned to db1f482 after failed apply) | unknown |
| apply-smoke-web-cutover | agents-helmfile | done | 863180f | 0 fix (points_actual 2) | unknown |
| deploy-pin-orch-no-spa | agents-helmfile | done | 13c35f9 | 0 fix | unknown |
| apply-smoke-orch-no-spa | agents-helmfile | done | 29bd7c7 | 0 fix | unknown |
| repin-web-after-review-fixes | agents-helmfile | done | c99cfdc | 0 fix | unknown |

Approvals (approvals.json; plan-execute `approvals` return not available, status from task files and notes):

| Id | Text | Decisions | Tasks | Status |
|---|---|---|---|---|
| A | Decouple the frontend; UI runs on its own, talks to orchestrator only via HTTP API | D1 D3 D9 | 15 tasks (all but repin) | delivered |
| T1 | New repo agents-web, history kept | D1 D5 D12 | web-* (8) | delivered |
| U2 | One host, path routing: UI /, orchestrator /api | D2 D6 D7 D13 | web-chart-config-ingress, smoke-web-ui, deploy-pin-web, apply-smoke-web-cutover | delivered |
| C3 | Runtime config.json backends set by chart | D3 D14 | web-runtime-config, web-backend-menu, web-chart-config-ingress, deploy-pin-web | delivered |
| N4 | nginx-unprivileged static image | D4 D15 | web-nginx-image, web-chart-workload, web-ci-release | delivered |
| R5 | Releases, pin bumps, apply plus smoke are epic tasks | D8 D10 D16 | web-ci-release, deploy-pin-web, apply-smoke-web-cutover, deploy-pin-orch-no-spa, apply-smoke-orch-no-spa | delivered |
| H6 | Headless parity; kind e2e keeps passing | D5 D9 D17 | orch-drop-spa-mount, orch-drop-frontend-build | delivered (e2e evidenced by PR #13 CI) |
| O7 | Runs after agent-init-scripts and cluster-scaling, moves UI as it stands | D11 D18 | orch-drop-frontend-build, web-openapi-vendor | delivered |

## Rulings

- Repo name: user asked about "agents-frontend", then chose "Keep agents-web as is". Cost if wrong: a repo rename.
- Repo creation and every live apply run by the orchestrator, not subagents (classifier refuses them there; user approved the rules). Cost if wrong: none, only who runs it.
- orch-drop-frontend-build: AC7 amended (it contradicted the requirement's `sync:api` README note); AC6 evidenced by PR #13 CI e2e pass instead of a local run. Cost if wrong: a README/AC mismatch, or an unproven e2e (CI run is the proof).
- deploy-pin-web: first live apply failed on duplicate imagePullSecrets (chart concatenated values and global). Root fix in agents-web PR #2 (dedupe), re-pinned to db1f482; agent-orchestrator untouched by the failed apply. Cost if wrong: a repeat failed apply on the live namespace.
- smoke-web-ui: two live bugs fixed after cutover (port-forward hit the SSO sidecar; config.json keyed by id); user confirmed UI loads (Q6).
- Security review: MEDIUM regctl-installer@main acted on (pinned, PR #3). Dropped: MEDIUM in-cluster http-insecure port to static UI (static content; NetworkPolicy is new scope); LOW mutable base tags, missing nginx security headers, origin check scope (match existing repos / speculative). Cost if wrong: unpinned base tags and no nginx headers stay until a hardening epic.
- Epic review, acted on: chart config.json validation parity with parseConfig and helm test bypassing the sidecar (agents-web PR #4); re-pinned live to cedcbbc (task repin-web-after-review-fixes, helmfile PR #19), smoke OK.
- Epic review, declined: image-smoke vs old test_spa case mapping (AC5 judgement, covered per task); stale `.dockerignore` node lines (not correctness). Cost if wrong: a coverage gap in image smoke; cosmetic.

## Discovered and blocked

- Clusters menu slot (order 10) is not registered; configuration-improvements owns it. Clearable by that epic.
- The plan-execute return (`declined`, `cannotVerify`, `forwardMerged`, per-task verifier heads, red evidence) was not supplied to this record: unknown. The orchestrator can add it.
- Blocked items: none otherwise.

## Not pushed

Workbench main: commits for this epic (ticket files, submodule pointer bump 10bb104, this record) are local; the record itself is uncommitted. Pusher: the orchestrator. Submodule repos: all PRs merged, nothing unpushed known.

## Lessons routed to

- Duplicate imagePullSecrets failed only at live apply: add a chart/helmfile render test that fails on duplicate imagePullSecrets (added in d9e6867 in agents-helmfile; add the same to the agents-web chart tests).
- Chart config.json validation drifted from `parseConfig`: add a test that feeds the same invalid fixtures to both (shared fixture list in agents-web).
- Unpinned action `regctl-installer@main`: add a CI lint (`scripts/ci.test.mjs`) failing on `uses:` refs not pinned to a SHA.
- Smoke port-forward hit the SSO sidecar and config.json keyed wrongly: smoke checks now cover both (14a1d94, 70d8073); no further check.
- AC contradicting a requirement note (orch-drop-frontend-build AC7): judgement call, edit the plan-writing guidance in start-development to cross-check ACs against requirement text.
