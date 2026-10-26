---
title: matrix sync loop
status: done
repo: agents-matrix-connector
value: "chats, users and rooms are discovered automatically and each message is judged by the rules exactly once"
files: [src/agents_matrix_connector/sync.py, tests/test_sync.py]
verify: "uv run --frozen pytest tests/test_sync.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-settings-model, matrix-client-and-fake-hs, rules-and-settings-repo, inbound-queue-repository]
model: opus
review: full
verified_head: 6e83f49d082fc4b3bb3371450fdb509c2c42fa3b
points: 5
expected_minutes: 14
expected_tokens: 1883475
points_actual: 5
actual_minutes: 18
actual_tokens: 2841808
actual_roles: "impl 9, review 9"
actual_role_tokens: "impl 2404507, review 437301"
---

# matrix sync loop

## Requirement

The bot's sync loop: discovery and intake from Matrix into the database (design D4, D5, D6, D7). Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/sync.py`:

- `SyncLoop(matrix: MatrixClient, pool, settings: BotSettings, *, now: Callable[[], datetime] = utcnow)`, `last_sync_at: datetime | None`, `async run_once() -> None`, `async run(stop: asyncio.Event) -> None`.
- Filter: on the first call with no stored `filter_id`, `create_filter` with timeline and state types `m.room.message`, `m.room.member`, `m.room.name`, `m.room.canonical_alias`, `m.room.encryption`, `m.bridge`, `uk.half-shot.bridge`, and presence, account data and ephemeral excluded; stored in `sync_state`.
- `run_once`: `sync(since=next_batch, timeout_ms=sync_timeout_seconds*1000, filter_id)`, then one transaction that applies the whole response and stores the new `next_batch`:
  - `rooms.invite`: `upsert_room(membership="invite", inviter=<sender of our invite member event>)`, then `join` (after the transaction; a `MatrixError` on join is logged with the room id and retried on the next sync, since the invite stays pending).
  - `rooms.join`: a room not yet classified gets `room_state` and `classify`; state and timeline state events update the room info and members (`upsert_members` with `discovery.facebook_id`); `touch_room` on any timeline event.
  - Timeline messages (skipped entirely on the first sync after an empty database, design D5: no replay): `parse_message`; `Skip` writes nothing; `Unsupported` inserts `ignored`, `unsupported_content`, no body; a `Candidate` is judged with `policy.evaluate` (rules read once per response, `Subject` from the room and the sender's directory row); then, when allowed, the room's effective trigger (`effective_trigger` with `room_settings.trigger` and `MATRIX_GROUP_TRIGGER`) and `mentions_self` (self names are the self identities' display names in that room) decide `not_mentioned`; then the per-room cap `MATRIX_MAX_QUEUED_PER_ROOM` decides `queue_full`; otherwise `new`. Body storage per design D7: no body for `denied: *`, `room_encrypted`, `room_infrastructure`, `unsupported_content`; bodies truncated to `MATRIX_MAX_INBOUND_CHARS`.
  - `rooms.leave`: `set_membership(leave)`.
  - `last_sync_at` is set after the commit.
- `run`: loops `run_once` until `stop`; `MatrixUnavailable` backs off 1 s doubling to 60 s and resets on success; `MatrixAuthError` propagates (the process exits, design D5).

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: an invite is recorded and joined, and the joined portal is classified with its members and Facebook ids [evidence: test:tests/test_sync.py::test_invite_join_and_classify]
- AC2: the first sync after an empty database records rooms but inserts no inbound row for history [evidence: test:tests/test_sync.py::test_first_sync_no_replay]
- AC3: with default deny and no rules a message is stored ignored not_allowed with its body, and with an allow room rule it is stored new [evidence: test:tests/test_sync.py::test_default_deny_then_allow]
- AC4: a denied sender's message is stored ignored with no body, and self and bridge-bot messages store nothing [evidence: test:tests/test_sync.py::test_denied_and_self_messages]
- AC5: a group message without a mention is ignored not_mentioned and with a mention is new [evidence: test:tests/test_sync.py::test_group_mention_trigger]
- AC6: encrypted and infrastructure rooms store ignored rows without body, unsupported msgtypes store unsupported_content [evidence: test:tests/test_sync.py::test_encrypted_infrastructure_unsupported]
- AC7: beyond the per-room cap messages are ignored queue_full [evidence: test:tests/test_sync.py::test_queue_cap]
- AC8: a crash before commit replays the same response without duplicate rows, and next_batch advances only with the rows [evidence: test:tests/test_sync.py::test_since_token_and_rows_commit_together]
- AC9: unavailable homeserver backs off and an auth error stops the loop [evidence: test:tests/test_sync.py::test_backoff_and_auth_error]

## Files

- `src/agents_matrix_connector/sync.py`
- `tests/test_sync.py`

## Interfaces

- `src/agents_matrix_connector/sync.py`: `SyncLoop` (`run_once`, `run`, `last_sync_at`). Started by mxc-service-entrypoints in the `bot` process.
- Uses `MatrixClient`, `discovery`, `policy`, `db.directory`, `db.rules`, `db.inbound`.

## Expected outcome

Running the loop against the fake homeserver, an invite to a Messenger DM portal becomes a joined, classified room; its messages land in `inbound` as `new` only when a rule allows them.

## Steps

- Red: `tests/test_sync.py` with the nine tests, `FakeHomeserver` via `httpx.ASGITransport`, a migrated database, and a fixed clock. Fails on the missing module.
- Green: write `sync.py`. Run the verify (Docker).

## Notes

- Review focus: the since token and the inbound inserts commit in one transaction; denied bodies are never written.
- To simulate a crash before commit, make a repository call raise inside the transaction on the first attempt and run `run_once` again.
- Joining is done after commit so a slow join never holds the transaction open.

- 2026-10-25 done
