---
title: On start instance hook
status: todo
repo: claude-code-wrapper
value: "Agent clusters can install tools such as any-mcp once per pod start, before any session or MCP server runs"
files: [src/claude_code_wrapper/config.py, src/claude_code_wrapper/hooks.py, src/claude_code_wrapper/service.py, README.md, tests/test_on_start_hook.py]
verify: "uv run pytest tests/test_on_start_hook.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [wrapper-on-start-hook]
uses: []
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

# On start instance hook

## Requirement

A new instance lifecycle hook `onStart`, fired once per ccw process start, before any session can be created or resumed. agent-orchestrator renders one onStart command per agent cluster that installs any-mcp and writes its config, so the hook must have run before claude spawns its stdio MCP servers.

Why it is needed (probed on main, c53f7ed): the wrapper has no instance-start hook today. `HooksConfig` (src/claude_code_wrapper/config.py:419-439) lists session events (onCreate, onResume, ...) and the peer instance events preJoin, postJoin, preLeave and postLeave only. `onCreate` fires after claude is already running (manager.py:594-605, README.md:1305-1308), which is too late for an MCP server binary. `init.setup_commands` run before claude, but per created session only: manager.py:474-482 calls them in `create` and never in `resume` (manager.py:975-1009), and workdir.py:149-160 skips them once the `setup.done` marker exists. `preJoin` (README.md:1461-1463) never fires when `peers.enabled` is false.

Behaviour:
- `onStart` is added to `HOOK_EVENTS` (config.py:29), to `HooksConfig`, to `INSTANCE_EVENTS` (hooks.py:50) and to `VETO_EVENTS` (config.py:52), so it honours `allow` and `deny`. `matcher`, `interval_seconds` and `when` stay rejected on it by the existing validators.
- It fires in `service._run` (service.py:188-245) after `tooling.install_global` (service.py:194-195) and before `manager.start_peers` and `manager.load_persisted` (service.py:220-221). The service therefore does not listen until onStart has finished: no create, resume, `resume_on_start` or peer join happens first.
- The envelope is the instance-event envelope that `fire_instance` builds (hooks.py:443-460): empty `session_id` and `workdir`, null `claude_session_id` and `turn_id`, and `data` `{}`. Actions run in the sessions root and get the full service environment, as the other command actions do.
- Blocking actions are awaited, each bounded by its `timeout_seconds`.
- A blocking `deny`, or a failure or timeout of a blocking action with `on_error: deny`, makes ccw log `onStart denied: <reason>` and exit with code 1 before it binds the public port. The pod then restarts and the failure shows up.
- A failing action with `on_error: allow` is logged and startup continues. Non-blocking actions run in the background and never delay startup.
- No onStart actions means no change in behaviour.
- README.md documents `### onStart` next to preJoin (trigger, order, envelope, the exit-on-deny rule) and adds onStart to the event list and to the decision table (`allow`, `deny`). tests/test_readme_api.py keeps passing.

Additive only: no existing event changes order or payload.

## Acceptance conditions

- AC1: hooks.onStart is accepted by load_config and rejects matcher and interval_seconds [evidence: test:tests/test_on_start_hook.py::test_config_accepts_on_start_and_rejects_matcher]
- AC2: onStart fires once per process start, before peer join and before resume_on_start resumes a persisted session [evidence: test:tests/test_on_start_hook.py::test_fires_before_peers_and_resume]
- AC3: a blocking onStart deny exits the service with code 1 before the public port is bound [evidence: test:tests/test_on_start_hook.py::test_blocking_deny_exits_non_zero]
- AC4: a failing blocking action with on_error deny exits non-zero and one with on_error allow lets startup continue [evidence: test:tests/test_on_start_hook.py::test_on_error_deny_exits_and_allow_continues]
- AC5: a non-blocking onStart action does not delay startup [evidence: test:tests/test_on_start_hook.py::test_non_blocking_does_not_delay_startup]
- AC6: a command action sees the instance envelope on stdin and runs in the sessions root [evidence: test:tests/test_on_start_hook.py::test_command_gets_instance_envelope_in_sessions_root]
- AC7: README documents onStart [evidence: command:grep -qE '^### `?onStart`?$' README.md]
- AC8: the README API parity test passes with onStart documented [evidence: command:uv run pytest tests/test_readme_api.py -q]

## Files

- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/hooks.py`
- `src/claude_code_wrapper/service.py`
- `README.md`
- `tests/test_on_start_hook.py`

## Interfaces

- `claude_code_wrapper.config:HooksConfig.onStart` and `HOOK_EVENTS`, `VETO_EVENTS` including `onStart`
- `claude_code_wrapper.hooks:INSTANCE_EVENTS` including `onStart`; `fire_instance` returns deny for a failed blocking onStart action with `on_error: deny`, as it does for preJoin
- README `### \`onStart\`` (contract `wrapper-on-start-hook`, consumed by agent-orchestrator k8s-object-renderer and kind-e2e)

## Expected outcome

A config with `hooks.onStart: [{type: command, run: "sh /etc/ccw/on-start.sh", blocking: true, on_error: deny, timeout_seconds: 600}]` runs the script once at process start, before the service listens. A failing script stops the process with exit code 1.

## Steps

- Write tests/test_on_start_hook.py with the six named tests. Drive `service._run` through the existing service test helpers (see tests/test_peers_startup.py) with tests/fake_claude, and use command actions that write marker files. Run `uv run pytest tests/test_on_start_hook.py -q` and expect failures.
- Add onStart to config.py, hooks.py and service.py, and write the README section.
- Rerun `uv run pytest tests/test_on_start_hook.py tests/test_readme_api.py -q` and expect every test to pass. Then run `uv run ruff check . && uv run ruff format --check .`.

## Notes

Requested at the agent-orchestrator gate (its Q8): any-mcp is installed by a rendered onStart script instead of a derived image. The agent pod gets a startupProbe sized to the hook timeout, because the service does not listen until onStart finishes. Reuse `fire_instance` (hooks.py:443) and the HookDispatcher that peer membership uses (peer_membership.py:192); do not build a second dispatcher. The exit code is 1 (my call). The README heading follows the existing style (`### \`onStart\``).
