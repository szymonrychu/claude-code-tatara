---
title: web chats access panels
status: in-progress
repo: agents-web
value: "an operator manages allow and deny lists, people and the default preset in the UI"
files: [src/matrix/UsersTable.tsx, src/matrix/RulesPanel.tsx, src/matrix/DefaultPreset.tsx, src/matrix/ChatsPage.tsx, src/matrix/Access.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/matrix/Access.test.tsx src/matrix/ChatsPage.test.tsx && npm run lint"
depends_on: [web-chats-rooms-page]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 14
expected_tokens: 1860143
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web chats access panels

## Requirement

Users, rules and default preset on the Chats page (design D6, D12). Paths are in code/agents-web.

- `src/matrix/UsersTable.tsx`: discovered users (display name, Matrix id, Facebook id, rooms count, access chip), a search box (`listUsers({q})`), Allow and Deny actions per user (`addRule` kind `facebook` when the user has a Facebook id, else `user`), each after a `ConfirmDialog`.
- `src/matrix/RulesPanel.tsx`: the allow and deny lists (`listRules`), each rule with kind, value, note, created time and a Delete action after a confirm; an Add rule form (list, kind from `meta.rule_kinds[list]` so `display_name` only appears under deny, value, note) with `FormError` for 422 and 409.
- `src/matrix/DefaultPreset.tsx`: the default preset (`getSettings`, `setSettings`) with `PresetSelect` and a note that rooms without their own preset use it, and that the default policy (from `meta.default_policy`) applies to rooms and users no rule covers.
- `src/matrix/ChatsPage.tsx`: Rooms, Users and Rules as tabs, the default preset above them.
- `src/matrix/Access.test.tsx`: users search and allow/deny create the right rule; the rules panel lists, adds (display_name offered only under deny) and deletes rules and shows a 409; the default preset saves.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: users can be searched and allowed or denied by Facebook id or Matrix id after a confirm [evidence: command:npx vitest run src/matrix/Access.test.tsx -t "allows and denies a user"]
- AC2: the rules panel lists both lists, adds with display_name offered only under deny, shows a 409 and deletes after a confirm [evidence: command:npx vitest run src/matrix/Access.test.tsx -t "manages rules"]
- AC3: the default preset is shown and saved [evidence: command:npx vitest run src/matrix/Access.test.tsx -t "saves the default preset"]
- AC4: lint passes [evidence: command:npm run lint]

## Files

- `src/matrix/UsersTable.tsx`
- `src/matrix/RulesPanel.tsx`
- `src/matrix/DefaultPreset.tsx`
- `src/matrix/ChatsPage.tsx`
- `src/matrix/Access.test.tsx`

## Interfaces

- `src/matrix/UsersTable.tsx`, `RulesPanel.tsx`, `DefaultPreset.tsx`; `ChatsPage` tabs.

## Expected outcome

An operator allows a person by their Facebook id, sees the rule, and removes it again.

## Steps

- Red: `src/matrix/Access.test.tsx` with the three cases. Fails: no components.
- Green: write the components and the tabs. Run the verify (also re-runs `ChatsPage.test.tsx`).

## Notes

- The UI never decides access itself; it shows the API's access views.
