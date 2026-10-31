# Init leaves a green tree retro

## Review

Migrated from the epic format.

## What went well

- 5 of 12 tasks passed with 0 or 1 fix rounds and a quoted red (secrets-skip-gitlinks, init-writes-allow-entries, license-every-plugin, e2e-behind-slow-marker, license-missing-refusal each had 1 round with a named failing test).
- Live update of claude-code-tatara exposed that refresh did not write the allow file; this became refresh-writes-allow-entries and the update then succeeded (a9dc548).
- Rulings were explicit with cost-if-wrong: template-marker-skip gate-repeat accepted (conftest.py:78 skipif is the deliverable), ruff-e501 accepted with no change (wrap already in ce694a7).
- Review findings were placed as tasks, not dropped: refresh-writes-allow-entries, e2e-behind-slow-marker, license-missing-refusal, ci-workflow-test-pins-e2e-jo (9 planned, 3 added per record summary; 4 added per rulings).
- Final gate passed: `mise run test && mise run lint` on main (close.json), lint:secrets "no leaks found".

## What went wrong or could improve

- e2e-init-green hit the round cap (3 rounds, verified=false) and the verifier timed out at 540s against a 48-min file; hand-verified on 27d001e (7 passed in 2867.48s).
- e2e-init-green was estimated at 5 min but its test run alone took 2867s: the estimate ignored test runtime.
- template-marker-skip needed 2 rounds and stopped on a gate-repeat false positive (debt-marker check matched an explanatory comment at conftest.py:68).
- Tasks, rounds and approvals bookkeeping was unreliable: return 1 marked all five approvals escalated and e2e-init-green dependency-failed, and license-every-plugin's return head was the literal "$(see below)" (no SHA).
- ci-workflow-test-pins-e2e-jo has no populated tests.red or verification.evidence; a test-only commit gives tdd-revert nothing to restore.
- Points, minutes and tokens actuals are "not recorded" for all 12 tasks, so every delta and MdAPE is unmeasured; ruff-e501-errors-in-scripts has no estimate at all.
- The new e2e CI job is unconfirmed on GitHub Actions because main is not pushed; the two slow e2e tests were not run by the e2e-behind-slow-marker implementer (~48 min).

## Recommendations

- Code:
  - scripts/tests/e2e/test_instantiate.py: test_suite_green_on_initialised_copy and test_full_mise_test_green_on_initialised_copy overlap (both slow); both kept, costs CI time only. Merge one into the other.
  - mise-tasks/lint/secrets: unchecked `git ls-files -sz` (dropped finding, false positive only) and untracked nested repos listed by `git ls-files -o`; not run under macOS bash 3.2. Check the exit status and add a bash 3.2 run.
  - scripts/init_engine/finalize.py: `--license none` on a non-first run does not rewrite plugin licenses; refusal order when both holder and LICENSE are missing differs from pre-epic code. Pin both with tests or decide the behaviour.
  - Tests for init-writes-allow-entries use synthetic hashed terms, not the real repo denylist digests (scripts/tests, finalize tests); only the tatara live proof covers the real digests.
- Delivered differently:
  - The record says 9 planned and 3 added tasks; rulings and the task list show 4 added (refresh-writes-allow-entries, e2e-behind-slow-marker, license-missing-refusal, ci-workflow-test-pins-e2e-jo), because review and the live tatara update found gaps the design (D1-D7) did not cover.
  - ruff-e501-errors-in-scripts was delivered with no change: the wrap had already landed in ce694a7, so the discovered task was a no-op.
  - Heavy e2e moved behind the slow marker and `mise run e2e` plus a pinned CI job, which the original six FEEDBACK.md defects did not ask for; it was needed to keep `mise run test` green and fast.
- Tech debt:
  - New e2e CI job unverified on GitHub Actions: lives in the CI workflow pinned by scripts/tests/test_ci_workflow.py; remove by pushing and reading the CI run.
  - Tasks carry no actuals (`actual`, `actual_roles` empty): remove by recording actuals at close (see workflow proposal).
  - Template and claude-code-tatara not pushed (stated non-goal).
- Workflow:
  - recurring: actuals and expected values not recorded (housekeeping-rules-estimates: tasks lacked points and expected minutes/tokens, MdAPE unmeasured; this epic again has every actual "not recorded"). Change: have `ticket.py close` or epic-run run `actuals --backfill` before `ticket.py retro` and refuse to close a task with no recorded actuals.
  - recurring: verification reported or accepted from weak evidence (housekeeping-rules-estimates: false greens from tail reads; this epic: "$(see below)" head, ci-workflow-test-pins-e2e-jo with no red evidence, e2e-init-green verified=false). Change: add a schema check that the landed head matches `^[0-9a-f]{40}$` and have the verifier accept a test-only diff's implementer `tests.red`.
  - Verifier deadline (540s) is shorter than a legitimate slow e2e file: flag tasks whose test command is marked slow at estimate lint and take a recorded hand run instead of the independent verifier. Estimates must include test runtime.
  - Late returns must restate every approval so a dependency-failed task that later passes does not leave approvals marked escalated.

## Delivery record (migrated)

### Summary

Asked: fix the six init defects in FEEDBACK.md so init and component add leave `mise run lint` and `mise run test` green.
Shipped: project allow file for personal lint, gitlink-free secrets scan, holder in every plugin LICENSE (plus missing-LICENSE refusal), template-only tests skip after init, skill text on local-bare and the --path move. Review findings added: refresh writes the allow file, heavy e2e behind the slow marker and `mise run e2e`, CI workflow test pins the e2e job.
Verdict: pass. 12 tasks done (9 planned, 3 added). Main fast-forwarded locally to 404c442, not pushed. `mise run test && mise run lint` passed on main (close.json). Live proof: claude-code-tatara template update a9dc548 succeeded with lint green.

### Planned vs built

Verifier head = `tasks[].verification.head`. Review rounds from the return `rounds`; continuations: none recorded in the returns (unknown). Files abbreviated.

| Task | Status | Rounds | Files | Verifier head | Red evidence (implementer `tests.red`) |
|---|---|---|---|---|---|
| personal-allow-file | done | 0 | scripts/check_personal.py + test | 191d8ec | none recorded |
| secrets-skip-gitlinks | done | 1 | mise-tasks/lint/secrets + test | 18769df | pytest test_secret_scanning.py: FAILED before fix |
| init-writes-allow-entries | done | 1 | scripts/init_engine/finalize.py, cli | 5d7ad13 | reverse-applied impl patch, -k vocabulary/literal: failed |
| license-every-plugin | done | 1 | scripts/init_engine/finalize.py, update | unverified: return head is the literal "$(see below)", no SHA | pytest test_finalize/test_update: failed |
| skill-text-local-bare-move | done | 0 | init/SKILL.md, component-add skill | 9577be0 | pytest test_init_skills -k local_bare: failed |
| template-marker-skip | done | 2 (stopped gate-repeat, ruled accept) | scripts/tests/conftest.py | 5619cda | none recorded |
| e2e-init-green | done | 3 (round-cap; verified=false) | scripts/tests/e2e/test_instantiate.py | 27d001e (verifier timed out; hand-verified) | none recorded |
| refresh-writes-allow-entries | done | 2 | finalize.py, test_refresh.py | 8bfd79a | test_refresh.py with add-all: FAILED |
| e2e-behind-slow-marker | done | 1 | pyproject.toml, mise-tasks/test/scripts, mise-tasks/e2e | 3145b85 | test_root_config/test_root_tooling: FAILED |
| license-missing-refusal | done | 1 | finalize.py + test | b8c4d96 | test_finalize -k missing_refuses: FAILED |
| ci-workflow-test-pins-e2e-jo | done | 2 | scripts/tests/test_ci_workflow.py | 9d7de6c | old assertion run against ci.yml (test-only commit) |
| ruff-e501-errors-in-scripts | done, no change (wrap landed in ce694a7) | 2 (gate-repeat) | none | 5619cda (verified=false) | n/a, formatting |

Verification tail: close.json `mainVerify` `mise run test && mise run lint` passed; lint:secrets "no leaks found", all lint tasks finished. Hand-verified e2e-init-green on 27d001e: `pytest scripts/tests/e2e/test_instantiate.py -q` -> 7 passed in 2867.48s.
Return 1 reported all five approvals as `escalated` and e2e-init-green as `dependency-failed` (0 rounds); return 2 re-ran it. The files and rulings show it done.

| Approval | Text | Decisions | Tasks | Status |
|---|---|---|---|---|
| A | personal lint accepts project vocabulary | D1, D2, D7 | personal-allow-file, init-writes-allow-entries, e2e-init-green, refresh-writes-allow-entries | delivered (return 3 delivered refresh; e2e-init-green hand-verified) |
| B | secrets lint skips gitlinks | D3, D7 | secrets-skip-gitlinks, e2e-init-green | delivered |
| C | holder in every LICENSE | D4, D7 | license-every-plugin, e2e-init-green, license-missing-refusal | delivered (license-every-plugin has no verifier SHA: unverified in the return; covered by integration verify) |
| D | template-only tests skip after init | D5, D7 | template-marker-skip, e2e-init-green, e2e-behind-slow-marker, ci-workflow-test-pins-e2e-jo | delivered |
| E | skill text on local-bare and --path move | D6 | skill-text-local-bare-move | delivered (returns 1 listed it escalated; later returns omit it) |

### Deviations and rulings

- template-marker-skip gate-repeat accepted. What: verifier flagged a debt marker at conftest.py:78. Why: the skipif is the deliverable (D5); line 68 is an explanatory comment. Verified on 5619cda: 31 passed, lint:root clean. Cost if wrong: a real parked item ships unnoticed.
- e2e-init-green verifier timeout accepted. What: 540s verifier deadline vs a 48-min test file. Why: hand-verified 7 passed in 2867.48s on 27d001e. Cost if wrong: e2e regression unseen by the independent verifier.
- ruff-e501-errors-in-scripts accepted with no change. Why: the wrap landed in ce694a7 (d7b265c on main); pure formatting, no targeted test. Cost if wrong: lint:ruff E501 recurs.
- Added tasks after review: refresh-writes-allow-entries (found during the tatara update), e2e-behind-slow-marker, license-missing-refusal, ci-workflow-test-pins-e2e-jo. Cost if wrong: scope growth of 4 tasks; each delivered.
- Dropped review finding: unchecked `git ls-files -sz` in lint/secrets. Why: failure yields a false positive, not a hidden leak. Cost if wrong: confusing scan failure.
- forwardMerged: none in any return.

### Duplicates reconciled

None. Return 3 noted overlap between test_suite_green_on_initialised_copy and test_full_mise_test_green_on_initialised_copy (both slow); both kept, redundancy costs CI time only.

### Discovered and blocked

- Declined/cannotVerify, unsettled by a ruling (owner: Szymon):
  - `--license none` on a non-first run does not rewrite plugin licenses (edge, not certain to violate the requirement).
  - Untracked nested repos listed by `git ls-files -o` in the secrets scan (declined by implementer).
  - lint:secrets not run under real bash 3.2 (macOS /bin/bash).
  - The two slow e2e tests were not run by the implementer of e2e-behind-slow-marker (~48 min); the new e2e CI job running green on GitHub Actions is unconfirmed because main is not pushed. Cleared by: push and read the CI run (Szymon).
  - Behaviour against the real repo denylist digests (init-writes-allow-entries): tests use synthetic hashed terms. Partly covered by the tatara live proof.
  - Refusal order when both holder and LICENSE are missing differs from pre-epic code; not a stated requirement.
- Process gap: ci-workflow-test-pins-e2e-jo has no populated `tests.red` or `verification.evidence`; the test-only commit has no non-test file for the tdd-revert to restore (not quoted as red).
- Template and tatara not pushed (non-goal).

### Research that changed the plan

Live update of claude-code-tatara from a pre-fix workbench showed refresh did not write the allow file; this created refresh-writes-allow-entries (a9dc548 update succeeded after the fix). Per-task estimates were amended by the builder check (dd8d309).

### Cost

Agent counts, continuations and wall-clock: unknown (not in the returns; `actual` and `actual_roles` are empty in every task file). Triage calls were 1 each on init-writes-allow-entries, template-marker-skip, e2e-behind-slow-marker, license-missing-refusal, refresh-writes-allow-entries and ci-workflow-test-pins-e2e-jo.

README Time: Estimate 59 agent-min, critical path 44 min, expected wall 1.5 h at P=1.5; Actual 0 min (not recorded).

| Task | Estimate | Actual |
|---|---|---|
| personal-allow-file | 5 | unknown |
| secrets-skip-gitlinks | 5 | unknown |
| init-writes-allow-entries | 6 | unknown |
| license-every-plugin | 6 | unknown |
| skill-text-local-bare-move | 5 | unknown |
| template-marker-skip | 6 | unknown |
| e2e-init-green | 5 | unknown (test run alone 47.8 min) |
| refresh-writes-allow-entries | 5 | unknown |
| e2e-behind-slow-marker | 6 | unknown |
| license-missing-refusal | 5 | unknown |
| ci-workflow-test-pins-e2e-jo | 5 | unknown |
| ruff-e501-errors-in-scripts | none | unknown |

e2e-init-green estimated 5 min but its verification run alone took 2867s: the estimate ignored test runtime.

### MRs and deploy

Meta mode: no MRs. Main fast-forwarded locally (474a64b -> 404c442), not pushed. Deploy: none. Live proof: claude-code-tatara template update a9dc548 succeeded with lint green.

### Lessons routed to

- Verifier deadline (540s) shorter than a legitimate e2e file: add a check in plan-execute/estimate that flags tasks whose test command is marked slow, and skip independent verification for them in favour of a recorded hand run (mechanical; check in estimate lint).
- Returns reported `$(see below)` as a landed head: add a schema check in the plan-execute return validation that `land.head` matches `^[0-9a-f]{40}$`.
- Test-only tasks cannot produce tdd-revert red evidence: add a rule in the verifier that a test-only diff takes the implementer `tests.red` and is not marked failed (mechanical, verify-task.py).
- Approvals marked `escalated` by a dependency-failed task that later passed: edit the plan-execute skill text so late returns restate every approval (judgement).
- Heavy e2e in the default suite: already routed to the slow marker and the pinned CI e2e job (test_ci_workflow.py).
