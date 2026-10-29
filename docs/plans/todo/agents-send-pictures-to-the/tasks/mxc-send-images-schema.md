---
title: mxc send images schema
status: todo
repo: agents-matrix-connector
value: "the send queue can hold a picture until the bot uploads it, without loading bytes on every read"
files: ["src/agents_matrix_connector/migrations/<MIGRATION>_send_images.sql", src/agents_matrix_connector/db/sends.py, src/agents_matrix_connector/db/runs.py, tests/test_schema.py, tests/test_sends_repo.py, tests/test_runs_repo.py]
verify: "uv run --frozen pytest tests/test_schema.py tests/test_sends_repo.py tests/test_runs_repo.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1901552
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc send images schema

## Requirement

README Goal G2, verbatim: "the Matrix token stays in the bot pod: the bot uploads the bytes and sends m.image; the caption goes as its own text message after the picture; reply_to anchors the picture."

Design D3, verbatim:
"- Inserts `sends(kind='image', status='queued')` with `image` bytea, `image_mime`, `image_size`, `image_sha256`, `image_name` (basename of path), `image_path`; caption in `text`. Answers 202 `{id: "s<n>", status, path}`.
- Migration `<MIGRATION>_send_images.sql` (the next free connector number at build time; 0003 is claimed): widens the sends.kind CHECK to message|reaction|image, adds the image columns, adds `outbound.content` jsonb NULL (full event content when set) and widens the outbound kind CHECK as needed. 0002 is not edited.
- `_COLUMNS`/`SendRow` never select the `image` bytea; only the upload step reads it by id.
- `sends.insert` kind check and `_txn_ids` accept image rows."

Design D4, verbatim: "4. One claim transaction as today (queued->sending, authoritative re-check and binding), which also sets `mxc_uri`, sets `image = NULL`, and inserts outbound rows `mxa-<send>-i` (m.image, reply relation) and, with a caption, `mxa-<send>-1` (m.text)." and "`claim_queued` skips image rows whose upload has not succeeded in this tick." and "Upload failures: 413 or 403 M_FORBIDDEN -> guarded queued->failed `upload_rejected:<errcode>`; 429, 5xx, transport -> retry next tick until created_at + 600 s, then failed `upload_failed`."

Design D7, verbatim: "Duplicate: same session, room, kind image, image_sha256, caption and reply_to within 60 s returns the existing send." and "D10 duplicate-final (`message_sends_since`): an image send's caption counts as its text."

Delta fix-as-ac, verbatim: "Migration and plugins tag take the next free number (0003 and v0.4.0/v0.5.0 are claimed)." "`claim_queued` skips image rows whose upload has not succeeded this tick." "`_COLUMNS`/SendRow never load the image bytea." "`sends.insert` kind check, `_txn_ids` and the outbound kind CHECK accept the image row." "`message_sends_since` includes image captions (D10)."

User decision (binding), verbatim: "Release numbers are placeholders resolved at build time, exactly as /workdir/workdir/docs/plans/in-progress/hive-decoupling does (read its design.md 'Build-time settlements' and tasks orch-activity-route, plugins-release-0-4-0, orch-plugins-pin-0-4-0, helmfile-deploy-pin for the pattern): <MIGRATION> for the connector migration (0003 is claimed by immediate-message-delivery-w), <TAG>/<VERSION> for the plugins release (v0.3.0-v0.5.0 claimed). The first task needing each reads it from main and amends dependents."

This is the first (and only) task that needs `<MIGRATION>`. Before the first implementer is dispatched the orchestrator session reads the highest `NNNN_*.sql` in `src/agents_matrix_connector/migrations/` on agents-matrix-connector `main` (after immediate-message-delivery-w merged), adds one, and replaces `<MIGRATION>` (four digits) in this task by `ticket.py amend` (Requirement and acceptance conditions) and in its frontmatter `files` and body. The migration test is named `test_send_images_migration` without the number.

Scope (agents-matrix-connector):
- `migrations/<MIGRATION>_send_images.sql`: `sends.kind` CHECK `message|reaction|image`; columns `image bytea NULL`, `image_mime text NULL`, `image_size integer NULL`, `image_sha256 text NULL`, `image_name text NULL`, `image_path text NULL`, `mxc_uri text NULL`; a CHECK that an image row has mime, size, sha256, name and path (my call: the bot cannot build m.image without them); `outbound.content jsonb NULL`; the outbound kind CHECK gains `image`. The table comments stay (tests/test_schema.py::test_writer_comments).
- `db/sends.py`: `SendRow` gains `image_mime`, `image_size`, `image_sha256`, `image_name`, `image_path`, `mxc_uri` and never `image`; an image insert (kind check accepts `image`) storing bytes, mime, size, sha256, name, path and the caption in `text`; `image_bytes(conn, send_id)`, the only read of the bytea; `queued_images(conn)` (queued image rows with bytes present, oldest first, read-only, for the upload step); `claim_queued(conn, now, ready)` where `ready` maps an image send id to its mxc uri, or to None when the pre-check refused it: message and reaction rows are claimed as today, an image row only when its id is in `ready`, and its `queued -> sending` transition sets `image = NULL` and `mxc_uri`; `fail_queued(conn, send_id, reason)`, the guarded `queued -> failed` that also sets `image = NULL`; `count_recent_kind(conn, session_id, kind, seconds)`; `find_duplicate` for images on session, room, kind image, `image_sha256`, caption (`text`) and `reply_to`; `message_sends_since` includes image sends that have a caption.
- `db/runs.py`: `_txn_ids("image", ...)` is exactly `[f"mxa-{send_id}-i"]`, one chunk, a send and no run; `OutboundRow.content`; `add_outbound(..., content=...)` stores the content on the first row only (like `relates_to`); `pending` and `list_outbound` return it.

## Acceptance conditions

- ac1: the migration widens sends.kind to message, reaction and image, adds the image columns, mxc_uri and outbound.content, widens the outbound kind check with image, refuses an image row without mime, size, sha256, name or path, and re-running the migrator is a no-op [evidence: test:tests/test_schema.py::test_send_images_migration]
- ac2: 0001 and 0002 are not edited [evidence: command:git diff --quiet origin/main -- src/agents_matrix_connector/migrations/0001_init.sql src/agents_matrix_connector/migrations/0002_agent_sends.sql]
- ac3: SendRow has no image field and _COLUMNS names no image bytea column (pure test, runs without a database) [evidence: test:tests/test_sends_repo.py::test_send_row_never_loads_image_bytes]
- ac4: an image insert stores kind image, the bytes, mime, size, sha256, name, path and the caption as text; get returns the metadata without bytes; image_bytes returns the exact bytes [evidence: test:tests/test_sends_repo.py::test_image_send_insert_and_bytes]
- ac5: claim_queued claims message and reaction rows as before and an image row only when ready names it; the claim sets mxc_uri and clears the bytes; an image row not in ready stays queued with its bytes [evidence: test:tests/test_sends_repo.py::test_claim_skips_unready_images]
- ac6: fail_queued moves a queued send to failed with its reason and clears the bytes, and changes nothing on a send that is not queued [evidence: test:tests/test_sends_repo.py::test_fail_queued_clears_image]
- ac7: an image duplicate matches session, room, kind image, sha256, caption and reply_to within the window; another sha256, caption or reply_to is not a duplicate [evidence: test:tests/test_sends_repo.py::test_image_duplicate]
- ac8: count_recent_kind counts only the session's sends of that kind in the window [evidence: test:tests/test_sends_repo.py::test_count_recent_kind]
- ac9: message_sends_since returns an image send's caption as its text and skips caption-less images and failed or refused sends [evidence: test:tests/test_sends_repo.py::test_message_sends_since_includes_image_captions]
- ac10: _txn_ids gives mxa-<send>-i for an image (one chunk, a send and no run; anything else raises) (pure test) [evidence: test:tests/test_runs_repo.py::test_image_txn_ids]
- ac11: add_outbound stores content on the first row only and pending and list_outbound return it [evidence: test:tests/test_runs_repo.py::test_outbound_content_stored]
- ac12: (orchestrator session, before dispatch) the real next migration number read from connector main replaces <MIGRATION> in this task [evidence: judgement:orchestrator quotes the migrations listed on main and a grep of this task file showing no placeholder left]
- ac13: the schema, sends and runs repo tests and lint pass (DB tests in CI) [evidence: command:uv run --frozen pytest tests/test_schema.py tests/test_sends_repo.py tests/test_runs_repo.py && mise run lint]

## Files

- `src/agents_matrix_connector/migrations/<MIGRATION>_send_images.sql`
- `src/agents_matrix_connector/db/sends.py`
- `src/agents_matrix_connector/db/runs.py`
- `tests/test_schema.py`
- `tests/test_sends_repo.py`
- `tests/test_runs_repo.py`

## Interfaces

- `migrations/<MIGRATION>_send_images.sql` (additive).
- `db/sends.py`: `SendRow` (+ `image_mime`, `image_size`, `image_sha256`, `image_name`, `image_path`, `mxc_uri`); the image insert; `image_bytes(conn, send_id) -> bytes | None`; `queued_images(conn) -> list[SendRow]`; `claim_queued(conn, now=None, ready: Mapping[int, str | None] = ...) -> list[SendRow]`; `fail_queued(conn, send_id, reason) -> bool`; `count_recent_kind(conn, session_id, kind, seconds) -> int`; `find_duplicate(...)` for images; `message_sends_since` with image captions.
- `db/runs.py`: `_txn_ids("image", None, send_id, 1) == [f"mxa-{send_id}-i"]`; `OutboundRow.content: dict | None`; `add_outbound(..., content: dict | None = None)`.

## Expected outcome

The queue can hold an image send whose bytes live on the row only until the bot claims or fails it; every existing reader still gets a `SendRow` without bytes.

## Steps

- Orchestrator session, before dispatch: read the migrations on connector main and amend `<MIGRATION>` (ac12).
- Red: write `test_send_images_migration`, the sends repo tests (ac3-ac9) and the runs repo tests (ac10, ac11); run `uv run --frozen pytest tests/test_sends_repo.py::test_send_row_never_loads_image_bytes tests/test_runs_repo.py::test_image_txn_ids`: fail locally (the DB tests error without Docker).
- Green: migration, sends and runs repository changes; run the task's verify; quote the local summary line, then the CI run of the pushed head for the DB tests.

## Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- Every status move goes through `agents_common.db.queue.transition` (status-guarded); the api inserts, the bot moves (one writer per table, design D4).
- Shared files with immediate-message-delivery-w (`db/runs.py`, `runs.relayed_turn_id`): read them as merged on main first.
- `claim_queued` keeps `FOR UPDATE SKIP LOCKED` and oldest-first order; the sender's use of `ready` is task mxc-bot-image-upload.
