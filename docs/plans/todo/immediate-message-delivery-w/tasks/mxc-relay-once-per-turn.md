---
title: mxc relay once per turn
status: todo
repo: agents-matrix-connector
value: a Matrix room gets one reply when several of its messages were answered by one agent turn
files: [pyproject.toml, uv.lock, src/agents_matrix_connector/tracker.py, tests/test_tracker.py, MEMORY.md]
verify: "uv run ruff check . && uv run ruff format --check . && uv run pytest tests/test_tracker.py"
depends_on: [common-release-0-4-0]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc relay once per turn

## Requirement

Goal G4 (README), verbatim: "Matrix chat messages in a room whose run is in progress are delivered at once, and an answer shared by merged messages is relayed to the room once."

Design D18 (tracker part), verbatim: "The tracker relays a completed turn's final text once per turn: among in-progress runs whose messages link to the same `turn_id`, the run with the lowest id relays and the others finish `handled` with reason `merged` and no reply. agents-common `Message.turn_id` (new, released 0.4.0, connector pin moved) carries the link; the fake orchestrator can complete one turn for several messages."

Design anti-goal, verbatim: "The same final answer relayed twice to a Matrix room (D18)."

Scope (agents-matrix-connector): `pyproject.toml` and `uv.lock` (agents-common v0.3.0 to v0.4.0, both the dependency and the testing extra), `src/agents_matrix_connector/tracker.py` (the once-per-turn rule), `tests/test_tracker.py`, `MEMORY.md`.

## Acceptance conditions

- ac1: the connector pins agents-common v0.4.0 in both dependency lines and uv.lock, and Message has turn_id [evidence: command:test "$(grep -c 'agents-common@v0.4.0' pyproject.toml)" = 2 && ! grep -q 'agents-common@v0.3.0' pyproject.toml && uv run --frozen python -c "from agents_common.orchestrator import Message; assert 'turn_id' in Message.model_fields"]
- ac2: (CI or a Docker host) two in-progress runs of one room whose messages link to the same completed turn produce exactly one reply, from the lower run id; the other run finishes handled with reason merged and sends nothing (new) [evidence: test:tests/test_tracker.py::test_merged_turn_relayed_once]
- ac3: (CI or a Docker host) runs whose messages link to different turns each relay their own answer as today (new) [evidence: test:tests/test_tracker.py::test_distinct_turns_each_relayed]
- ac4: (CI or a Docker host) the existing tracker cases pass unchanged [evidence: command:uv run pytest tests/test_tracker.py]
- ac5: MEMORY.md has a dated entry on relaying a merged turn once and why [evidence: command:grep -q 'merged' MEMORY.md]
- ac6: lint passes and the tracker suite runs [evidence: command:uv run ruff check . && uv run ruff format --check . && uv run pytest tests/test_tracker.py]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/agents_matrix_connector/tracker.py`
- `tests/test_tracker.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
