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
