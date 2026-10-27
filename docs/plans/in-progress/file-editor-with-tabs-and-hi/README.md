---
title: file editor with tabs and highlighting
blockers: [file-download-in-file-browse, markdown-rendering-in-chat]
stage: review
owner: Szymon Richert
repos: [claude-code-wrapper, agents-orchestrator, agents-web]
created: 2026-10-27
---

# file editor with tabs and highlighting

## Project brief

What: Files panel with an always-visible tree on the left and a tabbed RO/RW editor with syntax highlighting and checking
How: CodeMirror 6 editor, terminal-style tabs, new write route in wrapper and orchestrator
Why: Users can read and edit several workspace files side by side without leaving the UI

## Description

User request (2026-10-27), verbatim:

"## file open

* inside "Files" in RW editor mode- support python/yaml/json/terraform/toml syntax highlighting and syntax- no hints for now
* file tree always visible on the left
* multiple files can be opened- similar design to tabs in terminal"

Discovery (2026-10-27): no RW editor mode, editor library or file-write API exists today; the Files panel shows one read-only preview below the tree.

## Goals

- Files panel: file tree always visible on the left, editor area on the right.
- Multiple files open at once as tabs, styled like the terminal tabs (closable, scrollable).
- RO/RW editor mode: read-only by default, RW lets the user edit and save the file back to the agent's workspace (new write route in claude-code-wrapper and orchestrator).
- Syntax highlighting for python, yaml, json, terraform and toml, plus syntax checking (errors marked) where the language allows.

## Non-goals

- No hints: no autocomplete, hover info or language-server features.
- No file create, rename or delete.
- Open tabs are not persisted across page reloads.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-27)

- web-code-editor: ac3 checked through view.state.sliceDoc() (D11 CRLF separator makes doc.toString() join with \n; reviewer confirmed in @codemirror/state source); ac9 'old element' = data-testid=file-editor root. Orchestrator rulings, reviewer-confirmed.
- web-file-tabs-state: 1 fix round (save did not invalidate an in-flight live refetch; fixed 92529d1 with test).
- web-editor-syntax-check: 2 fix rounds (quadratic yaml duplicate-key check -> cooperative 500 ms budget + linear dup check c9bd6a9; honest tests 1c3c4da). orch-file-write-route: 1 fix round (origin.py docstring 0c99a1a).
- web-file-tabs-view: ac8 moved to web-files-split-layout ac13 (chunk only emitted once FilesPanel mounts FileTabs).
- web-files-split-layout: the download-icon test (FilesPanel.test.tsx:653-667) changed its lookup from file-preview-text to file-editor because the single preview is removed by design (ac10); assertion intent unchanged (download opens nothing, name click opens the file). Accepted as 'test no longer accurate' (housekeeping rule 2); the implementer did not report it.
- Epic review round 1: whole-epic reviewer accept with 1 medium (symlink tab stamps) -> task web-symlink-tab-stamps (with the scope-audit stampKey duplicate). Security: 3 medium, 2 low; acted: orchestrator write body cap -> task orch-write-body-cap; dropped: intermediate-symlink TOCTOU on write (agent-only racer, already has a shell; same as download epic), check-then-replace lost-update window (documented in README/design, accepted), setuid/setgid copied by fchmod (low; wrapper and agent share a uid in the pod; noted, not doing now), absent Origin passes the guard (browsers always send Origin on cross-origin PUT; JSON PUT needs preflight, no CORS middleware). Wrapper-side body cap: noted, not doing now (wrapper reachable only from the orchestrator and the agent's pod).
- Deploy note: browser saves get 403 unless the deployed orchestrator allowed_origins includes the UI origin; check in the deploy epic.
- Full suites round 1: web 1 failed | 622 passed: PresetForm name_rules_default_name_and_pvc timed out at 5086 ms (5 s limit) under load; src/presets untouched by this epic; the file alone passes 45/45. Orchestrator: only the known lightkube env failure plus Docker errors; lint clean.
- Round 2: web-symlink-tab-stamps (4c2690c) and orch-write-body-cap (1cd6f3b) reviewed clean; full suites after them (reviewer run): web 625 passed, orchestrator only the known lightkube env failure and Docker errors, lint clean. Deploy note: the orchestrator write cap assumes the wrapper default limits.file_preview_max_bytes 1 MiB.
