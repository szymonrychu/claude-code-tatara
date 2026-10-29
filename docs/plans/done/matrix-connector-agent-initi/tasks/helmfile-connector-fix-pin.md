---
title: helmfile-connector-fix-pin
status: done
repo: agents-helmfile
value: the connector with outbound limits and the pool fix is the one applied
files: [helmfile.yaml.gotmpl, values/agents-matrix-connector/common.yaml, tests/test_matrix_connector_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py"
depends_on: [mxc-pool-and-binding]
model: sonnet
review: ""
verified_head: 051affd5f34b28eb547a765eebee66e45b978c81
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: 1
actual_minutes: 2
actual_tokens: 309929
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 265212, review 44717"
---

# helmfile-connector-fix-pin

## Requirement

Pin agents-matrix-connector to merge commit c98c501 of PR #4 (review fixes mxc-outbound-limits and mxc-pool-and-binding; main CI run 40792219425 green incl images and chart-publish): chart `0.1.0-main.c98c501` in helmfile.yaml.gotmpl and the image tag `c98c501` in values/agents-matrix-connector/ (wherever the current edfb876 pin lives). The connector now enforces a per-room cap on outbound chunks per hour (new setting, default 60): keep the default unless the chart exposes it with a different value, and say which. Keep every other pin unchanged. Update tests/test_matrix_connector_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

## Acceptance conditions

- AC1: the connector chart version and image tag agree on c98c501 [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py]
- AC2: every pin's main CI is green [evidence: command:mise run check-pins]
- AC3: lint passes [evidence: command:mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-matrix-connector/common.yaml`
- `tests/test_matrix_connector_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done
