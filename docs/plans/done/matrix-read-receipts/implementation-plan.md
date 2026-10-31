# matrix read receipts implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: mxc read receipts

- Status: done
- Files: `src/agents_matrix_connector/matrix.py`, `src/agents_matrix_connector/fake_homeserver.py`, `src/agents_matrix_connector/worker.py`, `tests/test_matrix_client.py`, `tests/test_worker.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q tests/test_matrix_client.py tests/test_worker.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 98bdf1ff816a043f5d5a697fb960d722cde1d86e

#### Requirement

Send a Matrix read receipt when the connector hands messages to an agent (epic goals G1, G2). Paths are in code/agents-matrix-connector.

User request 2026-10-26, verbatim: 'Add read receipts'. User decision 2026-10-26: "On handoff": mark read once the message is delivered to the agent session, in the same step that starts the typing indicator; only in allowed chats.

- `src/agents_matrix_connector/matrix.py`: `MatrixClient.send_receipt(room_id: str, event_id: str) -> None` posts `POST /_matrix/client/v3/rooms/{roomId}/receipt/m.read/{eventId}` with body `{}`; path segments encoded through the existing `_path`; errors map through the existing `_error` like every other call; the token is never in an error or log.
- `src/agents_matrix_connector/fake_homeserver.py`: the receipt route, recording `(room_id, receipt_type, event_id)`; an accessor `receipts(room_id) -> list[str]` (event ids in order); unknown room answers as the other room routes do.
- `src/agents_matrix_connector/worker.py`: `_delivered(batch)` (reached after both `_dispatch` and `_deliver`) also sends one `m.read` receipt for the newest event of the batch (the row with the greatest `origin_ts`, falling back to the greatest `id`), best-effort: a `MatrixError` is logged as a warning (room id and status only) and never fails the run or skips the typing call. Rows that never reach `_delivered` (ignored, failed, session gone, orchestrator refused) get no receipt.
- Tests: `tests/test_matrix_client.py::test_send_receipt` (method, encoded path, empty JSON body, a 403 maps to MatrixForbidden without the token in the message); `tests/test_worker.py::test_handoff_sends_read_receipt` (first dispatch and delivery into a running session each mark the newest event of their batch read, exactly once, and typing still runs); `tests/test_worker.py::test_receipt_failure_does_not_fail_run` (the fake homeserver rejects the receipt; the run still proceeds and typing is still sent); `tests/test_worker.py::test_no_receipt_without_handoff` (a refused dispatch and an ignored row send no receipt).
- `README.md`: the Operations section says the bot marks a message read when it hands it to the agent, and never in chats it does not route. `MEMORY.md`: a dated line with the user decision and why receipts sit next to typing.

#### Acceptance conditions

- AC1: send_receipt posts an empty m.read receipt to the encoded path and maps errors without the token [evidence: test:tests/test_matrix_client.py::test_send_receipt]
- AC2: dispatch and delivery each mark the newest event of the batch read once, next to typing [evidence: test:tests/test_worker.py::test_handoff_sends_read_receipt]
- AC3: a failing receipt never fails the run nor skips typing [evidence: test:tests/test_worker.py::test_receipt_failure_does_not_fail_run]
- AC4: messages that are never handed off get no receipt [evidence: test:tests/test_worker.py::test_no_receipt_without_handoff]
- AC5: README and MEMORY record the behaviour, and lint passes [evidence: command:grep -qi "read receipt\|marks .* read" README.md && grep -q "2026-10-26" MEMORY.md && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_matrix_connector/matrix.py`
- `src/agents_matrix_connector/fake_homeserver.py`
- `src/agents_matrix_connector/worker.py`
- `tests/test_matrix_client.py`
- `tests/test_worker.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-26 done

### S2: connector repin receipts

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-matrix-connector/common.yaml`, `tests/test_matrix_connector_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .`
- Verified head: 5ae6486889567de0318b060f36eee2dd254ecd1b

#### Requirement

Re-pin the connector release to the build with read receipts (epic goal G3). Paths are in code/agents-helmfile.

User request 2026-10-26, verbatim: 'Add read receipts'.

Precondition, checked first: the agents-matrix-connector PR of task mxc-read-receipts is merged to main and chart `oci://harbor.szymonrichert.pl/charts/agents-matrix-connector` `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agents-matrix-connector:<sha7>` exist (read-only checks; the orchestrator amends `<sha7>` in). Otherwise end `blocked`, whoCanClear "orchestrator: merge the connector PR and wait for its main CI".

- `helmfile.yaml.gotmpl`: release `agents-matrix-connector` version `0.1.0-main.038b4f9` becomes `0.1.0-main.<sha7>`.
- `values/agents-matrix-connector/common.yaml`: `image.tag` `038b4f9` becomes `<sha7>`.
- `tests/test_matrix_connector_release.py`: the expected pin is updated first (red), then the two files (green).

#### Acceptance conditions

- AC1: the connector chart and image are pinned to the new sha and the release test expects it [evidence: test:tests/test_matrix_connector_release.py::test_matrix_connector_pin_and_needs]
- AC2: the offline release tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-matrix-connector/common.yaml`
- `tests/test_matrix_connector_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-26 done

### S3: apply receipts live

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run diff && mise run smoke`
- Verified head: 296318b4bbf54d31e3d4feb2abee24e00799b737

#### Requirement

Apply the re-pinned connector and prove receipts live (epic goal G3; live-deploy rule: only the main orchestrator session `claude-code-tatara-7b` applies, through "APPLY REQUEST <epic> <tree> <sha>"). Paths are in code/agents-helmfile.

User request 2026-10-26, verbatim: 'Add read receipts'.

- Implementer, before the apply: `mise run diff`; only the agents-matrix-connector release changes (chart version, image tag). Anything else ends `blocked` with the diff, whoCanClear "user". End the round with "ready for apply".
- After the apply, implementer: `mise run diff` (no drift) and `mise run smoke` (exit 0); `MEMORY.md`: a dated line: applied agents-matrix-connector `0.1.0-main.<sha7>` with read receipts; smoke green (quote its last log line).
- Live proof, read-only, after the user sends one new Messenger message in the owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl`: the bot log shows the receipt request for that room answered 200 (no token in the output), `GET /matrix/api/v1/rooms/{room_id}/messages` shows the message handed off, and the user confirms the message shows as seen in Messenger. Evidence (statuses, event ids, no bodies) goes to `/Users/szymonri/Documents/claude-code-tatara/.scratchpad/matrix-read-receipts/live-proof.md`. Never send a Matrix message, never change rules or settings.

#### Acceptance conditions

- AC1: the live namespace has no drift after the apply and the smoke passes [evidence: command:mise run diff && mise run smoke]
- AC2: MEMORY.md records the applied version [evidence: command:grep -q "read receipts" MEMORY.md]
- AC3: a real handed-off message in the owner DM got a 200 receipt and shows as seen [evidence: judgement:the log excerpt, messages output and user confirmation in live-proof.md]

#### Files

- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-26 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
