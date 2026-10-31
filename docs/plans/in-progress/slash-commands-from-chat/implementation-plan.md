# slash commands from chat implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: orch slash parser

- Status: done
- Files: `src/agents_orchestrator/slash.py`, `tests/test_slash.py`
- Verify: `uv run --frozen pytest tests/test_slash.py && mise run lint`
- Verified head: a84881031646a982f088104d8281ca1b1bd3b560

#### Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards." Goal G2, verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."

Design D1, verbatim (the parser part): "[both routes] call one new `agents_orchestrator.slash.parse(text) -> tuple[str, str] | None` and store the message with `kind = 'command'` when it matches, else `kind = 'turn'`."

Design D2, verbatim: "Slash text mirrors Claude Code's own parser (claude 2.1.304 binary, interrogate item 2). After leading whitespace the text starts with `/`. A trailing agents-common run marker (`<!-- agents-<kind>:<id> -->`, `agents_common.runs.marker`, posted as `text\n\nmarker` by `runs.py:_post_once`) is removed first (interrogate item 8). The name is the text after the `/` up to the first whitespace (space, tab or newline); the args are the rest, stripped, and may span lines. The text is a command when the name is empty (`/`, `/ is root`: claude answers "Commands are in the form `/command [args]`" and calls no model; the wrapper refuses an empty name 422 `invalid_command`) or matches `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, with no length cap (`/tmp`, `/_x`, a 100-character name: claude runs it or answers "Unknown command", again with no model call, so a bare `/tmp` fails `unknown_command`). A name with any other character is prose (`/workdir/foo is broken`, `/etc/hosts`, `//x`, `/notes.txt`): claude sends it to the model as a prompt. The orchestrator classifies with this rule and the wrapper's turn guard (D3) refuses with the same rule, both pinned by one shared case table, so a text that claude would parse as a command can never be typed as a turn. The path-like prose leg is confirmed by a real-binary probe in task wrapper-command-signals; a result that contradicts this rule is reported back and amends both parser tasks, never worked around."

Interrogate item 2 (interrogate.md), verbatim: "Classification must match Claude Code's own parser (B, critical). D2 types `/`, `/ is root`, `/_x` and names over 64 chars as turns; claude runs no model call for them, so no Stop and the session hangs. Mirror the binary: name = text up to the first whitespace, empty name is `invalid_command` (claude: "Commands are in the form `/command [args]`"), unknown-command regex `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap. Fix wrapper-slash-turn-guard ac3 and orch-slash-parser ac2. Path-like prose (`/workdir/foo is broken`) must be pinned either way after a probe."

Interrogate item 8, verbatim: "Multi-line slash text and existing callers (C). agents-common runs.py:151 posts `text\n\nmarker`; a preset prompt starting with `/` used to run and would now fail `invalid_command`. Strip the ccw marker before classifying and accept multi-line args (pasted) up to a cap; test the marker-suffixed case."

User decision (builder check), verbatim: "a bare '/word' message such as '/tmp' is a command that fails unknown_command, while '/etc/hosts'-like paths stay prose (per the parser rule of item 2, after the probe)."

Scope (agents-orchestrator): new module `src/agents_orchestrator/slash.py` with `parse`, and `tests/test_slash.py`. Pure, no database. `parse` returns `("", args)` for an empty name (the wrapper refuses it `invalid_command`, D10 fails the message with that code); it never rejects on args length (the wrapper's `MAX_COMMAND_ARGS` applies). The marker pattern is written in `slash.py` with a comment naming `agents_common.runs.marker` as its source (the orchestrator does not depend on agents-common).

#### Acceptance conditions

- ac1: parse returns (name, args) for "/reload-plugins", "  /compact keep the plan", "/workbench:start-development x", "/model sonnet", "/_x", "/tmp", a 100-character name and a multi-line "/x a\nb" (args "a\nb") (new) [evidence: test:tests/test_slash.py::test_parse_slash_commands]
- ac2: parse returns ("", "") for "/" and ("", "is root") for "/ is root" (empty name: a command the wrapper refuses invalid_command) (new) [evidence: test:tests/test_slash.py::test_parse_empty_name_is_command]
- ac3: parse returns None for prose, "/workdir/foo is broken", "/etc/hosts", "//x", "/notes.txt" and text where the slash is not first ("see /compact") (new) [evidence: test:tests/test_slash.py::test_parse_leaves_prose]
- ac4: a trailing agents-common run marker is removed before classifying: "/review-pr 12\n\n<!-- agents-webhook:42 -->" gives ("review-pr", "12") and "/compact\n\n<!-- agents-schedule:7 -->" gives ("compact", ""); a marker-like comment that is not trailing stays in the args (new) [evidence: test:tests/test_slash.py::test_parse_strips_trailing_run_marker]
- ac5: the test file and lint pass without a database [evidence: command:uv run --frozen pytest tests/test_slash.py && mise run lint]

#### Files

- `src/agents_orchestrator/slash.py`
- `tests/test_slash.py`

#### Interfaces

- `agents_orchestrator.slash.parse(text: str) -> tuple[str, str] | None`: `(name, args)`; `name` without the slash, `""` for an empty name; args with a trailing run marker removed, newlines kept.

#### Expected outcome

One function decides, for both message routes, whether a text is a slash command, with the same rule the wrapper's turn guard uses.

#### Steps

- Red: write `tests/test_slash.py` (ac1-ac4); run `uv run --frozen pytest tests/test_slash.py`: import error.
- Green: write `slash.py`; run the task's verify: passes. Quote the summary line.

#### Notes

- Keep the case table identical to the wrapper's guard tests in task wrapper-slash-turn-guard (`test_slash_rule_matches_claude_parser`, `test_slash_rule_leaves_paths_and_prose`), so the two sides cannot drift (retro proposal of generic-any-mcp-with-git-and: one shared parity table).
- Docker-free: runs in this container.

- 2026-10-27 amended: interrogate items 2 and 8 (parser mirrors claude: empty name is a command, name regex with no length cap, paths stay prose; trailing run marker stripped, multi-line args), builder check (/tmp is a command), design D2 revised

- 2026-10-27 done

### S2: orch wrapper command client

- Status: done
- Files: `src/agents_orchestrator/wrapper/client.py`, `src/agents_orchestrator/wrapper/models.py`, `src/agents_orchestrator/wrapper/__init__.py`, `src/agents_orchestrator/dispatcher/loop.py`, `tests/test_wrapper_client.py`, `tests/fakes/fake_wrapper.py`, `tests/test_fake_wrapper_contract.py`, `tests/test_dispatcher.py`
- Verify: `uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py && mise run lint`
- Verified head: 85cd446f37647b73a97a8f1e74326522f0236c38

#### Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D10, verbatim (the client part): "`WrapperClient.command(session_id, name, args)` returns `CommandOutcome = CommandAccepted(command_id, record) | Busy | ConfigError | Rejected(code, reason) | Gone | Unavailable | Ambiguous`; the existing `/agents/{id}/compact` path keeps its `done {response: record}` result."

Design D5, verbatim (the parts this fake mirrors): "`sessions.commands.deny: list[str]`, default (my call, interrogate item 5) `[exit, quit, clear, reset, new, resume, continue, branch, fork, cd, background, bg, teleport, tp, stop, remote-control, rc, restart, update, login, logout, upgrade, setup-bedrock, setup-vertex, web-setup, design-login]` (`DEFAULT_COMMAND_DENY` in `config.py`), matched case-insensitively (`/EXIT`, `/Clear` are denied), checked before the allowlists: 403 `command_denied`. [...] the orchestrator's fake wrapper copies it with a comment naming the source". D2 name pattern (interrogate item 2): `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap; an empty name is refused 422 `invalid_command`.

Design "Left to the builder", verbatim: "Fake wrapper (orchestrator) command timing model, as long as it emits `command_queued`, `command_started`, `command_completed` with the record shape of the real wrapper and runs a command queued during a turn after that turn completes."

Discovery fix-as-ac (agents-orchestrator.md), verbatim: "fake wrapper `/commands` ignores the per-origin allowlist (tests/fakes/fake_wrapper.py:641-649), hiding that refusal from unit tests" and "`WrapperClient.command` sends only `{"name"}`, no args (wrapper/client.py:198-200)".

Scope (agents-orchestrator):
- `wrapper/client.py`: `command(session_id, name, args="") -> CommandOutcome`, POST `{name, args}` with the send timeout; 202 -> `CommandAccepted(record["id"], record)`; 409 -> `Busy` (booting, dead, carrying the code); 429 -> `Busy` (code `command_queue_full`); 401 -> `ConfigError`; 403 and 422 -> `Rejected(code, reason)`; 404/410 -> `Gone`; connect errors -> `Unavailable`; read timeout, 500, 502 -> `Ambiguous`; other 5xx -> `Unavailable`.
- `wrapper/models.py` and `wrapper/__init__.py`: `CommandAccepted`, `CommandOutcome`, and a `code` on `Rejected` and `Busy` where the wrapper sent one.
- `dispatcher/loop.py:_run_command` (the agents commands table path for compact): `CommandAccepted` -> `("done", {"response": record})`, any other outcome -> `("failed", {"error": <reason>})`.
- `tests/fakes/fake_wrapper.py`: `POST /v1/sessions/{id}/commands` takes any D2-pattern name and string args, enforces a settable client allowlist (default `["*"]`) and a copy of the wrapper's `DEFAULT_COMMAND_DENY` (the 26 names of D5, matched case-insensitively, with a comment naming `claude_code_wrapper.config.DEFAULT_COMMAND_DENY` as the source) (403 `command_denied`, 403 `command_not_allowed`, 422 `invalid_command` for an empty or non-pattern name), answers 202 with the real record shape (`id`, `name`, `args`, `origin` "client", `state` "queued", `turn_id`), and emits `command_queued`, `command_started`, `command_completed` (`data.record`); on an idle session it runs at once (state busy, then ready), during a turn after that turn completes.
- `tests/test_fake_wrapper_contract.py`: one contract case for both legs (the real leg is `-m integration`).

Tests no longer accurate (named): `tests/test_wrapper_client.py::test_sessions_and_control_methods` pins `command()` returning the response JSON dict and the body `{"name"}`; it now asserts `{name, args}` and a `CommandAccepted`. `tests/test_dispatcher.py::test_interrupt_and_compact_commands` keeps its assertions if the result shape `{"response": record}` holds; it changes only where it reads the fake's old `command_id` key.

#### Acceptance conditions

- ac1: command() posts {name, args} and maps 202, 409, 429, 401, 403, 422, 404, connect error, read timeout, 500 and 503 to the D10 outcomes (new) [evidence: test:tests/test_wrapper_client.py::test_command_outcomes]
- ac2: the control-methods test asserts the new body and outcome (updated) [evidence: test:tests/test_wrapper_client.py::test_sessions_and_control_methods]
- ac3: contract, both legs: POST /commands with any allowed name and args answers 202 with id, name, args and state queued; {name: exit} and {name: Reset} answer 403 command_denied; {name: ""} answers 422 invalid_command (new; the real leg runs with -m integration in CI or on a Docker host after orch-wrapper-pin-0-4-0) [evidence: test:tests/test_fake_wrapper_contract.py::test_commands_any_name_and_denied]
- ac4: the fake emits command_queued, command_started and command_completed with the record, at once when idle and after the running turn completes otherwise (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_command_events_and_turn_ordering]
- ac5: (Docker) the agents compact command still ends done with the wrapper record as response [evidence: test:tests/test_dispatcher.py::test_interrupt_and_compact_commands]
- ac6: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py && mise run lint]

#### Files

- `src/agents_orchestrator/wrapper/client.py`
- `src/agents_orchestrator/wrapper/models.py`
- `src/agents_orchestrator/wrapper/__init__.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `tests/test_wrapper_client.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`
- `tests/test_dispatcher.py`

#### Interfaces

- `WrapperClient.command(session_id: str, name: str, args: str = "") -> CommandOutcome`.
- `CommandAccepted(command_id: str, record: dict)`; `CommandOutcome = CommandAccepted | Busy | ConfigError | Rejected | Gone | Unavailable | Ambiguous`; `Rejected.code`, `Busy.code`.
- Fake wrapper: `FakeWrapper.commands_client: list[str]` (default `["*"]`), deny list = the wrapper's `DEFAULT_COMMAND_DENY` names.

#### Expected outcome

The orchestrator can send any slash command with args to a wrapper and knows exactly what happened; its fake behaves like the real wrapper on the commands route, so dispatcher tests see refusals.

#### Steps

- Red: add ac1, ac3, ac4, update ac2; run `uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py`: they fail.
- Green: client, models, exports, `_run_command`, the fake; run the task's verify: passes. Quote the summary line.

#### Notes

- The real leg of ac3 pins the fake's record shape against the real wrapper image (retro proposal: fakes checked against real output). It needs the 0.4.0 pin (orch-wrapper-pin-0-4-0) and `client: ["*"]` in `e2e/agent-test.config.yaml`; until then only the fake leg runs.
- The fake imports nothing from claude_code_wrapper at runtime if it does not today; copy the design D5 deny names (26 since the interrogate revision) with a comment naming `claude_code_wrapper.config.DEFAULT_COMMAND_DENY` as the source, and match them case-insensitively.
- No dependency inside the epic.

- 2026-10-27 amended: interrogate items 5 and 2 (the fake copies the revised DEFAULT_COMMAND_DENY, matches it case-insensitively and refuses an empty name invalid_command), design D5 revised

- 2026-10-27 done

### S3: plugin session send slash

- Status: done
- Files: `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`, `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- Verify: `uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 932d12e3d93c482514ca2f5ccfcaa35d6ef5419d

#### Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."

Design D13, verbatim: "any-mcp-tatara-plugins `orchestration/orchestrator` `_descriptions()["session_send"]` adds: "When your session is a superleader, text that starts with a slash command such as /compact runs as a Claude Code slash command on the target session's leader (not framed); commands that end or replace a session, such as /exit or /clear, are refused. From any other session it is delivered as a message." (my call, matching D1 after interrogate item 1). It names no full list (D5 keeps the list in one place)."

Interrogate item 1 (interrogate.md), verbatim (why the sentence names the superleader): "Store `kind='command'` only when the sender's session has `session_messaging`; otherwise the text stays a framed turn."

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py` (`_descriptions` session_send text), `orchestration/orchestrator/tests/test_orchestrator_plugin.py` (`test_descriptions_from_config` asserts the new sentence). The release of this change is task plugins-release-0-2-0.

#### Acceptance conditions

- ac1: the session_send description says a superleader's slash text runs as a Claude Code slash command on the target's leader, that session-ending commands are refused and that from other sessions it is a message, and names no full deny list (updated) [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_descriptions_from_config]
- ac2: the plugin tests and lint pass [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`

#### Interfaces

- `orchestrator_session_send` tool description text (no schema change).

#### Expected outcome

A superleader agent reading its tool list knows that "/x" sent to another session runs as a command there.

#### Steps

- Red: add the assertions to `test_descriptions_from_config`; run it: fails.
- Green: change the description; run the task's verify: passes. Quote the summary line.

#### Notes

- The description reaches agents only through a plugins release and the orchestrator's `ORCH_ANY_MCP_PLUGINS_REF` pin (`v0.1.0` today): tasks plugins-release-0-2-0 and orch-plugins-pin-0-2-0 (builder check).
- No dependency inside the epic.

- 2026-10-27 amended: interrogate item 1 (the description says only a superleader's slash text runs as a command), design D13 revised

- 2026-10-27 done

### S4: web command rows

- Status: done
- Files: `src/chat/chatModel.ts`, `src/chat/entries.tsx`, `src/chat/chatModel.test.ts`, `src/chat/ChatLog.test.tsx`
- Verify: `npx vitest run src/chat/chatModel.test.ts src/chat/ChatLog.test.tsx src/layout/designRules.test.ts && npm run lint`
- Verified head: 24e6911363fc1ba04c254a883d21cb77bc047917

#### Requirement

Goal G4 (README), verbatim: "The chat shows the command and its outcome." Non-goal, verbatim: "No slash-command autocomplete or picker in the composer."

Design D12, verbatim: "agents-web `chatModel.ts` adds a `command` ChatItem `{commandId, name, args, status, result?, error?, output?}` built from `command_queued`, `command_started`, `command_completed`, `command_failed` event rows (`data.record`), updated in place by `record.id` (tool-row pattern): status `queued` -> `running` -> `completed` (with result ok | dismissed | skipped_cache | turn) or `failed` (with error) or `cancelled`. `entries.tsx` renders it with the label `command`, the line `/name args`, the status and the output in a mono `<pre>`. Ruling (my call): `user_message` rows with origin `command` (the typed-line echo) are folded into the command row and not rendered on their own, so a command shows once. A promoted prompt command also shows its normal turn rows. A command the orchestrator could not deliver shows in QueueStrip as failed with the wrapper code (D10). Composer is unchanged (non-goal: no picker)."

Wrapper event shape (claude-code-wrapper `router.py:_emit_command`): `{"type": "command_queued" | "command_started" | "command_completed" | "command_failed", "data": {"record": {"id", "name", "args" (string), "origin", "turn_id", "state" (queued | running | completed | failed | cancelled), "result", "error", "output", ...}}}`; a cancelled record arrives as `command_failed` with `state: "cancelled"`.

Scope (agents-web): `src/chat/chatModel.ts`, `src/chat/entries.tsx`, `src/chat/chatModel.test.ts`, `src/chat/ChatLog.test.tsx`.

Test no longer accurate (named): `src/chat/chatModel.test.ts` "maps event types to item kinds" expects a `user_message` row with origin `command` to become a `user_message` item (row 4); under the D12 ruling that row yields no item.

#### Acceptance conditions

- ac1: command_queued, command_started, command_completed rows of one record id become one command item that goes queued, running, completed with result and output, in any arrival order within a batch and across batches (new) [evidence: test:src/chat/chatModel.test.ts::command row lifecycle]
- ac2: command_failed gives status failed with the error, or cancelled when the record state is cancelled (new) [evidence: test:src/chat/chatModel.test.ts::command row failure and cancel]
- ac3: a user_message row with origin command yields no item; other origins are unchanged (updated) [evidence: test:src/chat/chatModel.test.ts::maps event types to item kinds]
- ac4: ChatLog renders the command row: label command, the line "/reload-plugins", the status and the output in a pre (new) [evidence: test:src/chat/ChatLog.test.tsx::renders command row]
- ac5: the design rules and nomenclature guards stay green [evidence: command:npx vitest run src/layout/designRules.test.ts src/nomenclature.test.ts]
- ac6: targeted tests and lint pass [evidence: command:npx vitest run src/chat/chatModel.test.ts src/chat/ChatLog.test.tsx src/layout/designRules.test.ts && npm run lint]

#### Files

- `src/chat/chatModel.ts`
- `src/chat/entries.tsx`
- `src/chat/chatModel.test.ts`
- `src/chat/ChatLog.test.tsx`

#### Interfaces

- `ChatItem` variant `Base & { kind: 'command'; commandId: string; name: string; args: string; status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'; result?: string; error?: string; output?: string }`.

#### Expected outcome

A slash command sent from the chat appears as one row that updates from queued to its outcome, with claude's output when there is any.

#### Steps

- Red: add the chatModel and ChatLog tests (ac1, ac2, ac4), update ac3; run `npx vitest run src/chat/chatModel.test.ts src/chat/ChatLog.test.tsx`: they fail.
- Green: chatModel.ts and entries.tsx; run the task's verify: passes. Quote the vitest summary line.

#### Notes

- Reuse the tool-row pairing pattern (`chatModel.ts` merge: update items already in the window, keep the earliest eventId as the row position).
- Status colours come from theme tokens (`STATUS_COLOUR` pattern in entries.tsx); no colour literals, no arrows (designRules).
- Ruling pinned by ac3: the typed-line echo folds into the command row.
- Run only the chat test files: the full suite has 10 load-dependent timeouts here (design Constraints).
- No dependency inside the epic (the event shape is the wrapper's existing one; `args` becomes a string with wrapper-command-args).

- 2026-10-27 done

### S5: wrapper command policy

- Status: done
- Files: `src/claude_code_wrapper/config.py`, `src/claude_code_wrapper/commands.py`, `src/claude_code_wrapper/metrics.py`, `src/claude_code_wrapper/router.py`, `src/claude_code_wrapper/api/commands.py`, `README.md`, `tests/test_command_registry.py`, `tests/test_api_commands.py`
- Verify: `uv run pytest tests/test_command_registry.py tests/test_api_commands.py tests/test_command_vocabulary.py tests/test_readme_config.py tests/test_readme_api.py tests/test_slash_review_fixes.py tests/test_command_runner.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: f03cf5000bce9f032468fb5bf6dbc332e1a41120

#### Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D5, verbatim: "`sessions.commands.deny: list[str]`, default (my call, interrogate item 5) `[exit, quit, clear, reset, new, resume, continue, branch, fork, cd, background, bg, teleport, tp, stop, remote-control, rc, restart, update, login, logout, upgrade, setup-bedrock, setup-vertex, web-setup, design-login]` (`DEFAULT_COMMAND_DENY` in `config.py`), matched case-insensitively (`/EXIT`, `/Clear` are denied), checked before the allowlists: 403 `command_denied`. Aliases are listed by name from claude's own alias table (binary grep, 2026-10-27: clear `reset`, `new`; resume `continue`; exit `quit`; restart `update`; background `bg`; teleport `tp`; remote-control `rc`), each pinned by a test, so the list stays one config value with no alias resolver. `sessions.commands.agent|client` accept names (D2 pattern) or `"*"`; `timeout_seconds` keys are free names or `default`; `CommandsOverride` mirrors `deny`. A gate change to the deny list is an amend of this one default and its pins (user decision 2)." The per-name reasons are design.md D5's table.

Interrogate item 5 (interrogate.md), verbatim: "Deny list misses aliases and session-moving commands (B, C). Add `reset`, `new` (clear), `continue` (resume), `update` (restart), `cd`; match case-insensitively; resolve aliases from claude's table, pin each with a test. Review the rest of cmdtable.txt (`background`, `teleport`, `stop`, `session`, `remote-control`, `upgrade`) and record each as denied or allowed with the reason."

User decision, verbatim: "Keep the deny list as one config value".

Design D15, verbatim: "`metrics.py` keeps a fixed label set `METRIC_COMMAND_NAMES` (compact, context, mcp, reload-plugins, reload-skills) and counts every other name as `other`, so arbitrary names cannot grow the label cardinality."

D2 name pattern (design D2, interrogate item 2): `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$` (full match, no length cap).

Scope (claude-code-wrapper):
- `config.py`: remove `BUILTIN_COMMAND_NAMES`; add the D2 name pattern as a module constant; `_check_command_names` accepts a name matching the pattern or `"*"`; `_check_command_timeouts` accepts a pattern name or `default`; `CommandsConfig.deny: list[str]` defaulting to `DEFAULT_COMMAND_DENY` (the 26 names above, pattern names, no `"*"`); `CommandsOverride.deny: list[str] | None`.
- `commands.py`: `CommandQueue.request` checks, for origins agent and client, the name lowercased against the lowercased deny list first (`CommandRejected("denied", ...)`), then the allowlist (`"*"` admits every name); origin idle stays compact only. Drop the `assert` that ties `BUILTIN_COMMANDS` to `BUILTIN_COMMAND_NAMES`. `validate_params` and the five-name registry stay in this task (task wrapper-command-args replaces them).
- `router.py`: `request_command` drops its duplicate `validate_params` call before the state check, so the queue's order deny, allowlist, validation holds.
- `metrics.py`: `METRIC_COMMAND_NAMES` as in D15.
- `api/commands.py`: `_REJECT["denied"] = (403, "command_denied")`.
- `README.md`: Configuration reference rows for `sessions.commands.deny` (the default list, case-insensitive matching; the agent/client rows say "names or `*`"), the Errors table row `command_denied`, `### Configuration` of `## Slash commands` mentions the deny list.

Tests no longer accurate (named): `tests/test_command_registry.py::test_unknown_command_name_rejected_at_config` and `::test_unknown_client_and_timeout_key` assert that a name outside the five built-ins is a config error; D5 makes names free-form. They are rewritten to assert that a name outside the D2 pattern (for example `rm -rf`, `-x`, `/clear`, `notes.txt`) is rejected with its config path, and that `timeout_seconds: {compact: 0}` still fails "must be greater than 0".

#### Acceptance conditions

- ac1: agent and client allowlists accept any D2-pattern name ("_x", a 100-character name) and "*", and a name outside the pattern ("rm -rf", "-x", "/clear", "notes.txt") is a config error naming its path (new) [evidence: test:tests/test_command_registry.py::test_command_names_free_form_and_wildcard]
- ac2: sessions.commands.deny defaults to exactly the 26 names of design D5, and a per-session override replaces it (new) [evidence: test:tests/test_command_registry.py::test_deny_list_default_and_override]
- ac3: each alias of claude's table is denied by name: reset and new (clear), continue (resume), quit (exit), update (restart), bg (background), tp (teleport), rc (remote-control), and cd, stop, upgrade, setup-bedrock, setup-vertex, web-setup, design-login are denied; session and its alias remote are allowed (new) [evidence: test:tests/test_command_registry.py::test_deny_list_covers_aliases_and_session_moving_commands]
- ac4: the deny match is case-insensitive: EXIT, Clear and Reset are denied with code denied (new) [evidence: test:tests/test_command_registry.py::test_deny_is_case_insensitive]
- ac5: a denied name is refused with code denied even when the allowlist is "*" or names it; "*" admits any other name (new) [evidence: test:tests/test_command_registry.py::test_deny_checked_before_allowlist]
- ac6: POST /v1/sessions/{id}/commands {name: exit} and {name: Reset} with client ["*"] answer 403 command_denied, queue nothing and emit no event (new) [evidence: test:tests/test_api_commands.py::test_denied_command_403]
- ac7: with client ["*"] POST /v1/sessions/{id}/commands {name: context} answers 202 (new) [evidence: test:tests/test_api_commands.py::test_wildcard_client_allowlist]
- ac8: the commands metric label stays bounded to the five names plus other [evidence: test:tests/test_command_vocabulary.py::test_command_metrics_bounded]
- ac9: every config key, deny included, is documented with its default [evidence: test:tests/test_readme_config.py::test_defaults_match_model]
- ac10: the README Errors table lists command_denied [evidence: command:grep -q '^| `command_denied`' README.md]
- ac11: no BUILTIN_COMMAND_NAMES left in src, and the deny names are written only in config.py [evidence: command:! grep -rn BUILTIN_COMMAND_NAMES src && test "$(grep -rln '"remote-control"' src)" = "src/claude_code_wrapper/config.py"]
- ac12: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_registry.py tests/test_api_commands.py tests/test_command_vocabulary.py tests/test_readme_config.py tests/test_readme_api.py tests/test_slash_review_fixes.py tests/test_command_runner.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/commands.py`
- `src/claude_code_wrapper/metrics.py`
- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/api/commands.py`
- `README.md`
- `tests/test_command_registry.py`
- `tests/test_api_commands.py`

#### Interfaces

- `claude_code_wrapper.config.DEFAULT_COMMAND_DENY: tuple[str, ...]` (or list): the 26 names of design D5, the only place the deny list is written.
- `CommandsConfig.deny: list[str]`, `CommandsOverride.deny: list[str] | None`; `agent`, `client`: pattern names or `"*"`.
- `CommandRejected("denied", message)` -> HTTP 403 `command_denied` (`api/commands.py:_REJECT`).
- `metrics.METRIC_COMMAND_NAMES`.

#### Expected outcome

A session config can allow any command name or `"*"` for clients and agents; the session-ending, session-moving, account and credential commands of design D5, under any alias or letter case, are refused 403 `command_denied` before any allowlist; nothing else about running commands changes yet.

#### Steps

- Red: write the seven new tests (ac1-ac7) and rewrite the two inaccurate config tests; run `uv run pytest tests/test_command_registry.py tests/test_api_commands.py`: the new ones fail (unknown command, no deny key).
- Green: change config.py, commands.py, router.py, metrics.py, api/commands.py, README.md; run the task's verify: passes. Quote the pytest summary line with its counts.

#### Notes

- Ruling, pinned by ac5: deny is checked before the allowlist; a name in both deny and the allowlist is denied.
- Ruling, pinned by ac3 and ac4: aliases are listed by name (no alias resolver) and matched case-insensitively.
- `CommandsOverride` merges through `commands.effective_commands` (model_copy update): a set `deny` replaces the default, it does not extend it.
- `test_command_vocabulary.py::test_command_metrics_bounded` must stay green unchanged.
- No LSP: find every `BUILTIN_COMMAND_NAMES` use with `grep -rn BUILTIN_COMMAND_NAMES src tests` (config.py, commands.py, metrics.py today).

- 2026-10-27 amended: interrogate item 5 (aliases reset, new, continue, update, quit, bg, tp, rc; cd and the reviewed session-moving and account commands; case-insensitive; one config value) and item 2 (D2 name pattern), design D5 revised

- 2026-10-27 done

### S6: wrapper deny list extend 0.4.2

- Status: done
- Files: `src/claude_code_wrapper/config.py`, `README.md`, `config.example.yaml`, `tests/test_command_registry.py`
- Verify: `uv run pytest tests/test_command_registry.py tests/test_slash_commands_docs.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 24c2ce95dd865251a3200ece14c47416bc7872a0

#### Requirement

User decision PENDING (mx-34 #471 Q1-3, recommended yes to all; tatara #473 confirmed the version v0.4.2). The leader amends this paragraph with the user verbatim answer before the merge; nothing merges or is tagged before it. Questions, verbatim: "1) Deny the account or cloud group too? That means wrapper v0.4.2 (patch, after v0.4.1) before the slash deploy, about 1 h of agent time. Recommended: yes. 2) Also deny mcp, permissions, config and hooks in v0.4.2? Recommended: yes, so that chat cannot rewrite the session's tool and permission settings. 3) Bump the version to wrapper v0.4.2? Live is 0.3.3, v0.4.1 is tagged but not deployed, and v0.4.2 would replace it in the same deploy. Recommended: yes, pending tatara's confirmation."

Security re-review (.scratchpad/slash-fix-phase5/security.md), verbatim: "MEDIUM wrapper config.py:499: still allowed by client [\"*\"] and reaching account/cloud: privacy-settings, ultraplan, ultrareview, autofix-pr, cloud-plugins, session (alias remote). Names confirmed present in claude 2.1.304 binary by cct2-1. Local-settings commands also allowed: mcp, permissions/allowed-tools, config/settings, hooks."

Name check (cct2-1, claude 2.1.304 binary): privacy-settings, ultraplan, ultrareview, autofix-pr, cloud-plugins, mcp and hooks are commands; session has alias remote; permissions has alias allowed-tools; config has alias settings. None is in the current 51-name DEFAULT_COMMAND_DENY.

Scope (claude-code-wrapper, new branch slash-deny-v042 from origin/main eed2c3c):
- `src/claude_code_wrapper/config.py`: append the 13 names privacy-settings, ultraplan, ultrareview, autofix-pr, cloud-plugins, session, remote, mcp, permissions, allowed-tools, config, settings, hooks to `DEFAULT_COMMAND_DENY` (51 + 13 = 64), with the comment naming why (account/cloud reach; session tool and permission settings).
- README.md: the default deny list documented as the 64 names.
- `config.example.yaml`: the commented `deny:` line lists the 64 names in the same order.
- `tests/test_command_registry.py`: `test_deny_list_default_and_override` pins 51 names and is no longer accurate (named): update it to 64; add a test that each of the 13 is refused denied for agent and client origins in any letter case.

#### Acceptance conditions

- ac1: DEFAULT_COMMAND_DENY holds the 51 earlier names plus privacy-settings, ultraplan, ultrareview, autofix-pr, cloud-plugins, session, remote, mcp, permissions, allowed-tools, config, settings, hooks (64), override still extend-only (updated, named) [evidence: test:tests/test_command_registry.py::test_deny_list_default_and_override]
- ac2: with agent and client ["*"], each of the 13 added names is refused denied for both origins in any letter case ("Ultrareview", "MCP") (new) [evidence: test:tests/test_command_registry.py::test_deny_list_covers_account_and_settings]
- ac3: config.example.yaml's commented deny list equals DEFAULT_COMMAND_DENY [evidence: test:tests/test_slash_commands_docs.py::test_config_example_documents_command_keys]
- ac4: README names the added commands [evidence: command:grep -q "ultrareview" README.md && grep -q "allowed-tools" README.md]
- ac5: the named tests and lint pass [evidence: command:uv run pytest tests/test_command_registry.py tests/test_slash_commands_docs.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/config.py`
- `README.md`
- `config.example.yaml`
- `tests/test_command_registry.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

- 2026-10-29 actuals: no agent records

### S7: orch message kind

- Status: done
- Files: `src/agents_orchestrator/db/migrations/0008_slash_messages.sql`, `src/agents_orchestrator/db/queue.py`, `src/agents_orchestrator/db/views.py`, `src/agents_orchestrator/api/schemas.py`, `src/agents_orchestrator/api/messages.py`, `openapi.json`, `tests/test_api_messages.py`, `tests/test_migrations.py`
- Verify: `uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint`
- Verified head: f4c16fbdf6f84edb0659d79123a6df4abae58a14

#### Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D1, verbatim (as amended 2026-10-29: the migration number only): "`POST /api/v1/sessions/{id}/messages` (`api/messages.py:post_message`, the chat) and `POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:session_send`, the superleader) both call one new `agents_orchestrator.slash.parse(text) -> tuple[str, str] | None` and store the message with `kind = 'command'` when it matches, else `kind = 'turn'`. Migration `0010_slash_messages.sql` adds `messages.kind text NOT NULL DEFAULT 'turn' CHECK (kind IN ('turn', 'command'))` and `messages.wrapper_command_id text`. The stored text stays raw; `MessageView` gains `kind`. The `commands` table and its CHECK are untouched."

Amendment (2026-10-29, user-approved release order agreed between hives 2026-10-28): agents-orchestrator `main` now carries migrations `0008_wrapper_resume.sql` and `0009_created_by_service.sql` (the latter from the epic matrix-connector-agent-initi, merge a9f936f), so this epic's migration is `0010_slash_messages.sql`, not `0008_slash_messages.sql`. The epic's orchestrator branch `slash-commands-from-chat` (base with migrations up to 0007) is rebased onto orchestrator `main` before this task's commit. Where the frontmatter `files`, the Files section and the Steps below still name `0008_slash_messages.sql` or "migration 0008" (written before this amendment), they mean `0010_slash_messages.sql` and migration 0010.

Scope (agents-orchestrator), the chat route (the superleader route is task orch-session-send-command):
- `src/agents_orchestrator/db/migrations/0010_slash_messages.sql`: the two columns, idempotent (`ADD COLUMN IF NOT EXISTS`, like 0006 to 0009).
- `db/queue.py`: `enqueue_message(..., kind: str = "turn")` writes `kind`.
- `db/views.py`: `_MESSAGE_SELECT` returns `m.kind` and `m.wrapper_command_id`.
- `api/schemas.py`: `MessageView.kind: Literal["turn", "command"]`, `MessageView.wrapper_command_id: str | None`.
- `api/messages.py:post_message`: `kind = "command" if slash.parse(body.text) else "turn"`.
- `openapi.json` regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`) on the rebased branch, so it carries main's API changes too.

Tests no longer accurate (named): on orchestrator `main`, `tests/test_migrations.py::test_fresh_database_gets_all_tables` pins the applied versions to 0001-0009, `::test_presets_migration_on_existing_sessions` to 0002-0009 and `::test_0005_renames_clusters_to_sessions` to 0005-0009; each gains `0010`.

#### Acceptance conditions

- ac1: (Docker: CI or a Docker host) POST /api/v1/sessions/{id}/messages {text: "/reload-plugins"} answers 202 and stores kind command with the raw text (new) [evidence: test:tests/test_api_messages.py::test_slash_text_enqueues_command_kind]
- ac2: (Docker) prose stores kind turn and GET /api/v1/messages/{id} returns kind and wrapper_command_id (new) [evidence: test:tests/test_api_messages.py::test_message_view_has_kind]
- ac3: (Docker) migration 0010 applies on a fresh database after 0001-0009 and on rerun (updated) [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- ac4: (Docker) an existing database migrates through 0010 (updated) [evidence: test:tests/test_migrations.py::test_presets_migration_on_existing_sessions]
- ac5: (Docker) the 0005 upgrade path runs on through 0010 (updated) [evidence: test:tests/test_migrations.py::test_0005_renames_clusters_to_sessions]
- ac6: the migration is numbered 0010 after main's 0009, and no 0008_slash_messages.sql is tracked [evidence: command:test -n "$(git ls-files src/agents_orchestrator/db/migrations/0009_created_by_service.sql)" && test -n "$(git ls-files src/agents_orchestrator/db/migrations/0010_slash_messages.sql)" && test -z "$(git ls-files src/agents_orchestrator/db/migrations/0008_slash_messages.sql)"]
- ac7: openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac8: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

#### Files

- `src/agents_orchestrator/db/migrations/0008_slash_messages.sql`
- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/db/views.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/messages.py`
- `openapi.json`
- `tests/test_api_messages.py`
- `tests/test_migrations.py`

#### Interfaces

- `messages.kind text NOT NULL DEFAULT 'turn' CHECK (kind IN ('turn','command'))`, `messages.wrapper_command_id text`.
- `queue.enqueue_message(conn, session_id, text, target_agent_id=None, *, kind="turn", sender_session_id=None, sender_slug=None, hop=0) -> int`.
- `MessageView.kind`, `MessageView.wrapper_command_id`.

#### Expected outcome

A chat message starting with a slash command is stored as a command message; the queue view and the API expose its kind.

#### Steps

- Red: add ac1 and ac2, update the migrations version list; on a Docker host run `uv run --frozen pytest tests/test_api_messages.py tests/test_migrations.py`: they fail. In this container only ac4 and ac5 run.
- Green: migration, queue, views, schemas, route, openapi.json; run the task's verify: passes. Quote the summary line; the Docker legs run in CI.

#### Notes

- The api module may import `agents_orchestrator.slash` (no wrapper import: the layering pin `tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper` must stay green).
- Text is stored raw; never rewrite it (agents-orchestrator.md do-not-build).
- Depends on orch-slash-parser.

- 2026-10-29 amended: orchestrator main now has migrations 0008_wrapper_resume and 0009_created_by_service (matrix-connector-agent-initi merged first, user-approved order): migration renumbered 0010_slash_messages.sql, three migration version-list tests named, branch rebases onto main

- 2026-10-29 done

### S8: orch slash js whitespace

- Status: done
- Files: `src/agents_orchestrator/slash.py`, `tests/test_slash.py`, `README.md`
- Verify: `uv run --frozen pytest tests/test_slash.py tests/test_readme_api.py && mise run lint`
- Verified head: f681026b0629bfa12e2f80862d3669aba6059f34

#### Requirement

User decision F1 (2026-10-29), verbatim: "F1 (security): both slash parsers adopt claude's JS whitespace set and skip invisible Cc/Cf characters as the architect specifies, including the ESC hole and the Session.probe guard; wrapper release v0.4.1 (tag approved by the user and mx-34 #432; the orchestrator session pushes it after merge) and an orchestrator pin to it; amend D2."

Architect brief (`/workdir/workdir/.scratchpad/slash-fix-design.md`), verbatim:

"**F1: exact character rules (identical code in both repos)**
- **Whitespace (W):** exactly JS `\s`, which is the same set as JS `trim`. Checked under node v24: U+0009-000D, 0020, 00A0, 1680, 2000-200A, 2028, 2029, 202F, 205F, 3000, FEFF. Python's `isspace` differs: it adds U+001C-001F and U+0085, and it lacks U+FEFF.
- **Ignorable (D):** every other character in Unicode categories Cc or Cf. This includes ESC, NUL, DEL, C1, U+001C-001F, U+0085, zero-width and bidi characters. In the leading run and inside the name these are deleted before classifying.
- **Parse steps:**
  1. Remove the run marker.
  2. Skip leading W and D characters.
  3. Require `/`.
  4. The name runs to the first W character, with D characters dropped from it.
  5. The args are the rest, stripped of W only.
  6. The existing name regex applies unchanged.
- **Python's extra stripping must change:** stop using `lstrip()`, `strip()` and `\s` everywhere in the parser. U+001C-001F are still skipped when leading, but they no longer split the name.
- This leans toward calling more text a command, which design D2 already treats as the safe direction. The orchestrator then sends the cleaned name.
- Normalising in the orchestrator alone is not enough: direct wrapper clients, the initial prompt and the probe all bypass it."

"2. `orch-slash-js-whitespace` (agents-orchestrator): `slash.py` and `tests/test_slash.py`, with the same case table. Can run in parallel with task 1.
   - New cases: `"/exit x"`, `"/clear\x0bx"`, `"/login\rx"`, `"﻿/login"`, `"/exit　"`, `"\x1b/exit"`, `"/ex\x1bit"`, `"/ex​it"`, `"\x1c/exit"`, `"/exit\x1cx"` giving `("exitx","")`.
   - Prose stays prose: `"x /exit"`, `"/etc/hosts x"`."

Design D2 (amended 2026-10-29) names the set; the orchestrator keeps one case table with the wrapper's (task wrapper-slash-js-whitespace).

Scope (agents-orchestrator, epic branch in `/workdir/workdir/.claude/worktrees/slash-commands-from-chat/agents-orchestrator`): `src/agents_orchestrator/slash.py` (`parse` per the parse steps; the dispatcher already sends `parse`'s name and args, so the cleaned name reaches the wrapper), `tests/test_slash.py`, README.md (the two places that describe slash text, `POST /api/v1/sessions/{id}/messages` and `orchestrator_session_send`, say leading whitespace and invisible characters are skipped and the name ends at the first whitespace character).

#### Acceptance conditions

- ac1: parse keeps the existing command table and adds: "/exit x" -> ("exit", "x"), "/clear\x0bx" -> ("clear", "x"), "/login\rx" -> ("login", "x"), "﻿/login" -> ("login", ""), "/exit　" -> ("exit", ""), "\x1b/exit" -> ("exit", ""), "/ex\x1bit" -> ("exit", ""), "/ex​it" -> ("exit", ""), "\x1c/exit" -> ("exit", ""), "/exit\x1cx" -> ("exitx", "") (updated) [evidence: test:tests/test_slash.py::test_parse_slash_commands]
- ac2: "x /exit" and "/etc/hosts x" join the prose cases and return None (updated) [evidence: test:tests/test_slash.py::test_parse_leaves_prose]
- ac3: exactly U+0009-000D, 0020, 00A0, 1680, 2000-200A, 2028, 2029, 202F, 205F, 3000 and FEFF end the name and are stripped from the args; U+001C-001F and U+0085 do not (new) [evidence: test:tests/test_slash.py::test_parse_whitespace_set_is_js_whitespace]
- ac4: for every code point of category Zs, Zl, Zp, Cc and Cf, "<c>/exit" and "/exit<c>x" parse as a command (never None) (new) [evidence: test:tests/test_slash.py::test_no_whitespace_or_invisible_char_hides_a_slash_command]
- ac5: the trailing run marker rule still holds [evidence: test:tests/test_slash.py::test_parse_strips_trailing_run_marker]
- ac6: README's slash text descriptions name the skipped invisible characters [evidence: command:grep -q "invisible" README.md]
- ac7: the Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_slash.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/agents_orchestrator/slash.py`
- `tests/test_slash.py`
- `README.md`

#### Interfaces

- `agents_orchestrator.slash.parse(text: str) -> tuple[str, str] | None`: unchanged signature; the name cleaned of Cc/Cf characters, the args stripped of JS whitespace only. The dispatcher sends this name and these args to the wrapper.

#### Expected outcome

The orchestrator stores every text claude would run as a command as `kind = 'command'`, with the cleaned name, so none is dispatched as a turn.

#### Steps

- Red: add the shared cases and the two new tests to `tests/test_slash.py`; run `uv run --frozen pytest tests/test_slash.py`: the new cases fail.
- Green: rewrite `parse` per the parse steps (explicit JS whitespace set, `unicodedata.category` in Cc/Cf); update README; run the task's verify. Quote the summary line.

#### Notes

- Same code shape and the same case table as wrapper-slash-js-whitespace, so the two parsers cannot drift (retro proposal: one shared parity table).
- No `str.strip()`, `str.lstrip()`, `str.isspace` or regex `\s` in the parser, the `_RUN_MARKER` regex included.
- Docker-free: runs in this container. Can run in parallel with the wrapper tasks.

- 2026-10-29 done

### S9: plugins release 0.2.0

- Status: done
- Files: `orchestration/orchestrator/pyproject.toml`, `uv.lock`, `orchestration/orchestrator/README.md`, `tests/test_source_install.py`
- Verify: `uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 3dfd403cc5e372b32307d32cd74474c1fad4a9a4

#### Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."

Open question Q1 of design.md, verbatim: "Release any-mcp-tatara-plugins v0.2.0 after plugin-session-send-slash merges and bump the orchestrator's plugins pin (ORCH_ANY_MCP_PLUGINS_REF default, the any-mcp-tatara-orchestrator dev dependency, README, tests) to v0.2.0, as two small tasks added at the gate, so superleaders actually see the new session_send description? Without them the description change stays unreleased." Settled by the builder check (user decision, verbatim): "add two tasks, any-mcp-tatara-plugins release v0.2.0 after plugin-session-send-slash, and an orchestrator plugins pin bump (ORCH_ANY_MCP_PLUGINS_REF, dev dependency, README, tests)".

Design D13, verbatim (the release part): "Release and pin (builder check, my call): any-mcp-tatara-plugins `v0.2.0` after the description change (task plugins-release-0-2-0: version bump; the tag is pushed by the orchestrator session after the merge), then the orchestrator pins it (task orch-plugins-pin-0-2-0: the `ORCH_ANY_MCP_PLUGINS_REF` default, the `any-mcp-tatara-orchestrator` dev dependency, README, tests), so superleaders actually see the description. The helmfile value of `ORCH_ANY_MCP_PLUGINS_REF` stays with the gate's deploy decision."

Amendment (2026-10-29, user-approved release order agreed between hives 2026-10-28): the epic matrix-connector-agent-initi ran first and released any-mcp-tatara-plugins `v0.2.0` (tag on origin at commit 4506e70, its chat tools; plugin version 0.2.0, README example `?ref=v0.2.0`). This task therefore releases `v0.3.0` on top of `v0.2.0`: every `v0.2.0`/`0.2.0` of this release in the quotes above now reads `v0.3.0`/`0.3.0` (design D13 amended the same way). The task slug stays plugins-release-0-2-0. Where the Interfaces, Expected outcome and Steps sections below still name 0.2.0 or 0.1.0 (written before this amendment), they read 0.3.0 and 0.2.0 respectively.

Repo README `## Releases`, verbatim: "Releases are `vX.Y.Z` tags on `main`; pin `?ref=` to a release tag. Nothing is published beyond the tag."


Amendment 2 (2026-10-29, user-approved, mx-34 #406): tatara's epic hive-decoupling released any-mcp-tatara-plugins `v0.4.0` (merge 6d5cc19, plugin version 0.4.0) and pinned agents-orchestrator `main` to it (df2b80e) before this epic's `v0.3.0` was tagged; `v0.3.0` stays unused. This epic ships as plugins `v0.5.0` on top of `v0.4.0`. Where Amendment 1 and the sections below read `v0.3.0`/`0.3.0` they now read `v0.5.0`/`0.5.0`, and where they read `v0.2.0`/`0.2.0` as the current release on `main` they now read `v0.4.0`/`0.4.0`. The Scope below is restated with these numbers. Tagging `v0.5.0` is approved (standing release-tag rule mx-34 #396 satisfied by #406).

Scope (any-mcp-tatara-plugins):
- The epic branch `slash-commands-from-chat` (plugin-session-send-slash) is rebased onto plugins `main` (which carries `v0.4.0`) before this task's commit, keeping the v0.4.0 chat tools and this epic's session_send description.
- `orchestration/orchestrator/pyproject.toml`: version `0.4.0` -> `0.5.0`; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=v0.5.0` (was `?ref=v0.4.0`).
- `tests/test_source_install.py::test_orchestrator_distribution_metadata` is no longer accurate (named): on `main` it pins version `0.4.0` in the pyproject and the installed metadata; it asserts `0.5.0`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: `git tag v0.5.0 <merge sha> && git push origin v0.5.0` (irreversible, listed in design.md). ac3 is checked by the orchestrator after that push, not by the implementer or reviewer.
- The branch's earlier `0.3.0` release commit (4ee917c, built on `v0.2.0`) is not kept: the branch is rebased onto plugins `main` (`v0.4.0`), and the release commit sets `0.5.0`.

#### Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.5.0 (updated) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release v0.5.0 and no older one [evidence: command:grep -q "ref=v0.5.0" orchestration/orchestrator/README.md && ! grep -q "ref=v0.4.0" orchestration/orchestrator/README.md && ! grep -q "ref=v0.1.0" orchestration/orchestrator/README.md]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.5.0 exists on origin at the merge commit, on top of v0.4.0 [evidence: command:test -n "$(git ls-remote --tags origin v0.5.0)" && git merge-base --is-ancestor v0.4.0 v0.5.0]
- ac4: the release is built on v0.4.0 (the branch contains the v0.4.0 tag commit) [evidence: command:git merge-base --is-ancestor v0.4.0 HEAD]
- ac5: targeted tests and lint pass [evidence: command:uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

#### Interfaces

- Distribution `any-mcp-tatara-orchestrator` version `0.2.0`; git tag `v0.2.0` on the `main` merge commit.

#### Expected outcome

The orchestrator plugin with the new session_send description is released as tag v0.2.0, so the orchestrator can pin it.

#### Steps

- Red: change `test_orchestrator_distribution_metadata` to 0.2.0; run `uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata`: fails.
- Green: bump the plugin pyproject, `uv lock`, the plugin README example; run the task's verify: passes. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, `git tag v0.2.0 <merge sha> && git push origin v0.2.0`, then check ac3.

#### Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- The tag push is an orchestrator-session step (retro proposal: plan live steps as orchestrator-run).
- Depends on plugin-session-send-slash.

- 2026-10-29 amended: release order changed (user-approved, agreed between hives 2026-10-28): matrix-connector-agent-initi released plugins v0.2.0 first, so this task releases v0.3.0 on top of v0.2.0 after rebasing onto plugins main; slug stays plugins-release-0-2-0

- 2026-10-29 done

- 2026-10-29 in-progress: reopened: rebase onto plugins main v0.4.0 and release 0.5.0 (Amendment 2, mx-34 #406)

- 2026-10-29 amended: plugins renumbered: hive-decoupling took v0.4.0 first; slash ships v0.5.0 (user-approved mx-34 #406)

- 2026-10-29 done: merged PR #4 as dfa0355 (main CI green), tag v0.5.0 pushed on it; ac3 ok

### S10: wrapper command args

- Status: done
- Files: `src/claude_code_wrapper/commands.py`, `src/claude_code_wrapper/router.py`, `src/claude_code_wrapper/api/commands.py`, `src/claude_code_wrapper/mcp_server.py`, `README.md`, `tests/test_command_registry.py`, `tests/test_slash_review_fixes.py`, `tests/test_mcp_server.py`, `tests/test_api_commands.py`, `tests/test_command_runner.py`, `tests/test_auto_compact.py`, `tests/test_mcp_injection.py`
- Verify: `uv run pytest tests/test_command_registry.py tests/test_slash_review_fixes.py tests/test_mcp_server.py tests/test_api_commands.py tests/test_command_runner.py tests/test_auto_compact.py tests/test_mcp_injection.py tests/test_command_vocabulary.py tests/test_fake_claude_mcp.py tests/test_readme_api.py tests/test_slash_commands_docs.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 796437ff6850496f34d4b30a7e46f37915789235

#### Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D4, verbatim: "`commands.py`: `validate(name, args)` (name by the D2 name pattern, an empty name refused `invalid_command`; args by the D2 args rule: newlines and tabs allowed, `\r\n` normalised, at most `MAX_COMMAND_ARGS` 20000 characters, no other control character), `render(name, args)` = `f"/{name} {args}".rstrip()`, `CommandRecord.args: str` (default ""). `BUILTIN_COMMANDS`, `validate_params` and `params_schema` are removed. `--force` among the args of `reload-plugins` needs `allow_force` (`force_not_allowed`). `POST /v1/sessions/{id}/commands` takes `{name, args: str = ""}`. The ccw MCP tool `command` takes `{name, args?}` (name: an enum of the agent allowlist, or a plain string when the allowlist holds `"*"`). The onCommand hook payload and `command_*` event records carry `args` as a string. Auto-compact queues `compact` with args = `auto_compact.instructions`. Ruling (my call): a queued duplicate coalesces only when name and args are identical, so `/model a` and `/model b` both queue. The line is typed as one bracketed paste and one CR (`Session.send_command`, `pty.send_prompt`), so a second line of multi-line args that starts with `/` is part of the first command's args, never a command of its own (the probe: a paste "/x\n\n<!-- ccw turn: id -->" ran /x with the rest as args)."

Design D2, verbatim (the args part): "Args are at most `MAX_COMMAND_ARGS` 20000 characters (my call: webhook prompt templates render issue bodies and the default event block) and may hold newlines and tabs; `\r\n` is normalised to `\n`; any other control character (ESC included, so args cannot end the bracketed paste the line is typed in) and U+2028/U+2029 are refused 422 `invalid_command`, and the message fails visibly with that code (D10)." D2 name pattern: `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap.

Interrogate item 8 (interrogate.md), verbatim: "Multi-line slash text and existing callers (C). agents-common runs.py:151 posts `text\n\nmarker`; a preset prompt starting with `/` used to run and would now fail `invalid_command`. Strip the ccw marker before classifying and accept multi-line args (pasted) up to a cap; test the marker-suffixed case." Interrogate item 2, verbatim (the name part): "Mirror the binary: name = text up to the first whitespace, empty name is `invalid_command` (claude: "Commands are in the form `/command [args]`"), unknown-command regex `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap."

Design D18, verbatim: "wrapper-command-args touches 12 files (4 source, README, 7 test files), over the 8-file guideline: removing `validate_params` and `params_schema` and changing `CommandRecord.args` to a string breaks every caller (router, API, MCP server) and the tests that pass params dicts in the same commit; there is no green intermediate without a compatibility shim (rule 4)."

User decision (gate brief): "Replace the five structured command params (compact.instructions, reload-plugins.force, mcp.action/server) with free-text `args` everywhere, including the ccw MCP `command` tool and the example configs, with no compatibility shim" (example configs: task wrapper-command-docs).

Scope (claude-code-wrapper):
- `commands.py`: `validate(name, args) -> str` (the normalised, stripped args; `CommandRejected("invalid_command", ...)` for an empty name, a name outside the D2 pattern, or args breaking the D2 args rule; `force_not_allowed` for `reload-plugins` args holding the token `--force` without `allow_force`); `MAX_COMMAND_ARGS = 20000`; `render(name, args)`; `CommandRecord.args: str = ""`; `CommandQueue.request(name, args: str, *, origin, turn_id)`; coalescing only for an identical queued (name, args) pair (ruling); remove `BUILTIN_COMMANDS`, `validate_params`, `params_schema`, `SERVER_NAME`.
- `router.py`: `request_command(name, args: str = "", *, origin)`; `_auto_compact_due` passes `cfg.instructions`; the onCommand payload carries `"args": record.args`; the runner types `render(record.name, record.args)` through `Session.send_command` (one paste, one CR).
- `api/commands.py`: `CommandRequest {name: str, args: str = ""}` (`extra="forbid"`); a non-string `args` is 422.
- `mcp_server.py`: tool `command` input schema `{name: string (enum of the agent allowlist, plain string when it holds "*"), args?: string}`, `additionalProperties: false`; `_call` accepts exactly `name` and optional string `args`, an extra key lists "allowed: name, args".
- `README.md`: `### The ccw command tool`, `### Commands endpoint` (body `{name, args}`, multi-line args up to 20000 characters), the onCommand payload and the command record (`args` string).

Tests no longer accurate (named), because D4 removes structured params: `tests/test_command_registry.py` (`test_validate_params`, `test_render_command_lines`, `test_params_schema_lists_allowed_commands`, `test_unknown_param_rejected_naming_allowed`, `test_force_and_instruction_limits`, and every `request(name, {...})` call), `tests/test_slash_review_fixes.py` (pins `validate_params`, `params_schema`, `BUILTIN_COMMANDS`; its still-valid invariants - control characters, length cap, smuggled `/exit` never run as its own command, flat tool schema - are rewritten against `validate(name, args)`, the one-paste typing and the new tool schema; a newline is no longer a refused control character, ESC still is), `tests/test_mcp_server.py` (`params` argument and `params_schema`), `tests/test_api_commands.py` (`args` objects in `test_post_command_bad_args_422`, `test_post_command_queue_full_429`), `tests/test_command_runner.py` (params dicts in `request_command` calls and the onCommandComplete `args` dict), `tests/test_auto_compact.py` (`rec["args"] == {"instructions": ...}`), `tests/test_mcp_injection.py` (`SELF` tool arguments with `params`).

#### Acceptance conditions

- ac1: validate accepts any D2-pattern name ("_x", a 100-character name) with args that span lines and hold tabs, normalises "\r\n" to "\n", and rejects an empty name, a name holding "." or "/", ESC, U+2028 and args over 20000 characters as invalid_command (new) [evidence: test:tests/test_command_registry.py::test_validate_name_and_args]
- ac2: render(name, args) is "/name args" with no trailing space for empty args, multi-line args kept (new) [evidence: test:tests/test_command_registry.py::test_render_name_and_args]
- ac3: reload-plugins args holding --force are refused force_not_allowed unless allow_force (new) [evidence: test:tests/test_command_registry.py::test_force_needs_allow_force]
- ac4: only an identical queued (name, args) pair coalesces; the same name with other args queues a second record (new) [evidence: test:tests/test_command_registry.py::test_coalesce_identical_name_and_args]
- ac5: args holding a newline plus /exit are typed inside the one paste with one CR (the fake records one input and /exit never runs on its own); args holding ESC (the paste end "\x1b[201~") are refused invalid_command and nothing is typed (updated) [evidence: test:tests/test_slash_review_fixes.py::test_args_smuggling_never_typed]
- ac6: POST /commands {name, args} answers 202 with a record whose args is the string (updated) [evidence: test:tests/test_api_commands.py::test_post_command_returns_202_record]
- ac7: POST /commands with an object as args answers 422; with an empty name answers 422 invalid_command (new) [evidence: test:tests/test_api_commands.py::test_post_command_args_must_be_string]
- ac8: tools/list gives the command tool the {name, args} schema: an enum of the agent allowlist, a plain string with "*" (new) [evidence: test:tests/test_mcp_server.py::test_tools_list_schema_name_and_args]
- ac9: tools/call queues the command with its args string (updated) [evidence: test:tests/test_mcp_server.py::test_tools_call_queues_command]
- ac10: a command with args is typed as "/mcp reconnect github" (updated) [evidence: test:tests/test_command_runner.py::test_other_commands_complete_with_output]
- ac11: multi-line args are typed as one paste and one CR, "/compact keep\nthe plan" (new) [evidence: test:tests/test_command_runner.py::test_multiline_args_typed_as_one_paste]
- ac12: onCommandComplete receives the record with args as a string (updated) [evidence: test:tests/test_command_runner.py::test_on_command_complete_fired_with_record]
- ac13: idle auto-compact queues compact with args = the instructions string (updated) [evidence: test:tests/test_auto_compact.py::test_auto_compact_fires_after_idle]
- ac14: the agent self-compact e2e still runs through the ccw tool with args (updated) [evidence: test:tests/test_mcp_injection.py::test_agent_self_compact_same_turn_e2e]
- ac15: the removed registry symbols are gone from src and tests [evidence: command:! grep -rnE "validate_params|params_schema|BUILTIN_COMMANDS" src tests]
- ac16: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_registry.py tests/test_slash_review_fixes.py tests/test_mcp_server.py tests/test_api_commands.py tests/test_command_runner.py tests/test_auto_compact.py tests/test_mcp_injection.py tests/test_command_vocabulary.py tests/test_fake_claude_mcp.py tests/test_readme_api.py tests/test_slash_commands_docs.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/commands.py`
- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/api/commands.py`
- `src/claude_code_wrapper/mcp_server.py`
- `README.md`
- `tests/test_command_registry.py`
- `tests/test_slash_review_fixes.py`
- `tests/test_mcp_server.py`
- `tests/test_api_commands.py`
- `tests/test_command_runner.py`
- `tests/test_auto_compact.py`
- `tests/test_mcp_injection.py`

#### Interfaces

- `commands.validate(name: str, args: str, *, allow_force: bool) -> str`, `commands.render(name: str, args: str = "") -> str`.
- `CommandRecord.args: str`; `CommandQueue.request(name, args, *, origin, turn_id)`.
- `SessionRouter.request_command(name: str, args: str = "", *, origin) -> CommandRecord`.
- HTTP `POST /v1/sessions/{id}/commands` body `{"name": str, "args": str = ""}`; response the record (`id`, `name`, `args`, `origin`, `state`, ...).
- ccw MCP tool `command` arguments `{"name": str, "args"?: str}`.

#### Expected outcome

Any allowed command name with free args (multi-line, up to 20000 characters) can be queued through the API and the ccw tool; the typed line is `/name args` in one paste; structured params are gone everywhere in src and tests.

#### Steps

- Red: rewrite the named inaccurate tests and add the new ones (ac1-ac5, ac7, ac8); run `uv run pytest tests/test_command_registry.py tests/test_slash_review_fixes.py tests/test_mcp_server.py`: they fail (old signatures).
- Green: change commands.py, router.py, api/commands.py, mcp_server.py, README.md together (one commit: no intermediate is green); run the task's verify: passes. Quote the summary line.

#### Notes

- Ruling, pinned by ac4: coalescing matches (name, args), so `/model a` and `/model b` both queue.
- Ruling, pinned by ac3: only `reload-plugins` checks `--force` (as today); the token check splits args on whitespace.
- The fake claude still knows only its five names in this task: tests of arbitrary names that need completion come in wrapper-command-signals; use the five names here.
- Depends on wrapper-command-policy (deny list, wildcard, the name pattern constant in config.py).
- Sizing exception D18: 12 files, opus.

- 2026-10-27 amended: interrogate items 8 and 2 (multi-line args up to MAX_COMMAND_ARGS 20000 typed as one paste, ESC still refused; empty name invalid_command; claude's name regex), design D2 and D4 revised

- 2026-10-29 done

### S11: wrapper release 0.4.2

- Status: todo
- Files: `pyproject.toml`, `uv.lock`, `src/claude_code_wrapper/__init__.py`, `tests/test_packaging.py`
- Verify: `uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

User decision PENDING (mx-34 #471 Q1-3, recommended yes to all; tatara #473 confirmed the version v0.4.2). The leader amends this paragraph with the user verbatim answer before the merge; nothing merges or is tagged before it. Questions, verbatim: "1) Deny the account or cloud group too? That means wrapper v0.4.2 (patch, after v0.4.1) before the slash deploy, about 1 h of agent time. Recommended: yes. 2) Also deny mcp, permissions, config and hooks in v0.4.2? Recommended: yes, so that chat cannot rewrite the session's tool and permission settings. 3) Bump the version to wrapper v0.4.2? Live is 0.3.3, v0.4.1 is tagged but not deployed, and v0.4.2 would replace it in the same deploy. Recommended: yes, pending tatara's confirmation."

Scope (mirrors wrapper-release-0-4-1): version `0.4.2` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`; `uv lock`; `tests/test_packaging.py::test_version_matches_pyproject` keeps them in agreement. The wrapper PR (wrapper-deny-list-extend-0-4 and this task) merges to `main` only after the user answer. Release steps, by the leader session (never a subagent): wait for `build.yaml` to push `claude-code-wrapper:<sha7>`, push tag `v0.4.2` on the merge commit (irreversible; version confirmed by tatara #473, tag only after the user answer), watch `release.yaml`, then amend orch-wrapper-pin-0-4-2 with the merge sha. ac3 is checked by the leader after the tag; the implementer and reviewer check ac1, ac2, ac4.

#### Acceptance conditions

- ac1: pyproject, __version__ and the installed metadata agree [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- ac2: the version is 0.4.2 in pyproject and the package [evidence: command:grep -q '^version = "0.4.2"' pyproject.toml && grep -q '__version__ = "0.4.2"' src/claude_code_wrapper/__init__.py]
- ac3: (checked by the leader after it pushed the tag) tag v0.4.2 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.2)"]
- ac4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

### S12: orch session send command

- Status: done
- Files: `src/agents_orchestrator/api/agent.py`, `tests/test_agent_session_messaging.py`, `README.md`
- Verify: `uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint`
- Verified head: 58eeeba799ec0a657e6317e3900e9e71922dfb3a

#### Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text." User request, verbatim: "Both user and superleader can send them."

Design D1, verbatim: "`POST /api/v1/sessions/{id}/messages` (`api/messages.py:post_message`, the chat) and `POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:session_send`, the superleader) both call one new `agents_orchestrator.slash.parse(text) -> tuple[str, str] | None` and store the message with `kind = 'command'` when it matches, else `kind = 'turn'`. On the agent route a match stores `kind = 'command'` only when the sender's own session has `spec.session_messaging` (a superleader); a leader of any other session sending to a superleader (admitted by the D7 check of `api/agent.py:session_send`, `own.spec.session_messaging or target.spec.session_messaging`) keeps `kind = 'turn'`, so its slash text is delivered as framed prose (my call, interrogate item 1: the user asked for "user and superleader")."

Interrogate item 1 (interrogate.md), verbatim: "Non-superleader to superleader command execution (A, B, C). D7 admits any leader sending to a superleader (api/agent.py:412), so with the change a plain worker session runs unframed commands on a superleader. The user asked for "user and superleader". Store `kind='command'` only when the sender's session has `session_messaging`; otherwise the text stays a framed turn. AC with a worker-to-superleader test."

Scope (agents-orchestrator): `api/agent.py:session_send` passes `kind="command"` to `queue.enqueue_message` when `slash.parse(body.text)` matches and `own.spec.session_messaging` is true, else `kind="turn"`; every D7 check (leader only, self send, superleader, deleting, hop, rate, pair budget, queue cap) applies unchanged and in the same order; `README.md` (the superleader messaging section says slash text from a superleader runs as a command on the target's leader, unframed, and slash text from any other session is delivered as a framed message).

#### Acceptance conditions

- ac1: (Docker: CI or a Docker host) a superleader's session_send "/compact" stores kind command with sender_session_id, sender_slug and hop (new) [evidence: test:tests/test_agent_session_messaging.py::test_session_send_slash_is_command_kind]
- ac2: (Docker) a leader of a session without session_messaging sending "/compact" to a superleader is accepted 202 and stored kind turn, so the dispatcher frames it as a session message (new) [evidence: test:tests/test_agent_session_messaging.py::test_session_send_slash_from_non_superleader_stays_turn]
- ac3: (Docker) the D7 refusals still apply to slash text in the same order (not_leader, target_not_superleader, rate_limited) (new) [evidence: test:tests/test_agent_session_messaging.py::test_session_send_slash_keeps_refusals]
- ac4: README documents that only a superleader's slash text runs as a command [evidence: command:grep -i "slash" README.md | grep -qi "superleader"]
- ac5: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

#### Files

- `src/agents_orchestrator/api/agent.py`
- `tests/test_agent_session_messaging.py`
- `README.md`

#### Interfaces

- `POST /agent/v1/sessions/{slug}/messages` unchanged on the wire; the stored message carries `kind`.

#### Expected outcome

A superleader's `orchestrator_session_send` with "/x ..." becomes a command message for the target session's leader; the dispatcher (orch-dispatch-commands) sends it unframed.

#### Steps

- Red: add ac1-ac3; on a Docker host ac1 fails (kind turn).
- Green: change `session_send` and the README; run the task's verify: passes. Quote the summary line; the Docker legs run in CI.

#### Notes

- Reuse `_leads` and the D7 check order (api/agent.py:session_send); the kind decision reads `own.spec.session_messaging` after every refusal check.
- Ruling, pinned by ac2: a non-superleader's slash text stays a framed turn (interrogate item 1).
- Depends on orch-message-kind (`enqueue_message(kind=...)`).

- 2026-10-27 amended: interrogate item 1 (only a superleader's slash text becomes a command; a worker-to-superleader slash text stays a framed turn), design D1 revised

- 2026-10-29 done

### S13: wrapper slash turn guard

- Status: done
- Files: `src/claude_code_wrapper/session.py`, `src/claude_code_wrapper/router.py`, `src/claude_code_wrapper/api/turns.py`, `src/claude_code_wrapper/manager.py`, `README.md`, `tests/test_session_turns.py`, `tests/test_api_turns.py`, `tests/test_manager.py`
- Verify: `uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_manager.py tests/test_readme_api.py tests/test_submit_busy_first.py --deselect tests/test_manager.py::test_shutdown_stops_all && uv run ruff check . && uv run ruff format --check .`
- Verified head: fc58ec9defd4fa1b68d9478797fdca5385f5c3ed

#### Requirement

Goal G3 (README), verbatim: "Sending /reload-plugins (the reported case) no longer hangs the session; a regression test pins it." User decision: "A regression test must pin the reported case: sending '/reload-plugins' from chat never leaves the session busy (wrapper and orchestrator level)." This task is the wrapper-level pin.

Design D3, verbatim: "`Session.submit` raises `TurnRejected("slash_command")` for slash text (D2 rule) before reserving the slot or typing, for every origin (client, peer, initial, agent). `SessionRouter.submit_turn` checks the same rule first, so no onTurn hook fires and no file is written for a refused turn. `POST /v1/sessions/{id}/turns` maps it to 422 `slash_command` with the message "slash commands go to POST /v1/sessions/{id}/commands". `SessionManager._initial_turn` routes a slash initial prompt to `router.request_command(name, args, origin="client")` (refusals are reported as today's `initial_turn_rejected` error event). Peer turns are framed (`peer_inbox.py` `frame(item)`), so a peer "/x" is prose by construction. This is the regression pin for the reported hang."

Design D2, verbatim: "Slash text mirrors Claude Code's own parser (claude 2.1.304 binary, interrogate item 2). After leading whitespace the text starts with `/`. A trailing agents-common run marker (`<!-- agents-<kind>:<id> -->`, `agents_common.runs.marker`, posted as `text\n\nmarker` by `runs.py:_post_once`) is removed first (interrogate item 8). The name is the text after the `/` up to the first whitespace (space, tab or newline); the args are the rest, stripped, and may span lines. The text is a command when the name is empty (`/`, `/ is root`: claude answers "Commands are in the form `/command [args]`" and calls no model; the wrapper refuses an empty name 422 `invalid_command`) or matches `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, with no length cap (`/tmp`, `/_x`, a 100-character name: claude runs it or answers "Unknown command", again with no model call, so a bare `/tmp` fails `unknown_command`). A name with any other character is prose (`/workdir/foo is broken`, `/etc/hosts`, `//x`, `/notes.txt`): claude sends it to the model as a prompt. The orchestrator classifies with this rule and the wrapper's turn guard (D3) refuses with the same rule, both pinned by one shared case table, so a text that claude would parse as a command can never be typed as a turn. The path-like prose leg is confirmed by a real-binary probe in task wrapper-command-signals; a result that contradicts this rule is reported back and amends both parser tasks, never worked around."

Interrogate item 2 (interrogate.md), verbatim: "Classification must match Claude Code's own parser (B, critical). D2 types `/`, `/ is root`, `/_x` and names over 64 chars as turns; claude runs no model call for them, so no Stop and the session hangs. Mirror the binary: name = text up to the first whitespace, empty name is `invalid_command` (claude: "Commands are in the form `/command [args]`"), unknown-command regex `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap. Fix wrapper-slash-turn-guard ac3 and orch-slash-parser ac2. Path-like prose (`/workdir/foo is broken`) must be pinned either way after a probe."

User decision (builder check), verbatim: "a bare '/word' message such as '/tmp' is a command that fails unknown_command, while '/etc/hosts'-like paths stay prose (per the parser rule of item 2, after the probe)."

Scope (claude-code-wrapper): `session.py` (the D2 rule as one shared helper, the guard in `Session.submit`), `router.py` (`submit_turn` checks the helper before onTurn), `api/turns.py` (`_REJECT_STATUS["slash_command"] = 422`, its text), `manager.py` (`_initial_turn` slash branch; an empty name goes to `request_command` too and is refused `invalid_command`, reported as `initial_turn_rejected`), `README.md` (Errors row `slash_command`; the turns endpoint notes that slash text is refused and goes to `/commands`). The guard's case table is the same as orch-slash-parser's (`tests/test_slash.py` of agents-orchestrator), case for case.

#### Acceptance conditions

- ac1: regression pin: POST /turns {text: "/reload-plugins"} answers 422 slash_command, fake-inputs.jsonl stays empty, the session stays ready, and the next POST /turns with prose answers 202 (new) [evidence: test:tests/test_api_turns.py::test_slash_text_turn_is_refused_not_typed]
- ac2: Session.submit raises TurnRejected("slash_command") for slash text with each origin client, peer, initial and agent, leaves the state ready and writes nothing to the PTY (new) [evidence: test:tests/test_session_turns.py::test_submit_refuses_slash_text_for_every_origin]
- ac3: "/", "/ is root", "/_x", "/tmp", a 100-character name, "/x a\nb" and "/review-pr 12\n\n<!-- agents-webhook:42 -->" are refused slash_command, as claude's parser would run them as commands (new) [evidence: test:tests/test_session_turns.py::test_slash_rule_matches_claude_parser]
- ac4: "/workdir/foo is broken", "/etc/hosts", "//x", "/notes.txt" and prose mentioning "/compact" mid-sentence are accepted as turns (new) [evidence: test:tests/test_session_turns.py::test_slash_rule_leaves_paths_and_prose]
- ac5: a refused slash turn fires no onTurn hook and writes no turn file (new) [evidence: test:tests/test_api_turns.py::test_slash_turn_fires_no_on_turn]
- ac6: an initial prompt "/reload-plugins" (client allowlist ["*"]) runs as a client command that completes, no turn record is created and the session ends ready (new) [evidence: test:tests/test_manager.py::test_initial_slash_prompt_runs_as_command]
- ac7: an initial slash prompt the allowlist refuses, or one with an empty name ("/ is root"), emits error initial_turn_rejected and the session stays ready (new) [evidence: test:tests/test_manager.py::test_initial_slash_prompt_refused_is_reported]
- ac8: the README Errors table lists slash_command [evidence: command:grep -q '^| `slash_command`' README.md]
- ac9: targeted suites and lint pass [evidence: command:uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_manager.py tests/test_readme_api.py tests/test_submit_busy_first.py --deselect tests/test_manager.py::test_shutdown_stops_all && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/api/turns.py`
- `src/claude_code_wrapper/manager.py`
- `README.md`
- `tests/test_session_turns.py`
- `tests/test_api_turns.py`
- `tests/test_manager.py`

#### Interfaces

- One helper for the D2 rule, for example `claude_code_wrapper.session.slash_command(text) -> tuple[str, str] | None` (name, args), used by `Session.submit`, `SessionRouter.submit_turn` and `SessionManager._initial_turn`.
- `TurnRejected("slash_command")`; HTTP 422 envelope code `slash_command`.

#### Expected outcome

No origin can type a slash line with a turn marker any more: the reported `/reload-plugins` hang cannot recur through the turns path, and a slash initial prompt runs as a command.

#### Steps

- Red: add the seven tests (ac1-ac7); run `uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_manager.py --deselect tests/test_manager.py::test_shutdown_stops_all`: they fail (the text is typed as a turn; the API answers 202).
- Green: add the helper and the guards, the 422 mapping, the initial-turn branch and the README rows; run the task's verify: passes. Quote the summary line.

#### Notes

- `tests/test_manager.py::test_shutdown_stops_all` fails in this container (PID 1 process group, design Constraints); it is deselected, not changed.
- The guard runs before `check_submittable` side effects and before the slot is reserved (`Session.submit` reserves before the first byte today).
- The probe that defines the hang: a paste "/x\n\n<!-- ccw turn: id -->" runs /x with the marker as `<command-args>` (design Research, probed).
- `peer_inbox.py` needs no change (frames every peer turn); ac2 still covers origin peer at the session level.
- Depends on wrapper-command-args (`request_command(name, args, origin=...)`).

- 2026-10-27 amended: interrogate item 2 (guard mirrors claude's parser; ac3 fixed: /, / is root, /_x, long names are refused, paths stay turns), builder check (/tmp), design D2 revised

- 2026-10-29 done

### S14: orch dispatch commands

- Status: done
- Files: `src/agents_orchestrator/db/queue.py`, `src/agents_orchestrator/dispatcher/loop.py`, `src/agents_orchestrator/dispatcher/verify.py`, `tests/test_dispatcher.py`, `tests/test_queue_leader_routing.py`, `tests/test_ambiguous_verify.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py tests/test_slash.py && mise run lint`
- Verified head: d5a0044b2161c6d2c913db6ae3aadd3ef92ccdd0

#### Requirement

Goals (README), verbatim: G1 "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."; G2 "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."; G3 "Sending /reload-plugins (the reported case) no longer hangs the session; a regression test pins it." User decision: "A regression test must pin the reported case: sending '/reload-plugins' from chat never leaves the session busy (wrapper and orchestrator level)." This task is the orchestrator-level pin.

Design D10, verbatim: "`db/queue.py`: `Claim.kind`; a command head picks an agent with `_PICK_COMMAND` (ready, not gone, has a wrapper session, the target or the leader; no `state = 'idle'` and no `free_since` predicate); a command neither needs nor writes the `agents.last_dispatched_at` reservation (my call: a command does not take the orchestrator's turn slot, and a rejected command would otherwise leave `last_dispatched_at > free_since` and starve prose); a command is exempt from the busy-leader hold and the handover hold of `_claim_in_session` but not from backoff (`not_before`) or a gone leader (it waits for the successor) (my call). It may overtake queued prose of its session (intended: "at any moment"). `dispatcher/loop.py:_send` sends kind=command unframed (no `<session-message>`) with `WrapperClient.command(wsid, name, args)`. Outcomes: 202 -> `mark_sent_command` (status `sent`, `wrapper_command_id`); 409 booting|dead and 429 `command_queue_full` -> requeue with `not_before = now() + retry_backoff_base_seconds`, no attempt counted (my call: an immediate requeue would spin on a full wrapper queue); 403 `command_denied` | `command_not_allowed` and 422 -> failed with the wrapper's envelope code as `error` (my call: QueueStrip shows `error`, so the user sees why); 401 -> failed `config_error`; 404/410 -> as a turn (backoff, rebootstrap); an ambiguous send (read timeout, 500, 502) -> failed `ambiguous` (my call: the verifier looks for a turn carrying `orch_message_id`, a command has none, so verifying would resend it blindly); a stale `dispatching` command row is failed `ambiguous` by the verifier instead of resent. Only the user's Retry resends a failed command. [...] The args the dispatcher sends are `slash.parse(text)`'s, so a trailing agents-common run marker is never sent to claude (D2); the stored text keeps it. Per-session order (my call, interrogate item 3): while a session has a `kind = 'command'` row in `dispatching`, no later message of that session (higher id, prose or command) is claimed; the command's 202 puts it in the wrapper's FIFO command queue, so two commands, or a command and later prose, of one session reach the wrapper in id order. Pinned in `tests/test_queue_leader_routing.py`." (The hop-guard part of D10 is task orch-command-turn-link.)

Interrogate item 3 (interrogate.md), verbatim: "Per-session ordering of commands and prose (B, C). Commands write no `last_dispatched_at`, so two commands, or a command and later prose, of one session can be claimed concurrently and arrive out of order. Hold a session's later messages while one of its command rows is `dispatching`; pin in test_queue_leader_routing."

Interrogate item 8, verbatim (the dispatch part): "agents-common runs.py:151 posts `text\n\nmarker`; [...] Strip the ccw marker before classifying [...]; test the marker-suffixed case."

Interrogate item 13, verbatim: "AC evidence that already passes today (A): orch-dispatch-commands ac10 grep matches MEMORY.md:41; web-sync-message-kind ac3 grep matches the current source pin. Replace with assertions specific to the new state."

Scope (agents-orchestrator): `db/queue.py` (`Claim.kind`, `_PICK_COMMAND`, the kind-aware pick, the hold exemption in `_claim_in_session`, the per-session hold behind a `dispatching` command row, no reservation write for commands, `mark_sent_command`, a requeue with `not_before`), `dispatcher/loop.py` (`_send` kind=command branch and outcome mapping; `slash.parse` gives name and args from the stored text, the run marker excluded), `dispatcher/verify.py` (a verifying kind=command row fails `ambiguous` at once), `README.md` (`## API` messages: slash text, kind, the failure codes; `## Architecture` notes the command dispatch and the per-session order), `MEMORY.md` (an entry dated and tagged `(slash-commands-from-chat)` with the why of the no-reservation, hold-exemption and per-session-order rulings, naming `last_dispatched_at`).

#### Acceptance conditions

- ac1: (Docker: CI or a Docker host) regression pin: POST message "/reload-plugins" reaches the fake wrapper as POST /commands {name: reload-plugins, args: ""} and never as POST /turns, the message ends sent with wrapper_command_id, and a following prose message is dispatched as a turn to the same agent and completes (new) [evidence: test:tests/test_dispatcher.py::test_reload_plugins_from_chat_runs_as_command_and_frees_agent]
- ac2: (Docker) a superleader command message is sent unframed to /commands; a prose session message is still framed (new) [evidence: test:tests/test_dispatcher.py::test_command_message_sent_unframed_to_commands]
- ac3: (Docker) a command message is dispatched while its agent is busy with a turn (new) [evidence: test:tests/test_dispatcher.py::test_command_message_dispatched_while_agent_busy]
- ac4: (Docker) "/review-pr 12\n\n<!-- agents-webhook:42 -->" is sent as POST /commands {name: review-pr, args: "12"} and the stored text keeps the marker (new) [evidence: test:tests/test_dispatcher.py::test_command_args_exclude_run_marker]
- ac5: (Docker) 429 command_queue_full and 409 booting requeue with not_before about retry_backoff_base_seconds ahead and no attempt counted (new) [evidence: test:tests/test_dispatcher.py::test_command_busy_requeues_with_backoff]
- ac6: (Docker) 403 command_denied fails the message with error command_denied; 422 invalid_command (for example "/ is root", an empty name) fails it with error invalid_command (new) [evidence: test:tests/test_dispatcher.py::test_command_refusal_fails_with_wrapper_code]
- ac7: (Docker) an ambiguous command send fails ambiguous and never enters verifying (new) [evidence: test:tests/test_dispatcher.py::test_command_ambiguous_fails_without_verify]
- ac8: (Docker) a command claim writes no last_dispatched_at; after a refused command the idle agent still takes the next prose message (new) [evidence: test:tests/test_queue_leader_routing.py::test_command_claim_keeps_reservation_free]
- ac9: (Docker) an untargeted command head overtakes queued prose held for a busy leader and for a pending handover, waits on backoff and on a gone leader, and prose order is unchanged (new) [evidence: test:tests/test_queue_leader_routing.py::test_command_skips_leader_holds]
- ac10: (Docker) per-session order: while a session's command row is dispatching, no later message of that session (a second command or prose) is claimed; once it is sent the next is claimed, so the fake wrapper receives them in id order (new) [evidence: test:tests/test_queue_leader_routing.py::test_session_messages_wait_for_dispatching_command]
- ac11: (Docker) a stale dispatching command row is failed ambiguous by the verifier, never resent (new) [evidence: test:tests/test_ambiguous_verify.py::test_stale_command_row_fails_ambiguous]
- ac12: MEMORY.md has an entry tagged with this epic that records the command dispatch rulings and names last_dispatched_at (absent today) [evidence: command:grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\)" MEMORY.md | grep -q "last_dispatched_at"]
- ac13: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py tests/test_slash.py && mise run lint]

#### Files

- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `src/agents_orchestrator/dispatcher/verify.py`
- `tests/test_dispatcher.py`
- `tests/test_queue_leader_routing.py`
- `tests/test_ambiguous_verify.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- `Claim.kind: str`; `queue.mark_sent_command(conn, id, wrapper_command_id) -> bool`; a guarded requeue with `not_before` (for example `queue.requeue_later(conn, id, seconds) -> bool`).
- `messages.error` values for commands: `command_denied`, `command_not_allowed`, `invalid_command`, `ambiguous`, `config_error`.

#### Expected outcome

A slash message from the chat or a superleader is delivered to the target's wrapper command queue at once, even mid-turn, and never as a turn; its delivery outcome is visible on the message.

#### Steps

- Red: add the eleven Docker tests (ac1-ac11); on a Docker host run `uv run --frozen pytest tests/test_dispatcher.py tests/test_queue_leader_routing.py tests/test_ambiguous_verify.py`: they fail. In this container only ac13 runs.
- Green: queue, dispatcher, verifier, README, MEMORY.md; run the task's verify: passes. Quote the summary line; the Docker legs run in CI.

#### Notes

- Rulings and their pins (retro proposal): no reservation write (ac8), hold exemption and its limits (ac9), per-session order behind a dispatching command (ac10), backoff requeue (ac5), wrapper code as error (ac6), ambiguous fails (ac7, ac11), run marker excluded from args (ac4).
- The hop-guard link of a promoted command turn is task orch-command-turn-link (it extends `mark_sent_command`).
- Every status change stays a guarded UPDATE (`WHERE status = 'dispatching'`); one writer per transition.
- `release_agent` is skipped for command claims (nothing was reserved).
- Depends on orch-message-kind (the `kind` column) and orch-wrapper-command-client (`command()` outcomes, the fake's command route).

- 2026-10-27 amended: interrogate items 3 (hold a session's later messages while its command row is dispatching), 8 (run marker never sent as args) and 13 (ac10 evidence replaced by an epic-tagged MEMORY.md entry naming last_dispatched_at), design D10 revised

- 2026-10-29 done

### S15: wrapper command signals

- Status: done
- Files: `src/claude_code_wrapper/transcript.py`, `src/claude_code_wrapper/router.py`, `tests/fake_claude/fake_claude.py`, `tests/test_transcript_commands.py`, `tests/test_command_signals.py`, `tests/test_fake_claude_commands.py`, `tests/test_command_runner.py`, `MEMORY.md`
- Verify: `uv run pytest tests/test_transcript_commands.py tests/test_transcript.py tests/test_command_signals.py tests/test_fake_claude_commands.py tests/test_fake_claude.py tests/test_command_runner.py tests/test_command_turn_resume.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 606f1676e3de47c84466df7a8d69092086a945c8

#### Requirement

Goal G3 (README), verbatim: "Sending /reload-plugins (the reported case) no longer hangs the session; a regression test pins it." Goal G1, verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D6, verbatim: "The runner keeps: wait quiet (`quiet_seconds` 1.5) -> onCommand -> mark -> type the line (no marker) -> await. `_await_completion` becomes class-agnostic, first signal after the mark wins:
1. a `command_output` after any `command_invoked` (claude echoes the resolved alias: /cost echoes /usage) -> completed, `output` = stdout; stderr only -> failed `command_error`; compact keeps its PostCompact / compact_boundary / failure-pattern leg; reload-plugins keeps `skipped_cache`.
2. a `command_unknown` (new transcript event from a `system` line of subtype `informational` "Unknown command: /x", also in the suggestion form "Unknown command: /x. Did you mean /y?" that the binary writes for a near miss, interrogate item 11) -> failed `unknown_command` at once, no ESC.
Real-binary probe (user decision, my call on placement): task wrapper-command-signals settles, in a throwaway dir under `/workdir/workdir/.scratchpad/probe-slash` and recorded in the wrapper's `MEMORY.md`, whether local commands never fire UserPromptSubmit and how claude treats path-like prose such as `/workdir/foo is broken` (D2); a result that contradicts the design is reported back, not worked around.
Transcript fix: a `system/local_command` body starting with `<command-name>` is a `CommandInvoked` (today a `CommandOutput` with empty stdout, so /context, /model and every dialog command on the real binary never match). The fake claude writes the real echo shapes: user echo for reload-plugins, compact, mcp, model with an arg; system echo for context; informational line for an unknown name."

Interrogate item 11 (interrogate.md), verbatim: "Unknown command with suggestion (B). Claude writes "Unknown command: /x. Did you mean /y?"; pin it in wrapper-command-signals so a typo fails fast instead of waiting the full timeout."

User decision (probes), verbatim: "the owning tasks (prompt-command turn, command signals) get a requirement to settle by a real-binary probe in a throwaway dir under /workdir/workdir/.scratchpad/probe-slash, recorded in the component MEMORY.md, whether Stop fires after a promoted prompt-command turn, whether plugin commands fire UserPromptSubmit, whether local commands never fire it, and how claude treats path-like prose such as '/workdir/foo is broken'; a probe result that contradicts the design is reported back, not worked around."
This task's probe facts (design D6): whether local commands (for example /reload-plugins, /context) never fire UserPromptSubmit, and how claude treats path-like prose such as '/workdir/foo is broken' and '/etc/hosts' (prose to the model, design D2), with '/nonexistent' (Unknown command) and '/tmp' (an existing path: sent to the model, design D2 as amended 2026-10-29) and '/ is root' (the "Commands are in the form" message) as the contrast cases. The probe runs the real binary (`/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe`) in a new throwaway directory under `/workdir/workdir/.scratchpad/probe-slash` (never a session workdir, never a test), and each fact is recorded as a dated entry tagged `(slash-commands-from-chat) probe` in the wrapper's `MEMORY.md` (the repo has none yet: this task creates it), with the observed result and the raw evidence path. A fact the probe cannot settle (for example a step that needs a model call and there are no credentials) is recorded as "not settled: <why>" and returned to the orchestrator as a question. A result that contradicts design D2 or D6 is reported back and not worked around.

Design D16, verbatim: "ESC keys the fake receives are appended to `$CLAUDE_CONFIG_DIR/fake-keys.jsonl` (`{"key": "esc", "ts"}`), not to `fake-inputs.jsonl`, so the existing pins that every input was typed while idle (`tests/test_command_turn_resume.py`, `tests/test_fake_claude_commands.py::test_esc_not_recorded_as_busy`) stay accurate, and dialog tests can count and space ESCs."

Scope (claude-code-wrapper): `transcript.py` (`_system_events`: `<command-name>` body -> `CommandInvoked`; subtype `informational` with "Unknown command: /x", with or without ". Did you mean /y?", -> new `CommandUnknown(name)`; other informational lines yield nothing), `router.py` (`_on_transcript_events` publishes `command_unknown`; `_await_completion` legs 1 and 2), `tests/fake_claude/fake_claude.py` (echo style per command and scenario key `commands.<name>.echo: system|user`, `echo_name` for an alias, any name listed under scenario `commands` is known, an unknown name writes the two informational lines, `suggest` for the suggestion form, ESC keys logged to `fake-keys.jsonl`, docstring updated), `MEMORY.md` (new, the probe entries).

Real samples the fake must match (retro proposal: cite captured real output): `/workdir/workdir/.scratchpad/probe-slash/summaries/outC.txt` lines 15-16 (`type=system sub=informational` "Unknown command: /nonexistent" and "Args from unknown skill: some args"), lines 71-73 (`/context`: system echo, system stdout, isMeta user table), outC.txt line 32 (`/cost` echoes `/usage`); the surviving real transcript `/workdir/workdir/.scratchpad/probe-slash/config/projects/-workdir-workdir--scratchpad-probe-slash-work/64b31430-13c7-48b0-ba54-c6c432f345db.jsonl` (system `local_command` echoes of /context, /permissions, /theme; user echo of /exit); the binary's format string `Unknown command: /${Be}. Did you mean` (interrogate lead check).

Tests no longer accurate (named): `tests/test_fake_claude_commands.py::test_unknown_command` asserts that an unknown name writes no transcript line; real claude writes `system/informational` lines (outC.txt:15-16), so it asserts those lines instead. If `tests/test_transcript_commands.py::test_other_system_lines_yield_nothing` or `::test_other_system_lines_ignored` use an informational "Unknown command" line, they change to another informational text.

Amendment (2026-10-29, user-approved release order agreed between hives 2026-10-28): claude-code-wrapper `main` is now at `v0.3.3`, which adds a transcript fix in `src/claude_code_wrapper/transcript.py` (`parse_line` reads an `attachment` line through the new `_attachment_events`: a `queued_command` attachment's prompt is a prompt event, other attachment types yield nothing; pinned in `tests/test_transcript.py`). This task also edits `transcript.py`, so the epic's wrapper branch `slash-commands-from-chat` is rebased onto wrapper `main` (`v0.3.3`) before this task's commits, and this task keeps the `queued_command` attachment handling and its tests intact next to its own `_system_events` changes. This epic's wrapper release stays 0.4.0 (task wrapper-release-0-4-0).

#### Acceptance conditions

- ac1: a system local_command line whose body starts with <command-name> parses as CommandInvoked with name and args (new) [evidence: test:tests/test_transcript_commands.py::test_system_command_echo_is_command_invoked]
- ac2: a system informational "Unknown command: /x" line parses as CommandUnknown(name "x"); an "Args from unknown skill" line and other informational lines yield nothing (new) [evidence: test:tests/test_transcript_commands.py::test_informational_unknown_command]
- ac3: the suggestion form "Unknown command: /comapct. Did you mean /compact?" parses as CommandUnknown(name "comapct") (new) [evidence: test:tests/test_transcript_commands.py::test_informational_unknown_command_with_suggestion]
- ac4: the user-echo shape still parses as CommandInvoked [evidence: test:tests/test_transcript_commands.py::test_command_echo_is_command_invoked]
- ac5: command_unknown is published on the signal bus for the main chain only (new) [evidence: test:tests/test_command_signals.py::test_unknown_command_publishes_signal]
- ac6: regression pin: with client ["*"], POST /commands {name: reload-plugins} on the fake with the real shape (user echo, system stdout) ends command_completed with output "Reloaded: ..." and a POST /turns within 5 s answers 202 (new) [evidence: test:tests/test_command_runner.py::test_reload_plugins_from_client_completes_and_frees_slot]
- ac7: /context with the system echo completes with its stdout (new) [evidence: test:tests/test_command_runner.py::test_context_with_system_echo_completes]
- ac8: an unknown name ("nonexistent", the real sample outC.txt:15) fails unknown_command within 5 s, no ESC in fake-keys.jsonl, session ready (new) [evidence: test:tests/test_command_runner.py::test_unknown_command_fails_fast_without_esc]
- ac9: a typo answered with the suggestion form fails unknown_command within 5 s, not at the timeout, and sends no ESC (new) [evidence: test:tests/test_command_runner.py::test_unknown_command_with_suggestion_fails_fast]
- ac10: /cost whose echo names /usage completes (new) [evidence: test:tests/test_command_runner.py::test_alias_echo_completes]
- ac11: the fake writes user or system echoes per command and logs ESC keys to fake-keys.jsonl only (new) [evidence: test:tests/test_fake_claude_commands.py::test_echo_styles_and_key_log]
- ac12: the fake writes the two informational lines for an unknown name, and the suggestion form when the scenario sets suggest (updated) [evidence: test:tests/test_fake_claude_commands.py::test_unknown_command]
- ac13: MEMORY.md records the real-binary probe of this task: whether local commands fire UserPromptSubmit and how path-like prose, /tmp and "/ is root" are treated, each with its observed result or "not settled" [evidence: command:grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\) probe" MEMORY.md | grep -q "UserPromptSubmit" && grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\) probe" MEMORY.md | grep -q "/workdir/foo is broken"]
- ac14: targeted suites and lint pass [evidence: command:uv run pytest tests/test_transcript_commands.py tests/test_transcript.py tests/test_command_signals.py tests/test_fake_claude_commands.py tests/test_fake_claude.py tests/test_command_runner.py tests/test_command_turn_resume.py && uv run ruff check . && uv run ruff format --check .]
- ac15: the branch is rebased onto wrapper main v0.3.3 and its queued_command attachment parsing still holds (updated) [evidence: command:git merge-base --is-ancestor v0.3.3 HEAD && uv run pytest tests/test_transcript.py -k "queued_command or other_attachment_types"]

#### Files

- `src/claude_code_wrapper/transcript.py`
- `src/claude_code_wrapper/router.py`
- `tests/fake_claude/fake_claude.py`
- `tests/test_transcript_commands.py`
- `tests/test_command_signals.py`
- `tests/test_fake_claude_commands.py`
- `tests/test_command_runner.py`
- `MEMORY.md` (new)

#### Interfaces

- `transcript.CommandUnknown(_Event)` with `name: str`; part of the `Event` union; parsed from "Unknown command: /x" with or without ". Did you mean /y?".
- SignalBus kind `command_unknown` `{name}`.
- `_await_completion(record, mark, timeout)` returns `("failed", None, "unknown_command", None)` on `command_unknown`.
- Fake claude scenario: `commands.<name>: {echo: "system"|"user", echo_name, stdout, as_user, delay_seconds, hang}`; `$CLAUDE_CONFIG_DIR/fake-keys.jsonl` lines `{"key": "esc", "ts": ...}`.

#### Expected outcome

Every local command on the real echo shapes completes with its stdout, an unknown command fails at once, and the reported `/reload-plugins` sent through the command path completes and frees the slot.

#### Steps

- Probe first (real binary, throwaway dir under `/workdir/workdir/.scratchpad/probe-slash`, never a test): local commands and UserPromptSubmit (a hooks log as in the first probe), `/workdir/foo is broken`, `/etc/hosts`, `/tmp`, `/ is root`; write the dated `(slash-commands-from-chat) probe` entries in a new `MEMORY.md` (ac13). A result that contradicts design D2 or D6, or a fact the probe cannot settle, is returned to the orchestrator as a question before going on.
- Red: add the parser, signal, runner and fake tests (ac1-ac3, ac5-ac11) and update test_unknown_command; run `uv run pytest tests/test_transcript_commands.py tests/test_command_signals.py tests/test_command_runner.py tests/test_fake_claude_commands.py`: they fail.
- Green: change transcript.py, router.py and the fake; run the task's verify: passes. Quote the summary line.

#### Notes

- Completion matches any `command_invoked` after the mark, never the typed name (aliases).
- Ruling, pinned by ac8 and ac9: an unknown command, the suggestion form included, sends no ESC.
- The probe is never a test: tests keep using the fake claude (repo CLAUDE.md).
- The reviewer checks the fake's echo and informational lines against the cited real samples (retro proposal).
- Depends on wrapper-slash-turn-guard (sequenced: both touch router.py).

- 2026-10-27 amended: interrogate item 11 (suggestion form 'Unknown command: /x. Did you mean /y?' fails fast), user decision on the Noted items (real-binary probe of local commands and UserPromptSubmit and of path-like prose, recorded in MEMORY.md, contradictions reported back), builder check (/tmp fails unknown_command), design D6 revised

- 2026-10-29 amended: wrapper main is at v0.3.3 with a queued_command attachment fix in transcript.py, which this task also edits: the wrapper branch rebases onto main and keeps that fix (ac15); release stays 0.4.0

- 2026-10-29 amended: fable ruling 2026-10-29 on the wrapper-command-signals probe: claude sends a bare name that exists on disk (/tmp) to the model; D2 rule unchanged, ac8 uses nonexistent, D8 promotion pins the prose case

- 2026-10-29 done

### S16: orch command turn link

- Status: done
- Files: `src/agents_orchestrator/db/queue.py`, `src/agents_orchestrator/ingester/loop.py`, `tests/test_ingester.py`, `tests/test_agent_session_messaging.py`, `MEMORY.md`
- Verify: `uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint`
- Verified head: fa476aad89cfb94ec93f2917ac5b88e06b85b3f7

#### Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."

Interrogate item 9 (interrogate.md), verbatim: "Hop guard for promoted prompt commands (B, C). A command message stores no `turn_id`, so sends from its promoted turn restart at hop 1 and bypass session_message_max_hops. Set messages.turn_id on `command_completed` with `result=turn` through a status-guarded update by the single writer."

Design D10, verbatim (the hop-guard part): "Hop guard (my call, interrogate item 9): a command message stores no `turn_id` at 202, so sends from its promoted turn (D8) would restart at hop 1 and bypass `session_message_max_hops`. `queue.link_command_turn(conn, wrapper_command_id, turn_id)` is the one writer of the transition "sent command, no turn -> linked turn": `UPDATE messages SET turn_id = ... WHERE kind = 'command' AND status = 'sent' AND wrapper_command_id = ... AND turn_id IS NULL`, called by the ingester when it stores a `command_completed` envelope whose record has `result = 'turn'` and a `turn_id`. For the reverse arrival order (the event stored before the dispatcher's 202 handling), `mark_sent_command` takes that `turn_id` from the stored `command_completed` event in its own guarded update (`dispatching -> sent`). `queue.turn_hop` then finds the command message of the promoted turn, so a send from it counts that message's hop plus one; agents-common's run tracker also sees the promoted turn's completion on the message."

Scope (agents-orchestrator):
- `src/agents_orchestrator/db/queue.py`: `link_command_turn(conn, wrapper_command_id, turn_id) -> bool` (the guarded UPDATE above); `mark_sent_command` (from task orch-dispatch-commands) also sets `turn_id` from an already stored `command_completed` event of that command id with `result = 'turn'`, in the same guarded `dispatching -> sent` update.
- `src/agents_orchestrator/ingester/loop.py`: `_project` calls `queue.link_command_turn` for a `command_completed` envelope whose `data.record` has `result == "turn"` and a non-empty `turn_id`; every other command event projects nothing new.
- `MEMORY.md`: a dated entry tagged `(slash-commands-from-chat)` naming `link_command_turn`, its single-writer transition and why (the hop guard).

#### Acceptance conditions

- ac1: (Docker: CI or a Docker host) storing a command_completed envelope whose record has result turn and a turn_id sets turn_id on the sent command message with that wrapper_command_id; result ok links nothing; a second event never overwrites a set turn_id (new) [evidence: test:tests/test_ingester.py::test_command_completed_turn_links_message]
- ac2: (Docker) when the command_completed event is stored before mark_sent_command runs, mark_sent_command sets turn_id in the same guarded update (new) [evidence: test:tests/test_ingester.py::test_command_turn_linked_when_event_precedes_sent]
- ac3: (Docker) a superleader's "/x" (hop 1) promoted to a turn on the target: a session_send from that turn by the target's leader is stored with hop 2, and with session_message_max_hops 1 it is refused hop_limit (new) [evidence: test:tests/test_agent_session_messaging.py::test_promoted_command_turn_keeps_hop_count]
- ac4: MEMORY.md records the link_command_turn transition under this epic's tag [evidence: command:grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\)" MEMORY.md | grep -q "link_command_turn"]
- ac5: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

#### Files

- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/ingester/loop.py`
- `tests/test_ingester.py`
- `tests/test_agent_session_messaging.py`
- `MEMORY.md`

#### Interfaces

- `queue.link_command_turn(conn, wrapper_command_id: str, turn_id: str) -> bool`: `UPDATE messages SET turn_id = %s WHERE kind = 'command' AND status = 'sent' AND wrapper_command_id = %s AND turn_id IS NULL`.
- `queue.mark_sent_command(conn, id, wrapper_command_id) -> bool` (task orch-dispatch-commands) also writes `turn_id` from a stored `command_completed` event of that command id with `result = 'turn'`.
- Ingester `_project`: `command_completed` with `data.record.result == "turn"` and a `turn_id` -> `link_command_turn`.

#### Expected outcome

A command message whose prompt command became a turn carries that turn id, so a session message sent from the promoted turn counts the right hop and the hop limit holds; the message's turn also shows its completion to API readers such as agents-common.

#### Steps

- Red: add ac1-ac3; on a Docker host run `uv run --frozen pytest tests/test_ingester.py tests/test_agent_session_messaging.py`: they fail (turn_id stays null, hop 1). In this container only ac5 runs.
- Green: queue.py, ingester/loop.py, MEMORY.md; run the task's verify: passes. Quote the summary line; the Docker legs run in CI.

#### Notes

- One writer per transition (design Constraints): `link_command_turn` for sent -> linked, `mark_sent_command` for dispatching -> sent; both guarded (`turn_id IS NULL`).
- If a layering test forbids the ingester importing `db.queue`, return that as a question instead of moving the write elsewhere.
- The ingester stores every envelope first (`insert_events`); the link runs in the same projection transaction.
- Depends on orch-dispatch-commands (`kind`, `wrapper_command_id`, `mark_sent_command`).

- 2026-10-29 done

### S17: wrapper dialog commands

- Status: done
- Files: `src/claude_code_wrapper/config.py`, `src/claude_code_wrapper/session.py`, `src/claude_code_wrapper/router.py`, `tests/fake_claude/fake_claude.py`, `README.md`, `tests/test_command_dialogs.py`, `tests/test_fake_claude_commands.py`
- Verify: `uv run pytest tests/test_command_dialogs.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_registry.py tests/test_readme_config.py tests/test_session_turns.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 24ccb08f4951172e55a940f320dde143ae2c5275

#### Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D7, verbatim: "A `DialogScanner` (a `FatalScanner` over `sessions.commands.dialog_patterns`, default `esc to cancel`, `esc to close`, `esc to clear`, `esc to exit`, `enter to confirm`) is fed the PTY output from the mark. No completion signal and a dialog hit -> wait `dialog_grace_seconds` (2.0, restarted by any PTY output) for a late signal, then ESC; 1.5 s later, if still no `command_output` and the scanner hit again since the ESC, ESC again (budget 3, never two ESCs within 1 s: a double ESC at an empty prompt opens the rewind menu). Output after an ESC -> completed `dismissed`, output = claude's stdout ("Help dialog dismissed"). No output after the budget -> failed `dialog_stuck`. Timeout (`timeout_seconds[name]`, default 60, compact 600) -> ESC, 1.5 s, a second ESC only when a dialog pattern is on screen -> failed `timeout`. Compact is excluded from dialog detection (its own leg). One deadline per command (my call, interrogate item 7): `timeout_seconds[name]` counts from the runner taking the command and is spent by the quiet wait, typing, the completion wait and the dialog leg together (today `wait_quiet` and the completion wait each spend a full `timeout`, about 2x the stated bound). A dialog left open (my call, interrogate item 6): when a command ends `dialog_stuck`, or `timeout` with a dialog pattern still on screen after the last ESC, claude is restarted through the existing relaunch path (`Session._recover`: `_boot(resume=True)`, the same pinned claude session id) before the slot is released, so the next turn never lands in an open dialog (a paste into an open dialog acts on it, probe outA). This wrapper-initiated restart does not count against `max_restarts` (my call: three stuck dialogs must not kill a session), emits the usual restart event, and a failed relaunch takes the crash path's outcome (dead). Dialog commands stay allowed: "dismissed" with claude's own message is the honest answer for a chat with no keyboard (user decision 1)."

Design Bounds, verbatim: "one deadline per command (my call, interrogate item 7): `timeout_seconds[name]` (`default` 60 s, `compact` 600 s; operators may add names), counted from the runner taking the command and spent by the quiet wait (`quiet_seconds` 1.5 s), typing, the completion wait and the dialog leg together; "screen never settled" fails `timeout` at that deadline.", "dialog: `dialog_grace_seconds` 2.0 s after the first footer hit; ESC budget 3, 1.5 s apart, never two ESCs within 1 s; `dialog_stuck` after the budget; all inside the deadline.", "at the deadline: ESC, 1.5 s, a second ESC only with a dialog pattern on screen -> `timeout`.", "dialog still open after `dialog_stuck` or `timeout` (my call, interrogate item 6): one claude relaunch with `--resume` before the slot is released, bounded by `boot.timeout_seconds` (60 s); it does not count against `max_restarts`." and "worst-case slot hold for a non-promoted command: timeout + 1.5 s = about 62 s (default), plus one relaunch of at most `boot.timeout_seconds` 60 s when a dialog stays open."

Interrogate item 6 (interrogate.md), verbatim: "Dialog left open after the ESC budget (C). On `dialog_stuck` or `timeout` with a dialog still on screen, restart claude through the existing restart path before releasing the slot; AC."

Interrogate item 7, verbatim: "One deadline per command (C). wait_quiet plus _await_completion each spend `timeout`, so the real bound is about 2x the stated one; use one deadline and pin it."

Scope (claude-code-wrapper): `config.py` (`CommandsConfig.dialog_grace_seconds: float = 2.0` (ge 0), `dialog_patterns: list[str]` with the five defaults; `CommandsOverride` mirrors both), `session.py` (a dialog scanner over the PTY output, reset at the mark, with "hit since" and "on screen now" queries; an ESC helper that never sends two ESCs within 1 s; a wrapper-initiated restart of claude through the relaunch path with `--resume` that leaves `restarts` unchanged), `router.py` (`_run_command` computes one deadline and passes the remaining time to `wait_quiet` and `_await_completion`; `_await_completion` dialog leg and the conditional second ESC of the timeout leg; result `dismissed`, error `dialog_stuck`; the restart before `end_command` when a dialog is still on screen), `tests/fake_claude/fake_claude.py` (scenario `commands.<name>.dialog: {footer, dismiss_stdout, escs: 1|2|"never"}`: print the footer, write nothing until the given number of ESCs, then the system echo and the stdout; "never" keeps the footer on screen; ESC keys already logged to `fake-keys.jsonl` by wrapper-command-signals), `README.md` (config rows; `### Lifecycle` of `## Slash commands` describes dialogs, the restart and the bound).

Real samples the fake must match: `/workdir/workdir/.scratchpad/probe-slash/summaries/outA.txt` (/model and /config dialogs: system echo written only after ESC; /config needed two ESCs; a paste into an open dialog acted on it), outC.txt (/usage dismissed: "Settings dialog dismissed"), the real transcript `/workdir/workdir/.scratchpad/probe-slash/config/projects/-workdir-workdir--scratchpad-probe-slash-work/64b31430-13c7-48b0-ba54-c6c432f345db.jsonl` (/permissions, /theme echoes). Footers seen: "Esc to cancel", "Esc to clear", "Enter to confirm . Esc to cancel" (design Research, probed).

#### Acceptance conditions

- ac1: a dialog command (fake dialog, footer "Esc to cancel", escs 1) completes with result dismissed and claude's stdout as output, after exactly one ESC sent at least dialog_grace_seconds after the footer (new) [evidence: test:tests/test_command_dialogs.py::test_dialog_command_dismissed_by_escape]
- ac2: a dialog that needs two ESCs (escs 2) is dismissed with two ESCs at least 1.5 s apart (new) [evidence: test:tests/test_command_dialogs.py::test_config_dialog_needs_two_escapes]
- ac3: a dialog that never closes fails dialog_stuck after 3 ESCs, no two within 1 s (new) [evidence: test:tests/test_command_dialogs.py::test_dialog_stuck_after_esc_budget]
- ac4: after dialog_stuck, and after a timeout with the dialog still on screen, claude is relaunched with --resume before the slot is released: the fake is spawned again with the same session id, the session returns to ready, a following prose turn is typed into the fresh prompt (never into the dialog) and restarts is unchanged (new) [evidence: test:tests/test_command_dialogs.py::test_open_dialog_restarts_claude_before_release]
- ac5: a command that only times out with no dialog on screen sends one ESC, fails timeout and does not restart claude; with a dialog on screen a second ESC follows (new) [evidence: test:tests/test_command_dialogs.py::test_timeout_second_escape_only_with_dialog]
- ac6: one deadline: a command whose screen keeps changing for most of timeout_seconds and then never completes fails timeout within timeout_seconds plus 2 s of the runner taking it, not after a second full timeout (new) [evidence: test:tests/test_command_dialogs.py::test_one_deadline_covers_quiet_wait_and_completion]
- ac7: PTY output during the grace restarts it: a slow command printing within 2 s is not ESCed (new) [evidence: test:tests/test_command_dialogs.py::test_grace_restarts_on_output]
- ac8: compact never takes the dialog leg (new) [evidence: test:tests/test_command_dialogs.py::test_compact_excluded_from_dialog_detection]
- ac9: dialog_grace_seconds and dialog_patterns have the D7 defaults and a per-session override (new) [evidence: test:tests/test_command_dialogs.py::test_dialog_config_defaults_and_override]
- ac10: the fake's dialog scenario prints the footer, waits for N ESCs (or never closes), then writes the system echo and stdout (new) [evidence: test:tests/test_fake_claude_commands.py::test_dialog_scenario]
- ac11: every config key is documented with its default [evidence: test:tests/test_readme_config.py::test_defaults_match_model]
- ac12: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_dialogs.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_registry.py tests/test_readme_config.py tests/test_session_turns.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/router.py`
- `tests/fake_claude/fake_claude.py`
- `README.md`
- `tests/test_command_dialogs.py`
- `tests/test_fake_claude_commands.py`

#### Interfaces

- `CommandsConfig.dialog_grace_seconds: float = 2.0`, `CommandsConfig.dialog_patterns: list[str]`; mirrored in `CommandsOverride`.
- Results and errors: `result = "dismissed"`, `error = "dialog_stuck"`.
- A session method for a wrapper-initiated restart of claude through the relaunch path (`_boot(resume=True)`), leaving `Session.restarts` unchanged (for example `Session.restart_for_dialog() -> None`).
- One deadline: `_run_command` passes `deadline - now` to `wait_quiet` and `_await_completion`.
- Fake scenario `commands.<name>.dialog = {"footer": str, "dismiss_stdout": str, "escs": 1 | 2}`.

#### Expected outcome

A dialog command sent from the chat never leaves the session wedged: it is dismissed with claude's own message, or fails `dialog_stuck` or `timeout` inside the D7 bound, and the slot is released.

#### Steps

- Red: add `tests/test_command_dialogs.py` (ac1-ac9) and the fake test (ac10); run `uv run pytest tests/test_command_dialogs.py tests/test_fake_claude_commands.py`: they fail.
- Green: config, session, router, fake, README; run the task's verify: passes. Quote the summary line.

#### Notes

- Reuse `session.FatalScanner` (escape-, whitespace- and case-insensitive matching across chunks) for the dialog scanner.
- ESC count and spacing are read from `fake-keys.jsonl` (D16), never from `fake-inputs.jsonl`.
- Rulings pinned: never two ESCs within 1 s (ac2, ac3); ESC only while a dialog pattern was seen since the last ESC or at the timeout (ac5); compact excluded (ac8); restart only with a dialog still on screen and without spending `max_restarts` (ac4, ac5); one deadline (ac6).
- Reuse the crash relaunch path (`Session._on_exit` and `_recover`); do not add a second boot path.
- Depends on wrapper-command-signals (class-agnostic `_await_completion`, the key log).

- 2026-10-27 amended: interrogate items 6 (restart claude with --resume before releasing the slot when a dialog stays open) and 7 (one deadline per command), design D7 and Bounds revised

- 2026-10-29 done

### S18: orch command outcome

- Status: done
- Files: `src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql`, `src/agents_orchestrator/db/views.py`, `src/agents_orchestrator/api/schemas.py`, `src/agents_orchestrator/api/messages.py`, `openapi.json`, `README.md`, `tests/test_api_messages.py`, `tests/test_migrations.py`
- Verify: `uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint`
- Verified head: 2c018ffc4217459f5af9cf749700b272ffc8dd1c

#### Requirement

User decision F2 (2026-10-29), verbatim: "F2: read-side command outcome on MessageView (orchestrator, migration 0012 partial index; check the next free migration number on the rebased orchestrator branch at /workdir/workdir/.claude/worktrees/slash-commands-from-chat/agents-orchestrator, which contains main's 0011), agents-common run tracker handles kind=command outcomes per the architect's mapping, agents-common release v0.4.0 (tag pending mx-34 confirmation; write the task so the orchestrator session pushes the tag after confirmation), then pin bumps in agents-webhook and agents-schedule."

Next free migration number, checked 2026-10-29: the rebased epic branch ends at `0011_drop_feed_cursor.sql` (main's), so this is `0012`.

Architect brief, verbatim: "F2: a command message stays `sent` and never gets a turn, so `runs.track` waits until it gives up with `timeout`." and "**Read-side outcome (chosen):** the message query looks up the latest `command_completed` or `command_failed` event for the message's `wrapper_command_id`, as `mark_sent_command` already does.
  - For: no new writer, and no race between the event and the dispatcher's 202.
  - Against: a JSON lookup on every message read.
  - Mitigation: migration `0012` adds a partial index on the command record id. The build briefly blocks event inserts."
"5. `orch-command-outcome` (orchestrator)
   - Files: `0012_command_outcome_index.sql`, `db/views.py`, `api/schemas.py` (new `CommandOutcomeView {state, result, error, turn_id, at}` as `MessageView.command`), `api/messages.py`, `openapi.json`.
   - Tests (new, in `tests/test_api_messages.py`, CI only): `test_message_command_outcome_completed`, `..._failed_unknown_command`, `..._cancelled`, `test_message_command_none_for_turns_and_pending`."

Design D19, verbatim: "`MessageView.command` (new `CommandOutcomeView {state, result, error, turn_id, at}`, null for turn messages and for a command with no outcome yet) is looked up at query time: the latest `command_completed` or `command_failed` event of the message's agent whose `data.record.id` equals the message's `wrapper_command_id` (as `mark_sent_command` already does); `state`, `result`, `error` and `turn_id` come from the event's record, `at` is the event's `ts`; a cancelled command is a `command_failed` event whose record state is `cancelled`. Migration `0012_command_outcome_index.sql` adds a partial index on the command record id over those two event types (my call: keyed by `agent_id` and the record id, the lookup's two equality predicates); its build briefly blocks event inserts. No new writer, no new message status."

Scope (agents-orchestrator): `src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql` (new; `CREATE INDEX IF NOT EXISTS ... ON events (agent_id, (data -> 'record' ->> 'id')) WHERE type IN ('command_completed', 'command_failed')`), `src/agents_orchestrator/db/views.py` (`_MESSAGE_SELECT` gains a `LEFT JOIN LATERAL` on that lookup, so `get_message` and `list_messages` both carry it), `src/agents_orchestrator/api/schemas.py`, `src/agents_orchestrator/api/messages.py` (`_message_view`), `openapi.json` (regenerated), README.md (the message view field list documents `command` (null, or the command's outcome once it finished: `state`, `result`, `error`, `turn_id`, `at`)), `tests/test_api_messages.py`, `tests/test_migrations.py`. Test no longer accurate (named): `tests/test_migrations.py::test_fresh_database_gets_all_tables` and `test_presets_migration_on_existing_sessions` list every migration by number; they gain 0012.

#### Acceptance conditions

- ac1: (Docker: CI or a Docker host) a sent command message whose agent stored command_completed for its wrapper_command_id (record state completed, result ok) returns command {state: completed, result: ok, error: null, turn_id: null, at: the event ts} from GET /api/v1/messages/{id} and from the session's message list (new) [evidence: test:tests/test_api_messages.py::test_message_command_outcome_completed]
- ac2: (Docker) a command_failed record with error unknown_command returns command {state: failed, error: unknown_command}; a later event for the same command id wins over an earlier one; an event of another agent with the same record id is ignored (new) [evidence: test:tests/test_api_messages.py::test_message_command_outcome_failed_unknown_command]
- ac3: (Docker) a command_failed record with state cancelled returns command {state: cancelled} (new) [evidence: test:tests/test_api_messages.py::test_message_command_outcome_cancelled]
- ac4: (Docker) command is null for a turn message, for a queued command message and for a sent command with no outcome event yet (new) [evidence: test:tests/test_api_messages.py::test_message_command_none_for_turns_and_pending]
- ac5: (Docker) migration 0012 applies on a fresh database after 0001-0011 and on rerun (updated, named) [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- ac6: (Docker) an existing database migrates through 0012 (updated, named) [evidence: test:tests/test_migrations.py::test_presets_migration_on_existing_sessions]
- ac7: the migration is tracked as 0012 next to main's 0011 and creates a partial index on the command record id [evidence: command:test -n "$(git ls-files src/agents_orchestrator/db/migrations/0011_drop_feed_cursor.sql)" && test -n "$(git ls-files src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql)" && grep -q "command_completed" src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql && grep -qi "IF NOT EXISTS" src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql]
- ac8: openapi.json matches the app and carries CommandOutcomeView [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac9: README documents the command field of the message view [evidence: command:grep -qF '`command` (null' README.md]
- ac10: the Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

#### Files

- `src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql`
- `src/agents_orchestrator/db/views.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/messages.py`
- `openapi.json`
- `README.md`
- `tests/test_api_messages.py`
- `tests/test_migrations.py`

#### Interfaces

- `api/schemas.py`: `CommandOutcomeView(BaseModel)`: `state: Literal["completed", "failed", "cancelled"]`, `result: str | None`, `error: str | None`, `turn_id: str | None`, `at: datetime`; `MessageView.command: CommandOutcomeView | None`.
- `db/views.py` `_MESSAGE_SELECT`: `LEFT JOIN LATERAL (SELECT e.ts, e.data -> 'record' AS record FROM events e WHERE e.agent_id = m.agent_id AND e.type IN ('command_completed', 'command_failed') AND e.data -> 'record' ->> 'id' = m.wrapper_command_id ORDER BY e.id DESC LIMIT 1) co ON m.kind = 'command'` (shape; the builder may name columns).
- Migration `0012_command_outcome_index.sql`: `CREATE INDEX IF NOT EXISTS events_command_record_id ON events (agent_id, (data -> 'record' ->> 'id')) WHERE type IN ('command_completed', 'command_failed')`.
- The wire shape agents-common's `Message.command` reads (task common-command-outcome).

#### Expected outcome

`GET /api/v1/messages/{id}` and the session's message list show, for a command message, the command's outcome once it finished, with no new writer and no new message status.

#### Steps

- Red: write the four tests in `tests/test_api_messages.py` (insert the `command_*` events rows directly, as the ingester would store them) and add 0012 to the migration lists in `tests/test_migrations.py`; in CI or on a Docker host they fail.
- Green: migration, view, schema, `_message_view`, regenerate `openapi.json`, README; run the task's verify (Docker-free part) and quote the summary line; the Docker tests run in CI.

#### Notes

- Read-side only (design D19): the ingester stays the only writer of `events`; no UPDATE of `messages`.
- `mark_sent_command` (`db/queue.py`) already looks up a command's event by `data -> 'record' ->> 'id'` and agent: reuse that predicate.
- A cancelled command arrives as `command_failed` with record `state = 'cancelled'`.
- Migration 0012 is the next free number on the rebased epic branch (main's 0011_drop_feed_cursor). The todo epic immediate-message-delivery-w planned `0012_message_priority.sql`; it renumbers when claimed.
- Builds on orch-slash-js-whitespace (README touched by both).

- 2026-10-29 done: 1 fix round: added promoted-command turn_id test

### S19: wrapper prompt command turn

- Status: done
- Files: `src/claude_code_wrapper/router.py`, `src/claude_code_wrapper/session.py`, `tests/fake_claude/fake_claude.py`, `README.md`, `tests/test_command_prompt_turn.py`, `tests/test_fake_claude_commands.py`, `MEMORY.md`
- Verify: `uv run pytest tests/test_command_prompt_turn.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_turn_resume.py tests/test_session_turns.py tests/test_stop_gate.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 2fe4eb72ad2f48d3196e5e0acaefd3ec428a3393

#### Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D8, verbatim: "`_on_user_prompt_submit` publishes `prompt_submitted` on the SignalBus while a command runs. On that signal the runner calls `Session.adopt_turn(line, origin)` (origin client -> turn origin `client`, agent -> `agent`, idle -> `agent`): a running `TurnRecord` is created and persisted while the slot is already held, `router._last_marker` is set to its turn id (so its Stop is not dropped as stale), `turn_started` and `user_message` are emitted; the command record completes at once with result `turn` and `turn_id`. The turn then ends like any turn (Stop, interrupt, `turn_max_seconds`). Rulings (my call): after a promotion the runner stops; commands still queued stay queued for the promoted turn's Stop. In the agent same-turn path (commands run at a held turn's Stop, D9), a prompt command does not create a new record: the held turn continues as the prompt command's turn (`_commands_turn` cleared, `_last_marker` = the held turn id, result `turn` with that turn id) and no continue prompt is typed. The hold is released through a session API (my call, interrogate item 10; for example `Session.release_commands_hold(record)`), which clears the session's own `_commands_turn` (session.py `continue_turn`, `interrupt`), so an interrupt on the continued turn sends ESC like any running turn instead of ending the record with no ESC. Real-binary probe (user decision): task wrapper-prompt-command-turn settles, in a throwaway dir under `/workdir/workdir/.scratchpad/probe-slash` and recorded in the wrapper's `MEMORY.md`, whether Stop fires after a promoted prompt-command turn and whether plugin commands fire UserPromptSubmit; a result that contradicts the design (or a fact the probe cannot settle, for example with no credentials for a model call) is reported back, not worked around."

Interrogate item 10 (interrogate.md), verbatim: "Held-turn interrupt (B). When the held turn continues as a prompt-command turn, `_commands_turn` is not cleared (session.py:702-703, 1128-1131), so an interrupt ends the record without ESC. Release the hold through a session API; AC that an interrupt on that turn sends ESC."

User decision (probes), verbatim: "the owning tasks (prompt-command turn, command signals) get a requirement to settle by a real-binary probe in a throwaway dir under /workdir/workdir/.scratchpad/probe-slash, recorded in the component MEMORY.md, whether Stop fires after a promoted prompt-command turn, whether plugin commands fire UserPromptSubmit, whether local commands never fire it, and how claude treats path-like prose such as '/workdir/foo is broken'; a probe result that contradicts the design is reported back, not worked around."
This task's probe facts (design D8): whether Stop fires after a promoted prompt-command turn (a project command such as `.claude/commands/hello.md`, as in the first probe) and whether a plugin-namespaced command (for example `/<plugin>:<command>` from a plugin installed in the throwaway config) fires UserPromptSubmit. The probe runs the real binary in a new throwaway directory under `/workdir/workdir/.scratchpad/probe-slash` (never a session workdir, never a test), and each fact is recorded as a dated entry tagged `(slash-commands-from-chat) probe` in the wrapper's `MEMORY.md` (created by wrapper-command-signals), with the observed result and the raw evidence path. A fact the probe cannot settle (the Stop needs a model call; with no credentials it cannot run) is recorded as "not settled: <why>" and returned to the orchestrator as a question. A result that contradicts design D8 is reported back and not worked around (design Assumptions: no UserPromptSubmit for plugin commands means an amend of this task to promote on the echo plus isMeta pair).

Scope (claude-code-wrapper): `router.py` (`_on_user_prompt_submit` publish; `_await_completion` promotion leg; the runner stops after a promotion; the held-turn branch releases the hold through the session API), `session.py` (`adopt_turn(text, origin) -> TurnRecord`: create, persist, arm the turn watch, keep busy; `end_command` then leaves busy to the turn; the hold-release API that clears `_commands_turn` for the continued held turn), `tests/fake_claude/fake_claude.py` (scenario `commands.<name>.prompt: true`: the `<command-message>` user echo, an isMeta user line with the expanded body, UserPromptSubmit, then a normal turn with its steps and Stop), `README.md` (`### Lifecycle`: prompt and skill commands run as real turns), `MEMORY.md` (the probe entries).

Real sample the fake must match: design Research, probed: "/hello world (.claude/commands/hello.md): user line `<command-message>hello</command-message><command-name>/hello</command-name><command-args>world`, then an isMeta user line with the expanded body, then a normal model turn. UserPromptSubmit fired". Stop at the end of that turn is inferred (no credentials in the first probe): the fake pins it (design Assumptions) until this task's probe settles it.

#### Acceptance conditions

- ac1: a prompt command (fake prompt true) becomes a turn: turn_started, user_message, the command completes result turn with its turn_id, the Stop completes that turn with its final_text and no "ignoring stale Stop" is logged (new) [evidence: test:tests/test_command_prompt_turn.py::test_prompt_command_promotes_to_turn]
- ac2: the promoted turn is interruptible: POST /interrupt ends it interrupted and the session returns to ready (new) [evidence: test:tests/test_command_prompt_turn.py::test_prompt_command_turn_is_interruptible]
- ac3: a command queued behind a promoted prompt command stays queued and runs only after the promoted turn's Stop; nothing is typed while that turn runs (new) [evidence: test:tests/test_command_prompt_turn.py::test_queued_commands_wait_for_promoted_turn]
- ac4: an agent-origin prompt command run at a held turn's Stop continues that turn: no new turn record, no continue prompt, result turn with the held turn_id (new) [evidence: test:tests/test_command_prompt_turn.py::test_agent_prompt_command_continues_held_turn]
- ac5: an interrupt on that continued held turn sends one ESC (fake-keys.jsonl), ends the turn interrupted and returns the session to ready; the session's commands hold is cleared (new) [evidence: test:tests/test_command_prompt_turn.py::test_interrupt_on_continued_held_turn_sends_escape]
- ac6: a promoted turn after an earlier completed turn is not dropped as stale (second-turn case of the discovery fix-as-ac) (new) [evidence: test:tests/test_command_prompt_turn.py::test_promoted_turn_after_earlier_turn_completes]
- ac7: the fake's prompt scenario writes the echo, the isMeta body, fires UserPromptSubmit, runs the turn and fires Stop (new) [evidence: test:tests/test_fake_claude_commands.py::test_prompt_command_scenario]
- ac8: MEMORY.md records the real-binary probe of this task: whether Stop fires after a promoted prompt-command turn and whether a plugin command fires UserPromptSubmit, each with its observed result or "not settled" [evidence: command:grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\) probe" MEMORY.md | grep -qi "promoted" && grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\) probe" MEMORY.md | grep -qi "plugin"]
- ac9: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_prompt_turn.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_turn_resume.py tests/test_session_turns.py tests/test_stop_gate.py && uv run ruff check . && uv run ruff format --check .]
- ac10: a command whose name claude sends to the model with no command echo (fake scenario `commands.<name>.prose: true`: a plain user prompt line, UserPromptSubmit, a turn, Stop; the real case `/tmp`, probe 2026-10-29) is promoted on `prompt_submitted` alone, completes result `turn` with its turn_id, the Stop completes the turn, and the session is ready within the fake turn, never at `timeout_seconds` (new) [evidence: test:tests/test_command_prompt_turn.py::test_prose_dispatched_command_promotes_to_turn]

#### Files

- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/session.py`
- `tests/fake_claude/fake_claude.py`
- `README.md`
- `tests/test_command_prompt_turn.py`
- `tests/test_fake_claude_commands.py`
- `MEMORY.md`

#### Interfaces

- `Session.adopt_turn(text: str, *, origin: Origin) -> TurnRecord` (turns.Origin: client, initial, agent, peer).
- A session API that releases the commands hold of a held turn that continues as a prompt-command turn (for example `Session.release_commands_hold(record: TurnRecord) -> None`), clearing `Session._commands_turn`.
- SignalBus kind `prompt_submitted`; command `result = "turn"`, `CommandRecord.turn_id` = the promoted (or held) turn id.

#### Expected outcome

`/init`, a skill or a plugin command sent from the chat runs as a normal turn with assistant rows, turn accounting and the usual bounds, and the session is ready again at its Stop.

#### Steps

- Probe first (real binary, throwaway dir under `/workdir/workdir/.scratchpad/probe-slash`, never a test): Stop after a promoted project command, UserPromptSubmit for a plugin command; append the dated `(slash-commands-from-chat) probe` entries to `MEMORY.md` (ac8). A contradiction, or a fact the probe cannot settle (no credentials for the model call), is returned to the orchestrator as a question before going on.
- Red: add `tests/test_command_prompt_turn.py` (ac1-ac6) and the fake test (ac7); run them: they fail (the command times out; the Stop is dropped as stale).
- Green: router, session, fake, README; run the task's verify: passes. Quote the summary line.

#### Notes

- Rulings pinned: queued commands stay queued after a promotion (ac3); the held-turn branch (ac4); the hold release and its ESC on interrupt (ac5).
- The busy slot is already held by `begin_command` (idle runner) or `hold_for_commands` (held turn); `adopt_turn` must not set busy twice or emit a second `session_state`.
- If the logged-in contract check later shows no UserPromptSubmit for plugin commands, this task is amended to promote on the echo plus isMeta pair (design Assumptions).
- Depends on wrapper-dialog-commands (sequenced: router.py, session.py and the fake).

- 2026-10-27 amended: interrogate item 10 (release the held-turn hold through a session API so an interrupt sends ESC), user decision on the Noted items (real-binary probe of Stop after a promoted turn and of plugin commands and UserPromptSubmit, recorded in MEMORY.md, contradictions reported back), design D8 revised

- 2026-10-29 amended: fable ruling 2026-10-29 on the wrapper-command-signals probe: claude sends a bare name that exists on disk (/tmp) to the model; D2 rule unchanged, ac8 uses nonexistent, D8 promotion pins the prose case

- 2026-10-29 done

### S20: common command outcome

- Status: done
- Files: `src/agents_common/orchestrator.py`, `src/agents_common/runs.py`, `src/agents_common/fake_orchestrator.py`, `tests/test_runs.py`, `tests/test_orchestrator_client.py`, `README.md`
- Verify: `uv run pytest tests/test_runs.py tests/test_orchestrator_client.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 4d495171ff9cd299a132f7082909896995bb232c

#### Requirement

User decision F2 (2026-10-29), verbatim: "F2: read-side command outcome on MessageView (orchestrator, migration 0012 partial index; check the next free migration number on the rebased orchestrator branch at /workdir/workdir/.claude/worktrees/slash-commands-from-chat/agents-orchestrator, which contains main's 0011), agents-common run tracker handles kind=command outcomes per the architect's mapping, agents-common release v0.4.0 (tag pending mx-34 confirmation; write the task so the orchestrator session pushes the tag after confirmation), then pin bumps in agents-webhook and agents-schedule."

Architect brief, verbatim: "6. `common-command-outcome` (agents-common)
   - Files: `orchestrator.py` (new `Message.command`), `runs.py` (`track`), `fake_orchestrator.py` (new `complete_command` and `fail_command`).
   - Mapping in `track`:

     | Command outcome | Run result |
     |---|---|
     | completed: ok, dismissed, skipped_cache | handled |
     | failed (e.g. unknown_command, dialog_stuck, timeout) | failed, reason `command_<error>` |
     | cancelled | failed, reason `command_cancelled` |
     | completed with result `turn` | decided by the existing turn checks |

   - Tests in `tests/test_runs.py`: `test_track_command_completed_is_handled`, `test_track_command_failed_reason_is_error_code`, `test_track_command_cancelled_is_failed`, `test_track_promoted_command_waits_for_turn`, `test_track_command_pending_times_out`."

Design D20, verbatim: "A command with no outcome yet keeps waiting and ends `timeout` as today; a failed outcome with no error code reads `command_failed` (my call). `fake_orchestrator` gains `complete_command` and `fail_command`."

The wire shape is the orchestrator's `MessageView.command` (task orch-command-outcome, design D19): null, or `{state, result, error, turn_id, at}` with `state` one of `completed`, `failed`, `cancelled`.

Scope (agents-common, branch from origin `main`): `src/agents_common/orchestrator.py` (new `CommandOutcome` model, `Message.command: CommandOutcome | None = None`), `src/agents_common/runs.py` (`track` per the mapping), `src/agents_common/fake_orchestrator.py` (`complete_command(message_id, result="ok", turn_id=None)` marks the message `sent` with a completed outcome; `fail_command(message_id, error, state="failed")` with `state` `failed` or `cancelled` marks it `sent` with that outcome), `tests/test_runs.py`, `tests/test_orchestrator_client.py` (the client parses `command`), README.md (`## runs`: `track` judges a command message by its outcome, with the reasons).

#### Acceptance conditions

- ac1: a command message completed with result ok, dismissed or skipped_cache finishes the run handled with no reason (new) [evidence: test:tests/test_runs.py::test_track_command_completed_is_handled]
- ac2: a failed command with error unknown_command, dialog_stuck or timeout finishes the run failed with reason command_unknown_command, command_dialog_stuck or command_timeout; a failed outcome with no error reads command_failed (new) [evidence: test:tests/test_runs.py::test_track_command_failed_reason_is_error_code]
- ac3: a cancelled command finishes the run failed with reason command_cancelled (new) [evidence: test:tests/test_runs.py::test_track_command_cancelled_is_failed]
- ac4: a command completed with result turn is decided by the turn: running returns None, a completed turn is handled, a failed turn is turn_failed (new) [evidence: test:tests/test_runs.py::test_track_promoted_command_waits_for_turn]
- ac5: a sent command message with no outcome returns None until the timeout, then finishes failed timeout (new) [evidence: test:tests/test_runs.py::test_track_command_pending_times_out]
- ac6: the existing turn mapping is unchanged [evidence: test:tests/test_runs.py::test_track_completed_is_handled]
- ac7: the client parses Message.command from the fake's message view, and it is None for a turn message (new) [evidence: test:tests/test_orchestrator_client.py::test_message_command_outcome_roundtrip]
- ac8: README names the command reasons [evidence: command:grep -q "command_cancelled" README.md]
- ac9: the named tests and lint pass [evidence: command:uv run pytest tests/test_runs.py tests/test_orchestrator_client.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_common/orchestrator.py`
- `src/agents_common/runs.py`
- `src/agents_common/fake_orchestrator.py`
- `tests/test_runs.py`
- `tests/test_orchestrator_client.py`
- `README.md`

#### Interfaces

- `agents_common.orchestrator.CommandOutcome(_Model)`: `state: str`, `result: str | None = None`, `error: str | None = None`, `turn_id: str | None = None`, `at: datetime | None = None`; `Message.command: CommandOutcome | None = None`.
- `agents_common.runs.track(...)`: same signature and return; order of checks: completed turn -> handled; message failed/cancelled -> `message_<status>`; failed turn -> `turn_failed`; command outcome (when `turn` is None and the outcome is not completed with result `turn`) -> handled / `command_<error>` / `command_failed` / `command_cancelled`; timeout.
- `FakeOrchestrator.complete_command(message_id: int, result: str = "ok", turn_id: str | None = None) -> None`; `FakeOrchestrator.fail_command(message_id: int, error: str | None, state: str = "failed") -> None` (`state` `failed` or `cancelled`).

#### Expected outcome

A run whose prompt the orchestrator stored as a command finishes by the command's outcome instead of waiting for a turn until `timeout`.

#### Steps

- Red: write the five `test_track_command_*`/`test_track_promoted_command_waits_for_turn` tests and `test_message_command_outcome_roundtrip`; run `uv run pytest tests/test_runs.py tests/test_orchestrator_client.py`: they fail (no `complete_command`).
- Green: model, fake methods, `track` mapping, README; run the task's verify. Quote the summary line.

#### Notes

- `track_delivery` (reuse path) already finishes on `sent`; unchanged.
- A promoted command (result `turn`) gets its `turn` from the orchestrator's turn link (orch-command-turn-link), so the existing turn checks decide it.
- Wire shape from orch-command-outcome (design D19). The todo epic immediate-message-delivery-w also edits `orchestrator.py` and `fake_orchestrator.py` (`Message.turn_id`) and plans agents-common 0.4.0; it rebases on this and renumbers its release when claimed.
- `model` is opus by the file-count rule (6 files).

- 2026-10-29 done

### S21: wrapper commands after stop

- Status: done
- Files: `src/claude_code_wrapper/router.py`, `README.md`, `tests/test_command_turn_resume.py`, `tests/test_api_commands.py`
- Verify: `uv run pytest tests/test_command_turn_resume.py tests/test_api_commands.py tests/test_stop_gate.py tests/test_command_runner.py tests/test_command_prompt_turn.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: cd9bed696a48b25e7d802c9bed21c0a773918c4d

#### Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards." User request, verbatim: "Allow these commands to be run from chat window at any moment."

Design D9, verbatim: "The orchestrator dispatches a command even to a busy agent (D10); the wrapper queues it and runs it at the running turn's Stop (Claude Code itself holds commands typed while it responds until the turn ends: parity). When every pending command has origin `client`, `_stop_gate` lets the Stop complete the turn normally (`turn_completed`, final text intact) and the idle runner starts after the turn completed; no `continue_prompt`, no `turn_resumed`. Agent-origin commands keep the same-turn resume. Slot handover (my call, interrogate item 4): the router takes the slot for the queued client commands (`_start_idle_runner`, `Session.begin_command`) synchronously right after `session.complete` and before any await (onTurnComplete, the callback), so a `POST /turns` right after `turn_completed` gets 409 `busy` until the queued commands drained; prose can no longer take the slot ahead of them. This behaviour is isolated in task wrapper-commands-after-stop, so a gate change (for example interrupt and run now) is an amend of that one task (user decision 2)."

Interrogate item 4 (interrogate.md), verbatim: "Slot handover at Stop (B, C; A judged it no-hang). The idle runner starts after the awaited onTurnComplete hooks, so prose can take the slot before queued commands. Take the slot for queued commands at Stop before any await; AC: a POST /turns right after turn_completed gets 409 until the commands drain."

User decision, verbatim: "Keep [...] the mid-turn behaviour isolated in one task." and "Do not change the two gate questions' defaults (deny list exists; mid-turn commands accepted at once and run at the turn's Stop)".

Scope (claude-code-wrapper): `router.py` (`_stop_gate` client-only leg returns None; in `_on_stop`, right after `session.complete` returns the completed record and before `_after_turn` is awaited, `_start_idle_runner` takes the slot for the queued client commands), `README.md` (`### Lifecycle`: client commands sent during a turn run after it completes, before any new turn; agent commands resume the same turn).

Tests no longer accurate (named): `tests/test_api_commands.py::test_client_command_during_turn_resumes_turn` pins a same-turn resume with the continue prompt for a client command; D9 changes it, so it becomes `test_client_command_during_turn_runs_after_turn_completes`. In `tests/test_command_turn_resume.py` the tests that use origin `client` only to exercise the same-turn resume (`test_command_runs_at_stop_and_turn_resumes`, `test_interrupt_cancels_queued_and_running`, `test_crash_mid_command_follows_k12`, `test_turn_max_seconds_counts_through_command`, `test_usage_accumulates_across_command`, `test_deferred_reason_and_resumed_cause`) switch to origin `agent`, which keeps that behaviour; `test_onstop_block_keeps_command_queued`, `test_background_defer_keeps_command_queued`, `test_interrupt_before_stop_cancels_queued` and the mixed-origin `test_continue_prompt_lists_results_with_same_marker` stay as they are.

#### Acceptance conditions

- ac1: a client command queued during a turn runs after the turn completed: turn_completed with the turn's final_text, then command_started and command_completed, no turn_resumed, no continue prompt typed, all inputs typed while idle (new) [evidence: test:tests/test_command_turn_resume.py::test_client_only_commands_run_after_turn_completes_without_continue_prompt]
- ac2: an agent command queued during a turn still runs at the Stop and resumes the same turn with the continue prompt (new) [evidence: test:tests/test_command_turn_resume.py::test_agent_commands_still_resume_same_turn]
- ac3: through the API, POST /commands during a turn answers 202 queued with the turn_id and completes after the turn (renamed from test_client_command_during_turn_resumes_turn) [evidence: test:tests/test_api_commands.py::test_client_command_during_turn_runs_after_turn_completes]
- ac4: slot handover: with a slow onTurnComplete hook and client commands queued, a POST /turns sent right after turn_completed answers 409 busy until the queued commands completed, then 202; the session never shows ready between turn_completed and the first command_started (new) [evidence: test:tests/test_api_commands.py::test_turn_refused_until_queued_client_commands_drain]
- ac5: an interrupted turn cancels its queued client commands (ruling, unchanged pin) [evidence: test:tests/test_command_turn_resume.py::test_interrupt_before_stop_cancels_queued]
- ac6: a mixed agent and client queue resumes the turn once with every result listed [evidence: test:tests/test_command_turn_resume.py::test_continue_prompt_lists_results_with_same_marker]
- ac7: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_turn_resume.py tests/test_api_commands.py tests/test_stop_gate.py tests/test_command_runner.py tests/test_command_prompt_turn.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/router.py`
- `README.md`
- `tests/test_command_turn_resume.py`
- `tests/test_api_commands.py`

#### Interfaces

- No API change: `POST /v1/sessions/{id}/commands` during a turn answers 202 `queued` with `turn_id`, as today.

#### Expected outcome

A command a user sends while the agent works waits for that turn's Stop; the turn completes untouched and the command then runs on the idle session. No fabricated "continue" prompt appears for a human-sent command.

#### Steps

- Red: add ac1, ac2 and ac4, rename and rewrite the API test (ac3), switch the named resume tests to origin agent; run `uv run pytest tests/test_command_turn_resume.py tests/test_api_commands.py`: ac1, ac3 and ac4 fail.
- Green: change `_stop_gate` and the post-completion runner start, README; run the task's verify: passes. Quote the summary line.

#### Notes

- Ruling, pinned by ac5: an interrupted or failed turn cancels its queued client commands (today's behaviour, kept).
- Ruling, pinned by ac4: the slot is taken for queued client commands synchronously after `session.complete`, before `_after_turn` is awaited (`begin_command` is synchronous; no await in between).
- A gate change of the mid-turn behaviour amends only this task (user decision 2).
- Depends on wrapper-prompt-command-turn (sequenced: router.py).

- 2026-10-27 amended: interrogate item 4 (take the slot for queued client commands at Stop before any await; POST /turns gets 409 until they drain), design D9 revised; gate default kept (run at the turn's Stop)

- 2026-10-29 done

### S22: common release 0.4.0

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `CHANGELOG.md`, `README.md`, `tests/test_release.py`
- Verify: `uv run pytest tests/test_release.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: e90008012264e46610b458465fca7468c00f57c4

#### Requirement

User decision F2 (2026-10-29), verbatim: "[...] agents-common release v0.4.0 (tag pending mx-34 confirmation; write the task so the orchestrator session pushes the tag after confirmation), then pin bumps in agents-webhook and agents-schedule."

Architect brief, verbatim: "7. `common-release-0-4-0` (a minor release), then two pin tasks".

Design D14 (amended 2026-10-29), verbatim: "agents-common 0.4.0 (minor: `Message.command`, D20) is released by common-release-0-4-0; its tag waits for mx-34's confirmation and the orchestrator session pushes it after that."

Scope (agents-common, mirrors done task common-release-v0-3-0 of epic orchestrator-rename-sessions):
- `pyproject.toml` `version = "0.4.0"`; `uv.lock` refreshed.
- `CHANGELOG.md`: `## v0.4.0` on top: `orchestrator`: `Message.command` (`CommandOutcome`: `state`, `result`, `error`, `turn_id`, `at`; needs agents-orchestrator with `MessageView.command`); `runs.track` judges a command message by its outcome (reasons `command_<error>`, `command_cancelled`); `fake_orchestrator`: `complete_command`, `fail_command`. No breaking change.
- `README.md` install line `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.4.0`; `tests/test_release.py` `INSTALL` and the expected version 0.4.0.
- Release step, run by the orchestrator session (never a subagent): the agents-common PR merges to `main` through the normal PR flow; the session sends version, epic, live and replaces to the leader and waits for mx-34's confirmation; only then it pushes tag `v0.4.0` on the merge commit (irreversible, listed in design.md), confirms `uv pip install "agents-common @ git+https://github.com/szymonrychu/agents-common@v0.4.0"` in a fresh venv, and the pin tasks webhook-common-pin-0-4-0, schedule-common-pin-0-4-0 and mxc-command-outcome start. ac3 is checked by the orchestrator session after the push; the implementer and the reviewer check ac1, ac2 and ac4.

#### Acceptance conditions

- ac1: version, CHANGELOG, README install line and package metadata agree on 0.4.0 (updated) [evidence: test:tests/test_release.py::test_versions_agree]
- ac2: CHANGELOG's top section is v0.4.0 and names Message.command [evidence: command:grep -m1 '^## v' CHANGELOG.md | grep -q 'v0.4.0' && grep -q 'Message.command' CHANGELOG.md]
- ac3: (checked by the orchestrator session after mx-34 confirmed and it pushed the tag) tag v0.4.0 exists on origin at the main merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.0)"]
- ac4: the release test and lint pass [evidence: command:uv run pytest tests/test_release.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`
- `tests/test_release.py`

#### Interfaces

- Tag `v0.4.0` on the agents-common main merge commit; install string `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.4.0`.

#### Expected outcome

agents-common 0.4.0 is documented, versioned and, after mx-34's confirmation and the release step, tagged on origin.

#### Steps

- Red: set `INSTALL` and the expected version in `tests/test_release.py` to 0.4.0; `uv run pytest tests/test_release.py` fails.
- Green: bump, `uv lock`, CHANGELOG, README; run the task's verify. End "ready for tag".
- Orchestrator session, after merge: send version 0.4.0, epic slash-commands-from-chat, live (whether the tag changes anything running: no service image changes until the pins deploy) and replaces (v0.3.0) to the leader; push the tag only after mx-34 confirms; then check ac3 and run the install in a fresh venv.

#### Notes

- Mirrors done task orchestrator-rename-sessions/common-release-v0-3-0.
- The tag push is an orchestrator-session step (the permission classifier blocks subagent live actions; retro proposal). Tags are never re-pointed.
- The todo epic immediate-message-delivery-w planned its own common-release-0-4-0; this epic lands first, so that one becomes 0.5.0 when claimed.

- 2026-10-29 done: merged PR #4 as 0809056 (main CI green), tag v0.4.0 pushed on it

### S23: wrapper command docs

- Status: done
- Files: `README.md`, `config.example.yaml`, `src/claude_code_wrapper/data/config.example.yaml`, `src/claude_code_wrapper/data/examples/workbench.config.yaml`, `tests/test_slash_commands_docs.py`
- Verify: `uv run pytest tests/test_slash_commands_docs.py tests/test_readme_api.py tests/test_readme_config.py tests/test_examples.py tests/test_config.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 6b4353e729402f34162a75f8affbe3eb855df5b2

#### Requirement

Design D17, verbatim: "README `## Slash commands` (tool, endpoint, lifecycle, configuration, limits) describes any name, args, the deny list, the classes and bounds; the Limits paragraph "the five names above are the whole set" goes. `data/examples/workbench.config.yaml` sets `client: ["*"]`; tatara and magic-trainer keep their agent lists. `config.example.yaml` documents `deny`, `dialog_grace_seconds`, `dialog_patterns`."

User decision (gate brief): "Replace the five structured command params [...] with free-text `args` everywhere, including the ccw MCP `command` tool and the example configs, with no compatibility shim".

Scope (claude-code-wrapper): `README.md` `## Slash commands` (all six subsections, Limits rewritten: what runs, the deny list, dialog and prompt classes, the bounds of design Bounds), `config.example.yaml` and `src/claude_code_wrapper/data/config.example.yaml` (commented `commands:` block with `deny`, `dialog_grace_seconds`, `dialog_patterns`), `src/claude_code_wrapper/data/examples/workbench.config.yaml` (`client: ["*"]`, its comment), `tests/test_slash_commands_docs.py`.

Tests no longer accurate (named): `tests/test_slash_commands_docs.py::test_workbench_example_enables_commands` pins the client list to the five built-ins (`ALL_COMMANDS`); the example now allows `"*"`. `::test_config_example_documents_command_keys` gains the three new keys.

#### Acceptance conditions

- ac1: README Slash commands keeps its six subsections and names the deny list, dialog dismissal, prompt commands as turns and the bounds (updated) [evidence: test:tests/test_slash_commands_docs.py::test_readme_slash_commands_content]
- ac2: the five-name Limits sentence is gone [evidence: command:! grep -q "the five names above are the whole set" README.md]
- ac3: the example config documents deny, dialog_grace_seconds and dialog_patterns with the model defaults (updated) [evidence: test:tests/test_slash_commands_docs.py::test_config_example_documents_command_keys]
- ac4: the workbench example allows client ["*"] (updated) [evidence: test:tests/test_slash_commands_docs.py::test_workbench_example_enables_commands]
- ac5: every example config still validates [evidence: command:uv run pytest tests/test_examples.py tests/test_config.py]
- ac6: targeted suites and lint pass [evidence: command:uv run pytest tests/test_slash_commands_docs.py tests/test_readme_api.py tests/test_readme_config.py tests/test_examples.py tests/test_config.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `README.md`
- `config.example.yaml`
- `src/claude_code_wrapper/data/config.example.yaml`
- `src/claude_code_wrapper/data/examples/workbench.config.yaml`
- `tests/test_slash_commands_docs.py`

#### Interfaces

None beyond the documented config keys (`sessions.commands.deny`, `dialog_grace_seconds`, `dialog_patterns`, agent/client names or `"*"`).

#### Expected outcome

An operator reading the README or the example configs learns that any command except the deny list runs, how each class completes and the worst-case hold.

#### Steps

- Red: update the docs tests (ac1, ac3, ac4); run `uv run pytest tests/test_slash_commands_docs.py`: they fail.
- Green: README and the example configs; run the task's verify: passes. Quote the summary line.

#### Notes

- Doc and config edit with test pins; the docs tests are written first.
- `config.example.yaml` at the repo root and `src/claude_code_wrapper/data/config.example.yaml`: check whether one is a copy of the other (`test_config_example_documents_command_keys` reads the root one) and keep both consistent.
- Depends on wrapper-commands-after-stop (every behaviour the docs describe has landed).

- 2026-10-29 done

### S24: mxc command outcome

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `src/agents_matrix_connector/tracker.py`, `README.md`, `MEMORY.md`, `tests/test_tracker.py`
- Verify: `uv run --frozen pytest tests/test_tracker.py tests/test_readme_api.py && mise run lint`
- Verified head: 534f886bf0331f5e05d16b4fc53f7401203948cb

#### Requirement

User decision F2 (2026-10-29), verbatim: "Check agents-matrix-connector (code/agents-matrix-connector): if it tracks message completion by turn (its own tracker or agents-common's), add the task that makes it handle command outcomes too (user said full scope)."

Check result (2026-10-29): it does. `src/agents_matrix_connector/tracker.py` `_outcome` polls the run's orchestrator message through agents-common's client and decides only by `message.turn` and `message.status`, so a Messenger message "/compact" (stored by the orchestrator as a command message, which stays `sent` with no turn) ends `timeout` with the "Sorry, the agent could not answer that message." notice. Architect brief, verbatim: "Noted, not doing now: agents-matrix-connector has the same gap in its own tracker, and a Messenger contact can now send `/compact`." The user's decision above puts the tracker gap in scope.

Architect's mapping (design D20), verbatim:

| Command outcome | Run result |
|---|---|
| completed: ok, dismissed, skipped_cache | handled |
| failed (e.g. unknown_command, dialog_stuck, timeout) | failed, reason `command_<error>` |
| cancelled | failed, reason `command_cancelled` |
| completed with result `turn` | decided by the existing turn checks |

Design D20, verbatim: "agents-matrix-connector has its own tracker that decides by the turn (`tracker.py:_outcome`), so a Messenger "/compact" times out today: it applies the same mapping, a failed or cancelled command posts the usual notice, and a completed command finishes `handled` with reason `command` and posts nothing (my call, Open questions Q4)."

Needs the agents-common v0.4.0 tag on origin (common-release-0-4-0 ac3, pushed by the orchestrator session after mx-34's confirmation).

Scope (agents-matrix-connector, branch from origin `main`): `pyproject.toml` (agents-common v0.3.0 to v0.4.0, both the dependency and the testing extra), `uv.lock`, `src/agents_matrix_connector/tracker.py` (`_outcome` applies the mapping before the timeout check; a failed outcome with no error reads `command_failed`), `tests/test_tracker.py`, README.md (the reasons list gains `command`, `command_<error>` and `command_cancelled`), MEMORY.md (the ruling and why).

#### Acceptance conditions

- ac1: the connector pins agents-common v0.4.0 in both pinning lines and uv.lock, and Message carries command [evidence: command:test "$(grep -c 'agents-common@v0.4.0' pyproject.toml)" = 2 && ! grep -q 'agents-common@v0.3.0' pyproject.toml && grep -q 'agents-common?rev=v0.4.0#' uv.lock && ! grep -q 'rev=v0.3.0' uv.lock && uv run --frozen python -c "from agents_common.orchestrator import Message; assert 'command' in Message.model_fields"]
- ac2: (Docker) a run whose message completed as a command with result ok, dismissed or skipped_cache finishes handled with reason command, settles its inbound rows and stores no outbound row (new) [evidence: test:tests/test_tracker.py::test_command_completed_handled_without_reply]
- ac3: (Docker) a failed command (unknown_command) finishes failed with reason command_unknown_command and posts the notice; a cancelled one finishes failed with reason command_cancelled and posts the notice (new) [evidence: test:tests/test_tracker.py::test_command_failed_or_cancelled_posts_notice]
- ac4: (Docker) a command completed with result turn is decided by the turn: still running keeps the run open, a completed turn posts its final text (new) [evidence: test:tests/test_tracker.py::test_promoted_command_relays_turn]
- ac5: (Docker) the turn and timeout outcomes are unchanged [evidence: test:tests/test_tracker.py::test_failure_and_timeout_notice]
- ac6: README's reasons list and MEMORY.md name the command outcomes [evidence: command:grep -q "command_cancelled" README.md && grep -q "command_cancelled" MEMORY.md]
- ac7: the named tests and lint pass [evidence: command:uv run --frozen pytest tests/test_tracker.py tests/test_readme_api.py && mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `src/agents_matrix_connector/tracker.py`
- `README.md`
- `MEMORY.md`
- `tests/test_tracker.py`

#### Interfaces

- `tracker.py`: constants `COMMAND = "command"`, `COMMAND_CANCELLED = "command_cancelled"`; `_outcome` checks `message.command` (agents-common v0.4.0 `Message.command`) after the turn checks and before the timeout: completed (result not `turn`) -> `_Outcome("handled", COMMAND)` with no chunks; failed -> `_failed(f"command_{error}")` (`command_failed` with no error); cancelled -> `_failed(COMMAND_CANCELLED)`; completed with result `turn` -> the existing turn checks.
- Uses `FakeOrchestrator.complete_command` and `fail_command` in `tests/test_tracker.py`.

#### Expected outcome

A Messenger message "/compact" finishes `handled` silently when the command completes, and with the usual notice when it fails or is cancelled, instead of timing out after `MATRIX_RUN_TIMEOUT_SECONDS`.

#### Steps

- Confirm the v0.4.0 tag on origin.
- Red: write the three new tests in `tests/test_tracker.py` against the v0.3.0 pin; they fail.
- Green: move both pins, `uv lock`, change `_outcome`, README reasons list, MEMORY.md entry; run the task's verify (Docker for the database tests). Quote the summary line.

#### Notes

- `_outcome` today decides only by `message.turn` and `message.status` (`tracker.py:111-142`); the `sent` command message with no turn falls through to `_timed_out`.
- The silent completed outcome is the planner's recommendation pending design Open questions Q4; an answer that wants a confirmation message amends this task.
- The todo epic immediate-message-delivery-w (mxc-relay-once-per-turn) also edits `tracker.py`, `pyproject.toml` and `uv.lock` and planned the same pin; it rebases on this when claimed.
- A Messenger contact can send any non-denied slash command once this lands (architect note); the wrapper deny list (wrapper-deny-list-extend) bounds it.

- 2026-10-29 done: completed command posts nothing (task file behaviour; matches the recommendation in pending user question mx-34 #454)

### S25: schedule common pin 0.4.0

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `README.md`, `tests/test_tracker.py`
- Verify: `uv run --frozen pytest tests/test_tracker.py && mise run lint`
- Verified head: 25601bb3620d83fadd41772b883dd07af790755f

#### Requirement

User decision F2 (2026-10-29), verbatim: "F2: read-side command outcome on MessageView (orchestrator, migration 0012 partial index; [...]), agents-common run tracker handles kind=command outcomes per the architect's mapping, agents-common release v0.4.0 (tag pending mx-34 confirmation; write the task so the orchestrator session pushes the tag after confirmation), then pin bumps in agents-webhook and agents-schedule."

Architect brief, verbatim: "7. `common-release-0-4-0` (a minor release), then two pin tasks:
   - `webhook-common-pin-0-4-0`: `pyproject.toml` (2 lines), `uv.lock`, test `tests/test_worker.py::test_command_prompt_run_handled`.
   - `schedule-common-pin-0-4-0`: `pyproject.toml`, `uv.lock`, test `tests/test_tracker.py::test_command_prompt_run_handled`."

Design D20, verbatim: "agents-webhook and agents-schedule move their pins to v0.4.0 and pin a slash preset prompt run that ends handled."

Needs the agents-common v0.4.0 tag on origin (common-release-0-4-0 ac3, pushed by the orchestrator session after mx-34's confirmation).

Scope (agents-schedule, branch from origin `main`): `pyproject.toml` (agents-common v0.3.0 to v0.4.0 in every line that pins it: 1), `uv.lock`, `tests/test_tracker.py` (a run whose prompt is slash text is tracked by the command outcome), README.md (the run reasons table gains `command_<error>` and `command_cancelled`, both `failed`).

#### Acceptance conditions

- ac1: the service pins agents-common v0.4.0 in every pinning line and uv.lock, and Message carries command [evidence: command:test "$(grep -c 'agents-common@v0.4.0' pyproject.toml)" = 1 && ! grep -q 'agents-common@v0.3.0' pyproject.toml && grep -q 'agents-common?rev=v0.4.0#' uv.lock && ! grep -q 'rev=v0.3.0' uv.lock && uv run --frozen python -c "from agents_common.orchestrator import Message; assert 'command' in Message.model_fields"]
- ac2: (Docker) a run whose prompt is "/review-pr 12" ends handled when the fake orchestrator completes the command (fake.complete_command), with no timeout (new) [evidence: test:tests/test_tracker.py::test_command_prompt_run_handled]
- ac3: (Docker) a run whose command fails unknown_command ends failed with reason command_unknown_command, and a cancelled one with command_cancelled (new) [evidence: test:tests/test_tracker.py::test_command_prompt_run_failed_reason]
- ac4: README's reason table names command_cancelled and command_<error> [evidence: command:grep -q "command_cancelled" README.md && grep -q "command_<error>" README.md]
- ac5: the named tests and lint pass [evidence: command:uv run --frozen pytest tests/test_tracker.py && mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_tracker.py`

#### Interfaces

- `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.4.0` in every line of `pyproject.toml` that pins it; `uv.lock` resolved to the v0.4.0 tag.
- Uses `agents_common.fake_orchestrator.FakeOrchestrator.complete_command` and `fail_command` in `tests/test_tracker.py`.

#### Expected outcome

A agents-schedule run whose prompt is slash text finishes `handled` when its command completes and `failed` with `command_<error>` or `command_cancelled` when it does not, instead of `timeout`.

#### Steps

- Confirm the v0.4.0 tag on origin (`git ls-remote --tags https://github.com/szymonrychu/agents-common v0.4.0`).
- Red: write `test_command_prompt_run_handled` and `test_command_prompt_run_failed_reason` in `tests/test_tracker.py` against the v0.3.0 pin; they fail (no `complete_command`).
- Green: move the pin, `uv lock`, README reason rows; run the task's verify (Docker for the database tests). Quote the summary line.

#### Notes

- The run tracking itself is agents-common's `runs.track` (common-command-outcome); this task only pins it and proves it end to end in the service.
- Dependency bump: the TDD exception covers the pin values; the new tests are the behaviour guard.

- 2026-10-29 done

### S26: webhook common pin 0.4.0

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `README.md`, `tests/test_worker.py`
- Verify: `uv run --frozen pytest tests/test_worker.py && mise run lint`
- Verified head: 4b0185421bd6a0462ef754dd4c659fe6de7ada69

#### Requirement

User decision F2 (2026-10-29), verbatim: "F2: read-side command outcome on MessageView (orchestrator, migration 0012 partial index; [...]), agents-common run tracker handles kind=command outcomes per the architect's mapping, agents-common release v0.4.0 (tag pending mx-34 confirmation; write the task so the orchestrator session pushes the tag after confirmation), then pin bumps in agents-webhook and agents-schedule."

Architect brief, verbatim: "7. `common-release-0-4-0` (a minor release), then two pin tasks:
   - `webhook-common-pin-0-4-0`: `pyproject.toml` (2 lines), `uv.lock`, test `tests/test_worker.py::test_command_prompt_run_handled`.
   - `schedule-common-pin-0-4-0`: `pyproject.toml`, `uv.lock`, test `tests/test_tracker.py::test_command_prompt_run_handled`."

Design D20, verbatim: "agents-webhook and agents-schedule move their pins to v0.4.0 and pin a slash preset prompt run that ends handled."

Needs the agents-common v0.4.0 tag on origin (common-release-0-4-0 ac3, pushed by the orchestrator session after mx-34's confirmation).

Scope (agents-webhook, branch from origin `main`): `pyproject.toml` (agents-common v0.3.0 to v0.4.0 in every line that pins it: 2), `uv.lock`, `tests/test_worker.py` (a run whose prompt is slash text is tracked by the command outcome), README.md (the run reasons table gains `command_<error>` and `command_cancelled`, both `failed`).

#### Acceptance conditions

- ac1: the service pins agents-common v0.4.0 in every pinning line and uv.lock, and Message carries command [evidence: command:test "$(grep -c 'agents-common@v0.4.0' pyproject.toml)" = 2 && ! grep -q 'agents-common@v0.3.0' pyproject.toml && grep -q 'agents-common?rev=v0.4.0#' uv.lock && ! grep -q 'rev=v0.3.0' uv.lock && uv run --frozen python -c "from agents_common.orchestrator import Message; assert 'command' in Message.model_fields"]
- ac2: (Docker) a run whose prompt is "/review-pr 12" ends handled when the fake orchestrator completes the command (fake.complete_command), with no timeout (new) [evidence: test:tests/test_worker.py::test_command_prompt_run_handled]
- ac3: (Docker) a run whose command fails unknown_command ends failed with reason command_unknown_command, and a cancelled one with command_cancelled (new) [evidence: test:tests/test_worker.py::test_command_prompt_run_failed_reason]
- ac4: README's reason table names command_cancelled and command_<error> [evidence: command:grep -q "command_cancelled" README.md && grep -q "command_<error>" README.md]
- ac5: the named tests and lint pass [evidence: command:uv run --frozen pytest tests/test_worker.py && mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_worker.py`

#### Interfaces

- `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.4.0` in every line of `pyproject.toml` that pins it; `uv.lock` resolved to the v0.4.0 tag.
- Uses `agents_common.fake_orchestrator.FakeOrchestrator.complete_command` and `fail_command` in `tests/test_worker.py`.

#### Expected outcome

A agents-webhook run whose prompt is slash text finishes `handled` when its command completes and `failed` with `command_<error>` or `command_cancelled` when it does not, instead of `timeout`.

#### Steps

- Confirm the v0.4.0 tag on origin (`git ls-remote --tags https://github.com/szymonrychu/agents-common v0.4.0`).
- Red: write `test_command_prompt_run_handled` and `test_command_prompt_run_failed_reason` in `tests/test_worker.py` against the v0.3.0 pin; they fail (no `complete_command`).
- Green: move the pin, `uv lock`, README reason rows; run the task's verify (Docker for the database tests). Quote the summary line.

#### Notes

- The run tracking itself is agents-common's `runs.track` (common-command-outcome); this task only pins it and proves it end to end in the service.
- Dependency bump: the TDD exception covers the pin values; the new tests are the behaviour guard.

- 2026-10-29 done

### S27: wrapper release 0.4.0

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `src/claude_code_wrapper/__init__.py`, `tests/test_packaging.py`
- Verify: `uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 4d84a4d86a34ce6f4c5d98d626533124682a5a4a

#### Requirement

Design D14, verbatim: "claude-code-wrapper 0.4.0 (version bump, tag `v0.4.0` on the merge commit after the `main` build, run by the orchestrator session), then agents-orchestrator pins that merge commit (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images) and enables `client: ["*"]` in `e2e/agent-test.config.yaml` for the real contract leg and e2e. No agents-helmfile task (user decision 4). Precedent: in-progress epic leader-auto-handover tasks wrapper-release-0-3-0 and orch-wrapper-pin-0-3-0. Builder check settlements (my call): the wrapper PR merges mid-epic through the normal PR flow; the orchestrator session pushes tag `v0.4.0`, and wrapper-release-0-4-0's "tag exists on origin" condition is checked by the orchestrator after that push, not by the implementer or reviewer."

User decision, verbatim: "Release and pin flow like done epic leader-auto-handover (wrapper release, orchestrator pin) if the orchestrator needs a new wrapper API".

User decision (builder check), verbatim: "the wrapper PR merges mid-epic through the normal PR flow, the orchestrator session pushes tag v0.4.0, and wrapper-release-0-4-0's 'tag exists on origin' AC is checked by the orchestrator after the push (state that in the task)".

Scope:
- Version `0.4.0` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`; `uv lock`.
- `tests/test_packaging.py::test_version_matches_pyproject` keeps pyproject, `__version__` and the installed metadata in agreement.
- The wrapper PR of this epic (every wrapper task) merges to `main` mid-epic through the normal PR flow, before the orchestrator pin tasks start.
- Release steps, run by the orchestrator session (never a subagent) once that PR is merged to `main`: wait for `build.yaml` to push `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, push tag `v0.4.0` on the merge commit (`release.yaml` retags `:0.4.0` and `:latest`; irreversible, listed in design.md), then amend `orch-wrapper-pin-0-4-0` with the merge sha.
- ac3 ("tag exists on origin") is checked by the orchestrator session after it pushed the tag; the implementer and the reviewer check ac1, ac2 and ac4 only.

#### Acceptance conditions

- ac1: pyproject, __version__ and the installed metadata agree [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- ac2: the version is 0.4.0 in pyproject and the package [evidence: command:grep -q '^version = "0.4.0"' pyproject.toml && grep -q '__version__ = "0.4.0"' src/claude_code_wrapper/__init__.py]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.4.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.0)"]
- ac4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

#### Interfaces

- Package version `0.4.0`; image tags `:0.4.0` and `:latest` from `release.yaml`.

#### Expected outcome

The orchestrator and, after the gate's deploy decision, the live agents can run a wrapper that takes any slash command.

#### Steps

- Bump the version to 0.4.0 in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`, run `uv lock` (dependency-bump exception; the packaging test is the guard); run the task's verify: passes.
- After the merge (orchestrator session): wait for `build.yaml` green on the merge commit, `git tag v0.4.0 <merge sha> && git push origin v0.4.0`, watch `release.yaml` green, then amend orch-wrapper-pin-0-4-0 with the merge sha.

#### Notes

- README `### Release`: `release.yaml` fails when the `:<shortsha>` image is missing, so tag only after the main build is green.
- If another epic releases the wrapper first, this task and orch-wrapper-pin-0-4-0 are amended to the next minor (design Assumptions).
- Depends on every wrapper task of this epic.

- 2026-10-27 amended: builder check settlement: the wrapper PR merges mid-epic through the normal PR flow, the orchestrator session pushes v0.4.0 and checks ac3 after the push, design D14 revised

- 2026-10-29 done

### S28: orch wrapper pin 0.4.0

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `e2e/agent-test.config.yaml`, `README.md`
- Verify: `uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint`
- Verified head: a406c59987888f499eb98c4f11538673fc24baff

#### Requirement

Design D14, verbatim: "claude-code-wrapper 0.4.0 (version bump, tag `v0.4.0` on the merge commit after the `main` build, run by the orchestrator session), then agents-orchestrator pins that merge commit (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images) and enables `client: ["*"]` in `e2e/agent-test.config.yaml` for the real contract leg and e2e. No agents-helmfile task (user decision 4). [...] Kind e2e placement (my call, interrogate item 12): the e2e job runs on every PR and agents get `client: ["*"]` only from the render change (D11), so an e2e case in the pin PR would be red with 403. The case is its own task orch-e2e-slash-command, right after orch-render-client-commands (a separate task keeps orch-render-client-commands at 8 files); orch-wrapper-pin-0-4-0 no longer touches `tests/e2e/test_e2e_kind.py`."

Interrogate item 12 (interrogate.md), verbatim: "Kind e2e case placed before the render change (A). The e2e job runs on every PR and agents get `client: ["*"]` only in orch-render-client-commands, so the pin PR would be red with 403. Move the e2e case and its AC to orch-render-client-commands."

Needs a merged upstream: the claude-code-wrapper PR of this epic merged on `main` and tagged `v0.4.0` (task wrapper-release-0-4-0). The orchestrator amends this task with the merge sha.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<merge sha>`; `uv lock`.
- `e2e/agent-test.Dockerfile`: `BASE_IMAGE` tag `<sha7>` and `WRAPPER_SHA` `<merge sha>`.
- `e2e/agent-test.config.yaml`: `sessions.commands.client: ["*"]` (the real contract leg).
- README `## Images`: recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- This task does not touch `tests/e2e/test_e2e_kind.py` (the kind e2e slash case is task orch-e2e-slash-command).

Merged upstream (2026-10-29): claude-code-wrapper PR #10 merged to `main` as `e94628868d28416e9e33b9f5dcb0f8c829cf2fd8` (sha7 `e946288`), tagged `v0.4.0`; `build.yaml` pushed `harbor.szymonrichert.pl/containers/claude-code-wrapper:e946288` and `release.yaml` retagged `:0.4.0` and `:latest`, both green. `<merge sha>` above reads `e94628868d28416e9e33b9f5dcb0f8c829cf2fd8` and `<sha7>` reads `e946288`. The epic branch is already rebased onto orchestrator `main` (HEAD 402d1ae).

#### Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper accepts "*" and its deny list holds the interrogate item 5 additions [evidence: command:uv run --frozen python -c "from claude_code_wrapper.config import CommandsConfig, DEFAULT_COMMAND_DENY; CommandsConfig(client=['*']); assert {'exit', 'reset', 'cd'} <= set(DEFAULT_COMMAND_DENY)"]
- ac4: (Docker host) the real contract leg passes, test_commands_any_name_and_denied included [evidence: command:mise run test:integration]
- ac5: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `e2e/agent-test.config.yaml`
- `README.md`

#### Interfaces

- The wrapper pin (pyproject dev dependency, `uv.lock`, `e2e/agent-test.Dockerfile` `BASE_IMAGE` and `WRAPPER_SHA`, README `## Images`), all one sha: the claude-code-wrapper `main` merge commit tagged v0.4.0.

#### Expected outcome

CI's contract leg and kind e2e run the wrapper that takes any slash command; the e2e slash case itself lands in orch-e2e-slash-command.

#### Steps

- Confirm the merged upstream and read the merge sha (`git -C /workdir/workdir/code/claude-code-wrapper fetch origin main` and the `v0.4.0` tag).
- Change the pyproject pin, run `uv lock`; run `uv run --frozen pytest tests/test_images.py`: the Dockerfile and README checks fail on the old sha.
- Update the Dockerfile args, the agent-test config and README `## Images`; run the task's verify: passes. Quote the summary line. The integration leg runs in CI or on a Docker host.

#### Notes

- `tests/test_images.py` ties pyproject, uv.lock, README Images and the Dockerfile to one sha; `tests/test_render.py` validates rendered configs against the pinned wrapper's config model.
- Dependency bump: the TDD exception for the pin values applies; the equality tests are the guard.
- Depends on wrapper-release-0-4-0, orch-wrapper-command-client and orch-dispatch-commands.

- 2026-10-27 amended: interrogate item 12 (the kind e2e case moved out of the pin task to orch-e2e-slash-command after orch-render-client-commands, so the pin PR is not red with 403), design D14 revised

- 2026-10-29 amended: wrapper v0.4.0 merged and tagged: merge sha e946288

- 2026-10-29 done: ac4 (real-wrapper integration leg) verified in CI run 40886319362 on a406c59 (rebased 325d842): e2e and test green

### S29: wrapper slash js whitespace

- Status: done
- Files: `src/claude_code_wrapper/session.py`, `README.md`, `MEMORY.md`, `tests/test_session_turns.py`, `tests/test_api_turns.py`
- Verify: `uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 7b3953a26182e7d7c228a739d9d65da9c0efa866

#### Requirement

User decision F1 (2026-10-29), verbatim: "F1 (security): both slash parsers adopt claude's JS whitespace set and skip invisible Cc/Cf characters as the architect specifies, including the ESC hole and the Session.probe guard; wrapper release v0.4.1 (tag approved by the user and mx-34 #432; the orchestrator session pushes it after merge) and an orchestrator pin to it; amend D2."

Architect brief (`/workdir/workdir/.scratchpad/slash-fix-design.md`), verbatim:

"F1: claude 2.1.304 (binary `/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe`) parses slash text like this:
- `Kb`: `t.trim()`, then checks the text starts with `/`.
- `hIe`: the name ends at the first `search(/\s/)` and the args are `.trim()`'d.
- Command lookup is an exact, case-sensitive match on name or alias.

Our two parsers split only at space, tab and newline, so claude runs `/exit` and `/login` texts that we class as prose. A second hole: `pty_proc.paste_bytes` deletes ESC before typing, so `"/ex\x1bit"` and `"\x1b/exit"` also reach claude as `/exit`. A third: `Session.probe` pastes client text with no guard at all, so a probe text of `/exit` runs."

"**F1: exact character rules (identical code in both repos)**
- **Whitespace (W):** exactly JS `\s`, which is the same set as JS `trim`. Checked under node v24: U+0009-000D, 0020, 00A0, 1680, 2000-200A, 2028, 2029, 202F, 205F, 3000, FEFF. Python's `isspace` differs: it adds U+001C-001F and U+0085, and it lacks U+FEFF.
- **Ignorable (D):** every other character in Unicode categories Cc or Cf. This includes ESC, NUL, DEL, C1, U+001C-001F, U+0085, zero-width and bidi characters. In the leading run and inside the name these are deleted before classifying.
- **Parse steps:**
  1. Remove the run marker.
  2. Skip leading W and D characters.
  3. Require `/`.
  4. The name runs to the first W character, with D characters dropped from it.
  5. The args are the rest, stripped of W only.
  6. The existing name regex applies unchanged.
- **Python's extra stripping must change:** stop using `lstrip()`, `strip()` and `\s` everywhere in the parser. U+001C-001F are still skipped when leading, but they no longer split the name.
- This leans toward calling more text a command, which design D2 already treats as the safe direction. The orchestrator then sends the cleaned name.
- Normalising in the orchestrator alone is not enough: direct wrapper clients, the initial prompt and the probe all bypass it."

"1. `wrapper-slash-js-whitespace` (claude-code-wrapper)
   - Files: `session.py` (`slash_command`, plus the same guard in `probe`), `tests/test_session_turns.py`, `tests/test_api_turns.py`.
   - Tests: extend `test_slash_rule_matches_claude_parser` and `test_slash_rule_leaves_paths_and_prose`. Add `test_slash_whitespace_set_is_js_whitespace`, `test_no_whitespace_or_invisible_char_hides_a_slash_command` (loops over every Zs/Zl/Zp/Cc/Cf code point as a leading character and as the separator), and `test_probe_refuses_slash_text` (422 `slash_command`)."

The case table, verbatim from the architect's orchestrator task (both repos share it): "New cases: `"/exit x"`, `"/clear\x0bx"`, `"/login\rx"`, `"﻿/login"`, `"/exit　"`, `"\x1b/exit"`, `"/ex\x1bit"`, `"/ex​it"`, `"\x1c/exit"`, `"/exit\x1cx"` giving `("exitx","")`. Prose stays prose: `"x /exit"`, `"/etc/hosts x"`."

Design D2 (amended 2026-10-29) names the JS whitespace set and the ignorable characters; design D3 keeps every origin refused.

Scope (claude-code-wrapper, branch from origin `main` e946288, which carries v0.4.0): `src/claude_code_wrapper/session.py` (`slash_command` per the parse steps; `Session.probe` raises `TurnRejected("slash_command")` for slash text before anything is pasted, so `POST /v1/sessions/{id}/probe` answers 422 `slash_command` and counts the probe `rejected`), `tests/test_session_turns.py`, `tests/test_api_turns.py`, README.md (the slash rule at "Slash commands" names the JS whitespace set and the skipped invisible characters; the probe endpoint documents 422 `slash_command`), MEMORY.md (the rule and why). `router.py` and `manager.py` already call `slash_command` and need no change.

#### Acceptance conditions

- ac1: slash_command keeps the existing table and adds the shared cases: "/exit x" -> ("exit", "x"), "/clear\x0bx" -> ("clear", "x"), "/login\rx" -> ("login", "x"), "﻿/login" -> ("login", ""), "/exit　" -> ("exit", ""), "\x1b/exit" -> ("exit", ""), "/ex\x1bit" -> ("exit", ""), "/ex​it" -> ("exit", ""), "\x1c/exit" -> ("exit", ""), "/exit\x1cx" -> ("exitx", ""); Session.submit refuses each with slash_command and writes nothing (updated) [evidence: test:tests/test_session_turns.py::test_slash_rule_matches_claude_parser]
- ac2: "x /exit" and "/etc/hosts x" join the prose cases: slash_command returns None and each is typed as a turn (updated) [evidence: test:tests/test_session_turns.py::test_slash_rule_leaves_paths_and_prose]
- ac3: exactly U+0009-000D, 0020, 00A0, 1680, 2000-200A, 2028, 2029, 202F, 205F, 3000 and FEFF end the name and are stripped from the args; U+001C-001F and U+0085 neither end the name nor are stripped from the args (new) [evidence: test:tests/test_session_turns.py::test_slash_whitespace_set_is_js_whitespace]
- ac4: for every code point of category Zs, Zl, Zp, Cc and Cf, "<c>/exit" and "/exit<c>x" are classified as a command (never None), with the name the parse steps give (new) [evidence: test:tests/test_session_turns.py::test_no_whitespace_or_invisible_char_hides_a_slash_command]
- ac5: POST /v1/sessions/{id}/probe with text "/exit", "\x1b/exit" or "/exit now" answers 422 slash_command and pastes nothing; a prose probe text is still accepted (new) [evidence: test:tests/test_api_turns.py::test_probe_refuses_slash_text]
- ac6: README names the JS whitespace set and the skipped Cc/Cf characters in the slash rule [evidence: command:grep -q "U+3000" README.md && grep -q "U+FEFF" README.md && grep -qE "\bCf\b" README.md]
- ac7: MEMORY.md records the rule under this epic's tag [evidence: command:grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\)" MEMORY.md | grep -q "JS"]
- ac8: the named tests and lint pass [evidence: command:uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/session.py`
- `README.md`
- `MEMORY.md`
- `tests/test_session_turns.py`
- `tests/test_api_turns.py`

#### Interfaces

- `claude_code_wrapper.session.slash_command(text: str) -> tuple[str, str] | None`: unchanged signature; `(name, args)` with the name cleaned of Cc/Cf characters and the args stripped of JS whitespace only.
- `Session.probe(text)`: raises `TurnRejected("slash_command")` when `slash_command(text)` is not None, before anything is pasted; `POST /v1/sessions/{id}/probe` maps it to 422 `slash_command` (the existing `_REJECT_STATUS` entry) and counts the probe `rejected`.
- One case table, identical to orch-slash-js-whitespace's `tests/test_slash.py`.

#### Expected outcome

No text that claude 2.1.304 would run as a slash command (JS whitespace separators, a leading BOM, an ESC or zero-width character inside or before the name) can reach the PTY as a turn, an initial prompt or a probe.

#### Steps

- Branch from origin `main` (e946288, v0.4.0) in the wrapper tree.
- Red: extend `SLASH_COMMANDS`/`SLASH_PROSE` and add the three new tests in `tests/test_session_turns.py` and `test_probe_refuses_slash_text` in `tests/test_api_turns.py`; run `uv run pytest tests/test_session_turns.py tests/test_api_turns.py`: the new cases fail (for example "/exit x" returns None).
- Green: rewrite `slash_command` per the parse steps with an explicit whitespace set (a frozenset of the JS code points) and `unicodedata.category(c) in ("Cc", "Cf")` for ignorable characters; guard `probe`; update README and MEMORY.md; run the task's verify. Quote the summary line.

#### Notes

- Parse steps, in order: remove the run marker; skip leading W and D; require `/`; name to the first W with D dropped; args = rest stripped of W only; `COMMAND_NAME.fullmatch` unchanged.
- Do not use `str.isspace`, `str.strip()`, `str.lstrip()` or regex `\s` in the parser: Python's set differs from JS (`U+001C-001F`, `U+0085` added, `U+FEFF` missing). The `_RUN_MARKER` regex is part of the parser: spell its whitespace explicitly.
- `pty_proc.paste_bytes` keeps deleting ESC (the todo epic immediate-message-delivery-w owns `pty_proc.py` in wrapper-paste-hygiene); the parser closes the hole by dropping ESC from the name.
- `router.py` (`submit_turn`) and `manager.py` (`_initial_turn`) call `slash_command` already; no change there.
- Do not run `tests/test_manager.py` (`test_shutdown_stops_all` fails locally, a known pre-existing failure).
- Claude's parser evidence: `.scratchpad/slash-fix-design.md` sources (binary offsets 254536412, 267231000, 243756307).

- 2026-10-29 done

### S30: orch plugins pin 0.2.0

- Status: done
- Files: `src/agents_orchestrator/settings.py`, `pyproject.toml`, `uv.lock`, `README.md`, `tests/test_settings.py`
- Verify: `uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint`
- Verified head: b5997f7eda04bbf8acf9a9bf59a3076b0a7cf1ce

#### Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."

Builder check settlement (user decision), verbatim: "add two tasks, any-mcp-tatara-plugins release v0.2.0 after plugin-session-send-slash, and an orchestrator plugins pin bump (ORCH_ANY_MCP_PLUGINS_REF, dev dependency, README, tests)".

Design D13, verbatim (the pin part): "then the orchestrator pins it (task orch-plugins-pin-0-2-0: the `ORCH_ANY_MCP_PLUGINS_REF` default, the `any-mcp-tatara-orchestrator` dev dependency, README, tests), so superleaders actually see the description. The helmfile value of `ORCH_ANY_MCP_PLUGINS_REF` stays with the gate's deploy decision."

Amendment (2026-10-29, user-approved release order agreed between hives 2026-10-28): the epic matrix-connector-agent-initi ran first, released any-mcp-tatara-plugins `v0.2.0` (commit 4506e70) and already pinned agents-orchestrator `main` to it (settings default, dev dependency, uv.lock, README, `tests/test_settings.py::test_defaults`, merge a9f936f). This epic releases `v0.3.0` (task plugins-release-0-2-0), so this pin moves `v0.2.0` -> `v0.3.0`: the release named `v0.2.0` in the quotes above now reads `v0.3.0` (design D13 amended the same way). The task slug stays orch-plugins-pin-0-2-0. Where the Interfaces, Steps and Notes sections below still name v0.2.0 (written before this amendment), they read v0.3.0.

Needs a merged upstream (see Amendment 2): any-mcp-tatara-plugins tag `v0.5.0` on origin (task plugins-release-0-2-0).


Amendment 2 (2026-10-29, user-approved, mx-34 #406): tatara's epic hive-decoupling released any-mcp-tatara-plugins `v0.4.0` (merge 6d5cc19, plugin version 0.4.0) and pinned agents-orchestrator `main` to it (df2b80e) before this epic's `v0.3.0` was tagged; `v0.3.0` stays unused. This epic ships as plugins `v0.5.0` on top of `v0.4.0`. Where Amendment 1 and the sections below read `v0.3.0`/`0.3.0` they now read `v0.5.0`/`0.5.0`, and where they read `v0.2.0`/`0.2.0` as the current release on `main` they now read `v0.4.0`/`0.4.0`. The Scope below is restated with these numbers. Tagging `v0.5.0` is approved (standing release-tag rule mx-34 #396 satisfied by #406).

Scope (agents-orchestrator), on the epic branch rebased onto orchestrator `main` (which carries the v0.4.0 pin):
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `v0.4.0` -> `v0.5.0`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.5.0#subdirectory=orchestration/orchestrator` (was `@v0.4.0`); `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `v0.5.0` and the `## Images` any-mcp paragraph (`v0.4.0` -> `v0.5.0` for the plugins release tag only; the any-mcp `v0.5.0` pin is unchanged).
- `tests/test_settings.py::test_defaults` is no longer accurate (named): on `main` it pins `any_mcp_plugins_ref == "v0.4.0"`; it asserts `v0.5.0`.
- No agents-helmfile change (the gate's deploy decision).
- Needs any-mcp-tatara-plugins tag `v0.5.0` on origin (task plugins-release-0-2-0).

#### Acceptance conditions

- ac1: the settings default is v0.5.0 (updated) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.5.0 default and no longer names v0.4.0 or v0.1.0 for the plugins [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.5.0` |' README.md && ! grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.4.0` |' README.md && ! grep -qF 'pin the same plugins release tag (`v0.4.0`)' README.md && ! grep -q "plugins release tag (\`v0.1.0\`)" README.md]
- ac4: the pinned orchestrator plugin carries the new session_send description [evidence: command:grep -rq "Claude Code slash command" "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
- ac5: settings, images and on-start suites and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint]

#### Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_settings.py`

#### Interfaces

- `Settings.any_mcp_plugins_ref` default `v0.2.0` (`ORCH_ANY_MCP_PLUGINS_REF`); dev dependency `any-mcp-tatara-orchestrator` at `v0.2.0`.

#### Expected outcome

Agent pods rendered by this orchestrator install the plugins release whose session_send description says slash text from a superleader runs as a command.

#### Steps

- Confirm tag `v0.2.0` on any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins v0.2.0`).
- Red: change `test_defaults` to v0.2.0; run `uv run --frozen pytest tests/test_settings.py tests/test_images.py`: fails.
- Green: settings default, pyproject pin, `uv lock`, README; run the task's verify: passes. Quote the summary line.

#### Notes

- `tests/test_images.py::test_plugins_dev_pin_matches_settings_ref` ties the dev dependency, uv.lock and the settings default to one tag.
- Changing the default changes the rendered config hash and rolls agent pods on deploy (README `## Images`); deploy is the gate's decision.
- Sequenced after orch-wrapper-pin-0-4-0 so one task at a time edits `pyproject.toml` and `uv.lock` (my call).
- Depends on plugins-release-0-2-0 and orch-wrapper-pin-0-4-0.

- 2026-10-29 amended: release order changed (user-approved, agreed between hives 2026-10-28): orchestrator main already pins plugins v0.2.0 (matrix-connector-agent-initi), so this pin moves v0.2.0 -> v0.3.0; slug stays orch-plugins-pin-0-2-0

- 2026-10-29 amended: plugins renumbered: hive-decoupling took v0.4.0 first; slash ships v0.5.0 (user-approved mx-34 #406)

- 2026-10-29 done

### S31: orch render client commands

- Status: done
- Files: `src/agents_orchestrator/k8s/render.py`, `src/agents_orchestrator/spec.py`, `README.md`, `openapi.json`, `tests/test_render.py`, `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`, `tests/test_spec_config.py`
- Verify: `uv run --frozen pytest tests/test_render.py tests/test_spec_config.py tests/test_readme_api.py tests/test_api_config.py && mise run lint`
- Verified head: b51399a1f45e3ded1607929c9834e3a3dd0ead1f

#### Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D11, verbatim: "`k8s/render.py` always renders `sessions.commands.client = ["*"]` (the orchestrator is the wrapper's only client; this also repairs the compact button, refused 403 today because the client allowlist was never rendered) and `sessions.commands.agent = spec.wrapper.agent_commands` when set. `spec.wrapper.agent_commands` becomes `list[str]` of names (D2 pattern) or `"*"`, validated by the wrapper's config model through the existing render validation. Needs the 0.4.0 wrapper pin (the 0.3.0 config model rejects `"*"`)."

D2 name pattern (design D2, interrogate item 2, verbatim): "unknown-command regex `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap".

Discovery fix-as-ac (agents-orchestrator.md), verbatim: "orchestrator never renders wrapper `sessions.commands.client`, so client-origin commands (existing `/agents/{id}/compact`) are refused by the real wrapper (k8s/render.py:133-134; ccw:commands.py:170-176)".

Scope (agents-orchestrator): `k8s/render.py`, `spec.py` (`agent_commands: list[str] | None`, each a D2-pattern name or `"*"`), `README.md` (the `agent_commands` row: names or `*`; the rendered client allowlist), `openapi.json` regenerated (the spec schema changes). The kind e2e case is task orch-e2e-slash-command, which builds on this task (interrogate item 12, design D14).

Tests no longer accurate (named): `tests/golden/session_single.yaml` and `tests/golden/session_two_peers.yaml` pin the rendered wrapper config, which now carries `sessions.commands.client: ["*"]`; they are regenerated. `tests/test_spec_config.py::test_wrapper_value_rules_refused` case `{"agent_commands": ["compact", "rm"]}` asserts `rm` is refused; `rm` is now a valid name, so the case becomes `["compact", "rm -rf"]` (outside the pattern), with `notes.txt` as a second refused case.

#### Acceptance conditions

- ac1: every rendered session config has sessions.commands.client ["*"], and agent equal to spec agent_commands when set (new) [evidence: test:tests/test_render.py::test_commands_client_wildcard_rendered]
- ac2: the goldens carry the client allowlist (updated) [evidence: test:tests/test_render.py::test_golden_single_without_peers]
- ac3: the two-peer golden carries it too (updated) [evidence: test:tests/test_render.py::test_golden_two_replicas_with_peers]
- ac4: the rendered config, with agent_commands ["*"] or a free name such as "_x", validates against the pinned wrapper (updated) [evidence: test:tests/test_render.py::test_rendered_ccw_config_validates]
- ac5: agent_commands accepts free names and "*" and refuses "rm -rf" and "notes.txt" (outside the D2 pattern) at wrapper.agent_commands (updated) [evidence: test:tests/test_spec_config.py::test_wrapper_value_rules_refused]
- ac6: openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac7: targeted suites and lint pass [evidence: command:uv run --frozen pytest tests/test_render.py tests/test_spec_config.py tests/test_readme_api.py tests/test_api_config.py && mise run lint]

#### Files

- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/spec.py`
- `README.md`
- `openapi.json`
- `tests/test_render.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `tests/test_spec_config.py`

#### Interfaces

- Rendered wrapper config: `sessions.commands = {"client": ["*"]}` plus `"agent": [...]` when the spec sets `agent_commands`.
- `SessionSpec.wrapper.agent_commands: list[str] | None`.

#### Expected outcome

Every agent pod's wrapper accepts client commands from the orchestrator, so chat and superleader commands (and the existing compact button) are no longer refused 403.

#### Steps

- Red: add ac1, update the spec case and ac4; run `uv run --frozen pytest tests/test_render.py tests/test_spec_config.py`: they fail.
- Green: render, spec, regenerate the goldens and openapi.json, README; run the task's verify: passes. Quote the summary line.

#### Notes

- Changing the rendered config changes the config hash and rolls agent pods on deploy (README `## Images` note); deploy is decided at the gate.
- `tests/test_api_config.py` uses `agent_commands: ["compact", "context"]` and must stay green.
- Depends on orch-wrapper-pin-0-4-0 (the pinned wrapper must accept `"*"`).

- 2026-10-27 amended: interrogate item 2 (agent_commands names follow claude's name regex) and item 12 (the kind e2e case builds on this task, as task orch-e2e-slash-command)

- 2026-10-29 done

### S32: wrapper deny list extend

- Status: done
- Files: `src/claude_code_wrapper/config.py`, `src/claude_code_wrapper/commands.py`, `README.md`, `config.example.yaml`, `tests/test_command_registry.py`
- Verify: `uv run pytest tests/test_command_registry.py tests/test_slash_commands_docs.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: ea7535f3cee9c180db34f16deb114e306007230c

#### Requirement

User decision (2026-10-29 15:26Z/15:29Z), verbatim: "User verbatim 2026-10-29 15:26Z/15:29Z: "Yes" / "all yes" to: (1) extend the wrapper's DEFAULT_COMMAND_DENY with heapdump, plugin, plugins, marketplace, install, import, daemon, schedule, routines, add-dir, export, install-github-app, install-slack-app, design-consent, design-revoke, desktop, remote-env, feedback, bug, extra-usage, usage-credits, terminal-setup, ide, memory (verify each name/alias against claude 2.1.304 at /usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe; a name that does not exist is reported, not invented); (2) a wrapper session-create override may only extend the deny list, never replace or empty it; (3) keep client ["*"] with the extended deny list. The orchestrator's fake wrapper COMMAND_DENY mirror and docs/examples follow."

Design D5 (amended 2026-10-29), verbatim: "(1) `DEFAULT_COMMAND_DENY` gains heapdump, plugin, plugins, marketplace, install, import, daemon, schedule, routines, add-dir, export, install-github-app, install-slack-app, design-consent, design-revoke, desktop, remote-env, feedback, bug, extra-usage, usage-credits, terminal-setup, ide, memory. Each name was checked against the claude 2.1.304 binary during planning: all 24 exist (plugins and marketplace are aliases of plugin, routines an alias of schedule; bug is its own command); desktop's alias `app` is not in the list (Open questions Q3). (2) A `POST /v1/sessions` `commands.deny` override only extends the deny list (the effective list is the configured list plus the override's names), never replaces or empties it; `sessions.commands.deny` in the server config keeps its D5 meaning (it sets the list). (3) Clients keep `["*"]` (D11) with the extended list. The orchestrator's fake wrapper `COMMAND_DENY` mirror and the wrapper docs and example configs follow."

Scope (claude-code-wrapper, on the same wrapper branch as wrapper-slash-js-whitespace):
- `src/claude_code_wrapper/config.py`: the 24 names appended to `DEFAULT_COMMAND_DENY` (26 + 24 = 50 names), the comment naming why (claude's own descriptions from the binary).
- `src/claude_code_wrapper/commands.py`: `effective_commands` merges an override's `deny` into the base list (base order kept, then the override's new names, compared case-insensitively); an override `deny: []` or unset leaves the base list. The stored override is reapplied on resume through the same function.
- README.md: the `POST /v1/sessions` `commands` row ("a set `deny` replaces the default list"), the "Slash commands" prose ("a `deny` there replaces the default list") and the `sessions.commands.deny` configuration reference row (default list, "a set value (config or create override) replaces the default list") say the override only extends; the default list is the 50 names.
- `config.example.yaml`: the commented `deny:` line lists the 50 names and says a create override only extends it.
- `tests/test_command_registry.py`. Test no longer accurate (named): `test_deny_list_default_and_override` pins `len(DENY) == 26` and an override `deny: ["exit"]` that replaces the default (`out.deny == ["exit"]`, `/clear` no longer denied); user decision (2) forbids exactly that, so the test is updated to the extend-only rule and the 50-name default.

#### Acceptance conditions

- ac1: DEFAULT_COMMAND_DENY holds the 26 earlier names plus heapdump, plugin, plugins, marketplace, install, import, daemon, schedule, routines, add-dir, export, install-github-app, install-slack-app, design-consent, design-revoke, desktop, remote-env, feedback, bug, extra-usage, usage-credits, terminal-setup, ide, memory (50); an override deny ["exit"] or [] leaves every default name denied, an override ["foo"] adds foo, and CreateSessionRequest still validates the names (updated, named) [evidence: test:tests/test_command_registry.py::test_deny_list_default_and_override]
- ac2: with agent and client ["*"], each of the 24 added names is refused denied for both origins, in any letter case ("Plugin", "MARKETPLACE") (new) [evidence: test:tests/test_command_registry.py::test_deny_list_covers_user_extension]
- ac3: a CommandQueue built from effective_commands(CommandsConfig(client=["*"]), CommandsOverride(deny=[])) or CommandsOverride(deny=["exit"]) refuses "clear" and "plugin" as denied, and a session-create request {"commands": {"deny": []}} validates without emptying the effective list (new) [evidence: test:tests/test_command_registry.py::test_create_override_only_extends_deny]
- ac4: config.example.yaml's commented deny list equals DEFAULT_COMMAND_DENY [evidence: test:tests/test_slash_commands_docs.py::test_config_example_documents_command_keys]
- ac5: README no longer says an override replaces the deny list and names the extension rule [evidence: command:! grep -q "a set \`deny\` replaces the default list" README.md && ! grep -q "a \`deny\` there replaces the default" README.md && grep -q "usage-credits" README.md]
- ac6: the named tests and lint pass [evidence: command:uv run pytest tests/test_command_registry.py tests/test_slash_commands_docs.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/commands.py`
- `README.md`
- `config.example.yaml`
- `tests/test_command_registry.py`

#### Interfaces

- `claude_code_wrapper.config.DEFAULT_COMMAND_DENY: tuple[str, ...]`: 50 names (26 earlier plus the 24 of user decision 1, in that order).
- `claude_code_wrapper.commands.effective_commands(base, override) -> CommandsConfig`: `deny` = base deny plus the override's names not already in it (case-insensitive); every other field as before (override replaces when set).
- `POST /v1/sessions` `commands.deny`: extends only; `sessions.commands.deny` in the server config still sets the list.

#### Expected outcome

`/plugin install ...`, `/memory`, `/export`, `/feedback` and the rest of the 24 are refused 403 `command_denied` for agent and client origins under `["*"]`, and no per-session override can remove a default name.

#### Steps

- Red: update `test_deny_list_default_and_override` (named, no longer accurate: it pins replace semantics and 26 names), add `test_deny_list_covers_user_extension` and `test_create_override_only_extends_deny`; run `uv run pytest tests/test_command_registry.py`: they fail.
- Green: extend `DEFAULT_COMMAND_DENY`, change `effective_commands`, update README (the `commands` row of `POST /v1/sessions`, the Slash commands prose, the `sessions.commands.deny` reference row) and `config.example.yaml`; run the task's verify. Quote the summary line.

#### Notes

- Name check done at planning (claude 2.1.304 binary): all 24 exist; `plugins` and `marketplace` are aliases of `plugin`, `routines` of `schedule`; `bug` is its own command; `desktop` has the alias `app`, which is not in the user's list (design Open questions Q3; an answer of yes amends this task). If the implementer finds a name missing from the binary, it is reported, not invented.
- `test_config_example_documents_command_keys` compares `config.example.yaml`'s commented deny list with `DEFAULT_COMMAND_DENY`; keep the example line in the same order.
- Builds on wrapper-slash-js-whitespace (same wrapper branch, README touched by both).
- Do not run `tests/test_manager.py` (known local failure `test_shutdown_stops_all`).

- 2026-10-29 done: 51 names: alias app of desktop added, leader-approved under the user's Q1

### S33: orch e2e slash command

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`
- Verify: `uv run --frozen python -m py_compile tests/e2e/test_e2e_kind.py && mise run lint`
- Verified head: 226d95d1be941a52df61e441a8987324475e8aa5

#### Requirement

User decision, verbatim: "A regression test must pin the reported case: sending '/reload-plugins' from chat never leaves the session busy (wrapper and orchestrator level)." This kind e2e case proves it against the real agent image.

Interrogate item 12 (interrogate.md), verbatim: "Kind e2e case placed before the render change (A). The e2e job runs on every PR and agents get `client: ["*"]` only in orch-render-client-commands, so the pin PR would be red with 403. Move the e2e case and its AC to orch-render-client-commands."

Design D14, verbatim (the placement part): "Kind e2e placement (my call, interrogate item 12): the e2e job runs on every PR and agents get `client: ["*"]` only from the render change (D11), so an e2e case in the pin PR would be red with 403. The case is its own task orch-e2e-slash-command, right after orch-render-client-commands (a separate task keeps orch-render-client-commands at 8 files); orch-wrapper-pin-0-4-0 no longer touches `tests/e2e/test_e2e_kind.py`."

Scope (agents-orchestrator), moved verbatim from task orch-wrapper-pin-0-4-0: "`tests/e2e/test_e2e_kind.py`: new `test_slash_command_from_chat_keeps_session_responsive`: POST a chat message "/reload-plugins" through the API; the session's events show `command_completed` for reload-plugins; the agent returns idle; a following prose message completes its turn; POST "/exit" fails with error `command_denied`."

Retro proposal (cross-session-messaging-and), verbatim from design Research inputs: "kind e2e allow-list assertions should derive from the shared constant": the case asserts on the wrapper's error code `command_denied`, never on a hard-coded deny list.

Depends on orch-render-client-commands (agents render `client: ["*"]`) and, through it, orch-wrapper-pin-0-4-0 (the agent image runs wrapper 0.4.0).

#### Acceptance conditions

- ac1: (CI only, kind) test_slash_command_from_chat_keeps_session_responsive passes against the real agent image: "/reload-plugins" ends command_completed, the agent returns idle, a following prose message completes its turn, "/exit" fails command_denied (new) [evidence: command:mise run test:e2e]
- ac2: the case asserts on the wrapper error code command_denied and names no deny list [evidence: command:grep -q "def test_slash_command_from_chat_keeps_session_responsive" tests/e2e/test_e2e_kind.py && grep -q "command_denied" tests/e2e/test_e2e_kind.py && ! grep -q "DEFAULT_COMMAND_DENY" tests/e2e/test_e2e_kind.py]
- ac3: the module compiles and lint passes [evidence: command:uv run --frozen python -m py_compile tests/e2e/test_e2e_kind.py && mise run lint]

#### Files

- `tests/e2e/test_e2e_kind.py`

#### Interfaces

- New kind e2e case `tests/e2e/test_e2e_kind.py::test_slash_command_from_chat_keeps_session_responsive` (marker `e2e`, CI job e2e).

#### Expected outcome

CI's kind e2e proves the reported case end to end against the real agent image: a chat "/reload-plugins" completes as a command, the agent is free again, prose still runs, and "/exit" is refused with the wrapper's code.

#### Steps

- Write the case first against the existing fixtures (`api`, `session`); it cannot run here (kind, CI only).
- Run the task's verify: compiles and lint passes. Quote the output; the e2e leg runs in CI on the PR (green only with orch-render-client-commands and the 0.4.0 pin in place).

#### Notes

- Reuse the fixtures and helpers of `tests/e2e/test_e2e_kind.py` (for example the ones `test_agent_api_identity` and `test_hive_notes_delivered` use).
- Assert on the wrapper error code `command_denied`, never on a list of names (retro proposal).
- Depends on orch-render-client-commands.

- 2026-10-29 done: kind e2e PASSED in CI run 40887222737 (tests/e2e/test_e2e_kind.py::test_slash_command_from_chat_keeps_session_responsive)

### S34: web sync message kind

- Status: done
- Files: `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts`
- Verify: `npm run check:api && npx tsc -b && npm run lint`
- Verified head: e533228523871c9b393e48a177f892989b9b64f6

#### Requirement

Design D12, verbatim (the API part): "A command the orchestrator could not deliver shows in QueueStrip as failed with the wrapper code (D10)." Design D1, verbatim: "The stored text stays raw (agents-common adopts an existing message by `marker in m.text`, `runs.py:_post_once`); `MessageView` gains `kind`." Constraint, verbatim: "Orchestrator route/schema changes regenerate `openapi.json` [...]; agents-web vendors it with `npm run sync:api -- orchestrator`."

Interrogate item 13 (interrogate.md), verbatim: "AC evidence that already passes today (A): orch-dispatch-commands ac10 grep matches MEMORY.md:41; web-sync-message-kind ac3 grep matches the current source pin. Replace with assertions specific to the new state."

Scope (agents-web): run `npm run sync:api -- orchestrator` against the agents-orchestrator commit carrying orch-message-kind and orch-render-client-commands; commit `openapi/orchestrator.json`, `openapi/orchestrator.source` and the generated `src/api/schema.d.ts` (never hand-edited). No UI change: QueueStrip already shows a failed message's `error`.

#### Acceptance conditions

- ac1: the vendored spec and the generated types agree [evidence: command:npm run check:api]
- ac2: MessageView in the vendored spec and the generated types has kind and wrapper_command_id [evidence: command:grep -q "wrapper_command_id" openapi/orchestrator.json && grep -q "wrapper_command_id" src/api/schema.d.ts]
- ac3: the source pin names an agents-orchestrator commit whose openapi.json carries the message kind (the current pin does not) [evidence: command:git -C ../agents-orchestrator show "$(awk '{print $2}' openapi/orchestrator.source):openapi.json" | grep -q "wrapper_command_id"]
- ac4: the app type-checks and lint passes [evidence: command:npx tsc -b && npm run lint]

#### Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

#### Interfaces

- `components['schemas']['MessageView']` gains `kind: 'turn' | 'command'` and `wrapper_command_id: string | null`; `wrapper.agent_commands` becomes `string[]`.

#### Expected outcome

agents-web's vendored orchestrator API matches the orchestrator of this epic.

#### Steps

- Run `npm run sync:api -- orchestrator` (reads ../agents-orchestrator at the epic's integration commit); run the task's verify: passes.

#### Notes

- Generated files only: the TDD exception for a generated-code sync with no behaviour change applies; `npm run check:api` is the guard.
- `src/sessions/sessionSpecForm.ts` and `PresetForm.tsx` keep compiling with `agent_commands: string[]` (noted, not doing now: free-form agent command input in PresetForm).
- The sibling epic file-download-in-file-browse re-vendors the same files (task web-sync-orchestrator-api); whichever lands second re-runs the sync (design Assumptions).
- Depends on orch-message-kind and orch-render-client-commands.

- 2026-10-27 amended: interrogate item 13 (ac3 evidence replaced: the pinned orchestrator commit's openapi.json must carry wrapper_command_id)

- 2026-10-29 done

### S35: wrapper release 0.4.1

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `src/claude_code_wrapper/__init__.py`, `tests/test_packaging.py`
- Verify: `uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 85ba295731c56baf492b3629843333609aef03e7

#### Requirement

User decision F1 (2026-10-29), verbatim: "F1 (security): both slash parsers adopt claude's JS whitespace set and skip invisible Cc/Cf characters as the architect specifies, including the ESC hole and the Session.probe guard; wrapper release v0.4.1 (tag approved by the user and mx-34 #432; the orchestrator session pushes it after merge) and an orchestrator pin to it; amend D2."

Architect brief, verbatim: "wrapper v0.4.0 is already tagged on origin (e946288), so any wrapper fix needs a new release." and "3. `wrapper-release-0-4-1`: then `orch-wrapper-pin-0-4-1`, touching the same files as `orch-wrapper-pin-0-4-0`."

Design D14 (amended 2026-10-29), verbatim: "wrapper v0.4.0 is already tagged on origin (e946288), so the F1 parser fix and the D5 deny extension ship as wrapper 0.4.1 (task wrapper-release-0-4-1; tag approved by the user and mx-34 #432; the orchestrator session pushes it after merge)".

Scope (mirrors wrapper-release-0-4-0):
- Version `0.4.1` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`; `uv lock`.
- `tests/test_packaging.py::test_version_matches_pyproject` keeps pyproject, `__version__` and the installed metadata in agreement.
- The wrapper PR of this fix round (wrapper-slash-js-whitespace, wrapper-deny-list-extend, this task) merges to `main` through the normal PR flow before orch-wrapper-pin-0-4-1 starts.
- Release steps, run by the orchestrator session (never a subagent) once that PR is merged to `main`: wait for `build.yaml` to push `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, push tag `v0.4.1` on the merge commit (`release.yaml` retags `:0.4.1` and `:latest`; irreversible, listed in design.md, approved by the user and mx-34 #432), then amend `orch-wrapper-pin-0-4-1` with the merge sha.
- ac3 ("tag exists on origin") is checked by the orchestrator session after it pushed the tag; the implementer and the reviewer check ac1, ac2 and ac4 only.

#### Acceptance conditions

- ac1: pyproject, __version__ and the installed metadata agree [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- ac2: the version is 0.4.1 in pyproject and the package [evidence: command:grep -q '^version = "0.4.1"' pyproject.toml && grep -q '__version__ = "0.4.1"' src/claude_code_wrapper/__init__.py]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.4.1 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.1)"]
- ac4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

#### Interfaces

- Package version `0.4.1`; image tags `:0.4.1` and `:latest` from `release.yaml`.

#### Expected outcome

The orchestrator and, after the deploy decision, the live agents can run a wrapper with the claude-exact slash rule, the probe guard and the extended deny list.

#### Steps

- Bump the version to 0.4.1 in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`, run `uv lock` (dependency-bump exception; the packaging test is the guard); run the task's verify: passes. End "ready for tag".
- After the merge (orchestrator session): wait for `build.yaml` green on the merge commit, `git tag v0.4.1 <merge sha> && git push origin v0.4.1`, watch `release.yaml` green, then amend orch-wrapper-pin-0-4-1 with the merge sha.

#### Notes

- README `### Release`: `release.yaml` fails when the `:<shortsha>` image is missing, so tag only after the main build is green.
- The tag is approved by the user and mx-34 #432; tags are never re-pointed.
- Depends on every wrapper task of the fix round.

- 2026-10-29 done: merged PR #11 as eed2c3c (main build green), tag v0.4.1 pushed on it

### S36: orch wrapper pin 0.4.1

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `README.md`, `tests/fakes/fake_wrapper.py`, `tests/test_fake_wrapper_contract.py`
- Verify: `uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint`
- Verified head: 44416f0dff8b98df22bb7cd00cce2de3b1b723ea

#### Requirement

User decision F1 (2026-10-29), verbatim: "F1 (security): both slash parsers adopt claude's JS whitespace set and skip invisible Cc/Cf characters as the architect specifies, including the ESC hole and the Session.probe guard; wrapper release v0.4.1 (tag approved by the user and mx-34 #432; the orchestrator session pushes it after merge) and an orchestrator pin to it; amend D2."

User decision (2026-10-29 15:26Z/15:29Z), verbatim: "User verbatim 2026-10-29 15:26Z/15:29Z: "Yes" / "all yes" to: (1) extend the wrapper's DEFAULT_COMMAND_DENY with heapdump, plugin, plugins, marketplace, install, import, daemon, schedule, routines, add-dir, export, install-github-app, install-slack-app, design-consent, design-revoke, desktop, remote-env, feedback, bug, extra-usage, usage-credits, terminal-setup, ide, memory (verify each name/alias against claude 2.1.304 at /usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe; a name that does not exist is reported, not invented); (2) a wrapper session-create override may only extend the deny list, never replace or empty it; (3) keep client ["*"] with the extended deny list. The orchestrator's fake wrapper COMMAND_DENY mirror and docs/examples follow."

Architect brief, verbatim: "3. `wrapper-release-0-4-1`: then `orch-wrapper-pin-0-4-1`, touching the same files as `orch-wrapper-pin-0-4-0`."

Design D14 (amended 2026-10-29), verbatim: "then orch-wrapper-pin-0-4-1 moves the orchestrator pin (same files as orch-wrapper-pin-0-4-0, plus the fake wrapper's deny mirror and the contract test)."

Needs a merged upstream: the claude-code-wrapper fix-round PR merged on `main` and tagged `v0.4.1` (task wrapper-release-0-4-1). The orchestrator amends this task with the merge sha.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<merge sha>`; `uv lock`.
- `e2e/agent-test.Dockerfile`: `BASE_IMAGE` tag `<sha7>` and `WRAPPER_SHA` `<merge sha>`.
- README `## Images`: recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- `e2e/agent-test.config.yaml` keeps `sessions.commands.client: ["*"]` (user decision 3); unchanged.
- `tests/fakes/fake_wrapper.py`: `COMMAND_DENY` mirrors the pinned wrapper's 51-name `DEFAULT_COMMAND_DENY` (50 plus `app`, the alias of `desktop`, leader-approved under the user's Q1) (comment names the source).
- `tests/test_fake_wrapper_contract.py`: `test_commands_any_name_and_denied` (both legs) also refuses the added names; a Docker-free check pins the mirror to the pinned wrapper's constant.

Merged upstream (2026-10-29): claude-code-wrapper PR #11 merged to `main` as `eed2c3c582827e297eb6d838cb00500db9a27333` (sha7 `eed2c3c`), tagged `v0.4.1`; `build.yaml` green on it (image `harbor.szymonrichert.pl/containers/claude-code-wrapper:eed2c3c`). `<merge sha>` above reads `eed2c3c582827e297eb6d838cb00500db9a27333` and `<sha7>` reads `eed2c3c`.

#### Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper carries the F1 parser and the extended deny list [evidence: command:uv run --frozen python -c "from claude_code_wrapper.session import slash_command; from claude_code_wrapper.config import DEFAULT_COMMAND_DENY; assert slash_command('/exit x') == ('exit', 'x'); assert slash_command('/ex\x1bit') == ('exit', ''); assert {'plugin', 'marketplace', 'routines', 'memory', 'usage-credits'} <= set(DEFAULT_COMMAND_DENY)"]
- ac4: the fake wrapper's COMMAND_DENY equals the pinned wrapper's DEFAULT_COMMAND_DENY, lower-cased (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_deny_mirrors_wrapper_default]
- ac5: on the fake leg, and on the real leg on a Docker host, "plugin", "Marketplace", "routines", "memory" and "usage-credits" are refused 403 command_denied while "context" still queues (updated) [evidence: test:tests/test_fake_wrapper_contract.py::test_commands_any_name_and_denied]
- ac6: the agent-test config still allows every client command [evidence: command:grep -q 'client: \["\*"\]' e2e/agent-test.config.yaml]
- ac7: (Docker host) the real contract leg passes [evidence: command:mise run test:integration]
- ac8: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: add `test_fake_deny_mirrors_wrapper_default` and the new names in `test_commands_any_name_and_denied`, move the pyproject pin to the merge sha and run `uv lock`; run `uv run --frozen pytest tests/test_images.py tests/test_fake_wrapper_contract.py`: the Dockerfile/README image checks and the mirror test fail.
- Green: update `e2e/agent-test.Dockerfile` (`BASE_IMAGE` sha7, `WRAPPER_SHA`), README `## Images` and `COMMAND_DENY` to the pinned wrapper's list; run the task's verify: passes. Quote the summary line. The real contract leg (ac7) runs in CI on the PR.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 amended: wrapper v0.4.1 merged and tagged: merge sha eed2c3c

- 2026-10-29 done

### S37: orch plugins pin 0.5.1

- Status: done
- Files: `src/agents_orchestrator/settings.py`, `pyproject.toml`, `uv.lock`, `README.md`, `tests/test_settings.py`
- Verify: `uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint`
- Verified head: 3ae80e25b85c1768b10bb7cc9700b20cb642785d

#### Requirement

Leader decision (2026-10-29, mx-34 #462, relaying tatara #460): tatara tagged any-mcp-tatara-plugins `v0.5.1` (76d7fb3, merge ef17204: the orchestrator plugin floors the handover advice threshold at 1%), on top of this epic's `v0.5.0` (dfa0355; `git merge-base --is-ancestor dfa0355 v0.5.1` verified). The slash deploy pins `v0.5.1` instead of `v0.5.0` (deployed pins are always the latest stable, standing rule mx-34 #396).

Scope (agents-orchestrator), on the epic branch rebased onto orchestrator `main`, same files as orch-plugins-pin-0-2-0:
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `v0.5.0` -> `v0.5.1`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.5.1#subdirectory=orchestration/orchestrator`; `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `v0.5.1` and the `## Images` plugins release tag (`v0.5.0` -> `v0.5.1`; the any-mcp `v0.5.0` pin is a different repo and stays).
- `tests/test_settings.py::test_defaults` is no longer accurate (named): it pins `v0.5.0`; it asserts `v0.5.1`.

#### Acceptance conditions

- ac1: the settings default is v0.5.1 (updated) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.5.1 default and no longer names v0.5.0 for the plugins [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.5.1` |' README.md && ! grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.5.0` |' README.md]
- ac4: the pinned orchestrator plugin carries the slash session_send description and the advice floor [evidence: command:d="$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')" && grep -rq "Claude Code slash command" "$d"]
- ac5: settings, images and on-start suites and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint]

#### Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_settings.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: change `tests/test_settings.py::test_defaults` to `v0.5.1`; run `uv run --frozen pytest tests/test_settings.py`: fails on the `v0.5.0` default.
- Green: settings default, pyproject dev dependency (`uv lock`), README rows; run the task's verify: passes. Quote the summary line.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

### S38: orch command name single source

- Status: done
- Files: `src/agents_orchestrator/slash.py`, `src/agents_orchestrator/spec.py`, `tests/test_slash.py`
- Verify: `uv run --frozen pytest tests/test_slash.py tests/test_spec_config.py && mise run lint`
- Verified head: c9bc1ebc2ece5040838799389a42fdcb465e873c

#### Requirement

Scope audit (phase 5 re-audit, .scratchpad/slash-fix-phase5/scope-audit.md), verbatim: "the D2 command-name regex is written twice in agents-orchestrator. Where: `src/agents_orchestrator/spec.py:225` (the `AgentCommand` pattern literal) and `src/agents_orchestrator/slash.py:47` (`_NAME`). Suggested task: build `AgentCommand`'s pattern from the one name constant in `slash.py` instead of a second literal."

Scope (agents-orchestrator, branch slash-commands-from-chat): `slash.py` exposes the D2 name regex once as a public string constant `NAME_PATTERN` (`_NAME` compiles it); `spec.py`'s `AgentCommand` builds its pattern from it (`rf"^(\*|{NAME_PATTERN})$"`), so the literal `[a-zA-Z0-9_][a-zA-Z0-9:_-]*` appears once under `src/`. Behaviour unchanged; a test pins the single source and that `AgentCommand` still accepts `*`, `compact`, `plugin:cmd`, `_x` and rejects `/x`, `a.b`, `-x`.

#### Acceptance conditions

- ac1: the D2 name regex literal appears exactly once under src/ [evidence: command:test "$(grep -rn 'a-zA-Z0-9_\]\[a-zA-Z0-9:_-' src | wc -l)" -eq 1]
- ac2: AgentCommand is built from slash.NAME_PATTERN and still accepts "*", "compact", "plugin:cmd", "_x" and rejects "/x", "a.b", "-x" (new) [evidence: test:tests/test_slash.py::test_agent_command_pattern_shares_slash_name]
- ac3: slash and spec suites and lint pass [evidence: command:uv run --frozen pytest tests/test_slash.py tests/test_spec_config.py && mise run lint]

#### Files

- `src/agents_orchestrator/slash.py`
- `src/agents_orchestrator/spec.py`
- `tests/test_slash.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

- 2026-10-29 actuals: no agent records

### S39: orch wrapper pin 0.4.2

- Status: todo
- Files: `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `README.md`, `tests/fakes/fake_wrapper.py`, `tests/test_fake_wrapper_contract.py`
- Verify: `uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint`
- Verified head: none

#### Requirement

User decision PENDING (mx-34 #471 Q1-3, recommended yes to all; tatara #473 confirmed the version v0.4.2). The leader amends this paragraph with the user verbatim answer before the merge; nothing merges or is tagged before it. Questions, verbatim: "1) Deny the account or cloud group too? That means wrapper v0.4.2 (patch, after v0.4.1) before the slash deploy, about 1 h of agent time. Recommended: yes. 2) Also deny mcp, permissions, config and hooks in v0.4.2? Recommended: yes, so that chat cannot rewrite the session's tool and permission settings. 3) Bump the version to wrapper v0.4.2? Live is 0.3.3, v0.4.1 is tagged but not deployed, and v0.4.2 would replace it in the same deploy. Recommended: yes, pending tatara's confirmation."

Scope (agents-orchestrator, branch slash-commands-from-chat, same files as orch-wrapper-pin-0-4-1): dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<merge sha>` and `uv lock`; `e2e/agent-test.Dockerfile` `BASE_IMAGE` `<sha7>` and `WRAPPER_SHA` `<merge sha>`; README `## Images` agent image `<sha7>`; `tests/fakes/fake_wrapper.py` `COMMAND_DENY` mirrors the pinned wrapper's 64-name `DEFAULT_COMMAND_DENY`; `tests/test_fake_wrapper_contract.py` `test_commands_any_name_and_denied` also refuses "ultrareview", "MCP", "allowed-tools", "remote" and "settings". `<merge sha>`/`<sha7>` are amended by the leader after wrapper-release-0-4-2.

#### Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the fake wrapper's COMMAND_DENY equals the pinned wrapper's DEFAULT_COMMAND_DENY, lower-cased [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_deny_mirrors_wrapper_default]
- ac4: on the fake leg, and on the real leg on a Docker host, "ultrareview", "MCP", "allowed-tools", "remote" and "settings" are refused 403 command_denied while "context" still queues (updated) [evidence: test:tests/test_fake_wrapper_contract.py::test_commands_any_name_and_denied]
- ac5: (Docker host, CI e2e) the real contract leg passes [evidence: command:mise run test:integration]
- ac6: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
