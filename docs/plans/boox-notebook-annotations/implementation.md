# boox-notebook-annotations P2-P7 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the notebook contract in agents-app-connector 2.1.0, deploy it, then deliver rendered text rows, handwritten edit ops (replace, strike, margin insert with tool shapes and freehand loops and arrows), image regions, revert to vN and the share bundle in agents-boox-sketch.

**Architecture:** The connector gains a per-page `layout.<i>.json` upload part, region PNG parts, `base_version`, a `specs.layout` column with connector-assigned line ids, `document_write(markdown, lines, ops)`, an images route, a revert route and image attachments on hand-off. The app segments and classifies strokes on Send in pure Kotlin (`:core:model`), uploads layouts, and on every new spec version places runs on rows, hides consumed strokes and repaints a page-sized text bitmap through the existing hold at pen idle.

**Tech Stack:** Python 3 / FastAPI / psycopg / fastmcp / pytest + testcontainers (connector); helmfile (agents-helmfile); Kotlin / Compose / Room / OkHttp / Robolectric / Roborazzi / Onyx pen SDK (app).

**Spec:** `docs/plans/boox-notebook-annotations/plan.md` (workbench PR #6, branch `docs/boox-notebook-annotations`). Executors read it first: sections 3 (UX), 4 (data model), 5 (contract), 6 (rendering), 9 (tests) are normative except where the answers below override them.

## Answers applied (taskboard T-46)

| Q | Answer | Effect on the plan text |
|---|---|---|
| 1 | A board pages | Documents stays a reader |
| 2 | A every page is a notebook page | No `PageKind`, no "New drawing page"; drop `kind` from the wire layout (always notebook). `NotebookGeometry(pageW, pageH)` from P1 stays derived, not stored |
| 3 | B 6 mm dots, 12 mm rows | Shipped in P1 (`NotebookGeometry.CELL` 53, `ROW_PITCH` 106) |
| 4 | B 30 percent margin | Shipped in P1 (`MARGIN_FRACTION` 0.30) |
| 5 | A sans, half row | `Typeface.SANS_SERIF`, 40 px, baseline 11 px above the row line |
| 6 | A hidden after transcription, no toggle | `Page.consumed`, never drawn, never exported |
| 7 | A explicit Send | Existing send button and outbox |
| 8 | A words under it | Replace targets whole words overlapped by the annotation x extent |
| 9 | A whole words | Strike targets whole words |
| 10 | B app crop, ref plus bundle | Share .md exports a zip with images; hand-off attaches the images |
| 11 | A word boundary or new line | Tip in text band: nearest word boundary; else `after_line` |
| 12 | C freehand recognition | IN scope: P5b recognises freehand loops and freehand arrows in addition to the rectangle and arrow tools |
| 13 | A send all, reject conflicts | Ops in x order; rejected ops keep their ink |
| 14 | A translator applies ops | Connector checks coverage only |
| 15 | B revert to vN | Connector route copies vN (markdown plus layout) as a new version; app action and re-render |
| 16 | A shrink, wrap, shift rows | 85 percent shrink, wrap, whole-row shift of runs and ink |
| 17 | A 409 `stale_base` | App re-renders latest, keeps marks for re-send |
| 18 | A dismiss, consume | Shipped in P0 (v0.14.0..v0.14.3) |

Open product questions that block parts of this plan are in `.scratchpad/boox-notebook-annotations/open-questions.md` (OQ1-OQ7). Each task below that depends on one names it; build the Recommended option unless the answer says otherwise.

## Global Constraints

- Plain ASCII everywhere: no em dashes, smart quotes or arrows in code, comments, commits, PR text.
- No backward-compatibility shims, aliases or feature detection (spec 5.3). A new app against an old connector fails with the existing 422 "Not sent" dialog.
- Deploy only semver images X.Y.Z; the connector's and the app's main builds release the tag (`scripts/next_version.py`: `feat:` minor, `type!:` major, else patch). PRs are squash-merged, so the PR title decides the bump.
- Every merge to the app's main publishes a signed APK. Therefore no app PR that sends layouts may merge before connector 2.1.0 is applied and the preset is pushed (P3 done).
- `mise run --cd code/agents-helmfile apply` and `scripts/ensure_preset.py` need explicit user approval in the chat, every time.
- Connector repo is public: no hostnames, secrets, personal data. App repo public: fixtures use `https://connector.example` and `test-token`.
- Tests are not negotiable: never edit or delete a test to pass; when a test is no longer accurate, say which and why in the commit body and in the component MEMORY.md.
- Every non-obvious decision gets a dated MEMORY.md line in its component.
- Page geometry constants (page px): canvas 1404 x 1872, cell 53, row pitch 106, top margin 106, text left 53, margin x = round(1404 * 0.70) = 983, text size 40, baseline 11 px above the row line, shrink floor 0.85.
- Classifier thresholds (spec 3.5, 4.2): strike height < 0.40 x band (21.2 px), width > 1.5 x height, mean chord deviation < 0.25 x band; segment split gap > 2 cells (106 px); a stroke spanning > 1.5 rows is a drawing stroke; replace grouping gap 1 cell; arrow tail snap `SNAP_RADIUS` 40 px.
- Connector limits: `max_regions_per_page` 4 (new setting), `max_layout_bytes` 262144 (new setting), region PNGs count toward `max_upload_bytes` and the device quota.
- Worktrees: `/workdir/workdir/.worktrees/boox-notebook-annotations-<phase>/<repo>`; logs: `/workdir/workdir/.logs/boox-notebook-annotations/`; scratch: `/workdir/workdir/.scratchpad/boox-notebook-annotations/`.

## Review Focus

1. A layout whose `quote` no longer matches because the spec changed in a revert between render and send: expect 409 `stale_base` (the revert made a newer version), never 422 or a misapplied op. Test: `test_upload_after_revert_is_stale_base` (Task 2.6).
2. A notebook turn delivered to a translator session still on the old prompt that calls `document_write(markdown)` without `lines`/`ops`: expect tool error `layout_incomplete` naming the ids, no version stored. Test: `test_notebook_turn_without_lines_is_layout_incomplete` (Task 2.4).
3. A spec version arriving while the pen is down: the text layer swap must wait for pen idle and never draw while raw drawing is live. Test: `version_while_pen_down_applies_after_idle_through_one_hold` (Task 4.6).
4. Row shift pushing runs and ink past the last row (row 15) of the page: see OQ4; expect the Recommended behaviour, never a run placed outside `rowCount` or ink lost. Test: `shift_past_last_row_moves_overflow_to_a_new_page_after` (Task 4.4).
5. Undo after a version consumed strokes: undo must not resurrect consumed strokes into a later Send as new handwriting (they stay in `consumed`). Test: `undo_after_apply_keeps_consumed_strokes_out_of_segments` (Task 4.3).

---

## Phase overview, dependencies and release boundaries

| Phase | Repo | PR title (decides the bump) | Release | Estimate (agent wall clock) |
|---|---|---|---|---|
| P2 | agents-app-connector | `feat(sketch): notebook layouts, edit ops, region images, revert and hand-off images` | 2.1.0 (image + chart `0.1.0-main.<sha7>`) | 8 h |
| P3 | agents-helmfile | `feat: pin agents-app-connector 2.1.0 (notebook layouts)` | apply after approval; then `ensure_preset` after approval | 0.5 h plus approvals |
| P4 | agents-boox-sketch | `feat(board): rendered text rows from notebook layouts, revert to a version` | 0.15.0 | 7 h |
| P5a | agents-boox-sketch | `feat(board): handwritten replace, strike and margin insert ops` | 0.16.0 | 5 h |
| P5b | agents-boox-sketch | `feat(board): freehand loops and arrows make margin inserts` | 0.17.0 | 3 h |
| P6 | agents-boox-sketch | `feat(board): image region tool, inline images and share bundle` | 0.18.0 (0.17.0 if it merges before P5b) | 4 h |
| P7 | all | release verification, device round, final review, retro | patch releases only for fixes | 1.5 h plus device time |

Dependency graph:

```
P2.1 (contract + openapi.json) --> P4.1 can start (mocked connector from the P2 branch openapi.json)
P2 (all) --> 2.1.0 tag --> P3 PR --> [user approves apply] --> apply --> [user approves] --> ensure_preset
P4.1-P4.2 (model + DTOs, pushed on the P4 branch) --> P5a and P6 worktrees branch from there
P3 done --> merge P4 --> rebase + merge P5a --> rebase + merge P5b
                    \--> rebase + merge P6 (independent of P5a/P5b; whichever is green first)
all merged --> P7
```

Parallelism: P2 and P4/P5/P6 build at the same time. P4, P5a and P6 build in three worktrees against the mocked connector (`core/api/src/test/resources/openapi.json` refreshed from the P2 branch, MockWebServer). P5b starts after P5a's classifier task (5.2) exists on the P5a branch.

Release decision: one PR and one APK per phase (P4, P5a, P5b, P6), as the superleader asked. It is safe because (a) every app release that sends layouts merges only after P3 is applied, so no release needs an undeployed connector feature, and (b) each phase is complete on its own: P4 alone turns handwriting into rows (writing above text before P5a is just new handwriting); P5a adds ops; P5b only widens which marks count as an insert; P6 only adds a tool. P7 releases patches only.

---

## P2: agents-app-connector 2.1.0

Repo: `code/agents-app-connector`, worktree `.worktrees/boox-notebook-annotations-p2/agents-app-connector` from `origin/main` (4f764ce, v2.0.2). Read `AGENTS.md`, `MEMORY.md` (entries 2026-11-04 on annotates, translator tools, document_write) and `ROADMAP.md` (server-side crop stays out of scope). Commands: `mise run test` (Docker needed), `mise run lint`, `mise run fmt`, `mise run test:chart`. Single test: `uv run pytest tests/<file>.py::<name> -v`.

### Task 2.1: Wire contract (schemas, settings, openapi) - first, unblocks the app

**Files:**
- Create: `src/agents_app_connector/plugins/sketch/layout.py`
- Modify: `src/agents_app_connector/api/schemas.py` (`SketchMeta.base_version`), `src/agents_app_connector/settings.py`, `src/agents_app_connector/api/openapi.py`, `openapi.json`
- Test: `tests/test_layout_schema.py`, `tests/test_settings.py`, `tests/test_openapi_current.py`

**Interfaces:**
- Produces (`plugins/sketch/layout.py`, pydantic, `extra="forbid"`):
  - `Geometry(cell: int, row_pitch: int, top: int, rows: int, text_left: int, margin_left: int)`
  - `Segment(id: str  # ^p\d+-r\d+-\d+$, row: int>=0, x0: float, x1: float, strokes: list[int])`
  - `VisibleRun(line_id: str  # ^L\d+$, row: int, x0: float)`
  - `OpTarget(line_id: str, from_: int = Field(alias="from"), to: int, quote: str)`
  - `OpAt(line_id: str, offset: int, mode: Literal["inline", "after_line"])`
  - `Region(id: uuid.UUID, part: str  # ^region\.\d+\.\d+\.png$, after_line: str | None)`
  - `EditOp(id: uuid.UUID, kind: Literal["replace","delete","insert","image"], target: OpTarget | None, at: OpAt | None, strokes: list[int], rect: tuple[float,float,float,float] | None, region: Region | None)` with a validator: replace/delete need `target`; insert needs `at` and `rect`; image needs `region` and `rect`.
  - `PageLayout(version: Literal[1], geometry: Geometry, segments: list[Segment], runs: list[VisibleRun], ops: list[EditOp])`
  - `layout_field(i: int) -> str` = `layout.{i}.json`; `region_field(i: int, k: int) -> str` = `region.{i}.{k}.png`
  - `SpecLine(line_id: str, source_line: int, origin: dict | None)`, `OpStatus(id: uuid.UUID, status: Literal["applied","rejected"], note: str | None)`, `SpecLayout(lines: list[SpecLine], ops: list[OpStatus], base_version: int | None, reverted_from: int | None = None)`
- Produces: `SketchMeta.base_version: int | None = Field(default=None, ge=1)`; requires `conversation_id` when set; mutually exclusive with `annotates`.
- Produces settings `max_regions_per_page: int = Field(4, ge=0, le=16)`, `max_layout_bytes: int = Field(262144, ge=1024, le=1048576)`.

- [ ] **Step 1: Write failing tests** in `tests/test_layout_schema.py`: `test_page_layout_round_trip`, `test_op_kind_requires_its_fields` (parametrised over the four kinds, missing field raises), `test_segment_id_pattern`, `test_unknown_key_rejected`, `test_base_version_requires_conversation_id`, `test_base_version_excludes_annotates`; in `tests/test_settings.py` `test_layout_and_region_limits_defaults` (4, 262144); in `tests/test_openapi_current.py` `test_upload_documents_layout_and_region_parts` (the upload operation names `layout.{i}.json`, `region.{i}.{k}.png`, `base_version`, errors `stale_base`, `stale_target`, `op_replayed`) and `test_spec_schema_has_layout`.
- [ ] **Step 2:** `uv run pytest tests/test_layout_schema.py tests/test_settings.py tests/test_openapi_current.py -v` - FAIL (module missing).
- [ ] **Step 3:** Implement the models and settings; declare the new parts, errors, `Spec.layout` (nullable `SpecLayout`), and the routes of Tasks 2.7-2.8 (`GET /conversations/{id}/images/{region_id}.png`, `POST /conversations/{id}/spec/{version}/revert`) in `api/openapi.py`; regenerate with `uv run python -m agents_app_connector.api.openapi > openapi.json`.
- [ ] **Step 4:** Re-run the three files - PASS (`test_openapi_json_matches_apps` stays red until the routes exist; it is the last thing fixed, in Task 2.8; note it in the commit body as in MEMORY 2026-11-04).
- [ ] **Step 5:** Commit `feat(sketch): notebook layout wire models and settings`. Push the branch so the app side can copy `openapi.json` (`mise run --cd <app worktree> api:refresh <path>`).

### Task 2.2: Migration 0006 and repositories

**Files:**
- Create: `src/agents_app_connector/migrations/0006_notebook_layout.sql`, `src/agents_app_connector/db/spec_images.py`
- Modify: `src/agents_app_connector/db/specs.py`, `src/agents_app_connector/db/attachments.py`
- Test: `tests/test_schema.py`, `tests/test_specs_repo.py`, `tests/test_spec_images_repo.py`, `tests/test_retention.py`

**Interfaces:**
- Migration: `ALTER TABLE specs ADD COLUMN layout jsonb NULL`; attachments kind check becomes `('sketch_png','sketch_strokes','sketch_layout','spec_image')`; `ALTER TABLE attachments ALTER COLUMN expires_at DROP NOT NULL`; `CREATE TABLE spec_images (conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, region_id uuid NOT NULL, attachment_id uuid NOT NULL REFERENCES attachments(id) ON DELETE CASCADE, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (conversation_id, region_id))`; `COMMENT ON TABLE spec_images IS 'writer: app'`.
- `specs.SpecRow.layout: dict | None`; `specs.add(conn, conversation_id, markdown, inbound_id, sketch_ids, run_id, layout: dict | None = None) -> int`; `specs.max_line_number(conn, conversation_id) -> int` (max N of every `L<N>` in every layout of the conversation, 0 when none); `specs.reported_op_ids(conn, conversation_id) -> set[uuid.UUID]`.
- `attachments.NewAttachment.expires_at: datetime | None`.
- `spec_images.add(conn, conversation_id, region_id, attachment_id) -> None`; `spec_images.get(conn, conversation_id, region_id) -> attachments.AttachmentRow | None`; `spec_images.missing(conn, conversation_id, region_ids: Iterable[uuid.UUID]) -> set[uuid.UUID]`.

- [ ] **Step 1: Failing tests:** `test_schema.py::test_migration_0006_layout_and_spec_images`; `test_specs_repo.py::test_add_stores_layout`, `test_max_line_number_scans_all_versions`, `test_reported_op_ids`; `test_spec_images_repo.py::test_add_get_missing`, `test_cascade_with_conversation`; `test_retention.py::test_spec_images_never_purged` (an attachment with `expires_at` NULL survives `purge` at now + 10 years).
- [ ] **Step 2:** Run them - FAIL.
- [ ] **Step 3:** Implement. `attachments.expired` needs no change (NULL never satisfies `<=`).
- [ ] **Step 4:** Run - PASS. `mise run test` green except the openapi current check.
- [ ] **Step 5:** Commit `feat(sketch): migration 0006 for spec layouts and spec images`.

### Task 2.3: Upload accepts layouts, regions and base_version

**Files:**
- Modify: `src/agents_app_connector/plugins/sketch/router.py` (upload only), `src/agents_app_connector/plugins/sketch/layout.py` (validation functions), `src/agents_app_connector/images.py` (reuse `validate_png` for regions)
- Test: `tests/test_api_sketches_layout.py`, `tests/helpers.py` (helpers `layout(...)`, `region_png(...)`, `files(..., layouts=..., regions=...)`)

**Interfaces:**
- `layout.parse_layout(raw: bytes, *, index: int, max_bytes: int) -> PageLayout` (422 `invalid_request` with `layout.<i>.json: <msg>`)
- `layout.check_layout(layout: PageLayout, *, index: int, strokes_count: int | None, canvas: Canvas, region_parts: set[str]) -> None`: stroke indices `< strokes_count` (no strokes part means no indices allowed), rects and segment x inside the canvas, op ids unique across the upload, every `region.part` present for this page index and every region part referenced (422 `invalid_request`).
- `layout.check_base(layouts: dict[int, PageLayout], base: specs.SpecRow) -> None`: every `line_id` in runs and ops exists in `base.layout.lines`; for each op target, `base.markdown.splitlines()[source_line-1][from:to] == quote` else 422 `stale_target`.
- Upload rules: `base_version` required when any layout has ops (422 `invalid_request`); `base_version` not equal to `specs.latest_version` is 409 `stale_base`; any op id in `specs.reported_op_ids` is 409 `op_replayed`; region count per page `<= max_regions_per_page`; `request.form(max_files=2*max_pages + max_pages + max_pages*max_regions_per_page)`; layouts stored as `sketch_layout` attachments (normal retention), regions as `spec_image` attachments with `expires_at=None` plus a `spec_images` row; the fingerprint digests now include layout and region parts in field order.

- [ ] **Step 1: Failing tests** in `tests/test_api_sketches_layout.py`: `test_layout_and_regions_stored`, `test_bad_stroke_index_422`, `test_rect_outside_canvas_422`, `test_missing_region_part_422`, `test_unreferenced_region_part_422`, `test_too_many_regions_422`, `test_ops_without_base_version_422`, `test_unknown_line_id_422`, `test_quote_mismatch_422_stale_target`, `test_old_base_version_409_stale_base`, `test_replayed_op_id_409_op_replayed`, `test_fingerprint_covers_layout_and_region_parts` (same client id, changed layout bytes: 422 `idempotency_mismatch`), `test_client_id_replay_200`, `test_region_counts_toward_quota`, `test_plain_upload_unchanged` (no layout parts: same 202 and rows as today).
- [ ] **Step 2:** Run - FAIL.
- [ ] **Step 3:** Implement. Keep the router readable: the per-part parsing loop moves into a helper `_read_parts(form, meta, settings) -> Parts` in `router.py`; layout checks live in `layout.py`.
- [ ] **Step 4:** Run the new file plus `tests/test_api_sketches.py` - PASS.
- [ ] **Step 5:** Commit `feat(sketch): uploads carry page layouts, region images and base_version`.

### Task 2.4: document_write with lines and ops, line ids

**Files:**
- Create: `src/agents_app_connector/line_ids.py`
- Modify: `src/agents_app_connector/translator_tools.py`, `src/agents_app_connector/db/inbound.py` (if needed, a reader for the run's layouts)
- Test: `tests/test_line_ids.py`, `tests/test_translator_tools.py`

**Interfaces:**
- `line_ids.assign(markdown: str, lines: list[LineProvenance] | None, base: SpecLayout | None, next_number: int) -> list[SpecLine]` where `LineProvenance(n: int, segments: list[str] = [], kept: str | None = None, op: str | None = None)`. One `SpecLine` per markdown source line (1-based `source_line`). A line with `kept` keeps that id (must exist in `base`, each kept id used once); every other line gets `L<next_number>`, `L<next_number+1>`... in source order. Origin: `{"segments": [...]}`, `{"kept": id}`, `{"op": id}` or null.
- `TranslatorTools.write_document(session_id, markdown, lines: list[dict] | None = None, ops: list[dict] | None = None) -> dict`. When the run's inbound has `sketch_layout` attachments: `lines` and `ops` required; every segment id and op id of the inbound must appear (tool error `layout_incomplete: missing <ids>`); `images/<uuid>.png` references must exist in `spec_images` of the conversation (`unknown_image: <ids>`); stored layout = `SpecLayout(lines=assign(...), ops=ops, base_version=meta.base_version)`. Without layouts: `lines` or `ops` present is tool error `layout_not_expected`; layout stored NULL. The tool result adds `"lines": <count>`.
- MCP tool `document_write` gains the two optional arguments with descriptions; `DOCUMENT_WRITE` text adds one sentence: "For notebook pages also pass lines (provenance of every source line) and ops (applied or rejected for every op id)."

- [ ] **Step 1: Failing tests:** `test_line_ids.py::test_new_lines_numbered_after_max`, `test_kept_ids_survive`, `test_unknown_kept_id_raises`, `test_kept_twice_raises`, `test_blank_lines_get_ids` (every source line has an id); `test_translator_tools.py::test_notebook_turn_stores_layout_with_line_ids`, `test_notebook_turn_without_lines_is_layout_incomplete`, `test_missing_op_status_is_layout_incomplete`, `test_unknown_image_reference`, `test_plain_turn_rejects_lines_and_ops`, `test_lists_exactly_the_two_tools_with_the_contract` (existing test: update only the schema expectation of `document_write`; say why in the commit body: the contract changed).
- [ ] **Step 2:** Run - FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run - PASS.
- [ ] **Step 5:** Commit `feat(sketch): document_write records line provenance and op status`.

### Task 2.5: Prompt and system_append for notebook pages

**Files:**
- Modify: `src/agents_app_connector/plugins/__init__.py` (`TurnInput.layouts: Sequence[tuple[int, PageLayout]] = ()`, `TurnInput.base: tuple[int, str, SpecLayout] | None = None`), `src/agents_app_connector/worker.py` (load `sketch_layout` attachments and the base spec for the turn), `src/agents_app_connector/plugins/sketch/__init__.py` (`render_prompt`), `src/agents_app_connector/plugins/sketch/system_append.md`
- Test: `tests/test_sketch_prompt.py`, `tests/test_worker.py`

**Interfaces:** prompt lines exactly as spec 5.2: after `Image i: ...` a line `Notebook geometry: cell 53, rows 16 from y 106, pitch 106, text x 53-983, margin x 983-1404`; visible runs as `L12 row 4: "<display text>"`; segments as `p0-r4-0 row 4 x 60-900`; ops as `op <first 4 hex of id> replace L12[4:9] "milk" with the handwriting above it (rect x,y,w,h)`, `op ... delete L12[4:9] "milk"`, `op ... insert at L12 offset 9 inline|after L12 from the margin note (rect ...)`, `op ... image region <region id> (rect ...) after L11: do not transcribe inside`; then `Spec version <base>` in full plus the base layout as `L<n>: line <source_line>` pairs. Full op ids appear in a final `Op ids:` line so the model can report them. `turn_attachments` is unchanged (layout and region parts never attached). `system_append.md` gains the "Notebook pages" section of spec 5.2 including: segments become their own source lines where the block allows; lines inside fences and tables keep their source strokes as ink (no `segments` provenance for them); report every op; unclassified margin ink is applied under the annotated-spec rule (OQ3 Recommended).

- [ ] **Step 1: Failing tests:** `test_notebook_prompt_snapshot` (fixture turn with 2 runs, 1 segment, one op of each kind), `test_notebook_prompt_carries_base_in_full`, `test_plain_prompts_unchanged_by_notebook_support`, `test_annotation_prompt_snapshot` stays green unchanged, `test_system_append_has_notebook_pages_section`, `test_worker.py::test_turn_input_carries_layouts_and_base`.
- [ ] **Step 2:** Run - FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run - PASS.
- [ ] **Step 5:** Commit `feat(sketch): translator prompt for notebook pages`.

### Task 2.6: Spec layout on the read side and the images route

**Files:**
- Modify: `src/agents_app_connector/plugins/sketch/router.py` (`spec_json` adds `"layout"`; new image route)
- Test: `tests/test_api_spec.py`, `tests/test_api_spec_images.py`

**Interfaces:** `GET /conversations/{id}/spec` and `/spec/{version}` bodies gain `layout` (`SpecLayout` JSON or null). The `spec` event payload stays `{version}` (the app fetches the version). `GET /app/v1/sketch/conversations/{id}/images/{region_id}.png`: device bearer, conversation ownership (404 `not_found`), unknown region 404 `not_found`, ETag = `"<sha256>"`, 304 on `If-None-Match`, `image/png`.

- [ ] **Step 1: Failing tests:** `test_spec_json_includes_layout`, `test_spec_json_layout_null_for_plain`; `test_api_spec_images.py::test_image_served_with_etag_and_304`, `test_other_device_404`, `test_unknown_region_404`, `test_image_survives_retention`, `test_image_deleted_with_conversation`, `test_upload_after_revert_is_stale_base` (seed v1 with layout, revert via Task 2.7 route, upload ops on base 1: 409).
- [ ] **Step 2:** Run - FAIL (the last one stays red until 2.7; write it here, it is the Review Focus item 1).
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run - PASS except the revert one.
- [ ] **Step 5:** Commit `feat(sketch): spec layout in responses and the spec images route`.

### Task 2.7: Revert route (Q15 B)

**Files:**
- Modify: `src/agents_app_connector/plugins/sketch/router.py`, `src/agents_app_connector/db/inbound.py` (`has_open(conn, conversation_id) -> bool`: any row queued or in-progress), `src/agents_app_connector/api/schemas.py` (`RevertIn(base_version: int >= 1)`)
- Test: `tests/test_api_revert.py`

**Interfaces:** `POST /conversations/{id}/spec/{version}/revert` body `{"base_version": <latest the app shows>}`. 404 `no_spec` when vN is missing; 409 `stale_base` when `base_version` is not the latest; 409 `busy` when `inbound.has_open`; 422 when `version == latest`. On success, in one transaction: `specs.add(conn, id, vN.markdown, inbound_id=None, sketch_ids=vN.sketch_ids, run_id=None, layout={**vN.layout, "ops": [], "base_version": latest, "reverted_from": N})` (lines and line ids copied unchanged, so the board can re-match runs by id); `events.append(..., "spec", {"version": new})`; 201 `{"version": new, "reverted_from": N}`. A replay with the same `base_version` after success gets 409 `stale_base` (idempotency through the base check; documented in README).

- [ ] **Step 1: Failing tests:** `test_revert_copies_markdown_and_layout_as_new_version`, `test_revert_emits_spec_event`, `test_revert_stale_base_409`, `test_revert_busy_while_turn_open_409`, `test_revert_to_latest_422`, `test_revert_unknown_version_404`, `test_revert_other_device_404`, `test_line_ids_after_revert_continue_from_max` (a later `document_write` numbers new lines after the max over all versions).
- [ ] **Step 2:** Run - FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run, plus `test_upload_after_revert_is_stale_base` - PASS.
- [ ] **Step 5:** Commit `feat(sketch): revert a conversation to an earlier spec version`.

### Task 2.8: Hand-off attaches the spec images (Q10 B); docs, eval set, release prep

**Files:**
- Modify: `src/agents_app_connector/handoff.py`, `README.md`, `openapi.json`, `MEMORY.md`, `scripts/make_eval_set.py`, `scripts/eval_sketches.py`, `eval/README.md`
- Create: `eval/sketches/12-notebook-lines.png` .. `15-image-region.png`, `eval/expected/12-*.json` .. `15-*.json`, `eval/specs/12-*.md` .. `15-*.md`, `eval/layouts/12-*.json` .. `15-*.json`, `eval/regions/15-image-region.0.0.png`
- Test: `tests/test_handoff.py`, `tests/test_readme_api.py`, `tests/test_eval_set.py`, `tests/test_openapi_current.py`

**Interfaces:** `handoff.spec_image_ids(markdown: str) -> list[uuid.UUID]` (regex `!\[[^\]]*\]\(images/([0-9a-f-]{36})\.png\)`, first-seen order, unique). `_post` loads each through `spec_images.get` and passes `attachments=[Attachment(f"{id}.png", "image/png", data)]` to `deliver` / `dispatch`, at most `ORCHESTRATOR_ATTACHMENTS_MAX_COUNT` (8); the rest are listed by name in the text (OQ5 Recommended). The text says `Images: images/<id>.png are attached under the same names.`

- [ ] **Step 1: Failing tests:** `test_handoff.py::test_handoff_attaches_referenced_images`, `test_handoff_caps_images_and_lists_the_rest`, `test_handoff_without_images_unchanged`; `test_readme_api.py::test_readme_documents_notebook_layouts` (README mentions `layout.<i>.json`, `region.<i>.<k>.png`, `base_version`, `stale_base`, `stale_target`, `op_replayed`, `layout_incomplete`, revert, images route) and the route count assertion grows by 2 (route count is no longer accurate: two routes added); `test_eval_set.py::test_notebook_items_regenerate_identically`, `test_notebook_items_valid_for_upload` (each layout passes `parse_layout` + `check_layout` against its strokes count), `test_notebook_expected_has_lines_and_op_statuses`.
- [ ] **Step 2:** Run - FAIL.
- [ ] **Step 3:** Implement; regenerate `uv run python scripts/make_eval_set.py`; regenerate `openapi.json`. MEMORY.md lines (dated): line id numbering from the max over all versions; revert idempotency through `base_version`; `busy` refusal; spec images never expire and count toward the device quota; hand-off image cap 8.
- [ ] **Step 4:** `mise run test`, `mise run lint`, `mise run test:chart`, `mise run lint:chart` - all green (log to `.logs/boox-notebook-annotations/p2-*.log`).
- [ ] **Step 5:** Commit `feat(sketch): hand-off attaches spec images; docs and eval cases 12-15`.

### P2 PR and release

- [ ] Push, open PR with the title from the overview (no `!`: additive for the old app). Body lists the new routes, errors, migration 0006, and "Preset text changed: run ensure_preset after the apply (P3)".
- [ ] `superpowers:requesting-code-review` (sonnet reviewer) and `workbench:pullrequests-review-loop`; CI green; squash-merge.
- [ ] Confirm the main build pushed `v2.1.0` and the image; record the release commit sha7 for the chart version `0.1.0-main.<sha7>`.

---

## P3: agents-helmfile pin, apply, preset

Repo: `code/agents-helmfile`. Read `AGENTS.md` (deploy rule, check-pins), `MEMORY.md`.

### Task 3.1: Pin 2.1.0

**Files:** Modify `values/agents-app-connector/common.yaml` (`tag: "2.1.0"`), `helmfile.yaml.gotmpl` (agents-app-connector `version: 0.1.0-main.<sha7>`), `tests/test_app_connector_release.py` (`CHART`, `TAG`, the comment naming the release commit; these constants are the pin itself).

- [ ] **Step 1:** Edit the test constants first; `mise run --cd code/agents-helmfile test` - FAIL on the pin asserts.
- [ ] **Step 2:** Edit values and helmfile; `mise run test`, `mise run lint`, `mise run check-pins` - PASS.
- [ ] **Step 3:** Commit `feat: pin agents-app-connector 2.1.0 (notebook layouts)`; PR; `workbench-infra:helmfile-differ` for the diff summary (expect: image tag, chart version, configmap if settings render; migration runs on start).
- [ ] **Step 4:** Merge when green.

### Task 3.2: Apply (user approval gate)

- [ ] Ask the user in one line: "Apply agents-app-connector 2.1.0 now (`mise run --cd code/agents-helmfile apply`)?" Wait for an explicit yes.
- [ ] Apply; `workbench-observability:k8s-triage` (sonnet) for rollout health; `mise run --cd code/agents-helmfile smoke`.

### Task 3.3: Push the preset (user approval gate)

- [ ] Ask: "Run `scripts/ensure_preset.py` to push the sketch-translator notebook prompt?" Wait for yes. Run it from `code/agents-app-connector` at tag v2.1.0 with the token by reference only (never printed). Expect `updated`.
- [ ] Record in the workbench handoff: sessions on the old prompt reclaim within 900 s idle.

---

## P4: agents-boox-sketch - text rows (0.15.0)

Repo: `code/agents-boox-sketch`, worktree `.worktrees/boox-notebook-annotations-p4/agents-boox-sketch` from `origin/main` (9fc3711, v0.14.3). Read `AGENTS.md`, `MEMORY.md` (2026-11-03 "Shapes are strokes", 2026-11-04 "Pen ink latency after #40", "Board overlays", the P0/P1 entries of v0.14.x), `ROADMAP.md`, `docs/device-checklist.md`. Commands: `mise run test`, `mise run lint`, `mise run test:screenshot`, `mise run screenshot:record` (only for new goldens), `mise run build`. Single test: `./gradlew :core:model:test --tests '<Class>'` or `./gradlew :app:testDebugUnitTest --tests '<Class>'` (through the mise env). App path prefix `app/src/main/kotlin/io/github/szymonrychu/booxsketch/`; model prefix `core/model/src/main/kotlin/io/github/szymonrychu/booxsketch/model/`; api prefix `core/api/src/main/kotlin/io/github/szymonrychu/booxsketch/api/`.

Merge gate: P3 Tasks 3.2 and 3.3 done.

### Task 4.1: Notebook model types (shared foundation for P5 and P6)

**Files:**
- Create: `model/notebook/TextRun.kt`, `model/notebook/EditOp.kt`, `model/notebook/SourceMap.kt`
- Modify: `model/Page.kt`
- Test: `core/model/src/test/kotlin/.../model/notebook/SourceMapTest.kt`, `NotebookPageTest.kt`, `model/NotebookStoreTest.kt` (app, decode of an old notebook)

**Interfaces (all `@Serializable`):**
- `data class ColourSpan(val from: Int, val to: Int, val color: PenColor)`
- `data class TextRun(val lineId: String, val specVersion: Int, val sourceLine: Int, val row: Int, val x0: Float, val wrapRows: Int = 1, val scale: Float = 1f, val display: String, val colourSpans: List<ColourSpan>, val sourceMap: SourceMap, val sourceStrokeIds: List<String>)`
- `data class SourceMap(val displayToSource: IntArray)` (size `display.length + 1`), `fun toSource(displayOffset: Int): Int`, companion `fun strip(sourceLine: String): Pair<String, SourceMap>` removing inline markdown (`**`, `*`, `_`, backticks, leading `#`s, list bullets kept as typed text) and `[[colour]]...[[/]]` markers (reuse `model/doc/MarkerSpan.kt` parsing), returning colour spans too via `fun stripWithColours(sourceLine: String): StrippedLine(display, map, spans)`.
- `data class PendingSegment(val clientId: String, val segmentId: String, val row: Int, val x0: Float, val x1: Float, val strokeIds: List<String>)`
- `data class EditOp(val id: String, val kind: OpKind, val target: OpTarget? = null, val at: OpAt? = null, val strokeIds: List<String>, val rect: List<Float>? = null, val region: RegionRef? = null)`, `enum class OpKind { REPLACE, DELETE, INSERT, IMAGE }`, `OpTarget(lineId, from, to, quote)`, `OpAt(lineId, offset, mode: AtMode { INLINE, AFTER_LINE })`, `RegionRef(id, part, afterLine: String?)`. Stroke ids in the model; the wire codec (4.2) maps them to indices.
- `Page` gains `text: List<TextRun> = emptyList()`, `consumed: Set<String> = emptySet()`, `pendingSegments: List<PendingSegment> = emptyList()`, `pendingOps: List<PendingOp> = emptyList()` with `PendingOp(clientId: String, op: EditOp)`; helper `val visibleStrokes: List<Stroke>` (strokes minus consumed).
- `Notebook` gains `conversationLocalId: String? = null` (OQ1 Recommended: the board notebook is bound to one conversation; see Task 4.7).

- [ ] **Step 1: Failing tests:** `SourceMapTest`: `strips_bold_and_maps_offsets_back`, `colour_markers_become_spans`, `heading_hashes_removed`, `bullet_kept_as_typed_text`, `round_trip_every_offset_monotonic`; `NotebookPageTest`: `visible_strokes_skip_consumed`; app `NotebookStoreTest.old_notebook_without_text_fields_loads` (JSON fixture of v0.14.3 shape).
- [ ] **Step 2:** Run - FAIL. **Step 3:** Implement. **Step 4:** PASS.
- [ ] **Step 5:** Commit `feat(model): notebook text runs, edit ops and source maps`. Push the branch: P5a and P6 worktrees branch from here.

### Task 4.2: Wire DTOs, layout codec, client and Room v4

**Files:**
- Modify: `api/Dto.kt`, `api/ConnectorClient.kt`, `api/ApiError.kt`, `core/api/src/test/resources/openapi.json` (`mise run api:refresh <P2 worktree>/openapi.json`)
- Create: `model/notebook/LayoutCodec.kt`
- Modify: `app/.../data/Entities.kt` (`SpecEntity.layout: String? = null`), `data/AppDatabase.kt` (version 4, migration 3->4 adds the column), `documents/SpecSync.kt` (store `layout`)
- Test: `core/api/.../ContractTest.kt`, `ConnectorClientTest.kt`, `ErrorMappingTest.kt`, `core/model/.../notebook/LayoutCodecTest.kt`, app `data/MigrationV4Test.kt`, `documents/SpecSyncTest.kt`

**Interfaces:**
- DTOs: `GeometryDto`, `SegmentDto(id, row, x0, x1, strokes: List<Int>)`, `VisibleRunDto(lineId, row, x0)`, `EditOpDto`, `PageLayoutDto(version = 1, geometry, segments, runs, ops)`, `SpecLineDto(lineId, sourceLine, origin: JsonObject?)`, `OpStatusDto(id, status, note?)`, `SpecLayoutDto(lines, ops, baseVersion?, revertedFrom?)`; `SpecDto.layout: SpecLayoutDto? = null`; `SketchMetaDto.baseVersion: Int? = null` (`@SerialName("base_version")`).
- `ConnectorClient.uploadSketch(meta, pngs, strokes, layouts: List<ByteArray?> = emptyList(), regions: Map<String, ByteArray> = emptyMap())` adds parts `layout.<i>.json` and the given `region.<i>.<k>.png` names; `suspend fun revertSpec(conversationId: String, version: Int, baseVersion: Int): RevertResult(version, revertedFrom)`; `suspend fun specImage(conversationId: String, regionId: String): ByteArray`.
- `ApiError`: `StaleBase` (409 `stale_base`), `StaleTarget` (422 `stale_target`), `OpReplayed` (409 `op_replayed`), `Busy` (409 `busy`).
- `LayoutCodec.encode(page: Page, geometry: NotebookGeometry, segments: List<PendingSegment>, ops: List<EditOp>): ByteArray`: stroke ids map to the index of the stroke in `StrokesCodec.encode(canvas, page)` order (the same visible-stroke list the export uses); runs from `page.text`.

- [ ] **Step 1: Failing tests:** `ContractTest.layout_and_spec_layout_match_openapi` (every DTO field name exists in the fixture schema), `ConnectorClientTest.upload_sends_layout_and_region_parts`, `revert_posts_base_version`, `spec_image_get`, `ErrorMappingTest.stale_base_stale_target_op_replayed_busy`, `LayoutCodecTest.stroke_ids_map_to_strokes_json_indices`, `consumed_strokes_not_in_indices`, `MigrationV4Test.layout_column_added_and_null`, `SpecSyncTest.stores_layout`.
- [ ] **Step 2-4:** FAIL, implement, PASS. Strokes export must use `visibleStrokes` from now on (StrokesCodec and PNG export): add `PngExporterTest.consumed_strokes_not_exported`.
- [ ] **Step 5:** Commit `feat(api): notebook layout DTOs, revert and spec image calls`.

### Task 4.3: Segmentation of new handwriting

**Files:** Create `model/notebook/Segmenter.kt`; Test `core/model/.../notebook/SegmenterTest.kt`

**Interfaces:** `object Segmenter { fun segment(page: Page, geometry: NotebookGeometry, pageIndex: Int, exclude: Set<String> = emptySet()): Segmentation }`, `data class Segmentation(val segments: List<SegmentDraft>, val drawing: List<String>)`, `data class SegmentDraft(val id: String, val row: Int, val x0: Float, val x1: Float, val strokeIds: List<String>)`. Candidates: freehand (non-shape) visible strokes, not in `exclude` (ops and regions, from P5/P6), not in pending segments, centre not in the margin. Row = `geometry.rowAt(centreY)`; height > 1.5 x `rowPitch` or row null is drawing. Split on x gap > 2 cells. Ids `p<pageIndex>-r<row>-<n>`, n from 0 per row in x order.

- [ ] **Step 1: Failing tests:** `one_row_one_segment`, `gap_over_two_cells_splits`, `multi_row_stroke_is_drawing`, `margin_strokes_excluded`, `consumed_and_pending_strokes_excluded`, `shapes_are_drawing`, `top_margin_stroke_is_drawing`, `undo_after_apply_keeps_consumed_strokes_out_of_segments` (Review Focus 5: a page where undo re-added a stroke whose id is in `consumed` still yields no segment for it).
- [ ] **Step 2-4:** FAIL, implement, PASS. **Step 5:** Commit `feat(model): segment new handwriting into row lines`.

### Task 4.4: Run placement, wrap and row shift (Q16 A)

**Files:** Create `model/notebook/RunPlacer.kt`; Test `core/model/.../notebook/RunPlacerTest.kt`

**Interfaces:**
- `fun interface TextMeasure { fun width(text: String, scale: Float): Float }` (the app passes a `Paint`-backed one; tests a fixed 20 px per char).
- `object RunPlacer { fun apply(notebook: Notebook, version: Int, markdown: String, layout: SpecLayoutModel, measure: TextMeasure, geometry: NotebookGeometry): Placement }`, `data class Placement(val notebook: Notebook, val changedRows: Map<Int, IntRange>)` (page index to rows to repaint). `SpecLayoutModel` is the model mirror of `SpecLayoutDto` (in `model/notebook/SpecLayoutModel.kt`, mapped in the app).
- Rules: for each spec line in source order: `kept` keeps the existing run (updates `specVersion`, `sourceLine`, `display`); `segments` places a new run at the pending segment's page, row and `x0` and marks its strokes consumed and drops the pending segment; `op` replaces or inserts per the op's target (P5 fills ops; here only the `after_line` placement path is needed for revert and for origin-null lines, OQ6 Recommended: place after the run of the previous source line, new row, shift). Runs whose line id is gone are removed. Lines inside fenced blocks and table rows are never placed; their segments' strokes stay as ink (not consumed) and the pending segments are dropped. Fit: width <= column at scale 1 keeps 1; else scale = max(0.85, column/width); still too wide wraps at word boundaries into `wrapRows`. Occupied following rows and every stroke whose centre row is in them shift down by whole rows (`Command.ShiftRows` in `model/Commands.kt` so it is one undoable step). Overflow past the last row: OQ4 Recommended, rows that leave the page move to a new page inserted right after it.
- Revert: a layout with `revertedFrom` re-matches runs by line id; runs whose line ids are absent are removed; strokes consumed by those runs: OQ2 Recommended, they are un-consumed (become visible ink again).

- [ ] **Step 1: Failing tests:** `segment_line_placed_on_its_row_at_x0_and_strokes_consumed`, `kept_line_updates_text_in_place`, `removed_line_drops_run`, `long_line_shrinks_to_85_percent`, `longer_line_wraps_and_shifts_rows_below_with_their_ink`, `shift_is_one_undoable_command`, `shift_past_last_row_moves_overflow_to_a_new_page_after` (Review Focus 4), `fenced_lines_not_placed_ink_kept`, `origin_null_line_placed_after_previous_run`, `revert_removes_runs_and_restores_their_ink`.
- [ ] **Step 2-4:** FAIL, implement, PASS. **Step 5:** Commit `feat(model): place spec lines on rows with wrap and row shift`.

### Task 4.5: Text layer bitmap and board drawing

**Files:** Create `board/TextLayer.kt`; Modify `board/BoardView.kt` (`BoardSurfaceView.show(..., textLayer: Bitmap?)`, `paint` draws it after the grid and before strokes, skipping consumed strokes), `render/PageRasterExporter.kt` and `send/SendUseCase.kt` (notebook page PNG = text layer + visible ink, no grid); Test `app/src/test/.../board/TextLayerTest.kt`, `BoardBackgroundTest.kt`, `board/BoardScreenshotTest.kt` (new goldens `notebook_page_with_text_portrait`, `..._landscape`), `render/PageRasterExportTest` addition.

**Interfaces:** `class TextLayer(private val geometry: NotebookGeometry) { val measure: TextMeasure; fun render(page: Page, reuse: Bitmap?, overlay: List<RectF> = emptyList()): Bitmap }` - `ARGB_8888` 1404 x 1872, `Typeface.SANS_SERIF` 40 px black, anti-alias on, hinting off, headings bold, colour spans in their `PenColor.argb`, baseline `rowLineY(row) - 11`, `overlay` rects filled 50 percent grey (used by P5 strike preview). One cached bitmap for the current page.

- [ ] **Step 1: Failing tests:** `TextLayerTest.run_pixels_in_text_band_only`, `colour_span_drawn_in_pen_colour`, `scaled_run_is_narrower`, `overlay_rect_is_grey`, `render_under_50ms_robolectric_benchmark` (log the time; assert < 200 ms in Robolectric as the CI bound, record the device number in MEMORY); `BoardBackgroundTest.text_layer_under_strokes_over_grid`, `consumed_strokes_not_painted`; export test `notebook_page_png_has_text_and_no_grid` (keeps `GridNotExportedTest` green).
- [ ] **Step 2-4:** FAIL, implement, `mise run screenshot:record` for the two new goldens only, PASS with `mise run test:screenshot`.
- [ ] **Step 5:** Commit `feat(board): text layer drawn on notebook rows`.

### Task 4.6: Send with layouts; apply versions through one hold at pen idle

**Files:** Create `board/NotebookSync.kt`; Modify `send/SendUseCase.kt` (`send` writes `layout.<n>.json` per part and `base_version`), `send/Payload.kt` (`layout(dir, n)`, `PagesFile.baseVersion`), `send/OutboxRunner.kt` (passes layouts; maps `ApiError.StaleBase` to a failed item with reason `stale_base` and triggers spec sync), `board/BoardViewModel.kt` (`applyVersion(placement)`, `addPendingSegments`), `board/BoardScreen.kt` (wiring), `AppContainer.kt`; Test `send/SendUseCaseLayoutTest.kt`, `send/OutboxRunnerTest` additions, `board/NotebookSyncTest.kt`, `board/BoardChromeWiringTest` addition.

**Interfaces:**
- `SendUseCase.send(all, caption)`: for each exported notebook page, `Segmenter.segment`, record `PendingSegment`s with the client id (board marks them through `SendBoard.addPending(page: Int, segments: List<PendingSegment>)`), write layout bytes via `LayoutCodec`. `baseVersion` = the newest `specVersion` among runs of the sent pages' conversation, or the conversation's latest stored version when it has one, else null.
- `class NotebookSync(specs: SpecDao, board: BoardViewModel, holds: TextLayerHolds) { suspend fun onVersion(conversationServerId: String, version: Int) }` - reads `SpecEntity.layout`, runs `RunPlacer.apply` on `Dispatchers.Default`, renders `TextLayer` off the main thread, then `holds.swap(bitmap, dirty)`; `TextLayerHolds.swap` waits for pen idle (`onPenUpRefresh` 700 ms) and does sync committed, raw off, set bitmap, draw dirty rows, GU refresh, raw on - one `ChromeHolds` hold.
- Pending tick (spec 3.3.6): `TextLayer.render` draws a 12 px grey tick at `textLeft - 30` of each row with pending segments; a failed item clears that client id's pending segments and ops.

- [ ] **Step 1: Failing tests:** `SendUseCaseLayoutTest.layout_part_written_with_segments_and_base_version`, `pending_segments_recorded_with_client_id`, `drawing_strokes_not_segmented`; `OutboxRunnerTest.upload_sends_layout_parts` (MockWebServer), `stale_base_fails_item_and_syncs`; `NotebookSyncTest.version_applies_runs_and_consumes`, `version_while_pen_down_applies_after_idle_through_one_hold` (Review Focus 3: no bitmap swap while raw drawing is enabled; exactly one hold), `failed_item_clears_pending_ticks`.
- [ ] **Step 2-4:** FAIL, implement, PASS. **Step 5:** Commit `feat(board): send notebook layouts and render returned versions`.

### Task 4.7: Conversation binding and revert action (Q15 B)

**Files:** Modify `conversations/ConversationRepository.kt`, `board/BoardViewModel.kt`, `board/NotebookStore.kt` (one notebook file per conversation, OQ1 Recommended), `documents/DocumentScreen.kt` and `documents/DocumentViewModel.kt` (version picker gets "Revert to this version", OQ7 Recommended), `send/SendUseCase.kt` (`revert(conversationLocalId, version, latest): SendOutcome` through the outbox, kind `REVERT` with payload `revert.json`), `data/Entities.kt` (`OutboxKind.REVERT` if kinds are an enum there); Test `documents/DocumentViewModelTest` additions, `send/SendUseCaseRevertTest.kt`, `board/BoardViewModelTest` additions, `documents/DocumentScreenshotTest` golden `version_picker_with_revert`.

**Interfaces:** `NotebookStore(dir: File).forConversation(localId: String): File` (`notebook-<localId>.json`); switching or creating a conversation saves the current notebook and loads the bound one (empty notebook for a new conversation). Revert: confirmation dialog "Revert to version N? This adds version M+1 with the text of version N." -> outbox item -> `ConnectorClient.revertSpec` -> `stale_base` / `busy` shown as the failed item reason ("The document changed; check the latest version" / "A translation is running; try again when it finishes"). The resulting `spec` event syncs and `NotebookSync.onVersion` re-renders the board.

- [ ] **Step 1: Failing tests:** `BoardViewModelTest.switching_conversation_swaps_notebook`, `new_conversation_starts_empty_notebook`; `SendUseCaseRevertTest.revert_enqueues_with_latest_as_base`, `revert_busy_and_stale_reasons`; `DocumentViewModelTest.revert_action_only_on_older_versions`.
- [ ] **Step 2-4:** FAIL, implement, PASS; record the golden.
- [ ] **Step 5:** Commit `feat(board): notebook per conversation and revert to a version`.

### Task 4.8: Instrumented test, docs, PR

- [ ] Add `app/src/androidTest/.../NotebookSendTest.kt::send_notebook_page_through_outbox` (MockWebServer answers 202 then a spec event with a layout; the run appears on the row). `mise run test:instrumented` runs on CI.
- [ ] `docs/device-checklist.md`: row text legibility, pen latency with a full text layer, version swap during writing. MEMORY.md dated lines: stroke-id-to-index mapping uses the export order; overflow and revert behaviours chosen (OQ2, OQ4, OQ6); notebook per conversation (OQ1).
- [ ] `mise run lint`, `mise run test`, `mise run test:screenshot`, `mise run build`, `mise run public-check` green.
- [ ] Commit `docs: notebook text rows checklist and memory`; push; PR (title in overview); review loop; merge only after P3 is done; confirm v0.15.0 release assets.

---

## P5a: agents-boox-sketch - edit ops (0.16.0)

Worktree `.worktrees/boox-notebook-annotations-p5/agents-boox-sketch`, branched from the P4 branch after Task 4.2; rebase on main after P4 merges. Merge gate: P4 merged.

### Task 5.1: Word boxes and tip resolution

**Files:** Create `model/notebook/WordBoxes.kt`; Test `core/model/.../notebook/WordBoxesTest.kt`

**Interfaces:** `data class WordBox(val from: Int, val to: Int, val left: Float, val right: Float, val row: Int)` (display offsets); `object WordBoxes { fun of(run: TextRun, geometry: NotebookGeometry, measure: TextMeasure): List<WordBox>; fun overlapped(boxes: List<WordBox>, x0: Float, x1: Float): IntRange?; fun nearestBoundary(boxes: List<WordBox>, x: Float): Int }` (wrapped runs give boxes on each of their rows).

- [ ] Tests: `boxes_follow_measured_widths`, `wrapped_run_boxes_on_second_row`, `overlap_expands_to_whole_words`, `nearest_boundary_between_word_centres`, `scaled_run_boxes_scaled`. FAIL, implement, PASS, commit `feat(model): word boxes of rendered runs`.

### Task 5.2: AnnotationClassifier (rules 2-4 of spec 4.3 with tool shapes)

**Files:** Create `model/notebook/AnnotationClassifier.kt`, `model/notebook/StrikeDetector.kt`; Test `AnnotationClassifierTest.kt`, `StrikeDetectorTest.kt` (fixture pages built in a `NotebookFixtures.kt` test helper)

**Interfaces:**
- `fun interface InsertMarkFinder { fun find(page: Page, geometry: NotebookGeometry): List<InsertMark> }`, `data class InsertMark(val boxStrokeId: String, val arrowStrokeIds: List<String>, val rect: RectF4, val tip: PointF2, val noteStrokeIds: List<String>)`; `ToolInsertMarks` implements it for `RECTANGLE` in the margin plus `ARROW` whose tail is within `SNAP_RADIUS` of one of `rectAnchors` and tip in the text column. (P5b adds `FreehandInsertMarks`.)
- `class AnnotationClassifier(private val finders: List<InsertMarkFinder>) { fun classify(page: Page, geometry: NotebookGeometry, measure: TextMeasure, newId: () -> String): Classification }`, `data class Classification(val ops: List<EditOp>, val opStrokeIds: Set<String>, val marginInk: List<String>)`. Rule order: (region ops come from P6 and are passed in `exclude` of `Segmenter`), insert, strike, replace, rest. Insert `at`: tip in text band -> `INLINE` at `SourceMap.toSource(nearestBoundary)`; else `AFTER_LINE` of the nearest run above. Strike: `StrikeDetector.isStrike(stroke, band)` with the Global Constraints thresholds, scribble (zig-zag) accepted when inside the band; target the touched words. Replace: strokes in an annotation band overlapping a run on that row, grouped by a 1-cell x gap; target the overlapped words. `quote` = source substring at `[from, to)`. Ops ordered by x within a line (Q13).
- `marginInk`: margin strokes in no insert mark - sent as ordinary ink (OQ3 Recommended); the prompt rule handles them.

- [ ] Tests: `StrikeDetectorTest.flat_wide_stroke_is_strike`, `tall_stroke_is_not`, `curvy_stroke_is_not`, `scribble_inside_band_is_strike`; `AnnotationClassifierTest.write_above_words_is_replace_of_those_words`, `strike_is_delete_of_touched_words`, `margin_box_and_snapped_arrow_is_insert_inline_at_boundary`, `arrow_tip_in_annotation_band_is_after_line`, `unsnapped_arrow_is_not_insert`, `margin_ink_without_box_is_margin_ink`, `two_ops_on_one_line_in_x_order`, `quote_is_source_text_with_markup_offsets`. FAIL, implement, PASS, commit `feat(model): classify handwritten replace, strike and margin insert`.

### Task 5.3: Send ops, pending state, optimistic strike, results

**Files:** Modify `send/SendUseCase.kt`, `board/NotebookSync.kt`, `model/notebook/RunPlacer.kt` (op origins and statuses), `board/TextLayer.kt` (strike overlay), `board/BoardViewModel.kt`; Test `send/SendUseCaseOpsTest.kt`, `RunPlacerTest` additions, `board/StrikePreviewTest.kt`, screenshot golden `pending_strike_overlay`.

**Interfaces:** On Send: `AnnotationClassifier.classify` first, its `opStrokeIds` go to `Segmenter.segment(exclude=...)`; `Page.pendingOps += PendingOp(clientId, op)`; layout carries ops; `baseVersion` required (non-null) when ops exist, else the send is refused locally with `SendOutcome.NothingToSend`-style outcome `NoBaseVersion` (cannot happen with runs present; assert). On a version: `op` origin lines place replaced or inserted text (insert `AFTER_LINE` takes the next row and shifts); `applied` ops consume their strokes; `rejected` ops keep their strokes visible and clear the pending op; the note of a rejected op goes to the feedback strip. Optimistic strike: at pen idle sync, `StrikeDetector` hits on visible runs add grey overlay rects for the touched words (local, not persisted; recomputed from page state). `stale_base` (Q17): pending ops of that client id are cleared, their strokes stay visible, the latest version is synced and rendered; the user re-sends.

- [ ] Tests: `SendUseCaseOpsTest.ops_in_layout_with_stroke_indices`, `op_strokes_not_segmented`; `RunPlacerTest.applied_replace_updates_words_and_consumes_annotation`, `rejected_op_keeps_ink`, `applied_insert_after_line_takes_next_row_and_shifts`, `applied_delete_removes_words`; `StrikePreviewTest.strike_overlay_drawn_at_idle_not_on_pen_up`; `NotebookSyncTest.stale_base_keeps_marks_and_renders_latest`. FAIL, implement, record golden, PASS, commit `feat(board): send edit ops and apply their results`.

### Task 5.4: Docs and PR

- [ ] Device checklist: strike, replace, insert end to end; misclassification rate note. MEMORY lines for thresholds that changed on device (if any). `mise run lint`, `mise run test`, `mise run test:screenshot`, `mise run build` green. Commit, PR, review loop, merge after P4; confirm v0.16.0.

---

## P5b: agents-boox-sketch - freehand loops and arrows (Q12 C) (0.17.0)

Own PR because it is a separate recognition surface a reviewer can reject alone. Branch from the P5a branch after Task 5.2; rebase after P5a merges.

### Task 5.5: Freehand shape recognition

**Files:** Create `model/notebook/FreehandShapes.kt`; Test `core/model/.../notebook/FreehandShapesTest.kt` (fixtures: hand-traced point lists in `core/model/src/test/resources/freehand/*.json`, at least 6 loops, 6 arrows, 6 negatives: letters O, D, 0, underline, bracket, a long word)

**Interfaces:**
- `object FreehandShapes { fun loop(stroke: Stroke): Loop?; fun arrow(strokes: List<Stroke>, startIndex: Int): FreehandArrow? }`
- `data class Loop(val strokeId: String, val polygon: List<PointF2>, val bounds: RectF4)`: closed when the end-to-start gap < 1 cell (53 px) or the path self-intersects within the last 15 percent; area >= (1.5 cells)^2; bounds width and height >= 1 cell (rejects letter O at handwriting size, about 0.6 cell).
- `data class FreehandArrow(val strokeIds: List<String>, val tail: PointF2, val tip: PointF2)`: a shaft stroke with chord length >= 2 cells and mean chord deviation < 0.25 x chord, plus a head either in the same stroke (the last 20 percent turns back by 100-170 degrees) or in one or two following strokes (each < 0.6 cell long, starting or ending within 0.3 cell of a shaft end, together forming a V opening away from the shaft); `tip` is the shaft end at the head.

### Task 5.6: FreehandInsertMarks and classifier wiring

**Files:** Modify `model/notebook/AnnotationClassifier.kt` (add finder), `send/SendUseCase.kt` (finders list `listOf(ToolInsertMarks, FreehandInsertMarks)`); Test `AnnotationClassifierTest` additions.

**Interfaces:** `object FreehandInsertMarks : InsertMarkFinder`: a `Loop` whose bounds lie in the margin (>= 80 percent of the bounds right of `marginX`), with the strokes whose centre is inside its polygon as the note; an arrow (freehand `FreehandArrow` or the `ARROW` tool) whose tail lies within `SNAP_RADIUS` of the loop outline and whose tip is in the text column. Mixed marks count: tool rectangle plus freehand arrow, freehand loop plus tool arrow. Loop and arrow strokes never become segments.

- [ ] Tests: `FreehandShapesTest.traced_loops_recognised`, `letters_are_not_loops`, `straight_arrow_with_v_head`, `arrow_with_hook_head_in_one_stroke`, `underline_is_not_arrow`; `AnnotationClassifierTest.freehand_loop_and_arrow_make_insert`, `tool_rect_with_freehand_arrow_makes_insert`, `loop_in_text_column_is_not_insert`, `arrow_tail_far_from_loop_is_not_insert`. FAIL, implement, PASS. Commit `feat(model): freehand loops and arrows make margin inserts`.
- [ ] Device checklist item "freehand loop plus arrow insert, 10 tries, count misses"; MEMORY line with the thresholds and the why. PR, review loop, merge after P5a; confirm v0.17.0.

---

## P6: agents-boox-sketch - image regions, inline images, share bundle (0.18.0)

Worktree `.worktrees/boox-notebook-annotations-p6/agents-boox-sketch`, branched from the P4 branch after Task 4.2; rebase after P4 merges. Independent of P5a/P5b except a rebase conflict in `SendUseCase.send` (both add exclusions to `Segmenter`; resolve by unioning the sets).

### Task 6.1: IMAGE_REGION tool, icon, dashed drawing

**Files:** Modify `model/Stroke.kt` (`IMAGE_REGION("image_region")`, `isShape` includes it), `model/StrokesCodec.kt` (codec accepts the new wire name), `board/ToolIcons.kt` (dashed rectangle plus small mountain), `board/ToolPopups.kt` (shape popup third entry), `render/CanvasStrokeRenderer.kt` (dashed dark grey `0xFF555555` while pending; thin solid frame plus "image" label 20 px once applied), `ink/*` routing for shapes (same as `RECTANGLE`); Test `StrokesCodecTest.image_region_round_trip`, `ToolPopupsTest.shape_popup_has_image_region`, `ToolIconsScreenshotTest` golden, `ShapePreviewTest.image_region_drag_preview`, `OnyxShapeRoutingTest.image_region_routed_as_shape`.

- [ ] FAIL, implement, record goldens, PASS. Commit `feat(board): image region tool`.

### Task 6.2: Region crop and upload

**Files:** Create `render/RegionCropper.kt`; Modify `send/SendUseCase.kt`, `send/Payload.kt` (`region(dir, n, k)`), `send/OutboxRunner.kt`; Test `render/RegionCropperTest.kt`, `send/SendUseCaseRegionTest.kt`

**Interfaces:** `class RegionCropper { fun crop(page: Page, region: Stroke, textLayer: Bitmap?, canvas: Canvas, cfg: ConfigDto): ByteArray? }` - visible ink and the text layer inside `rectOf(region)` at canvas resolution, no grid, no frame, white background; shrink loop 0.85x while > `maxPngBytes` (reuse the `PngExporter` loop). Send: every pending `IMAGE_REGION` stroke on a sent page becomes an `EditOp(kind=IMAGE, rect, region=RegionRef(id=uuid, part="region.<n>.<k>.png", afterLine=<run above the rect top, or null>))`; strokes whose bbox centre is inside the rect go into `op.strokeIds` and the `Segmenter` exclude set; more than `max_regions_per_page` (4, fixed client constant until `/config` exposes it) refuses the send with `SendOutcome.TooManyRegions(page, max)`. Total bytes include regions.

- [ ] Tests: `RegionCropperTest.crop_has_ink_and_text_no_grid_no_frame`, `crop_shrinks_under_cap`; `SendUseCaseRegionTest.region_part_and_image_op_written`, `ink_inside_region_not_segmented`, `fifth_region_refused`. FAIL, implement, PASS. Commit `feat(send): crop image regions and upload them with image ops`.

### Task 6.3: Region frame states on the board

**Files:** Modify `model/notebook/RunPlacer.kt` (an applied image op marks the region stroke `regionApplied` - store in `Page.appliedRegions: Set<String>`), `render/CanvasStrokeRenderer.kt`; Test `RunPlacerTest.applied_image_op_marks_region_and_keeps_ink`, screenshot `region_frame_pending` and `region_frame_applied`.

- [ ] Ink inside a region is never consumed. FAIL, implement, record, PASS. Commit `feat(board): region frames show pending and applied states`.

### Task 6.4: Documents renders inline images

**Files:** Create `documents/SpecImageCache.kt`; Modify `documents/MarkdownPaginator.kt` (image node `images/<uuid>.png` becomes an `ImageBlock` from the cache, else the literal `[image]` as today), `documents/BlockRenderer.kt` (scale to the column width, keep aspect), `documents/DocumentViewModel.kt` (prefetch images of the version before paginating); Test `documents/SpecImageCacheTest.kt`, `MarkdownPaginatorTest.image_reference_renders_image_block`, `unknown_image_falls_back_to_text`, `DocumentScreenshotTest` golden `document_with_inline_image`.

**Interfaces:** `class SpecImageCache(root: File, client: suspend () -> ConnectorClient?) { suspend fun get(conversationServerId: String, regionId: String): ByteArray?; fun cached(conversationServerId: String, regionId: String): File? }` - files at `<filesDir>/spec-images/<conversation>/<region>.png`; deleted with the conversation (hook into the existing conversation delete).

- [ ] FAIL, implement, PASS. Commit `feat(documents): inline spec images`.

### Task 6.5: Share .md as a zip bundle (Q10 B)

**Files:** Create `documents/ShareBundle.kt`; Modify `documents/DocumentHost.kt` (Share .md: when the markdown references images, share `spec-v<N>.zip` through `FileProvider` with type `application/zip`; else the existing `text/markdown` text share), `app/src/main/AndroidManifest.xml` and `res/xml/file_paths.xml` (FileProvider for `cache/share/` if not present); Test `documents/ShareBundleTest.kt`, `DocumentsFlowTest.share_with_images_shares_zip`.

**Interfaces:** `object ShareBundle { suspend fun build(dir: File, version: Int, markdown: String, image: suspend (String) -> ByteArray?): File }` - zip entries `spec-v<N>.md` (markdown unchanged, references stay `images/<id>.png`) and `images/<id>.png` for every referenced id; a missing image is left out and its id listed in a `MISSING.txt` entry.

- [ ] Tests: `zip_has_markdown_and_every_image`, `missing_image_listed`, `no_images_no_zip_path_taken`. FAIL, implement, PASS. Commit `feat(documents): share the spec with its images as a zip`.

### Task 6.6: Docs and PR

- [ ] Device checklist: region end to end, share to a file manager, hand-off target receives images. MEMORY lines (cache location, zip naming, client region cap). `mise run lint`, `mise run test`, `mise run test:screenshot`, `mise run build`, `mise run public-check` green. PR, review loop, merge after P4 (and after P3); confirm the release tag.

---

## P7: release verification, device round, final review

### Task 7.1: Release and pin check

- [ ] Confirm GitHub Releases for every app version of P4-P6 (APK asset, stable latest link) and that `v2.1.0` of the connector is the deployed image (`workbench-observability:k8s-triage`, sonnet).
- [ ] Workbench superrepo: bump the `code/agents-app-connector`, `code/agents-helmfile`, `code/agents-boox-sketch` pointers to their merged main (one commit per bump, as the recent history does: `chore(code): bump ...`).

### Task 7.2: Device round (user, Note Air 6C)

- [ ] Hand the user one checklist (from `docs/device-checklist.md` items added in P4-P6 plus spec 9 "Device checks"); collect results; each failure goes through `superpowers:systematic-debugging` and a `fix(...)` PR (patch release).
- [ ] Manual eval run of cases 12-15 (`uv run python scripts/eval_sketches.py` against the deployed connector, user approval first since it creates conversations); record scores in connector MEMORY.

### Task 7.3: Final review and retro

- [ ] Final reviewer (sonnet) checks delivered scope against plan.md sections 3-6 with the answers table above (all 18 answers, OQ answers), under- and over-delivery, and writes `docs/plans/boox-notebook-annotations/retro.md`. The orchestrator relays its recommendations.
- [ ] Close taskboard T-46 (`done`) when everything landed.

## Self-review notes

- Spec coverage: items 2 (P4), 3 (P5a 5.2/5.3), 4 (P5a), 5 (P6), 6 (P5a, P5b), contract 5.1-5.3 (P2), rendering 6 (P4.5/4.6), risks table (thresholds, holds, bitmap reuse, stale base) mapped; Q10 B bundle (6.5) and hand-off images (2.8); Q15 B route (2.7) and UI (4.7); Q12 C (P5b). Items 1 and the bugfix shipped in P0/P1.
- Deliberately dropped by answers: `PageKind`, "New drawing page", "Show my ink" toggle.
