# file download in file browser retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| wrapper client download | 2 | 2 | 5 | 3 | 546295 | 338636 |
| wrapper file download route | 5 | 5 | 11 | 6 | 1858483 | 887331 |
| fake wrapper download | 3 | 3 | 6 | 4 | 963314 | 370840 |
| orch file download route | 5 | 5 | 11 | 9 | 1858483 | 3271323 |
| web sync orchestrator api | 1 | 1 | 4 | 4 | 656326 | 458404 |
| web download icon | 3 | 3 | 6 | 4 | 963314 | 534640 |
| orch wrapper pin download | 2 | 2 | 5 | 4 | 546295 | 364866 |
| Total | 21 | 21 | 48 | 34 | 7392510 | 6226040 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| wrapper client download | 0 | 0.60 | 0.62 |
| wrapper file download route | 0 | 0.55 | 0.48 |
| fake wrapper download | 0 | 0.67 | 0.38 |
| orch file download route | 0 | 0.82 | 1.76 |
| web sync orchestrator api | 0 | 1.00 | 0.70 |
| web download icon | 0 | 0.67 | 0.56 |
| orch wrapper pin download | 0 | 0.80 | 0.67 |

- MdAPE points: 0.0%
- MdAPE minutes: 50.0%
- MdAPE tokens: 61.3%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| All 7 tasks closed clean in the first review round: zero fix rounds, zero escalations. | Superrepo push was blocked by GitHub email privacy; 90 commits had to be rewritten to the noreply address. |
| Points held: 21 estimated, 21 post-delivery, MdAPE 0.0%. | The global gitconfig had lost user.name and user.email (pod reset), so commits failed until a repo-local identity was set. |
| Whole-epic review (sonnet) clean; cross-repo seams (headers, error map, fake vs real wrapper, target_type) consistent. | The https origins of agents-orchestrator and agents-web had no credential helper, so pushes needed manual setup. |
| Scope audit: complete, no gaps, no new tasks. | The orchestrator's own MEMORY.md edit tripped lint:personal and pushed a red main briefly; fixed in the next commit. |
| Security review: no critical, high or medium findings; two LOW findings dropped with rulings (intermediate-symlink TOCTOU in resolve_in_workdir, pre-existing and shared with read_preview; no concurrent-download cap, same posture as the existing file routes). | No Docker in the container: agents-orchestrator full suite ended `1 failed, 571 passed, 59 deselected, 1 warning, 525 errors` (testcontainers); the 1 failure (test_reconciler.py::test_lightkube_default_client_uses_env_config) and 3 wrapper process-group tests also fail on main. CI is the only full verifier. |
| Minutes under the seed in total: 34 actual vs 48 expected; six of seven tasks at 0.55-0.82x (web sync orchestrator api at 1.00x). | The claude-code-wrapper full suite takes about 14 min locally (`3 failed, 1682 passed, 26 deselected`). |
| claude-code-wrapper PR #5 CI green (unit, integration, build-push), merged as 4581f3b; agents-web full suite `Tests  515 passed (515)`, lint clean. | orch file download route used 3271323 tokens vs 1858483 expected (1.76x), the only token overrun; tokens MdAPE 61.3%, minutes MdAPE 50.0%. |
| One implementer added an out-of-Notes fixture commit; judged and accepted. | |

## Improvements

- Code:
  - agents-orchestrator `test_reconciler.py::test_lightkube_default_client_uses_env_config`: fails when KUBERNETES_SERVICE_HOST is set in the environment (in-cluster); the test should clear or patch that env var so it passes anywhere.
  - Wrapper process-group tests (3): fail without a PID 1 reaper; skip or fixture-guard them when the environment lacks one, so a container run is not red on main.
  - Fake wrapper (task fake wrapper download) duplicates three wrapper helpers by design; the contract suite pins them, so keep that suite in the epic's verify.
- Delivered differently:
  - One implementer added a fixture commit outside the task Notes; accepted because the diff stayed in scope.
  - The superrepo history was rewritten (90 commits to the noreply address) before push, because GitHub email privacy blocked the original author addresses.
- Tech debt:
  - Intermediate-symlink TOCTOU in claude-code-wrapper `resolve_in_workdir` (pre-existing, shared with read_preview, LOW, dropped): resolving with an open-then-fstat on the final path would remove it.
  - No concurrent-download cap on the file routes (LOW, dropped): a per-session semaphore in the wrapper route would remove it.
  - Deploy coupling: orchestrator `FileEntry.target_type` is required, so the orchestrator image must deploy with wrapper >= 4581f3b; the later deploy epic must pin them together.
- Workflow:
  - recurring (leader-auto-handover): no Docker in the pod makes the orchestrator DB tests CI-only (525 testcontainers errors here; about 16 min per PR there). Change: provide a Docker-capable or shared-Postgres runner for agent pods, or make epic-run's task verify run the targeted non-DB tests locally and treat the CI watcher as the full-suite gate.
  - recurring (leader-auto-handover): the session gitconfig had no identity and no credential helper (there: no user identity and no gh helper; here: lost user.name/email after a pod reset, and no helper on two https origins). Change: the harness setup or SessionStart hook sets user.name, user.email and `gh auth setup-git`, and the epic-run preflight checks `git config user.email` before the first task.
  - recurring (paste-env-contents-into-the): minutes and tokens seeds far off actuals; there small pure-module and UI tasks came in at 0.17-0.46x, here six of seven tasks came in at 0.55-0.82x minutes and 0.38-0.70x tokens, while the orchestrator route task ran 1.76x tokens. Change: calibrate minutes and tokens seeds by task kind from earlier epics' actuals (small client, fake and UI tasks lower; routes with new error maps higher).
  - Orchestrator-authored edit to MEMORY.md tripped lint:personal and pushed a red main (one-off, Retro table only).
  - GitHub email privacy blocking the superrepo push (one-off, Retro table only).
