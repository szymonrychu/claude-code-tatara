---
title: connector repin receipts
status: done
repo: agents-helmfile
value: the cluster runs the connector build that sends read receipts
files: [helmfile.yaml.gotmpl, values/agents-matrix-connector/common.yaml, tests/test_matrix_connector_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py -k \"not helmfile_build\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-read-receipts]
model: sonnet
review: ""
verified_head: 5ae6486889567de0318b060f36eee2dd254ecd1b
points: 1
expected_minutes: 4
expected_tokens: 665870
points_actual: 1
actual_minutes: 4
actual_tokens: 255136
actual_roles: "impl 4, review 1"
actual_role_tokens: "impl 197980, review 57156"
---

# connector repin receipts

## Requirement

Re-pin the connector release to the build with read receipts (epic goal G3). Paths are in code/agents-helmfile.

User request 2026-10-26, verbatim: 'Add read receipts'.

Precondition, checked first: the agents-matrix-connector PR of task mxc-read-receipts is merged to main and chart `oci://harbor.szymonrichert.pl/charts/agents-matrix-connector` `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agents-matrix-connector:<sha7>` exist (read-only checks; the orchestrator amends `<sha7>` in). Otherwise end `blocked`, whoCanClear "orchestrator: merge the connector PR and wait for its main CI".

- `helmfile.yaml.gotmpl`: release `agents-matrix-connector` version `0.1.0-main.038b4f9` becomes `0.1.0-main.<sha7>`.
- `values/agents-matrix-connector/common.yaml`: `image.tag` `038b4f9` becomes `<sha7>`.
- `tests/test_matrix_connector_release.py`: the expected pin is updated first (red), then the two files (green).

## Acceptance conditions

- AC1: the connector chart and image are pinned to the new sha and the release test expects it [evidence: test:tests/test_matrix_connector_release.py::test_matrix_connector_pin_and_needs]
- AC2: the offline release tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .]

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

- 2026-10-26 done
