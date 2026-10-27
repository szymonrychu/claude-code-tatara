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

Design D2, verbatim: "Slash text is: after leading whitespace, `/` then a name matching `[A-Za-z0-9][A-Za-z0-9:_.-]{0,63}`, then whitespace or the end of the text. The name is that token; the args are the rest, stripped. [...] Text such as `/workdir/foo is broken` or `/ is root` is prose (the name stops at `/` or is empty)."

Scope (claude-code-wrapper): `session.py` (the D2 rule as one shared helper, the guard in `Session.submit`), `router.py` (`submit_turn` checks the helper before onTurn), `api/turns.py` (`_REJECT_STATUS["slash_command"] = 422`, its text), `manager.py` (`_initial_turn` slash branch), `README.md` (Errors row `slash_command`; the turns endpoint notes that slash text is refused and goes to `/commands`).

## Acceptance conditions

- ac1: regression pin: POST /turns {text: "/reload-plugins"} answers 422 slash_command, fake-inputs.jsonl stays empty, the session stays ready, and the next POST /turns with prose answers 202 (new) [evidence: test:tests/test_api_turns.py::test_slash_text_turn_is_refused_not_typed]
- ac2: Session.submit raises TurnRejected("slash_command") for slash text with each origin client, peer, initial and agent, leaves the state ready and writes nothing to the PTY (new) [evidence: test:tests/test_session_turns.py::test_submit_refuses_slash_text_for_every_origin]
- ac3: text starting with a path ("/workdir/foo is broken"), "/ is root" and prose mentioning "/compact" mid-sentence are accepted as turns (new) [evidence: test:tests/test_session_turns.py::test_slash_rule_leaves_paths_and_prose]
- ac4: a refused slash turn fires no onTurn hook and writes no turn file (new) [evidence: test:tests/test_api_turns.py::test_slash_turn_fires_no_on_turn]
- ac5: an initial prompt "/reload-plugins" (client allowlist ["*"]) runs as a client command that completes, no turn record is created and the session ends ready (new) [evidence: test:tests/test_manager.py::test_initial_slash_prompt_runs_as_command]
- ac6: an initial slash prompt the allowlist refuses emits error initial_turn_rejected and the session stays ready (new) [evidence: test:tests/test_manager.py::test_initial_slash_prompt_refused_is_reported]
- ac7: the README Errors table lists slash_command [evidence: command:grep -q '^| `slash_command`' README.md]
- ac8: targeted suites and lint pass [evidence: command:uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_manager.py tests/test_readme_api.py tests/test_submit_busy_first.py --deselect tests/test_manager.py::test_shutdown_stops_all && uv run ruff check . && uv run ruff format --check .]

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
