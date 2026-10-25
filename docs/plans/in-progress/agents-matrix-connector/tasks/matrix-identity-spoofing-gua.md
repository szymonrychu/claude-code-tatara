---
title: matrix identity spoofing guards
status: done
repo: agents-matrix-connector
value: senders and rooms from other homeservers cannot borrow an allowed facebook id or alias
files: [src/agents_matrix_connector/discovery.py, src/agents_matrix_connector/sync.py, src/agents_matrix_connector/matrix.py, src/agents_matrix_connector/fake_homeserver.py, tests/test_discovery.py, tests/test_sync.py, tests/test_matrix_client.py, README.md]
verify: "uv run --frozen pytest tests/test_discovery.py tests/test_sync.py tests/test_matrix_client.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: 3157bce8df164eac1555b1154adcaabdd19fdb13
points: 3
expected_minutes: 6
expected_tokens: 937864
points_actual: 3
actual_minutes: 10
actual_tokens: 2845183
actual_roles: "impl 9, review 2"
actual_role_tokens: "impl 2677310, review 167873"
---

# matrix identity spoofing guards

## Requirement

Found by the epic security review (2026-10-25). Matrix ids from other homeservers can impersonate an allowed Facebook sender or an allowed room alias when the homeserver federates or the bot auto-joins a remote room (design D5, D6, anti-goal "a stranger on Messenger reaching an agent without an explicit allow rule"). Paths are in code/agents-matrix-connector.

- Facebook id: `discovery.facebook_id` (and every caller, sync.py) derives a `facebook_id` only when the user id fully matches `MATRIX_PUPPET_PATTERN` AND its server part equals the bridge's server, which is the server part of `MATRIX_USER_ID` (mautrix-meta ghosts live on the bot's own homeserver). Use `fullmatch`; `@facebook_<id>:evil.example` yields no facebook id, so `facebook` allow rules never match it (it can still be denied or allowed by its exact `user` id).
- Alias: a room's `alias` (from `m.room.canonical_alias`) is stored only after `GET /_matrix/client/v3/directory/room/{roomAlias}` resolves it to that same `room_id`; otherwise the room's alias is stored as null and logged once as unverified (room id and alias only). Add `MatrixClient.resolve_alias(alias) -> str | None` (404 -> None; same auth, error mapping, redaction and 429 handling as the existing calls) and the matching FakeHomeserver route plus a helper to register aliases. A transport error leaves the previous stored alias unchanged and retries on the next state read.
- README `## Security`: one line each on both guarantees.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: a ghost on another server gets no facebook id and a facebook allow rule does not admit it, while the same id on the bot's server does [evidence: test:tests/test_discovery.py::test_facebook_id_only_on_bridge_server]
- AC2: a sync message from @facebook_<allowed-id>:evil.example in a joined room is not allowed by a facebook allow rule [evidence: test:tests/test_sync.py::test_foreign_ghost_cannot_use_facebook_rule]
- AC3: resolve_alias maps a 200 to the room id, a 404 to None, and never exposes the token [evidence: test:tests/test_matrix_client.py::test_resolve_alias]
- AC4: a canonical alias that does not resolve to the room is not stored and an alias allow rule does not admit the room; a verified alias is stored and matches [evidence: test:tests/test_sync.py::test_canonical_alias_verified]

## Files

- `src/agents_matrix_connector/discovery.py`
- `src/agents_matrix_connector/sync.py`
- `src/agents_matrix_connector/matrix.py`
- `src/agents_matrix_connector/fake_homeserver.py`
- `tests/test_discovery.py`
- `tests/test_sync.py`
- `tests/test_matrix_client.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-25 done
