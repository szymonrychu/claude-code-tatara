# cluster form defaults and gauge tick record

## Summary

Asked (2026-10-23): Model and Effort dropdowns in the cluster form, every field prefilled from /meta defaults (cpu 500m/4, memory 1Gi/8Gi real defaults on agent pods), the gauge auto-compact tick drawn on the ring, deployed.
Shipped: 7 of 7 planned tasks done (2 original, 5 added from review, CI and deploy). Approvals A, B, C delivered. agent-orchestrator PR #3 merged as d5a7738, agents-helmfile PR #5 merged as 38a2543, applied to the cluster, smoke OK.
Verdict: pass. Not verified: the visual render of the form and the gauge tick in a real browser (Chrome extension not connected; jsdom tests only).

## Planned vs built

Runs: wf_169501a3-ea5 (return1), wf_e3cf829b-ffa (return2), wf_65f9bd95-aae (return3), wf_134d8e27-611 (return4, blocked), wf_e1400bda-eb3 (return5). Review rounds are from the run returns.

| task | status | rounds | continuations | files | verifier head | verification tail |
|---|---|---|---|---|---|---|
| meta-form-defaults | done | 3 | none | settings.py, api/clusters.py, api/schemas.py, spec.py, k8s/render.py, openapi.json, frontend/src/api/schema.d.ts, README.md, tests/test_render.py | 9b0efb6 | pass: test_settings, test_api_clusters, test_render, test_readme_api + mise run lint |
| form-dropdowns-and-gauge-tic | done | 1 | none | ClusterForm.tsx, ClusterForm.test.tsx, clusterSpecForm.ts, ContextGauge.tsx, ContextGauge.test.tsx | c993d7c | pass: vitest src/clusters src/ribbon (20 of 20) + npm run lint. Red (implementer): 3 failed, 17 passed |
| defaults-at-write-time-and-l | done | 1 | none | api/clusters.py, spec.py, k8s/render.py, tests/test_render.py, tests/test_api_clusters.py, 2 goldens, README.md | 2d099ec | pass: test_render, test_api_clusters + lint. Red (implementer): test_render_keeps_spec_resources_unchanged and test_write_fills_default_resources_* FAILED |
| model-default-option | done | 1 | none | ClusterForm.tsx, ClusterForm.test.tsx | 34631bd | pass: vitest src/clusters + lint. Red (implementer): 3 failed, 7 passed incl. null-model edit |
| deterministic-in-flight-cap | done | 2 (stopped gate-repeat) | none | tests/test_dispatcher.py | 3fcbb0b | pass: test_dispatcher + lint. TDD exception: test-only change; red = cap mutated to 7 and 9 fails the test (implementer run, not tdd-revert) |
| fast-full-spec-form-test | done | 2 (stopped gate-repeat) | none | ClusterForm.test.tsx | 3f272a6 | pass: vitest src/clusters + lint. TDD exception: test-only change; no red run |
| deploy-pin-d5a7738 | done (run 4 blocked, run 5 done) | 0 then 1 | none | helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py (+ ruff edits in tests/test_helmfile_base.py, test_mise_tasks.py, test_smoke_script.py) | 7329bc8 (run 4 attempt: 9c88ccf, failed) | pass: uv run pytest -q + mise run lint. Red (implementer, run 4): test_orchestrator_pin_is_d5a7738 AssertionError |

Full suites on epic tip 3fcbb0b: test 405 passed, integration 8 passed, chart, lint, lint:chart, frontend lint/test/build/check:api and kind e2e all exit 0.

Discrepancies between summaries and files:
- fast-full-spec-form-test: return3 lists `filesChanged` as empty and `tests.red` as none; the task file and commit name ClusterForm.test.tsx. The file wins.
- deploy-pin-d5a7738: `files` in the task lists 3 files; the landed commit 7329bc8 also touches 3 test files for ruff style fixes (re.M to re.MULTILINE, check=False, quotes). Behaviour-neutral, declined as a finding by the run; ruling says it is the ruff cleanup commit in PR #5.
- meta-form-defaults: tests/test_render.py was edited in the fix round without a finding or tests.added entry (process gap). The render-time default behaviour this task added was later removed by defaults-at-write-time-and-l.
- return1 carried no red evidence for meta-form-defaults (`tests.red` none); only the verification pass is recorded.

Approvals (from `approvals.json` and the run 1 return):

| id | text | decisions | tasks | status |
|---|---|---|---|---|
| A | Model and Effort are dropdowns fed by /meta (4 models, opus default; efforts low..max) | none | meta-form-defaults, form-dropdowns-and-gauge-tic | delivered |
| B | Every other form field shows its default when not provided; cpu 500m/4 and memory 1Gi/8Gi are real defaults on agent pods | none | meta-form-defaults, form-dropdowns-and-gauge-tic | delivered (defaults now applied at write time, see rulings) |
| C | The ribbon gauge auto-compact tick sits on the ring | none | form-dropdowns-and-gauge-tic | delivered (geometry pinned in test; not seen in a browser) |

## Deviations and rulings

- Whole-diff review found 3 medium issues, all fixed in run wf_e3cf829b-ffa: (1) render-time resource defaults would roll running clusters, contradicting the README non-goal; moved to write time (2d099ec), goldens byte-identical to pre-epic main. (2) PATCH returned 422 for stored legacy model/effort and for a high request without a limit; now validates only changed values and fills limits with a guard (2d099ec). (3) edit mode showed a blank Model select for a null model; added an empty default option (34631bd). Cost if wrong: running clusters roll on image deploy, or old clusters cannot be saved.
- User ruling 2026-10-23: live session edit is not needed. Edit removal moves to the cluster-presets epic, so the PATCH legacy fixes are interim. Cost if wrong: interim code is removed later with that epic.
- TDD exception, deterministic-in-flight-cap: test-only change (no non-test file to revert). Red shown by mutating the dispatcher cap to 7 and 9. Cost if wrong: the flake under full-suite load was not stress-reproduced.
- TDD exception, fast-full-spec-form-test: test-only speed change, assertions unchanged (CI timeout 5046 ms; fixed with a 15 s timeout and paste). Cost if wrong: a slow test could still time out on the runner; only the 15000 ms headroom is confirmed.
- forwardMerged: none in any run.
- Added tasks beyond the original two: model-default-option, defaults-at-write-time-and-l, deterministic-in-flight-cap, fast-full-spec-form-test, deploy-pin-d5a7738.

## Duplicates reconciled

none

## Discovered and blocked

- Run 4 (wf_134d8e27-611) blocked deploy-pin-d5a7738: chart 0.1.0-main.d5a7738 absent from Harbor because agent-orchestrator main chart-publish (run 39936687362) got 403 at Harbor login. Cleared: transient 403, passed on rerun; run 5 landed the pin.
- Pre-existing flake test_at_most_eight_sends_in_flight (peak 7 under load): fixed in 3fcbb0b.
- PR #3 frontend CI timeout on "creates cluster with full spec": fixed in 3f272a6.
- Process gap: stash@{0} left in the agent-orchestrator worktree by the fast-full-spec-form-test implementer. Clearer: orchestrator (drop the stash).
- cannotVerify, open: visual render of form dropdowns and gauge tick at 28px and 40px (needs a connected browser; Szymon or the next session with Chrome); reconciler behaviour for existing clusters whose stored model is outside settings.models (validate_spec runs only on the API path); old flake absence under CPU load not stress-tested.

## Research that changed the plan

none

## Cost

Five plan-execute runs; roles per run: sonnet implementers and reviewers, triage calls 4, 3, 1, 0, 1. Continuations: none. Audits: off, no scope audit in any run. Wall-clock: unknown (runs span 11:03 to 12:22 on 2026-10-23 per file times).

| task | estimate | actual |
|---|---|---|
| meta-form-defaults | 6 | unknown |
| form-dropdowns-and-gauge-tic | 6 | unknown |
| defaults-at-write-time-and-l | 7 | unknown |
| model-default-option | 5 | unknown |
| deterministic-in-flight-cap | 5 | unknown |
| fast-full-spec-form-test | 5 | unknown |
| deploy-pin-d5a7738 | 5 | unknown |

README Time: estimate 39 agent-min, critical path 22 min, expected wall 0.9 h at P=1.5, actual 0 min (not filled), remaining 0 min.

## MRs and deploy

- szymonrychu/agent-orchestrator#3: merged as d5a7738. Main CI chart-publish got a transient Harbor 403 and passed on rerun.
- szymonrychu/agents-helmfile#5: merged as 38a2543, includes a ruff cleanup commit (7329bc8).
- Deploy: `mise run apply` updated agent-orchestrator to chart 0.1.0-main.d5a7738. All 4 deployments run image d5a7738. Live /api/v1/meta returns the 4 models, 5 efforts and resource defaults 500m/4 and 1Gi/8Gi. `mise run smoke` OK (any-mcp Connected, v0.1.0, smoke cluster discarded).

## Lessons routed to

- Behaviour changes that alter rendered manifests must not roll running clusters: add a render test that pins golden output for a spec with no resources (now test_render_keeps_spec_resources_unchanged) and a CI check that golden files change only with a labelled migration. Mechanical.
- Tests with sleep-based overlap flake under load: add a lint rule or test-review check flagging `asyncio.sleep` used as a synchronisation primitive in tests/test_dispatcher.py. Mechanical.
- Frontend tests typing long values char by char hit the 5 s vitest default: set a project-wide vitest `testTimeout` and a lint rule against `userEvent.type` for strings over a threshold. Mechanical.
- Deploy pin ran before the chart was published: add a precondition in the helmfile pin test or task (chart exists in Harbor via `helm show chart`) so the block is caught up front. Mechanical.
- Whole-diff review caught what per-task review missed (README non-goal vs render-time defaults): edit start-development's plan template to require each task to list the README non-goals it could break. Judgement call.
- Test-only tasks flagged `tdd-skipped` by the gate: edit the plan-execute TDD gate to accept a declared test-only exception instead of repeating. Judgement call.
