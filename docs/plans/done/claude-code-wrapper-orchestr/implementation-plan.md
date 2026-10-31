# claude-code-wrapper orchestrator support implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: Idle since in snapshot

- Status: done
- Files: `src/claude_code_wrapper/manager.py`, `src/claude_code_wrapper/router.py`, `README.md`, `tests/test_idle_since.py`
- Verify: `uv run pytest tests/test_idle_since.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 9961bc9094a8a0bd2a7a92b12a9d6b83eb14661f

#### Requirement

The session snapshot (manager.py snapshot dict, manager.py:1429-1453) gains `idle_since`: the ISO timestamp of the latest transition into the public state `ready`, and null in any other state. `idle_since` is set by every transition into ready: creating -> ready at boot (session.py:496-497), busy -> ready on turn completion (session.py:989 `_set_state(next_state)` and 1037), and the post-restart boot that reaches ready again. A turn start (busy) clears it. Stopped sessions loaded from disk report null.

Every `session_state` event data gains `since` (ISO timestamp of that transition), including the events emitted by `Router.on_state` (router.py:1355) and the restart event in `Router.on_restart` (router.py:1380-1390, whose `state` comes from `session.snapshot()` and may be creating or ready; its `since` is the time of that emit and equals the preceding transition). Both are additive; existing fields and events are unchanged.

Relation to `ready_at`: `ready_at` (session.py:381, set at session.py:496) is the time the latest boot of claude became ready and is not touched by turns; `idle_since` equals it right after boot and then moves forward on each turn completion. They are not merged; `ready_at` stays as is.

README.md documents `idle_since` in the snapshot table and `since` in the session_state event row (tests/test_readme_api.py enforces documented routes and events). The orchestrator uses idle_since to route to the agent free the longest.

#### Acceptance conditions

- AC1: a freshly ready session snapshot has a non-null ISO idle_since equal to the creating -> ready transition [evidence: test:tests/test_idle_since.py::test_ready_session_has_idle_since]
- AC2: idle_since is null while busy and reset to the completion transition time on turn completion [evidence: test:tests/test_idle_since.py::test_idle_since_cleared_when_busy_and_reset_on_completion]
- AC3: every session_state event carries since, including the creating -> ready event and the on_restart event [evidence: test:tests/test_idle_since.py::test_session_state_event_carries_since]
- AC4: after a claude restart that reaches ready, idle_since equals the latest transition into ready and ready_at is the boot time [evidence: test:tests/test_idle_since.py::test_idle_since_after_restart_and_ready_at_relation]
- AC5: README documents idle_since and since [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]

#### Files

- `src/claude_code_wrapper/manager.py`
- `src/claude_code_wrapper/router.py`
- `README.md`
- `tests/test_idle_since.py`

#### Interfaces

manager.py snapshot dict (~1429-1453) gains idle_since; router.py session_state data gains since. Contract wrapper-idle-since.

#### Expected outcome

GET /v1/sessions/{id} shows idle_since while ready and null otherwise; session_state events carry since.

#### Steps

- Write tests/test_idle_since.py; run `uv run pytest tests/test_idle_since.py -q` and see it fail (no idle_since key).
- Implement in manager.py snapshot and the router session_state emit; update README.md.
- Run `uv run pytest tests/test_idle_since.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`; expect all passed.

#### Ruling

- 2026-10-22 accepted: land-failed was suite-lock contention (lock held 1200s by the template epic close, pid 79691), not a code failure; task verified on 9961bc9 (11 passed, ruff clean). Process gap recorded: tests written after the implementation (no red run); the tests exercise the behaviour.

#### Notes

Reuse the existing now_iso helper (timeutil.py). Session.on_state is notified only when the public state changes (session.py:412-419), so `since` is stamped there, in one place, from the same clock reading that updates idle_since. Never run the full suite (11 min). The branch must be rebased on origin/main before the PR.

### S2: On start instance hook

- Status: done
- Files: `src/claude_code_wrapper/config.py`, `src/claude_code_wrapper/hooks.py`, `src/claude_code_wrapper/service.py`, `README.md`, `tests/test_on_start_hook.py`
- Verify: `uv run pytest tests/test_on_start_hook.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 7f04ddc0f40f92c634deb7fac4c9eb243f536e67

#### Requirement

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

#### Acceptance conditions

- AC1: hooks.onStart is accepted by load_config and rejects matcher and interval_seconds [evidence: test:tests/test_on_start_hook.py::test_config_accepts_on_start_and_rejects_matcher]
- AC2: onStart fires once per process start, before peer join and before resume_on_start resumes a persisted session [evidence: test:tests/test_on_start_hook.py::test_fires_before_peers_and_resume]
- AC3: a blocking onStart deny exits the service with code 1 before the public port is bound [evidence: test:tests/test_on_start_hook.py::test_blocking_deny_exits_non_zero]
- AC4: a failing blocking action with on_error deny exits non-zero and one with on_error allow lets startup continue [evidence: test:tests/test_on_start_hook.py::test_on_error_deny_exits_and_allow_continues]
- AC5: a non-blocking onStart action does not delay startup [evidence: test:tests/test_on_start_hook.py::test_non_blocking_does_not_delay_startup]
- AC6: a command action sees the instance envelope on stdin and runs in the sessions root [evidence: test:tests/test_on_start_hook.py::test_command_gets_instance_envelope_in_sessions_root]
- AC7: README documents onStart [evidence: command:grep -qE '^### `?onStart`?$' README.md]
- AC8: the README API parity test passes with onStart documented [evidence: command:uv run pytest tests/test_readme_api.py -q]

#### Files

- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/hooks.py`
- `src/claude_code_wrapper/service.py`
- `README.md`
- `tests/test_on_start_hook.py`

#### Interfaces

- `claude_code_wrapper.config:HooksConfig.onStart` and `HOOK_EVENTS`, `VETO_EVENTS` including `onStart`
- `claude_code_wrapper.hooks:INSTANCE_EVENTS` including `onStart`; `fire_instance` returns deny for a failed blocking onStart action with `on_error: deny`, as it does for preJoin
- README `### \`onStart\`` (contract `wrapper-on-start-hook`, consumed by agent-orchestrator k8s-object-renderer and kind-e2e)

#### Expected outcome

A config with `hooks.onStart: [{type: command, run: "sh /etc/ccw/on-start.sh", blocking: true, on_error: deny, timeout_seconds: 600}]` runs the script once at process start, before the service listens. A failing script stops the process with exit code 1.

#### Steps

- Write tests/test_on_start_hook.py with the six named tests. Drive `service._run` through the existing service test helpers (see tests/test_peers_startup.py) with tests/fake_claude, and use command actions that write marker files. Run `uv run pytest tests/test_on_start_hook.py -q` and expect failures.
- Add onStart to config.py, hooks.py and service.py, and write the README section.
- Rerun `uv run pytest tests/test_on_start_hook.py tests/test_readme_api.py -q` and expect every test to pass. Then run `uv run ruff check . && uv run ruff format --check .`.

#### Notes

Requested at the agent-orchestrator gate (its Q8): any-mcp is installed by a rendered onStart script instead of a derived image. The agent pod gets a startupProbe sized to the hook timeout, because the service does not listen until onStart finishes. Reuse `fire_instance` (hooks.py:443) and the HookDispatcher that peer membership uses (peer_membership.py:192); do not build a second dispatcher. The exit code is 1 (my call). The README heading follows the existing style (`### \`onStart\``).

### S3: Peer mesh view route

- Status: done
- Files: `src/claude_code_wrapper/api/peers.py`, `src/claude_code_wrapper/peer_membership.py`, `README.md`, `tests/test_api_peers_view.py`
- Verify: `uv run pytest tests/test_api_peers_view.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 892610075f08ff303a9f9b8481777d143a0c53e7

#### Requirement

`GET /v1/peers` (bearer auth) returns the peer mesh view: `{enabled: false}` when `peers` is not enabled, otherwise `{enabled: true, self: {instance, url}, members: [{instance, url, sessions, last_seen_at, missed}]}`. It is mounted unconditionally: api/app.py:79-85 mounts the HMAC `peers.router` only when `cfg.peers.enabled`, so the new bearer route lives in a separate router included in the `v1` router (api/app.py:73-78) regardless, and answers `{enabled: false}` itself when `manager.peers is None` (manager.py:302). Fields come from peers.py: `self` from `PeerService.instance` and `.url` (peer_service.py:78-79); each member from `Member` (peers.py:60-66) fields `instance`, `url`, `sessions` (tuple of `PeerSession` {session_id, name, cwd}, peers.py:53), `missed` and `last_seen` (a monotonic float, converted to ISO `last_seen_at`, null when None); `reachable` is not exposed. It never exposes peers.token and is not HMAC-signed (the existing POST /v1/peers/* routes stay HMAC-only). Implemented in api/peers.py (a bearer router separate from the signed one) with a read accessor on the MemberTable. README.md documents the route and the response (test_readme_api enforces it).

#### Acceptance conditions

- AC1: peers disabled returns {enabled: false} [evidence: test:tests/test_api_peers_view.py::test_disabled_returns_enabled_false]
- AC2: enabled returns self and members with sessions, last_seen_at and missed [evidence: test:tests/test_api_peers_view.py::test_enabled_lists_members]
- AC3: requires the bearer token and never leaks peers.token [evidence: test:tests/test_api_peers_view.py::test_requires_bearer_and_hides_token]
- AC4: README documents GET /v1/peers [evidence: test:tests/test_readme_api.py::test_every_public_route_documented]

#### Files

- `src/claude_code_wrapper/api/peers.py`
- `src/claude_code_wrapper/peer_membership.py`
- `README.md`
- `tests/test_api_peers_view.py`

#### Interfaces

api/peers.py bearer route GET /v1/peers; peer_membership.py snapshot accessor. Contract wrapper-peers-view.

#### Expected outcome

GET /v1/peers with the bearer returns the mesh view; peers off returns {enabled: false}.

#### Steps

- Write tests/test_api_peers_view.py; run it and see it fail (404).
- Add a bearer router in api/peers.py and a read accessor on PeerMembership; update README.md.
- Run `uv run pytest tests/test_api_peers_view.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`.

#### Notes

The signed POST /v1/peers/* routes are mounted only with peers.enabled (api/app.py:79-85); the GET must be mounted always. Reuse the bearer dependency in api/auth.py (require_auth, applied to `v1`). Monotonic `last_seen` must be converted to wall-clock using the table clock offset at read time.

### S4: User message event

- Status: done
- Files: `src/claude_code_wrapper/router.py`, `src/claude_code_wrapper/events.py`, `README.md`, `tests/test_user_message_event.py`
- Verify: `uv run pytest tests/test_user_message_event.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: d9c061f9c42ec7fe7afeba4ec13fc127eee5e2c4

#### Requirement

A new SSE/history event type `user_message` with data `{turn_id, origin, text, files}`, emitted by the router every time a prompt is pasted into the session. `origin` reuses the Origin values of turns.py:27 (`client`, `initial`, `agent`, `peer`) plus `restart` (the continue or resume prompt pasted after a claude restart) and `command` (a slash command line). `turn_id` is null for `command`. `turn_started.data.text` stays unchanged. The type is added to events.py EVENT_TYPES and documented in README.md (event table and origin values; tests/test_readme_api.py enforces it). Additive only. The event rides the normal ring and rotation like every other event (my call).

Emitting paths (exhaustive; line numbers at checkout c53f7ed):

- Fresh submit: `Session.submit` (session.py:762) sets state busy (session.py:796, so `session_state busy` is already logged) and pastes (session.py:801); `Router.submit_turn` then emits `user_message` immediately before `turn_started` (router.py:809), origin = the record's origin (`client`, `initial`, `agent` or `peer`). This also covers the peer path, because `peer_inbox.py:297` goes through `router.submit_turn(..., origin="peer")`; `text` is the framed peer message, `files` empty.
- Continue paths, all through `Session.continue_turn` (session.py:680, paste at session.py:700): the post-command continuation (router.py:1039, emitted next to `turn_resumed` cause command) and the post-restart continuation (`Session._continue_held`, session.py:678, with `on_turn_resumed` at router.py:1403/1410). The Stop-hook block path (`turn_continued`, router.py:676) pastes nothing, the reason goes back as the hook answer, so it emits no `user_message`. A command continuation uses the turn's own origin and `text` is the continue prompt. On a restart continue, `text` is the continue prompt (`sessions.restart_continue_prompt`) and origin is `restart`.
- Slash commands: `Session.send_command` (session.py:1056, called from router.py:1218) emits `user_message` with origin `command`, `turn_id` null and `text` the rendered command line.

Order within the log: `session_state busy` < `user_message` < `turn_started` (fresh submit) and `user_message` < `turn_completed` for the same turn_id.
Existing contract pinned, no new feature: turn events keep `origin`, `final_text` and `usage` (the `record` is a TurnRecord dump, `_emit_turn_event`, router.py:731-732; fields turns.py:90, 93, 95), and the snapshot keeps `current_turn_id`, `model` and `workdir` (manager.py:1436, 1438, 1445). AC9 pins them with a test.

#### Acceptance conditions

- AC1: a client-origin turn emits user_message with text, files and origin client after session_state busy and before turn_started [evidence: test:tests/test_user_message_event.py::test_user_turn_emits_user_message]
- AC2: a peer-origin turn (via peer_inbox.py:297) emits user_message with origin peer [evidence: test:tests/test_user_message_event.py::test_peer_origin]
- AC3: a restart continue emits user_message with origin restart whose text is the restart continue prompt [evidence: test:tests/test_user_message_event.py::test_restart_continue_origin_and_text]
- AC4: a command-continuation paste (router.py:1039 path) emits user_message with the continue prompt and the turn's origin [evidence: test:tests/test_user_message_event.py::test_command_continuation_paste]
- AC5: a slash command emits user_message with origin command and turn_id null [evidence: test:tests/test_user_message_event.py::test_slash_command_origin_command]
- AC6: user_message is ordered after session_state busy and before turn_completed of the same turn [evidence: test:tests/test_user_message_event.py::test_event_order]
- AC7: turn_started text is unchanged [evidence: test:tests/test_user_message_event.py::test_turn_started_text_unchanged]
- AC8: user_message is in EVENT_TYPES and documented in README.md [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]
- AC9: turn_completed.data.record carries origin, final_text and usage, and the session snapshot carries current_turn_id, model and workdir [evidence: test:tests/test_user_message_event.py::test_turn_and_snapshot_fields_pinned]

#### Files

- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/events.py`
- `README.md`
- `tests/test_user_message_event.py`

#### Interfaces

events.py EVENT_TYPES gains user_message; data {turn_id, origin, text, files}. Contract wrapper-user-message-event.

#### Expected outcome

After a prompt is pasted the event log holds user_message with turn_id, origin, text, files; turn_started is unchanged.

#### Steps

- Write tests/test_user_message_event.py with the fake claude; run it and see it fail (unknown event type).
- Add user_message to events.py EVENT_TYPES; emit in router.py at paste time (router.py:810 is where turn_started is emitted); update README.md.
- Run `uv run pytest tests/test_user_message_event.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`.

#### Notes

Emit when the prompt is actually pasted, not on accept. Shares events.py/router.py with other tasks: this is why the chain is ordered. The Stop-hook block (turn_continued, router.py:676) is deliberately not a paste. The `user_message` for slash commands is emitted in the router where `send_command` is called (router.py:1216-1218), after `command_started`. Origin is the turns.py:27 Literal extended by `restart` and `command`; do not widen `TurnRecord.origin`, only the event data.

- 2026-10-23 run claude-code-wrapper-orchestr: dependency-failed on idle-since-in-snapshot

### S5: History before_seq and types

- Status: done
- Files: `src/claude_code_wrapper/events.py`, `src/claude_code_wrapper/api/events.py`, `README.md`, `tests/test_history_backward.py`
- Verify: `uv run pytest tests/test_history_backward.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: e6c6e4be81099264628a95b4e3d26e8d443c7991

#### Requirement

`GET /v1/sessions/{id}/history` accepts `before_seq=N`, `limit` (max 1000, as today) and `types=a,b` (comma list). `types` is validated against `EVENT_TYPES` (events.py:20), which by then includes the new `user_message` and `context` types; an unknown type returns 400 invalid_request. With before_seq it returns the events with seq < N, the newest page selected but returned in ascending seq order, plus `prev_seq` (the seq to pass as before_seq for the next older page; null when `has_more_before` is false) and `has_more_before`. `types` filters before paging, also for the forward (after_seq) mode. Combining before_seq with after_seq returns 400 invalid_request. Works for stopped (readonly) sessions and reads the rotated events.jsonl correctly. Implementation lives in EventLog (events.py, a new page_before method beside `page` at events.py:236) and api/events.py (history at api/events.py:35). README.md documents the parameters and response fields. Additive: the existing response shape is unchanged without before_seq.

#### Acceptance conditions

- AC1: before_seq returns the newest older page in ascending order with prev_seq and has_more_before [evidence: test:tests/test_history_backward.py::test_before_seq_pages_backwards]
- AC2: types filters in both directions [evidence: test:tests/test_history_backward.py::test_types_filter]
- AC3: before_seq with after_seq is 400 and an unknown type is 400 [evidence: test:tests/test_history_backward.py::test_invalid_combinations_are_400]
- AC4: works on a stopped session and after log rotation [evidence: test:tests/test_history_backward.py::test_stopped_session_and_rotation]
- AC5: README documents before_seq, types, prev_seq, has_more_before [evidence: test:tests/test_readme_api.py::test_every_public_route_documented]
- AC6: prev_seq is null when has_more_before is false; types accepts user_message and context and rejects an unknown type with 400 [evidence: test:tests/test_history_backward.py::test_prev_seq_null_and_types_validated_against_event_types]

#### Files

- `src/claude_code_wrapper/events.py`
- `src/claude_code_wrapper/api/events.py`
- `README.md`
- `tests/test_history_backward.py`

#### Interfaces

events.py EventLog.page_before(before_seq, limit, types) -> (events, has_more_before); api/events.py query params. Contract wrapper-history-backward.

#### Expected outcome

Backward pages work with before_seq and types, with prev_seq and has_more_before; invalid combinations are 400.

#### Steps

- Write tests/test_history_backward.py; run it and see it fail (param ignored).
- Add EventLog.page_before in events.py and wire before_seq/types in api/events.py; update README.md.
- Run `uv run pytest tests/test_history_backward.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`.

#### Notes

Existing page() takes the ring fast path only when ring[0].seq <= after_seq+1; backward paging must fall back to _read_file when the ring does not cover the range. Rotation drops the oldest half of events.jsonl (events.py:212-225).

- 2026-10-23 run claude-code-wrapper-orchestr: dependency-failed on user-message-event

### S6: Statusline relay

- Status: done
- Files: `src/claude_code_wrapper/cli.py`, `src/claude_code_wrapper/statusline.py`, `src/claude_code_wrapper/internal_api.py`, `src/claude_code_wrapper/bootstrap/settings.py`, `src/claude_code_wrapper/router.py`, `README.md`, `tests/test_statusline_relay.py`
- Verify: `uv run pytest tests/test_statusline_relay.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 8fa8c5f8e53c17685750536ccacf4435f2715684

#### Requirement

Statusline relay, the source of context-window usage. (1) A new CLI subcommand `ccw statusline` (cli.py main at cli.py:94, logic in a new statusline.py) reads the Claude Code statusLine JSON from stdin, posts it to the loopback internal API route `POST /internal/statusline` (internal_api.py beside `/internal/hooks/{event}` at internal_api.py:72, session identified as the hook relay identifies it, hook_relay.py:136), then runs the chained command and feeds it the same stdin and prints its stdout; with no chained command it prints nothing. A failure to post never fails the statusline (best effort, bounded timeout). (2) bootstrap/settings.py renders the session settings in this order: relay hooks (settings.py:99-107), permissions, the `claude.settings` overlay merge (settings.py:134-143), and then, new, the statusLine step: the chained command is the `statusLine.command` present in the document after the overlay merge, i.e. the user's `claude.settings.statusLine` as rendered at settings.py:134; the step replaces `doc["statusLine"]` with `{type: command, command: "ccw statusline"}`, writes the original command (and its padding/refreshInterval are kept on the replacement) to the chain config file the relay reads, and then the file is written (settings.py:145). Re-rendering is idempotent: if the document's statusLine already is `ccw statusline` the chain config is left as is, never chained to itself. (3) The route validates the payload and hands `context_window.{used_percentage, context_window_size, current_usage}` and `model` to a router callback `on_statusline(payload)` that stores the latest values; surfacing them is task context-in-snapshot-and-sse. README.md documents the subcommand, the route being internal, and the chaining behaviour; test_readme_config enforces any config key.

#### Acceptance conditions

- AC1: ccw statusline posts the stdin JSON to /internal/statusline [evidence: test:tests/test_statusline_relay.py::test_cli_posts_stdin_to_internal_route]
- AC2: it runs the chained user statusLine and prints its stdout [evidence: test:tests/test_statusline_relay.py::test_chained_command_output_is_printed]
- AC3: an unreachable internal API does not fail the statusline [evidence: test:tests/test_statusline_relay.py::test_post_failure_is_best_effort]
- AC4: settings bootstrap installs ccw statusline and preserves a user statusLine as the chain [evidence: test:tests/test_statusline_relay.py::test_settings_install_and_chain]
- AC5: the internal route validates the payload and calls the router callback [evidence: test:tests/test_statusline_relay.py::test_internal_route_validates_and_dispatches]
- AC6: README documents the relay [evidence: test:tests/test_readme_api.py::test_every_internal_route_documented]
- AC7: the chained command is the user's claude.settings.statusLine as rendered after the overlay merge, and re-rendering is idempotent (never chains itself) [evidence: test:tests/test_statusline_relay.py::test_chain_taken_after_overlay_and_idempotent]

#### Files

- `src/claude_code_wrapper/cli.py`
- `src/claude_code_wrapper/statusline.py`
- `src/claude_code_wrapper/internal_api.py`
- `src/claude_code_wrapper/bootstrap/settings.py`
- `src/claude_code_wrapper/router.py`
- `README.md`
- `tests/test_statusline_relay.py`

#### Interfaces

cli.py: ccw statusline; internal_api.py: POST /internal/statusline; router.py: on_statusline(payload). Contract wrapper-statusline-callback.

#### Expected outcome

A session's Claude Code runs ccw statusline; the wrapper receives context_window values at /internal/statusline and the user's own statusLine output is unchanged.

#### Steps

- Write tests/test_statusline_relay.py (CLI with a stub internal server, chain command, settings render); run it and see it fail.
- Add statusline.py and the ccw statusline subcommand in cli.py, the internal route, the settings.py install and chain, the router on_statusline callback; update README.md.
- Run `uv run pytest tests/test_statusline_relay.py tests/test_readme_api.py tests/test_readme_config.py -q && uv run ruff check . && uv run ruff format --check .`.

#### Notes

Follow hook_relay.py for how the CLI finds the internal API and session id. Best effort post with a short timeout. Statusline JSON fields: context_window.used_percentage, context_window_size, current_usage (code.claude.com/docs/en/statusline); null before the first assistant message and after /compact.

- 2026-10-23 run claude-code-wrapper-orchestr: dependency-failed on history-before-seq-and-types

### S7: Context in snapshot and SSE

- Status: done
- Files: `src/claude_code_wrapper/manager.py`, `src/claude_code_wrapper/router.py`, `src/claude_code_wrapper/events.py`, `README.md`, `tests/test_context_surface.py`
- Verify: `uv run pytest tests/test_context_surface.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 25d4cc1897fb1f8e82e8a433ae8fe60572ac05f4

#### Requirement

Expose context usage. The snapshot gains `context: {used_tokens, window_tokens, used_percentage, model, source: "statusline", updated_at} | null`, filled from the values the statusline relay delivers to the router (`on_statusline`). A new SSE/history event `context` carries the same fields and is emitted only when the values change (dedupe on used_tokens, window_tokens and used_percentage). The context is null until the first assistant message, and is reset to null (and a null-context event emitted if it was non-null) after `compacted`, as the statusline docs describe. The denominator is the full model window reported by the statusline; the wrapper holds no model-window table. `context` is added to EVENT_TYPES and documented in README.md (snapshot table and event table).
Field derivation from the statusline stdin JSON (statusline doc, "Available data", context_window fields: `current_usage{input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens}`, `context_window_size`, `used_percentage`, `model.{id,display_name}`): `used_tokens` = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` of `current_usage` (output tokens excluded, matching the doc's definition of used_percentage); `window_tokens` = `context_window_size`; `model` = the statusline `model.id`; `used_percentage` = the statusline value, and when it is null but `window_tokens` and `used_tokens` are both known it is computed as `used_tokens / window_tokens * 100` (clamped to 0-100); otherwise null. When `current_usage` is null (before the first call and after /compact) the whole context is null. `context` and its events ride the normal ring and rotation (my call).

#### Acceptance conditions

- AC1: snapshot context is null before any statusline update [evidence: test:tests/test_context_surface.py::test_snapshot_context_null_initially]
- AC2: a statusline update fills the snapshot and emits one context event [evidence: test:tests/test_context_surface.py::test_update_fills_snapshot_and_emits_event]
- AC3: an identical update emits no second event [evidence: test:tests/test_context_surface.py::test_identical_update_is_deduped]
- AC4: compacted resets context to null [evidence: test:tests/test_context_surface.py::test_compact_resets_context]
- AC5: README documents the context snapshot field and event [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]
- AC6: used_tokens is the sum of input, cache_creation and cache_read tokens and model is model.id [evidence: test:tests/test_context_surface.py::test_used_tokens_sum_and_model_id]
- AC7: a null used_percentage with known window and tokens is computed; unknown inputs give null [evidence: test:tests/test_context_surface.py::test_used_percentage_computed_when_null]

#### Files

- `src/claude_code_wrapper/manager.py`
- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/events.py`
- `README.md`
- `tests/test_context_surface.py`

#### Interfaces

manager.py snapshot gains context {used_tokens, window_tokens, used_percentage, model, source, updated_at} | null; events.py gains context. Contracts wrapper-context-surface (owns), wrapper-statusline-callback (uses).

#### Expected outcome

Snapshot context is null, then filled after a statusline update, with one context event per distinct change, and null again after compaction.

#### Steps

- Write tests/test_context_surface.py driving router.on_statusline; run it and see it fail.
- Store the latest context in the router, expose it in manager.py snapshot, add the context event type with dedupe, reset on compacted; update README.md.
- Run `uv run pytest tests/test_context_surface.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`.

#### Notes

router.py already keeps _last_context for auto-compact (router.py:257, 858); do not conflate it with the statusline values. Compaction emit is router.py:887.
Statusline field semantics are from the Claude Code statusline doc (brief-docs.md section 5, item 1): used_percentage = (input + cache_creation + cache_read) / context_window_size, output excluded; current_usage and the percentages are null early in the session and current_usage after /compact.

- 2026-10-23 run claude-code-wrapper-orchestr: dependency-failed on statusline-relay

### S8: history scan off event loop

- Status: done
- Files: `src/claude_code_wrapper/events.py`, `src/claude_code_wrapper/api/events.py`, `tests/test_history_backward.py`
- Verify: `uv run pytest tests/test_history_backward.py tests/test_event_log.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: d41dd76a6710d1ffe7121ad1817075acdd6ec3ce

#### Requirement

Security finding (medium): EventLog.page_before (events.py:259-278) and page with types (:247-254) parse the whole JSONL file synchronously on the event loop when the ring misses, so repeated authenticated calls can stall the service. Run the file scan off the event loop (asyncio.to_thread from the API handler, or an async variant) and bound the bytes scanned per request (read the file backwards in chunks, stopping once limit matches are collected), keeping results identical.

#### Acceptance conditions

- AC1: a history request whose scan reads the file does not block the event loop (a concurrent request completes while the scan runs) [evidence: test:tests/test_history_backward.py::test_file_scan_runs_off_event_loop]
- AC2: page_before stops reading once limit matches are collected, results unchanged [evidence: test:tests/test_history_backward.py::test_page_before_bounded_scan]

#### Files

- `src/claude_code_wrapper/events.py`
- `src/claude_code_wrapper/api/events.py`
- `tests/test_history_backward.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The requirement above holds, pinned by the acceptance tests.

What is true and observable when the task is done.

#### Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S9: statusline absolute command

- Status: done
- Files: `src/claude_code_wrapper/statusline.py`, `src/claude_code_wrapper/bootstrap/settings.py`, `tests/test_statusline_relay.py`
- Verify: `uv run pytest tests/test_statusline_relay.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 8cad3c4dd7df7e779d784cd4edefe50c23179382

#### Requirement

Review finding (medium): statusline.py STATUSLINE_COMMAND is the bare 'ccw statusline' resolved through PATH, while the hook relay uses an absolute path (bootstrap/settings.py default_relay_command, :50-60) because the venv's ccw may not be on PATH. Resolve the statusline command the same way (absolute path to the running ccw), and make _install_statusline recognise an already-installed relay by basename so reinstalls stay idempotent. Security finding (low): statusline.run_chain runs the chained user command with shell=True and the inherited environment, so it receives CCW_HOOK_TOKEN; pass an env with CCW_HOOK_TOKEN removed. Update tests that pin the bare string.

#### Acceptance conditions

- AC1: the installed statusLine command is the absolute ccw path from the same resolver as the hook relay [evidence: test:tests/test_statusline_relay.py::test_statusline_command_is_absolute]
- AC2: an installed relay is recognised by basename and not installed twice [evidence: test:tests/test_statusline_relay.py::test_install_statusline_idempotent_by_basename]
- AC3: the chained user command does not receive CCW_HOOK_TOKEN [evidence: test:tests/test_statusline_relay.py::test_chain_env_drops_hook_token]

#### Files

- `src/claude_code_wrapper/statusline.py`
- `src/claude_code_wrapper/bootstrap/settings.py`
- `tests/test_statusline_relay.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The requirement above holds, pinned by the acceptance tests.

What is true and observable when the task is done.

#### Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S10: statusline input validation

- Status: done
- Files: `src/claude_code_wrapper/internal_api.py`, `README.md`, `tests/test_internal_api.py`
- Verify: `uv run pytest tests/test_internal_api.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 195bfaced052cb7ef199dc40e34ccbfc6cafe1c7

#### Requirement

Review + security finding (medium/low): parse_statusline (internal_api.py:43-60) only checks current_usage is a dict, so _derive_context's int(usage.get(key) or 0) raises ValueError/TypeError/OverflowError on non-numeric values and the route returns 500. Validate the token fields of current_usage and context_window as finite non-negative numbers in parse_statusline and return 400 otherwise; enforce a server-side request body cap on POST /internal/statusline (matching the client's MAX_STDIN 4096 bytes) with 413. Also add to README 'Trust model' that user_message events carry prompt text and file names into the event log, SSE and history (redacted by the configured redactor only).

#### Acceptance conditions

- AC1: non-numeric or non-finite token values return 400, not 500 [evidence: test:tests/test_internal_api.py::test_statusline_rejects_non_numeric_usage]
- AC2: a body over the cap returns 413 [evidence: test:tests/test_internal_api.py::test_statusline_body_cap]
- AC3: README Trust model documents user_message content in history [evidence: test:tests/test_readme_api.py]

#### Files

- `src/claude_code_wrapper/internal_api.py`
- `README.md`
- `tests/test_internal_api.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The requirement above holds, pinned by the acceptance tests.

What is true and observable when the task is done.

#### Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S11: vocabulary pins

- Status: done
- Files: `tests/test_command_vocabulary.py`, `tests/test_event_log.py`, `src/claude_code_wrapper/hooks.py`, `src/claude_code_wrapper/events.py`
- Verify: `uv run pytest tests/test_command_vocabulary.py tests/test_event_log.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 4d1989edeb1f30843536f0ab583b5d2d5484c445

#### Requirement

The epic full suite fails 2 exact-vocabulary pin tests (1576 passed): tests/test_command_vocabulary.py::test_hook_events_include_command_hooks and tests/test_event_log.py::test_event_types_exact. Read each assertion against the code: where the new vocabulary is intended (onStart instance hook event from on-start-instance-hook; user_message and context event types from user-message-event and context-in-snapshot-and-sse), update the pinned lists; where the code broke an invariant the pin protects (for example onStart wrongly listed as a command hook), fix the code instead. State which applied for each in the notes. Full-suite log: /private/tmp/claude-501/-Users-szymonri-Documents-claude-code-tatara/21d1a847-8d6b-4ee4-a271-ba52ec27cf3b/scratchpad/orch/run-claude-code-wrapper-orchestr/full-suite.log.

#### Acceptance conditions

- AC1: the hook-event vocabulary pin passes and matches the intended vocabulary [evidence: test:tests/test_command_vocabulary.py::test_hook_events_include_command_hooks]
- AC2: the event-type vocabulary pin passes and includes user_message and context [evidence: test:tests/test_event_log.py::test_event_types_exact]

#### Files

- `tests/test_command_vocabulary.py`
- `tests/test_event_log.py`
- `src/claude_code_wrapper/hooks.py`
- `src/claude_code_wrapper/events.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The wrapper full suite is green.

What is true and observable when the task is done.

#### Steps

- Red already seen in the epic full suite (assert 21 == 20; event list diff at context).
- Reconcile pins or code per the requirement; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Ruling

- 2026-10-22 accepted: false gate-repeat: verifier hit a stale pytest assertion-rewrite .pyc (20->21 edit keeps file size, cache reused). Hand-verified on 4d1989e after deleting the .pyc: 'uv run pytest tests/test_command_vocabulary.py tests/test_event_log.py -p no:cacheprovider' -> 31 passed; ruff check and format clean. Red is in the epic full-suite log (assert 21 == 20).

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none

## Rulings (migrated)

- idle-since-in-snapshot: accept true, at 2026-10-22T22:37:28Z: land-failed was suite-lock contention (lock held 1200s by the template epic close, pid 79691), not a code failure; task verified on 9961bc9 (11 passed, ruff clean). Process gap recorded: tests written after the implementation (no red run); the tests exercise the behaviour.
- vocabulary-pins: accept true, at 2026-10-22T23:17:41Z: false gate-repeat: verifier hit a stale pytest assertion-rewrite .pyc (20->21 edit keeps file size, cache reused). Hand-verified on 4d1989e after deleting the .pyc: 'uv run pytest tests/test_command_vocabulary.py tests/test_event_log.py -p no:cacheprovider' -> 31 passed; ruff check and format clean. Red is in the epic full-suite log (assert 21 == 20).
