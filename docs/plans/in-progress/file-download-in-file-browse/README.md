---
title: file download in file browser
blockers: []
stage: build
owner: Szymon Richert
repos: [claude-code-wrapper, agents-orchestrator, agents-web]
created: 2026-10-27
---

# file download in file browser

## Project brief

What: Download icon on each file row of the Files tree that saves the workspace file to the user's computer
How: raw-bytes download route in claude-code-wrapper, streamed through an orchestrator route, right-aligned icon in FilesPanel
Why: Users can take any file, text or binary, out of an agent's workspace

## Description

User request (2026-10-27), verbatim:

"## file download

In file browser, I need to be able to download a file. I expect small "arrow down" icon aligned with right side of the file browser, that's going to download a file to my computer from agent's workspace."

Implementation order given by the user: 1. download, 2. markdown, 3. editor.

## Goals

- A small download (arrow down) icon on every file row of the Files tree, aligned to the right edge of the file browser.
- Clicking it downloads that file from the agent's workspace to the user's computer, byte-exact, for text and binary files of any size (no 1 MiB preview cap).
- New raw-bytes download route in claude-code-wrapper and an orchestrator route forwarding it, with the existing workspace path guards.

## Non-goals

- No directory or multi-file (archive) download.
- No upload.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
