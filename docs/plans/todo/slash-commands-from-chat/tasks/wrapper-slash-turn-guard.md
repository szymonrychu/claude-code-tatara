---
title: wrapper slash turn guard
status: todo
repo: claude-code-wrapper
value: "a slash line can never be typed as a turn again, so /reload-plugins cannot hang a session"
files: [src/claude_code_wrapper/session.py, src/claude_code_wrapper/router.py, src/claude_code_wrapper/api/turns.py, src/claude_code_wrapper/manager.py, README.md, tests/test_session_turns.py, tests/test_api_turns.py, tests/test_manager.py]
verify: "uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_manager.py tests/test_readme_api.py tests/test_submit_busy_first.py --deselect tests/test_manager.py::test_shutdown_stops_all && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-command-args]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper slash turn guard

## Requirement

Goal G3 (README), verbatim: "Sending /reload-plugins (the reported case) no longer hangs the session; a regression test pins it." User decision: "A regression test must pin the reported case: sending '/reload-plugins' from chat never leaves the session busy (wrapper and orchestrator level)." This task is the wrapper-level pin.

Design D3, verbatim: "`Session.submit` raises `TurnRejected("slash_command")` for slash text (D2 rule) before reserving the slot or typing, for every origin (client, peer, initial, agent). `SessionRouter.submit_turn` checks the same rule first, so no onTurn hook fires and no file is written for a refused turn. `POST /v1/sessions/{id}/turns` maps it to 422 `slash_command` with the message "slash commands go to POST /v1/sessions/{id}/commands". `SessionManager._initial_turn` routes a slash initial prompt to `router.request_command(name, args, origin="client")` (refusals are reported as today's `initial_turn_rejected` error event). Peer turns are framed (`peer_inbox.py` `frame(item)`), so a peer "/x" is prose by construction. This is the regression pin for the reported hang."

Design D2, verbatim: "Slash text mirrors Claude Code's own parser (claude 2.1.304 binary, interrogate item 2). After leading whitespace the text starts with `/`. A trailing agents-common run marker (`<!-- agents-<kind>:<id> -->`, `agents_common.runs.marker`, posted as `text\n\nmarker` by `runs.py:_post_once`) is removed first (interrogate item 8). The name is the text after the `/` up to the first whitespace (space, tab or newline); the args are the rest, stripped, and may span lines. The text is a command when the name is empty (`/`, `/ is root`: claude answers "Commands are in the form `/command [args]`" and calls no model; the wrapper refuses an empty name 422 `invalid_command`) or matches `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, with no length cap (`/tmp`, `/_x`, a 100-character name: claude runs it or answers "Unknown command", again with no model call, so a bare `/tmp` fails `unknown_command`). A name with any other character is prose (`/workdir/foo is broken`, `/etc/hosts`, `//x`, `/notes.txt`): claude sends it to the model as a prompt. The orchestrator classifies with this rule and the wrapper's turn guard (D3) refuses with the same rule, both pinned by one shared case table, so a text that claude would parse as a command can never be typed as a turn. The path-like prose leg is confirmed by a real-binary probe in task wrapper-command-signals; a result that contradicts this rule is reported back and amends both parser tasks, never worked around."

Interrogate item 2 (interrogate.md), verbatim: "Classification must match Claude Code's own parser (B, critical). D2 types `/`, `/ is root`, `/_x` and names over 64 chars as turns; claude runs no model call for them, so no Stop and the session hangs. Mirror the binary: name = text up to the first whitespace, empty name is `invalid_command` (claude: "Commands are in the form `/command [args]`"), unknown-command regex `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap. Fix wrapper-slash-turn-guard ac3 and orch-slash-parser ac2. Path-like prose (`/workdir/foo is broken`) must be pinned either way after a probe."

User decision (builder check), verbatim: "a bare '/word' message such as '/tmp' is a command that fails unknown_command, while '/etc/hosts'-like paths stay prose (per the parser rule of item 2, after the probe)."

Scope (claude-code-wrapper): `session.py` (the D2 rule as one shared helper, the guard in `Session.submit`), `router.py` (`submit_turn` checks the helper before onTurn), `api/turns.py` (`_REJECT_STATUS["slash_command"] = 422`, its text), `manager.py` (`_initial_turn` slash branch; an empty name goes to `request_command` too and is refused `invalid_command`, reported as `initial_turn_rejected`), `README.md` (Errors row `slash_command`; the turns endpoint notes that slash text is refused and goes to `/commands`). The guard's case table is the same as orch-slash-parser's (`tests/test_slash.py` of agents-orchestrator), case for case.

## Acceptance conditions

- ac1: regression pin: POST /turns {text: "/reload-plugins"} answers 422 slash_command, fake-inputs.jsonl stays empty, the session stays ready, and the next POST /turns with prose answers 202 (new) [evidence: test:tests/test_api_turns.py::test_slash_text_turn_is_refused_not_typed]
- ac2: Session.submit raises TurnRejected("slash_command") for slash text with each origin client, peer, initial and agent, leaves the state ready and writes nothing to the PTY (new) [evidence: test:tests/test_session_turns.py::test_submit_refuses_slash_text_for_every_origin]
- ac3: "/", "/ is root", "/_x", "/tmp", a 100-character name, "/x a\nb" and "/review-pr 12\n\n<!-- agents-webhook:42 -->" are refused slash_command, as claude's parser would run them as commands (new) [evidence: test:tests/test_session_turns.py::test_slash_rule_matches_claude_parser]
- ac4: "/workdir/foo is broken", "/etc/hosts", "//x", "/notes.txt" and prose mentioning "/compact" mid-sentence are accepted as turns (new) [evidence: test:tests/test_session_turns.py::test_slash_rule_leaves_paths_and_prose]
- ac5: a refused slash turn fires no onTurn hook and writes no turn file (new) [evidence: test:tests/test_api_turns.py::test_slash_turn_fires_no_on_turn]
- ac6: an initial prompt "/reload-plugins" (client allowlist ["*"]) runs as a client command that completes, no turn record is created and the session ends ready (new) [evidence: test:tests/test_manager.py::test_initial_slash_prompt_runs_as_command]
- ac7: an initial slash prompt the allowlist refuses, or one with an empty name ("/ is root"), emits error initial_turn_rejected and the session stays ready (new) [evidence: test:tests/test_manager.py::test_initial_slash_prompt_refused_is_reported]
- ac8: the README Errors table lists slash_command [evidence: command:grep -q '^| `slash_command`' README.md]
- ac9: targeted suites and lint pass [evidence: command:uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_manager.py tests/test_readme_api.py tests/test_submit_busy_first.py --deselect tests/test_manager.py::test_shutdown_stops_all && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/api/turns.py`
- `src/claude_code_wrapper/manager.py`
- `README.md`
- `tests/test_session_turns.py`
- `tests/test_api_turns.py`
- `tests/test_manager.py`

## Interfaces

- One helper for the D2 rule, for example `claude_code_wrapper.session.slash_command(text) -> tuple[str, str] | None` (name, args), used by `Session.submit`, `SessionRouter.submit_turn` and `SessionManager._initial_turn`.
- `TurnRejected("slash_command")`; HTTP 422 envelope code `slash_command`.

## Expected outcome

No origin can type a slash line with a turn marker any more: the reported `/reload-plugins` hang cannot recur through the turns path, and a slash initial prompt runs as a command.

## Steps

- Red: add the six tests (ac1-ac6); run `uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_manager.py --deselect tests/test_manager.py::test_shutdown_stops_all`: they fail (the text is typed as a turn; the API answers 202).
- Green: add the helper and the guards, the 422 mapping, the initial-turn branch and the README rows; run the task's verify: passes. Quote the summary line.

## Notes

- `tests/test_manager.py::test_shutdown_stops_all` fails in this container (PID 1 process group, design Constraints); it is deselected, not changed.
- The guard runs before `check_submittable` side effects and before the slot is reserved (`Session.submit` reserves before the first byte today).
- The probe that defines the hang: a paste "/x\n\n<!-- ccw turn: id -->" runs /x with the marker as `<command-args>` (design Research, probed).
- `peer_inbox.py` needs no change (frames every peer turn); ac2 still covers origin peer at the session level.
- Depends on wrapper-command-args (`request_command(name, args, origin=...)`).

- 2026-10-27 amended: interrogate item 2 (guard mirrors claude's parser; ac3 fixed: /, / is root, /_x, long names are refused, paths stay turns), builder check (/tmp), design D2 revised
