---
title: fe terminal panel
status: todo
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
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# fe terminal panel

## Requirement

The terminal panel (user Q4, Q5), test-first.

- New `frontend/src/terminal/XtermView.tsx`: one `@xterm/xterm` 6 `Terminal` with `@xterm/addon-fit`, colours from a `terminalTheme` exported by `frontend/src/theme.ts` (the only place colour literals may live); `fit()` on mount and whenever its container resizes (ResizeObserver; this covers panel drags, minimize and maximize), sending the new size through the socket's `resize`; keyboard input goes to `send`; socket data goes to `write`; on each reconnect after the first it calls `reset()` before the replay; on `exit` it prints a one-line notice and leaves the tab open.
- New `frontend/src/terminal/TerminalPanel.tsx`: `TerminalPanel({cluster, agents})` with MUI `Tabs` (one tab per shell, label pod name plus a short id) and a "New terminal" button that opens a menu of the cluster's agents with the first ready agent (by ordinal) preselected; choosing one calls `createTerminal` and opens a tab. On mount and on cluster change it calls `listTerminals(cluster.id)` and opens a tab per existing shell (so shells survive tab switches and reloads, user Q5). Closing a tab calls `deleteTerminal`. Switching tabs keeps the other shells attached or reattaches them (replay restores the screen). Empty state: "No terminals" with the New terminal button. Errors (for example `terminal_limit`, `forbidden_origin`, `agent_not_ready`) show inline.
- `frontend/src/App.tsx` passes `TerminalPanel` into the workspace `terminal` slot.

## Acceptance conditions

- AC1: existing shells of the cluster open as tabs on mount [evidence: test:frontend/src/terminal/TerminalPanel.test.tsx::reattaches_existing_shells]
- AC2: New terminal preselects the first ready agent and creates a shell on the chosen agent [evidence: test:frontend/src/terminal/TerminalPanel.test.tsx::new_terminal_on_chosen_agent]
- AC3: several shells live as tabs and closing a tab deletes its shell [evidence: test:frontend/src/terminal/TerminalPanel.test.tsx::multiple_tabs_and_close]
- AC4: the view fits on container resize and sends the size, and resets before a reconnect replay [evidence: test:frontend/src/terminal/TerminalPanel.test.tsx::fit_on_resize_and_reset_on_reconnect]
- AC5: API errors render inline [evidence: test:frontend/src/terminal/TerminalPanel.test.tsx::errors_inline]
- AC6: terminal colours live in theme.ts and design rules pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/theme.test.ts src/layout/designRules.test.ts]
- AC7: tests, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal src/App.test.tsx src/theme.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/terminal/XtermView.tsx`
- `frontend/src/terminal/TerminalPanel.tsx`
- `frontend/src/terminal/TerminalPanel.test.tsx`
- `frontend/src/theme.ts`
- `frontend/src/App.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
