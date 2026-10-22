# Template update skill and init docs cleanup record

## Summary

Asked: init removes every template-specific doc from a new or adopted workbench, and a new skill updates an existing workbench from the template without the template's own docs (approvals A1-A4, Q1).
Shipped: single instance-owned path list (`scripts/init_engine/owned.py`) driving init cleanup and `init:update`; engine command `init:update` (clean, conflict, abort and unrelated-history `--base` paths); `template-update` skill; README "Pulling template updates" rewritten; e2e round trip on a real template copy. Phase 5 added two remediation tasks (update-safety, existing-remote-kept).
7 planned + 2 remediation = 9 tasks, all landed on main by plain --no-ff merges in landing trees with the full suite before each fast-forward of main. Nothing pushed, no MR (meta mode).
Verdict: pass. Main 6b4b660: scripts 467 passed, plugin "components with tests: 27   assertions passed: 2817", lint green.

## Planned vs built

Verifier head = `tasks[].verification.head` from the run return. Review rounds from the return. Per-task continuation counts: unknown (runs 2 and 3 were the two remediation runs).

| Task | Status | Rounds | Files (return `filesChanged`) | Verifier head | Verification tail |
|---|---|---|---|---|---|
| instance-owned-paths | done | 1 | owned.py, finalize.py, test_finalize.py | e0fb748 | 24 passed in 10.22s; ruff clean. Verifier flagged AC1-AC3 ref-missing (test names); retargeted later by scope audit |
| update-command | done | 2 | update.py, test_update.py | ae39c75 | 17 passed in 16.91s; ruff, shellcheck clean. Independent verifier reported AC2-AC8 not met; implementer could not reproduce; later suites pass |
| update-conflicts-and-abort | done | 2 | test_update_conflicts.py | 7221ebf | 20 passed in 24.44s; ruff clean |
| update-unrelated-history | done | 2 | test_update_unrelated.py | a9f0020 | 30 passed in 38.95s; ruff clean |
| e2e-template-update | done | 2 | none in final round (return `filesChanged` []; task file lists test_template_update.py, update.py) | 1be9a6d | 2 passed in 13.24s; ruff clean |
| template-update-skill | done | 2 | SKILL.md, test_template_update_skill.py | efddaf2 | skill tests 6 passed; readme release test 7 passed, 5 deselected |
| docs-update-flow | done, **unverified** (return: `verified` false, stopped gate-repeat, empty evidence) | 2 | README.md, MEMORY.md | cb97b45 (head present, but the run recorded `verified: false` and `evidence: ""`) | hand-verified by orchestrator: `check_personal.py` rc 0, README grep `init:update` rc 0 |
| update-safety (remediation) | done | 2 | test_update_safety.py, test_template_update_skill.py | 322a9ee | 17 passed in 11.80s; ruff clean |
| existing-remote-kept (remediation) | done | 2 (stopped gate-repeat on TDD-skipped gate) | none (pin test; return `filesChanged` []; commit a8d9524 adds the test to test_update.py) | a8d9524 | 14 passed in 15.84s; ruff clean |

Red evidence (implementer's own `tests.red`; no tdd-revert result quoted):
- instance-owned-paths: `ModuleNotFoundError: No module named 'owned'`, 3 failed, 21 passed.
- update-command: `FAILED test_update_conflict_resolves_in_linked_worktree`, 1 failed, 13 passed.
- update-safety: pre-fix update.py (586cd59) put back temporarily: 8 failed, 2 passed. The fix itself was committed earlier in 0c61e73; this task only renamed tests.
- existing-remote-kept: mutation of update.py (set template remote to default): 1 failed, 13 deselected. Restored afterwards.
- No red: update-conflicts-and-abort (behaviour pre-existed; wiring test verified by mutation per the return note), update-unrelated-history (rename only), e2e-template-update (no behaviour change), template-update-skill (renames plus new assertions added with the SKILL.md edit), docs-update-flow (doc edit exception).

Contradiction between summary and files: the run 3 `cannotVerify` entry says the mutation check was not run, while its `tests.red` shows the mutation output. The red output is recorded; the `cannotVerify` line is treated as stale.

Approvals (ledger `approvals.json`; status from the run 1 return, then the rulings):

| Id | Text | Decisions | Tasks | Status |
|---|---|---|---|---|
| A1 | Do not gitignore the template's docs; template keeps its plans, records, contracts, MEMORY.md, ROADMAP.md tracked | D1 | instance-owned-paths | delivered |
| A2 | Init removes every workbench-specific doc so a new or adopted workbench starts with empty plan folders and fresh MEMORY.md and ROADMAP.md | D2, D9 | instance-owned-paths, e2e-template-update, docs-update-flow | delivered after ruling (run 1 return: escalated on docs-update-flow; accepted, hand-verified) |
| A3 | Skill refreshes workbench instances from the template without the template-specific docs | D3-D9 | update-command, update-conflicts-and-abort, update-unrelated-history, e2e-template-update, template-update-skill, docs-update-flow | delivered after ruling (same) |
| A4 | Definition of workbench-specific docs (template dev docs go; README, docs/enterprise.md, docs/harnesses.md, plugin docs ship) | D2 | instance-owned-paths, update-command, e2e-template-update | delivered |
| Q1 | docs/handoffs is on the instance-owned list; cleanup removes it, update never brings it | D10 | instance-owned-paths | delivered |

Runs 2 and 3 returned `approvals: []`; the remediation tasks carry no ledger entries.

## Deviations and rulings

- docs-update-flow accepted despite gate-repeat on an empty verifier evidence field. Why: the finding was a missing verification run, not a defect; hand-verified check_personal rc 0 and README grep rc 0. Cost if wrong: README could ship a wrong flag form; the landing fix put `init:update` flags after `--` (217e844).
- existing-remote-kept accepted with TDD skipped (pin test of existing behaviour, no non-test file changed). Why: update.py already kept the remote; red shown by mutation. Cost if wrong: the pin could be vacuous; the mutation run shows it fails when the URL is rewritten.
- Q1 answered yes: docs/handoffs is instance-owned. Cost if wrong: a user's handoffs are removed by init cleanup; update-safety separately protects gitignored local notes during update.
- Landing fixes outside task scope (review-notes.md): README `init:update` flags after `--`; `init_engine` test helpers renamed `init_helpers` (shadowed the e2e helpers in one pytest run, d87b383); skill text describes the default URL instead of spelling it (personal-term lint, 1b4755a).
- Landing method: tasks landed by plain --no-ff merges in landing trees (tu-land, c2-land, cp-land, c3-land) with the full suite before each fast-forward of main.
- forwardMerged: none in any run.

## Duplicates reconciled

None (`duplicates: []` in all three run returns).

## Discovered and blocked

- Blocked: none (`blocked: []`, `undelivered: []` in all runs).
- Declined by agents, no ruling: duplicate 2026-10-20 MEMORY.md line (pre-existing, not in the task diff); engine mutation check on the e2e test; trailing-slash or `.git` URL variants counted as a different URL (strict string compare kept); live agent behaviour of the skill's confirmation prompt. The user can clear these if normalisation or live-behaviour tests are wanted.
- cannotVerify, open: live run against the real GitHub template URL (tests use local upstreams and `insteadOf`); real `mise run lint` as the default lint gate inside a project; ignored files created by refresh are not removed by `git clean -fd` on abort; behaviour on git versions other than 2.56 for the ignored-file overwrite guard; the e2e verifier's transient "unable to read tree" clone failure did not reproduce in 3 reruns. The user or a follow-up task can clear these.
- Security review dismissed by design: hidden test-only `--lint-command`; `git add -A` after refresh.
- Run 1 return had `finished: false` and `unverified: ["docs-update-flow"]`; settled by the ruling above.

## Research that changed the plan

Phase 5 findings (security-review.md, review-notes.md):
- HIGH: restore_owned deleted gitignored docs/research and docs/handoffs; preflight `status --porcelain` hides ignored files. Added task update-safety (keeps ignored notes, refuses an overwrite collision).
- MEDIUM: `--url` ignored when a `template` remote exists. update-safety refuses a mismatched URL.
- LOW: option-like `--branch` / `--base` reach git. update-safety refuses them.
- MEDIUM: a non-default `--url` runs that template's scripts. The skill now asks before using one.
- Scope audit: update-command AC4 had no test for an existing template remote keeping its URL; added task existing-remote-kept. Three AC refs retargeted to renamed tests.

## Cost

Run 1: 2566 s wall, 36 agents (7 tasks). Run 2: 640 s (update-safety). Run 3: 208 s (existing-remote-kept). Total 3414 s (about 57 min) of run wall-clock. Per-role agent counts for runs 2 and 3, audits and continuation counts: unknown. Phase 5 used a reviewer, a security-researcher and a scope-auditor (sonnet each).

README Time: Estimate 53 min | Actual 0 min (never filled) | Remaining 0 min. Task files carry no `actual` or `actual_roles` (all empty), so per-task actuals are unknown.

| Task | Estimate (min) | Actual |
|---|---|---|
| instance-owned-paths | 8 | unknown |
| update-command | 10 | unknown |
| update-conflicts-and-abort | 8 | unknown |
| update-unrelated-history | 8 | unknown |
| e2e-template-update | 8 | unknown |
| template-update-skill | 6 | unknown |
| docs-update-flow | 5 | unknown |
| update-safety | none | unknown |
| existing-remote-kept | none | unknown |

Estimates sum to 53 for the seven planned tasks.

## MRs and deploy

None. Meta mode; nothing pushed; no MR or PR. Landed locally on main (6b4b660). Deploy: not applicable.

## Lessons routed to

- Empty verifier evidence caused a gate-repeat on a docs-only task: add a check in the plan-execute verifier tests that fails a task when `evidence` is empty while the command passed (mechanical).
- Test names must match AC refs (three refs broke, AC1-AC3 flagged ref-missing): add a lint that checks each task's AC test refs resolve to a collected test before verification (mechanical).
- Shadowed test helper module names across suites (`init_engine` vs e2e): add a collection-time check that fails on duplicate helper module names under `scripts/tests` (mechanical).
- Personal-term lint caught the spelled default URL only at landing: add `check_personal.py` to the verify command of tasks that edit skills or docs (mechanical).
- Destructive restore step deleted gitignored user files: update-safety now tests it; add a security-review prompt line to run destructive commands on trees with ignored owned paths only if it recurs (judgement, skill edit).
- Pin tests of existing behaviour trip the TDD-skipped gate: name "pin test, red by mutation" as a listed exception in the tdd rule (judgement, rule edit).
