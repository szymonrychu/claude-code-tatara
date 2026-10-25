---
title: directory repository
status: todo
repo: agents-matrix-connector
value: "discovered rooms, users and members are stored and listable with their queue and session state"
files: [src/agents_matrix_connector/db/__init__.py, src/agents_matrix_connector/db/directory.py, tests/test_directory_repo.py]
verify: "uv run --frozen pytest tests/test_directory_repo.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-schema-migrations, room-and-event-discovery]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# directory repository

## Requirement

The directory repository: rooms, users, members and the sync state, written by the bot's sync loop and read by the API (design D5, D10). Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/db/__init__.py` (package marker) and `src/agents_matrix_connector/db/directory.py`. Writers take a `psycopg.AsyncConnection` so the sync loop composes one transaction per sync response; readers take the pool.

- Writers (bot sync): `upsert_room(conn, room_id, *, membership, info: RoomInfo | None = None, inviter: str | None = None, at)` (insert with `discovered_at`, update the given fields and `updated_at`; `info` sets kind, name, alias, encrypted, message_request, member_count); `set_membership(conn, room_id, membership, at)`; `upsert_members(conn, room_id, members: Mapping[str, tuple[str | None, str]], facebook_id: Callable[[str], str | None], at)` (user id to display name and membership; upserts `users` with display name, facebook id and `last_seen_at`, and `room_members`; recomputes `rooms.member_count` from joined members); `touch_room(conn, room_id, at)` (`last_event_at`); `get_sync_state(conn) -> tuple[str | None, str | None]` (next_batch, filter_id); `set_sync_state(conn, *, next_batch, filter_id=None, at)` (also `last_sync_at`).
- Readers (api): `RoomRow` and `MemberRow` dataclasses; `list_rooms(pool, kind: str | None = None) -> list[RoomRow]` ordered by `last_event_at` desc nulls last, each with `queued` (count of `inbound` rows `new`) and `session` (`session_id`, `slug`, `status` of the room's latest run, or None); `get_room(pool, room_id) -> RoomRow | None` with `members: list[MemberRow]` (user id, display name, facebook id, membership); `list_users(pool, q: str | None, limit: int) -> list[UserRow]` (user id, display name, facebook id, room ids of joined rooms), `q` matching user id, display name or facebook id case-insensitively; `room_exists(pool, room_id) -> bool`; `last_sync_at(pool) -> datetime | None`.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: upserting a room twice keeps one row, keeps discovered_at and updates the classified fields [evidence: test:tests/test_directory_repo.py::test_upsert_room_idempotent]
- AC2: member upserts record users with facebook ids, update a changed display name and recompute member_count [evidence: test:tests/test_directory_repo.py::test_upsert_members]
- AC3: the sync state round-trips next_batch, filter_id and last_sync_at [evidence: test:tests/test_directory_repo.py::test_sync_state_round_trip]
- AC4: list_rooms orders by last activity and carries the queued count and the latest session [evidence: test:tests/test_directory_repo.py::test_list_rooms_counts_and_session]
- AC5: get_room returns members and list_users filters by user id, display name or facebook id [evidence: test:tests/test_directory_repo.py::test_get_room_and_list_users]

## Files

- `src/agents_matrix_connector/db/__init__.py`
- `src/agents_matrix_connector/db/directory.py`
- `tests/test_directory_repo.py`

## Interfaces

- `src/agents_matrix_connector/db/directory.py`: writers `upsert_room`, `set_membership`, `upsert_members`, `touch_room`, `get_sync_state`, `set_sync_state` (matrix-sync-loop); readers `list_rooms`, `get_room`, `list_users`, `room_exists`, `last_sync_at` (api-rooms-and-users, mxc-service-entrypoints readiness).
- Reads `RoomInfo` from `discovery.py`.

## Expected outcome

The directory tables reflect what sync saw, and the API can list rooms with their queue and session state in one query each.

## Steps

- Red: `tests/test_directory_repo.py` on a migrated database (`migrated_db("agents_matrix_connector.migrations")`); insert `inbound` and `runs` rows with plain SQL for the counts. Fails on the missing module.
- Green: write the module. Run the verify (Docker).

## Notes

- Writers never commit; the caller owns the transaction (`async with conn.transaction()`).
- Use `agents_common.db.pool.open_pool` in tests as agents-webhook's repository tests do.
