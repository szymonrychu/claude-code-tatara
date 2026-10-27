# file editor with tabs and highlighting record

## Asked

Files panel with the file tree always visible on the left and a tabbed RO/RW editor on the right (terminal-style tabs, several files open at once). Read-only by default; RW edits and saves back to the agent's workspace through a new write route in claude-code-wrapper and agents-orchestrator. Syntax highlighting for python, yaml, json, terraform and toml, plus syntax checking where the language allows. No hints, no create/rename/delete, tabs not persisted across reloads.

## Shipped

14 of 14 planned tasks done across three repos. Wrapper: atomic write route `PUT /v1/sessions/{id}/files/content` with optimistic concurrency (claude-code-wrapper PR #6, merged fb005fd). Orchestrator: Origin-guarded forwarding route, fake wrapper write route, wrapper pin fb005fd with e2e case, 413 write body cap (agents-orchestrator PR #27, merged 96e46f3). Web: CodeMirror 6 editor with languages and syntax check, per-session tab state, terminal-style file tabs, split Files panel (agents-web PR #19, merged 01e971c). Superrepo pointers advanced in 1d426bfd. Epic review verdict: pass (2026-10-27), 1 fix round for the whole-epic findings (web-symlink-tab-stamps, orch-write-body-cap). Deploy: not deployed; the deploy of epics 1+3 waits on the user's answer about a wrapper release tag v0.3.1, because Harbor prunes sha7 tags.

## Tasks

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

## Rulings

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

## Discovered and blocked

- Blocked: deploy of epics 1+3 waits on the user's answer about a wrapper release tag v0.3.1, because Harbor prunes sha7 tags. Cleared by the user.
- Discovered: browser saves get 403 unless the deployed orchestrator `allowed_origins` includes the UI origin. Check in the deploy epic; the deploy epic owner clears it.
- Discovered: the orchestrator write cap assumes the wrapper default `limits.file_preview_max_bytes` of 1 MiB. Check the deployed wrapper config in the deploy epic.
- Discovered: PresetForm `name_rules_default_name_and_pvc` can time out at the 5 s limit under load (passed alone, 45/45); the web test owners can clear it.
- Discovered: the pins must go together at deploy: the orchestrator needs wrapper >= 4581f3b (FileEntry.target_type is required) and, for this epic, fb005fd.

## Not pushed

Component repos: claude-code-wrapper, agents-orchestrator and agents-web have `main` equal to `origin/main`; all three PRs are merged. Superrepo `main` has 85 commits not on `origin/main` (pointer advance 1d426bfd, the move-to-done 2bfa0eb7, the retro d53b076e, plus other epics' ticket commits); the supervisor pushes it. Uncommitted files of other epics are ignored.

## Lessons routed to

- Implementer edited an existing test (download-icon lookup) and did not report it: add a check to the epic-run reviewer prompt that diffs test files changed against the base and fails when a changed pre-existing test is not named in the hand-back (a mechanical diff check, not a judgement call).
- Quadratic yaml duplicate-key check reached review: add a size-scaled timing test to web-editor-syntax-check style tasks (a large input with a time budget); a lint rule cannot catch it.
- An AC depended on a code path that only mounts in a later task (ac8 editor chunk): edit the start-development planning guidance so an AC naming a built artifact lands in the task that mounts the code (judgement call).
- Suite timeout under load (5 s default) in an untouched file: raise the vitest `testTimeout` for the suite in agents-web, or mark the test with a longer per-test timeout (mechanical).
