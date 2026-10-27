---
title: file download in file browser
blockers: []
stage: review
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

Verdict: pass (2026-10-27)

# file-download-in-file-browse epic review notes

- Whole-epic review (start-review --single, sonnet): clean, no findings. Cross-repo seams consistent (headers, error map, fake vs real, target_type).
- Scope audit (sonnet): complete, no gaps, no new tasks. Fake duplicates three wrapper helpers by design (task note), pinned by the contract suite.
- Security (sonnet): no critical/high/medium. Dropped LOW 1 (intermediate-symlink TOCTOU in resolve_in_workdir): pre-existing, shared with read_preview, exploitable only by the agent that already has a shell in the same container. Dropped LOW 2 (no concurrent-download cap): same posture as the existing file routes, behind ingress auth; outside this epic's scope.
- Full suites, this container:
  - agents-web: `Tests  515 passed (515)`, lint clean (.logs/fdl-web-full.log).
  - agents-orchestrator: `1 failed, 571 passed, 59 deselected, 1 warning, 525 errors`; the 525 errors are testcontainers without Docker; the 1 failure (test_reconciler.py::test_lightkube_default_client_uses_env_config) fails identically on main 90f3ce3 (in-cluster KUBERNETES_SERVICE_HOST env). CI runs the full suite (.logs/fdl-orch-full.log).
  - claude-code-wrapper (implementer run on 7f7cd15): `3 failed, 1682 passed, 26 deselected`; the 3 process-group tests fail identically on main ee10aa8 (no PID 1 reaper); PR #5 CI green (unit, integration, build-push), merged 4581f3b.
- Deploy coupling: orchestrator FileEntry.target_type is required, so the orchestrator image must deploy with wrapper >= 4581f3b (for the later deploy epic).
