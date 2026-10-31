# Immediate message delivery with per-message priority implementation plan

## Agreed rung

Not agreed yet: a draft migrated from the epic's tasks; the plan-writer revises it after the gate.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: wrapper midturn probe

- Status: todo
- Files: `docs/claude-midturn-input.md`, `tests/fixtures/transcripts/midturn-probe.jsonl`, `tests/fixtures/transcripts/midturn-probe-hooks.jsonl`, `tests/fixtures/screens/midturn-dialogs.txt`, `tests/test_transcript_midturn.py`, `MEMORY.md`
- Verify: `uv run pytest tests/test_transcript_midturn.py tests/test_transcript.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "message should get through PTY immediately and let either Claude Code or even agent queue them internally."

Goal G6 (README), verbatim: "how Claude Code 2.1.304 treats input pasted mid-turn is probed on the real binary and recorded before the wrapper relies on it."

Design D11, verbatim: "Task wrapper-midturn-probe runs claude 2.1.304 under a PTY in `/workdir/workdir/.scratchpad/probe-midturn` (existing login, as the slash epic's probes did) and records P1-P12 of the docs brief in `docs/claude-midturn-input.md` of the wrapper, with captured transcript lines as a fixture and a consequences table naming each design decision it confirms or contradicts. A contradiction is a `ticket.py amend` of the named task by the orchestrator before that task starts; nothing downstream guesses."

Design D11 (gate), verbatim: "Gate (interrogate 6, builder Q4, my call): every other task depends on the probe, directly or through its chain; epic-run stops after it, the orchestrator reads the consequences table (rows D2-D7, D9, D10, D13, D14, D17, D18) and amends before any other task starts. P1, P2, P4 and P5 must be observed, never `not run`; P4 also records input combined across a turn end and across an Esc; P6 captures the real dialog footers, their dismissal output and a key that safely clears unsent input with a dialog open; P7 records how long an end-of-turn auto-compaction with queued input takes; the Stop and UserPromptSubmit payloads are captured beside the transcript lines, so wrapper-merge-stop-gate replays both through the Router."

Docs brief (`/workdir/workdir/.scratchpad/immediate-delivery/brief-docs.md`, "Probes only the real binary (2.1.304) can settle"), verbatim:
"P1. Tool-boundary injection: paste plus CR during a long Bash call. Record the transcript line type (`attachment/queued_command` vs `user` with `promptSource`), its position relative to the tool_result, and whether the marker survives verbatim.
P2. Text-only turn: paste while Claude streams with no tool calls. Check whether it waits for the turn end and whether Stop fires for the first turn before the queued one starts, giving two Stops or one. Check `stop_hook_active` and `last_assistant_message` on each.
P3. UserPromptSubmit for P1 and P2: whether it fires, when (at paste or at injection), with which `prompt` and `prompt_id`.
P4. Multiple pastes queued before a boundary: one combined injection or several? Order? One `queued_command` per paste? Do markers interleave?
P5. Esc with queued input: the transcript interrupt line, then the auto-sent queued prompt. Does the wrapper's second ESC (settle) clear or affect it? Does a bare Esc with empty input plus a second Esc open rewind?
P6. Paste plus CR while a permission dialog is visible (default mode, a tool needing approval): does the CR approve? Does the 2.1.299 hold-back apply to pasted text? Does the paste land in the input box or the dialog? Also test an AskUserQuestion dialog and an MCP elicitation.
P7. Paste during auto-compaction and during a queued or running `/compact`: is the message kept, delivered after, or dropped? Does it go before or after `compact_boundary`? Repeat P1 with a running `/compact` from the commands queue.
P8. Paste while a queued slash command is pending (the wrapper's own command queue): which runs first at the turn end, the queued message or the command?
P9. Paste plus CR when the prompt is collapsed (over 800 characters or over 3 lines): CR timing versus collapse rendering, mid-turn. Does `submit_delay` still suffice?
P10. Invisible-character prompt mid-turn: confirm the CR is swallowed and the text stays in the input, which would then corrupt the next paste.
P11. Background-task wake (the MEMORY.md case): a paste while the wrapper thinks it is ready but Claude was woken. Confirm it is the same mechanism as P1.
P12. The `chat:submit` interrupt case implied by `chat:queueSubmit` wording: find any state where plain Enter interrupts instead of queueing (for example just after submit, before the response starts; compare the 2.1.309 send-now bullet)."

Scope (claude-code-wrapper): `docs/claude-midturn-input.md` (new: the probe record), `tests/fixtures/transcripts/midturn-probe.jsonl` (new: the captured real transcript lines), `tests/fixtures/transcripts/midturn-probe-hooks.jsonl` (new: the captured Stop and UserPromptSubmit payloads), `tests/fixtures/screens/midturn-dialogs.txt` (new: the captured dialog screens and their dismissal), `tests/test_transcript_midturn.py` (new: pins over the captured lines), `MEMORY.md` (dated entry).

#### Acceptance conditions

- ac1: the probe record names claude 2.1.304 and has one `### P<n>` section for each of P1 to P12, each with an `Observed:` and a `Consequence:` line (new) [evidence: command:grep -q '2.1.304' docs/claude-midturn-input.md && for p in P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12; do grep -qE "^### $p( |:|$)" docs/claude-midturn-input.md || exit 1; done && test "$(grep -c '^Observed:' docs/claude-midturn-input.md)" -ge 12 && test "$(grep -c '^Consequence:' docs/claude-midturn-input.md)" -ge 12]
- ac2: P1, P2, P4 and P5 were observed on the binary: none of their Observed lines says not run (new) [evidence: command:for p in P1 P2 P4 P5; do awk -v p="$p" '$0 ~ "^### "p"([ :]|$)" {f=1; next} /^##/ {f=0} f' docs/claude-midturn-input.md | grep '^Observed:' | grep -qv 'not run' || exit 1; done]
- ac3: the P4 section records input queued across a turn end and across an Esc combined with the next paste; the P6 section records the dismissal output and a clear key (or none found); the P7 section records the duration of an end-of-turn auto-compaction (new) [evidence: command:sec() { awk -v p="$1" '$0 ~ "^### "p"([ :]|$)" {f=1; next} /^##/ {f=0} f' docs/claude-midturn-input.md; }; sec P4 | grep -qi 'turn end' && sec P4 | grep -qi 'esc' && sec P6 | grep -qi 'dismiss' && sec P6 | grep -qi 'clear' && sec P7 | grep -qi 'auto-compact']
- ac4: the record ends with a `## Design consequences` table with a row for each of D2, D3, D4, D5, D6, D7, D9, D10, D13, D14, D17 and D18, each saying `confirmed` or `contradicted` (new) [evidence: command:grep -q '^## Design consequences' docs/claude-midturn-input.md && for d in D2 D3 D4 D5 D6 D7 D9 D10 D13 D14 D17 D18; do grep -qE "^\| $d .*(confirmed|contradicted)" docs/claude-midturn-input.md || exit 1; done]
- ac5: the fixture holds the real transcript lines captured for P1, P2, P4 and P5, one JSON object per line, with no credential, token or home path in it (new) [evidence: test:tests/test_transcript_midturn.py::test_fixture_lines_are_real_transcript_lines]
- ac6: the hook fixture holds the real Stop payloads of P1, P2, P4 and P5 (with stop_hook_active and last_assistant_message) and the UserPromptSubmit payloads seen, in arrival order, redacted (new) [evidence: test:tests/test_transcript_midturn.py::test_hook_fixture_holds_real_stop_payloads]
- ac7: the dialog screen fixture has a block and a dismissed block for each dialog kind P6 opened, or P6 is recorded unsettled and the fixture is empty (new) [evidence: test:tests/test_transcript_midturn.py::test_dialog_fixture_matches_the_p6_record]
- ac8: every captured line whose prompt carries a pasted `<!-- ccw turn: ... -->` marker yields, through `parse_line`, a `UserPrompt` with that turn marker (new) [evidence: test:tests/test_transcript_midturn.py::test_captured_midturn_prompts_carry_the_turn_marker]
- ac9: MEMORY.md has a dated entry with the headline results and the record's path [evidence: command:grep -q 'docs/claude-midturn-input.md' MEMORY.md]
- ac10: the new and the transcript tests and lint pass [evidence: command:uv run pytest tests/test_transcript_midturn.py tests/test_transcript.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `docs/claude-midturn-input.md`
- `tests/fixtures/transcripts/midturn-probe.jsonl`
- `tests/fixtures/transcripts/midturn-probe-hooks.jsonl`
- `tests/fixtures/screens/midturn-dialogs.txt`
- `tests/test_transcript_midturn.py`
- `MEMORY.md`

#### Interfaces

- `docs/claude-midturn-input.md`: `# Claude Code mid-turn input (probed on 2.1.304, <date>)`, one `### P1` .. `### P12` section each with `Observed:` (what the screen, transcript and hooks showed, with the captured line ids) and `Consequence:` (what the wrapper must do), then `## Design consequences`: a table `| D<n> | confirmed or contradicted | evidence | task to amend |` for D2, D3, D4, D5, D6, D7, D9, D10, D13, D14, D17 and D18 of design.md (D13, D14, D17, D18 rest on the wrapper's 202 shape and refusal codes).
- `### P4` also records input queued across a turn end (settle bound case) and across an Esc combined with the next paste, with the captured line. `### P6` records the real footers, the screen output when each dialog is dismissed, and a key that clears pasted but unsubmitted input while a dialog is open without answering it (or `none found`). `### P7` records how long an end-of-turn auto-compaction with queued input takes.
- `tests/fixtures/transcripts/midturn-probe-hooks.jsonl`: the Stop and UserPromptSubmit hook payloads of P1, P2, P4 and P5, one JSON object per line with `hook_event_name`, in arrival order, redacted like the transcript fixture.
- `tests/fixtures/screens/midturn-dialogs.txt`: the ANSI-stripped screen text of each dialog P6 opened (permission, AskUserQuestion, MCP elicitation), one block per dialog headed `== <kind> ==`, followed by a `== <kind> dismissed ==` block with the screen after dismissal; empty only when P6 is recorded unsettled.
- Every probe paste uses the design D3 format exactly: `<text>\n\n<!-- ccw turn: <turn id> -->\n<!-- ccw merge: <merge id> -->` (ids such as `turn-probe1`, `m-probe1`), written as one bracketed paste, then CR after the wrapper's `boot.submit_delay_seconds` default, so the fixture carries both markers for task wrapper-merge-marker-parse.
- `tests/fixtures/transcripts/midturn-probe.jsonl`: raw transcript lines copied verbatim from the probe session's JSONL (only redaction of credentials and absolute home paths), at least the prompt-bearing lines of P1, P2, P4 and P5 plus the neighbouring tool_result and assistant lines that show the position.

#### Expected outcome

The facts the docs cannot settle (Stop count at a turn end with queued input, injection line shape, UserPromptSubmit, Esc with queued input, dialogs, compaction, collapsed pastes, invisible characters, Enter interrupting) are written down from the real binary, with real transcript lines pinned by tests; the orchestrator can amend wrapper-merge-marker-parse, wrapper-fake-claude-queue, wrapper-paste-hygiene, wrapper-immediate-turn-merge and wrapper-merge-stop-gate from the consequences table before they start.

#### Steps

- Read `src/claude_code_wrapper/pty_proc.py` (`paste_bytes`, `send_prompt`), `src/claude_code_wrapper/transcript.py` (`parse_line`, `_attachment_events`), `tests/test_transcript.py`, the docs brief and the slash epic's probe layout (`/workdir/workdir/.scratchpad/probe-slash`) in one pass.
- Set up a throwaway session under `/workdir/workdir/.scratchpad/probe-midturn` (own `CLAUDE_CONFIG_DIR` copy with the existing login, a work dir, a hooks log for UserPromptSubmit and Stop payloads); drive `claude` 2.1.304 through a PTY with the wrapper's paste format. Run P1 to P12; save raw screens and the transcript per probe there.
- Red: write `tests/test_transcript_midturn.py` (every test named in the acceptance conditions) and run `uv run pytest tests/test_transcript_midturn.py`; expect a failure on the missing fixture.
- Copy the captured lines, hook payloads and dialog screens into the fixtures, write the record and the MEMORY entry; rerun the task's verify; expect all passed. Quote the summary line.
- A probe the environment cannot run (for example no MCP elicitation available) is recorded as `Observed: not run (<reason>)` with the consequence `unsettled`, never guessed; report it back as a question. P1, P2, P4 and P5 may not be `not run`: if one cannot run, stop and report it as a blocker.
- After this task epic-run stops: the orchestrator reads the consequences table and amends every contradicted task before any other task starts (design D11).

#### Notes

- Never copy a credential, token or `/home/...` path into the repo; redact them in the fixture.
- The tests are characterisation pins over real data: the red step is the missing fixture, the green step is the captured lines; the parser itself is not changed here (0.3.3 already reads `queued_command`).
- A contradiction of the design goes into the consequences table and the report; do not change other tasks' code here.
- `docs/claude-midturn-input.md` is new; the wrapper's `docs/` holds `source-analysis.md` for style.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design

### S2: common message turn id

- Status: todo
- Files: `src/agents_common/orchestrator.py`, `src/agents_common/fake_orchestrator.py`, `tests/test_orchestrator_client.py`
- Verify: `uv run pytest tests/test_orchestrator_client.py tests/test_runs.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

Goal G4 (README), verbatim: "Matrix chat messages in a room whose run is in progress are delivered at once, and an answer shared by merged messages is relayed to the room once."

Design D18 (agents-common part), verbatim: "agents-common `Message.turn_id` (new, released 0.5.0, connector pin moved) carries the link; the fake orchestrator can complete one turn for several messages."

Design D14, verbatim: "`messages.status` stays `sent`; "answered" stays derived through `turn_id` (all messages merged into one turn read its `final_text`). agents-common's run tracker reads the linked turn as today."

Scope (agents-common): `src/agents_common/orchestrator.py` (`Message.turn_id`), `src/agents_common/fake_orchestrator.py` (`complete_turn(..., turn_id=None)` and the message view's `turn_id`), `tests/test_orchestrator_client.py`.

#### Acceptance conditions

- ac1: Message parses turn_id from a message view (a string, or null while unlinked) (new) [evidence: test:tests/test_orchestrator_client.py::test_message_turn_id]
- ac2: FakeOrchestrator.complete_turn with an explicit turn_id lets two messages share one turn; get_message returns that turn_id and the same final_text for both (new) [evidence: test:tests/test_orchestrator_client.py::test_fake_completes_one_turn_for_two_messages]
- ac3: the client and runs suites and lint pass [evidence: command:uv run pytest tests/test_orchestrator_client.py tests/test_runs.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_common/orchestrator.py`
- `src/agents_common/fake_orchestrator.py`
- `tests/test_orchestrator_client.py`

#### Interfaces

- `agents_common.orchestrator.Message.turn_id: str | None = None` (the orchestrator's `MessageView.turn_id`, already served).
- `FakeOrchestrator.complete_turn(message_id: int, final_text: str, turn_id: str | None = None) -> None`: without `turn_id` it allocates one per call as today; the fake's message view includes `turn_id`.

#### Expected outcome

Consumers of agents-common (the Matrix connector first) can tell when two messages were answered by one merged turn.

#### Steps

- Read `src/agents_common/orchestrator.py`, `src/agents_common/fake_orchestrator.py`, `tests/test_orchestrator_client.py` and `tests/test_runs.py` in one pass.
- Red: add the two tests; run `uv run pytest tests/test_orchestrator_client.py`; expect them to fail.
- Green: add the field and the fake parameter; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- `_Model` ignores extra keys, so the field is purely additive for consumers.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: depends_on wrapper-midturn-probe so the probe gates every root task (interrogate 6; frontmatter edited directly, amend cannot change it)

- 2026-10-29 amended: agents-common renumbered 0.4.0 -> 0.5.0: the slash fix round takes v0.4.0 (mx-34 #446, #453)

### S3: orch priority column

- Status: todo
- Files: `src/agents_orchestrator/db/migrations/0014_message_priority.sql`, `src/agents_orchestrator/db/queue.py`, `src/agents_orchestrator/db/views.py`, `src/agents_orchestrator/api/schemas.py`, `src/agents_orchestrator/api/messages.py`, `openapi.json`, `tests/test_api_messages.py`, `tests/test_migrations.py`
- Verify: `uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint`
- Verified head: none

#### Requirement

User scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Goal G2 (README), verbatim: "each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool."

Design D1 (orchestrator part), verbatim: "Every message route takes an optional `priority`: `"immediate"` (the default) or `"idle"`. Routes: orchestrator `POST /api/sessions/{id}/messages` (`schemas.PostMessage`), the agent route `POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:SessionMessageIn`), `MessageView.priority`, [...]"

Design D12, verbatim: "Migration `0014_message_priority.sql` (the next free number after session-orchestration-mcp's 0013, which follows slash's 0012 and hive-decoupling's 0011): `ALTER TABLE messages ADD COLUMN IF NOT EXISTS priority text NOT NULL DEFAULT 'idle' CHECK (priority IN ('immediate', 'idle'))`, then `ALTER TABLE messages ALTER COLUMN priority SET DEFAULT 'immediate'`. Existing rows take `idle`, new rows default to `immediate` (my call, Q11). The api writes it once at insert (`enqueue_message(priority=)`); `MessageView` and `views._MESSAGE_SELECT` expose it."

Design D8, verbatim: "`kind = 'command'` messages keep the slash epic's path (D9 run at the Stop, D10 dispatch); their `priority` is stored as sent and ignored (Q4)."

Scope (agents-orchestrator): `src/agents_orchestrator/db/migrations/0014_message_priority.sql` (new), `db/queue.py` (`enqueue_message(..., priority="immediate")`), `db/views.py` (`_MESSAGE_SELECT` reads `m.priority`), `api/schemas.py` (`MessagePriority`, `PostMessage.priority`, `MessageView.priority`), `api/messages.py` (passes it through), `openapi.json` (regenerated), `tests/test_api_messages.py`, `tests/test_migrations.py`. Test no longer accurate (named): `tests/test_migrations.py::test_fresh_database_gets_all_tables` and `test_presets_migration_on_existing_sessions` list every applied migration and gain `0014`.

#### Acceptance conditions

- ac1: (CI or a Docker host) migration 0014 adds messages.priority: rows that existed before it read idle, a new row without priority reads immediate, any other value violates the CHECK, and a rerun is a no-op (new) [evidence: test:tests/test_migrations.py::test_message_priority_column]
- ac2: (CI or a Docker host) the migration lists of the fresh and existing-database tests include 0014 (updated, named) [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- ac3: (CI or a Docker host) POST /api/v1/sessions/{id}/messages stores priority (immediate by default, idle when sent), GET of the message and the session list return it, and an unknown value answers 422 (new) [evidence: test:tests/test_api_messages.py::test_post_message_priority]
- ac4: PostMessage defaults to immediate, accepts idle, refuses other values, and MessageView carries priority [evidence: command:uv run --frozen python -c "from agents_orchestrator.api.schemas import PostMessage, MessageView; assert PostMessage(text='x').priority == 'immediate'; assert PostMessage(text='x', priority='idle').priority == 'idle'; assert 'priority' in MessageView.model_fields" && ! uv run --frozen python -c "from agents_orchestrator.api.schemas import PostMessage; PostMessage(text='x', priority='soon')" 2>/dev/null]
- ac5: openapi.json is regenerated from the app and carries the field [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac6: Docker-free suites and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

#### Files

- `src/agents_orchestrator/db/migrations/0014_message_priority.sql`
- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/db/views.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/messages.py`
- `openapi.json`
- `tests/test_api_messages.py`
- `tests/test_migrations.py`

#### Interfaces

- `0014_message_priority.sql`: the two ALTER statements of D12, idempotent, with a header comment in the style of 0010.
- `api/schemas.py`: `MessagePriority = Literal["immediate", "idle"]`; `PostMessage.priority: MessagePriority = "immediate"`; `MessageView.priority: MessagePriority`.
- `db/queue.py:enqueue_message(conn, session_id, text, target_agent_id=None, *, kind="turn", sender_session_id=None, sender_slug=None, hop=0, priority: str = "immediate") -> int`.
- No dispatch change here (task orch-dispatch-immediate).

#### Expected outcome

Every stored message carries a priority the dispatcher can act on; messages queued before the deploy keep today's wait-until-idle meaning.

#### Steps

- Read `db/migrations/0010_slash_messages.sql` and the `0011_*.sql` to `0013_*.sql` migrations of hive-decoupling, slash and session-orchestration-mcp, `db/migrate.py`, `db/queue.py:enqueue_message`, `db/views.py`, `api/schemas.py`, `api/messages.py`, `tests/test_migrations.py` and `tests/test_api_messages.py` in one pass.
- Red: add `test_message_priority_column`, `test_post_message_priority`, the 0014 entries and run `uv run --frozen python -c` of ac4; expect ac4 to fail here (the DB tests fail in CI until green).
- Green: write the migration, the schema fields, the insert and select; regenerate `openapi.json` with `uv run python -m agents_orchestrator.api.openapi > openapi.json`; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- Take the next free migration number at build time: if 0014 is taken, use the next one and report it so the orchestrator amends `files`.
- Commands keep `priority` as sent; nothing here interprets it.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: ac4 command simplified (two python -c calls instead of exec)

- 2026-10-29 amended: depends_on wrapper-midturn-probe so the probe gates every root task (interrogate 6; frontmatter edited directly, amend cannot change it)

- 2026-10-29 amended: migration renumbered 0012 to 0014 (mx-34 #469/#470): it lands after session-orchestration-mcp's 0013 on top of slash's 0012

### S4: orch wrapper client priority

- Status: todo
- Files: `src/agents_orchestrator/wrapper/client.py`, `src/agents_orchestrator/wrapper/models.py`, `tests/fakes/fake_wrapper.py`, `tests/test_wrapper_client.py`, `tests/test_fake_wrapper_contract.py`
- Verify: `uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint`
- Verified head: none

#### Requirement

Design D3 (response), verbatim: "The wrapper answers 202 `{turn_id: <running turn id>, state: "running", merged: true, merge_id}`."

Design D4 (codes), verbatim: "an `immediate` message is refused, and nothing is pasted, when: the turn is in its command phase or a slash command is running or queued for the Stop (409 `command_active`); the slash epic's `DialogScanner` patterns match the current screen (409 `dialog_open`); an interrupt of the turn is in flight (409 `interrupting`); the turn already holds `sessions.merge.max_unconfirmed` unconfirmed pastes (default 4) or `sessions.merge.max_per_turn` merged pastes (default 32) (429 `merge_queue_full`) [...] `idle` while busy stays 409 `busy`; booting and dead stay 503."

Design D13 (client part), verbatim: "`loop._send` sends `priority`; 202 `merged` or not is `mark_sent` with the returned turn id; a 409 other than booting|dead (`busy`, `command_active`, `dialog_open`, `interrupting`) and 429 `merge_queue_full` requeue with `not_before = now() + retry_backoff_base_seconds`, no attempt counted, no reservation to release (my call: an immediate requeue would spin against a busy wrapper)."

Design D14 (model part), verbatim: "The orchestrator's `TurnRecord` model gains `merged`."

Scope (agents-orchestrator): `wrapper/client.py` (`submit_turn(..., priority=None)`, 429 on a turn send maps to `Busy`), `wrapper/models.py` (`TurnAccepted.merged`, `TurnRecord.merged`), `tests/fakes/fake_wrapper.py` (mirrors the wrapper's merge leg, refusals and cap), `tests/test_wrapper_client.py`, `tests/test_fake_wrapper_contract.py` (the merge case, fake leg; the real leg is enabled by orch-wrapper-pin-0-5-0).

#### Acceptance conditions

- ac1: submit_turn sends priority in the body when given and none when not; a 202 parses TurnAccepted with turn_id and merged (false when the field is absent) (new) [evidence: test:tests/test_wrapper_client.py::test_submit_turn_sends_priority_and_parses_merged]
- ac2: a turn send answered 409 busy, command_active, dialog_open or interrupting, or 429 merge_queue_full, maps to Busy with the wrapper's code; 409 booting and dead keep their mapping (new) [evidence: test:tests/test_wrapper_client.py::test_submit_turn_refusal_codes]
- ac3: TurnRecord parses merged entries (merge_id, metadata, absorbed_at) and defaults to an empty list (new) [evidence: test:tests/test_wrapper_client.py::test_turn_record_parses_merged]
- ac4: the fake wrapper merges an immediate turn into a running one (same turn id, merged true, the record lists the merge), answers 409 busy to idle while busy and 429 merge_queue_full past the cap (fake leg) (new) [evidence: command:uv run --frozen pytest "tests/test_fake_wrapper_contract.py::test_immediate_while_busy_merges[fake]"]
- ac5: targeted suites and lint pass [evidence: command:uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint]

#### Files

- `src/agents_orchestrator/wrapper/client.py`
- `src/agents_orchestrator/wrapper/models.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_wrapper_client.py`
- `tests/test_fake_wrapper_contract.py`

#### Interfaces

- `WrapperClient.submit_turn(session_id: str, text: str, metadata: dict | None = None, priority: str | None = None) -> SubmitOutcome`; body `{"text", "metadata"?, "priority"?}`.
- `wrapper/models.py`: `TurnAccepted(turn_id: str, merged: bool = False)`; `MergedPrompt(_Model)` with `merge_id`, `origin`, `metadata`, `pasted_at`, `absorbed_at`; `TurnRecord.merged: list[MergedPrompt] = []`.
- `tests/fakes/fake_wrapper.py`: the same request field, response and refusal codes as the wrapper's D4 (`merge_queue_full` cap 4 unconfirmed; the fake can mark merges absorbed on demand).

#### Expected outcome

The orchestrator can ask the wrapper for immediate or idle delivery and understands a merged answer and every refusal, and its fake wrapper behaves like the real one.

#### Steps

- Read `wrapper/client.py` (`_send`, `submit_turn`, `_map_refusal`), `wrapper/models.py`, `tests/fakes/fake_wrapper.py`, `tests/test_wrapper_client.py`, `tests/test_fake_wrapper_contract.py` and the wrapper task wrapper-immediate-turn-merge's Interfaces in one pass.
- Red: add the tests named ac1 to ac4 (the contract case parametrised like the others; mark its real leg skipped with a reason naming orch-wrapper-pin-0-5-0); run `uv run --frozen pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m "not integration"`; expect them to fail.
- Green: implement the client, models and fake; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- The real contract leg runs against the pinned wrapper image (0.4.1 until orch-wrapper-pin-0-5-0), which refuses an unknown `priority` field; the merge case's real leg is skipped until that task removes the skip.
- `command()` keeps its own 429 mapping; only the turn send changes.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: depends_on wrapper-midturn-probe so the probe gates every root task (interrogate 6; frontmatter edited directly, amend cannot change it)

### S5: plugin session send priority

- Status: todo
- Files: `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`, `orchestration/orchestrator/tests/test_orchestrator_plugin.py`, `orchestration/orchestrator/README.md`
- Verify: `uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py && mise run lint`
- Verified head: none

#### Requirement

Goal G2 (README), verbatim: "each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool."

Design D15, verbatim: "any-mcp-tatara-plugins `session_send` gains `priority` (enum `immediate`, `idle`, default `immediate`) and its description says: a message to a busy leader joins its running turn at once and shares that turn's answer; `idle` waits until the leader is idle. The `chat_send` description's "chat-started turn" rule extends to a turn a chat message joined. Released as plugins 0.7.0 on top of session-orchestration-mcp's 0.6.0; the orchestrator pins it."

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py` (`session_send` schema and description, `chat_send` description), `orchestration/orchestrator/tests/test_orchestrator_plugin.py`, `orchestration/orchestrator/README.md` (tool table).

#### Acceptance conditions

- ac1: the session_send input schema has priority, a string enum of immediate and idle, not required, and a call with priority idle posts it in the body to /sessions/{slug}/messages (new) [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_session_send_priority]
- ac2: the session_send description says a message to a busy leader joins its running turn at once and shares its answer, and that idle waits until the leader is idle; the slash command sentence stays (updated) [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_descriptions_from_config]
- ac3: the chat_send description counts a turn a chat message joined as chat-started (updated) [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_descriptions]
- ac4: the plugin README's tool table names the priority parameter [evidence: command:grep -q 'priority' orchestration/orchestrator/README.md]
- ac5: the plugin tests and lint pass [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py && mise run lint]

#### Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- `orchestration/orchestrator/README.md`

#### Interfaces

- `spec("session_send", "POST", "/sessions/{slug}/messages", _schema({"slug": ..., "text": ..., "priority": {"type": "string", "enum": ["immediate", "idle"], "description": ...}}, ["slug", "text"]), "*")`.
- `_descriptions()["session_send"]` and `["chat_send"]`: wording within D15; the existing slash-command sentence of the slash epic stays.

#### Expected outcome

A superleader sees that its messages reach a busy leader at once by default, can ask for idle delivery, and knows a chat message that joined a turn makes that turn's answer reach the chat.

#### Steps

- Read the plugin `__init__.py` (`_descriptions`, the tool specs), `tests/test_orchestrator_plugin.py` and the plugin README in one pass.
- Red: add `test_session_send_priority` and extend the two description tests; run `uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py`; expect them to fail.
- Green: change the schema and descriptions, README; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- `test_lists_fifteen_tools` (or the count the hive-decoupling epic left) must stay accurate: no new tool here.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: depends_on wrapper-midturn-probe so the probe gates every root task (interrogate 6; frontmatter edited directly, amend cannot change it)

- 2026-10-29 amended: D15 quote follows the design: plugins 0.7.0 on top of 0.6.0 (mx-34 #469/#470)

### S6: wrapper fake claude queue

- Status: todo
- Files: `tests/fake_claude/fake_claude.py`, `tests/test_fake_claude_queue.py`, `tests/conftest.py`
- Verify: `uv run pytest tests/test_fake_claude_queue.py tests/test_fake_claude.py tests/test_fake_claude_commands.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

Design D10, verbatim: "Scenario key `"midturn_input": "queue"` (default `"drop"`, today's behaviour). With `queue`, a paste plus CR arriving while a turn runs is queued; it is written and handed to the turn at the next tool boundary, and input still queued at the turn end is sent as the next prompt, in the shapes and order the probe recorded (P1-P5). Every input is still logged in `fake-inputs.jsonl` with state `busy`."

Cartographer brief (Plan inputs, fix as acceptance criteria), verbatim: "The fake claude models absorption (`queued_command` line) instead of dropping busy input. That is the fake-claude task, which alone may edit `tests/conftest.py`."

Design Constraints, verbatim: "only wrapper-fake-claude-queue edits `tests/conftest.py`."

Scope (claude-code-wrapper): `tests/fake_claude/fake_claude.py` (the queue mode and its docstring), `tests/test_fake_claude_queue.py` (new), `tests/conftest.py` (only if a fixture helper for queue-mode scenarios is needed).

#### Acceptance conditions

- ac1: in queue mode a paste plus CR during a tool step is written, after that tool's result line, in the shape P1 recorded (a `queued_command` attachment carrying the full prompt, unless the probe recorded otherwise), and the turn goes on to one Stop whose `last_assistant_message` is the text after the injection (new) [evidence: test:tests/test_fake_claude_queue.py::test_paste_during_tool_is_injected_at_the_tool_boundary]
- ac2: in queue mode input still queued when the turn's steps end goes out as the next prompt in the shape and Stop order P2 recorded (new) [evidence: test:tests/test_fake_claude_queue.py::test_input_queued_at_turn_end_goes_out_after_the_turn]
- ac3: two pastes queued before one boundary are handed over as P4 recorded, in paste order, each keeping its own markers (new) [evidence: test:tests/test_fake_claude_queue.py::test_two_queued_pastes_keep_their_order]
- ac4: ESC with queued input writes the interrupt line and then does with the queued input what P5 recorded (new) [evidence: test:tests/test_fake_claude_queue.py::test_esc_with_queued_input_follows_the_probe]
- ac5: UserPromptSubmit fires for an injected prompt exactly as P3 recorded (new) [evidence: test:tests/test_fake_claude_queue.py::test_user_prompt_submit_for_injected_prompt_matches_probe]
- ac6: every input arriving in queue mode while a turn runs is logged in fake-inputs.jsonl with state busy (new) [evidence: test:tests/test_fake_claude_queue.py::test_queued_input_logged_busy]
- ac7: without the key, input while busy is still recorded busy and dropped, and ESC is still not recorded (unchanged pins) [evidence: command:uv run pytest tests/test_fake_claude_commands.py::test_input_while_busy_recorded tests/test_fake_claude_commands.py::test_esc_not_recorded_as_busy]
- ac8: the fake's module docstring documents `midturn_input` and both values [evidence: command:grep -q 'midturn_input' tests/fake_claude/fake_claude.py && grep -q '"queue"' tests/fake_claude/fake_claude.py]
- ac9: the fake claude suites and lint pass [evidence: command:uv run pytest tests/test_fake_claude_queue.py tests/test_fake_claude.py tests/test_fake_claude_commands.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `tests/fake_claude/fake_claude.py`
- `tests/test_fake_claude_queue.py`
- `tests/conftest.py`

#### Interfaces

- Scenario JSON, top level: `"midturn_input": "drop" | "queue"` (absent = `"drop"`). `queue` changes only what happens to a paste plus CR that arrives while a turn's steps run (between steps, during `sleep` and tool steps); command handling, ESC interrupts and the idle path are unchanged.
- Queue mode output follows `docs/claude-midturn-input.md` (task wrapper-midturn-probe): the injected line's JSON shape (copy the captured fixture's keys, for example `{"type": "attachment", "attachment": {"type": "queued_command", "prompt": ..., "commandMode": "prompt", ...}}`), its position (after the running tool's result), the turn-end behaviour (one Stop or two), the hook behaviour, the ESC behaviour.
- `fake-inputs.jsonl` row for queued input: `{"text", "state": "busy", "ts"}` as today.

#### Expected outcome

Wrapper tests can opt into a fake claude that behaves like Claude Code 2.1.304 when text is pasted mid-turn, so the merge tasks can be tested end to end; every existing test keeps today's drop behaviour.

#### Steps

- Read `tests/fake_claude/fake_claude.py` (run loop, `interrupted`, `run_steps`, `run_turn`, `stop_cycle`), `tests/test_fake_claude.py`, `tests/test_fake_claude_commands.py`, `tests/conftest.py`, `docs/claude-midturn-input.md` and `tests/fixtures/transcripts/midturn-probe.jsonl` in one pass.
- Red: write `tests/test_fake_claude_queue.py` with every test named in the acceptance conditions; run `uv run pytest tests/test_fake_claude_queue.py`; expect them to fail (input dropped).
- Green: add the queue mode to the fake (parse the paste and CR inside `interrupted()` instead of dropping, keep a queue, flush it at the next tool boundary and at the turn end per the probe), document the key in the docstring; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- Ruling (D10): opt-in only. The existing pins (`test_input_while_busy_recorded`, `test_esc_not_recorded_as_busy`, `tests/test_command_turn_resume.py` "typed while idle") prove the wrapper never types into a running turn for commands; they stay accurate and unchanged.
- Where the probe record says `unsettled` for a case, model the docs brief's documented behaviour (A2: injected at the tool boundary within the turn, still-queued input sent after the turn) and name the case in the report.
- The fake is stdlib only and must keep working for every existing scenario.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S7: wrapper merge marker parse

- Status: todo
- Files: `src/claude_code_wrapper/transcript.py`, `src/claude_code_wrapper/turns.py`, `tests/test_transcript.py`, `tests/test_transcript_midturn.py`, `tests/test_turns.py`
- Verify: `uv run pytest tests/test_transcript.py tests/test_transcript_midturn.py tests/test_transcript_commands.py tests/test_turns.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

Goal G3 (README), verbatim: "a message delivered mid-turn never wedges the session: the running turn still ends on its Stop, and the message is linked to the turn that answered it (hop guard and delivery verifier included)."

Design D5 (the record model and the parser part), verbatim: "`TurnRecord.merged: list[MergedPrompt]`, `MergedPrompt {merge_id, origin, metadata, callback_url, pasted_at, absorbed_at}` (persisted with the record, served by `GET /turns/{id}`). The transcript parser reads every `<!-- ccw merge: <id> -->` into `UserPrompt.merge_markers: list[str]` from every prompt-bearing line: a `user` line, a `queued_command` attachment (wrapper 0.3.3) and a `user` line with `promptSource: "queued"` (docs A10, issue 92478); the probe records which ones 2.1.304 writes. `UserPrompt.turn_marker` is the last turn marker of the text, not the first (interrogate 4): a merge left queued after the settle bound or an interrupt and combined with the next turn's paste must not name the old turn, or the new turn's Stop is dropped as stale (the 0.3.3 wedge). The router sets `absorbed_at` once (first sighting) for each listed merge of the running turn, ignores merge ids of any other turn, and emits `turn_merge_absorbed`. A merge marker never moves `_last_marker` by itself: the turn marker on the same line names the running turn."

Design D3 (the paste format), verbatim: "`<text>\n\n<!-- ccw turn: <running turn id> -->\n<!-- ccw merge: <merge id> -->`"

Scope (claude-code-wrapper): `src/claude_code_wrapper/transcript.py` (`_MERGE_MARKER`, `UserPrompt.merge_markers`, the last-turn-marker rule, read in `_prompt_events` for every prompt-bearing line), `src/claude_code_wrapper/turns.py` (`MergedPrompt`, `TurnRecord.merged`, persisted and reloaded), `tests/test_transcript.py`, `tests/test_transcript_midturn.py` (assertions over the probe's captured lines), `tests/test_turns.py`. Test no longer accurate (named): `tests/test_turns.py::test_turn_record_serializes_callback_url_camel_case` asserts the exact dumped field set of `TurnRecord`; it gains `merged`, and this file is changed only for that and the new model test. The router is not touched here (task wrapper-immediate-turn-merge).

#### Acceptance conditions

- ac1: a user line whose text ends with the D3 turn and merge markers yields one UserPrompt with turn_marker and merge_markers set (new) [evidence: test:tests/test_transcript.py::test_merge_marker_read_from_user_line]
- ac2: a queued_command attachment whose prompt carries both markers yields both (new) [evidence: test:tests/test_transcript.py::test_merge_marker_read_from_queued_command_attachment]
- ac3: a user line with promptSource queued carrying both markers yields both (new) [evidence: test:tests/test_transcript.py::test_merge_marker_read_from_queued_user_line]
- ac4: a combined prompt holding an older turn's merge (turn marker T1, merge marker m1) followed by a new turn's paste (turn marker T2) yields turn_marker T2 and merge_markers [m1]; two merges of one turn in one prompt yield both ids in text order (new) [evidence: test:tests/test_transcript.py::test_combined_prompt_takes_the_last_turn_marker_and_every_merge_marker]
- ac5: a prompt with a turn marker and no merge marker yields merge_markers empty; the 0.3.3 attachment pin is unchanged [evidence: test:tests/test_transcript.py::test_queued_command_attachment_yields_the_user_prompt_event]
- ac6: every captured probe line that carries merge markers yields all of them, with the last turn marker of the same line (new) [evidence: test:tests/test_transcript_midturn.py::test_captured_midturn_prompts_carry_the_merge_marker]
- ac7: TurnRecord.merged defaults to an empty list, MergedPrompt serialises callbackUrl in camelCase, and a record with merges survives TurnStore put and reload (new) [evidence: test:tests/test_turns.py::test_turn_record_merged_persists_and_reloads]
- ac8: the TurnRecord field-set pin lists merged (no longer accurate: it pins the exact field set) [evidence: test:tests/test_turns.py::test_turn_record_serializes_callback_url_camel_case]
- ac9: the transcript and turn suites and lint pass [evidence: command:uv run pytest tests/test_transcript.py tests/test_transcript_midturn.py tests/test_transcript_commands.py tests/test_turns.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/transcript.py`
- `src/claude_code_wrapper/turns.py`
- `tests/test_transcript.py`
- `tests/test_transcript_midturn.py`
- `tests/test_turns.py`

#### Interfaces

- `transcript.py`: `_MERGE_MARKER = re.compile(r"<!--\s*ccw merge:\s*(\S+?)\s*-->")`; `UserPrompt.merge_markers: list[str] = []` (every merge marker, in text order, via `findall`), filled wherever `turn_marker` is filled today (`_prompt_events`), so user lines, `queued_command` attachments and queued user lines all carry it. `UserPrompt.turn_marker` becomes the last `_TURN_MARKER` match of the text instead of the first.
- `turns.py`: `MergedPrompt(BaseModel)`: `merge_id: str`, `origin: Origin`, `metadata: dict`, `callback_url: str | None` (alias `callbackUrl`, serialised camelCase like `TurnRecord.callback_url`), `pasted_at: str`, `absorbed_at: str | None = None`; `TurnRecord.merged: list[MergedPrompt] = []`, persisted by `TurnStore` and reloaded.
- Consumer (task wrapper-immediate-turn-merge): `Router._on_transcript_events` reads `ev.merge_markers`; this task does not touch the router.

#### Expected outcome

The wrapper can tell which merged pastes Claude Code took, from any line shape 2.1.304 writes for it, a combined prompt never names a stale turn, and the turn record can carry its merges.

#### Steps

- Read `src/claude_code_wrapper/transcript.py`, `src/claude_code_wrapper/turns.py`, `tests/test_transcript.py`, `tests/test_transcript_midturn.py`, `tests/test_turns.py`, `tests/fixtures/transcripts/midturn-probe.jsonl` and `docs/claude-midturn-input.md` (P1, P2, P4) in one pass.
- Red: add the new tests named in the acceptance conditions and add `"merged"` to the field set of `tests/test_turns.py::test_turn_record_serializes_callback_url_camel_case`; run `uv run pytest tests/test_transcript.py tests/test_transcript_midturn.py tests/test_turns.py`; expect the new tests and the field-set pin to fail.
- Green: add the regex, the list field, the last-marker rule and the model; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- The `promptSource: "queued"` user line already reaches `_user_events`; check that its prompt text path reaches `_prompt_events` (issue 92478 shape: `{"type": "user", "promptSource": "queued", "message": {"content": ...}}`), and use the probe's captured shape where it differs.
- Redaction keeps applying to the text as today; markers are read from the unredacted text as `turn_marker` is.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design

### S8: wrapper paste hygiene

- Status: todo
- Files: `src/claude_code_wrapper/pty_proc.py`, `tests/test_pty_proc.py`, `README.md`
- Verify: `uv run pytest tests/test_pty_proc.py --deselect tests/test_pty_proc.py::test_exit_without_eof_still_fires --deselect tests/test_pty_proc.py::test_close_terminates_group_then_kill && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

Design D9, verbatim: "`paste_bytes` removes Unicode tag characters (U+E0000-U+E007F), bidi controls (U+202A-U+202E, U+2066-U+2069) and zero-width spaces (U+200B, U+FEFF) besides ESC, keeping ZWJ and ZWNJ (U+200C, U+200D) and variation selectors. Claude Code removes them itself on Enter, and then "that Enter sends nothing" and the cleaned prompt stays in the input box (docs G3); mid-turn, the next merged paste would be concatenated onto it. Applies to every paste, idle turns included."

Docs brief (Fix-as-AC), verbatim: "Strip invisible Unicode (tag chars, bidi controls, zero-width spaces; keep ZWJ/ZWNJ for Persian/Indic and emoji selectors) before pasting. Otherwise the CR submits nothing and text is left in the input (G3). This applies to idle turns too."

Scope (claude-code-wrapper): `src/claude_code_wrapper/pty_proc.py` (`paste_bytes`), `tests/test_pty_proc.py`, `README.md` (one sentence where turns and pastes are described).

#### Acceptance conditions

- ac1: paste_bytes removes every tag character U+E0000-U+E007F, the bidi controls U+202A-U+202E and U+2066-U+2069, U+200B and U+FEFF, and ESC, inside the bracketed paste (new) [evidence: test:tests/test_pty_proc.py::test_paste_bytes_strips_invisible_characters]
- ac2: paste_bytes keeps U+200C, U+200D, variation selectors U+FE00-U+FE0F, an emoji ZWJ sequence, Persian text with ZWNJ and plain text byte for byte (new) [evidence: test:tests/test_pty_proc.py::test_paste_bytes_keeps_joiners_and_variation_selectors]
- ac3: the README says which invisible characters are removed from every pasted prompt and why [evidence: command:grep -q 'U+200B' README.md && grep -q 'U+E0000' README.md]
- ac4: the PTY suite (minus the two PID-1 tests that fail in this container) and lint pass [evidence: command:uv run pytest tests/test_pty_proc.py --deselect tests/test_pty_proc.py::test_exit_without_eof_still_fires --deselect tests/test_pty_proc.py::test_close_terminates_group_then_kill && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/pty_proc.py`
- `tests/test_pty_proc.py`
- `README.md`

#### Interfaces

- `pty_proc.paste_bytes(text: str) -> bytes`: unchanged signature; the removed set is a module constant (for example `INVISIBLE = re.compile("[​﻿‪-‮⁦-⁩\U000e0000-\U000e007f]")`) applied with the ESC removal before encoding.
- Every writer that pastes (`send_prompt`, `paste`, probes, continue prompts, merges) goes through `paste_bytes`, so no caller changes.

#### Expected outcome

A prompt or message carrying a stray invisible character is submitted by the first CR instead of being left in Claude Code's input box, where it would corrupt the next pasted message.

#### Steps

- Read `src/claude_code_wrapper/pty_proc.py`, `tests/test_pty_proc.py`, the README section on turns and `docs/claude-midturn-input.md` (P10) in one pass.
- Red: add the two tests named in the acceptance conditions; run `uv run pytest tests/test_pty_proc.py -k paste_bytes`; expect ac1 to fail.
- Green: extend `paste_bytes` and add the README sentence; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- If the probe's P10 recorded that 2.1.304 does not swallow the CR, the stripping still stands (harmless, design D9); say so in the report.
- Keep U+200C and U+200D: they are needed by Persian and Indic text and emoji sequences.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S9: common release 0.5.0

- Status: todo
- Files: `pyproject.toml`, `uv.lock`, `tests/test_release.py`, `README.md`
- Verify: `uv run pytest tests/test_release.py tests/test_package.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.7.0 and agents-common 0.5.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer). [...] the connector pins agents-common v0.5.0."

Scope (agents-common): `pyproject.toml` (0.4.0 to 0.5.0), `uv.lock`, `tests/test_release.py` (the version and install pins), `README.md` (install line).

#### Acceptance conditions

- ac1: pyproject, installed metadata and __version__ agree on 0.5.0 (updated, named) [evidence: test:tests/test_release.py::test_versions_agree]
- ac2: the README install line and the release test pin v0.5.0 and no older tag [evidence: command:grep -q 'agents-common@v0.5.0' README.md && ! grep -q 'agents-common@v0.4.0' README.md && grep -q 'agents-common@v0.5.0' tests/test_release.py]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.5.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.5.0)"]
- ac4: release and package tests and lint pass [evidence: command:uv run pytest tests/test_release.py tests/test_package.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `tests/test_release.py`
- `README.md`

#### Interfaces

- `[project].version = "0.5.0"`; `tests/test_release.py` `INSTALL` and the asserted version move to 0.5.0.

#### Expected outcome

A tagged agents-common release with `Message.turn_id` exists for the Matrix connector to pin.

#### Steps

- Read `pyproject.toml`, `README.md`, `tests/test_release.py` and `tests/test_package.py` in one pass.
- Bump the version, run `uv lock`, update the two pins in `tests/test_release.py` (no longer accurate after the bump) and the README install line; version bump with no behaviour change (TDD exception), so no red step.
- Run the task's verify; expect all passed. Quote the summary line.

#### Notes

- The tag is pushed by the orchestrator session after the PR merges green; ac3 is checked by it.
- If the README has no install line with the tag, add one next to the existing usage section rather than inventing a new section.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
- Renumbered 0.4.0 to 0.5.0 (2026-10-29): the slash-commands-from-chat fix round takes agents-common v0.4.0 (run tracker command outcomes; user and mx-34 confirmed, #446). Build on v0.4.0; propose the exact tag through mx-34 before tagging (rule #396).

- 2026-10-29 amended: D19 quote follows the design: plugins 0.7.0 (mx-34 #469/#470)

### S10: orch dispatch immediate

- Status: todo
- Files: `src/agents_orchestrator/db/queue.py`, `src/agents_orchestrator/dispatcher/loop.py`, `tests/test_dispatcher.py`, `tests/test_queue_leader_routing.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint`
- Verified head: none

#### Requirement

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "currently the messages wait for too long. [...] message should get through PTY immediately and let either Claude Code or even agent queue them internally." Scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Goals G1 and G5 (README), verbatim: "a message sent to a busy session reaches its leader through the PTY at once, mid-turn, and Claude Code queues it internally; by default no message waits for the leader to go idle." "slash commands keep running at the turn's Stop whatever the priority, and nothing is pasted while a command runs or a dialog is open."

Design D13, verbatim: "In `_claim_in_session`, a `priority = 'immediate'` head picks with `_PICK_IMMEDIATE`: the target or the leader, `ready`, not gone, with a wrapper session, any state; no `state = 'idle'` and no `free_since` predicate. The claim writes the `agents.last_dispatched_at` reservation exactly as an idle claim does (interrogate 2): an immediate message that starts a turn on an idle agent would otherwise leave the agent pickable by `_PICK` until the ingester flips its state, and the next idle message would be dispatched, refused 409 and requeued every poll; on a busy agent the reservation is harmless (the turn's end moves `free_since` past it). It is exempt from the busy-leader hold, so it overtakes older queued `idle` messages of its session (Q5), and it still waits for backoff (`not_before`), the handover hold (`_handover_pending`, so it reaches the successor leader) and a gone leader. Order: an immediate message is not claimed while an older message of its session is `dispatching` (the slash D10 per-session order rule), nor while an older `immediate` message of its session on the same route (untargeted, or the same target) is still queued, for example in backoff (interrogate 3), so pastes reach the wrapper in id order. `loop._send` sends `priority`; 202 `merged` or not is `mark_sent` with the returned turn id; a 409 other than booting|dead (`busy`, `command_active`, `dialog_open`, `interrupting`) and 429 `merge_queue_full` release the reservation (`release_agent`, as every non-accept does today) and requeue with `not_before = now() + retry_backoff_base_seconds`, no attempt counted (my call: an immediate requeue would spin against a busy wrapper). `idle` messages keep today's path exactly."

Design D8, verbatim: "`kind = 'command'` messages keep the slash epic's path (D9 run at the Stop, D10 dispatch); their `priority` is stored as sent and ignored (Q4)."

Scope (agents-orchestrator): `db/queue.py` (`Claim.priority`, `_PICK_IMMEDIATE`, the immediate leg of `_claim_in_session` with the older-immediate hold, `_dispatch` writing the reservation for both legs, `requeue_backoff` or an equivalent guarded update), `dispatcher/loop.py` (`_send` passes `priority`, the immediate outcome mapping after the existing `release_agent`), `tests/test_dispatcher.py`, `tests/test_queue_leader_routing.py`, `README.md` (dispatch section), `MEMORY.md`.

#### Acceptance conditions

- ac1: (CI or a Docker host) an untargeted immediate message for a session whose leader is busy is claimed at once for the leader and writes the agents.last_dispatched_at reservation like an idle claim (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_to_busy_leader_claimed_with_reservation]
- ac2: (CI or a Docker host) an immediate message claimed for an idle agent reserves it: an idle message of the session queued behind it is not claimed for that agent until its free_since moves past the reservation (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_to_idle_agent_reserves_it]
- ac3: (CI or a Docker host) an immediate message overtakes older queued idle messages of its session, and those idle messages still wait for an idle leader (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_overtakes_queued_idle]
- ac4: (CI or a Docker host) an immediate message still waits for its backoff, for a pending handover (then reaches the successor) and for a gone leader's successor (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_waits_for_backoff_handover_and_gone_leader]
- ac5: (CI or a Docker host) an immediate message is not claimed while an older message of its session is dispatching, so sends reach the wrapper in id order (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_keeps_session_order]
- ac6: (CI or a Docker host) an immediate message is not claimed while an older immediate message of its session on the same route (untargeted, or the same target) is queued in backoff; a targeted immediate for another agent still flows (new) [evidence: test:tests/test_queue_leader_routing.py::test_immediate_waits_behind_older_immediate_in_backoff]
- ac7: (CI or a Docker host) a targeted immediate message for a busy target is claimed for that target (new) [evidence: test:tests/test_queue_leader_routing.py::test_targeted_immediate_to_busy_target]
- ac8: (CI or a Docker host) _send passes the message's priority; a merged 202 marks the message sent with the running turn id and keeps the reservation (new) [evidence: test:tests/test_dispatcher.py::test_immediate_send_merged_marks_sent_with_running_turn]
- ac9: (CI or a Docker host) for an immediate message 409 busy, command_active, dialog_open, interrupting and 429 merge_queue_full release the reservation (last_dispatched_at back to the claim's previous value) and requeue it with not_before about retry_backoff_base_seconds ahead, attempts unchanged (new) [evidence: test:tests/test_dispatcher.py::test_immediate_refusal_requeues_with_backoff]
- ac10: (CI or a Docker host) a kind command message ignores its priority and follows the slash D10 path (new) [evidence: test:tests/test_dispatcher.py::test_command_ignores_priority]
- ac11: (CI or a Docker host) idle messages behave exactly as before: the existing leader-routing and dispatcher suites pass unchanged [evidence: command:uv run --frozen pytest tests/test_queue_leader_routing.py tests/test_dispatcher.py tests/test_dispatch_queue.py]
- ac12: the README dispatch section and MEMORY.md describe immediate dispatch, the reservation on both legs, the exemptions, the older-immediate hold and the backoff requeue [evidence: command:grep -q '_PICK_IMMEDIATE\|immediate message' README.md && grep -q 'immediate' MEMORY.md && grep -q 'reservation' MEMORY.md]
- ac13: Docker-free suites and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint]

#### Files

- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `tests/test_dispatcher.py`
- `tests/test_queue_leader_routing.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- `db/queue.py`: `Claim.priority: str`; `_PICK_IMMEDIATE` (as `_PICK` without `s.state = 'idle'` and the `free_since` predicate, `FOR UPDATE OF a SKIP LOCKED`); the claim of an immediate message goes through `_dispatch` like an idle one (sets `status = 'dispatching'`, `agent_id`, `dispatched_at`, `heartbeat_at` and writes the `agents.last_dispatched_at` reservation, `previous_dispatched_at` kept on the claim); the immediate leg skips a head while an older `immediate` message of its session on the same route (untargeted, or the same target) is queued; one guarded update for "dispatching -> queued with not_before, attempts unchanged" (reuse or extend `requeue`, `WHERE status = 'dispatching'`).
- `dispatcher/loop.py:_send`: `client.submit_turn(wsid, text, metadata, priority=claim.priority)`; every non-accept keeps today's `release_agent` call (guarded by `claimed_at`), then an immediate refusal requeues with backoff.
- Kind `command` claims: unchanged (slash D10).

#### Expected outcome

A message to a busy agent is dispatched at once and lands in its running turn; idle messages, commands, handovers and backoff behave exactly as before.

#### Steps

- Read `db/queue.py` (`_CANDIDATES`, `_PICK`, `_PICK_COMMAND`, `_claim_in_session`, `_dispatch`, `requeue`, `record_failure`, `release_agent`), `dispatcher/loop.py` (`_send`), `tests/test_queue_leader_routing.py`, `tests/test_dispatcher.py`, `tests/test_dispatch_queue.py`, the README dispatch section and MEMORY.md in one pass.
- Red: add every new test named in the acceptance conditions; they need Postgres, so they fail in CI (and error locally without Docker); run the Docker-free verify to confirm nothing else broke.
- Green: implement the pick, the claim leg, the order rule, the send and the outcome mapping; README and MEMORY; run the task's verify; expect all passed. Quote the summary line; the reviewer quotes the CI summary for the Postgres tests.

#### Notes

- Headline promise check (retro, recurring): every place that reads or writes the reservation (`_PICK`, `_PICK_IMMEDIATE`, `release_agent`, `retry_message`, the rollout replacer's BUSY predicate) must stay correct now that an immediate claim reserves too (design D13, interrogate 2); name each in the report.
- CI: from this task until orch-wrapper-pin-0-5-0 the real-wrapper integration and kind legs run against wrapper 0.4.1, which refuses `priority`; the orchestrator PR merges only after the pin tasks are green (design Constraints, builder Q5). Do not skip or xfail those legs here.
- Per-task security check (retro): `target_queue_full` counts queued rows only, so the wrapper's 429 cap is the flood bound for immediate messages; do not add a second cap here.
- The busy-leader hold still applies to idle messages behind an immediate one; the handover hold applies to both.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design

### S11: orch session send priority

- Status: todo
- Files: `src/agents_orchestrator/api/agent.py`, `openapi.json`, `README.md`, `tests/test_agent_session_messaging.py`
- Verify: `uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint`
- Verified head: none

#### Requirement

Goal G2 (README), verbatim: "each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool."

Design D1 (agent route part), verbatim: "Routes: [...] the agent route `POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:SessionMessageIn`), `MessageView.priority`, [...]"

Design D15 (orchestrator side), verbatim: "any-mcp-tatara-plugins `session_send` gains `priority` (enum `immediate`, `idle`, default `immediate`) [...]"

Scope (agents-orchestrator): `api/agent.py` (`SessionMessageIn.priority`, passed to `enqueue_message`), `openapi.json` (regenerated), `README.md` (both message routes: the `priority` field and what `immediate` and `idle` do, the dispatch summary in the intro), `tests/test_agent_session_messaging.py`.

#### Acceptance conditions

- ac1: (CI or a Docker host) a superleader's session_send stores priority (immediate by default, idle when sent) on the queued message, and an unknown value answers 422 (new) [evidence: test:tests/test_agent_session_messaging.py::test_session_send_priority]
- ac2: SessionMessageIn defaults to immediate, accepts idle and refuses other values [evidence: command:uv run --frozen python -c "from agents_orchestrator.api.agent import SessionMessageIn; assert SessionMessageIn(text='x').priority == 'immediate'; assert SessionMessageIn(text='x', priority='idle').priority == 'idle'" && ! uv run --frozen python -c "from agents_orchestrator.api.agent import SessionMessageIn; SessionMessageIn(text='x', priority='soon')" 2>/dev/null]
- ac3: openapi.json is regenerated from the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac4: the README documents `priority` on both message routes and says that immediate reaches a busy leader mid-turn and idle waits for an idle leader [evidence: command:grep -q '`priority`' README.md && grep -qi 'mid-turn' README.md && uv run --frozen pytest tests/test_readme_api.py]
- ac5: Docker-free suites and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

#### Files

- `src/agents_orchestrator/api/agent.py`
- `openapi.json`
- `README.md`
- `tests/test_agent_session_messaging.py`

#### Interfaces

- `api/agent.py:SessionMessageIn.priority: MessagePriority = "immediate"` (the type from `api/schemas.py`, task orch-priority-column); `session_send` passes `priority=body.priority` to `q.enqueue_message`. The D7 checks, hop guard, rate, pair and `target_queue_full` checks are unchanged and run before the insert as today.

#### Expected outcome

A superleader can ask for a message to reach the target's busy leader at once (the default) or to wait until it is idle, and the README tells API users what each does.

#### Steps

- Read `api/agent.py` (`SessionMessageIn`, `session_send`), `api/schemas.py`, `tests/test_agent_session_messaging.py` and the README message sections in one pass.
- Red: add `test_session_send_priority` and run ac2's command; expect ac2 to fail.
- Green: add the field and pass it through; regenerate `openapi.json`; document both routes in the README; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- Per-task security check (retro, recurring): this route sends on a session's behalf; the rate, pair, hop and queue limits must still apply to immediate messages exactly as before (no new bypass).
- The README is overlap-ignored but shared with orch-dispatch-immediate; this task writes the route docs, that task the dispatch section.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S12: plugins release 0.7.0

- Status: todo
- Files: `orchestration/orchestrator/pyproject.toml`, `uv.lock`, `orchestration/orchestrator/README.md`, `tests/test_source_install.py`
- Verify: `uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint`
- Verified head: none

#### Requirement

Design D15, verbatim: "Released as plugins 0.7.0 on top of session-orchestration-mcp's 0.6.0; the orchestrator pins it."

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.7.0 and agents-common 0.5.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer)."

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/pyproject.toml` (0.6.0 to 0.7.0), `uv.lock`, `orchestration/orchestrator/README.md` (example ref), `tests/test_source_install.py` (the version pin, no longer accurate after the bump).

#### Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.7.0 (updated, named) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release and no older one [evidence: command:test "$(grep -oE "ref=v[0-9.]+" orchestration/orchestrator/README.md | sort -u)" = "ref=v0.7.0"]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.7.0 exists on origin at the merge commit, on top of v0.6.0 [evidence: command:test -n "$(git ls-remote --tags origin v0.7.0)" && git merge-base --is-ancestor v0.6.0 v0.7.0]
- ac4: the release is built on v0.6.0, the live baseline [evidence: command:git merge-base --is-ancestor v0.6.0 HEAD]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

#### Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

#### Interfaces

- `orchestration/orchestrator/pyproject.toml` `[project].version = "0.7.0"`; README example `ref=v0.7.0`.

#### Expected outcome

A tagged plugins release with the priority parameter exists for the orchestrator to pin.

#### Steps

- Read `orchestration/orchestrator/pyproject.toml`, `orchestration/orchestrator/README.md`, `tests/test_source_install.py` and hive-decoupling's plugins-release-0-4-0 task in one pass.
- Version bump with no behaviour change (TDD exception): bump, `uv lock`, update the metadata pin and the README ref.
- Run the task's verify; expect all passed. Quote the summary line.

#### Notes

- Id kept from an earlier numbering; it releases v0.7.0.
- The tag is pushed by the orchestrator session after the PR merges green; ac3 is checked by it.
- If 0.7.0 is taken at build time, take the next free minor and report it so the orchestrator amends this task and orch-plugins-pin-0-5-0.
- Before the tag, the orchestrator session proposes the exact version through mx-34 (epic, live version, what it replaces) and tags only after tatara confirms (standing user rule, mx-34 #396, 2026-10-29). Renumbered 0.5.0 to 0.6.0 because slash took plugins 0.5.0 (user approval, mx-34 #406), then 0.6.0 to 0.7.0 because session-orchestration-mcp takes plugins v0.6.0 (the live baseline; latest tag v0.5.1; mx-34 #469/#470, 2026-10-29).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: agents-common renumbered 0.4.0 -> 0.5.0: the slash fix round takes v0.4.0 (mx-34 #446, #453)

- 2026-10-29 amended: plugins release renumbered v0.6.0 to v0.7.0 (mx-34 #469/#470): built on session-orchestration-mcp's v0.6.0

- 2026-10-29 amended: fix: baseline is v0.6.0 (session-orchestration-mcp), the release is v0.7.0

### S13: wrapper immediate turn merge

- Status: todo
- Files: `src/claude_code_wrapper/api/turns.py`, `src/claude_code_wrapper/router.py`, `src/claude_code_wrapper/session.py`, `README.md`, `tests/test_turn_merge.py`, `tests/test_api_turns.py`, `tests/test_command_runner.py`, `tests/test_command_runner_failures.py`
- Verify: `uv run pytest tests/test_turn_merge.py tests/test_api_turns.py tests/test_command_runner.py tests/test_command_runner_failures.py tests/test_submit_busy_first.py tests/test_stop_gate.py tests/test_session_turns.py tests/test_user_message_event.py tests/test_command_turn_resume.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "Improvement idea to messaging system- currently the messages wait for too long. Ask agents to queue another epic- message should get through PTY immediately and let either Claude Code or even agent queue them internally." Scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Goals G1, G3 and G5 (README), verbatim: "a message sent to a busy session reaches its leader through the PTY at once, mid-turn, and Claude Code queues it internally; by default no message waits for the leader to go idle." "a message delivered mid-turn never wedges the session: the running turn still ends on its Stop, and the message is linked to the turn that answered it (hop guard and delivery verifier included)." "slash commands keep running at the turn's Stop whatever the priority, and nothing is pasted while a command runs or a dialog is open."

Design D1 (wrapper part), verbatim: "`idle` is exactly today's behaviour: it waits for an idle leader and the wrapper refuses it with 409 `busy` while a turn runs. The wrapper default is `immediate` too (Q8), and the orchestrator always sends the field explicitly."

Design D2, verbatim: "The wrapper writes the message with its existing `PtyProcess.send_prompt` (bracketed paste, then CR after `boot.submit_delay_seconds`, under the PTY lock, so no other writer interleaves)."

Design D3, verbatim: "When a turn runs, an `immediate` message is pasted as `<text>\n\n<!-- ccw turn: <running turn id> -->\n<!-- ccw merge: <merge id> -->`, the running turn's marker (the `continue_turn` / `_with_marker` convention) plus a new per-paste merge marker. The wrapper answers 202 `{turn_id: <running turn id>, state: "running", merged: true, merge_id}`. Several messages then share one turn and its `final_text`; the orchestrator links each to that turn (`messages.turn_id`). A test pins that a mid-turn paste never carries another turn id in its turn marker. A session that is ready takes an `immediate` message as a normal new turn, as today (`merged: false`). A turn of any origin (client, agent, peer) can absorb a merge (my call)."

Design D4, verbatim: "No new endpoint: `TurnRequest.priority`. While a turn runs, an `immediate` message is refused, and nothing is pasted, when: the turn is in its command phase or a slash command is running or queued for the Stop (409 `command_active`); the slash epic's `DialogScanner` patterns match the current screen (409 `dialog_open`); an interrupt of the turn is in flight (409 `interrupting`); the turn already holds `sessions.merge.max_unconfirmed` unconfirmed pastes (default 4) or `sessions.merge.max_per_turn` merged pastes (default 32) (429 `merge_queue_full`) (my call, the numbers mirror the command queue's `MAX_QUEUED` 4 and Claude Code's own queue bounds). `idle` while busy stays 409 `busy`; booting and dead stay 503. The onTurn hook fires for a merge too, with `merge_into: <turn id>` in its payload; a deny is 403 `vetoed`; its annotations shallow-merge into the turn's (my call). `files` are written as for a turn; a merge's `callbackUrl` is kept on its merge entry and receives the turn's terminal event (my call). Events: `user_message` at paste time (turn_id of the running turn, `merged: true`), `turn_merged {turn_id, merge_id, origin, metadata}` at paste time, `turn_merge_absorbed {turn_id, merge_id}` when the transcript shows the paste. Order of a merge (interrogate 7, as `Session.submit` reserves before the first byte): the onTurn hook first, then every refusal re-checked and the merge entry appended to the running record and persisted synchronously, then the paste; a paste that fails (`PtyClosed`) removes the entry. A Stop during the paste delay therefore already sees the pending merge (D6), and concurrent merges cannot pass the cap. `dialog_open` (interrogate 5): the wrapper reads a named "current screen" source in which a dialog footer that was dismissed no longer matches (a byte tail alone does not qualify); the default patterns must match the permission, AskUserQuestion and MCP elicitation footers probe P6 captured; the check runs before the paste and again under the PTY lock just before the CR; a dialog seen at the second check withholds the CR, clears the unsent text with the key P6 recorded as safe and refuses 409 `dialog_open` with the entry removed. The dialog guard and the caps are task wrapper-merge-guards; the rest of D4 is wrapper-immediate-turn-merge."

Design D5 (router part), verbatim: "The router sets `absorbed_at` once (first sighting) for each listed merge of the running turn, ignores merge ids of any other turn, and emits `turn_merge_absorbed`. A merge marker never moves `_last_marker` by itself: the turn marker on the same line names the running turn."

Design D8 (wrapper part), verbatim: "Immediate prose is never pasted while a command runs or waits for the Stop (D4 `command_active`), and the slash epic's slot handover at Stop keeps queued client commands ahead of prose."

Scope (claude-code-wrapper): `api/turns.py` (`TurnRequest.priority`, response `merged`, `merge_id`, the refusal codes `command_active` and `interrupting`), `router.py` (`submit_turn(priority=...)`, the merge leg, onTurn `merge_into`, events, `merge_markers` handling in `_on_transcript_events`, callback delivery to merge entries), `session.py` (`Session.merge`: onTurn first, then the refusal re-check and the entry appended and persisted before the paste, marker text, paste under the existing lock, entry removed on `PtyClosed`), `README.md` (API, events, codes), `tests/test_turn_merge.py` (new). `MergedPrompt` and `TurnRecord.merged` come from task wrapper-merge-marker-parse; `dialog_open`, the caps and `sessions.merge.*` are task wrapper-merge-guards; the MEMORY.md entry on the merge model is written by task wrapper-merge-stop-gate. Tests no longer accurate (named): `tests/test_api_turns.py::test_submit_busy_409_and_booting_503` keeps its 409 for a body with `priority: "idle"` and its stub router's `submit_turn` gains the `priority` parameter; `tests/test_command_runner.py::test_idle_command_marks_busy_and_turn_409` and `tests/test_command_runner_failures.py::test_turn_during_idle_command_is_busy_and_drained_runner_accepts` post with no priority while an idle command runs and assert 409 `busy`, which the immediate default makes 409 `command_active`; their bodies gain `"priority": "idle"` (my call, builder Q2); these three files are changed only for that.

#### Acceptance conditions

- ac1: POST /turns with priority immediate, and with no priority, while a turn runs answers 202 {turn_id of the running turn, state running, merged true, merge_id}; exactly one paste reaches the fake (new) [evidence: test:tests/test_turn_merge.py::test_immediate_while_busy_merges_into_running_turn]
- ac2: wedge pin: the pasted text ends with the running turn's turn marker and the merge marker, and no turn marker written while that turn runs names any other turn id (new) [evidence: test:tests/test_turn_merge.py::test_midturn_paste_never_carries_a_new_turn_marker]
- ac3: priority idle while busy answers 409 busy and nothing is typed (new) [evidence: test:tests/test_turn_merge.py::test_idle_while_busy_is_409_busy]
- ac4: priority immediate on a ready session starts a normal new turn: 202 merged false, turn_started emitted (new) [evidence: test:tests/test_turn_merge.py::test_immediate_on_ready_session_starts_a_turn]
- ac5: refusals write nothing to the PTY: 409 command_active while a slash command runs, while one is queued for the Stop, while the turn is in its command phase and while an idle command holds the session busy with no turn record; 409 interrupting while an interrupt is in flight (new) [evidence: test:tests/test_turn_merge.py::test_refusals_while_busy_write_nothing]
- ac6: the merge entry is on the running record and persisted before the first pasted byte, the refusals are re-checked after the onTurn hook, and a paste that raises PtyClosed leaves no entry (new) [evidence: test:tests/test_turn_merge.py::test_merge_entry_recorded_before_the_paste]
- ac7: GET /turns/{id} lists the merge entries with pasted_at; with the fake in queue mode absorbed_at is set when the transcript shows the merge marker and turn_merge_absorbed is emitted once; a merge id of another turn is ignored; _last_marker stays the running turn's id (new) [evidence: test:tests/test_turn_merge.py::test_merge_absorbed_from_transcript]
- ac8: at paste time user_message (turn_id of the running turn, merged true) and turn_merged {turn_id, merge_id, origin, metadata} are emitted, and no turn_started (new) [evidence: test:tests/test_turn_merge.py::test_merge_events]
- ac9: onTurn fires for a merge with merge_into; a deny answers 403 vetoed and nothing is typed; allow annotations merge into the turn's annotations (new) [evidence: test:tests/test_turn_merge.py::test_on_turn_on_merge]
- ac10: with the fake in queue mode a message merged during a tool step ends with the running turn: one turn_completed whose final_text answers after the injection, the session ready afterwards, the merge's callbackUrl receiving the terminal event (new) [evidence: test:tests/test_turn_merge.py::test_merged_message_completes_with_running_turn]
- ac11: limits.max_prompt_bytes and the 16 KiB metadata cap apply to a merge (413 too_large) (new) [evidence: test:tests/test_turn_merge.py::test_merge_size_limits]
- ac12: the stub-based API test keeps 409 busy for an idle body (body and stub signature only, named) [evidence: test:tests/test_api_turns.py::test_submit_busy_409_and_booting_503]
- ac13: the two command runner tests keep 409 busy for an idle body during an idle command (body only, named, builder Q2) [evidence: command:uv run pytest tests/test_command_runner.py::test_idle_command_marks_busy_and_turn_409 tests/test_command_runner_failures.py::test_turn_during_idle_command_is_busy_and_drained_runner_accepts]
- ac14: README documents priority, merged, merge_id, command_active, interrupting and the merge events, and the API README guard stays green [evidence: command:grep -q 'merge_id' README.md && grep -q 'turn_merged' README.md && uv run pytest tests/test_readme_api.py]
- ac15: targeted suites and lint pass [evidence: command:uv run pytest tests/test_turn_merge.py tests/test_api_turns.py tests/test_command_runner.py tests/test_command_runner_failures.py tests/test_submit_busy_first.py tests/test_stop_gate.py tests/test_session_turns.py tests/test_user_message_event.py tests/test_command_turn_resume.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/api/turns.py`
- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/session.py`
- `README.md`
- `tests/test_turn_merge.py`
- `tests/test_api_turns.py`
- `tests/test_command_runner.py`
- `tests/test_command_runner_failures.py`

#### Interfaces

- `api/turns.py:TurnRequest.priority: Literal["immediate", "idle"] = "immediate"`. Response 202: `{"turn_id", "state", "merged": bool, "merge_id": str | None}`. Refusals here: 409 `busy` (idle while busy), 409 `command_active` (also immediate during an idle command, busy with no turn record), 409 `interrupting`, 503 `booting` / `dead`, 403 `vetoed`, 413 `too_large`. Task wrapper-merge-guards adds 409 `dialog_open` and 429 `merge_queue_full` inside the same `Session.merge`.
- `router.SessionRouter.submit_turn(text, *, files=None, callback_url=None, origin="client", metadata=None, priority: Literal["immediate", "idle"] = "idle") -> TurnRecord | MergeResult`: the router's own default stays `idle` so internal callers (peer inbox, tests) keep today's behaviour; the API passes the body's value. The builder picks the return shape (for example a `MergeResult(record, merge_id)`), documented in the docstring.
- `session.Session.merge(text, *, origin, metadata, callback_url) -> MergedPrompt`: called after the onTurn hook allowed; synchronously re-checks every refusal (`TurnRejected("busy" | "command_active" | "interrupting" | "booting" | "dead")`), appends the entry to `running.merged` and persists, all before the first await; then pastes `self._with_marker(text, running)` plus `\n<!-- ccw merge: <merge_id> -->` through `pty.send_prompt`; on `PtyClosed` removes the entry and persists (design D4 order, as `Session.submit` reserves before the first byte).
- `turns.MergedPrompt` and `TurnRecord.merged` come from task wrapper-merge-marker-parse; this task fills them.
- Router absorption: for each id in `UserPrompt.merge_markers` that names a merge of the running turn, set `absorbed_at` once and emit `turn_merge_absorbed`; ids of any other turn are ignored (logged at debug).
- Events: `user_message` gains `merged: true` on the merge leg; new `turn_merged`, `turn_merge_absorbed`.

#### Expected outcome

A message posted to a busy session is pasted into the running turn at once, joins it and is answered by its final text; the session cannot wedge on the marker; commands and interrupts are never disturbed by a paste; the merge is on the record before its first byte. Dialogs and the flood cap follow in wrapper-merge-guards.

#### Steps

- Read `api/turns.py`, `router.py` (`submit_turn`, `_submit_turn`, `_on_transcript_events`, `_after_turn`, `_deliver`), `session.py` (`check_submittable`, `submit`, `continue_turn`, `_with_marker`, `command_active`, `_commands_turn`, `_interrupting`), `turns.py` (`MergedPrompt` from wrapper-merge-marker-parse), the slash epic's command queue in `commands.py` / `router.py`, `tests/test_api_turns.py`, `tests/test_command_runner.py`, `tests/test_command_runner_failures.py`, `tests/test_submit_busy_first.py`, `tests/test_stop_gate.py`, `tests/conftest.py`, the fake's queue mode and `docs/claude-midturn-input.md` in one pass.
- Red: write `tests/test_turn_merge.py` with every new test named in the acceptance conditions (fake claude in `"midturn_input": "queue"` where absorption is needed), change the stub signature in `tests/test_api_turns.py` and add `"priority": "idle"` to the busy-while-command bodies of the two command runner tests; run `uv run pytest tests/test_turn_merge.py tests/test_api_turns.py tests/test_command_runner.py tests/test_command_runner_failures.py`; expect the new tests to fail.
- Green: implement the field, the merge leg, the refusals, the events, the absorption handling and README; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- The anti-goal this task pins: never `new_turn_id()` on the merge leg; the turn marker is always the running record's (`_with_marker`).
- `check_submittable` stays the idle-path gate; the merge leg has its own checks in `Session.merge`, all synchronous before the paste (no await between the checks and the slot-free write except the PTY lock).
- `dialog_open`, the caps and `sessions.merge.*` are task wrapper-merge-guards (files capped at 8); do not add them here.
- Per-task security check (retro, recurring): this route sends text into a running agent on a caller's behalf; check the size caps, the onTurn veto and that no metadata or text reaches a log line beyond today's redaction.
- If the probe's consequences table contradicts D3, D4 or D5, the orchestrator amends this task before it starts; do not work around a contradiction here.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: files capped at 8: the MEMORY.md entry moves to wrapper-merge-stop-gate

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design

### S14: mxc relay once per turn

- Status: todo
- Files: `pyproject.toml`, `uv.lock`, `src/agents_matrix_connector/migrations/0003_run_relayed_turn.sql`, `src/agents_matrix_connector/db/runs.py`, `src/agents_matrix_connector/tracker.py`, `tests/test_tracker.py`, `tests/test_schema.py`, `MEMORY.md`
- Verify: `uv run ruff check . && uv run ruff format --check . && uv run pytest tests/test_tracker.py tests/test_schema.py`
- Verified head: none

#### Requirement

Goal G4 (README), verbatim: "Matrix chat messages in a room whose run is in progress are delivered at once, and an answer shared by merged messages is relayed to the room once."

Design D18 (tracker part), verbatim: "The tracker relays a completed turn's final text once per turn, in any evaluation order (interrogate 1: `tick` finishes runs one at a time, so a rule over in-progress runs relays twice): a run that finishes from a completed turn records that turn id in `runs.relayed_turn_id` (new nullable column, migration `0003_run_relayed_turn.sql`, written only by the tracker inside the same guarded `runs.finish`); a run whose message links to a turn already recorded on another run of its room finishes `handled` with reason `merged` and no reply. agents-common `Message.turn_id` (new, released 0.5.0, connector pin moved) carries the link; the fake orchestrator can complete one turn for several messages."

Design anti-goal, verbatim: "The same final answer relayed twice to a Matrix room (D18)."

Scope (agents-matrix-connector): `pyproject.toml` and `uv.lock` (agents-common to v0.5.0 from the pin on main: v0.3.0, or v0.4.0 if the slash fix round moved it, both the dependency and the testing extra), `src/agents_matrix_connector/migrations/0003_run_relayed_turn.sql` (new, `runs.relayed_turn_id`), `src/agents_matrix_connector/db/runs.py` (`finish` writes it, `turn_relayed`), `src/agents_matrix_connector/tracker.py` (the once-per-turn rule), `tests/test_tracker.py`, `tests/test_schema.py`, `MEMORY.md`. Test no longer accurate (named): `tests/test_schema.py` pins the exact `MIGRATIONS` list; it gains `0003_run_relayed_turn.sql`.

#### Acceptance conditions

- ac1: the connector pins agents-common v0.5.0 in both dependency lines and uv.lock, and Message has turn_id [evidence: command:test "$(grep -c 'agents-common@v0.5.0' pyproject.toml)" = 2 && ! grep -qE 'agents-common@v0\.[34]\.0' pyproject.toml && uv run --frozen python -c "from agents_common.orchestrator import Message; assert 'turn_id' in Message.model_fields"]
- ac2: (CI or a Docker host) migration 0003 adds the nullable runs.relayed_turn_id with its writer comment, and the migration list, idempotence and writer-comment pins pass with it (new) [evidence: test:tests/test_schema.py::test_run_relayed_turn_column]
- ac3: (CI or a Docker host) two in-progress runs of one room whose messages link to the same completed turn produce exactly one reply in one tick; the relaying run stores relayed_turn_id in its finish and the other finishes handled with reason merged and sends nothing (new) [evidence: test:tests/test_tracker.py::test_merged_turn_relayed_once]
- ac4: (CI or a Docker host) a run evaluated in a later tick, after its sibling already finished and relayed the same turn (for example its poll hit OrchestratorUnavailable once), still sends nothing and finishes handled merged (new) [evidence: test:tests/test_tracker.py::test_merged_turn_not_relayed_after_sibling_finished]
- ac5: (CI or a Docker host) runs whose messages link to different turns each relay their own answer as today (new) [evidence: test:tests/test_tracker.py::test_distinct_turns_each_relayed]
- ac6: (CI or a Docker host) the existing tracker and schema cases pass, the schema MIGRATIONS list changed only to add 0003 (named) [evidence: command:uv run pytest tests/test_tracker.py tests/test_schema.py]
- ac7: MEMORY.md has a dated entry on relaying a merged turn once, the persisted relayed_turn_id and why [evidence: command:grep -q 'merged' MEMORY.md && grep -q 'relayed_turn_id' MEMORY.md]
- ac8: lint passes and the tracker and schema suites run [evidence: command:uv run ruff check . && uv run ruff format --check . && uv run pytest tests/test_tracker.py tests/test_schema.py]

#### Files

- `pyproject.toml`
- `uv.lock`
- `src/agents_matrix_connector/migrations/0003_run_relayed_turn.sql`
- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/tracker.py`
- `tests/test_tracker.py`
- `tests/test_schema.py`
- `MEMORY.md`

#### Interfaces

- `migrations/0003_run_relayed_turn.sql` (next free number; if taken, the next free one, reported so the orchestrator amends `files`): `ALTER TABLE runs ADD COLUMN IF NOT EXISTS relayed_turn_id text NULL`, an index on `(room_id, relayed_turn_id)`, and the writer comment the schema test expects (written only by the tracker through `runs.finish`).
- `db/runs.py`: `finish(conn, run_id, status, reason=None, *, relayed_turn_id=None)` writes it in the same guarded `in-progress -> handled|failed` transition; `turn_relayed(conn, room_id, turn_id, *, exclude_run_id) -> bool`.
- `tracker._outcome`: when the run's message has `turn.status == "completed"` and `runs.turn_relayed(room, message.turn_id, exclude_run_id=run.id)`, the outcome is `_Outcome("handled", "merged")` with no chunks; otherwise the run relays as today (including `_send_match`) and `_finish` stores `relayed_turn_id = message.turn_id` for every run it finishes from a completed turn, so the rule holds in any evaluation order (design D18, interrogate 1).
- New reason constant `MERGED = "merged"` beside `ALREADY_SENT` / `EMPTY_REPLY`.

#### Expected outcome

When several chat messages were answered by one merged agent turn, the room gets that answer once.

#### Steps

- Read `pyproject.toml`, `src/agents_matrix_connector/tracker.py`, `db/runs.py`, `db/__init__.py` (`transition`), `migrations/0002_agent_sends.sql`, `tests/test_tracker.py`, `tests/test_schema.py`, `tests/conftest.py` and agents-common's `fake_orchestrator.complete_turn(..., turn_id=)` in one pass.
- Move the pin (`uv lock`); red: add the new tests named in the acceptance conditions and add `0003_run_relayed_turn.sql` to the `MIGRATIONS` list of `tests/test_schema.py` (no longer accurate: it lists the migrations exactly); they need Postgres and fail in CI until green.
- Green: write the migration, the runs writer, the once-per-turn rule and the MEMORY entry; run the task's verify; expect lint clean (the tracker suite runs in CI). Quote the summary lines.

#### Notes

- Depends on the agents-common v0.5.0 tag on origin (common-release-0-5-0 ac3, pushed by the orchestrator session).
- Runs finish through the existing guarded transition in `db/runs.py`; `relayed_turn_id` gets no other writer.
- Tree state: the connector's repo tests (`pool`, `conn`, `url` fixtures from `agents_common.testing.migrated_db`) need Postgres through Docker, absent in agent pods; they run in CI on the PR and the reviewer quotes the CI summary line.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design

- 2026-10-29 amended: agents-common renumbered 0.4.0 -> 0.5.0: the slash fix round takes v0.4.0 (mx-34 #446, #453)

### S15: orch merged delivery

- Status: todo
- Files: `src/agents_orchestrator/db/queue.py`, `src/agents_orchestrator/dispatcher/verify.py`, `tests/test_agent_session_messaging.py`, `tests/test_ambiguous_verify.py`, `MEMORY.md`
- Verify: `uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py && mise run lint`
- Verified head: none

#### Requirement

Goal G3 (README), verbatim: "a message delivered mid-turn never wedges the session: the running turn still ends on its Stop, and the message is linked to the turn that answered it (hop guard and delivery verifier included)."

Design D14, verbatim: "`queue.turn_hop` takes `max(hop)` over the messages with a sender linked to the agent's current turn (today `ORDER BY m.id DESC LIMIT 1`), so a merged session message cannot reset the hop count. The verifier's `_carries` matches a turn whose `metadata.orch_message_id` or any `merged[].metadata.orch_message_id` equals the message id, so an ambiguous send that was merged resolves `started` with that turn instead of being resent. The orchestrator's `TurnRecord` model gains `merged`. `messages.status` stays `sent`; "answered" stays derived through `turn_id` (all messages merged into one turn read its `final_text`). agents-common's run tracker reads the linked turn as today."

Design anti-goal, verbatim: "An ambiguous send resent after it was merged (duplicate delivery): the verifier recognises merged deliveries (D14)."

Scope (agents-orchestrator): `db/queue.py` (`turn_hop`), `dispatcher/verify.py` (`_carries`), `tests/test_agent_session_messaging.py`, `tests/test_ambiguous_verify.py`, `MEMORY.md`.

#### Acceptance conditions

- ac1: (CI or a Docker host) turn_hop returns the highest hop among the sender messages linked to the agent's current turn, not the newest one's (new) [evidence: test:tests/test_agent_session_messaging.py::test_turn_hop_is_max_over_merged_messages]
- ac2: (CI or a Docker host) a session_send from a turn that absorbed a hop-3 message and then a hop-1 message is stored with hop 4 (new) [evidence: test:tests/test_agent_session_messaging.py::test_send_from_merged_turn_counts_the_max_hop]
- ac3: (CI or a Docker host) an ambiguous send whose message was merged into a running turn resolves started with that turn and is never resent (new) [evidence: test:tests/test_ambiguous_verify.py::test_merged_delivery_resolves_started]
- ac4: (CI or a Docker host) a stale dispatching immediate message that the wrapper merged resolves the same way (new) [evidence: test:tests/test_ambiguous_verify.py::test_stale_dispatching_merged_resolves_started]
- ac5: MEMORY.md has a dated entry on merged deliveries (hop and verifier) and why [evidence: command:grep -q 'merged' MEMORY.md]
- ac6: Docker-free suites and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_wrapper_client.py && mise run lint]

#### Files

- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/dispatcher/verify.py`
- `tests/test_agent_session_messaging.py`
- `tests/test_ambiguous_verify.py`
- `MEMORY.md`

#### Interfaces

- `db/queue.py:turn_hop(conn, agent_id) -> int | None`: `SELECT max(m.hop) ...` over `messages m` with `m.turn_id = s.current_turn_id` and `m.sender_session_id IS NOT NULL`; None when there is none.
- `dispatcher/verify.py:_carries(record: TurnRecord, message_id: int) -> bool`: true when `record.metadata["orch_message_id"]` or any `record.merged[i].metadata["orch_message_id"]` equals the id (compared as strings, as today).

#### Expected outcome

A message merged into another message's turn is counted correctly by the hop guard and is never delivered twice after an ambiguous send.

#### Steps

- Read `db/queue.py:turn_hop`, `dispatcher/verify.py`, `wrapper/models.py:TurnRecord` (with `merged` from orch-wrapper-client-priority), `tests/test_agent_session_messaging.py` and `tests/test_ambiguous_verify.py` in one pass.
- Red: add the four tests; they need Postgres and fail in CI until green.
- Green: change `turn_hop` and `_carries`, MEMORY entry; run the task's verify; expect all passed. Quote the summary line; the reviewer quotes the CI summary for the Postgres tests.

#### Notes

- The verifier looks at the newest turns (`NEWEST_TURNS`); a merged delivery lives in the running turn, which is among them.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S16: web sync message priority

- Status: todo
- Files: `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts`
- Verify: `npm run check:api && npx tsc -b && npm run lint`
- Verified head: none

#### Requirement

Design D16, verbatim: "The vendored orchestrator spec and `schema.d.ts` are re-synced first."

Design Constraints, verbatim: "Generated files are regenerated, never hand-edited: orchestrator `openapi.json` (`uv run python -m agents_orchestrator.api.openapi > openapi.json`), agents-web `src/api/schema.d.ts` (`npm run sync:api -- orchestrator`)."

Scope (agents-web): `openapi/orchestrator.json`, `openapi/orchestrator.source` (an agents-orchestrator commit whose `openapi.json` carries `priority`), `src/api/schema.d.ts` (generated).

#### Acceptance conditions

- ac1: the vendored spec and the generated types agree [evidence: command:npm run check:api]
- ac2: PostMessage and MessageView carry priority in the vendored spec and the generated types [evidence: command:grep -q '"priority"' openapi/orchestrator.json && grep -q 'priority' src/api/schema.d.ts]
- ac3: the source pin names an agents-orchestrator commit whose openapi.json carries priority [evidence: command:git -C ../agents-orchestrator show "$(awk '{print $2}' openapi/orchestrator.source):openapi.json" | grep -q '"priority"']
- ac4: the app type-checks and lint passes [evidence: command:npx tsc -b && npm run lint]

#### Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

#### Interfaces

- `openapi/orchestrator.source`: `<repo> <commit>` as today, moved to the epic's orchestrator commit that has `orch-session-send-priority`; `src/api/schema.d.ts` regenerated by `npm run sync:api -- orchestrator`.

#### Expected outcome

The web client's types know the message priority field.

#### Steps

- Read `openapi/orchestrator.source`, `scripts/` sync tooling and the slash epic's web-sync-message-kind task in one pass.
- Generated-file sync with no behaviour change (TDD exception): run `npm run sync:api -- orchestrator` against the pinned commit.
- Run the task's verify; expect all passed. Quote the summary line.

#### Notes

- Never hand-edit `schema.d.ts` or the vendored JSON.
- Source commit (my call, builder Q6): `openapi/orchestrator.source` names the orchestrator epic-branch commit that carries orch-session-send-priority; the orchestrator PR is merged with a merge commit so that sha stays reachable (precedent in retro deploy-safe-agent-sessions, matrix-connector-agent-initi). ac3 reads `../agents-orchestrator`, the sibling tree in the epic worktree layout (`.claude/worktrees/immediate-message-delivery-w/agents-orchestrator`), as in `code/`.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun; a named load-dependent flake becomes a reported finding, not a silent rerun (retro).

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: source commit and worktree path settled (builder Q6, my call; Notes edited directly)

### S17: wrapper merge guards

- Status: todo
- Files: `src/claude_code_wrapper/session.py`, `src/claude_code_wrapper/pty_proc.py`, `src/claude_code_wrapper/ring.py`, `src/claude_code_wrapper/config.py`, `README.md`, `tests/test_turn_merge_guards.py`, `tests/test_pty_proc.py`
- Verify: `uv run pytest tests/test_turn_merge_guards.py tests/test_turn_merge.py tests/test_pty_proc.py tests/test_readme_config.py tests/test_readme_api.py tests/test_config.py --deselect tests/test_pty_proc.py::test_exit_without_eof_still_fires --deselect tests/test_pty_proc.py::test_close_terminates_group_then_kill && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "message should get through PTY immediately and let either Claude Code or even agent queue them internally."

Goal G5 (README), verbatim: "slash commands keep running at the turn's Stop whatever the priority, and nothing is pasted while a command runs or a dialog is open."

Design D4 (caps), verbatim: "the turn already holds `sessions.merge.max_unconfirmed` unconfirmed pastes (default 4) or `sessions.merge.max_per_turn` merged pastes (default 32) (429 `merge_queue_full`) (my call, the numbers mirror the command queue's `MAX_QUEUED` 4 and Claude Code's own queue bounds)."

Design D4 (dialog guard, interrogate 5), verbatim: "`dialog_open` (interrogate 5): the wrapper reads a named "current screen" source in which a dialog footer that was dismissed no longer matches (a byte tail alone does not qualify); the default patterns must match the permission, AskUserQuestion and MCP elicitation footers probe P6 captured; the check runs before the paste and again under the PTY lock just before the CR; a dialog seen at the second check withholds the CR, clears the unsent text with the key P6 recorded as safe and refuses 409 `dialog_open` with the entry removed. The dialog guard and the caps are task wrapper-merge-guards; the rest of D4 is wrapper-immediate-turn-merge."

Design D4 (order, interrogate 7), verbatim: "the onTurn hook first, then every refusal re-checked and the merge entry appended to the running record and persisted synchronously, then the paste; a paste that fails (`PtyClosed`) removes the entry. A Stop during the paste delay therefore already sees the pending merge (D6), and concurrent merges cannot pass the cap."

Design anti-goals, verbatim: "Text pasted while a slash command runs, while the turn is in its command phase or while a dialog is on screen (a CR answers a dialog, probe outA of the slash epic)." "An unbounded number of pastes into one turn (flood): capped, 429 (D4)."

Scope (claude-code-wrapper): `session.py` (`dialog_open` and cap checks inside `Session.merge`, the pre-CR re-check), `pty_proc.py` (`send_prompt` takes a check run under its lock before the CR), `ring.py` (the current-screen source, if the builder builds it there), `config.py` (`sessions.merge.max_unconfirmed`, `sessions.merge.max_per_turn`, dialog defaults extended to the captured footers), `README.md` (screen source, codes, configuration), `tests/test_turn_merge_guards.py` (new), `tests/test_pty_proc.py`.

#### Acceptance conditions

- ac1: with a dialog footer on the current screen, POST /turns immediate while a turn runs answers 409 dialog_open and nothing is typed (new) [evidence: test:tests/test_turn_merge_guards.py::test_dialog_on_screen_refuses_merge]
- ac2: the default dialog patterns match every dialog block of tests/fixtures/screens/midturn-dialogs.txt captured by probe P6 (permission, AskUserQuestion, MCP elicitation) (new) [evidence: test:tests/test_turn_merge_guards.py::test_default_patterns_match_captured_dialog_footers]
- ac3: once the captured dismissal output has followed a footer, the dismissed footer no longer refuses and the merge is accepted (new) [evidence: test:tests/test_turn_merge_guards.py::test_dismissed_dialog_does_not_refuse_merge]
- ac4: a dialog that appears between the paste and the CR withholds the CR, writes the clear key P6 recorded, removes the merge entry from the record and answers 409 dialog_open (new) [evidence: test:tests/test_turn_merge_guards.py::test_dialog_between_paste_and_cr_withholds_the_cr]
- ac5: send_prompt runs its check under the PTY lock after the paste delay and before the CR, and writes no CR when the check refuses (new) [evidence: test:tests/test_pty_proc.py::test_send_prompt_checks_before_the_cr]
- ac6: with max_unconfirmed unconfirmed pastes the next merge is 429 merge_queue_full and writes nothing; once one is absorbed a new paste is accepted; past max_per_turn merges the next is 429 merge_queue_full (new) [evidence: test:tests/test_turn_merge_guards.py::test_unconfirmed_and_per_turn_caps]
- ac7: concurrent merge requests never leave more than max_unconfirmed unconfirmed entries on the record, the surplus answered 429 merge_queue_full (new) [evidence: test:tests/test_turn_merge_guards.py::test_concurrent_merges_respect_the_cap]
- ac8: README names the current-screen source, dialog_open, merge_queue_full and sessions.merge.max_unconfirmed and max_per_turn, and the README and config guards pass [evidence: command:grep -q 'dialog_open' README.md && grep -q 'merge_queue_full' README.md && grep -q 'max_unconfirmed' README.md && uv run pytest tests/test_readme_config.py tests/test_readme_api.py tests/test_config.py]
- ac9: targeted suites and lint pass [evidence: command:uv run pytest tests/test_turn_merge_guards.py tests/test_turn_merge.py tests/test_pty_proc.py tests/test_readme_config.py tests/test_readme_api.py tests/test_config.py --deselect tests/test_pty_proc.py::test_exit_without_eof_still_fires --deselect tests/test_pty_proc.py::test_close_terminates_group_then_kill && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/pty_proc.py`
- `src/claude_code_wrapper/ring.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `tests/test_turn_merge_guards.py`
- `tests/test_pty_proc.py`

#### Interfaces

- `pty_proc.PtyProcess.send_prompt(text, delay, *, before_cr: Callable[[], bool] | None = None)`: paste, wait `delay`, then call `before_cr()` under the same lock hold; when it refuses, no CR is written, the P6 clear key is written instead within the same lock hold (no other writer between), and the method raises or returns a value the caller can tell apart (builder's choice, documented in the docstring).
- `session.Session.merge`: after the onTurn hook, synchronously checks `dialog_open` (current screen) and the caps together with the refusals of wrapper-immediate-turn-merge, appends the entry, then pastes with `before_cr` re-checking `dialog_open`; on a refusal at that point (clear key already written by `send_prompt`) it removes the entry, persists and raises `TurnRejected("dialog_open")`.
- Current-screen source (design D4, "Left to the builder"): a screen snapshot or the scanner's last hit cleared by the dismissal output P6 recorded; whichever is chosen is named in README; a byte tail alone does not qualify.
- `config.py`: `sessions.merge.max_unconfirmed: int = 4`, `sessions.merge.max_per_turn: int = 32`; `sessions.commands.dialog_patterns` defaults extended only as far as needed to match the captured footers.
- Refusals added: 409 `dialog_open`, 429 `merge_queue_full`.

#### Expected outcome

A mid-turn paste is never typed into, or submitted onto, a dialog of the real Claude Code 2.1.304; a dismissed dialog does not block delivery; no turn holds more unconfirmed pastes than the cap, even under concurrent requests.

#### Steps

- Read `session.py` (`Session.merge` from wrapper-immediate-turn-merge, `FatalScanner`, the slash epic's `DialogScanner`), `pty_proc.py` (`send_prompt`, `paste_bytes`), `ring.py`, `config.py` (`sessions.commands.dialog_patterns`), `README.md`, `tests/test_turn_merge.py`, `tests/test_pty_proc.py`, `tests/fixtures/screens/midturn-dialogs.txt` and `docs/claude-midturn-input.md` (P6) in one pass.
- Red: write `tests/test_turn_merge_guards.py` with every test named in the acceptance conditions and add `test_send_prompt_checks_before_the_cr` to `tests/test_pty_proc.py`; run `uv run pytest tests/test_turn_merge_guards.py tests/test_pty_proc.py::test_send_prompt_checks_before_the_cr`; expect them to fail.
- Green: implement the screen source, the checks, the pre-CR hook, the caps, config and README; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- If P6 is recorded unsettled or found no safe clear key, the orchestrator amends this task before it starts (design D11); never invent footers or keys.
- Agents boot in bypass-permissions mode (boot dialog in `config.py`), so AskUserQuestion and MCP elicitation are the likely dialogs mid-turn; still pin all three captured kinds.
- `ESC` is never a clear key here: mid-turn it interrupts the turn, and two ESCs at an empty prompt open the rewind menu.
- Per-task security check (retro, recurring): the 429 cap is the flood bound for immediate messages (the orchestrator adds no second cap).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

### S18: mxc deliver during run

- Status: todo
- Files: `src/agents_matrix_connector/db/inbound.py`, `tests/test_inbound_repo.py`, `tests/test_worker.py`, `README.md`, `MEMORY.md`
- Verify: `uv run ruff check . && uv run ruff format --check . && uv run pytest tests/test_inbound_repo.py tests/test_worker.py`
- Verified head: none

#### Requirement

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "currently the messages wait for too long. [...] message should get through PTY immediately and let either Claude Code or even agent queue them internally."

Goal G4 (README), verbatim: "Matrix chat messages in a room whose run is in progress are delivered at once, and an answer shared by merged messages is relayed to the room once."

Design D18 (delivery part), verbatim: "`inbound.rooms_ready` also returns a room whose in-progress runs are all `follow` runs with a posted message (`message_id` set) and a session, so its new rows are claimed into a new follow run and posted at once (server default `immediate`); a room whose first run has not posted yet still waits (there is no session to post to)."

Scope (agents-matrix-connector): `src/agents_matrix_connector/db/inbound.py` (`rooms_ready`), `tests/test_inbound_repo.py`, `tests/test_worker.py`, `README.md` (the run model), `MEMORY.md`.

#### Acceptance conditions

- ac1: (CI or a Docker host) rooms_ready returns a room with new rows whose in-progress runs are all follow runs with a message_id and a session (new) [evidence: test:tests/test_inbound_repo.py::test_rooms_ready_includes_room_with_posted_follow_run]
- ac2: (CI or a Docker host) rooms_ready does not return a room whose in-progress run is a first run or has no message_id yet (new) [evidence: test:tests/test_inbound_repo.py::test_rooms_ready_waits_for_unposted_or_first_run]
- ac3: (CI or a Docker host) the worker claims a room's new rows into a second follow run and posts them to the bound session while the first run is still in progress (new) [evidence: test:tests/test_worker.py::test_new_messages_posted_while_run_in_progress]
- ac4: (CI or a Docker host) the existing inbound and worker cases pass unchanged [evidence: command:uv run pytest tests/test_inbound_repo.py tests/test_worker.py]
- ac5: README and MEMORY.md describe delivery during a run and why [evidence: command:grep -qi 'in progress' README.md && grep -q 'rooms_ready' MEMORY.md]
- ac6: lint passes and the suites run [evidence: command:uv run ruff check . && uv run ruff format --check . && uv run pytest tests/test_inbound_repo.py tests/test_worker.py]

#### Files

- `src/agents_matrix_connector/db/inbound.py`
- `tests/test_inbound_repo.py`
- `tests/test_worker.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- `db/inbound.rooms_ready(conn) -> list[str]`: a room is ready when it has `status = 'new'` rows and every `runs` row of it with `status = 'in-progress'` has `kind = 'follow'`, `message_id IS NOT NULL` and `session_id IS NOT NULL` (none in progress keeps today's meaning); order by the oldest new row as today.
- The worker's `_room` / `_follow` / `_claim` path is reused unchanged: a bound room's new rows become a new follow run.

#### Expected outcome

A Matrix user's follow-up message reaches the agent at once while it is still working on the previous one; the answer reaches the room once (mxc-relay-once-per-turn).

#### Steps

- Read `db/inbound.py`, `db/runs.py`, `worker.py` (`tick`, `_room`, `_follow`, `_claim`, `_deliver`), `tests/test_inbound_repo.py`, `tests/test_worker.py`, README and MEMORY.md in one pass.
- Red: add ac1 to ac3; they need Postgres and fail in CI until green.
- Green: change `rooms_ready`, README and MEMORY; run the task's verify; expect lint clean (the suites run in CI). Quote the summary lines.

#### Notes

- Ordering inside a room stays by row id: a new follow run claims only rows newer than every claimed one, because `claim_room` takes `status = 'new'` rows only.
- The PREAMBLE rule of `_deliver` (sent when the session has no other run in the room) stays as is; a second concurrent run gets no preamble.
- Depends on mxc-relay-once-per-turn, so a room can never get the same merged answer twice.
- Tree state: the connector's repo tests (`pool`, `conn`, `url` fixtures from `agents_common.testing.migrated_db`) need Postgres through Docker, absent in agent pods; they run in CI on the PR and the reviewer quotes the CI summary line.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S19: web composer send when idle

- Status: todo
- Files: `src/chat/Composer.tsx`, `src/chat/QueueStrip.tsx`, `src/chat/Composer.test.tsx`
- Verify: `npx vitest run src/chat/Composer.test.tsx src/layout/designRules.test.ts && npx tsc -b && npm run lint`
- Verified head: none

#### Requirement

User scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Goal G2 (README), verbatim: "each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool."

Design D16, verbatim: "agents-web `Composer.tsx` gains a "Send when idle" toggle (off by default) beside the target select; when on, `postMessage` sends `priority: "idle"`, when off it sends no `priority` (the server default), so the existing `{ text }` call shapes stay. `QueueStrip.tsx` adds "waits until idle" to a queued `idle` message's detail. The vendored orchestrator spec and `schema.d.ts` are re-synced first."

Scope (agents-web): `src/chat/Composer.tsx`, `src/chat/QueueStrip.tsx`, `src/chat/Composer.test.tsx` (the composer and queue strip tests live there).

#### Acceptance conditions

- ac1: with "Send when idle" on, Enter posts { text, priority: "idle" } (with target_agent_id when an agent is chosen) (new) [evidence: command:npx vitest run src/chat/Composer.test.tsx -t "send when idle posts idle priority"]
- ac2: the toggle is off by default and a send posts { text } with no priority, so the existing call-shape tests stay unchanged [evidence: command:npx vitest run src/chat/Composer.test.tsx -t "enter sends to any agent|sends to chosen agent|send when idle is off by default"]
- ac3: the queue strip shows "waits until idle" for a queued idle message and nothing new for an immediate one (new) [evidence: command:npx vitest run src/chat/Composer.test.tsx -t "queue strip shows waits until idle"]
- ac4: the design rules and nomenclature guards stay green [evidence: test:src/layout/designRules.test.ts]
- ac5: targeted tests, type-check and lint pass [evidence: command:npx vitest run src/chat/Composer.test.tsx src/layout/designRules.test.ts && npx tsc -b && npm run lint]

#### Files

- `src/chat/Composer.tsx`
- `src/chat/QueueStrip.tsx`
- `src/chat/Composer.test.tsx`

#### Interfaces

- `Composer`: a MUI toggle (Switch or Checkbox with label "Send when idle", `aria-label` "Send when idle") beside the target `Select`; state resets to off on session change; body `chosen === ANY ? { text } : { text, target_agent_id }` plus `priority: 'idle'` only when on.
- `QueueStrip.detail(m)`: for `m.status === 'queued' && m.priority === 'idle'` the detail includes "waits until idle" (combined with the attempt text when both apply).

#### Expected outcome

A user can send a message that waits for the agent to finish its turn; by default messages reach a busy agent at once, and the queue shows which messages are waiting on purpose.

#### Steps

- Read `src/chat/Composer.tsx`, `src/chat/QueueStrip.tsx`, `src/chat/Composer.test.tsx`, `src/api/client.ts` (`postMessage`, `PostMessage`), `src/layout/designRules.ts` and `src/theme.ts` in one pass.
- Red: add the tests named in ac1 to ac3; run `npx vitest run src/chat/Composer.test.tsx`; expect them to fail.
- Green: add the toggle and the queue strip detail; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- Design rules: no colour literals outside `theme.ts`, no arrows or decorative Unicode, fontWeight 400/500.
- The full web suite has load-dependent timeouts (PresetForm, ScheduleForm, Endpoints, FiltersEditor); run only the files in the verify.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun; a named load-dependent flake becomes a reported finding, not a silent rerun (retro).

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S20: wrapper merge stop gate

- Status: todo
- Files: `src/claude_code_wrapper/router.py`, `src/claude_code_wrapper/session.py`, `src/claude_code_wrapper/config.py`, `README.md`, `MEMORY.md`, `tests/test_turn_merge_stop.py`
- Verify: `uv run pytest tests/test_turn_merge_stop.py tests/test_turn_merge.py tests/test_turn_merge_guards.py tests/test_stop_gate.py tests/test_command_turn_resume.py tests/test_session_turns.py tests/test_shutdown_turn_resume.py tests/test_readme_config.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

Goal G3 (README), verbatim: "a message delivered mid-turn never wedges the session: the running turn still ends on its Stop, and the message is linked to the turn that answered it (hop guard and delivery verifier included)."

Design D6, verbatim: "At a Stop that targets the running turn, after the onStop gate allowed it, when the turn holds a merge with no `absorbed_at`: the relay answers allow, the turn stays running and busy (`turn_deferred` with reason `merge_pending` and the pending `merge_ids`), and the wrapper waits up to `sessions.merge.settle_seconds` (default 15, my call) for the merge markers. Claude Code sends input still queued at the turn's end without another key press (docs A2), so the queued prompt starts and its own Stop (same turn marker) completes the turn normally. If the bound expires first, the wrapper completes the turn from the deferred Stop's payload (`last_assistant_message`, usage) and leaves the unseen merges with `absorbed_at: null`. Order inside `_stop_gate`: onStop block wins, then the hook or background defer, then `merge_pending`, then the slash epic's command hold; queued commands stay queued until the turn really completes. A Stop with every merge confirmed completes as today. Compaction (interrogate 9): the settle wait pauses from a PreCompact hook until the `compact_boundary` signal (both already observed by the router), for at most `sessions.merge.compact_settle_seconds` (default 600, the slash epic's compact timeout), so an end-of-turn auto-compaction cannot make the bound expire and orphan the merged prompt."

Design D7, verbatim: "`POST /interrupt` ends the running turn `interrupted` as today, its merged messages with it; the merges never seen stay `absorbed_at: null` and the wrapper never resends them. Claude Code sends queued input right after Esc (docs B1); if it does so, the run that follows surfaces through the existing ready-state Stop path (`stop_target` while ready makes an `origin="agent"` record), so the session cannot wedge. The second ESC stays conditional on a missing interrupt line, so it does not hit the auto-sent prompt or open the rewind menu (docs B3)."

Design D5 (combined prompts), verbatim: "`UserPrompt.turn_marker` is the last turn marker of the text, not the first (interrogate 4): a merge left queued after the settle bound or an interrupt and combined with the next turn's paste must not name the old turn, or the new turn's Stop is dropped as stale (the 0.3.3 wedge)."

Design D4 (order), verbatim: "A Stop during the paste delay therefore already sees the pending merge (D6), and concurrent merges cannot pass the cap."

Design D11 (gate), verbatim: "Gate (interrogate 6, builder Q4, my call): every other task depends on the probe, directly or through its chain; epic-run stops after it, the orchestrator reads the consequences table (rows D2-D7, D9, D10, D13, D14, D17, D18) and amends before any other task starts. P1, P2, P4 and P5 must be observed, never `not run`; P4 also records input combined across a turn end and across an Esc; P6 captures the real dialog footers, their dismissal output and a key that safely clears unsent input with a dialog open; P7 records how long an end-of-turn auto-compaction with queued input takes; the Stop and UserPromptSubmit payloads are captured beside the transcript lines, so wrapper-merge-stop-gate replays both through the Router."

Design anti-goal, verbatim: "A Stop that never completes the running turn because a merged paste was never seen: the defer is bounded (D6)."

Design Non-goals, verbatim: "No change to `limits.turn_max_seconds`: it keeps counting from the first submit (wrapper MEMORY 2026-10-28), so merged messages do not extend a bounded turn."

Scope (claude-code-wrapper): `router.py` (`_stop_gate` merge-pending leg and order, the settle timer and its pause between PreCompact and `compact_boundary`, completion from the stored Stop payload), `session.py` (interrupt with merges, timer cancellation when the turn ends), `config.py` (`sessions.merge.settle_seconds`, `sessions.merge.compact_settle_seconds`), `README.md` (turn lifecycle with merges, interrupt, compaction pause), `MEMORY.md` (dated entry on the merge model: marker rule, bounded defer, interrupt), `tests/test_turn_merge_stop.py` (new, including the replay of the probe's captured lines and hook payloads).

#### Acceptance conditions

- ac1: a Stop for the running turn while a merge has no absorbed_at answers allow, keeps the turn running and the session busy, and emits turn_deferred with reason merge_pending and the pending merge_ids (new) [evidence: test:tests/test_turn_merge_stop.py::test_stop_with_unconfirmed_merge_defers]
- ac2: a Stop that arrives while a merge is still in its paste delay (entry recorded, CR not yet written) defers the same way (new) [evidence: test:tests/test_turn_merge_stop.py::test_stop_during_paste_delay_defers]
- ac3: when the merged prompt then shows in the transcript and its Stop arrives, the same turn completes once, with final_text from that later Stop (new) [evidence: test:tests/test_turn_merge_stop.py::test_deferred_turn_completes_on_the_merged_prompt_stop]
- ac4: when merge.settle_seconds passes with the merge unseen, the turn completes once from the deferred Stop's last_assistant_message and usage, the merge keeps absorbed_at null and the session is ready (new) [evidence: test:tests/test_turn_merge_stop.py::test_settle_bound_completes_the_turn]
- ac5: the settle wait pauses from a PreCompact hook until compact_boundary and resumes after it, and a compaction longer than merge.compact_settle_seconds ends the pause (new) [evidence: test:tests/test_turn_merge_stop.py::test_settle_wait_pauses_during_compaction]
- ac6: after the settle bound completed a turn with a merge unseen, a combined prompt carrying that merge's markers and the next turn's marker completes the next turn on its own Stop and the session is ready (new) [evidence: test:tests/test_turn_merge_stop.py::test_combined_prompt_after_settle_bound_completes_the_new_turn]
- ac7: the settle wait ends without a second completion when the turn ends another way first (interrupt, turn_max_seconds timeout, claude exit) (new) [evidence: test:tests/test_turn_merge_stop.py::test_settle_wait_ends_when_turn_ends_otherwise]
- ac8: gate order: an onStop block wins over merge_pending; with client commands queued and a merge pending, the commands stay queued until the turn completes and then run (slash D9) (new) [evidence: test:tests/test_turn_merge_stop.py::test_gate_order_block_then_merge_then_commands]
- ac9: an interrupt of a turn with merges ends it interrupted, unseen merges keep absorbed_at null, nothing is resent, a later Stop of a prompt Claude sent after the Esc makes an origin agent record, and the next POST /turns answers 202 (new) [evidence: test:tests/test_turn_merge_stop.py::test_interrupt_with_merges_never_wedges]
- ac10: with queued input at the interrupt the second ESC is sent only when no interrupt line arrived within interrupt_settle_seconds (new) [evidence: test:tests/test_turn_merge_stop.py::test_second_esc_only_without_interrupt_line]
- ac11: with the fake in queue mode, a message pasted near the end of a text-only turn ends up in exactly one completed turn whose record lists the merge as absorbed (new) [evidence: test:tests/test_turn_merge_stop.py::test_turn_end_queue_end_to_end]
- ac12: the probe's captured transcript lines and hook payloads, replayed through the Router in arrival order with their turn and merge ids, end in exactly one completed turn per probed turn, every captured merge absorbed and the session ready (new) [evidence: test:tests/test_turn_merge_stop.py::test_probe_capture_replays_to_one_completed_turn]
- ac13: turn_max_seconds still counts from the first submit with merges in the turn (new) [evidence: test:tests/test_turn_merge_stop.py::test_turn_max_seconds_counts_from_first_submit_with_merges]
- ac14: README documents the merge lifecycle, sessions.merge.settle_seconds and compact_settle_seconds; MEMORY.md has the dated merge entry [evidence: command:grep -q 'settle_seconds' README.md && grep -q 'compact_settle_seconds' README.md && grep -q 'merge_pending' README.md && grep -q 'ccw merge' MEMORY.md && uv run pytest tests/test_readme_config.py]
- ac15: targeted suites and lint pass [evidence: command:uv run pytest tests/test_turn_merge_stop.py tests/test_turn_merge.py tests/test_turn_merge_guards.py tests/test_stop_gate.py tests/test_command_turn_resume.py tests/test_session_turns.py tests/test_shutdown_turn_resume.py tests/test_readme_config.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `MEMORY.md`
- `tests/test_turn_merge_stop.py`

#### Interfaces

- `config.py`: `sessions.merge.settle_seconds: float = 15.0` (`ge=0`); `sessions.merge.compact_settle_seconds: float = 600.0` (`ge=0`), the most the settle wait pauses between a PreCompact hook and the `compact_boundary` signal.
- Replay input: `tests/fixtures/transcripts/midturn-probe.jsonl` and `tests/fixtures/transcripts/midturn-probe-hooks.jsonl` (task wrapper-midturn-probe), fed to the Router in arrival order through the transcript tail and the hook relay entry points the router tests already use.
- Event `turn_deferred` gains reason `merge_pending` and a `merge_ids: list[str]` field (other reasons unchanged).
- `_stop_gate` order: onStop block -> hook or background defer -> `merge_pending` -> slash command hold -> complete.
- Turn record: merges never seen keep `absorbed_at: null` after completion or interrupt; nothing else in the record changes shape.

#### Expected outcome

A turn that absorbed messages still completes exactly once: on the Stop that follows the last merged prompt, or at the latest `merge.settle_seconds` after a Stop when a paste was never taken. An interrupt keeps its contract and never leaves the session busy.

#### Steps

- Read `router.py` (`_on_stop`, `_stop_gate`, `_emit_deferred`, `_after_turn`), `session.py` (`stop_target`, `complete`, `_end_turn`, `interrupt`, `_run_interrupt`, `on_interrupted`, `_watch_turn`), `config.py`, `tests/test_stop_gate.py`, `tests/test_command_turn_resume.py`, `tests/test_turn_merge.py`, the fake's queue mode and `docs/claude-midturn-input.md` (P2, P5) in one pass.
- Red: write `tests/test_turn_merge_stop.py` with every test named in the acceptance conditions; run `uv run pytest tests/test_turn_merge_stop.py`; expect them to fail.
- Green: implement the merge-pending leg, the bounded wait, the completion from the stored payload, the interrupt rule, README and MEMORY; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- Depends on probe P2 (one Stop or two at a turn end with queued input), P4 (combined input), P5 (Esc with queued input) and P7 (compaction). If the consequences table contradicts D5, D6 or D7, the orchestrator amends this task before it starts.
- The merge entry exists before the paste (wrapper-immediate-turn-merge), so a Stop during the paste delay must defer on it; pin that here.
- The deferred Stop's payload and usage must be kept so the bound can complete the turn honestly; the usage accumulator keeps counting if the merged prompt runs.
- `turn_max_seconds` and `turn_stall_seconds` keep their meaning; the settle timer is separate and cancelled with the turn.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design

### S21: wrapper peer priority

- Status: todo
- Files: `src/claude_code_wrapper/mcp_server.py`, `src/claude_code_wrapper/peer_service.py`, `src/claude_code_wrapper/peer_client.py`, `src/claude_code_wrapper/peer_inbox.py`, `README.md`, `tests/test_peer_priority.py`
- Verify: `uv run pytest tests/test_peer_priority.py tests/test_peer_inbox.py tests/test_peer_inbox_outcomes.py tests/test_mcp_peers.py tests/test_peer_service.py tests/test_peer_client.py tests/test_peers_readme.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

User scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Goal G2 (README), verbatim: "each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool."

Design D17, verbatim: "`send_message` gains `priority` (`immediate` default, `idle`), carried on the peer wire to the receiving instance; the receiver's `PeerInbox` delivers an `immediate` item while the session is busy through `SessionRouter.submit_turn(priority="immediate")` (a merge), and an `idle` item as today. Refusals (D4 409s, 429) keep the item queued for the next state change. `notify_when_idle` is unchanged and reports `delivered` once the handling turn, merged or not, is terminal; several items may map to one turn."

Scope (claude-code-wrapper): `mcp_server.py` (`send_message` schema, argument check, description), `peer_service.py` (send and receive carry `priority`), `peer_client.py` (wire model field), `peer_inbox.py` (`InboxItem.priority`, the immediate delivery path, several items per turn for `notify_when_idle`), `README.md` (peer tool and wire docs), `tests/test_peer_priority.py` (new).

#### Acceptance conditions

- ac1: send_message accepts priority immediate or idle, defaults to immediate, and answers invalid arguments for any other value (new) [evidence: test:tests/test_peer_priority.py::test_send_message_priority_argument]
- ac2: the priority travels on the peer wire and reaches the receiving inbox item (new) [evidence: test:tests/test_peer_priority.py::test_priority_travels_on_the_peer_wire]
- ac3: an immediate item for a busy session is delivered at once as a merge into the running turn; peer_message_delivered carries that turn id (new) [evidence: test:tests/test_peer_priority.py::test_immediate_peer_message_merges_into_busy_turn]
- ac4: an idle item waits for a ready session as today (new) [evidence: test:tests/test_peer_priority.py::test_idle_peer_message_waits_for_ready]
- ac5: an immediate item refused with command_active, dialog_open, interrupting or merge_queue_full stays queued and is delivered after the next state change (new) [evidence: test:tests/test_peer_priority.py::test_refused_immediate_item_stays_queued]
- ac6: with notify_when_idle, each of two items merged into one turn gets its delivered outcome once that turn is terminal (new) [evidence: test:tests/test_peer_priority.py::test_notify_when_idle_for_items_merged_into_one_turn]
- ac7: the peer inbox, MCP and README guards stay green unchanged [evidence: command:uv run pytest tests/test_peer_inbox.py tests/test_peer_inbox_outcomes.py tests/test_mcp_peers.py tests/test_peers_readme.py]
- ac8: targeted suites and lint pass [evidence: command:uv run pytest tests/test_peer_priority.py tests/test_peer_inbox.py tests/test_peer_inbox_outcomes.py tests/test_mcp_peers.py tests/test_peer_service.py tests/test_peer_client.py tests/test_peers_readme.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/mcp_server.py`
- `src/claude_code_wrapper/peer_service.py`
- `src/claude_code_wrapper/peer_client.py`
- `src/claude_code_wrapper/peer_inbox.py`
- `README.md`
- `tests/test_peer_priority.py`

#### Interfaces

- MCP `send_message` input schema: `{"to", "message", "notify_when_idle": bool, "priority": {"type": "string", "enum": ["immediate", "idle"]}}`; absent = `immediate`; the description names both values.
- `PeerTools.send(caller_session, to, message, notify_when_idle, priority="immediate")`; the wire body model in `peer_client.py` gains `priority: Literal["immediate", "idle"] = "immediate"`.
- `peer_inbox.InboxItem.priority`; the inbox maps `turn_id -> list[InboxItem]` for outcomes.
- Delivery: `router.submit_turn(frame(item), origin="peer", metadata={"peer": ...}, priority=item.priority)`.

#### Expected outcome

A hive peer's message reaches a busy session mid-turn at once by default, and a sender can still ask for wait-until-idle.

#### Steps

- Read `mcp_server.py` (`_peer_tools`, `_call_peers`), `peer_service.py` (`send`, `_send`, the receive route), `peer_client.py`, `peer_inbox.py` (`put`, `_session_ready`, `_attempt`, `turn_finished`), `tests/test_peer_inbox.py`, `tests/test_peer_inbox_outcomes.py`, `tests/test_mcp_peers.py`, `tests/test_peers_readme.py` and the merge API from task wrapper-immediate-turn-merge in one pass.
- Red: write `tests/test_peer_priority.py` with every test named ac1 to ac6; run `uv run pytest tests/test_peer_priority.py`; expect them to fail.
- Green: implement the field end to end and the immediate delivery path, README; run the task's verify; expect all passed. Quote the summary line.

#### Notes

- FIFO among items stays per priority: an immediate item may overtake a queued idle item (design D13 and Q5 apply to peers too); idle items keep their order.
- Rate limits, inbox bounds and dedupe are unchanged (per-task security check, retro: this tool sends on a caller's behalf).
- `notify_when_idle` is about reporting, `priority` about delivery; keep them independent.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

### S22: wrapper release 0.5.0

- Status: todo
- Files: `pyproject.toml`, `uv.lock`, `src/claude_code_wrapper/__init__.py`, `tests/test_packaging.py`
- Verify: `uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: none

#### Requirement

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.7.0 and agents-common 0.5.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer). [...] The wrapper is pinned by its release tag, cut before the orchestrator task (retro file-editor-with-tabs-and-hi: Harbor prunes sha7 tags)."

Design Constraints, verbatim: "This epic therefore takes migration 0014, wrapper 0.5.0, plugins 0.7.0 (negotiated 2026-10-29, mx-34 #469/#470); when a number is taken at build time the task takes the next free one and the orchestrator amends its `files`."

Scope (claude-code-wrapper): `pyproject.toml` and `src/claude_code_wrapper/__init__.py` (0.4.1 from the slash epic's fix round to 0.5.0), `uv.lock`, `tests/test_packaging.py` (the version pin, if it names the version).

#### Acceptance conditions

- ac1: the version is 0.5.0 in pyproject and the package, and the branch contains the v0.4.1 tag commit [evidence: command:grep -q '^version = "0.5.0"' pyproject.toml && grep -q '__version__ = "0.5.0"' src/claude_code_wrapper/__init__.py && git merge-base --is-ancestor v0.4.1 HEAD]
- ac2: the built wheel installs and reports its version [evidence: test:tests/test_packaging.py::test_wheel_installs_and_ccw_version]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.5.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.5.0)"]
- ac4: packaging tests and lint pass [evidence: command:uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

#### Interfaces

- Version string `0.5.0` in `pyproject.toml` `[project].version` and `claude_code_wrapper.__version__`; `uv.lock` regenerated with `uv lock`.

#### Expected outcome

A wrapper release carrying the mid-turn merge, the bounded Stop defer, the paste hygiene and the peer priority exists for the orchestrator to pin by tag.

#### Steps

- Read `pyproject.toml`, `src/claude_code_wrapper/__init__.py`, `tests/test_packaging.py` and the slash epic's wrapper-release-0-4-1 task in one pass.
- Bump the version, run `uv lock`; this is a version bump with no behaviour change (TDD exception: dependency or version bump), so there is no red step; if `tests/test_packaging.py` names the version, update that pin (no longer accurate after the bump).
- Run the task's verify; expect all passed. Quote the summary line.

#### Notes

- The tag is pushed by the orchestrator session after the PR merges green; ac3 is checked by it, not by the implementer or reviewer.
- If 0.5.0 is taken at build time, take the next free minor and report it so the orchestrator amends this task and orch-wrapper-pin-0-5-0.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: agents-common renumbered 0.4.0 -> 0.5.0: the slash fix round takes v0.4.0 (mx-34 #446, #453)

- 2026-10-29 amended: slash baseline is wrapper 0.4.1 (fix round); immediate delivery still releases 0.5.0

- 2026-10-29 amended: design quotes follow the design: migration 0014, plugins 0.7.0 (mx-34 #469/#470)

### S23: orch wrapper pin 0.5.0

- Status: todo
- Files: `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `e2e/agent-test.scenario.json`, `README.md`, `tests/test_fake_wrapper_contract.py`, `tests/e2e/test_e2e_kind.py`
- Verify: `uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint`
- Verified head: none

#### Requirement

Goal G1 (README), verbatim: "a message sent to a busy session reaches its leader through the PTY at once, mid-turn, and Claude Code queues it internally; by default no message waits for the leader to go idle."

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.7.0 and agents-common 0.5.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer). The orchestrator pins the wrapper merge commit of v0.5.0 (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images) with a real-wrapper contract case and a kind e2e case for a merged message, then the plugins ref v0.7.0; the connector pins agents-common v0.5.0. The wrapper is pinned by its release tag, cut before the orchestrator task (retro file-editor-with-tabs-and-hi: Harbor prunes sha7 tags). The agent-test scenario (`e2e/agent-test.scenario.json`) sets `"midturn_input": "queue"`, so the real contract case and the kind e2e prove real delivery (the merge's `absorbed_at` set, the turn completed on the merged prompt's Stop), not the settle-bound fallback (interrogate 8). PR order: Constraints. No agents-helmfile task (Q9)."

Scope (agents-orchestrator): `pyproject.toml` and `uv.lock` (the claude-code-wrapper dev dependency at the v0.5.0 merge commit), `e2e/agent-test.Dockerfile`, `e2e/agent-test.scenario.json` (`"midturn_input": "queue"`), `README.md` (Images), `tests/test_fake_wrapper_contract.py` (remove the real-leg skip of `test_immediate_while_busy_merges`; the real leg asserts the merge absorbed), `tests/e2e/test_e2e_kind.py` (one case: a message posted while the agent is busy joins its running turn and is absorbed).

#### Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit, the v0.5.0 merge commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper takes priority with immediate as its default and its turn record has merged [evidence: command:uv run --frozen python -c "from claude_code_wrapper.api.turns import TurnRequest; from claude_code_wrapper.turns import TurnRecord; assert TurnRequest(text='x').priority == 'immediate'; assert 'merged' in TurnRecord.model_fields"]
- ac4: the agent-test scenario puts the fake claude in queue mode, so mid-turn input is queued like Claude Code instead of dropped (new) [evidence: command:python3 -c "import json; assert json.load(open('e2e/agent-test.scenario.json')).get('midturn_input') == 'queue'"]
- ac5: (CI or a Docker host) the real contract leg passes with the merge case enabled, and on the real leg the merged entry has absorbed_at set (new) [evidence: command:mise run test:integration]
- ac6: (CI kind job) the kind e2e passes, including a case where a chat message posted while the agent is busy reaches it mid-turn, both messages link to the one turn, its record lists the merge with absorbed_at set and the turn completes on the merged prompt's Stop, not the settle bound (new) [evidence: command:mise run test:e2e]
- ac7: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `e2e/agent-test.scenario.json`
- `README.md`
- `tests/test_fake_wrapper_contract.py`
- `tests/e2e/test_e2e_kind.py`

#### Interfaces

- Pin form as the slash epic's orch-wrapper-pin-0-4-0: the `claude-code-wrapper` dev dependency `@ git+https://github.com/szymonrychu/claude-code-wrapper@<v0.5.0 merge sha>`, the Dockerfile's `ARG`/image reference, README Images row.
- `e2e/agent-test.scenario.json`: top-level `"midturn_input": "queue"` (wrapper-fake-claude-queue), so the fake claude in the agent-test image queues mid-turn input like Claude Code instead of dropping it; the contract real leg and the kind e2e both use this scenario.
- e2e case in `tests/e2e/test_e2e_kind.py`: post a message whose scenario keeps the agent busy (the e2e fake claude's slow prompt), then post a second message; assert the second is `sent` with the first's `turn_id`, the turn record lists its merge with `absorbed_at` set, and the turn completes on the merged prompt's Stop (no `turn_deferred` with reason `merge_pending` left unresolved by the settle bound).

#### Expected outcome

The orchestrator runs against a wrapper that merges mid-turn messages, and the real wrapper and a kind cluster prove a message to a busy agent is delivered into its running turn.

#### Steps

- Read `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `e2e/agent-test.config.yaml`, the README Images section, `tests/test_images.py`, `tests/test_fake_wrapper_contract.py`, `tests/fakes/real_wrapper.py`, `tests/e2e/test_e2e_kind.py` and the slash epic's orch-wrapper-pin-0-4-0 task in one pass.
- Red: remove the real-leg skip and add the e2e case; run `uv run --frozen python -c` of ac3; expect it to fail on the 0.4.1 pin.
- Green: move the pin (`uv lock`), Dockerfile and README; run the task's verify; expect all passed. Quote the summary line; the reviewer quotes the CI integration and e2e job summaries.

#### Notes

- Depends on the v0.5.0 tag on origin (wrapper-release-0-5-0 ac3, pushed by the orchestrator session); pin the release, never a branch sha (Harbor prunes sha7 tags).
- Headline promise (retro, recurring): the e2e case is the end-to-end proof of G1; it must post to a really busy agent, not to an idle one.
- The fake claude drops mid-turn input unless the scenario sets `"midturn_input": "queue"`; this task sets it, so the real contract case and the kind e2e prove real delivery (the merge absorbed), not the settle-bound fallback (interrogate 8). Every existing e2e case runs with the new key; read any that changes behaviour and report it.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design

- 2026-10-29 amended: agents-common renumbered 0.4.0 -> 0.5.0: the slash fix round takes v0.4.0 (mx-34 #446, #453)

- 2026-10-29 amended: D19 quote follows the design: plugins 0.7.0 (mx-34 #469/#470)

### S24: orch plugins pin 0.7.0

- Status: todo
- Files: `src/agents_orchestrator/settings.py`, `pyproject.toml`, `uv.lock`, `README.md`, `tests/test_settings.py`
- Verify: `uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint`
- Verified head: none

#### Requirement

Design D15, verbatim: "Released as plugins 0.7.0 on top of session-orchestration-mcp's 0.6.0; the orchestrator pins it."

Design D19, verbatim: "The orchestrator pins the wrapper merge commit of v0.5.0 [...] then the plugins ref v0.7.0".

Scope (agents-orchestrator): `src/agents_orchestrator/settings.py` (`ORCH_ANY_MCP_PLUGINS_REF` default v0.6.0 from session-orchestration-mcp, the live baseline, to v0.7.0), `pyproject.toml` and `uv.lock` (the `any-mcp-tatara-orchestrator` dev dependency), `README.md` (settings table), `tests/test_settings.py` (the default pin, no longer accurate after the bump).

#### Acceptance conditions

- ac1: the settings default is v0.7.0 (updated, named) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.7.0 default and names no older plugins tag [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.7.0` |' README.md && test "$(grep -oE 'plugins release tag \(`v[0-9.]+`\)' README.md | grep -vc 'v0.7.0')" = 0]
- ac4: the pinned orchestrator plugin's session_send schema carries priority [evidence: command:grep -rq '"priority"' "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
- ac5: settings, images and on-start suites and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint]

#### Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_settings.py`

#### Interfaces

- `settings.Settings.any_mcp_plugins_ref` default `"v0.7.0"`; dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.7.0#subdirectory=orchestration/orchestrator` (the existing form).

#### Expected outcome

Superleaders get the session_send tool that offers immediate or idle delivery.

#### Steps

- Read `settings.py`, `pyproject.toml`, the README settings table, `tests/test_settings.py`, `tests/test_images.py` and hive-decoupling's orch-plugins-pin-0-4-0 task in one pass.
- Version pin bump with no behaviour change (TDD exception): update `tests/test_settings.py::test_defaults` (no longer accurate), the default, `uv lock`, README.
- Run the task's verify; expect all passed. Quote the summary line.

#### Notes

- Id kept from an earlier numbering; it pins v0.7.0.
- Depends on the plugins v0.7.0 tag on origin (plugins-release-0-5-0 ac3, pushed by the orchestrator session).
- The helmfile value of `ORCH_ANY_MCP_PLUGINS_REF` stays with the gate's deploy decision (Q9).
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: plugins pin renumbered v0.6.0 to v0.7.0 (mx-34 #469/#470): the baseline pin is session-orchestration-mcp's v0.6.0

- 2026-10-29 amended: fix: baseline pin is v0.6.0 (session-orchestration-mcp), the bump goes to v0.7.0

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
