# Init leaves a green tree retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| personal allow file | 1 | not recorded | 5 | not recorded | 750000 | not recorded |
| secrets skip gitlinks | 1 | not recorded | 5 | not recorded | 750000 | not recorded |
| skill text local bare move | 1 | not recorded | 5 | not recorded | 750000 | not recorded |
| init writes allow entries | 1 | not recorded | 6 | not recorded | 750000 | not recorded |
| ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch | not recorded | not recorded | not recorded | not recorded | not recorded | not recorded |
| template marker skip | 1 | not recorded | 6 | not recorded | 750000 | not recorded |
| e2e init green | 1 | not recorded | 5 | not recorded | 750000 | not recorded |
| refresh writes allow entries | 1 | not recorded | 5 | not recorded | 750000 | not recorded |
| license missing refusal | 1 | not recorded | 5 | not recorded | 750000 | not recorded |
| e2e behind slow marker | 1 | not recorded | 6 | not recorded | 750000 | not recorded |
| ci workflow test pins e2e job | 1 | not recorded | 5 | not recorded | 750000 | not recorded |
| license every plugin | 1 | not recorded | 6 | not recorded | 750000 | not recorded |
| Total | 11 (11 of 12 tasks) | not recorded | 59 (11 of 12 tasks) | not recorded | 8250000 (11 of 12 tasks) | not recorded |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| personal allow file | not recorded | not recorded | not recorded |
| secrets skip gitlinks | not recorded | not recorded | not recorded |
| skill text local bare move | not recorded | not recorded | not recorded |
| init writes allow entries | not recorded | not recorded | not recorded |
| ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch | not recorded | not recorded | not recorded |
| template marker skip | not recorded | not recorded | not recorded |
| e2e init green | not recorded | not recorded | not recorded |
| refresh writes allow entries | not recorded | not recorded | not recorded |
| license missing refusal | not recorded | not recorded | not recorded |
| e2e behind slow marker | not recorded | not recorded | not recorded |
| ci workflow test pins e2e job | not recorded | not recorded | not recorded |
| license every plugin | not recorded | not recorded | not recorded |

- MdAPE points: not recorded
- MdAPE minutes: not recorded
- MdAPE tokens: not recorded
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| 5 of 12 tasks passed with 0 or 1 fix rounds and a quoted red (secrets-skip-gitlinks, init-writes-allow-entries, license-every-plugin, e2e-behind-slow-marker, license-missing-refusal each had 1 round with a named failing test). | e2e-init-green hit the round cap (3 rounds, verified=false) and the verifier timed out at 540s against a 48-min file; hand-verified on 27d001e (7 passed in 2867.48s). |
| Live update of claude-code-tatara exposed that refresh did not write the allow file; this became refresh-writes-allow-entries and the update then succeeded (a9dc548). | e2e-init-green was estimated at 5 min but its test run alone took 2867s: the estimate ignored test runtime. |
| Rulings were explicit with cost-if-wrong: template-marker-skip gate-repeat accepted (conftest.py:78 skipif is the deliverable), ruff-e501 accepted with no change (wrap already in ce694a7). | template-marker-skip needed 2 rounds and stopped on a gate-repeat false positive (debt-marker check matched an explanatory comment at conftest.py:68). |
| Review findings were placed as tasks, not dropped: refresh-writes-allow-entries, e2e-behind-slow-marker, license-missing-refusal, ci-workflow-test-pins-e2e-jo (9 planned, 3 added per record summary; 4 added per rulings). | Tasks, rounds and approvals bookkeeping was unreliable: return 1 marked all five approvals escalated and e2e-init-green dependency-failed, and license-every-plugin's return head was the literal "$(see below)" (no SHA). |
| Final gate passed: `mise run test && mise run lint` on main (close.json), lint:secrets "no leaks found". | ci-workflow-test-pins-e2e-jo has no populated tests.red or verification.evidence; a test-only commit gives tdd-revert nothing to restore. |
| | Points, minutes and tokens actuals are "not recorded" for all 12 tasks, so every delta and MdAPE is unmeasured; ruff-e501-errors-in-scripts has no estimate at all. |
| | The new e2e CI job is unconfirmed on GitHub Actions because main is not pushed; the two slow e2e tests were not run by the e2e-behind-slow-marker implementer (~48 min). |

## Improvements

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
