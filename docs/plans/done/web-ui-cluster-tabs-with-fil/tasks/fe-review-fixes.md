---
title: fe review fixes
status: done
repo: agent-orchestrator
value: "refused terminals say so at once, shells never hide after a late agent, and tabs keep the ribbon's hook-failed and ready marks"
files: [frontend/src/terminal/terminalSocket.ts, frontend/src/terminal/terminalSocket.test.ts, frontend/src/terminal/TerminalPanel.tsx, frontend/src/terminal/TerminalPanel.test.tsx, frontend/src/layout/TopBar.tsx, frontend/src/layout/TopBar.test.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal src/layout && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fake-wrapper-workdir-regress, fe-terminal-panel, fe-terminal-socket, fe-top-bar, kind-e2e-workspace]
model: sonnet
review: ""
verified_head: 6227ccccc4d191c49d2f2f1e4771906651adb473
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 6
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# fe review fixes

## Requirement

Close the epic review findings on the frontend (epic review 2026-10-24).

1. Origin refusal reads as transient: an Origin-refused WebSocket upgrade is an HTTP 403 that the browser reports as close 1006, so frontend/src/terminal/terminalSocket.ts keeps reconnecting for 10 attempts. A socket that closes before it ever reached `open` on two consecutive attempts (the initial attempt and one retry) goes to state `refused` with the reason "connection refused before open (check ORCH_ALLOWED_ORIGINS)". A socket that had been open keeps the existing backoff policy (ruling 6).
2. TerminalPanel lists shells only on mount: re-list the cluster's terminals whenever the set of ready agents of the cluster changes (from the useClusters store), and show the `unavailable_agents` returned by GET /api/v1/clusters/{id}/terminals as a notice line in the panel ("shells on <pod> unavailable") instead of silently hiding them.
3. Indicators lost with the ribbon: each cluster tab label shows a hook-failed mark when the cluster's `discard_hook_failed` is true (with a tooltip "discard hook failed") and the ready/replicas count (for example `2/3`) beside the slug, as ClusterRow did before the ribbon retirement.

## Acceptance conditions

- AC1: two consecutive closes before open put the terminal socket in refused with the ORCH_ALLOWED_ORIGINS reason; a socket that had opened keeps backoff [evidence: command:mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/terminalSocket.test.ts -t "refuses after two closes before open"]
- AC2: the terminal panel re-lists shells when the cluster's ready agents change and renders unavailable_agents as a notice [evidence: command:mise x node@24.20.0 -- npm --prefix frontend test -- src/terminal/TerminalPanel.test.tsx -t "relists when ready agents change and shows unavailable agents"]
- AC3: a cluster tab shows the hook-failed mark when discard_hook_failed and the ready/replicas count [evidence: command:mise x node@24.20.0 -- npm --prefix frontend test -- src/layout/TopBar.test.tsx -t "tab shows hook failed mark and ready count"]

## Files

- `frontend/src/terminal/terminalSocket.ts`
- `frontend/src/terminal/terminalSocket.test.ts`
- `frontend/src/terminal/TerminalPanel.tsx`
- `frontend/src/terminal/TerminalPanel.test.tsx`
- `frontend/src/layout/TopBar.tsx`
- `frontend/src/layout/TopBar.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

A refused terminal shows refused within two attempts; shells appear once an agent turns ready, with unavailable agents named; tabs show the hook-failed mark and ready count.

## Steps

- Write the AC tests and run the verify command: they fail.
- Implement the requirement.
- Run the verify command: all pass.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
