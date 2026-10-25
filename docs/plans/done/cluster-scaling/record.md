# cluster scaling record

## Summary

Asked: agents join and leave a running cluster; the leader scales it between 1 and a cap set at init (ceiling 16) via a scale tool; static clusters offer no scale tool. Shipped: set_replicas guarded writer, scale-down drain, public and agent scale routes, scale tool allow rule, UI scale control and leaving mark, kind e2e, smoke scale step, deploy pin 3b9926d. 10 of 10 planned tasks built. Verdict: pass (2026-10-25); whole-diff review PASS, security none past boundary, CI green on PR #11.

**INCIDENT (live deploy):** helm revision 12 (2026-10-25 08:54 CET, 07:53Z) was an accidental rollback of the live agents namespace to a5b5a75. The plan-execute verifier ran AC3 `command:mise run apply` from the unbuilt deploy-pin tree. The orchestrator re-applied 3b9926d as revision 13 under the user's standing apply approval. Post-apply `mise run diff`: "No affected releases". `mise run smoke` last line: `smoke: OK` (scale 1->2->1, pod-0 uid kept, init scripts succeeded). Fix: AC3 evidence changed to `judgement` ("never run apply as AC evidence") here and in two todo epics; MEMORY note added.

## Planned vs built

Verifier head = `tasks[].verification.head` from run wf_92726cff-61b. Files from `filesChanged` in the return (agent-scale-route and kind-e2e-scaling list test files only; the route feature commit d2c41af landed in the same branch earlier).

| Task | Status | Review rounds | Continuations | Files | Verifier head | Verification tail |
|---|---|---|---|---|---|---|
| scale-tool-allow | built | 1 | 0 | k8s/on_start.py, tests/test_render.py | 69a3929 | pytest test_render + ruff pass; red: 3 scale tests failed pre-impl (implementer run) |
| scale-replicas-repo | built | 1 | 0 | db/clusters.py, tests/test_clusters_repo.py, MEMORY.md | 8446f55 | pytest test_clusters_repo + ruff pass; red: AttributeError no set_replicas |
| scale-down-drain | built | 1 | 0 | reconciler/loop.py, settings.py, README.md, MEMORY.md, tests/test_reconciler.py | e91c1bb | 36 passed + ruff; red: 3+ drain/scale tests failed |
| public-scale-route | built | 1 | 0 | api/clusters.py, api/schemas.py, README.md, openapi.json, frontend schema.d.ts, tests/test_api_scale.py | 1269471 | 43 passed (self-run) + ruff; red: route absent |
| scale-ui-control | built | 1 | 0 | ScaleControl.tsx(+test), ChatView.tsx, api/client.ts, ChatLog.test.tsx | b484c95 | vitest ScaleControl + lint pass; red: not captured (first run failed on missing node_modules) |
| agents-strip-leaving-mark | built | 2 | 0 | AgentsStrip leaving label (no new files in round 2) | ffc9148 | vitest AgentsStrip 9 passed + lint; no red (existing tests) |
| agent-scale-route | built | 2 | 0 | api/agent.py route (d2c41af), tests/test_agent_scale.py | 0e94649 | 12 passed + ruff; round 2 assertion strengthening, no red |
| smoke-scale-check | built | 2 | 0 | scripts/smoke.sh | 0dd5aa2 | tests/test_smoke_script.py + mise run lint pass; no red (bash timing reset); branch reset to integration head, see Deviations |
| kind-e2e-scaling | built | 2 | 0 | tests/e2e/test_e2e_kind.py | 41567ec | collect-only 32 + ruff pass; real e2e run only in PR CI (green after fixes); no red, gate tdd-skipped accepted |
| deploy-pin-scaling | built (pin ed0233a, PR #17) | 0 | 0 (relaunched as run wf_4aa7ace3-6e1) | helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py | unverified (deploy run: verify script did not run, denied by classifier; the first-run head 0dd5aa2 is the pre-pin tree) | implementer: 12 passed + ruff; ACs by judgement and orchestrator apply, see incident |

`tdd-revert` results are not quoted as red evidence; red column above is the implementer's own `tests.red`.

Approvals (ledger `approvals.json`; the return value from the first run showed S1 and REL blocked on deploy-pin-scaling, later cleared by the deploy run and orchestrator apply):

| Id | Text | Decisions | Tasks | Status |
|---|---|---|---|---|
| S1 | Agents dynamically join and leave a running cluster | D3 D8 D9 | agents-strip-leaving-mark, deploy-pin-scaling, kind-e2e-scaling, scale-down-drain, smoke-scale-check | delivered (return: blocked pending deploy pin; cleared by rev 13 + smoke OK) |
| S2 | Replica cap N set at init (ceiling 16); leader scales 1..N | D1 D2 D5 D10 | agent-scale-route, kind-e2e-scaling, public-scale-route, scale-replicas-repo, scale-ui-control | delivered |
| S3 | Scaling disabled per cluster (static); static single = no hive tools | D1 D4 D5 D11 | kind-e2e-scaling, scale-replicas-repo, scale-tool-allow, scale-ui-control | delivered |
| X1 | One shared orchestrator any-mcp plugin carries scale | D2 D4 D12 | agent-scale-route, scale-tool-allow | delivered |
| X2 | Headless parity: documented API and API-only e2e | D2 D5 D13 | agents-strip-leaving-mark, kind-e2e-scaling, public-scale-route, scale-ui-control, smoke-scale-check | delivered |
| Q2 | First ready agent leads; scale-up never hands leadership | D7 | scale-replicas-repo, kind-e2e-scaling | delivered |
| Q4 | Handover only; scale-down never removes leader; only leader scales | D1 D3 D7 | scale-replicas-repo, agent-scale-route, scale-down-drain, kind-e2e-scaling | delivered |
| Q7 | Static single-pod gets no hive/peers/messaging/scale tools | D4 | scale-tool-allow, kind-e2e-scaling | delivered |
| REL | Releases, bumps, helmfile apply and smoke | D6 | smoke-scale-check, deploy-pin-scaling | delivered (apply by orchestrator, rev 13; smoke OK) |

## Deviations and rulings

- Live rollback (helm rev 12) by verifier running AC3 apply. Why: AC3 was `command:mise run apply`, executed from the unbuilt deploy-pin tree. Fix: orchestrator re-applied 3b9926d (rev 13) under the user's standing apply approval; AC evidence changed to judgement in this and two todo epics. Cost if wrong: live namespace on an old release until noticed; here about one hour (07:53Z to rev 13), no data loss seen, pod-0 uid kept.
- kind-e2e-scaling gate-repeat (tdd-skipped): accepted. Why: test-only deliverable, cannot run without kind. Cost if wrong: tests that never fail; mitigated by CI e2e on PR #11, which caught two stale expectations.
- deploy-pin-scaling: blocked until PR #11 merged and main published; relaunched after merge; accepted after orchestrator apply. Cost if wrong: pin on an unpublished chart; AC2 `helm show chart` confirmed it published.
- E2E fixes on the integration branch before merge (2bce9f5, 0389d6c): stale on_start expectation and refusal-test leader pick. Cost if wrong: red main; CI green on #11.
- helmfile integration branch was forked from old main; worktree-merger rebased it onto main 8ff9753, keeping the init-scripts smoke and scale step `{replicas:1, max_replicas:2, init_scripts}`. Cost if wrong: smoke regression on init scripts; smoke OK on rev 13.
- smoke-scale-check task branch reset to the integration head: its two commits reached main in conflict-resolved form (content verified on main, 70 passed). Cost if wrong: lost smoke change; content confirmed on main. Consequence: not an ancestor by sha (cherry-picks 2f64738, 0149e3d).
- Dropped: security LOW handover/scale race (just-demoted leader scales within cap; bounded by cap). Review "consider" ClusterNotFound uncaught in agent scale route (500 only on a discard race; speculative hardening, also declined in task review). Audit sha-lineage gaps (content on main). Cost if wrong: a rare 500 or one extra scale call within cap.
- Audit gap fixed: README leaving-agent derivation (docs PR #12).
- forwardMerged: none.

## Duplicates reconciled

none (return `duplicates` empty). Cherry-picked-vs-original commits of smoke-scale-check and double e2e fix commits (040bbcf/41567ec) are lineage noise, not duplicated work.

## Discovered and blocked

- Verifier ran a live-mutating AC3 (rollback incident above). Fixed by judgement-only AC evidence; cleared.
- Permission classifier denied `mise run apply`/`smoke` for the deploy-pin implementer and verifier ("Shared Cluster Mutation"). Cleared by the orchestrator applying under the user's standing approval.
- deploy-pin-scaling verifier head not obtained (verify script denied); task shown unverified. Who can clear: nobody needed, accepted by ruling with live evidence.
- declined/cannotVerify (return): ClusterNotFound mapping, full suites, schema.d.ts byte-identity with generator, plugin tool name prefix `orchestrator_scale` (contract test covers the plugin), live StatefulSet scale-down on real cluster (now covered by smoke 1->2->1), row-lock under concurrent writers, ChatView drainWaiting wiring from real status.drain, ScaleControl rendering in ChatView, smoke timeout paths, dispatcher refusing handover to a non-ready draining agent (hive epic code). Owner: next epic touching each; none block.
- Contradiction: the first return showed S1/REL blocked and deploy-pin `verification.head` 0dd5aa2 (same as smoke-scale-check) with `rounds: 0`; later files and rulings show it delivered. README Time shows Actual 1 min, which covers only deploy-pin (impl 1, verify 1); other tasks have empty `actual`.

## Research that changed the plan

none recorded.

## Cost

Agents by role, wall-clock and per-role counts: unknown (not in the inputs; only deploy-pin has `actual_roles: impl 1, verify 1`). Review rounds: 1 for five tasks, 2 for four, 0 for deploy-pin; continuations unknown. Scope audit run wf_0b33bdf5-b0d (2 agents: epic, settled) found one gap (README) fixed in PR #12. Triage calls 11.

| Task | Estimate | Actual |
|---|---|---|
| agent-scale-route | 6 | unknown |
| agents-strip-leaving-mark | 5 | unknown |
| deploy-pin-scaling | 5 | 1 (impl 1, verify 1) |
| kind-e2e-scaling | 5 | unknown |
| public-scale-route | 6 | unknown |
| scale-down-drain | 6 | unknown |
| scale-replicas-repo | 5 | unknown |
| scale-tool-allow | 5 | unknown |
| scale-ui-control | 6 | unknown |
| smoke-scale-check | 5 | unknown |

README Time: Estimate 54 agent-min, critical path 27 min, expected wall 1.2 h at P=1.5, Actual 1 min, Remaining 0.

## MRs and deploy

- szymonrychu/agent-orchestrator#11 merged, 3b9926d (CI test/lint/frontend/e2e green).
- szymonrychu/agent-orchestrator#12 README leaving-agent docs, merged, b7906aa.
- szymonrychu/agents-helmfile#17 merged, 8a11c0b (pin ed0233a, memory 894e057).
- Deploy: helm rev 13, chart 0.1.0-main.3b9926d (rev 12 accidental rollback to a5b5a75, see incident). Post-apply diff "No affected releases". Smoke last line `smoke: OK`, scale 1->2->1, pod-0 uid kept, init scripts succeeded.

## Lessons routed to

- AC evidence of `command:mise run apply` (any live mutation) must never run in verification: add a lint in the task/AC validator (`ticket.py` or verify-task.py) rejecting `command:` evidence matching apply/deploy/sync/helm upgrade; the judgement-only wording is already in the deploy-pin template text.
- Verifier must not run `--install`/AC commands from a tree whose base is unbuilt for deploy tasks: add a verify-task.py guard that refuses commands outside an allowlist when the epic repo is a deploy repo.
- Integration branch forked from stale main (helmfile): add a check in worktree creation that the base equals current origin/main, failing otherwise.
- Branch-sha lineage after conflict-resolved landings tripping the audit: judgement call; edit the scope-audit prompt to compare content (diff) not ancestry.
- TDD red missing on test-only/e2e tasks (gate tdd-skipped): judgement call; list "e2e test-only, run by CI" as an accepted exception in the plan-execute gate text.
