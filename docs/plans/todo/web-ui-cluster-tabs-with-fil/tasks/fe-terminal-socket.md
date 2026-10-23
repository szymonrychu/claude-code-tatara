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
- New `frontend/src/terminal/terminalSocket.ts`: `openTerminalSocket(url, {onData(bytes: Uint8Array), onExit(code), onStatus(status), WebSocketImpl?})` returning `{send(data: string | Uint8Array), resize(cols, rows), close()}`. Binary type `arraybuffer`; incoming binary frames go to `onData` (the first ones are the replay); incoming text frames are JSON control (`pong` ignored, `exit` calls `onExit` and stops); `send` encodes strings as UTF-8 binary frames and splits any input longer than `MAX_FRAME_BYTES` (65536, the wrapper default `terminal_max_frame_bytes`) into consecutive frames of at most that many bytes in order, so a large paste is never one oversized frame that the wrapper would close with 1009; `resize` sends `{"type":"resize","cols","rows"}` and remembers the size to resend after a reconnect; a `{"type":"ping"}` every 20 s while open. Reconnect on an abnormal close (not 1000, not after `exit`, not after `close()`, not on 4404 or 1008) with backoff from 1 s doubling to 30 s; a reconnect receives the replay again, so the caller resets its screen on each `onStatus('open')` after the first. `onStatus` reports `connecting`, `open`, `reconnecting`, `closed`, `refused`.

## Acceptance conditions

- AC1: binary frames reach onData and strings are sent as UTF-8 binary frames [evidence: test:frontend/src/terminal/terminalSocket.test.ts::bytes_in_and_out]
- AC2: resize sends the control frame and is resent after a reconnect [evidence: test:frontend/src/terminal/terminalSocket.test.ts::resize_and_resend]
- AC3: a ping is sent every 20 s while open [evidence: test:frontend/src/terminal/terminalSocket.test.ts::ping_every_20s]
- AC4: abnormal closes reconnect with 1 to 30 s backoff, while 1000, exit, close(), 4404 and 1008 do not [evidence: test:frontend/src/terminal/terminalSocket.test.ts::reconnect_policy]
- AC5: the exit frame calls onExit with the code [evidence: test:frontend/src/terminal/terminalSocket.test.ts::exit_frame]
- AC6: the socket URL follows the page protocol and host [evidence: test:frontend/src/terminal/terminalSocket.test.ts::socket_url_from_location]
- AC7: tests, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/terminalSocket.test.ts src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC8: close codes 1006, 1011, 1013 and 4409 reconnect and 1000, 1003, 1008 and 1009 never do [evidence: test:frontend/src/terminal/terminalSocket.test.ts::reconnect_close_codes]
- AC9: after 10 failed reconnect attempts the state is refused [evidence: test:frontend/src/terminal/terminalSocket.test.ts::refused_after_ten_attempts]
- AC10: send splits a string or Uint8Array larger than 64 KiB into ordered binary frames of at most 65536 bytes whose concatenation equals the input, and a smaller input stays one frame [evidence: test:frontend/src/terminal/terminalSocket.test.ts::large_paste_split_into_frames]

## Files

- `frontend/src/api/terminals.ts`
- `frontend/src/terminal/terminalSocket.ts`
- `frontend/src/terminal/terminalSocket.test.ts`

## Interfaces

- `frontend/src/terminal/terminalSocket.ts`: `openTerminalSocket` (owns part `fe-terminal-socket`, consumed by fe-terminal-panel).
- `frontend/src/api/terminals.ts`: the four functions above.
- Uses the api contract parts `orch-terminals-api` and `orch-terminal-ws` (README `WS /api/v1/agents/{agent_id}/terminals/{terminal_id}/attach`).

## Expected outcome

A tested client that keeps a shell connection alive through ingress idle timeouts and reconnects with replay.

## Steps

- Write `frontend/src/terminal/terminalSocket.test.ts` (node environment; a fake WebSocket class passed as `WebSocketImpl`; `vi.useFakeTimers()`; titles as in the AC refs); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/terminalSocket.test.ts`: fails.
- Implement both modules; run the verify command: passes.

## Notes

- Backoff constants mirror `api/stream.ts` (`BACKOFF_START_MS` 1000, `BACKOFF_MAX_MS` 30000); reuse them rather than duplicating numbers.
- The 20 s ping keeps ingress-nginx from closing an idle connection (its default proxy timeouts are 60 s; the deployed values are 3600).
- Builder check ruling 6: Reconnect on 1006, 1011, 1013 and 4409 with exponential backoff 1 s to 30 s, at most 10 attempts, then state refused; never reconnect on 1000, 1003, 1008, 1009. A refused tab stays with the reason, a Retry and a Close button.

- 2026-10-23 amended: builder check rulings 6 add acceptance conditions AC8-AC9

- 2026-10-23 amended: interrogate ruling 10: a large paste must not kill the terminal, so outgoing input is split into frames of at most 64 KiB
