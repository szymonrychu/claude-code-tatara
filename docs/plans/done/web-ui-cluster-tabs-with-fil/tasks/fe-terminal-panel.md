---
title: fe terminal panel
status: done
repo: agent-orchestrator
value: the user runs several shells on chosen agent pods beside the chat
files: [frontend/src/terminal/XtermView.tsx, frontend/src/terminal/TerminalPanel.tsx, frontend/src/terminal/TerminalPanel.test.tsx, frontend/src/theme.ts, frontend/src/App.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal src/App.test.tsx src/theme.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-terminal-socket, fe-filesystem-panel, fe-panel-workspace]
owns: []
uses: [fe-terminal-socket, fe-workspace-slots, fe-deps]
model: ""
estimate: 6
estimate_by: formula
actual: 12
actual_roles: "impl 4, verify 5, review 2, fix 1, land 1"
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/web-ui-cluster-tabs-with-fil-fe-terminal-panel/agent-orchestrator
branch: web-ui-cluster-tabs-with-fil-fe-terminal-panel
verified_head: 25e24cc32aab9be6397016de55a79f03c29723dc
run: web-ui-cluster-tabs-with-fil
provides: []
acs_for_audit: []
process_gaps: []
fork_point: 236c3348fbf3ac753a56d3efb83a547ea82e8024
---

# fe terminal panel

## Requirement

The terminal panel (user Q4, Q5), test-first.

- New `frontend/src/terminal/XtermView.tsx`: one `@xterm/xterm` 6 `Terminal` with `@xterm/addon-fit`, colours from a `terminalTheme` exported by `frontend/src/theme.ts` (the only place colour literals may live); `fit()` on mount and whenever its container resizes (ResizeObserver; this covers panel drags, minimize and maximize), sending the new size through the socket's `resize`; keyboard input goes to `send`; socket data goes to `write`; on each reconnect after the first it calls `reset()` before the replay; on `exit` it prints a one-line notice and leaves the tab open.
- New `frontend/src/terminal/TerminalPanel.tsx`: `TerminalPanel({cluster, agents})` with MUI `Tabs` (one tab per shell, label pod name plus a short id) and a "New terminal" button that opens a menu of the cluster's agents with the first ready agent (by ordinal) preselected; choosing one calls `createTerminal` and opens a tab. On mount and on cluster change it calls `listTerminals(cluster.id)` and opens a tab per existing shell (so shells survive tab switches and reloads, user Q5). Closing a tab calls `deleteTerminal`. Switching tabs keeps the other shells attached or reattaches them (replay restores the screen). Empty state: "No terminals" with the New terminal button. Errors (for example `terminal_limit`, `forbidden_origin`, `agent_not_ready`) show inline.
- `frontend/src/App.tsx` passes `TerminalPanel` into the workspace `terminal` slot.

## Acceptance conditions

- AC1: existing shells of the cluster open as tabs on mount [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t reattaches_existing_shells]
- AC2: New terminal preselects the first ready agent and creates a shell on the chosen agent [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t new_terminal_on_chosen_agent]
- AC3: several shells live as tabs and closing a tab deletes its shell [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t multiple_tabs_and_close]
- AC4: the view fits on container resize and sends the size, and resets before a reconnect replay [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t fit_on_resize_and_reset_on_reconnect]
- AC5: API errors render inline [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t errors_inline]
- AC6: terminal colours live in theme.ts and design rules pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/theme.test.ts src/layout/designRules.test.ts]
- AC7: tests, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal src/App.test.tsx src/theme.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC8: only alive shells from listTerminals reopen as tabs on mount [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t reopens_only_alive_shells]
- AC9: a refused tab stays with its reason, a Retry button that reconnects and a Close button [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t refused_tab_retry_and_close]
- AC10: unmounting closes the sockets without deleting the shells and remounting reattaches with scrollback replay [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/terminal/TerminalPanel.test.tsx -t remount_reattaches_with_replay]

## Files

- `frontend/src/terminal/XtermView.tsx`
- `frontend/src/terminal/TerminalPanel.tsx`
- `frontend/src/terminal/TerminalPanel.test.tsx`
- `frontend/src/theme.ts`
- `frontend/src/App.tsx`

## Interfaces

- Uses `openTerminalSocket` (part `fe-terminal-socket`), `api/terminals.ts`, the `terminal` slot (part `fe-workspace-slots`), `@xterm/xterm` 6 and `@xterm/addon-fit` 0.11 (part `fe-deps`).
- `frontend/src/theme.ts`: new export `terminalTheme` (xterm `ITheme`).

## Expected outcome

The right panel runs several interactive shells on chosen agent pods, sized to the panel, surviving tab switches and reloads.

## Steps

- Write `frontend/src/terminal/TerminalPanel.test.tsx` (jsdom; `vi.mock('@xterm/xterm')`, `vi.mock('@xterm/addon-fit')`, `vi.mock('../api/terminals')`, `vi.mock('./terminalSocket')`, a stub `ResizeObserver`; titles as in the AC refs); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/TerminalPanel.test.tsx`: fails.
- Implement `XtermView.tsx`, `TerminalPanel.tsx`, `terminalTheme`, wire the slot; run the verify command: passes.

## Notes

- xterm 6 removed the canvas renderer addon and reworked the viewport; use the default DOM renderer and import `@xterm/xterm/css/xterm.css` once.
- jsdom has no canvas, no ResizeObserver and no WebSocket: mock them; the real rendering is checked by the user in a browser after deploy.
- A colour literal outside `theme.ts` fails `designRules.test.ts`.
- Builder check ruling 1: Attaching to an exited shell replays the scrollback, sends the exit control frame, then closes 1000. The panel reopens tabs on mount only for alive shells from listTerminals.
- Builder check ruling 6: Reconnect on 1006, 1011, 1013 and 4409 with exponential backoff 1 s to 30 s, at most 10 attempts, then state refused; never reconnect on 1000, 1003, 1008, 1009. A refused tab stays with the reason, a Retry and a Close button.
- Builder check ruling 9: Only the active cluster tab's Workspace is mounted; switching away unmounts it and terminals reattach with scrollback replay on return. A minimized panel stays mounted, so its event subscription stays live.

- 2026-10-23 amended: builder check rulings 1,6,9 add acceptance conditions AC8-AC10
