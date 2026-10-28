---
title: mxc agent room policy
status: in-progress
repo: agents-matrix-connector
value: "agents reach rooms the user allowed through a person's rule and never a chat with a denied member"
files: [src/agents_matrix_connector/policy.py, src/agents_matrix_connector/api/rooms.py, tests/test_policy.py, README.md]
verify: "uv run pytest tests/test_policy.py && mise run lint"
depends_on: [mxc-room-initiate-flag]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 940114
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc agent room policy

## Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

README Non-goal, verbatim: "No change to the inbound allow/deny policy model."

Interrogate verdict Act on 2, verbatim: "Policy for agent sends with sender None (A,C high/medium): `policy.evaluate(_room_subject(room))` makes rooms allowed only by facebook:/user: rules default-deny for agents, and ignores deny rules on members. Define D4(a) precisely (my call): a room is policy-allowed for agent sends when a room/alias rule allows it, or when the inbound policy would accept a message from at least one current non-bot member; any member matching a deny rule denies. ACs: room allowed via facebook: rule passes; group with a denied member fails under default allow."

Design D4, verbatim: "(a) defined (interrogate Act 2, the lead's call): agents send with no sender, so the room subject alone (`policy.evaluate(_room_subject(R))`) would default-deny a room allowed only by `facebook:` or `user:` rules and would ignore deny rules on its members. R is policy-allowed for agent sends when a room or alias rule allows it, or when the inbound policy would accept a message from at least one current non-bot member of R; any member matching a deny rule denies. In order: an infrastructure or encrypted room is refused exactly as for inbound (`room_infrastructure`, `room_encrypted`); a room or alias deny rule denies (`denied: <kind>`); a deny rule (user, facebook or display_name) matching any current non-bot member denies (`denied: <kind>`); a room or alias allow rule allows; one current non-bot member for whom `policy.evaluate` with that member as sender allows makes R allowed; else `not_allowed`. A current non-bot member is a `room_members` row with membership `join` whose user id is not `MATRIX_USER_ID` and not in `MATRIX_SELF_IDENTITIES` or `MATRIX_BRIDGE_BOTS` (my call: the exclusion discovery already applies). One function, `api/rooms.py:agent_room_decision(room, rule_list, settings) -> policy.Decision` over the pure `policy.evaluate_agent_room(room_subject, member_subjects, rules, default_policy)`, serves the api checks, the listing, the bot's claim and the send-time check (task mxc-agent-room-policy). The inbound policy model is unchanged (README Non-goal); this is how its rules read for a sender-less agent message."

Scope (agents-matrix-connector): `policy.py` (the pure `evaluate_agent_room`), `api/rooms.py` (`agent_room_decision`: the member filter and the subjects, built with the existing `_room_subject` and `_member_subject`), README (the access section says how a room is policy-allowed for agent sends). The routes (mxc-agent-routes) and the bot (mxc-bot-sends-delivery) call `agent_room_decision`; this task does not.

## Acceptance conditions

- ac1: under default deny, a room matching a room or an alias allow rule is allowed for agent sends, with or without members [evidence: test:tests/test_policy.py::test_agent_room_allowed_by_room_rule]
- ac2: under default deny, a room whose only allow rule is a facebook or a user rule matching one current non-bot member is allowed, which the room subject alone would deny [evidence: test:tests/test_policy.py::test_agent_room_allowed_via_member_rule]
- ac3: a group with one member matching a deny rule (user, facebook or display_name) is denied with that rule's reason under default allow, and also when a room allow rule matches it [evidence: test:tests/test_policy.py::test_agent_room_denied_member_denies]
- ac4: a room with no matching rule under default deny, and a room with no current non-bot member and no room or alias allow rule under default allow, answer not_allowed [evidence: test:tests/test_policy.py::test_agent_room_not_allowed]
- ac5: an infrastructure room and an encrypted room are refused with room_infrastructure and room_encrypted, and a room or alias deny rule denies even when a member is allowed [evidence: test:tests/test_policy.py::test_agent_room_room_level_refusals]
- ac6: agent_room_decision counts only members with membership join whose user id is not MATRIX_USER_ID, a MATRIX_SELF_IDENTITIES id or a MATRIX_BRIDGE_BOTS id: a denied member that left, a denied self identity and a denied bridge bot change nothing [evidence: test:tests/test_policy.py::test_agent_room_decision_member_filter]
- ac7: the existing inbound policy tests pass unchanged, evaluate itself is not changed [evidence: command:uv run pytest tests/test_policy.py -k "not agent_room"]
- ac8: README says a room is policy-allowed for agent sends through a room or alias allow rule or an allowed current member, and that any denied member denies [evidence: command:grep -qi "policy-allowed for agent sends" README.md]
- ac9: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_policy.py && mise run lint]

## Files

- `src/agents_matrix_connector/policy.py`
- `src/agents_matrix_connector/api/rooms.py`
- `tests/test_policy.py`
- `README.md`

## Interfaces

- `policy.py:evaluate_agent_room(room: Subject, members: Sequence[Subject], rules: Sequence[Rule], default_policy: str) -> Decision` (pure): `room` has `sender_id` None; each member subject carries the member as sender. Order (D4): infrastructure, encrypted, room/alias deny, member deny, room/alias allow, any member allowed by `evaluate`, else `not_allowed`. Reasons reuse `ROOM_INFRASTRUCTURE`, `ROOM_ENCRYPTED`, `denied(kind)`, `NOT_ALLOWED`; `rule_id` and `source` as in `evaluate`.
- `api/rooms.py:agent_room_decision(room: directory.RoomRow, rule_list: list[policy.Rule], settings: ConnectorSettings) -> policy.Decision`: members with `membership == "join"` whose `user_id` is not in `settings.self_ids()` or `settings.bridge_bots`, built with `_member_subject`; the room with `_room_subject`.
- `policy.evaluate` is unchanged.

## Expected outcome

One function answers whether agents may post to a room under the user's existing rules: a chat allowed through a person's facebook or user rule is reachable, a chat with any denied member is not.

## Steps

- Red: add the six `test_agent_room_*` tests to `tests/test_policy.py`; run `uv run pytest tests/test_policy.py`: they fail (no function).
- Green: `policy.evaluate_agent_room`, `api/rooms.py:agent_room_decision`, README; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Pure and non-DB: build `directory.RoomRow` and `MemberRow` values in memory for the `agent_room_decision` test; the whole file runs locally.
- `room_infrastructure` and `room_encrypted` come first, exactly as `evaluate` does.
- Do not change `evaluate` or the inbound path (README Non-goal: no change to the inbound allow/deny policy model).
- The callers are mxc-agent-routes (routes and listing) and mxc-bot-sends-delivery (claim and send time); this task only provides the function.
