---
title: workspace ui fixes
blockers: []
stage: review
owner: Szymon Richert
repos: [agent-orchestrator]
created: 2026-10-24
---

# workspace ui fixes

## Project brief

What: Vertical dividers between the files, chat and terminal panes; the file tree updates live
How: pane divider styling, live file-tree updates pushed from the backend replacing the refresh button
Why: The workspace layout reads clearly and the tree never shows stale files

## Description

User request (2026-10-24), verbatim:

"UI fixes:
* missing vertical divider lines between files/chat/terminal
* files tree is not automatically updating (refresh button is not acceptable)"

## Goals

- Visible vertical dividers between files, chat and terminal.
- File tree updates itself (agents, terminals, new directories, notebooks); no refresh button.

## Non-goals

- No wrapper inotify, no new endpoint or event type.
- No phone layout change.

## Time

Estimate: 15 agent-min | Critical path: 10 min | Expected wall at P=1.5: 0.3 h (k=2.0) | Actual: 10 min | Remaining estimate: 0 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
