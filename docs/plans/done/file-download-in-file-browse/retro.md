# file download in file browser retro

## Review

Migrated from the epic format.

## What went well

- All 7 tasks closed clean in the first review round: zero fix rounds, zero escalations.
- Points held: 21 estimated, 21 post-delivery, MdAPE 0.0%.
- Whole-epic review (sonnet) clean; cross-repo seams (headers, error map, fake vs real wrapper, target_type) consistent.
- Scope audit: complete, no gaps, no new tasks.
- Security review: no critical, high or medium findings; two LOW findings dropped with rulings (intermediate-symlink TOCTOU in resolve_in_workdir, pre-existing and shared with read_preview; no concurrent-download cap, same posture as the existing file routes).
- Minutes under the seed in total: 34 actual vs 48 expected; six of seven tasks at 0.55-0.82x (web sync orchestrator api at 1.00x).
- claude-code-wrapper PR #5 CI green (unit, integration, build-push), merged as 4581f3b; agents-web full suite `Tests  515 passed (515)`, lint clean.
- One implementer added an out-of-Notes fixture commit; judged and accepted.

## What went wrong or could improve

- Superrepo push was blocked by GitHub email privacy; 90 commits had to be rewritten to the noreply address.
- The global gitconfig had lost user.name and user.email (pod reset), so commits failed until a repo-local identity was set.
- The https origins of agents-orchestrator and agents-web had no credential helper, so pushes needed manual setup.
- The orchestrator's own MEMORY.md edit tripped lint:personal and pushed a red main briefly; fixed in the next commit.
- No Docker in the container: agents-orchestrator full suite ended `1 failed, 571 passed, 59 deselected, 1 warning, 525 errors` (testcontainers); the 1 failure (test_reconciler.py::test_lightkube_default_client_uses_env_config) and 3 wrapper process-group tests also fail on main. CI is the only full verifier.
- The claude-code-wrapper full suite takes about 14 min locally (`3 failed, 1682 passed, 26 deselected`).
- orch file download route used 3271323 tokens vs 1858483 expected (1.76x), the only token overrun; tokens MdAPE 61.3%, minutes MdAPE 50.0%.

## Recommendations

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

## Delivery record (migrated)

### Asked

A small arrow-down icon on every file row of the Files tree, right-aligned, that downloads the workspace file to the user's computer. Byte-exact, text and binary, any size (no 1 MiB preview cap). New raw-bytes route in claude-code-wrapper, an orchestrator route forwarding it, existing workspace path guards kept. Non-goals: directory or archive download, upload.

### Shipped

Wrapper raw-bytes download route plus `target_type` on symlink listing entries; orchestrator streaming download route, wrapper client `open_download`, fake wrapper held to the contract, wrapper pin 4581f3b with an e2e case; web download icon on file rows via a plain anchor, schema synced. Epic review verdict: pass (2026-10-27); whole-epic review clean, scope audit complete with no gaps, security review with no critical/high/medium findings.

PRs (all merged, CI green):
- claude-code-wrapper ee10aa8..4581f3b: https://github.com/szymonrychu/claude-code-wrapper/pull/5 (unit, integration, build-push)
- agents-orchestrator 90f3ce3..cd52203: https://github.com/szymonrychu/agents-orchestrator/pull/26 (lint, test, e2e, chart, images)
- agents-web 4701820..03f05da: https://github.com/szymonrychu/agents-web/pull/17

Deploy: not deployed (gate: one deploy epic for the four epics later). Deploy coupling: orchestrator `FileEntry.target_type` is required, so the orchestrator image must deploy with wrapper >= 4581f3b. Superrepo pointer commit: ba78c346 (advance claude-code-wrapper to 4581f3b, agents-orchestrator to cd52203, agents-web to 03f05da).

### Tasks

7 of 7 planned tasks done. Every task was clean at the first review: 0 fix rounds. Verified heads all appear in the epic git logs. The per-task verification tail (summary line) is not in the orchestrator notes: unknown per task; the notes give only the full-suite results below.

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| wrapper-client-download (orchestrator) | done | e6aaf416717ce80333604f89da894e501740a7e4 | 0 fix rounds | unknown |
| wrapper-file-download-route (wrapper) | done | 7f7cd159d95e3445299b72c653eb703ef917142a | 0 fix rounds | unknown; implementer full run on 7f7cd15: `3 failed, 1682 passed, 26 deselected` (3 process-group tests fail identically on main ee10aa8) |
| fake-wrapper-download (orchestrator) | done | bd809e04997d2b08d5af63df3527aabaf5bed737 | 0 fix rounds | unknown; real leg runs only in CI |
| orch-file-download-route (orchestrator) | done | 33d1c8fafb09af72ec2dbb3d1683547e438f36d6 | 0 fix rounds | unknown; `tests/test_api_files.py` and contract real leg run only in CI (Docker) |
| web-sync-orchestrator-api (web) | done | 47a13832e81939c5500e81a061d4b92ca953e01c | 0 fix rounds | unknown; head includes fixture commit 47a1383 beyond the task Notes (see Rulings) |
| web-download-icon (web) | done | e7a2499db68fcf04a25f324fed88875c3faea644 | 0 fix rounds | unknown |
| orch-wrapper-pin-download (orchestrator) | done | 34194f4416736c64635cde6cd6ddba7f6f99928b | 0 fix rounds | unknown; task amended with sha 4581f3b after PR #5 merged |

Full suites in this container (orchestrator notes):
- agents-web: `Tests  515 passed (515)`, lint clean.
- agents-orchestrator: `1 failed, 571 passed, 59 deselected, 1 warning, 525 errors`; 525 errors are testcontainers without Docker; the 1 failure (`test_reconciler.py::test_lightkube_default_client_uses_env_config`) fails identically on main 90f3ce3. CI runs the full suite and is green.
- claude-code-wrapper: see the wrapper row; PR #5 CI green.

Notes and files agree; no contradiction found.

### Rulings

- web-sync-orchestrator-api: fixture commit 47a1383 (`target_type: null` in the `FileEntry` fixture) added beyond the task Notes. Why: tsc fails without it after the type sync. Reviewer accepted. Cost if wrong: one extra fixture line in a test file; trivial to revert.
- wrapper-file-download-route: undecodable file names render as `?` per design D2; the `_printable` docstring was corrected to say so. Cost if wrong: a download name with `?` instead of the original bytes for non-UTF-8 names.
- wrapper-file-download-route: download name is the last segment of the normalised requested path (link name for a symlink); fallback charset is printable ASCII 0x20-0x7E minus `"` and `\`, other characters `_`; `target_type` is null for dangling, looping and escaping links; bytes read stop at the `fstat` size. Each is pinned by a test named in the task Notes. Cost if wrong: wrong file name or type icon shown for odd links; the byte stream itself is unaffected.
- orch-file-download-route: amended because the design's abort-after-first-byte behaviour had no acceptance condition; builder's call, recorded in the task Notes. Cost if wrong: a mid-stream upstream failure may surface to the browser as a truncated download rather than a clean error.
- orch-wrapper-pin-download: wrapper PR #5 merged mid-epic, so the task was amended with the merge sha 4581f3b and the pin points at it. Cost if wrong: none while the sha stays on wrapper main.
- web-download-icon: icon rows are file and symlink with `target_type` file; dir, other and symlink with `target_type` dir, other or null get no icon. Plain anchor rather than fetch plus blob (blob buffers the whole file); errors surface in the browser, not the panel (MEMORY.md entry). Cost if wrong: a failed download shows the browser error page instead of an in-panel message.
- Security finding dropped, LOW 1: intermediate-symlink TOCTOU in `resolve_in_workdir`. Pre-existing, shared with `read_preview`, exploitable only by an agent that already has a shell in the same container. Cost if wrong: that agent could read a file outside the workdir through the new route as well as the preview route.
- Security finding dropped, LOW 2: no concurrent-download cap. Same posture as the existing file routes, behind ingress auth, outside epic scope. Cost if wrong: many parallel large downloads could load the wrapper.
- Fake wrapper duplicates three wrapper helpers by design (task note), pinned by the contract suite; scope audit found no gap. Cost if wrong: fake drifts from the wrapper; the contract suite's real leg catches it in CI.

### Discovered and blocked

- Blocked: deploy. Deferred to one deploy epic covering four epics; the user schedules it. It must ship the orchestrator image with wrapper >= 4581f3b.
- Discovered: `test_reconciler.py::test_lightkube_default_client_uses_env_config` fails on main 90f3ce3 in this container (in-cluster `KUBERNETES_SERVICE_HOST` env). Owner of agents-orchestrator can fix it; CI is unaffected.
- Discovered: 3 wrapper process-group tests fail on main ee10aa8 in this container (no PID 1 reaper); `tests/test_container.py` needs docker. Owner of claude-code-wrapper; CI is green.
- Discovered: orchestrator testcontainers tests (525 errors) cannot run here without Docker; only CI exercises them.
- Discovered: agents-web full suite has 10 load-dependent timeouts in unrelated files (PresetForm, ScheduleForm, Endpoints, FiltersEditor), per the web-download-icon Notes; owner of agents-web. The final full run passed 515 of 515.
- Unknown: whether a Harbor image exists for wrapper 4581f3b (only `main` builds publish it); the e2e script builds from source otherwise.

### Not pushed

- claude-code-wrapper, agents-orchestrator, agents-web: `git log origin/main..main` is empty in each submodule; all epic commits are merged through the PRs above.
- Superrepo: local `origin/main` is f7007d95 and `git log origin/main..main` lists 15 commits, from 699069b3 (move in-progress) to cf614396 (a different epic, markdown-rendering-in-chat, move in-progress), including every ticket commit of this epic. The notes say main was pushed after rewriting 90 unpushed commits to the user's GitHub noreply address (user-approved); that push predates these commits, or the local ref is stale (not checked, no network). The user or the orchestrator pushes.
- Origins for agents-orchestrator and agents-web are https: pushes need `-c credential.helper='!gh auth git-credential'`. A local branch `backup/pre-email-rewrite` exists in the superrepo.

### Lessons routed to

- Superrepo push blocked by GitHub email privacy after 90 commits carried a personal address (mechanical): add a pre-commit or pre-push hook, or a `ticket.py` check, that rejects commits whose author email is not the noreply address.
- Schema sync broke a test fixture and the task `files` list did not name it (mechanical): `ticket.py` task lint cannot see this; the existing `tsc -b` in the sync task's verify caught it. Add `src/**/*.test.tsx` fixtures to the `files` list of any web sync task, or have the planner template include them.
- Required field `target_type` creates a cross-repo deploy ordering constraint (judgement call): edit the start-development design template so a required field added across a service boundary lists the deploy coupling in design.md; carried here in Shipped for the deploy epic.
- Design behaviour with no acceptance condition (abort after first byte) was found by the builder, not the planner (judgement call): edit the plan-review checklist in start-development to require an acceptance condition for each stated failure mode.
- Pre-existing environment failures (reconciler, process-group, testcontainers) repeat in every epic (mechanical): add a known-failures list checked by the verify wrapper, or mark those tests with a skip condition for missing Docker, PID 1 and in-cluster env.
