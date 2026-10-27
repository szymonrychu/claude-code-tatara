# slash commands from chat design

## Summary

Any slash command typed in the chat (by the user) or sent by a superleader through
`orchestrator_session_send` runs as a Claude Code slash command on the target session, at any
moment, and the session stays responsive. The orchestrator classifies slash text at both message
routes into `messages.kind = 'command'` and dispatches it unframed, even to a busy agent, to the
wrapper's `POST /v1/sessions/{id}/commands`. Slash text follows Claude Code's own parser. The wrapper
command runner takes any name plus free args (they may span lines), detects completion at runtime per
command class (local stdout, unknown, dialog dismissed by ESC, prompt command promoted to a real turn)
under one deadline per command, and its turns path refuses slash text for every origin (422
`slash_command`), which pins the reported `/reload-plugins` hang. The chat renders the wrapper's
`command_*` events as one updating row. Wrapper 0.4.0 and any-mcp-tatara-plugins 0.2.0 are released
and pinned by the orchestrator; deploy is decided at the gate. Revised after the interrogate pass
(interrogate.md, items 1-13) and the builder check (2026-10-27).

## Intent and why

User request (2026-10-27): "I tried to send `/reload-plugins` from chat window and it made session
unresponsive. Allow these commands to be run from chat window at any moment. Both user and
superleader can send them. Any / comand." Today the chat text is pasted into the PTY as a turn with
a `<!-- ccw turn: id -->` marker; a local command never calls the model, so no Stop hook fires, the
turn never ends (`limits.turn_max_seconds` defaults to 0) and every later turn gets 409 busy. A
superleader's "/cmd" is framed as `<session-message>` prose and never runs as a command.

## Goals

- G1: any slash command typed in the chat runs as a Claude Code slash command on the session, at
  any moment, and the session stays responsive afterwards.
- G2: a superleader can send a slash command to a target session and it runs as a command, not as
  framed prompt text.
- G3: sending /reload-plugins (the reported case) no longer hangs the session; a regression test
  pins it at wrapper and orchestrator level.
- G4: the chat shows the command and its outcome.

## Non-goals

- No slash-command autocomplete or picker in the composer.
- No helmfile pin, apply or smoke task: deploy is decided at the gate for all four new epics
  together (user decision 4).
- No free-form agent command picker in agents-web PresetForm (noted, not doing now).

## Anti-goals

- A slash line is never typed into the PTY with the ccw turn marker appended (the marker becomes the
  command's args).
- Nothing is typed into a responding claude: commands run only at a quiet prompt (existing runner
  rule, `wait_quiet`), mid-turn commands wait for the turn's Stop.
- No command can hold a session busy without a bound (see Bounds).
- No backward-compatibility shim for the five structured command params (Housekeeping rule 4).
- A session-replacing, session-moving or account command (/exit, /clear, /resume, /cd, /login ...),
  under any alias or letter case, never runs: it would break the wrapper's pinned claude session id
  and lifecycle.
- A worker session cannot run unframed commands on a superleader: only a superleader's slash text
  becomes a command (D1).

## Constraints

- Python only (wrapper, orchestrator, plugin); TypeScript for agents-web.
- Services talk only through HTTP; `messages` has one writer per transition (status-guarded
  updates in `db/queue.py`).
- Wrapper tests use the fake claude (`tests/fake_claude/fake_claude.py`), never a real claude; only
  the fake-claude task edits `tests/conftest.py` (this epic never does).
- Orchestrator route/schema changes regenerate `openapi.json`
  (`uv run python -m agents_orchestrator.api.openapi > openapi.json`); agents-web vendors it with
  `npm run sync:api -- orchestrator`.
- agents-web design rules (`src/layout/designRules.ts`): no colour literals outside `theme.ts`, no
  arrows or decorative Unicode, fontWeight 400/500.
- Environment of this container (user decision 5), so task verifies stay targeted and Docker-free
  where possible:
  - agents-orchestrator: every Postgres-backed test (`pool`/`dsn` fixtures, testcontainers) needs
    Docker, absent here. `tests/test_api_messages.py`, `tests/test_agent_session_messaging.py`,
    `tests/test_dispatcher.py`, `tests/test_queue_leader_routing.py`, `tests/test_ambiguous_verify.py`,
    `tests/test_migrations.py` run only in CI (`mise run test` on GitHub) or a Docker host.
    `tests/test_slash.py`, `tests/test_wrapper_client.py`, `tests/test_fake_wrapper_contract.py`
    (fake leg), `tests/test_render.py`, `tests/test_spec_config.py`, `tests/test_images.py`,
    `tests/test_readme_api.py` run here.
  - agents-orchestrator real-wrapper contract leg (`-m integration`, `mise run test:integration`)
    and kind e2e (`mise run test:e2e`, CI job e2e) are CI or Docker-host only.
  - claude-code-wrapper: `tests/test_manager.py::test_shutdown_stops_all`,
    `tests/test_pty_proc.py::test_exit_without_eof_still_fires` and
    `tests/test_pty_proc.py::test_close_terminates_group_then_kill` fail here (PID 1 process group);
    a verify that includes `tests/test_manager.py` deselects the first. `tests/test_container.py`
    needs Docker.
  - agents-web: the full suite has 10 load-dependent timeouts (PresetForm, ScheduleForm, Endpoints,
    FiltersEditor); verifies name the chat test files only.

## Decisions

### D1: the orchestrator classifies slash text at both message routes

`POST /api/v1/sessions/{id}/messages` (`api/messages.py:post_message`, the chat) and
`POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:session_send`, the superleader) both call
one new `agents_orchestrator.slash.parse(text) -> tuple[str, str] | None` and store the message
with `kind = 'command'` when it matches, else `kind = 'turn'`. On the agent route a match stores
`kind = 'command'` only when the sender's own session has `spec.session_messaging` (a superleader); a
leader of any other session sending to a superleader (admitted by the D7 check of
`api/agent.py:session_send`, `own.spec.session_messaging or target.spec.session_messaging`) keeps
`kind = 'turn'`, so its slash text is delivered as framed prose (my call, interrogate item 1: the user
asked for "user and superleader"). Migration
`0008_slash_messages.sql` adds `messages.kind text NOT NULL DEFAULT 'turn' CHECK (kind IN ('turn',
'command'))` and `messages.wrapper_command_id text`. The stored text stays raw (agents-common adopts
an existing message by `marker in m.text`, `runs.py:_post_once`); `MessageView` gains
`kind`. The `commands` table and its CHECK are untouched (commands rows are per agent and lack leader
routing, FIFO and the chat's queue view).
Alternatives: route "/" in the agents-web composer (misses superleaders and API clients); the
wrapper turns endpoint auto-routes "/" (the turns contract returns a turn id the dispatcher stores,
and the superleader frame hides the "/" from the wrapper); a new `commands` kind (needs leader
routing and FIFO rebuilt). Why: ordering, targeting and the queue view already live in `messages`.

### D2: one slash-text rule on both sides, mirroring Claude Code's parser (my call)

Slash text mirrors Claude Code's own parser (claude 2.1.304 binary, interrogate item 2). After
leading whitespace the text starts with `/`. A trailing agents-common run marker
(`<!-- agents-<kind>:<id> -->`, `agents_common.runs.marker`, posted as `text\n\nmarker` by
`runs.py:_post_once`) is removed first (interrogate item 8). The name is the text after the `/` up
to the first whitespace (space, tab or newline); the args are the rest, stripped, and may span
lines. The text is a command when the name is empty (`/`, `/ is root`: claude answers "Commands are
in the form `/command [args]`" and calls no model; the wrapper refuses an empty name 422
`invalid_command`) or matches `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, with no length cap (`/tmp`, `/_x`, a
100-character name: claude runs it or answers "Unknown command", again with no model call, so a bare
`/tmp` fails `unknown_command`). A name with any other character is prose (`/workdir/foo is broken`,
`/etc/hosts`, `//x`, `/notes.txt`): claude sends it to the model as a prompt. The orchestrator
classifies with this rule and the wrapper's turn guard (D3) refuses with the same rule, both pinned
by one shared case table, so a text that claude would parse as a command can never be typed as a
turn. The path-like prose leg is confirmed by a real-binary probe in task wrapper-command-signals; a
result that contradicts this rule is reported back and amends both parser tasks, never worked
around. Args are at most `MAX_COMMAND_ARGS` 20000 characters (my call: webhook prompt templates
render issue bodies and the default event block) and may hold newlines and tabs; `\r\n` is
normalised to `\n`; any other control character (ESC included, so args cannot end the bracketed
paste the line is typed in) and U+2028/U+2029 are refused 422 `invalid_command`, and the message
fails visibly with that code (D10).
Alternatives: the first D2 rule (`[A-Za-z0-9][A-Za-z0-9:_.-]{0,63}`, empty and over-long names as
prose): `/`, `/ is root`, `/_x` and long names were typed as turns, claude called no model, no Stop
fired and the session hung (interrogate item 2); one-line args: a preset prompt starting with `/`
plus its run marker (agents-common) would fail `invalid_command` where it ran before (interrogate
item 8). Why: claude decides what is a command, so both sides must agree with it exactly.

### D3: the wrapper turns path refuses slash text for every origin

`Session.submit` raises `TurnRejected("slash_command")` for slash text (D2 rule) before reserving the
slot or typing, for every origin (client, peer, initial, agent). `SessionRouter.submit_turn` checks
the same rule first, so no onTurn hook fires and no file is written for a refused turn.
`POST /v1/sessions/{id}/turns` maps it to 422 `slash_command` with the message "slash commands go to
POST /v1/sessions/{id}/commands". `SessionManager._initial_turn` routes a slash initial prompt to
`router.request_command(name, args, origin="client")` (refusals are reported as today's
`initial_turn_rejected` error event). Peer turns are framed (`peer_inbox.py` `frame(item)`), so a
peer "/x" is prose by construction. This is the regression pin for the reported hang.
Alternative: only the orchestrator guards (other clients and the initial prompt still hang).

### D4: any command name plus free args (no structured params)

`commands.py`: `validate(name, args)` (name by the D2 name pattern, an empty name refused
`invalid_command`; args by the D2 args rule: newlines and tabs allowed, `\r\n` normalised, at most
`MAX_COMMAND_ARGS` 20000 characters, no other control character), `render(name, args)` =
`f"/{name} {args}".rstrip()`, `CommandRecord.args: str` (default ""). `BUILTIN_COMMANDS`,
`validate_params` and `params_schema` are removed. `--force` among the args of `reload-plugins` needs
`allow_force` (`force_not_allowed`). `POST /v1/sessions/{id}/commands` takes `{name, args: str = ""}`.
The ccw MCP tool `command` takes `{name, args?}` (name: an enum of the agent allowlist, or a plain
string when the allowlist holds `"*"`). The onCommand hook payload and `command_*` event records
carry `args` as a string. Auto-compact queues `compact` with args = `auto_compact.instructions`.
Ruling (my call): a queued duplicate coalesces only when name and args are identical, so `/model a` and `/model b` both queue.
The line is typed as one bracketed paste and one CR (`Session.send_command`, `pty.send_prompt`), so a
second line of multi-line args that starts with `/` is part of the first command's args, never a
command of its own (the probe: a paste "/x\n\n<!-- ccw turn: id -->" ran /x with the rest as args).
Alternatives: keep the five built-ins and add names one by one (never complete: every skill and plugin
command is a command). Why: "Any / command" (user); user decision 1 adopted the replacement with no shim.

### D5: the deny list is one config value; allowlists take names or "*"

`sessions.commands.deny: list[str]`, default (my call, interrogate item 5) `[exit, quit, clear,
reset, new, resume, continue, branch, fork, cd, background, bg, teleport, tp, stop, remote-control,
rc, restart, update, login, logout, upgrade, setup-bedrock, setup-vertex, web-setup, design-login]`
(`DEFAULT_COMMAND_DENY` in `config.py`), matched case-insensitively (`/EXIT`, `/Clear` are denied),
checked before the allowlists: 403 `command_denied`. Aliases are listed by name from claude's own
alias table (binary grep, 2026-10-27: clear `reset`, `new`; resume `continue`; exit `quit`; restart
`update`; background `bg`; teleport `tp`; remote-control `rc`), each pinned by a test, so the list
stays one config value with no alias resolver. `sessions.commands.agent|client` accept names (D2
pattern) or `"*"`; `timeout_seconds` keys are free names or `default`; `CommandsOverride` mirrors
`deny`. A gate change to the deny list is an amend of this one default and its pins (user decision
2). The orchestrator renders no deny list (the wrapper default applies), the orchestrator's fake
wrapper copies it with a comment naming the source, and the plugin description names no list (D13),
so the value lives in one place. Reasons, per name (claude's own descriptions from the binary,
`.scratchpad/probe-slash/summaries/cmdtable.txt` for the table):

| Name (aliases) | Ruling | Why |
|---|---|---|
| exit (quit), restart (update) | denied | end or relaunch the claude process the wrapper owns |
| clear (reset, new), resume (continue), branch, fork | denied | start or switch to another claude session id; the wrapper pins `--session-id` and drops every later Stop |
| cd | denied | "Move this session to a new working directory": the wrapper pins the workdir and tails the transcript of that project dir |
| background (bg), stop | denied | "Send this session to the background and free the terminal", "Stop this background session": detach or end the session the PTY holds |
| teleport (tp) | denied | "Send this session to the cloud, or resume one from claude.ai": replaces the session |
| remote-control (rc) | denied | "Control this session from your phone or claude.ai/code": a second controller past the wrapper's auth and its single PTY writer |
| login, logout, upgrade | denied | account identity or plan |
| setup-bedrock, setup-vertex, web-setup, design-login | denied | reconfigure provider credentials or link an account (credentials are the highest-risk surface) |
| session (remote) | allowed | "Show cloud session URL and QR code": read-only |
| every other cmdtable.txt name | allowed | informational, a setting, a dialog dismissed by ESC (D7) or a prompt command run as a turn (D8); recoverable by ESC and the bound |

Why: these end, replace or move the claude process or session, hand it to another controller, or
change account identity or credentials; everything else is recoverable by ESC and the bound.
Alternative: no deny list ("any" literally): /clear blinds the wrapper (new claude session id,
every later Stop dropped), /exit kills claude.

### D6: completion by runtime class detection, local and unknown classes

The runner keeps: wait quiet (`quiet_seconds` 1.5) -> onCommand -> mark -> type the line (no marker)
-> await. `_await_completion` becomes class-agnostic, first signal after the mark wins:
1. a `command_output` after any `command_invoked` (claude echoes the resolved alias: /cost echoes
   /usage) -> completed, `output` = stdout; stderr only -> failed `command_error`; compact keeps its
   PostCompact / compact_boundary / failure-pattern leg; reload-plugins keeps `skipped_cache`.
2. a `command_unknown` (new transcript event from a `system` line of subtype `informational`
   "Unknown command: /x", also in the suggestion form "Unknown command: /x. Did you mean /y?" that
   the binary writes for a near miss, interrogate item 11) -> failed `unknown_command` at once, no
   ESC.
Real-binary probe (user decision, my call on placement): task wrapper-command-signals settles, in a
throwaway dir under `/workdir/workdir/.scratchpad/probe-slash` and recorded in the wrapper's
`MEMORY.md`, whether local commands never fire UserPromptSubmit and how claude treats path-like prose
such as `/workdir/foo is broken` (D2); a result that contradicts the design is reported back, not
worked around.
Transcript fix: a `system/local_command` body starting with `<command-name>` is a `CommandInvoked`
(today a `CommandOutput` with empty stdout, so /context, /model and every dialog command on the real
binary never match). The fake claude writes the real echo shapes: user echo for reload-plugins,
compact, mcp, model with an arg; system echo for context; informational line for an unknown name.

### D7: dialog commands are dismissed by ESC under a budget

A `DialogScanner` (a `FatalScanner` over `sessions.commands.dialog_patterns`, default `esc to cancel`,
`esc to close`, `esc to clear`, `esc to exit`, `enter to confirm`) is fed the PTY output from the
mark. No completion signal and a dialog hit -> wait `dialog_grace_seconds` (2.0, restarted by any PTY
output) for a late signal, then ESC; 1.5 s later, if still no `command_output` and the scanner hit
again since the ESC, ESC again (budget 3, never two ESCs within 1 s: a double ESC at an empty prompt
opens the rewind menu). Output after an ESC -> completed `dismissed`, output = claude's stdout
("Help dialog dismissed"). No output after the budget -> failed `dialog_stuck`. Timeout
(`timeout_seconds[name]`, default 60, compact 600) -> ESC, 1.5 s, a second ESC only when a dialog
pattern is on screen -> failed `timeout`. Compact is excluded from dialog detection (its own leg).
One deadline per command (my call, interrogate item 7): `timeout_seconds[name]` counts from the
runner taking the command and is spent by the quiet wait, typing, the completion wait and the
dialog leg together (today `wait_quiet` and the completion wait each spend a full `timeout`, about
2x the stated bound). A dialog left open (my call, interrogate item 6): when a command ends
`dialog_stuck`, or `timeout` with a dialog pattern still on screen after the last ESC, claude is
restarted through the existing relaunch path (`Session._recover`: `_boot(resume=True)`, the same
pinned claude session id) before the slot is released, so the next turn never lands in an open
dialog (a paste into an open dialog acts on it, probe outA). This wrapper-initiated restart does
not count against `max_restarts` (my call: three stuck dialogs must not kill a session), emits the
usual restart event, and a failed relaunch takes the crash path's outcome (dead).
Dialog commands stay allowed: "dismissed" with claude's own message is the honest answer for a chat
with no keyboard (user decision 1).

### D8: a prompt (skill, plugin) command is promoted to a real turn

`_on_user_prompt_submit` publishes `prompt_submitted` on the SignalBus while a command runs. On that
signal the runner calls `Session.adopt_turn(line, origin)` (origin client -> turn origin `client`,
agent -> `agent`, idle -> `agent`): a running `TurnRecord` is created and persisted while the slot is
already held, `router._last_marker` is set to its turn id (so its Stop is not dropped as stale),
`turn_started` and `user_message` are emitted; the command record completes at once with result
`turn` and `turn_id`. The turn then ends like any turn (Stop, interrupt, `turn_max_seconds`).
Rulings (my call): after a promotion the runner stops; commands still queued stay queued for the
promoted turn's Stop. In the agent same-turn path (commands run at a held turn's Stop, D9), a prompt
command does not create a new record: the held turn continues as the prompt command's turn
(`_commands_turn` cleared, `_last_marker` = the held turn id, result `turn` with that turn id) and no
continue prompt is typed. The hold is released through a session API (my call, interrogate item 10;
for example `Session.release_commands_hold(record)`), which clears the session's own
`_commands_turn` (session.py `continue_turn`, `interrupt`), so an interrupt on the continued turn
sends ESC like any running turn instead of ending the record with no ESC.
Real-binary probe (user decision): task wrapper-prompt-command-turn settles, in a throwaway dir
under `/workdir/workdir/.scratchpad/probe-slash` and recorded in the wrapper's `MEMORY.md`, whether
Stop fires after a promoted prompt-command turn and whether plugin commands fire UserPromptSubmit; a
result that contradicts the design (or a fact the probe cannot settle, for example with no
credentials for a model call) is reported back, not worked around.
Alternative: wait for a Stop under the command record (the Stop is dropped as stale today and the
model turn has no record or accounting).

### D9: "at any moment" = accepted at once, run at the turn's Stop, no continue prompt

The orchestrator dispatches a command even to a busy agent (D10); the wrapper queues it and runs it
at the running turn's Stop (Claude Code itself holds commands typed while it responds until the turn
ends: parity). When every pending command has origin `client`, `_stop_gate` lets the Stop complete
the turn normally (`turn_completed`, final text intact) and the idle runner starts after the turn
completed; no `continue_prompt`, no `turn_resumed`. Agent-origin commands keep the same-turn resume.
Slot handover (my call, interrogate item 4): the router takes the slot for the queued client
commands (`_start_idle_runner`, `Session.begin_command`) synchronously right after
`session.complete` and before any await (onTurnComplete, the callback), so a `POST /turns` right
after `turn_completed` gets 409 `busy` until the queued commands drained; prose can no longer take
the slot ahead of them.
This behaviour is isolated in task wrapper-commands-after-stop, so a gate change (for example
interrupt and run now) is an amend of that one task (user decision 2).
Alternatives: type into the responding claude (claude defers it anyway; loses the completion window;
the fake drops bytes typed while busy); interrupt, run, resume (destroys work on a typo).

### D10: dispatch of kind=command messages

`db/queue.py`: `Claim.kind`; a command head picks an agent with `_PICK_COMMAND` (ready, not gone,
has a wrapper session, the target or the leader; no `state = 'idle'` and no `free_since` predicate);
a command neither needs nor writes the `agents.last_dispatched_at` reservation (my call: a command
does not take the orchestrator's turn slot, and a rejected command would otherwise leave
`last_dispatched_at > free_since` and starve prose); a command is exempt from the busy-leader hold
and the handover hold of `_claim_in_session` but not from backoff (`not_before`) or a gone leader
(it waits for the successor) (my call). It may overtake queued prose of its session (intended: "at
any moment"). `dispatcher/loop.py:_send` sends kind=command unframed (no `<session-message>`) with
`WrapperClient.command(wsid, name, args)`. Outcomes: 202 -> `mark_sent_command` (status `sent`,
`wrapper_command_id`); 409 booting|dead and 429 `command_queue_full` -> requeue with `not_before =
now() + retry_backoff_base_seconds`, no attempt counted (my call: an immediate requeue would spin on a
full wrapper queue); 403 `command_denied` | `command_not_allowed` and 422 -> failed with the wrapper's
envelope code as `error` (my call: QueueStrip shows `error`, so the user sees why); 401 -> failed
`config_error`; 404/410 -> as a turn (backoff, rebootstrap); an ambiguous send (read timeout, 500,
502) -> failed `ambiguous` (my call: the verifier looks for a turn carrying `orch_message_id`, a
command has none, so verifying would resend it blindly); a stale `dispatching` command row is failed
`ambiguous` by the verifier instead of resent. Only the user's Retry resends a failed command.
`WrapperClient.command(session_id, name, args)` returns `CommandOutcome = CommandAccepted(command_id,
record) | Busy | ConfigError | Rejected(code, reason) | Gone | Unavailable | Ambiguous`; the existing
`/agents/{id}/compact` path keeps its `done {response: record}` result.
The args the dispatcher sends are `slash.parse(text)`'s, so a trailing agents-common run marker is
never sent to claude (D2); the stored text keeps it.
Per-session order (my call, interrogate item 3): while a session has a `kind = 'command'` row in
`dispatching`, no later message of that session (higher id, prose or command) is claimed; the
command's 202 puts it in the wrapper's FIFO command queue, so two commands, or a command and later
prose, of one session reach the wrapper in id order. Pinned in `tests/test_queue_leader_routing.py`.
Hop guard (my call, interrogate item 9): a command message stores no `turn_id` at 202, so sends
from its promoted turn (D8) would restart at hop 1 and bypass `session_message_max_hops`.
`queue.link_command_turn(conn, wrapper_command_id, turn_id)` is the one writer of the transition
"sent command, no turn -> linked turn": `UPDATE messages SET turn_id = ... WHERE kind = 'command'
AND status = 'sent' AND wrapper_command_id = ... AND turn_id IS NULL`, called by the ingester when it
stores a `command_completed` envelope whose record has `result = 'turn'` and a `turn_id`. For the
reverse arrival order (the event stored before the dispatcher's 202 handling), `mark_sent_command`
takes that `turn_id` from the stored `command_completed` event in its own guarded update
(`dispatching -> sent`). `queue.turn_hop` then finds the command message of the promoted turn, so a
send from it counts that message's hop plus one; agents-common's run tracker also sees the promoted
turn's completion on the message.

### D11: the orchestrator renders `sessions.commands.client: ["*"]`

`k8s/render.py` always renders `sessions.commands.client = ["*"]` (the orchestrator is the wrapper's
only client; this also repairs the compact button, refused 403 today because the client allowlist was
never rendered) and `sessions.commands.agent = spec.wrapper.agent_commands` when set.
`spec.wrapper.agent_commands` becomes `list[str]` of names (D2 pattern) or `"*"`, validated by the
wrapper's config model through the existing render validation. Needs the 0.4.0 wrapper pin (the
0.3.0 config model rejects `"*"`).

### D12: the chat shows one updating command row

agents-web `chatModel.ts` adds a `command` ChatItem `{commandId, name, args, status, result?,
error?, output?}` built from `command_queued`, `command_started`, `command_completed`,
`command_failed` event rows (`data.record`), updated in place by `record.id` (tool-row pattern):
status `queued` -> `running` -> `completed` (with result ok | dismissed | skipped_cache | turn) or
`failed` (with error) or `cancelled`. `entries.tsx` renders it with the label `command`, the line
`/name args`, the status and the output in a mono `<pre>`. Ruling (my call): `user_message` rows with
origin `command` (the typed-line echo) are folded into the command row and not rendered on their
own, so a command shows once. A promoted prompt command also shows its normal turn rows. A command
the orchestrator could not deliver shows in QueueStrip as failed with the wrapper code (D10).
Composer is unchanged (non-goal: no picker).

### D13: the superleader's tool says what slash text does

any-mcp-tatara-plugins `orchestration/orchestrator` `_descriptions()["session_send"]` adds: "When
your session is a superleader, text that starts with a slash command such as /compact runs as a
Claude Code slash command on the target session's leader (not framed); commands that end or replace
a session, such as /exit or /clear, are refused. From any other session it is delivered as a
message." (my call, matching D1 after interrogate item 1). It names no full list (D5 keeps the list
in one place).
Release and pin (builder check, my call): any-mcp-tatara-plugins `v0.2.0` after the description
change (task plugins-release-0-2-0: version bump; the tag is pushed by the orchestrator session after
the merge), then the orchestrator pins it (task orch-plugins-pin-0-2-0: the `ORCH_ANY_MCP_PLUGINS_REF`
default, the `any-mcp-tatara-orchestrator` dev dependency, README, tests), so superleaders actually
see the description. The helmfile value of `ORCH_ANY_MCP_PLUGINS_REF` stays with the gate's deploy
decision.

### D14: release and pin like leader-auto-handover; no deploy task

claude-code-wrapper 0.4.0 (version bump, tag `v0.4.0` on the merge commit after the `main` build,
run by the orchestrator session), then agents-orchestrator pins that merge commit (pyproject, uv.lock,
`e2e/agent-test.Dockerfile`, README Images) and enables `client: ["*"]` in
`e2e/agent-test.config.yaml` for the real contract leg and e2e. No agents-helmfile task (user
decision 4). Precedent: in-progress epic leader-auto-handover tasks wrapper-release-0-3-0 and
orch-wrapper-pin-0-3-0.
Builder check settlements (my call): the wrapper PR merges mid-epic through the normal PR flow; the
orchestrator session pushes tag `v0.4.0`, and wrapper-release-0-4-0's "tag exists on origin"
condition is checked by the orchestrator after that push, not by the implementer or reviewer.
Kind e2e placement (my call, interrogate item 12): the e2e job runs on every PR and agents get
`client: ["*"]` only from the render change (D11), so an e2e case in the pin PR would be red with
403. The case is its own task orch-e2e-slash-command, right after orch-render-client-commands (a
separate task keeps orch-render-client-commands at 8 files); orch-wrapper-pin-0-4-0 no longer
touches `tests/e2e/test_e2e_kind.py`.

### D15: the commands metric label stays bounded (my call)

`metrics.py` keeps a fixed label set `METRIC_COMMAND_NAMES` (compact, context, mcp, reload-plugins,
reload-skills) and counts every other name as `other`, so arbitrary names cannot grow the label
cardinality. Alternative: label by any name (unbounded series).

### D16: the fake claude logs keys in a separate file (my call)

ESC keys the fake receives are appended to `$CLAUDE_CONFIG_DIR/fake-keys.jsonl` (`{"key": "esc",
"ts"}`), not to `fake-inputs.jsonl`, so the existing pins that every input was typed while idle
(`tests/test_command_turn_resume.py`, `tests/test_fake_claude_commands.py::test_esc_not_recorded_as_busy`)
stay accurate, and dialog tests can count and space ESCs.

### D17: the wrapper's slash-command docs and examples follow the new model

README `## Slash commands` (tool, endpoint, lifecycle, configuration, limits) describes any name,
args, the deny list, the classes and bounds; the Limits paragraph "the five names above are the
whole set" goes. `data/examples/workbench.config.yaml` sets `client: ["*"]`; tatara and magic-trainer
keep their agent lists. `config.example.yaml` documents `deny`, `dialog_grace_seconds`,
`dialog_patterns`.

### D18: the args vocabulary change is one atomic task (sizing exception)

wrapper-command-args touches 12 files (4 source, README, 7 test files), over the 8-file guideline:
removing `validate_params` and `params_schema` and changing `CommandRecord.args` to a string breaks
every caller (router, API, MCP server) and the tests that pass params dicts in the same commit; there
is no green intermediate without a compatibility shim (rule 4). The config and deny change (D5) is
split off before it to keep this task as small as it can be. Opus.

## Bounds

- one deadline per command (my call, interrogate item 7): `timeout_seconds[name]`
  (`default` 60 s, `compact` 600 s; operators may add names), counted from the runner taking the
  command and spent by the quiet wait (`quiet_seconds` 1.5 s), typing, the completion wait and the
  dialog leg together; "screen never settled" fails `timeout` at that deadline.
- dialog: `dialog_grace_seconds` 2.0 s after the first footer hit; ESC budget 3, 1.5 s apart, never
  two ESCs within 1 s; `dialog_stuck` after the budget; all inside the deadline.
- at the deadline: ESC, 1.5 s, a second ESC only with a dialog pattern on screen -> `timeout`.
- dialog still open after `dialog_stuck` or `timeout` (my call, interrogate item 6): one claude
  relaunch with `--resume` before the slot is released, bounded by `boot.timeout_seconds` (60 s);
  it does not count against `max_restarts`.
- unknown command: completes on the informational line (under 1 s typically), the suggestion form
  included; no ESC.
- promoted turn: `limits.turn_max_seconds` (0 = unbounded, as every turn), `turn_stall_seconds` 1800
  reports; the interrupt endpoint remains the manual bound.
- worst-case slot hold for a non-promoted command: timeout + 1.5 s = about 62 s (default), plus one
  relaunch of at most `boot.timeout_seconds` 60 s when a dialog stays open.
- args: at most `MAX_COMMAND_ARGS` 20000 characters (D2).
- orchestrator: `wrapper_send_timeout_seconds` 15 s per POST (exists); 409/429 requeue after
  `retry_backoff_base_seconds`.
- wrapper queue cap: `MAX_QUEUED` 4 per session (exists) -> 429.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| discovery (codebase-cartographer per repo) | ran: .scratchpad/discovery/claude-code-wrapper.md, agents-orchestrator.md, agents-web.md | reuse of the command queue, runner, SignalBus, interrupt (claude-code-wrapper.md Plan inputs); messages queue and leader routing (agents-orchestrator.md Plan inputs); tool-row update pattern (agents-web.md, chatModel.ts:155-170) | a second command channel or MCP server (claude-code-wrapper.md do-not-build); typing slash text with the marker (same) |
| architect-researcher (design fork) | ran: .scratchpad/discovery/slash-commands-design.md | Picks 1-5 (D1, D3-D9, D11, D12); bound values (Bounds) | composer routing (Pick 1 A); wrapper auto-route (Pick 1 C); interrupt and resume (Pick 4 B); polling command status (Pick 5 A) |
| research-docs | ran inside the architect pass: https://code.claude.com/docs/en/commands, https://code.claude.com/docs/en/interactive-mode (fetched 2026-10-27) | commands typed while claude responds are held to the turn end (D9 parity); double Esc opens the rewind menu (D7 spacing); /exit alias /quit (D5) | immediate typing for "immediate" commands (Pick 4 A) |
| research-code-internal | ran as the discovery sweep (each repo over ~200 files was mapped by grep and reads; no LSP in the session) | transcript parser gap (D6), stale-Stop drop for command echoes (D8), unrendered client allowlist (D11) | classifying by the binary's type flags (claude-code-wrapper.md ideas: inferred, not stable) |
| research-code-external | skipped: no known analogue wraps Claude Code's TUI commands; the fork was settled by probes | none | none |
| research-papers | skipped: no algorithmic core | none | none |

Probes and facts the design rests on (claude 2.1.304, throwaway session under
/workdir/workdir/.scratchpad/probe-slash: raw screens in out/, outA/ .. outD/; the per-probe transcript
summaries in summaries/outA.txt .. outD.txt (copied there from the architect's session scratchpad); the
last probe's full transcript in config/projects/-workdir-workdir--scratchpad-probe-slash-work/64b31430-13c7-48b0-ba54-c6c432f345db.jsonl):

| Fact | Kind | Source |
|---|---|---|
| a paste "/x\n\n<!-- ccw turn: id -->" runs /x with the marker as `<command-args>` | probed | slash-commands-design.md section 1 |
| local commands (/reload-plugins, /compact, /clear, /exit, /model arg, /mcp) write a user echo then `<local-command-stdout>` | probed | design section 2 |
| /context writes its echo as `system/local_command` | probed | design section 2 |
| dialog commands (/help, /model, /config, /usage, /cost, /resume, /permissions, /theme) write nothing until ESC, then echo + "... dismissed" stdout; /config needs two ESCs; footers "Esc to cancel", "Esc to clear", "Enter to confirm . Esc to cancel" | probed | design section 2 |
| a paste into an open dialog acts on it (a CR toggled auto-compact) | probed | design section 2, outA |
| unknown "/nonexistent args" writes `system/informational` "Unknown command: /nonexistent" and "Args from unknown skill: args"; no hook | probed | design section 2 |
| a prompt command (/hello world) writes the command-message echo, an isMeta body and fires UserPromptSubmit | probed | design section 2, hooks.log |
| Stop fires at the end of a promoted prompt-command turn | inferred (no credentials in the probe) | design section 7; pinned by the fake, live-checked by the contract leg with a login |
| /clear starts a new transcript and claude session id (wrapper then drops every Stop) | probed | design section 2 |
| `_system_events` turns a `<command-name>` system body into CommandOutput(stdout="") | read-from-code | claude-code-wrapper src/claude_code_wrapper/transcript.py:_system_events |
| `turn_max_seconds` defaults to 0 and stall only reports | read-from-code | config.py:688, session.py:_watch_turn |
| stop_target drops a Stop whose marker names another turn | read-from-code | session.py:stop_target |
| the orchestrator never renders `sessions.commands.client` | read-from-code | agents-orchestrator k8s/render.py:133-134 |
| the compact button is refused 403 by a real wrapper | inferred (not run live) | agents-orchestrator.md Open questions 1; fixed by D11 either way |
| plugin-namespaced commands (/workbench:x) also relay UserPromptSubmit | inferred | design section 8; contract leg with a login confirms |

## Research inputs

Retro proposals of the most recently done epics (`ticket.py retro --history`), recurring workflow
ones first:

- recurring (cross-session-messaging-and, paste-env-contents-into-the, generic-any-mcp-with-git-and):
  defects found only late because test fakes encoded the same wrong assumption; change: a task whose
  code reacts to an external tool's output cites a captured real sample and the reviewer checks the
  fake against it. Acts on it: wrapper-command-signals, wrapper-dialog-commands,
  wrapper-prompt-command-turn (each cites the probe transcripts under
  /workdir/workdir/.scratchpad/probe-slash/ for the fake's echo shapes), orch-wrapper-command-client
  (the fake wrapper's command record shape is pinned by the contract test's real leg).
- recurring (cross-session-messaging-and, agents-matrix-connector, paste-env-contents-into-the):
  hand-backs quote the verify summary line with counts against the committed head; run pytest with a
  summary-printing flag, not bare -q. Acts on it: every task (verifies run pytest without an extra
  `-q`: the repos' addopts already pass `-q`, and `-qq` hides the counts).
- recurring (matrix-read-receipts, paste-env-contents-into-the): a ruling in Notes not pinned by a
  test was found only in review; change: every merge-semantics or tiebreak ruling names its pin
  test. Acts on it: orch-dispatch-commands (no reservation, hold exemption, backoff, error codes),
  wrapper-prompt-command-turn (queued commands stay queued after a promotion), web-command-rows
  (echo fold), wrapper-command-policy (deny before allowlist).
- recurring (generic-any-mcp-with-git-and, cross-session-messaging-and, matrix-read-receipts,
  agents-matrix-connector-depl): live apply and smoke tasks run far over the minutes seed; change:
  seed them at 15-25 min. Not applicable: this epic has no apply or smoke task (user decision 4).
- recurring (matrix-read-receipts, agents-matrix-connector-depl): the permission classifier blocks
  subagent live actions; plan live steps as orchestrator-run. Acts on it: wrapper-release-0-4-0 (the
  tag push is an orchestrator-session step).
- code proposal (generic-any-mcp-with-git-and): keep one shared parity test table so two grammars
  cannot drift. Acts on it: orch-slash-parser and wrapper-slash-turn-guard use the same D2 case table.
- one-off (cross-session-messaging-and): task ACs must name existing test files or mark them new.
  Acts on it: every task marks new tests "(new)".
- one-off (cross-session-messaging-and): kind e2e allow-list assertions should derive from the
  shared constant. Acts on it: orch-e2e-slash-command (the e2e case asserts on the wrapper's error
  code, not on a hard-coded list).

Interrogate (interrogate.md, 2026-10-27) Act-on items, each applied (user decision):

| Item | Decision | Task(s) |
|---|---|---|
| 1 worker-to-superleader commands | D1 | orch-session-send-command |
| 2 parser mirrors claude | D2, D4 | orch-slash-parser, wrapper-slash-turn-guard, wrapper-command-policy, wrapper-command-args, orch-wrapper-command-client, orch-render-client-commands |
| 3 per-session order | D10 | orch-dispatch-commands |
| 4 slot handover at Stop | D9 | wrapper-commands-after-stop |
| 5 deny aliases and session-moving commands | D5 | wrapper-command-policy, orch-wrapper-command-client |
| 6 dialog left open | D7, Bounds | wrapper-dialog-commands |
| 7 one deadline per command | D7, Bounds | wrapper-dialog-commands |
| 8 run marker and multi-line args | D2, D4, D10 | orch-slash-parser, wrapper-command-args, orch-dispatch-commands |
| 9 hop guard for promoted commands | D10 | orch-command-turn-link (new) |
| 10 held-turn interrupt | D8 | wrapper-prompt-command-turn |
| 11 unknown command with suggestion | D6 | wrapper-command-signals |
| 12 e2e placement | D14 | orch-e2e-slash-command (new), orch-wrapper-pin-0-4-0 |
| 13 evidence that already passes | - | orch-dispatch-commands ac10, web-sync-message-kind ac3 |

Noted items (real-binary probes, user decision): wrapper-command-signals (local commands and
UserPromptSubmit, path-like prose), wrapper-prompt-command-turn (Stop after a promoted turn, plugin
commands and UserPromptSubmit). Consider item (immediate commands mid-turn): Open questions Q2.
Builder check: plugins release and pin (D13: plugins-release-0-2-0, orch-plugins-pin-0-2-0), the
wrapper tag flow (D14: wrapper-release-0-4-0), `/tmp` as an unknown command (D2).

Discovery plan inputs placed:

- fix-as-ac, slash text submitted as a turn leaves the session busy forever (claude-code-wrapper.md):
  wrapper-slash-turn-guard.
- fix-as-ac, prompt commands' Stop dropped as stale (claude-code-wrapper.md): wrapper-prompt-command-turn.
- fix-as-ac, peer and initial-prompt turns share the hang (claude-code-wrapper.md):
  wrapper-slash-turn-guard.
- fix-as-ac, the orchestrator never renders the client allowlist (agents-orchestrator.md):
  orch-render-client-commands.
- fix-as-ac, the fake wrapper ignores the allowlist (agents-orchestrator.md):
  orch-wrapper-command-client.
- fix-as-ac, `WrapperClient.command` sends only `{name}` (agents-orchestrator.md):
  orch-wrapper-command-client.
- fix-as-ac, a "/" chat message becomes a never-ending turn (agents-orchestrator.md):
  orch-message-kind, orch-dispatch-commands.
- fix-as-ac, agents-web full-suite timeouts (agents-web.md): out of this epic's scope; verifies name
  the chat test files only (noted, not doing now: the 10 load-dependent timeouts).
- reuse: CommandQueue, runner, SignalBus, interrupt, begin_command/end_command (wrapper tasks);
  `_leads` and the D7 refusal order of session_send (orch-session-send-command); chatModel tool-row
  pattern and ChatLog virtuoso stand-in (web-command-rows).
- do-not-build: a second command channel, a second PTY writer, client-side routing of "/" (Composer
  unchanged), hand edits to `src/api/schema.d.ts` (web-sync-message-kind regenerates it).

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 orchestrator classifies at both routes | orch-slash-parser, orch-message-kind, orch-session-send-command |
| D2 one slash-text rule | orch-slash-parser, wrapper-slash-turn-guard, wrapper-command-policy, wrapper-command-args |
| D3 wrapper refuses slash turns | wrapper-slash-turn-guard |
| D4 any name plus args | wrapper-command-args |
| D5 deny list and wildcard | wrapper-command-policy, orch-wrapper-command-client |
| D6 local and unknown classes | wrapper-command-signals |
| D7 dialog commands | wrapper-dialog-commands |
| D8 prompt command promoted | wrapper-prompt-command-turn |
| D9 run at Stop, no continue prompt | wrapper-commands-after-stop |
| D10 dispatch of command messages | orch-wrapper-command-client, orch-dispatch-commands, orch-command-turn-link |
| D11 render client allowlist | orch-render-client-commands |
| D12 command row in the chat | web-command-rows, web-sync-message-kind |
| D13 superleader tool description | plugin-session-send-slash, plugins-release-0-2-0, orch-plugins-pin-0-2-0 |
| D14 release and pin | wrapper-release-0-4-0, orch-wrapper-pin-0-4-0, orch-e2e-slash-command |
| D15 bounded metric label | wrapper-command-policy |
| D16 fake key log | wrapper-command-signals, wrapper-dialog-commands |
| D17 wrapper docs and examples | wrapper-command-docs |
| D18 atomic args task | wrapper-command-args |

## Review focus

- The slot invariant: every path that takes the wrapper slot (begin_command, hold_for_commands,
  adopt_turn) releases it or hands it to a turn record; `end_command` in `finally`; no command can
  hold busy past the Bounds. Tests: the regression pins in wrapper-slash-turn-guard and
  wrapper-command-signals, dialog_stuck and timeout in wrapper-dialog-commands.
- ESC safety: ESC is only sent while a dialog pattern is on screen since the last ESC or at a
  timeout, never two within 1 s, never at an idle prompt otherwise.
- `_claim_in_session` FIFO: prose order within a session is unchanged; only command heads skip the
  holds; command claims never write `last_dispatched_at`; nothing later of a session is claimed while
  one of its command rows is `dispatching`.
- The deny list lives only in `DEFAULT_COMMAND_DENY` (the orchestrator fake's copy names it), matched
  case-insensitively, aliases listed.
- The two parsers (orchestrator `slash.parse`, wrapper turn guard) share one case table that mirrors
  claude's parser (D2).
- Only a superleader's slash text becomes a command (D1); a promoted command turn keeps the hop
  count (D10).
- A wrapper-initiated restart for an open dialog resumes the same claude session id and leaves
  `max_restarts` untouched.
- The fake claude's echo shapes match the probe transcripts (retro proposal).

## Left to the builder

- Internal helper names and module layout inside the named files (for example where `is_slash_text`
  lives in the wrapper, as long as `Session.submit` and `SessionRouter.submit_turn` share it).
- The exact human wording of 4xx messages, as long as the codes match this design.
- Fake wrapper (orchestrator) command timing model, as long as it emits `command_queued`,
  `command_started`, `command_completed` with the record shape of the real wrapper and runs a
  command queued during a turn after that turn completes.

## Assumptions and unknown facts

- Stop fires at the end of a promoted prompt-command turn on the real binary (inferred; the probe had
  no credentials). Settled by the real-binary probe of task wrapper-prompt-command-turn (recorded in
  the wrapper's MEMORY.md); the fake pins the assumed behaviour. A contradicting result, or no
  credentials to run the model call, is reported back.
- Plugin-namespaced commands (/workbench:x) relay UserPromptSubmit like /hello (inferred); settled by
  the same probe. If they do not, D8 promotes on the transcript echo plus isMeta pair instead (design
  section 8), an amend of wrapper-prompt-command-turn.
- Local commands never fire UserPromptSubmit, and claude sends path-like prose (`/workdir/foo is
  broken`, `/etc/hosts`) to the model while `/tmp` gets "Unknown command" (inferred from the binary's
  regex; D2). Settled by the probe of task wrapper-command-signals; a contradiction amends the two
  parser tasks.
- Claude's own command table, aliases and descriptions (D5) are read from the 2.1.304 binary; a
  newer claude may add session-ending names, which is an amend of `DEFAULT_COMMAND_DENY`.
- The claude-code-wrapper repo has no `MEMORY.md` yet; task wrapper-command-signals creates it with
  its probe entry.
- Migration number 0008 is free: no other todo or in-progress epic adds an orchestrator migration
  (grep of docs/plans/todo and in-progress for 0008: none).
- Wrapper version 0.4.0 is free: no other open epic releases the wrapper (file-download-in-file-browse
  pins a sha, no release). If one releases first, wrapper-release-0-4-0 and orch-wrapper-pin-0-4-0 are
  amended to the next minor.
- agents-web `openapi/orchestrator.json` is also re-vendored by file-download-in-file-browse task
  web-sync-orchestrator-api; whichever lands second re-runs `npm run sync:api -- orchestrator`.

## Open questions

- Q1: Release any-mcp-tatara-plugins v0.2.0 after plugin-session-send-slash merges and bump the orchestrator's plugins pin (ORCH_ANY_MCP_PLUGINS_REF default, the any-mcp-tatara-orchestrator dev dependency, README, tests) to v0.2.0, as two small tasks added at the gate, so superleaders actually see the new session_send description? Without them the description change stays unreleased. [recommended: yes, add both tasks; the helmfile value ORCH_ANY_MCP_PLUGINS_REF stays with the gate's deploy decision]

## Irreversible operations in scope

- Tag `v0.4.0` pushed to claude-code-wrapper origin (release.yaml retags `:0.4.0` and `:latest`):
  covered by the gate approval of this plan; run by the orchestrator session after the `main` build of
  the merge commit is green (task wrapper-release-0-4-0).
- Tag `v0.2.0` pushed to any-mcp-tatara-plugins origin: covered by the gate approval; run by the
  orchestrator session after the plugins PR merged and its CI is green (task plugins-release-0-2-0).
- Migration `0008_slash_messages.sql` (additive columns with defaults, idempotent `IF NOT EXISTS`):
  runs on the next orchestrator deploy, which is decided at the gate.
