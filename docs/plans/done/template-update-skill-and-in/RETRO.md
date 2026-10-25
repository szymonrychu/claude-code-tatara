# Template update skill and init docs cleanup retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| Instance owned paths | 1 | not recorded | 8 | not recorded | 750000 | not recorded |
| Update command | 1 | not recorded | 10 | not recorded | 750000 | not recorded |
| Update conflicts and abort | 1 | not recorded | 8 | not recorded | 750000 | not recorded |
| Update unrelated history | 1 | not recorded | 8 | not recorded | 750000 | not recorded |
| E2e template update | 1 | not recorded | 8 | not recorded | 750000 | not recorded |
| Template update skill | 1 | not recorded | 6 | not recorded | 750000 | not recorded |
| Docs update flow | 1 | not recorded | 5 | not recorded | 750000 | not recorded |
| Update safety | not recorded | not recorded | not recorded | 11 | not recorded | 1422602 |
| Existing remote kept | not recorded | not recorded | not recorded | 4 | not recorded | 362093 |
| Total | 7 (7 of 9 tasks) | not recorded | 53 (7 of 9 tasks) | 15 (2 of 9 tasks) | 5250000 (7 of 9 tasks) | 1784695 (2 of 9 tasks) |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| Instance owned paths | not recorded | not recorded | not recorded |
| Update command | not recorded | not recorded | not recorded |
| Update conflicts and abort | not recorded | not recorded | not recorded |
| Update unrelated history | not recorded | not recorded | not recorded |
| E2e template update | not recorded | not recorded | not recorded |
| Template update skill | not recorded | not recorded | not recorded |
| Docs update flow | not recorded | not recorded | not recorded |
| Update safety | not recorded | not recorded | not recorded |
| Existing remote kept | not recorded | not recorded | not recorded |

- MdAPE points: not recorded
- MdAPE minutes: not recorded
- MdAPE tokens: not recorded
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| 7 planned tasks landed; all 9 tasks done, verdict pass, main 6b4b660 with scripts 467 passed, plugin 2817 assertions, lint green. | 7 of 9 tasks needed 2 review rounds (update-command to existing-remote-kept); only instance-owned-paths passed in round 1, and docs-update-flow escalated. |
| Phase 5 found a real HIGH: restore_owned deleted gitignored docs/research and docs/handoffs; update-safety added, red against pre-fix update.py (8 failed), now 17 passed. | The HIGH data-loss bug shipped through all 7 planned tasks' reviews and was caught only by the epic security review. |
| Scope audit found the update-command AC4 gap (existing template remote keeps its URL); existing-remote-kept pinned it, red by mutation. | update-command: independent verifier reported AC2-AC8 not met and the implementer could not reproduce it; later suites passed, so the verdict was noise (2 rounds spent). |
| Red evidence recorded per behaviour task (instance-owned-paths: ModuleNotFoundError, 3 failed; update-command: 1 failed, 13 passed); exceptions named for the rest. | docs-update-flow: `verified` false with empty evidence caused a gate-repeat; hand-verified (check_personal rc 0, README grep rc 0), and the README `init:update` flags then needed a `--` fix at landing. |
| Rulings carried cost-if-wrong (docs-update-flow, existing-remote-kept, Q1 handoffs). | existing-remote-kept stopped on the TDD-skipped gate for a pin test with no non-test change; accepted by ruling. |
| Landing used plain --no-ff merges in landing trees with the full suite before each fast-forward of main; no forward merges, no blocked or undelivered tasks. | Landing fixes outside task scope: init_engine helpers shadowed e2e helpers (d87b383), the spelled default URL tripped the personal-term lint (1b4755a), three AC refs broke on renamed tests. |
| | Deltas are all "not recorded": no post-delivery points, no actual minutes on the 7 planned tasks, README Time Actual 0 (never filled); the two remediation tasks have actuals (11 and 4 min, 1422602 and 362093 tokens) but no estimate. MdAPE unmeasurable. |
| | Open cannotVerify: no live run against the real template URL, git versions other than 2.56 unchecked, ignored files created by refresh are not removed on abort. |

## Improvements

- Code:
  - scripts/init_engine/update.py: URL comparison is a strict string compare; trailing-slash or `.git` variants count as a different URL. Normalise if wanted.
  - scripts/init_engine/update.py: abort cleanup leaves ignored files created by refresh; handle them scoped to owned paths, with a test.
  - scripts/tests (test_update_conflicts.py, test_update_unrelated.py): wiring and rename-only tests have no red; add a mutation check for the engine paths they guard.
  - MEMORY.md: duplicate 2026-10-20 line (pre-existing) left in place.
- Delivered differently:
  - Two remediation tasks (update-safety, existing-remote-kept) were added in phase 5 beyond the 7 planned; the plan missed ignored-file safety and the existing-remote AC test.
  - update-safety's fix was committed earlier (0c61e73) than its task; the task only renamed tests, so its red was shown by restoring pre-fix update.py.
  - README `init:update` flags were planned without `--`; the landing put them after `--` (217e844).
  - Skill text describes the default URL instead of spelling it, to satisfy the personal-term lint (1b4755a).
- Tech debt:
  - Hidden test-only `--lint-command` flag in update.py and `git add -A` after refresh: dismissed by design; removal needs a test seam that does not ship in the CLI.
  - Live behaviour of the skill's confirmation prompt for a non-default `--url` is untested; remove with a live skill run.
  - No live run against the real GitHub template (local upstreams and `insteadOf` only); remove with one manual run.
- Workflow:
  - recurring (housekeeping-rules-estimates): points, expected and actual minutes and tokens read "not recorded" again, so Deltas and MdAPE are empty. Change: epic-run records actuals at each task close, `move done` refuses while README Time Actual is 0 or a planned task lacks post-delivery points, and remediation tasks are created with estimates.
  - recurring (housekeeping-rules-estimates): implementer or verifier claims were unreliable (empty verifier evidence here; false greens from tail reads there). Change: the gate fails a task whose evidence is empty while the command passed, and the reviewer reruns the check itself instead of trusting the report.
  - Add a lint that each task's AC test refs resolve to a collected test, and a collection-time check for duplicate helper module names under scripts/tests (three refs broke, one shadowing).
  - Add `check_personal.py` to the verify command of tasks that edit skills or docs, so it fails before landing.
  - Name "pin test, red by mutation" as a listed exception in the tdd rule so it stops tripping the TDD-skipped gate.
  - Add a security-review prompt line: run destructive commands against trees with ignored owned paths. Seen once; raise to a proposal only if it recurs.
