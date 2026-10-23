# Interrogate verdict: web-ui-cluster-tabs-with-fil (design + plan)

Panel: A fable, B opus, C sonnet; one pass, 2026-10-23. Lead: orchestrator.

## Act on

1. Shell env contract contradicts itself (A, B, C). terminal-registry requirement and design D11 say `service_env` minus four names; ruling 4 / AC15 say the Claude env. Rewrite both to: the env `manager._child_env(ctx)` builds for Claude (BASE_ENV + passthrough + TERM), minus every `ClaudeEnv` name of kind `secret` (claude_env.py:30, includes ANTHROPIC_API_KEY, CLAUDE_CODE_OAUTH_TOKEN) and CCW_AUTH_TOKEN, CCW_PEER_TOKEN, CCW_HOOK_TOKEN. Also fix "exited terminal removed after the same delay" to ruling 2 (next reaper tick).
2. Scrub tests are vacuous (B, C). Unit tests and wrapper-workspace-e2e must seed every scrubbed name into the service and Claude env before asserting absence.
3. WebSocket close-code mapping (A, B, C). 1005 maps to 1000; 1006, 1015 and no code map to 1011; never re-send 1005/1006/1015. Pin in terminal-ws-relay AC6 / test_close_propagates_without_leak.
4. terminal_id format check (C; B saw a 307, either way the derived bearer must not reach other upstream paths). Orchestrator HTTP and WS terminal routes accept only the wrapper's terminal id format (`^term_[0-9a-f]{12}$` or whatever the wrapper registry emits, pinned in one place), 422 invalid_request otherwise; same check in the wrapper routes.
5. README error codes (C). Wrapper README Errors rows and orchestrator README error list gain session_not_active and invalid_size; tests/test_readme_api.py stays green.
6. Cap and reaper races (C). Reserve the slot synchronously before awaiting PtyProcess.start; unregister a terminal synchronously before awaiting close. Tests: concurrent creates never exceed the cap; attach during reap gets 404 or the exit frame, never a hang.
7. Token hygiene in the proxy seam (C). WrapperTarget.token is `field(repr=False)`; the token is only sent as an Authorization header; a caplog test at DEBUG over file and terminal proxy calls finds no token in logs or responses.
8. Shared httpx client vs ASGITransport tests (C). Create the client lazily (or in create_app) so tests that never run the lifespan work; close it in the lifespan shutdown.
9. File read TOCTOU (A). After the realpath confinement check open with O_RDONLY|O_NOFOLLOW|O_NONBLOCK, fstat the fd and refuse non-regular files; never stat-then-open by path.
10. Large paste kills the terminal (B). fe-terminal-socket splits outgoing input into frames of at most 64 KiB; AC.
11. Orphaned jobs survive close (B). Closing a shell kills every process in the shell's session (sid == shell pid), not only its process group; AC8 asserts a nohup'd background job is gone after close, destroy and shutdown.
12. Redaction stance (B). Wrapper README Trust model documents that file content and terminal frames are not passed through the secret redactor (redaction would corrupt files and PTY streams; the shell already runs as the agent uid). Doc AC on wrapper-file-api.
13. Bookkeeping (A, B). origin-allowlist `## Files` lists chart/agent-orchestrator/README.md; terminal-registry verify adds the test_manager.py tests it touches, deselecting test_shutdown_stops_all (fails only in this container: PID 1 does not reap zombies).

## Consider

- none

## Noted

- Agent pods reaching the ingress: mitigated by denySourceRanges (agents-helmfile common.yaml:40).
- Missing Origin header passes (non-browser clients); documented.

## Dismissed

- SSRF via agent selection: upstream URLs come only from agents.url, scoped by cluster (A, B, C agree).
- DNS rebinding: ingress host rule plus TLS.
- CSRF on existing chat POSTs: pre-existing, outside this epic.

Agreement: all three converged on the env contract and the close-code mapping; split only on the severity of the `..` terminal id (C high, B harmless 307); the lead acts on it because the fix is one regex.
