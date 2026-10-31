# file editor with tabs and highlighting retro

## Review

Migrated from the epic format.

## What went well

- All 14 tasks delivered; points held (MdAPE 0.0%, 51 estimated vs 48 post-delivery; web editor languages re-scored 5 to 3, web symlink tab stamps 3 to 2).
- Totals under the seed: 106 min actual vs 114 expected, 17335236 tokens vs 18170286; 10 of 14 tasks under 1.0x minutes (wrapper file write route 0.45x, web nomenclature allowlist 0.75x).
- Fix rounds were small and caught real defects: web-file-tabs-state (save did not invalidate an in-flight live refetch, 92529d1, with a test), orch-file-write-route (origin.py docstring, 0c99a1a).
- Epic review round 1: reviewer accept with 1 medium; security review 3 medium and 2 low, each ruled: 1 acted (body cap), the rest dropped or deferred with a stated reason (agent-only racer already has a shell, lost-update window documented, setuid/setgid copy low, absent Origin cannot come from a browser).
- Rulings were written down as they happened (ac3 via view.state.sliceDoc() for the CRLF separator, ac8 moved to web-files-split-layout ac13, download-icon test lookup changed), so the epic review could verify them.
- Final suites after round 2: web 625 passed, orchestrator only the known lightkube env failure plus Docker errors, lint clean.

## What went wrong or could improve

- web editor syntax check took 18 min vs 6 (3.00x, 2.07x tokens) and needed 2 fix rounds: a quadratic yaml duplicate-key check (fixed with a 500 ms cooperative budget and a linear check, c9bd6a9) and tests that were not honest (1c3c4da).
- orch write body cap took 13 min vs 5 (2.60x, 1.51x tokens); minutes MdAPE 43.8%, so the per-task minutes seed is loose both ways (0.45x to 3.00x).
- The two defects the whole-epic reviewer found (symlink tab stamps, medium; no orchestrator write body cap, from the security review) passed per-task review; they became follow-up tasks web-symlink-tab-stamps and orch-write-body-cap, reviewed clean in round 2 (4c2690c, 1cd6f3b). The notes record fix rounds only for the 3 tasks above; rounds for the other tasks are unknown here.
- Leadership handed over mid-epic (context over 35%); some mx-5 messages crossed during the handover. The handoff holds the state but the per-task review rounds only partly survive in .scratchpad/fe-review-notes.md.
- The implementer of web-files-split-layout changed the download-icon test (FilesPanel.test.tsx:653-667, lookup file-preview-text to file-editor) and did not report it; the orchestrator found it and accepted it as "test no longer accurate" (housekeeping rule 2).
- Full suite round 1: web `1 failed
- The orchestrator e2e CI takes about 16 min per PR, and the container has no Docker, so the DB tests were seen only in CI.
- Harbor prunes wrapper sha7 tags, so every orchestrator deploy that needs a newer wrapper requires a wrapper release tag; this blocked deploying straight after merge.

## Recommendations

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

## Delivery record (migrated)

### Asked

Files panel with the file tree always visible on the left and a tabbed RO/RW editor on the right (terminal-style tabs, several files open at once). Read-only by default; RW edits and saves back to the agent's workspace through a new write route in claude-code-wrapper and agents-orchestrator. Syntax highlighting for python, yaml, json, terraform and toml, plus syntax checking where the language allows. No hints, no create/rename/delete, tabs not persisted across reloads.

### Shipped

14 of 14 planned tasks done across three repos. Wrapper: atomic write route `PUT /v1/sessions/{id}/files/content` with optimistic concurrency (claude-code-wrapper PR #6, merged fb005fd). Orchestrator: Origin-guarded forwarding route, fake wrapper write route, wrapper pin fb005fd with e2e case, 413 write body cap (agents-orchestrator PR #27, merged 96e46f3). Web: CodeMirror 6 editor with languages and syntax check, per-session tab state, terminal-style file tabs, split Files panel (agents-web PR #19, merged 01e971c). Superrepo pointers advanced in 1d426bfd. Epic review verdict: pass (2026-10-27), 1 fix round for the whole-epic findings (web-symlink-tab-stamps, orch-write-body-cap). Deploy: not deployed; the deploy of epics 1+3 waits on the user's answer about a wrapper release tag v0.3.1, because Harbor prunes sha7 tags.

### Tasks

Status and verified head from the task files; every verified head appears in the git log of its repo. Rounds are fix rounds. The orchestrator notes carry no per-task verification tail; the only suite lines are epic-level, below the table.

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| wrapper-file-write-route | done | d13b2a3 (claude-code-wrapper) | none noted | unknown |
| fake-wrapper-file-write | done | cf72924 (agents-orchestrator) | none noted | unknown |
| orch-file-write-route | done | 0c99a1a (agents-orchestrator) | 1 fix (origin.py docstring 0c99a1a) | unknown |
| orch-wrapper-pin-write | done | c6860bb (agents-orchestrator) | none noted | unknown |
| orch-write-body-cap | done | 1cd6f3b (agents-orchestrator) | round 2 of the epic review, clean | epic-level: orchestrator only the known lightkube env failure and Docker errors, lint clean |
| web-nomenclature-allowlist | done | 8a6d7fe (agents-web) | none noted | unknown |
| web-editor-languages | done | 0ed55f2 (agents-web) | none noted | unknown |
| web-editor-syntax-check | done | 1c3c4da (agents-web) | 2 fix (yaml check bounded to a 500 ms budget with linear duplicate-key check c9bd6a9; honest tests 1c3c4da) | unknown |
| web-code-editor | done | dd388de (agents-web) | none noted | unknown |
| web-sync-write-api | done | 45a1e37 (agents-web) | none noted | unknown |
| web-file-tabs-state | done | 92529d1 (agents-web) | 1 fix (a save did not invalidate an in-flight live refetch, 92529d1 with test) | unknown |
| web-file-tabs-view | done | 618d5da (agents-web) | none noted | unknown |
| web-files-split-layout | done | 8a20af2 (agents-web) | none noted | unknown |
| web-symlink-tab-stamps | done | 4c2690c (agents-web) | round 2 of the epic review, clean | epic-level: web 625 passed, lint clean |

Epic-level suites: round 1 web 1 failed | 622 passed (PresetForm `name_rules_default_name_and_pvc` timed out at 5086 ms against a 5 s limit under load; `src/presets` untouched; the file alone passes 45/45). Round 2 (reviewer run): web 625 passed, orchestrator only the known lightkube env failure plus Docker errors, lint clean. Wrapper and orchestrator full suites run in CI; the in-container runs are partial.

Files vs notes: the handoff text says "9 of 12 tasks done" in State; the task files show 14 done (the handoff Next section also says 14). The task files win. The epic README frontmatter still says `stage: review` although the epic is in `done/`.

### Rulings

- web-code-editor ac3 checked through `view.state.sliceDoc()`: the D11 CRLF line separator makes `doc.toString()` join with `\n` (reviewer confirmed in @codemirror/state source). Cost if wrong: a CRLF round-trip regression goes unseen by the test.
- web-code-editor ac9 "old element" means the `data-testid=file-editor` root. Cost if wrong: the AC passes against the wrong element.
- web-file-tabs-view ac8 (editor chunk) moved to web-files-split-layout ac13, because the chunk is emitted only once FilesPanel mounts FileTabs. Cost if wrong: the lazy-chunk guarantee is unchecked if the move was dropped; it is carried by an amended task.
- web-files-split-layout: the download-icon test (FilesPanel.test.tsx:653-667) changed its lookup from `file-preview-text` to `file-editor`, because the single preview is removed by design (ac10). Assertion intent unchanged. Accepted as "test no longer accurate" (housekeeping rule 2); the implementer did not report the edit. Cost if wrong: a weakened download test hides a regression where download opens a file.
- Acted: symlink tab stamps (medium) became task web-symlink-tab-stamps, including the scope-audit stampKey duplicate. Cost if dropped: symlink tabs refetch wrongly.
- Acted: orchestrator write body cap became task orch-write-body-cap. Cost if dropped: unbounded request bodies on the write route.
- Dropped: intermediate-symlink TOCTOU on write. Why: the only racer is the agent, which already has a shell; same call as the download epic. Cost if wrong: an agent writes outside its workdir through a swapped path component.
- Dropped: check-then-replace lost-update window. Why: documented in README and design, accepted. Cost if wrong: a concurrent writer's edit is overwritten silently inside the window.
- Dropped: absent Origin passes the guard. Why: browsers always send Origin on a cross-origin PUT, a JSON PUT needs a preflight, and there is no CORS middleware. Cost if wrong: a non-browser client skips the Origin check (it still needs the orchestrator auth).
- Noted, not doing now: setuid/setgid bits copied by fchmod (low; wrapper and agent share a uid in the pod). Cost if wrong: a privilege bit survives a write; no escalation across uids today.
- Noted, not doing now: wrapper-side body cap (the wrapper is reachable only from the orchestrator and the agent's pod). Cost if wrong: an in-pod caller sends an oversized body to the wrapper; the wrapper's own encode-and-cap check still refuses it before disk.

### Discovered and blocked

- Blocked: deploy of epics 1+3 waits on the user's answer about a wrapper release tag v0.3.1, because Harbor prunes sha7 tags. Cleared by the user.
- Discovered: browser saves get 403 unless the deployed orchestrator `allowed_origins` includes the UI origin. Check in the deploy epic; the deploy epic owner clears it.
- Discovered: the orchestrator write cap assumes the wrapper default `limits.file_preview_max_bytes` of 1 MiB. Check the deployed wrapper config in the deploy epic.
- Discovered: PresetForm `name_rules_default_name_and_pvc` can time out at the 5 s limit under load (passed alone, 45/45); the web test owners can clear it.
- Discovered: the pins must go together at deploy: the orchestrator needs wrapper >= 4581f3b (FileEntry.target_type is required) and, for this epic, fb005fd.

### Not pushed

Component repos: claude-code-wrapper, agents-orchestrator and agents-web have `main` equal to `origin/main`; all three PRs are merged. Superrepo `main` has 85 commits not on `origin/main` (pointer advance 1d426bfd, the move-to-done 2bfa0eb7, the retro d53b076e, plus other epics' ticket commits); the supervisor pushes it. Uncommitted files of other epics are ignored.

### Lessons routed to

- Implementer edited an existing test (download-icon lookup) and did not report it: add a check to the epic-run reviewer prompt that diffs test files changed against the base and fails when a changed pre-existing test is not named in the hand-back (a mechanical diff check, not a judgement call).
- Quadratic yaml duplicate-key check reached review: add a size-scaled timing test to web-editor-syntax-check style tasks (a large input with a time budget); a lint rule cannot catch it.
- An AC depended on a code path that only mounts in a later task (ac8 editor chunk): edit the start-development planning guidance so an AC naming a built artifact lands in the task that mounts the code (judgement call).
- Suite timeout under load (5 s default) in an untouched file: raise the vitest `testTimeout` for the suite in agents-web, or mark the test with a longer per-test timeout (mechanical).
