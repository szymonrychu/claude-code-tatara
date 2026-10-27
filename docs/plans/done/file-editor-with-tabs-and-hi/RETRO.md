# file editor with tabs and highlighting retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| web nomenclature allowlist | 1 | 1 | 4 | 3 | 656326 | 223259 |
| wrapper file write route | 5 | 5 | 11 | 5 | 1858483 | 1337349 |
| web editor languages | 5 | 3 | 11 | 7 | 1858483 | 1919629 |
| fake wrapper file write | 3 | 3 | 6 | 5 | 963314 | 759899 |
| orch file write route | 5 | 5 | 11 | 10 | 1858483 | 2156975 |
| orch wrapper pin write | 2 | 2 | 5 | 3 | 546295 | 392937 |
| web editor syntax check | 3 | 3 | 6 | 18 | 963314 | 1993732 |
| web code editor | 5 | 5 | 11 | 8 | 1858483 | 1550507 |
| web sync write api | 2 | 2 | 5 | 4 | 546295 | 485827 |
| web file tabs state | 5 | 5 | 11 | 11 | 1858483 | 1639317 |
| web file tabs view | 5 | 5 | 11 | 7 | 1858483 | 1828146 |
| web files split layout | 5 | 5 | 11 | 8 | 1858483 | 1811472 |
| web symlink tab stamps | 3 | 2 | 6 | 4 | 941421 | 414142 |
| orch write body cap | 2 | 2 | 5 | 13 | 543940 | 822045 |
| Total | 51 | 48 | 114 | 106 | 18170286 | 17335236 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| web nomenclature allowlist | 0 | 0.75 | 0.34 |
| wrapper file write route | 0 | 0.45 | 0.72 |
| web editor languages | -2 | 0.64 | 1.03 |
| fake wrapper file write | 0 | 0.83 | 0.79 |
| orch file write route | 0 | 0.91 | 1.16 |
| orch wrapper pin write | 0 | 0.60 | 0.72 |
| web editor syntax check | 0 | 3.00 | 2.07 |
| web code editor | 0 | 0.73 | 0.83 |
| web sync write api | 0 | 0.80 | 0.89 |
| web file tabs state | 0 | 1.00 | 0.88 |
| web file tabs view | 0 | 0.64 | 0.98 |
| web files split layout | 0 | 0.73 | 0.97 |
| web symlink tab stamps | -1 | 0.67 | 0.44 |
| orch write body cap | 0 | 2.60 | 1.51 |

- MdAPE points: 0.0%
- MdAPE minutes: 43.8%
- MdAPE tokens: 23.3%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| All 14 tasks delivered; points held (MdAPE 0.0%, 51 estimated vs 48 post-delivery; web editor languages re-scored 5 to 3, web symlink tab stamps 3 to 2). | web editor syntax check took 18 min vs 6 (3.00x, 2.07x tokens) and needed 2 fix rounds: a quadratic yaml duplicate-key check (fixed with a 500 ms cooperative budget and a linear check, c9bd6a9) and tests that were not honest (1c3c4da). |
| Totals under the seed: 106 min actual vs 114 expected, 17335236 tokens vs 18170286; 10 of 14 tasks under 1.0x minutes (wrapper file write route 0.45x, web nomenclature allowlist 0.75x). | orch write body cap took 13 min vs 5 (2.60x, 1.51x tokens); minutes MdAPE 43.8%, so the per-task minutes seed is loose both ways (0.45x to 3.00x). |
| Fix rounds were small and caught real defects: web-file-tabs-state (save did not invalidate an in-flight live refetch, 92529d1, with a test), orch-file-write-route (origin.py docstring, 0c99a1a). | The two defects the whole-epic reviewer found (symlink tab stamps, medium; no orchestrator write body cap, from the security review) passed per-task review; they became follow-up tasks web-symlink-tab-stamps and orch-write-body-cap, reviewed clean in round 2 (4c2690c, 1cd6f3b). The notes record fix rounds only for the 3 tasks above; rounds for the other tasks are unknown here. |
| Epic review round 1: reviewer accept with 1 medium; security review 3 medium and 2 low, each ruled: 1 acted (body cap), the rest dropped or deferred with a stated reason (agent-only racer already has a shell, lost-update window documented, setuid/setgid copy low, absent Origin cannot come from a browser). | Leadership handed over mid-epic (context over 35%); some mx-5 messages crossed during the handover. The handoff holds the state but the per-task review rounds only partly survive in .scratchpad/fe-review-notes.md. |
| Rulings were written down as they happened (ac3 via view.state.sliceDoc() for the CRLF separator, ac8 moved to web-files-split-layout ac13, download-icon test lookup changed), so the epic review could verify them. | The implementer of web-files-split-layout changed the download-icon test (FilesPanel.test.tsx:653-667, lookup file-preview-text to file-editor) and did not report it; the orchestrator found it and accepted it as "test no longer accurate" (housekeeping rule 2). |
| Final suites after round 2: web 625 passed, orchestrator only the known lightkube env failure plus Docker errors, lint clean. | Full suite round 1: web `1 failed | 622 passed`, PresetForm name_rules_default_name_and_pvc timed out at 5086 ms (5 s limit) under load; src/presets is untouched by this epic and the file alone passes 45/45. |
| | The orchestrator e2e CI takes about 16 min per PR, and the container has no Docker, so the DB tests were seen only in CI. |
| | Harbor prunes wrapper sha7 tags, so every orchestrator deploy that needs a newer wrapper requires a wrapper release tag; this blocked deploying straight after merge. |

## Improvements

- Code:
  - agents-web `src/presets` PresetForm test `name_rules_default_name_and_pvc`: times out at 5086 ms against the 5 s limit under full-suite load; give it an explicit timeout or cut its render cost.
  - agents-web `FilesPanel.test.tsx` (lines 653-667): the download-icon test now looks up `file-editor`; keep an assertion that no second preview element exists so the removal in ac10 stays pinned.
  - agents-web tab stamps: the scope audit found a duplicate `stampKey`; web-symlink-tab-stamps was the task to merge it, confirm a single definition remains.
  - agents-orchestrator write route (write body cap): the 1 MiB limit is a literal that mirrors the wrapper's `limits.file_preview_max_bytes`; derive it from one setting or pin it with a test.
- Delivered differently:
  - 14 tasks ran against 12 planned: web-symlink-tab-stamps and orch-write-body-cap were added by the epic review (a medium finding and a security finding).
  - web-file-tabs-view ac8 moved to web-files-split-layout ac13, because the chunk is only emitted once FilesPanel mounts FileTabs.
  - The download-icon test lookup changed from file-preview-text to file-editor, because the single preview was removed by design (ac10); assertion intent unchanged.
  - Wrapper part merged mid-epic (claude-code-wrapper #6, fb005fd) with the orchestrator pin amended to that sha, instead of one end-of-epic merge.
- Tech debt:
  - Deploy: browser saves get 403 unless the deployed orchestrator `allowed_origins` includes the UI origin; the deploy epic must set it.
  - Deploy: the orchestrator write cap assumes the wrapper default `limits.file_preview_max_bytes` of 1 MiB; a changed wrapper limit silently disagrees. Remove by reading one shared value.
  - Wrapper has no body cap on the write route (noted, not doing now; reachable only from the orchestrator and the agent's pod); add a limit in the wrapper route to remove it.
  - Intermediate-symlink TOCTOU on write (dropped; same as the download epic) and the check-then-replace lost-update window (documented in README/design): an open-then-fstat resolve and a version or mtime precondition would remove them.
  - setuid/setgid bits are copied by fchmod on write (low, dropped); masking them out in the wrapper write path would remove it.
  - Orchestrator Origin guard lets an absent Origin through (dropped; browsers always send Origin on cross-origin PUT); requiring a token for non-browser callers would remove it.
- Workflow:
  - recurring (markdown-rendering-in-chat, file-download-in-file-browse, paste-env-contents-into-the, leader-auto-handover): minutes and tokens seeds are off by task kind; here 10 of 14 tasks ran under 1.0x minutes while web editor syntax check (3.00x) and orch write body cap (2.60x) ran over. Change: calibrate minutes and tokens seeds by task kind from earlier epics' actuals (small client, fake and UI tasks lower; tasks with a perf or limit constraint and fix rounds higher).
  - recurring (file-download-in-file-browse, leader-auto-handover): no Docker in the pod makes orchestrator DB and e2e tests CI-only, about 16 min per PR. Change: provide a Docker-capable or shared-Postgres runner for agent pods, or have epic-run treat the CI watcher as the full-suite gate and start it as soon as the last task of a lane merges.
  - recurring (markdown-rendering-in-chat): a load-dependent vitest timeout in agents-web on the first full run; there the failing test was never named, here it is PresetForm name_rules_default_name_and_pvc. Change: the reviewer brief requires saving the failing test name and output tail before any rerun, and a named flake becomes a task, not a note.
  - recurring (leader-auto-handover, generic-any-mcp-with-git-and): defects that per-task verify and review missed, found only in the epic review (here the symlink tab stamps and the missing write body cap). Change: add to the reviewer brief a check of every write or upload route for a size cap and of every path or symlink handling against the AC, and run the security review's size and symlink checklist per task for routes that accept bodies.
  - recurring (leader-auto-handover): work split across two leader sessions loses the review rounds and rulings of the earlier half (here only 3 tasks carry fix rounds; mx-5 messages also crossed during the handover). Change: `handoff` requires the per-task review-round list and the last mx-5 message ids sent and received, and the orchestrator notes file is written at each task close, not summarized at the end.
  - recurring (generic-any-mcp-with-git-and): the deploy depends on Harbor holding image tags; there a lost connector image broke smoke, here Harbor prunes wrapper sha7 tags so an orchestrator deploy needing a newer wrapper requires a wrapper release tag. Change: the deploy epic's plan pins the wrapper by release tag and cuts it before the orchestrator task, and the planning checklist adds "does the pinned image tag survive Harbor pruning".
  - An implementer changed an existing test and did not report it (one-off, Retro table only).
