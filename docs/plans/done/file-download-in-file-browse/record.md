# file download in file browser record

## Asked

A small arrow-down icon on every file row of the Files tree, right-aligned, that downloads the workspace file to the user's computer. Byte-exact, text and binary, any size (no 1 MiB preview cap). New raw-bytes route in claude-code-wrapper, an orchestrator route forwarding it, existing workspace path guards kept. Non-goals: directory or archive download, upload.

## Shipped

Wrapper raw-bytes download route plus `target_type` on symlink listing entries; orchestrator streaming download route, wrapper client `open_download`, fake wrapper held to the contract, wrapper pin 4581f3b with an e2e case; web download icon on file rows via a plain anchor, schema synced. Epic review verdict: pass (2026-10-27); whole-epic review clean, scope audit complete with no gaps, security review with no critical/high/medium findings.

PRs (all merged, CI green):
- claude-code-wrapper ee10aa8..4581f3b: https://github.com/szymonrychu/claude-code-wrapper/pull/5 (unit, integration, build-push)
- agents-orchestrator 90f3ce3..cd52203: https://github.com/szymonrychu/agents-orchestrator/pull/26 (lint, test, e2e, chart, images)
- agents-web 4701820..03f05da: https://github.com/szymonrychu/agents-web/pull/17

Deploy: not deployed (gate: one deploy epic for the four epics later). Deploy coupling: orchestrator `FileEntry.target_type` is required, so the orchestrator image must deploy with wrapper >= 4581f3b. Superrepo pointer commit: ba78c346 (advance claude-code-wrapper to 4581f3b, agents-orchestrator to cd52203, agents-web to 03f05da).

## Tasks

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

## Rulings

- web-sync-orchestrator-api: fixture commit 47a1383 (`target_type: null` in the `FileEntry` fixture) added beyond the task Notes. Why: tsc fails without it after the type sync. Reviewer accepted. Cost if wrong: one extra fixture line in a test file; trivial to revert.
- wrapper-file-download-route: undecodable file names render as `?` per design D2; the `_printable` docstring was corrected to say so. Cost if wrong: a download name with `?` instead of the original bytes for non-UTF-8 names.
- wrapper-file-download-route: download name is the last segment of the normalised requested path (link name for a symlink); fallback charset is printable ASCII 0x20-0x7E minus `"` and `\`, other characters `_`; `target_type` is null for dangling, looping and escaping links; bytes read stop at the `fstat` size. Each is pinned by a test named in the task Notes. Cost if wrong: wrong file name or type icon shown for odd links; the byte stream itself is unaffected.
- orch-file-download-route: amended because the design's abort-after-first-byte behaviour had no acceptance condition; builder's call, recorded in the task Notes. Cost if wrong: a mid-stream upstream failure may surface to the browser as a truncated download rather than a clean error.
- orch-wrapper-pin-download: wrapper PR #5 merged mid-epic, so the task was amended with the merge sha 4581f3b and the pin points at it. Cost if wrong: none while the sha stays on wrapper main.
- web-download-icon: icon rows are file and symlink with `target_type` file; dir, other and symlink with `target_type` dir, other or null get no icon. Plain anchor rather than fetch plus blob (blob buffers the whole file); errors surface in the browser, not the panel (MEMORY.md entry). Cost if wrong: a failed download shows the browser error page instead of an in-panel message.
- Security finding dropped, LOW 1: intermediate-symlink TOCTOU in `resolve_in_workdir`. Pre-existing, shared with `read_preview`, exploitable only by an agent that already has a shell in the same container. Cost if wrong: that agent could read a file outside the workdir through the new route as well as the preview route.
- Security finding dropped, LOW 2: no concurrent-download cap. Same posture as the existing file routes, behind ingress auth, outside epic scope. Cost if wrong: many parallel large downloads could load the wrapper.
- Fake wrapper duplicates three wrapper helpers by design (task note), pinned by the contract suite; scope audit found no gap. Cost if wrong: fake drifts from the wrapper; the contract suite's real leg catches it in CI.

## Discovered and blocked

- Blocked: deploy. Deferred to one deploy epic covering four epics; the user schedules it. It must ship the orchestrator image with wrapper >= 4581f3b.
- Discovered: `test_reconciler.py::test_lightkube_default_client_uses_env_config` fails on main 90f3ce3 in this container (in-cluster `KUBERNETES_SERVICE_HOST` env). Owner of agents-orchestrator can fix it; CI is unaffected.
- Discovered: 3 wrapper process-group tests fail on main ee10aa8 in this container (no PID 1 reaper); `tests/test_container.py` needs docker. Owner of claude-code-wrapper; CI is green.
- Discovered: orchestrator testcontainers tests (525 errors) cannot run here without Docker; only CI exercises them.
- Discovered: agents-web full suite has 10 load-dependent timeouts in unrelated files (PresetForm, ScheduleForm, Endpoints, FiltersEditor), per the web-download-icon Notes; owner of agents-web. The final full run passed 515 of 515.
- Unknown: whether a Harbor image exists for wrapper 4581f3b (only `main` builds publish it); the e2e script builds from source otherwise.

## Not pushed

- claude-code-wrapper, agents-orchestrator, agents-web: `git log origin/main..main` is empty in each submodule; all epic commits are merged through the PRs above.
- Superrepo: local `origin/main` is f7007d95 and `git log origin/main..main` lists 15 commits, from 699069b3 (move in-progress) to cf614396 (a different epic, markdown-rendering-in-chat, move in-progress), including every ticket commit of this epic. The notes say main was pushed after rewriting 90 unpushed commits to the user's GitHub noreply address (user-approved); that push predates these commits, or the local ref is stale (not checked, no network). The user or the orchestrator pushes.
- Origins for agents-orchestrator and agents-web are https: pushes need `-c credential.helper='!gh auth git-credential'`. A local branch `backup/pre-email-rewrite` exists in the superrepo.

## Lessons routed to

- Superrepo push blocked by GitHub email privacy after 90 commits carried a personal address (mechanical): add a pre-commit or pre-push hook, or a `ticket.py` check, that rejects commits whose author email is not the noreply address.
- Schema sync broke a test fixture and the task `files` list did not name it (mechanical): `ticket.py` task lint cannot see this; the existing `tsc -b` in the sync task's verify caught it. Add `src/**/*.test.tsx` fixtures to the `files` list of any web sync task, or have the planner template include them.
- Required field `target_type` creates a cross-repo deploy ordering constraint (judgement call): edit the start-development design template so a required field added across a service boundary lists the deploy coupling in design.md; carried here in Shipped for the deploy epic.
- Design behaviour with no acceptance condition (abort after first byte) was found by the builder, not the planner (judgement call): edit the plan-review checklist in start-development to require an acceptance condition for each stated failure mode.
- Pre-existing environment failures (reconciler, process-group, testcontainers) repeat in every epic (mechanical): add a known-failures list checked by the verify wrapper, or mark those tests with a skip condition for missing Docker, PID 1 and in-cluster env.
