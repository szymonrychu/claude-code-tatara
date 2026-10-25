---
title: access policy engine
status: todo
repo: agents-matrix-connector
value: "nobody reaches an agent without an explicit allow rule, and a deny rule always wins"
files: [src/agents_matrix_connector/policy.py, tests/test_policy.py]
verify: "uv run --frozen pytest tests/test_policy.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-scaffold-and-cli]
model: opus
review: full
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

# access policy engine

## Requirement

The allow and deny policy: rule validation and the decision for a message or a room (design D4, D6; contract `matrix-access-policy`). No I/O. Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/policy.py`:

- `KINDS = {"allow": ("user", "facebook", "room", "alias"), "deny": ("user", "facebook", "room", "alias", "display_name")}`.
- Reasons: `ROOM_INFRASTRUCTURE = "room_infrastructure"`, `ROOM_ENCRYPTED = "room_encrypted"`, `NOT_ALLOWED = "not_allowed"`, and `denied(kind) -> "denied: <kind>"`.
- `Rule` (frozen dataclass: `id: int`, `list`, `kind`, `value`).
- `validate_rule(list_: str, kind: str, value: str) -> tuple[str, str, str]` returns the canonical triple (value stripped) or raises `ValueError` whose message starts with the offending field (`list:`, `kind:`, `value:`): list in `KINDS`; kind in `KINDS[list]`, and `display_name` under `allow` is refused with a message saying display names are chosen by the sender and cannot grant access; value 1..255 characters; `user` matches `^@[^:\s]+:\S+$`; `facebook` matches `^[0-9]{1,32}$`; `room` matches `^![^:\s]+:\S+$`; `alias` matches `^#[^:\s]+:\S+$`; `display_name` 1..128 characters.
- `Subject` (frozen dataclass): `room_id`, `room_alias | None`, `room_kind | None`, `encrypted: bool`, `sender_id | None`, `sender_facebook_id | None`, `sender_name | None`.
- `Decision` (frozen dataclass): `allowed: bool`, `reason: str | None`, `rule_id: int | None`, `source` in `"room"`, `"rule"`, `"default"`.
- `evaluate(subject: Subject, rules: Sequence[Rule], default_policy: str) -> Decision`, first hit wins: room kind `infrastructure` -> not allowed, `room_infrastructure`, source room; encrypted -> `room_encrypted`; deny rules in ascending id: `room` equals room_id, `alias` equals room_alias, `user` equals sender_id, `facebook` equals sender_facebook_id, `display_name` equals sender_name casefolded -> not allowed, `denied: <kind>`, that rule; then an allow `room` or `alias` rule on the room -> allowed (lowest id); then an allow `user` or `facebook` rule on the sender -> allowed; else `default_policy` `deny` -> not allowed `not_allowed`, `allow` -> allowed with reason None, source default. A subject with `sender_id` None (the room-level view the API shows) is judged on room rules and the default only.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: with no rules and the default policy deny, every message is refused with not_allowed [evidence: test:tests/test_policy.py::test_default_deny_with_no_rules]
- AC2: with the default policy allow and no rules a message is allowed [evidence: test:tests/test_policy.py::test_default_allow]
- AC3: a deny rule on any of room, alias, user, facebook or display name wins over an allow rule on the room or the sender, and the lowest-id deny is reported [evidence: test:tests/test_policy.py::test_deny_wins_on_every_key]
- AC4: display name deny matches case-insensitively and a display name allow rule is refused by validation [evidence: test:tests/test_policy.py::test_display_name_deny_only]
- AC5: an allowed room admits every sender and an allowed user is admitted in any room that is not denied [evidence: test:tests/test_policy.py::test_allow_room_and_allow_user]
- AC6: infrastructure and encrypted rooms are refused even with allow rules [evidence: test:tests/test_policy.py::test_infrastructure_and_encrypted_refused]
- AC7: validation accepts and canonicalises each kind's format and rejects malformed values with the field name first [evidence: test:tests/test_policy.py::test_validate_rule_formats]
- AC8: a room-level subject without a sender is judged on room rules and the default only [evidence: test:tests/test_policy.py::test_room_level_decision]

## Files

- `src/agents_matrix_connector/policy.py`
- `tests/test_policy.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
