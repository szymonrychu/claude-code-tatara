---
title: room and event discovery
status: todo
repo: agents-matrix-connector
value: "bridged Messenger DMs and groups, plain Matrix rooms and bridge spaces are told apart, and only real text messages count"
files: [src/agents_matrix_connector/discovery.py, tests/test_discovery.py]
verify: "uv run --frozen pytest tests/test_discovery.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-scaffold-and-cli]
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

# room and event discovery

## Requirement

Pure discovery and intake functions: classify rooms from their state, parse Facebook ids, decide which timeline events are candidate messages and whether they mention the bot (design D4, D5, D7). No I/O. Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/discovery.py`:

- `RoomInfo` (frozen dataclass): `kind` (`dm`, `group`, `matrix`, `infrastructure`), `name`, `alias`, `encrypted`, `message_request`, `members: dict[str, str | None]` (joined user id to display name), `member_count`.
- `classify(state: Iterable[dict], self_ids: frozenset[str], bridge_bots: Sequence[str]) -> RoomInfo`: the latest `m.bridge` or `uk.half-shot.bridge` state event decides the kind from `content["com.beeper.room_type.v2"]`: `dm` is `dm`; `space` or `personal_filtering_space` is `infrastructure`; `group_dm`, empty or absent is `group`; no bridge event is `matrix`. `encrypted` is true when an `m.room.encryption` state event exists. `message_request` is `content["channel"]["com.beeper.message_request"]` of the bridge event. `alias` is `m.room.canonical_alias` `alias`. Name: `m.room.name` `name`, else the bridge `channel.displayname`, else the display name of the only joined member that is neither a self identity nor a bridge bot, else None. Members from `m.room.member` events with membership `join`.
- `facebook_id(user_id: str, pattern: re.Pattern[str]) -> str | None`: the `id` group of the settings' puppet pattern.
- `Candidate` (frozen dataclass: `event_id`, `room_id`, `sender`, `body`, `formatted_body`, `mention_ids: tuple[str, ...]`, `origin_ts`), `Skip` and `Unsupported` (with `event_id`, `sender`) results of `parse_message(room_id, event, self_ids, bridge_bots) -> Candidate | Skip | Unsupported`: only `m.room.message` events are considered; a sender in `self_ids` or `bridge_bots` is `Skip`; an edit (`m.relates_to.rel_type == "m.replace"`) or an event without a string `body` (redacted) is `Skip`; msgtype `m.text` or `m.emote` is a `Candidate`; any other msgtype is `Unsupported`.
- `mentions_self(candidate, self_ids, self_names: Iterable[str]) -> bool`: true when a self id is in `content["m.mentions"]["user_ids"]`, or `formatted_body` links `https://matrix.to/#/<self id>` (percent-encoded or not), or `body` contains a non-empty self display name, case-insensitive.
- `effective_trigger(kind: str, member_count: int, room_trigger: str | None, group_default: str) -> str`: `room_trigger` when set; else `all` for `dm` and for `matrix` rooms with at most two members; else `group_default`.
- `truncate(body: str, max_chars: int) -> str`: unchanged when short enough, else the first `max_chars` characters followed by ` [truncated]`.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: dm, group_dm, empty room type, space, personal_filtering_space, uk.half-shot.bridge and no bridge event classify as the requirement says [evidence: test:tests/test_discovery.py::test_room_kinds]
- AC2: an m.room.encryption state event marks the room encrypted and the bridge message request flag is read [evidence: test:tests/test_discovery.py::test_encrypted_and_message_request]
- AC3: the name falls back from m.room.name to the bridge channel name to the lone other member [evidence: test:tests/test_discovery.py::test_name_fallbacks]
- AC4: the Facebook id is parsed from a ghost id and None for other users [evidence: test:tests/test_discovery.py::test_facebook_id]
- AC5: self and bridge-bot senders, edits and redacted events are skipped, text and emote are candidates, other msgtypes unsupported [evidence: test:tests/test_discovery.py::test_parse_message]
- AC6: a mention is found through m.mentions, a matrix.to link or the display name, and not otherwise [evidence: test:tests/test_discovery.py::test_mentions_self]
- AC7: the trigger defaults to all for dm and two-member Matrix rooms and to the group default otherwise, and a room setting wins [evidence: test:tests/test_discovery.py::test_effective_trigger]
- AC8: long bodies are truncated with the marker [evidence: test:tests/test_discovery.py::test_truncate]

## Files

- `src/agents_matrix_connector/discovery.py`
- `tests/test_discovery.py`

## Interfaces

- `src/agents_matrix_connector/discovery.py`: `RoomInfo`, `classify`, `facebook_id`, `Candidate`, `Skip`, `Unsupported`, `parse_message`, `mentions_self`, `effective_trigger`, `truncate`. Used by directory-repository, matrix-sync-loop, chat-prompt-render.

## Expected outcome

Given a mautrix-meta portal's state, `classify` says `dm` or `group` with the Facebook thread name; spaces are `infrastructure`; Element rooms are `matrix`.

## Steps

- Red: `tests/test_discovery.py` with the eight tests, fixtures shaped like mautrix-meta portal state (`m.bridge` content with `bridgebot`, `protocol`, `channel` and `com.beeper.room_type.v2`). Fails on the missing module.
- Green: write `discovery.py`. Run the verify.

## Notes

- Ported semantics from Hermes `roomadmin.py` `room_kind`, `display_name`, `is_message_request` (ConfigMap `ai/hermes-agent-files`; design Research inputs).
- Ghost ids look like `@facebook_100000241356957:szymonrichert.pl`; the bridge bot is `@facebookbot:szymonrichert.pl`.
