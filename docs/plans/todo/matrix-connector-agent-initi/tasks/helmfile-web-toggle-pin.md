---
title: helmfile web toggle pin
status: todo
repo: agents-helmfile
value: "agents-helmfile pins the web build with the 'Agents may start chats' switch"
files: [values/agents-web/common.yaml, helmfile.yaml.gotmpl, tests/test_web_release.py]
verify: "uv run pytest tests/test_web_release.py && mise run lint"
depends_on: [web-room-initiate-toggle, helmfile-chat-values]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile web toggle pin

## Requirement

Design D14, verbatim (values): "agents-web tag with the toggle."

Design D15, verbatim: "The room drawer gets an "Agents may start chats" switch bound to `agents_may_initiate`, saved with the preset and trigger in the one PUT (gate question Q4)."

Design D18, verbatim: "then the orchestrator with its chat secret and the v0.3.0 plugins ref [...], then agents-web."

Scope (agents-helmfile): `values/agents-web/common.yaml` image tag and `helmfile.yaml.gotmpl` agents-web chart version `0.1.0-main.<sha7>`, both the agents-web `main` sha7 that carries web-room-initiate-toggle (CI-published). No apply here.

## Acceptance conditions

- ac1: the agents-web image tag and chart version name the same agents-web main sha7 [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- ac2: the pinned agents-web sha7 contains web-room-initiate-toggle on main with green CI [evidence: judgement:reviewer checks git merge-base --is-ancestor of the task's verified_head against the pinned sha and the CI run of that sha]
- ac3: the web release still lists the matrix backend and needs the connector [evidence: test:tests/test_web_release.py::test_matrix_backend_configured]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_web_release.py && mise run lint]

## Files

- `values/agents-web/common.yaml`
- `helmfile.yaml.gotmpl`
- `tests/test_web_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
