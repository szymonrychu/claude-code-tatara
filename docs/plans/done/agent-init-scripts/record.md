# agent init scripts record

## Summary

Asked: per-cluster init scripts exposed to the agent initialised with them and editable by it; run once per cluster. Shipped: `init_scripts` on ClusterSpec and presets, once-per-cluster init Job recorded in `status.init`, GET/PUT public and agent routes (edit writes cluster spec and source preset, no roll, no re-run), preset form rows, cluster Init scripts dialog, kind e2e, smoke coverage, pin bump, live apply.
10 of 10 planned tasks done. Verdict: pass (2026-10-25). One follow-up not built (any-mcp description, Non-goal of this epic). Audit run wf_433b68c6-93b found 2 gaps (apply-smoke MEMORY quote, any-mcp description); first fixed, second deferred.

## Planned vs built

Verifier head = `tasks[].verification.head` from wf_b3403889-1e2 (deploy tasks from wf_2f31a8b3-59d). Review rounds from `rounds` in the return; continuations: unknown (not in return). Files from `git diff --stat` per repo (orchestrator 918dc0a..22cf283: 29 files, +2655/-33; helmfile 7dcb257..8ff9753: 7 files, +109/-14); the return's `filesChanged` is empty for several tasks, so files were read from the diff.

| Task | Status | Rounds | Files | Verifier head | Verification tail |
|---|---|---|---|---|---|
| init-scripts-spec-field | done | 1 | spec.py, test_spec_init_scripts.py, test_render.py, README, openapi.json, schema.d.ts | 41da5fa | pytest spec/render/readme_api + ruff, pass. Red (implementer): ImportError INIT_DIR, init_scripts_hash missing |
| init-scripts-public-api | done | 1 | api/clusters.py, api/schemas.py, db/clusters.py, test_api_init_scripts.py, openapi, schema.d.ts | a38fbb6 | pytest api_init_scripts/api_clusters/readme_api + ruff, pass. Red (implementer): 7 failed |
| fe-preset-init-scripts | done | 1 | clusterSpecForm.ts, PresetForm.tsx(+test), client.test.ts | 5de9bd8 | vitest PresetForm + lint, pass. Red (implementer): 3 failed, 12 skipped |
| fe-cluster-init-dialog | done | 1 | InitScriptsDialog.tsx(+test), TopBar.tsx(+test), App.tsx(+test), client.ts | ec7dd9a | vitest dialog+TopBar + lint, pass. Red (implementer): 2 failed files, 2 tests failed |
| init-scripts-agent-api | done | 2 | api/agent.py, test_agent_init_scripts.py, README | 1bf5c96 | pytest agent_init_scripts/readme_api + ruff, pass (12 passed). No red: no behaviour change in round 2; round 1 red not in return |
| init-job-runner | done | 2 | reconciler/init.py, loop.py, checks.py, test_init_runner.py | 36d4fed | pytest init_runner/reconciler/checks + ruff, pass (--no-suites). Round 2 findings were verifier-capture issues, not defects; reviewer re-ran: 50 passed. Red cycle ran in round 1 (commit ccc6290), not in return |
| init-scripts-kind-e2e | done | 2 | tests/e2e/test_e2e_kind.py | 39a5210 | `--collect-only` + ruff only; no red run (test-only, no non-test file to revert). Gate-repeat accepted by ruling. Real kind e2e ran in CI: 4 failures found and fixed (see Deviations) |
| smoke-init-scripts | done | 2 | scripts/smoke.sh, tests/test_smoke_script.py | ce31b78 | pytest smoke_script + ruff, pass. No red (tightened one assertion) |
| deploy-pin-init-scripts | done | 0 review fixes (impl, verify, review clean, land) | helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py | f161544 (wf_2f31a8b3-59d) | pytest release (2 tests deselected) + ruff, pass. In the first run it was blocked until PR #10 merged |
| apply-smoke-init-scripts | done by ruling, unverified | 0 | MEMORY.md (PR #15, #16) | none in wf_b3403889-1e2; f161544 in wf_2f31a8b3-59d, FAILED (exit 2) | Verifier ran before the apply: `mise run diff` showed pending change, `smoke: FAIL: cluster create failed` (422). Acceptance rests on the orchestrator-run apply: helm rev 11, chart 0.1.0-main.22cf283, post-apply diff "No affected releases", smoke last line "smoke: OK" |

Red evidence above is the implementer's own `tests.red`; no `tdd-revert` result is quoted. Tasks with no red: init-scripts-agent-api (round 2), init-scripts-kind-e2e, smoke-init-scripts, deploy-pin, apply-smoke. `selfVerification` is not used in any column.

Approvals (`approvals.json`; status from the plan-execute return, A2 updated by later rulings):

| id | text | decisions | tasks | status |
|---|---|---|---|---|
| A1 | init_scripts on ClusterSpec and presets, UI fields, documented API | D1, D5 | init-scripts-spec-field, init-scripts-public-api, fe-preset-init-scripts, fe-cluster-init-dialog | delivered |
| A2 | Releases, pin bumps, helmfile apply plus smoke are tasks of this epic | D7 | smoke-init-scripts, deploy-pin-init-scripts, apply-smoke-init-scripts | delivered (return said blocked on PR merge; since cleared: PR #10 merged, apply done). apply-smoke row stays unverified by the verifier |
| C1 | Run once per cluster, ClusterSpec + preset field | D2, D9 | init-job-runner, init-scripts-kind-e2e, init-scripts-spec-field | delivered |
| C2 | Exposed to the agent initialised with them | D3, D10 | init-job-runner, init-scripts-agent-api | delivered (any-mcp tool description gap, see Discovered) |
| C3 | Agent edit writes cluster spec and source preset | D4, D11 | init-scripts-agent-api, init-scripts-public-api | delivered |
| X1 | Shared orchestrator any-mcp plugin carries agent tools | D6, D12 | init-scripts-agent-api | delivered (agent route and parity test; plugin owned by hive epic) |
| X2 | Headless parity: public API plus API-only e2e | D5, D8, D13 | fe-cluster-init-dialog, fe-preset-init-scripts, init-scripts-kind-e2e, init-scripts-public-api | delivered |

Contradictions between summaries and files: the return lists `finished: false`, `escalated` apply-smoke (dependency-failed) and `unverified: [apply-smoke-init-scripts]`; later rulings and the task files mark both deploy tasks done. The task files for apply-smoke and deploy-pin record `actual: 1`.

## Deviations and rulings

- init-scripts-kind-e2e gate-repeat (tdd-skipped) accepted. Why: test-only deliverable, run for real in phase 5. Cost if wrong: a test that cannot fail goes unproven; mitigated by CI kind e2e, which did fail 4 times and was fixed.
- Whole-diff review ACT: smoke replicas 1 breaks the leader wait (1-replica cluster is not a hive). Fixed: `fix(smoke): keep the smoke cluster a hive so it gets a leader` (agents-helmfile PR #14). Why: the task text prescribed replicas 1 and the fake API hid it. Cost if wrong: live smoke times out.
- Init Job workingDir created as root; e2e fixed by creating the workdir as the pod user (486abcf) and two test-shape fixes (b10880e). Found by CI e2e on PR #10. Cost if wrong: init Job fails on RWX PVC.
- Security MEDIUM no server-side main-agent gate on PUT /agent/v1/init-scripts: dropped. Why: design line 57, any agent of the cluster may edit, wrapper gates subagents (hive F2). Cost if wrong: a subagent with the pod token can edit the scripts that run in the next cluster.
- Security MEDIUM edit rewrites source and Default preset: dropped. Why: C3 to the letter. Cost if wrong: a compromised agent persists scripts into all future clusters from that preset.
- Security LOW init Job SA token / no pod hardening: dropped, matches agent pod (render.py). Noted, not doing now.
- Security LOW log_tail exposure: dropped, by design (C2). Cost if wrong: secrets echoed by a script land in DB and API.
- Review CONSIDER create_job error recorded permanent failed: dropped, `job_create_failed` per init-job-runner.md:37. Cost if wrong: one transient API error loses the scripts for the cluster's life.
- Review CONSIDER phase message "N of M pods ready; init running": dropped, task AC6 says message "carries" init running. Cost if wrong: cosmetic.
- Audit gap init-scripts-agent-api AC4 (any-mcp `init_scripts_get` description lacks `.agent-init/init.sh` and next-cluster semantics): partly dropped, any-mcp changes are a Non-goal (hive F1 owns the plugin). Cost if wrong: agents read an incomplete tool description.
- Audit gap apply-smoke AC4 (MEMORY smoke quote, diff in notes): fixed, agents-helmfile PR #16 and task notes.
- Audit gap submodule pointers: bumped at close (66cc413).
- apply-smoke accepted after orchestrator-run apply: the implementer's `mise run apply` was denied by the permission classifier; the user allowed `mise run apply` on 2026-10-25 and the orchestrator ran it. Cost if wrong: live state differs from the verifier's failed run, but the post-apply diff and smoke are the evidence.
- forwardMerged: none.

## Duplicates reconciled

none (`duplicates: []`).

## Discovered and blocked

- Follow-up, not built: any-mcp orchestrator plugin `init_scripts_get` description should name `.agent-init/init.sh` and next-cluster semantics. Who clears: hive-mode-leadership-handove owner (hive F1) or a new any-mcp task. `tests/test_agent_init_scripts.py:124-125` asserts only `.agent-init/` and `next cluster` in the edit description.
- cannotVerify (no ruling settled these): kind e2e and live Job script behaviour on a real cluster were only covered by CI e2e after the fact; `uv run mypy` could not spawn in the task env (init-job-runner); `npm run build` not run by the verifier for fe-cluster-init-dialog; server strip vs client trim() empty-check semantics (fe-preset-init-scripts); astral-character length vs 16384 limit; openapi/schema.d.ts regeneration drift (review: not run). Who clears: orchestrator CI or a human.
- declined (no ruling): fe-cluster-init-dialog TDD red order not visible in history (red evidence is in `tests.red`); init-job-runner extra get_job per tick on succeeded/failed clusters and argv chunking of INIT_SH (justified in MEMORY.md); fe-preset-init-scripts missing visible group heading; visual styling of the dialog.
- Blocked in first run: deploy-pin-init-scripts needed PR #10 merged; cleared by the orchestrator.
- Process gap: init-job-runner verifier reported "Worktree not clean" while `git status --short` was empty; reviewer re-ran the checks. Not resolved at source.

## Research that changed the plan

none recorded.

## Cost

Agents by role: unknown (usage totals not in the return; `triageUsage`: 8 calls, 16 input and 5221 output tokens). Continuations: unknown. Audits: one scope audit (wf_433b68c6-93b, two agents: epic and settled), 1 gap set closed or deferred. Wall-clock: unknown beyond timestamps 2026-10-25 06:35Z to 07:40Z for rulings.

README Time: Estimate 54 agent-min, critical path 32 min, expected wall 1.2 h (k=2.0), Actual 2 min (only the deploy tasks recorded `actual`).

| Task | Estimate (min) | Actual (min) |
|---|---|---|
| init-scripts-spec-field | 6 | unknown |
| init-scripts-public-api | 6 | unknown |
| fe-preset-init-scripts | 5 | unknown |
| fe-cluster-init-dialog | 6 | unknown |
| init-scripts-agent-api | 5 | unknown |
| init-job-runner | 6 | unknown |
| init-scripts-kind-e2e | 5 | unknown |
| smoke-init-scripts | 5 | unknown |
| deploy-pin-init-scripts | 5 | 1 (impl 1, verify 1, review 1, land 1) |
| apply-smoke-init-scripts | 5 | 1 (impl 1, verify 1) |

## MRs and deploy

- szymonrychu/agent-orchestrator#10: merged, 22cf283. CI test, lint, frontend and e2e green after the e2e fixes.
- szymonrychu/agents-helmfile#14 (pin to 22cf283 plus smoke, f161544): merged. #15 (MEMORY, apply record): merged. #16 (MEMORY smoke quote): merged, main at 8ff9753.
- Submodule pointers bumped in the workbench: 66cc413.
- Deploy: applied live by the orchestrator after the user allowed `mise run apply` (2026-10-25): helm revision 11, chart 0.1.0-main.22cf283; post-apply diff "No affected releases"; smoke last line "smoke: OK" with init scripts succeeded.

## Lessons routed to

- Smoke script prescribed replicas 1 and the fake API always returned a leader, hiding a live failure: add a test check in `tests/test_smoke_script.py` that the fake API returns a leader only for a hive spec (max_replicas>1). Mechanical.
- Kind-only behaviour (init Job workingDir as root) was found only in CI e2e: run the kind e2e for any task that adds a Job or pod spec before landing. Judgement call: edit `workbench:epic-run` skill phase-5 note.
- Verifier "Worktree not clean" false report: add a check in `verify-task.py` that the cleanliness flag is computed from `git status --porcelain` at the verified head. Mechanical.
- Task text prescribing an implementation detail (replicas 1) that conflicted with domain rules: judgement call, edit the plan-writing guidance to cite the invariant instead of a value.
- Implementer `mise run apply` denied by the permission classifier: record the standing approval for apply in `approvals.json` at planning time. Judgement call, edit `start-development` approval step.
- Acceptance of a task whose verifier failed relies on an out-of-band ruling: add a lint in `rulings.json` handling so an accepted `unverified` task requires a quoted post-apply evidence field. Mechanical.
