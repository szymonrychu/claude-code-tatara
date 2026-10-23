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

- The left ribbon is replaced by a top tab bar: one tab per open cluster, with its state mark, slug and context gauge; New cluster and discard stay reachable from the tab bar. Live cluster edit is not carried over (user, 2026-10-23: "Live session edit is not needed"); its API removal belongs to the presets epic.
- A hamburger button at the top left opens a menu listing every session (cluster) tab from the top and the settings categories from the bottom; this epic builds the menu and its sessions list, and the settings area shows the categories that exist (the presets epic adds Presets, the only one planned).
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

## Scope

In scope, per repo:

- claude-code-wrapper: a session-scoped file API (list one directory, read one file) confined to the session workdir, and a session-scoped terminal API (create, list, attach over WebSocket, close) that runs a login shell under a PTY in the workdir. Bearer auth as every `/v1` route; caps on terminals, frame size, file size and directory entries.
- agent-orchestrator backend: `/api/v1` proxies for both (the api already holds `ORCH_MASTER_KEY` through the shared chart env and can derive each cluster's wrapper token with `tokens_for`), an Origin allowlist for WebSocket upgrades, OpenAPI and `schema.d.ts` regenerated.
- agent-orchestrator frontend: cluster tab bar replacing `Shell` aside and `Ribbon`, the three-panel workspace, the filesystem panel, the terminal panel; ChatView reused unchanged.
- agent-orchestrator chart: documented ingress WebSocket timeouts, the new `ORCH_*` settings.
- agents-helmfile: version bumps, apply, smoke.

## Related epics and order

Order: cluster-form-defaults-and-ga (in progress), then this epic, then presets-for-cluster-scheduling (adds the Presets settings category to this epic's hamburger menu, removes live edit from the API, makes New cluster take a preset), then hive-mode-leadership-handove (its leader badge lands in this epic's tabs and agents strip).

## How (sketch, decided in design)

- Layout: `react-resizable-panels` 4.x `Group` (horizontal) with three `Panel`s (`collapsible`, a small pixel `collapsedSize`) and two `Separator`s. Minimize calls `panelRef.collapse()`, maximize collapses the other two, restore calls `expand()`; a rule keeps at least one panel expanded. `onLayoutChanged` persists the layout per cluster in localStorage (wrapped in try/catch, the page works without it).
- Cluster tabs: MUI `Tabs` (`variant="scrollable"`) in the top bar, one tab per cluster from the existing `useClusters` store (its `selectedId` becomes the active tab), each tab label carrying `StateMark`, slug and `ContextGauge`; a New cluster button and a per-tab actions menu (Edit, Discard) replace the ribbon controls (the Edit item is dropped). A hamburger `IconButton` at the top left opens a MUI `Drawer` whose list holds the sessions from the top and a settings section pinned to the bottom. Agent rows (pod, state, free since, gauge) move into the chat panel header beside `AgentFilter`.
- Filesystem: MUI X `SimpleTreeView` (MIT) with lazy children fetched on expand from `GET /api/v1/clusters/{id}/files?path=`; directories touched by `tool_call` events (Write, Edit, NotebookEdit `file_path`) or by any finished Bash `tool_result` are re-fetched when expanded; a read-only preview pane for text files.
- Terminal: MUI `Tabs` inside the panel, one `@xterm/xterm` 6 instance per tab with `@xterm/addon-fit` (re-fit on panel resize), a small WebSocket protocol (binary frames are PTY bytes, text frames are JSON control such as `{"type":"resize","cols":..,"rows":..}`), app-level ping every 20 s, reconnect with scrollback replay.
- Wrapper side: reuse `PtyProcess` and its ring (`pty_proc.py`) for shells; file API resolves every path and refuses anything that leaves the workdir after symlink resolution.

## Decisions (user, 2026-10-23)

- Q1: yes, one cluster is one tab.
- Q3: a shell in an agent pod; the user does not know how, so the mechanism is decided in design (recommended: served by the wrapper, proxied by the orchestrator api).
- Q7: yes, unauthenticated LAN-only shell with the mandatory Origin allowlist.
- From the presets message: live cluster edit is not needed (supports Q15: yes).

## Open questions

- Q1: Is a "session" in the request one orchestrator cluster, with every cluster shown as a tab (no closing, scrollable bar, ordered by slug)? [recommended: yes, a tab per cluster, same set the ribbon lists today]
- Q2: Where do the per-agent rows (pod, state, free since, own gauge) go once the ribbon is gone? [recommended: a compact agents strip in the chat panel header, merged with the agent filter chips]
- Q3: Where does a terminal run? [recommended: a shell in a chosen agent pod, served by the wrapper and proxied by the orchestrator api; not a separate workspace pod, not Kubernetes pods/exec]
- Q4: Does "terminal allows for scheduling multiple tabs" mean several concurrent terminal tabs, rather than queued or scheduled commands? [recommended: yes, several concurrent shells as tabs, each with its own pod choice]
- Q5: How long does a shell live? [recommended: survives tab switches and page reloads, reaped 15 minutes after its last client detaches, 256 KiB scrollback replayed on reattach, at most 8 shells per pod]
- Q6: Does the shell environment drop the wrapper and Claude secrets (CCW_AUTH_TOKEN, CCW_PEER_TOKEN, CCW_HOOK_TOKEN, CLAUDE_CODE_OAUTH_TOKEN)? [recommended: yes, as defence in depth only; the same uid can still read them from /proc, which the wrapper trust model already accepts]
- Q7: Is an unauthenticated, LAN-only interactive shell acceptable, given that a chat prompt can already run arbitrary commands in the pod? [recommended: yes, with a mandatory Origin allowlist on every WebSocket upgrade (ORCH_ALLOWED_ORIGINS) and the existing source allowlist; authentication stays a separate epic]
- Q8: Does "shows everything" include dotfiles and .git? [recommended: yes, everything, loaded lazily per directory, at most 2000 entries per directory with a "more" row]
- Q9: What does clicking a file do? [recommended: a read-only preview inside the filesystem panel, text only up to 1 MiB, binary files shown as size and type]
- Q10: How does the tree stay current? [recommended: re-fetch directories touched by the cluster event stream plus a manual refresh button; no inotify, which does not see writes from other CephFS clients]
- Q11: What does a minimized panel look like? [recommended: a narrow vertical strip with the panel name and a restore button; double-click on a separator restores the default 25/45/30 split]
- Q12: Phone layout? [recommended: one panel at a time with a three-way switch (a forced maximize), the cluster tabs scroll]
- Q13: Add `@mui/icons-material` 9.5.0 for minimize, maximize, folder and file icons? [recommended: yes, SVG icons pass designRules.ts, which only bans glyph Unicode]
- Q14: Does this epic build the hamburger menu (sessions from the top, a settings section at the bottom that stays empty until the presets epic adds Presets)? [recommended: yes, the top bar is designed once here; the presets epic only adds its category and page]
- Q15: Drop the cluster Edit action from the UI in this epic, before the presets epic removes the PATCH route? [recommended: yes, the user said live edit is not needed, so the tab actions carry only Discard]

## Risks

- Security: an interactive shell and a file reader on an unauthenticated UI. A WebSocket upgrade is not subject to CORS, so without an Origin check any web page open in a LAN browser can attach to a shell (cross-site WebSocket hijacking). The existing `AllowlistMiddleware` already closes disallowed WebSocket peers (api/allowlist.py:35-49) but sees only the direct peer, not the browser origin.
- Agent pods inside the cluster can reach the ingress hostname (README `## Security`); the new routes widen what a pod could do through it unless `ingress.denySourceRanges` is set as documented.
- ingress-nginx closes idle proxied connections after 60 s by default; long-lived terminals need app-level pings and raised `proxy-read-timeout` / `proxy-send-timeout`.
- MUI X lazy loading and virtualization are Pro features; the MIT tree needs hand-rolled lazy loading and entry caps, and very large directories (node_modules) stay slow.
- Shells in agent pods share CPU and memory with Claude; a runaway command can starve the agent.
- xterm.js 6 removed the canvas renderer and changed scrolling; many online examples target 5.x.
- react-resizable-panels 4 renamed its components (`Group`, `Panel`, `Separator`); older examples use `PanelGroup` / `PanelResizeHandle`.
- Retiring the ribbon retires `Ribbon.test.tsx` and parts of `Shell`; the in-progress epic cluster-form-defaults-and-ga edits `ContextGauge`, hence the blocker.

## Rough task list

1. wrapper: file API (list directory, read file) with path confinement, caps and tests.
2. wrapper: terminal API (create, list, WebSocket attach with the control protocol, close, reaper, caps, env scrub, scrollback ring) and tests.
3. wrapper: README sections and a release with the new image.
4. orchestrator api: file proxies and terminal proxies (HTTP plus WebSocket relay to the chosen pod), Origin allowlist setting, OpenAPI and schema.d.ts regen.
5. orchestrator chart: ingress WebSocket timeouts documented, new settings wired.
6. frontend: dependencies (react-resizable-panels, @xterm/xterm, @xterm/addon-fit, @mui/x-tree-view, optionally @mui/icons-material).
7. frontend: cluster tab bar and actions replacing Shell aside and Ribbon (retirement tests for the ribbon), hamburger menu with the sessions list and the settings section, phone behaviour.
8. frontend: three-panel workspace with minimize and maximize rules and persisted layout.
9. frontend: filesystem panel (lazy tree, event-driven refresh, preview).
10. frontend: terminal panel (tabs, xterm, protocol, fit on resize, reconnect).
11. e2e: kind test that lists the workdir and runs a shell command through the orchestrator proxy.
12. agents-helmfile: bump wrapper image and chart, apply, smoke from a LAN browser.

## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
