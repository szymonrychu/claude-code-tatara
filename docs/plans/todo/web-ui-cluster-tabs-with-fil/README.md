---
title: web ui cluster tabs with filesystem chat and terminal panels
blockers: [cluster-form-defaults-and-ga]
stage: build
owner: ""
repos: [agent-orchestrator, claude-code-wrapper, agents-helmfile]
created: 2026-10-23
---

# web ui cluster tabs with filesystem chat and terminal panels

## Project brief

What: Replace the left cluster ribbon with top tabs; each cluster tab is a three-panel workspace (filesystem tree, chat, multi-tab terminal) with resizable separators and minimize/maximize
How: react-resizable-panels for the panels, MUI Tabs for clusters and terminals, xterm.js over a WebSocket PTY served by the wrapper and proxied by the orchestrator api, MUI X SimpleTreeView over a lazy wrapper file-tree API on the shared RWX workdir
Why: One screen per cluster that shows what the agents changed on disk, lets the user run commands beside the chat, and scales past a handful of clusters better than a side ribbon

## Description

User request (2026-10-23), verbatim:

"Next epic concering webUI:
1. instead of left ribbon, lets switch to tabs (each session is a tab presented at the upper side of the screen)
2. session consist of 3 panels, separators allow to change their sizing horizontally, there is a minimize button that allows to minimize two out of three at a time and maximize one of them:
  1. filesystem
  2. chat
  3. terminal
3. chat stays as is, terminal allows for scheduling multiple tabs, filesystem shows everything in tree view (same as vscode)"

The "left ribbon" is the agent-orchestrator frontend aside (frontend/src/layout/Shell.tsx, frontend/src/ribbon/Ribbon.tsx). A "session" in this request is one orchestrator cluster: the unit the ribbon lists, the chat shows and the shared RWX workdir belongs to. The wrapper has no web UI of its own.

Research findings with citations are in research.md next to this README.

## Goals

- The left ribbon is replaced by a top tab bar: one tab per open cluster, with its state mark, slug and context gauge; New cluster, edit and discard stay reachable from the tab bar.
- A cluster tab shows three panels side by side, filesystem, chat and terminal, split by draggable separators (horizontal resizing).
- Each panel has minimize and maximize controls: at most two panels are minimized at once, maximize minimizes the other two, a minimized panel stays as a narrow labelled strip that restores it; the layout persists per cluster in the browser.
- The chat panel is the existing ChatView unchanged (log, agent filter, queue strip, composer).
- The terminal panel holds several terminal tabs, each an interactive shell in the cluster workdir on a chosen agent pod, over a WebSocket PTY, rendered with xterm.js.
- The filesystem panel shows the cluster's shared workdir as a lazily loaded tree (VS Code explorer style), refreshed when the event stream shows a write, with a read-only file preview.
- New backend surface, test-first: a wrapper file-tree and file-read API and a wrapper terminal WebSocket API, and orchestrator /api/v1 proxies for both, with Origin checks, path confinement, size caps and terminal caps.
- Deployed: wrapper image, orchestrator image and chart bumped in agents-helmfile, applied, smoke OK on the LAN.

## Non-goals

- No authentication or user accounts: the UI stays unauthenticated and LAN-only (ORCH_ALLOWED_CIDRS plus ingress source ranges). Adding auth is a separate epic if wanted.
- No file editing, upload, rename or delete in the filesystem panel (read-only tree and preview).
- No attaching a human keyboard to the Claude TUI PTY: terminals are separate shells.
- No change to chat behaviour or to dispatch.
- No Kubernetes pods/exec RBAC for the orchestrator.

## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
