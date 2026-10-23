---
title: fe terminal socket
status: todo
repo: agent-orchestrator
value: the browser keeps shell connections alive and reconnects them with replay
files: [frontend/src/api/terminals.ts, frontend/src/terminal/terminalSocket.ts, frontend/src/terminal/terminalSocket.test.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/terminalSocket.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [terminal-ws-relay, fe-deps-and-storage]
owns: [fe-terminal-socket]
uses: [orch-terminals-api, orch-terminal-ws, fe-deps]
model: ""
estimate: 5
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

# fe terminal socket

## Requirement

The browser side of the terminal protocol (design D2; user Q5), test-first, with no UI yet.

- New `frontend/src/api/terminals.ts`: `createTerminal(agentId, {rows, cols})`, `listTerminals(clusterId)`, `deleteTerminal(agentId, terminalId)` over `request` with the generated `TerminalView`/`TerminalList` types, and `terminalSocketUrl(agentId, terminalId)` that builds `ws://` or `wss://` (matching `location.protocol`) on `location.host` plus `/api/v1/agents/{agent_id}/terminals/{terminal_id}/attach`.
- New `frontend/src/terminal/terminalSocket.ts`: `openTerminalSocket(url, {onData(bytes: Uint8Array), onExit(code), onStatus(status), WebSocketImpl?})` returning `{send(data: string | Uint8Array), resize(cols, rows), close()}`. Binary type `arraybuffer`; incoming binary frames go to `onData` (the first ones are the replay); incoming text frames are JSON control (`pong` ignored, `exit` calls `onExit` and stops); `send` encodes strings as UTF-8 binary frames; `resize` sends `{"type":"resize","cols","rows"}` and remembers the size to resend after a reconnect; a `{"type":"ping"}` every 20 s while open. Reconnect on an abnormal close (not 1000, not after `exit`, not after `close()`, not on 4404 or 1008) with backoff from 1 s doubling to 30 s; a reconnect receives the replay again, so the caller resets its screen on each `onStatus('open')` after the first. `onStatus` reports `connecting`, `open`, `reconnecting`, `closed`, `refused`.

## Acceptance conditions

- AC1: binary frames reach onData and strings are sent as UTF-8 binary frames [evidence: test:frontend/src/terminal/terminalSocket.test.ts::bytes_in_and_out]
- AC2: resize sends the control frame and is resent after a reconnect [evidence: test:frontend/src/terminal/terminalSocket.test.ts::resize_and_resend]
- AC3: a ping is sent every 20 s while open [evidence: test:frontend/src/terminal/terminalSocket.test.ts::ping_every_20s]
- AC4: abnormal closes reconnect with 1 to 30 s backoff, while 1000, exit, close(), 4404 and 1008 do not [evidence: test:frontend/src/terminal/terminalSocket.test.ts::reconnect_policy]
- AC5: the exit frame calls onExit with the code [evidence: test:frontend/src/terminal/terminalSocket.test.ts::exit_frame]
- AC6: the socket URL follows the page protocol and host [evidence: test:frontend/src/terminal/terminalSocket.test.ts::socket_url_from_location]
- AC7: tests, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/terminalSocket.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/api/terminals.ts`
- `frontend/src/terminal/terminalSocket.ts`
- `frontend/src/terminal/terminalSocket.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
