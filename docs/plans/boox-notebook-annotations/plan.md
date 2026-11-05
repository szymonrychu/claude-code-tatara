# boox-notebook-annotations: notebook grid, rendered text rows, handwritten edits, image regions, margin inserts

Status: plan only, for future implementation. Components: `code/agents-boox-sketch` (Kotlin app),
`code/agents-app-connector` (Python connector, translator tools and the `sketch-translator` preset),
`code/agents-helmfile` (connector pins). Baselines read on 2026-11-05: agents-boox-sketch origin/main
`f641889` (v0.13.2; the `code/` checkout is stale at `860695d`), agents-app-connector origin/main `4f764ce`
(v2.0.2), agents-helmfile origin/main (connector image `2.0.1`). App paths are relative to
`app/src/main/kotlin/io/github/szymonrychu/booxsketch/` unless they start with a module name.

## 1. What and why

User request (verbatim):

> Launch the claude-code orchestrator and prepare a plan (for future implementation):
> 1. I need gentle light-grey grid (as if its a notebook- it might need to be sparse- see below)
> 2. Once the agent parses the handwriting, I want the text show up in the grid at around half of the grid
>    height, so I can handwrite above the parsed/rendered text (space between grid lines split into two
>    halfs- bottom with parsed text, upper part for place for my annotations)
> 3. such hand annotation above the text, means that I want to replace the text with the new one
> 4. If I cross the digital text (stroke through) it should be removed
> 5. Besides rectangle and arrow I also need a special tool: I will mark with rectangle place, where agent
>    isn't supposed to parse anything, instead the portion of the rendering should be treated as picture and
>    put into the markdown as in-line image
> 6. there should also be a wide margin at the right, where I can simply write a text, then draw a shape
>    around it with an arrow pointing somewhere in the digital text- this would mean, that I want to insert
>    text somewhere in the notes
>
> Bugfixes to tackle within this push:
> 1. when I open the left, or right toolbox tapping on the drawing area should dismiss the toolbox(es),
>    instead of drawing over the canvas.

Why: today the loop is "draw a page, send, read the spec elsewhere (Documents), annotate a frozen raster
of it, send again". The user wants one surface that behaves like a paper notebook: handwriting turns into
typed text in place, on the same rows, and every later correction is a pen gesture next to the text it
changes (write above to replace, strike to delete, box plus arrow from the margin to insert, a box to keep
a drawing as a picture). That needs (a) a row geometry the app and the translator share, (b) text that
stays anchored to rows and to the strokes it came from, (c) an edit-operation contract instead of "here is
a picture, guess what changed", and (d) a board that can show a text layer without hurting pen latency.

Deferred backlog from T-36, status in this push:

- 5 mm light-grey grid (WIP `feat/board-grid`): re-opened here, reworked into the notebook grid (phase 1).
- Bottom-left quick cluster: noted, not doing now.
- Board PR3 tests (PR #46): noted, not doing now (it is `CONFLICTING`; it stays deferred).

## 2. Research findings

### 2a. agents-boox-sketch reuse points (origin/main f641889)

- Stroke model: `:core:model` `Stroke(id, tool, width, points, color)`, `Tool` has `RECTANGLE` and `ARROW`
  (`isShape`), six `PenColor`s (`model/Stroke.kt`). Shapes are strokes, so undo, erase, hit test and export
  are shared (MEMORY 2026-11-03 "Shapes are strokes"). A new image-region tool is one more `Tool` entry.
- Page model: `Page(strokes, changedSinceSend)`, `Notebook(canvas, pages, current)` (`model/Page.kt`); the
  board canvas is fixed `Canvas(1404, 1872, 300f)` (`board/BoardViewModel.kt:202`) and is fitted and centred
  in the view by `BoardGeometry` (`board/BoardView.kt:48`), so page coordinates do not change on rotation.
- Shape geometry: `rectOf`, `rectAnchors` (8 anchors), `snapShape` (40 px `SNAP_RADIUS`, same-anchor rule),
  `arrowHead`, `shapeOutline` (`model/ShapeGeometry.kt`). An arrow whose tail snaps to a margin rectangle is
  already detectable from the stored points.
- Hit test: `hitStrokes` with segment distance (`model/HitTest.kt`); reusable for strike-through against
  glyph boxes.
- strokes.json: `StrokesCodec` v3, strokes are written in order without ids (decoder generates `s0, s1`);
  the layout contract below references strokes by index within `strokes.<i>.json`, so no codec change.
- Board surface: `BoardSurfaceView.paint` fills white, draws an optional `background` bitmap (used today by
  Documents for the frozen page), then the strokes, clipped to the dirty rect. While raw drawing is live a
  committed stroke never touches the surface; the surface catches up in `syncCommitted` when the pen is idle
  or before any hold (MEMORY 2026-11-04 "Pen ink latency after #40"). A text layer fits as a second
  page-sized background bitmap drawn in the same pass.
- Overlays and holds: every overlay change goes through `ChromeHolds` (hold raw drawing, wait until each
  overlay reported its rects, release), popups have their own `popup` key, a close does a GC full refresh
  (MEMORY 2026-11-04 "Board overlays", board-pr2 entries). `OverlayControl.dismissAll` / `hideAll` in
  `board/BoardScreen.kt:356-372` hide strip, popup and panel in one burst.
- Tap to dismiss today: `TapDetector` (`board/BoardView.kt:150-205`) accepts finger taps only; pen taps are
  strokes that arm the 600 ms auto-hide (`ShellState.AUTO_HIDE_AFTER_STROKE_MS`). Whether finger events reach
  the view while raw drawing is on is still an open device-checklist item (`docs/device-checklist.md` "Side
  panel and tap to dismiss"). So with raw drawing on, a pen tap on the board inks immediately (the firmware
  draws before the app sees anything) and the overlays only go away 600 ms later; a finger tap may not
  arrive at all. That is the reported bug.
- `FingerSwipeTracker` (`ink/FingerSwipeTracker.kt`) reads finger events from the Onyx wrapper's window
  callback even while raw drawing owns the pen (Documents page turns); the same feed can drive the tap.
- Documents: `MarkdownPaginator` (JetBrains markdown parser plus `StaticLayout`), fixed `DocumentLayout`
  (`BODY_TEXT_PX` 34), frozen pages in `AnnotationStore`, `PagePacker` in `:core:model/doc`. Markdown images
  are rendered as the literal text `[image]` (`documents/MarkdownPaginator.kt:381`); `ImageBlock`
  (`documents/BlockRenderer.kt:65`) already draws a bitmap block (mermaid), so image support is a small add.
  `splitColourMarkers` parses `[[red]]` markers for text runs.
- Send path: `send/SendUseCase.kt`, `send/Payload.kt` (`PagesFile`, `writeMeta`), `core/api` `SketchMetaDto`
  with `pages` and `annotates` (`api/Dto.kt:44-76`), outbox FIFO per conversation with idempotent client ids;
  `SpecSync` and `FeedbackSync` pull versions and feedback after each refresh.
- Device geometry: Note Air 6C portrait view 1860 x 2480 px (`w930dp-h1240dp` xhdpi, MEMORY Task 19), 300 ppi
  black-and-white layer. Portrait scale page-to-view is 1860 / 1404 = 1.325, so 1 mm = 8.91 canvas px in
  portrait; landscape fits the page height (scale 0.994), so the same canvas distance is about 25 percent
  smaller on glass in landscape, with roughly 46 mm of empty board on each side of the page.

### 2b. Grid WIP (`.worktrees/boox-grid/agents-boox-sketch`, branch `feat/board-grid`)

- Uncommitted, based on `f5ac1ac` (11 commits behind main): new `board/BoardGrid.kt` (light grey
  `0xFFD3D3D3`, 1 px lines, 5 mm pitch from display `xdpi`/`ydpi`, lines inside the dirty clip only, one
  reused `FloatArray`), a 3-line hook in `BoardSurfaceView.paint` after the white fill, `BoardGridTest`
  (5 tests), `GridNotExportedTest` (PNG export, page raster export and strokes.json never contain the grid),
  a MEMORY entry and a device-checklist item.
- Reusable as is: the drawing loop, the clip discipline, the not-exported guarantee and its tests.
- Must change for notebook rows: the pitch is in view pixels from the display dpi and anchored at the view
  page corner, so in landscape the grid no longer lines up with page coordinates. Rows must be defined in
  page-canvas pixels (the unit text and strokes are stored in) and scaled by `BoardGeometry` like the ink.

### 2c. PR #46 (`feat/boox-board-pr3`, "test(board): combined overlay replays and screenshots")

Open, all checks green on its last run, but `mergeStateStatus DIRTY` / `CONFLICTING` against main. Test-only
(integration replays, 10 overlay goldens). Deferred by the user; not touched here. Its overlay goldens will
need re-recording once the grid lands, which is one more reason to keep it deferred until after phase 1.

### 2d. agents-app-connector (origin/main 4f764ce, v2.0.2)

- Upload: `POST /app/v1/sketch/sketches`, multipart, `meta` (`SketchMeta`, `extra=forbid`: `client_id`,
  `conversation`, `conversation_id`, `caption`, `pages[{page, canvas}]`, `annotates`), parts `sketch.<i>.png`
  and optional `strokes.<i>.json`; `max_pages` 4 (orchestrator caps attachments at 8 per message);
  `request.form(max_files=2 * max_pages)` and any unknown form field is 422 `invalid_request`
  (`plugins/sketch/router.py:112-140`). Idempotency: `(device_id, client_id)` lock plus a fingerprint of the
  meta JSON and every part's sha256 (`_gate`, router.py:43).
- Storage: files under `/data/<device_id>/<attachment_id>` on a 5Gi RWO PVC; table `attachments` (kind,
  page, size, sha256, `expires_at`, `purged_at`); `GET /attachments/{id}` serves owned files with ETag, 410
  after purge (router.py:445). Retention purges sketch files; nothing today is kept forever.
- Translator: one session per conversation, preset `sketch-translator`, started through
  `agent_runs.dispatch` and fed through `agent_runs.deliver` (`worker.py`), images as orchestrator message
  attachments. Results come only through MCP tools served by the connector on port 8002 (`translator_tools.py`):
  `document_write(markdown)` stores spec version N+1 and emits a `spec` event; `feedback_add(kind, text,
  where)`. Specs live in `specs(conversation_id, version, markdown, inbound_id, sketch_ids, run_id)`.
- Annotation turns: `meta.annotates {spec_version, pages[{page, doc_page, lines[a,b]}]}`, the prompt always
  carries spec vN in full plus an "annotated spec" rule (strike means delete, arrow from a note means insert,
  margin notes apply to nearest lines) (`plugins/sketch/__init__.py render_prompt`, `system_append.md`).
- Preset: `plugins/sketch/preset.json` plus `system_append.md`, model `claude-sonnet-5-5`, deny list covers
  Bash, Write, Edit, MultiEdit, NotebookEdit, WebFetch, WebSearch, Task, Agent, `mcp__any-mcp__*`,
  `mcp__ccw__*`, `mcp__plugin_*`, `mcp__claude_ai_*`; no allow list (the orchestrator refuses it from a
  non-human). It is pushed by `scripts/ensure_preset.py` (manual run against the orchestrator admin API);
  it is not in helmfile values and has no version pin; running sessions keep the old prompt until reclaimed
  after 900 s idle.
- ROADMAP out of scope: "server-side crop and re-render from strokes". So image regions are cropped by the
  app (Q10 keeps a server crop only as a rejected option).
- Eval set: `eval/sketches`, `eval/expected`, `eval/specs` cases 01-11 (10 is the annotated spec), checked by
  `tests/test_eval_set.py`.
- agents-helmfile: image tag `values/agents-app-connector/common.yaml:4` (`2.0.1`, one patch behind),
  chart `helmfile.yaml.gotmpl:216-217`; pins asserted by `tests/test_app_connector_release.py`,
  `tests/test_check_pins.py`.

### 2e. Onyx SDK constraints (pen 1.5.8, device 1.3.6; official docs target 1.4.11)

- `setLimitRect(limit, excludeList)` takes several exclude rects; the vendor demo updates limit and exclude
  rects at runtime without toggling raw drawing
  (https://github.com/onyx-intl/OnyxAndroidDemo/blob/master/doc/Onyx-Pen-SDK.md,
  https://github.com/onyx-intl/OnyxAndroidDemo/blob/master/app/OnyxPenDemo/src/main/java/com/onyx/android/eink/pen/demo/PenManager.java).
  Our app re-opens raw drawing for new rects inside a hold (device-proven); keep that path.
- `setRawDrawingEnabled(true)`: "the screen will not refresh" until raw drawing is closed or disabled
  (Onyx-Pen-SDK.md). Any text-layer change must therefore go through the existing hold (raw off, draw,
  refresh, raw on), never a draw while raw is live.
- Refresh modes: DU black/white only, GU 16-level grey partial (default), GC 16-level grey full, REGAL
  partial for text pages (https://github.com/onyx-intl/OnyxAndroidDemo/blob/master/doc/EPD-Update-Mode.md,
  https://github.com/onyx-intl/OnyxAndroidDemo/blob/master/doc/EPD-Screen-Update.md). A light grey survives
  GU/GC/REGAL; in DU (and the pen's own fast mode) it most likely snaps to white (inference, not documented).
  The vendor guide asks for black/white or 16-level grey as main colours
  (https://github.com/onyx-intl/OnyxAndroidDemo/blob/master/doc/Eink-Develop-Guide.md).
- Note Air 6C: 10.3 in Carta 1200 with Kaleido 3, 2480 x 1860 at 300 ppi black and white, colour layer
  1240 x 930 at 150 ppi (https://ewritable.net/brands/boox/tablets/boox-note-air6-c/, review site; the
  vendor page answered 429). Greys are drawn by the 300 ppi layer, so a 1 px grey line stays sharp.
- Not documented anywhere: whether pen events inside an exclude rect are delivered to the view as normal
  `MotionEvent`s (device check in phase 0), and finger/stylus filter APIs (only unofficial AI-generated
  pages mention `enableFingerTouch`; not used).

## 3. UX

### 3.1 Notebook page geometry (all values in page-canvas px of the 1404 x 1872 page; mm are portrait on glass)

Recommended (Q3 B, Q4 B):

- Grid cell `c` = 53 px (6 mm). Row pitch `R` = 2c = 106 px (12 mm). The grid is sparse: light grey dots
  (2 x 2 px, `0xFFBDBDBD`) at every cell intersection, a solid 1 px row line (`0xFFD3D3D3`) every `R`, no
  vertical lines in the text column. The row line is the text baseline guide; the dot row halfway is the
  band split.
- Top margin one row (106 px, page title space, no text placed), then 16 rows (1872 - 106 = 1766, 16 x 106 =
  1696, 70 px foot).
- Each row is split: upper half (53 px) = annotation band, lower half (53 px) = text band. Rendered text
  sits in the text band: baseline at 0.2 x 53 = 11 px above the row line so descenders stay in the band,
  text size 40 px (cap height about 28 px, 3.2 mm on glass; about 34 px in the 1568 px export, above the
  28 px legibility floor recorded for Documents).
- Text column: x from 53 px (one cell of left padding, clear of the strip edge) to the margin line.
- Right margin: 30 percent of the page width, x from 983 px to 1404 px (421 px = 47 mm in portrait, about
  35 mm on glass in landscape because the whole page is scaled 0.75x there). A 1 px light grey vertical
  line marks it; inside the margin the grid shows dots only.
- Landscape: the page keeps its portrait canvas and is centred (the board never re-lays out the page, which
  keeps every stored stroke and text anchor valid). The side areas stay blank and refuse ink as today.
- The grid, row lines and margin line are view-only: never in the PNG, never in strokes.json (keeps
  `GridNotExportedTest`). The geometry goes to the connector as numbers (section 5).
- Page kinds (Q2): a notebook page (rows plus margin) or a drawing page (plain sparse dot grid, no rows,
  no margin, no text layer). The page strip popup gets "New notebook page" and "New drawing page".

### 3.2 Item 1: grid

Rebase `feat/board-grid` onto main, then rework `BoardGrid` to take a `NotebookGeometry` in page px and draw
through `BoardGeometry` (scale, dx, dy) so dots and rows stay locked to strokes in both orientations. Same
clip discipline, same single paint pass, no new surface frame.

### 3.3 Item 2: parsed text on the rows

1. The user writes on rows of a notebook page and taps Send (Q7 A; the existing send button and outbox).
2. The app segments new handwriting into lines (section 4.2) and uploads the page PNG, strokes.json and a
   `layout.<i>.json` with the geometry and the segments.
3. When the new spec version arrives, the app draws each transcribed line in the text band of the row it
   was written on, left aligned at the segment's left edge, in a sans serif black (Q5 A); `[[colour]]`
   spans keep their pen colour.
4. The source strokes of every transcribed text line are hidden (kept in the page as consumed, Q6), so the
   row now shows typed text in the lower half and a free upper half. Strokes the translator kept as a
   drawing (mermaid, table, wireframe) stay as ink and are not replaced.
5. A line longer than the text column shrinks to at most 85 percent size, then wraps into the next row's
   text band; if that row is taken, following rows and their ink shift down by whole rows (Q16 A).
6. Pending state: segments waiting for a version show a small grey "sent" tick at the row start; a failed
   turn clears it and shows the feedback strip.

### 3.4 Item 3: replace by writing above

- Handwriting in the annotation band of a row that has rendered text, overlapping the text's x range,
  becomes a `replace` op. Target (Q8 A): the words whose glyph boxes overlap the annotation's x extent
  (expanded to whole words); the target quote is sent with the op.
- Visual feedback before Send: none extra; the ink itself is the mark. After the new version, the replaced
  words show the new text and the annotation strokes are consumed (hidden).

### 3.5 Item 4: strike-through

- A stroke whose bounding box lies mostly inside a text band, is wide and flat (height under 40 percent of
  the band, width over 1.5x its height, mean deviation from its own chord under 25 percent of the band) and
  crosses glyph boxes is a `delete` op on the words it touches (Q9 A).
- Optimistic: the struck words are drawn with a 50 percent grey overlay at once (local only, no upload yet)
  so the user sees the gesture was understood; the delete is final when the new version arrives.
- Scribble-out (a zig-zag over a word) is classified the same way when it stays inside the band.

### 3.6 Item 5: image region tool

- New tool `IMAGE_REGION` in the shape popup next to rectangle and arrow, icon: dashed rectangle with a
  small mountain glyph. Drawn like a rectangle (same drag, same fixed width), shown dashed in dark grey.
- On Send, the app crops the region from the page raster (ink inside the rect, text layer included when it
  overlaps, no grid, no dashed frame) at full canvas resolution, uploads it as a region part, and tells the
  translator "do not transcribe inside this rect, place image `<id>` here in reading order".
- On the board the ink inside a region stays as ink (it is the picture); the region frame stays visible
  until the version arrives, then it turns into a thin solid frame with a small "image" label so the user
  knows it is a picture in the spec.
- In Documents and in shared markdown the region is an inline image (`![image](images/<id>.png)`, Q10).

### 3.7 Item 6: margin insert

- The user writes in the right margin, draws a rectangle around it (rectangle tool) and an arrow from that
  rectangle to the digital text (arrow tool; the tail snaps to the rectangle's anchors as today, Q12 A/B).
- The app resolves the arrow tip (Q11 A): tip inside a text band: insert at the nearest word boundary of
  that row; tip in an annotation band or in the gap below the last text: insert as a new line after that row.
- The op carries the margin strokes inside the rectangle, the rectangle and arrow stroke indices and the
  resolved target; the inserted text appears where the arrow points (a new line takes the next row and
  shifts the rows below, Q16).
- After the version arrives, the margin note, its box and its arrow are consumed (hidden).

### 3.8 Bugfix: tap on the board dismisses open toolboxes

- While the strip, a popup or the side panel is visible, the board is in "dismiss mode": the whole board
  rect is added to the raw-drawing exclude list (one more rect in the same `ChromeHolds` change that shows
  the overlay), so the firmware draws nothing.
- Any pen or finger tap or drag starting on the board in dismiss mode calls `OverlayControl.dismissAll` and
  consumes the gesture up to its pen-up: no ink, no stroke in the model (Q18 A). `TapDetector` accepts
  `TOOL_TYPE_STYLUS` in dismiss mode and treats a pen down as the dismiss (no tap slop needed).
- Finger taps are also fed from the Onyx window callback (as `FingerSwipeTracker` does), so they work even if
  the firmware withholds view events while raw drawing is open.
- When the dismiss lands, the excludes drop back to the strip indicator and panel indicator only, and the
  hold releases raw drawing as today (one GC flash, already there for popup close).

## 4. Data model

### 4.1 App, `:core:model`

```kotlin
enum class PageKind { NOTEBOOK, DRAWING }

data class NotebookGeometry(        // page px; fixed per page at creation, stored with the page
    val cell: Int, val rowPitch: Int, val top: Int, val rows: Int,
    val textLeft: Int, val marginLeft: Int,
)

data class Page(
    val strokes: List<Stroke>,
    val changedSinceSend: Boolean,
    val kind: PageKind = PageKind.DRAWING,
    val geometry: NotebookGeometry? = null,
    val text: List<TextRun> = emptyList(),        // rendered lines placed on rows
    val consumed: Set<String> = emptySet(),       // stroke ids hidden after a version used them
    val pendingOps: List<EditOp> = emptyList(),   // sent, waiting for a version
)

data class TextRun(
    val lineId: String,          // stable connector line id, e.g. "L12"
    val specVersion: Int,
    val sourceLine: Int,         // 1-based markdown source line in that version
    val row: Int, val x0: Float, // placement on this page
    val wrapRows: Int = 1,
    val display: String,         // inline markup stripped, colour spans kept as ranges
    val colourSpans: List<ColourSpan>,
    val sourceStrokeIds: List<String>,
)
```

- Default values mean notebooks saved before this change load as drawing pages (normal decoding, not a
  compatibility shim).
- Glyph boxes are not stored; they are measured from `display` with the same `Paint` (deterministic) when
  hit testing.
- Row index of a point: `floor((y - top) / rowPitch)`; band: upper if `(y - top) mod rowPitch < rowPitch/2`.

### 4.2 Segmentation of new handwriting (app, pure Kotlin)

- Candidates: freehand strokes on a notebook page that are not consumed, not inside an image region, not
  in the margin, and not classified as an op (4.3).
- Row assignment: a stroke belongs to the row containing its vertical centre; a stroke spanning more than
  1.5 rows is a drawing stroke (row = null, sent unsegmented).
- Line segments: strokes of one row sorted by x, split where the horizontal gap exceeds 2 cells. Segment id
  `p<page>-r<row>-<n>` within the upload; fields `row, x0, x1, strokes[indices]`.
- Shapes (rectangle, arrow) outside the margin and drawing strokes are sent as drawing ink; the translator
  may turn them into mermaid as today.

### 4.3 Annotation classification (app, pure Kotlin, `AnnotationClassifier`)

Order of rules on Send, over not-consumed strokes of a notebook page that has text runs:

1. `IMAGE_REGION` strokes: `image` op; every stroke with its bbox centre inside the region joins it.
2. Margin: a `RECTANGLE` whose rect lies in the margin, strokes inside it, and an `ARROW` whose tail snapped
   to one of its anchors (within `SNAP_RADIUS`) and whose tip is in the text column: `insert` op. Tip
   resolution: row of the tip; text band: nearest word boundary by glyph box centres (char offset in
   `display`, mapped to the source offset); annotation band or empty row: `after_line` of the nearest run
   above. Margin strokes without a box plus arrow: sent as unclassified ink (Q12).
3. Strike: wide flat stroke in a text band crossing glyph boxes (3.5): `delete` op with the touched words.
4. Replace: strokes in an annotation band whose x range overlaps a run on the same row, grouped by a 1 cell
   gap: `replace` op with the overlapped words.
5. Everything else: new handwriting (4.2).

Op shape (app and wire):

```json
{"id": "uuid", "kind": "replace|delete|insert|image",
 "target": {"line_id": "L12", "from": 4, "to": 9, "quote": "milk"},
 "at": {"line_id": "L12", "offset": 9, "mode": "inline|after_line"},
 "strokes": [5, 6], "rect": [x, y, w, h],
 "region": {"id": "uuid", "part": "region.0.0.png", "after_line": "L11"}}
```

- `from` and `to` are char offsets in the markdown source line (the app maps display offsets back through
  the strip map kept with each run); `quote` is the source text there, so the translator and the connector
  can check the target still matches.
- Several ops touching one line are all sent, in x order (Q13 A).

### 4.4 Connector

- New column `specs.layout jsonb` (migration 0006): for the version, `lines: [{line_id, source_line, origin}]`
  where origin is `{"segments": ["p0-r4-0"]}`, `{"kept": "L12"}`, `{"op": "uuid"}` or null, plus
  `ops: [{id, status: applied|rejected, note}]` and `base_version`.
- Line ids are assigned by the connector at `document_write`: a kept line keeps its id, every other line gets
  the next `L<n>` of the conversation (monotonic, never reused).
- Segment anchors (page, row, x0) are not stored by the connector; the app keeps them locally keyed by the
  upload client id and segment id, and places lines from `origin`.
- New table `spec_images(conversation_id, region_id, attachment_id, created_at)`; region PNGs stored as
  attachment kind `spec_image` with `expires_at` null (never purged by retention, deleted with the
  conversation).

## 5. Translator and connector contract changes

### 5.1 Upload (`POST /sketches`)

- `SketchMeta` gains `base_version: int | None` (the spec version whose text the board showed; required when
  any layout carries ops; 409 `stale_base` when it is not the latest version, Q17 A).
- New optional parts per page `layout.<i>.json` (pydantic `PageLayout`: `version: 1`, `kind`, `geometry`,
  `segments`, `runs` (line_id, row, x0 of every visible run, so the model can relate the PNG to line ids),
  `ops`), and `region.<i>.<k>.png` (k < `max_regions_per_page`, new setting, default 4). Validation: op ids
  unique uuids, stroke indices within that page's strokes.json, rects inside the canvas, every `region.part`
  present and every region part referenced, `line_id` known in `base_version`, `quote` equal to the source
  text at `[from, to)` (422 `stale_target` otherwise).
- `request.form(max_files=...)` and the allowed-field set grow accordingly; `max_upload_bytes` still caps the
  total. The idempotency fingerprint already covers every part.
- Regions are stored at upload time (`spec_image` attachments) so a translator turn that never writes a
  version leaves them orphaned until the conversation is deleted (bounded by the per-device quota).
- The page PNG for a notebook page is the page raster with the text layer and all ink (consumed strokes
  excluded), no grid, so the model sees what the user saw.
- Region PNGs are not attached to the translator message (the attachment cap stays 8 per message); the page
  PNG already shows them.

### 5.2 Prompt and tools

- `render_prompt`: for a notebook page, after "Image i": the geometry in one line, the visible runs as
  `L12 row 4: "buy milk"`, the new segments as `p0-r4-0 row 4 x 60-900`, and each op as one line, e.g.
  `op 3f2a replace L12[4:9] "milk" with the handwriting above it (rect ...)`,
  `op 9c1d image region r1 (rect ...) after L11: do not transcribe inside`. Spec `base_version` in full, as for
  annotation turns.
- `system_append.md`, new "Notebook pages" section: transcribe each segment as its own markdown source line
  where the block type allows (paragraph, heading, list item); apply each op exactly at its target; an image
  op becomes `![image](images/<region_id>.png)` on its own line at its position and nothing inside its rect is
  transcribed; report every op as applied or rejected; ambiguous handwriting goes to `feedback_add`.
- `document_write(markdown, lines=None, ops=None)`:
  - `lines: [{n: int, segments?: [str], kept?: str, op?: str}]` provenance per source line;
  - `ops: [{id, status: "applied"|"rejected", note?}]`.
  - For a turn whose inbound has layouts, both are required and must cover every op id and every segment
    id (tool error `layout_incomplete` naming the missing ids, so the model retries in the same turn);
    `images/<id>.png` references must name regions of this conversation (`unknown_image`).
  - For other turns (plain drawing pages, Documents annotations) they are rejected if present.
- The spec event and `GET /conversations/{id}/spec/{version}` response gain `layout` (4.4).
- New route `GET /conversations/{id}/images/{region_id}.png` (device bearer, ownership, ETag), used by the
  app's Documents renderer and the board.

### 5.3 Versioning, idempotency, release

- Versions stay linear (one row per `document_write`). Op ids make re-delivery visible: an op id already
  reported in an earlier version's layout is rejected at upload (409 `op_replayed`); a client-id replay of the
  same upload stays the existing 200.
- Breaking change: the `document_write` tool gains required arguments for notebook turns and the
  translator prompt changes; the connector, the preset text and the app move together. No compatibility shim,
  no feature detection: a new app against an old connector gets 422 `invalid_request` on the unknown
  `layout.<i>.json` part and shows the existing "Not sent" dialog.
- Release order:
  1. agents-app-connector `2.1.0` (additive HTTP surface; the old app never sends layouts) with migration
     0006, the tool change, the prompt, eval cases; semver tag from main.
  2. agents-helmfile: pin image `2.1.0` and the chart; PR; apply only with the user's approval.
  3. `scripts/ensure_preset.py` against the orchestrator (operator step, after the apply). Sessions started
     on the old prompt finish within 900 s idle; until then a notebook turn on such a session fails with
     `layout_incomplete` and is retried by the model, worst case it fails and the user re-sends.
  4. agents-boox-sketch release (semver tag via its green-main release flow) with the notebook features.
     The bugfix (phase 0) and the grid (phase 1) do not depend on the connector and can ship first.

## 6. Rendering text on the board

- Layer: a page-sized `ARGB_8888` text bitmap per notebook page (1404 x 1872 x 4 = 10.5 MB; only the current
  page is kept, the neighbour is rebuilt on page switch), drawn by `BoardSurfaceView.paint` after the grid
  and before the strokes, in the same pass and the same dirty clip as the Documents background. Consumed
  strokes are skipped by the stroke loop. Text never lives in the stroke list, so undo, erase and export
  of ink stay unchanged.
- Font: `Typeface.SANS_SERIF` regular (Q5 A), 40 px at page scale, black, `isAntiAlias = true`, hinting
  off; headings bold at the same size (the row is fixed), list items keep their bullet as typed text.
- Fit: measure with `Paint.measureText`; if wider than the column, scale down to 85 percent, then wrap with
  `StaticLayout` across rows (Q16).
- New version: the app diffs `layout.lines` against the page's runs, updates runs, consumed stroke ids and
  pending ops, rebuilds the bitmap off the main thread, then applies it through one hold: sync committed ink,
  raw off, swap the bitmap, draw the union of changed rows as a dirty rect, GU refresh (REGAL if the device
  accepts it), raw on. A version that arrives while the pen is down waits for the pen-idle callback
  (`onPenUpRefresh`, 700 ms) so it never stalls live ink.
- Raw drawing: the text bitmap is never drawn while raw drawing is live (Onyx docs: the screen does not
  refresh while raw drawing is enabled), so the pen path of #41 is untouched.
- The optimistic strike overlay (3.5) is drawn into the same layer at pen-idle sync, not on pen-up.

## 7. E-ink and performance risks

| Risk | Mitigation |
|---|---|
| Light grey dots or lines vanish in DU/fast modes or ghost after many partial refreshes | Dots `0xBDBDBD`, lines `0xD3D3D3` (16-level grey safe); drawn only in GU/GC frames; device check of both orientations; Q3 C (ruled only) as fallback |
| Text layer swap blocks the pen | Swap only through a hold at pen idle; bitmap built off the main thread; dirty rect of changed rows only |
| 10.5 MB bitmap per page | Only the current page cached; `inBitmap` reuse; rebuilt in under 50 ms target (measured in a Robolectric benchmark and on device) |
| Dismiss mode toggles excludes on every overlay change | It rides on the existing hold of that change; no extra raw re-open |
| Strike vs handwriting misclassification | Conservative thresholds, optimistic grey overlay gives instant feedback, a wrong strike is undone with the normal undo before Send |
| Glyph boxes differ between devices or font versions | Boxes are measured at classification time from the same `Paint` that drew the run; the op carries the quote so a mismatch is rejected, not misapplied |
| Model ignores an op or misplaces text | Per-op status required by `document_write`; rejected ops keep their strokes visible; eval cases 12-15 |
| Row shift moves user ink | Only whole rows shift, ink anchored to shifted rows moves by the same delta in one undoable command |
| Region crop size | Crop at canvas resolution, PNG; capped by `max_png_bytes` with the existing 0.85x shrink loop |
| Several translator turns racing on one page | Outbox is FIFO per conversation; `base_version` plus 409 `stale_base` stops a stale op set |

## 8. Phases, sizes and release order

Scope: all six items and the bugfix are delivered at every level; MVP and Recommended differ only in the
options chosen in section 10. Estimates are agent wall-clock time including review.

| Phase | Repo | What | Size | Estimate |
|---|---|---|---|---|
| 0 | boox-sketch | Bugfix: dismiss mode (board exclude, stylus tap, window-callback finger tap), tests, device checklist | S | 1.5 h |
| 1 | boox-sketch | Notebook geometry and page kinds; rebase and rework `feat/board-grid` into page-px sparse grid, rows, margin line | M | 2.5 h |
| 2 | app-connector | Contract: `base_version`, `layout.<i>.json`, region parts, `spec_images`, migration 0006, `document_write(lines, ops)`, images route, prompt, eval cases 12-15, OpenAPI, README; release 2.1.0 | L | 6 h |
| 3 | helmfile | Pin 2.1.0 image and chart, PR, apply after user approval; operator runs `ensure_preset` | S | 0.5 h plus approval |
| 4 | boox-sketch | Segmentation, layout upload, `core/api` DTOs, spec layout sync, text layer render, consumed strokes, row placement and shift | L | 6 h |
| 5 | boox-sketch | `AnnotationClassifier` (replace, strike, margin insert), op upload, pending ops, op results, optimistic strike overlay | L | 5 h |
| 6 | boox-sketch | `IMAGE_REGION` tool and icon, crop and region parts, board frame states, Documents paginator renders `images/` via the new route (`ImageBlock`) | M | 3 h |
| 7 | boox-sketch | Release, device checklist round, final review and retro | S | 1.5 h plus device time |

Order: 0 and 1 ship independently (app releases as they land). 2 then 3 must be applied before the app
release that contains 4-6. 4, 5, 6 can be built in parallel worktrees against a mocked connector (OpenAPI
fixture refreshed from 2.1.0) but release together in one app version.

MVP to complete:

- MVP: options marked MVP in section 10 (every page a notebook page, 10 mm rows, whole-line replace, end of
  line inserts, no undo of applied edits, image refs without share bundle).
- Recommended: options marked Recommended (page kinds, 12 mm sparse rows, word-level replace, boundary
  inserts, revert route, share bundle with images, unclassified ink forwarded to the model).
- Complete (not now): connector-side deterministic application of delete and image ops, freehand loop and
  arrow recognition, per-op undo, notebook geometry on the Documents view, in-place editing of text by
  typing, bottom-left quick cluster, board PR3 tests.

## 9. Test strategy

- agents-boox-sketch, JVM unit (`:core:model`): row and band math; segmentation (gaps, multi-row strokes,
  margin exclusion); classifier rules with fixture pages (replace, strike, scribble, margin box plus arrow,
  region membership, unclassified); tip resolution to offsets; display-to-source offset map incl. colour
  markers; row placement and shift; layout diff applying a version; op JSON shape against the connector's
  OpenAPI fixture.
- agents-boox-sketch, Robolectric (`GraphicsMode.NATIVE`): `BoardGrid` in page px under portrait and
  landscape geometry; `GridNotExportedTest` kept; text layer bitmap (pixel checks of a run in the text band);
  dismiss mode wiring log (`BoardChromeWiringTest` style: overlay open adds the board exclude, pen down
  dismisses, no stroke reaches the model, hold releases with indicator rects only); version swap goes
  through one hold at pen idle; upload payload parts (`layout.<i>.json`, `region.<i>.<k>.png`, meta
  `base_version`) with MockWebServer; Documents paginator draws an image block.
- Roborazzi goldens: notebook page empty (portrait, landscape), page with text runs, pending strike overlay,
  region frame states, drawing page.
- Instrumented (CI emulator): dismiss on stylus tap with the touch fallback input; send of a notebook page
  through the outbox.
- agents-app-connector, pytest contract tests: `PageLayout` validation (bad indices, rect outside canvas,
  missing region part, unknown line id, quote mismatch 422 `stale_target`), 409 `stale_base`, 409
  `op_replayed`, fingerprint covers layout parts, region storage and the images route (auth, ownership, ETag,
  not purged by retention, deleted with the conversation), `document_write` with and without layouts
  (`layout_incomplete`, `unknown_image`, rejected extra args on plain turns), line id assignment and kept ids,
  migration 0006, prompt snapshot for a notebook turn and unchanged snapshots for plain and annotation turns,
  OpenAPI and README current.
- Translator golden fixtures (`eval/`): 12-notebook-lines (segments to lines), 13-replace-and-strike, 14-margin
  insert, 15-image-region; each with the page PNG, layout JSON, base spec and the expected markdown plus
  expected `lines` and `ops` statuses; `test_eval_set.py` checks the shape, a manual eval run checks the model.
- Device checks (Note Air 6C, checklist additions): dismiss by pen and finger with strip, popup and panel;
  grid visibility and ghosting after 50 strokes in both orientations; row text legibility; pen latency
  unchanged with a full text layer; version swap during writing does not stall ink; strike, replace, insert,
  region end to end.

## 10. Open questions

Each question has one option marked Recommended and one marked MVP (the same option may carry both).

Q1. Where does the notebook (rendered text on rows) live? (sections 3.3, 6)
- A. On the board's pages: handwriting turns into text in place; Documents stays a reader. (MVP, Recommended)
- B. Only in the Documents view: the spec is re-paginated on rows and annotated there; the board is unchanged.
- C. Both: board pages and a row-based Documents view.

Q2. Which pages are notebook pages? (section 3.1)
- A. Every board page is a notebook page (rows plus margin). (MVP)
- B. Per page: "New notebook page" or "New drawing page" (sparse dots, no rows, no text layer). (Recommended)

Q3. Grid pitch and sparseness? (section 3.1)
- A. Full 5 mm square grid (the WIP), every second horizontal line a row line: 10 mm rows, 5 mm bands. (MVP)
- B. Sparse 6 mm dot grid plus light row lines every 12 mm: 6 mm text band, 6 mm annotation band. (Recommended)
- C. Ruled lines every 12 mm with a faint dashed mid line, no dots or verticals.
- D. 5 mm dot grid with row lines every 15 mm (7.5 mm bands).

Q4. Right margin: where and how wide? (section 3.1)
- A. Inside the page, 25 percent of the width (39 mm portrait, about 29 mm landscape). (MVP)
- B. Inside the page, 30 percent (47 mm portrait, about 35 mm landscape). (Recommended)
- C. Inside the page in portrait; in landscape a wider page canvas uses the empty side area as margin.

Q5. Font and size of the rendered text? (section 6)
- A. System sans serif, black, sized to the lower half row (about 3.2 mm cap height). (MVP, Recommended)
- B. System serif, same size.
- C. A bundled handwriting-style font (OFL) so text blends with the ink.

Q6. What happens to the source handwriting once it is transcribed? (sections 3.3, 4.1)
- A. Hidden (kept in the page as consumed), no way to show it. (MVP)
- B. Hidden, with a "Show my ink" toggle in the page popup. (Recommended)
- C. Kept visible in light grey under the text.

Q7. When is a page translated? (section 3.3)
- A. On the existing Send (explicit). (MVP, Recommended)
- B. Automatically after 20 s of pen idle on a page with new ink.
- C. Automatically on page switch and on leaving the board.

Q8. What does handwriting above a line replace? (section 3.4)
- A. The words under the annotation's horizontal extent. (Recommended)
- B. The whole line. (MVP)
- C. Let the translator decide from the picture.

Q9. Strike-through granularity? (section 3.5)
- A. Whole words touched by the stroke. (MVP, Recommended)
- B. Exactly the characters covered.
- C. The whole line when 80 percent or more is covered, otherwise whole words.

Q10. Image region: storage and markdown form? (sections 3.6, 5.1, 5.2)
- A. App crops; connector stores the PNG (never purged while the conversation exists); markdown
  `![image](images/<id>.png)` served by a connector route; share and hand-off carry the reference only. (MVP)
- B. A, plus "Share .md" exports a zip with the images and hand-off attaches the images to the target
  session. (Recommended)
- C. App crops; connector embeds the image as a data URI in the markdown at `document_write`.
- D. Connector crops from the page PNG (needs the ROADMAP out-of-scope item re-opened).

Q11. Where does a margin insert go? (sections 3.7, 4.3)
- A. Arrow tip in a text band: nearest word boundary; tip above or below text: a new line after that row.
  (Recommended)
- B. Always at the end of the line the tip is on. (MVP)
- C. Always a new paragraph after the line the tip is on.

Q12. Which marks make a margin insert? (sections 3.7, 4.3)
- A. Only the rectangle tool plus the arrow tool (snapped tail); other margin ink is ignored. (MVP)
- B. Rectangle plus arrow tools as in A; other margin ink is sent as unclassified ink for the translator to
  interpret under the existing annotated-spec rule. (Recommended)
- C. The app also recognises freehand loops and freehand arrows.

Q13. Several annotations touching one line? (section 4.3)
- A. Send all ops in x order; the translator applies them in order and reports conflicting ones as rejected;
  rejected ops keep their ink. (MVP, Recommended)
- B. The app refuses to send and frames the conflicting marks.
- C. The last drawn mark wins silently.

Q14. Who applies the edit operations? (sections 5.2, 8)
- A. The translator applies structured ops to spec vN and reports a status per op; the connector checks
  coverage. (MVP, Recommended)
- B. The connector applies delete and image ops deterministically; the translator only transcribes replace and
  insert handwriting, then the connector applies them.

Q15. Undo of applied edits? (sections 5.3, 8)
- A. None; correct by annotating again. (MVP)
- B. "Revert to vN": a connector route that copies an older version (markdown plus layout) as a new version;
  the board re-renders. (Recommended)
- C. Per-op undo through a new translator turn.

Q16. Text longer than its row, and inserted lines? (sections 3.3, 6)
- A. Shrink to 85 percent, then wrap into following rows; rows below (and their ink) shift down by whole
  rows. (Recommended)
- B. Wrap only into free rows; when none is free, show the line truncated with a marker and the full text on
  tap; nothing shifts. (MVP)
- C. Re-flow the whole page from the markdown on every version (ink drawings become images).

Q17. The spec changed between what the board shows and the send (stale base)? (section 5.1)
- A. Connector refuses with 409 `stale_base`; the app re-renders the latest version and keeps the marks for
  the user to check and re-send. (MVP, Recommended)
- B. Apply the ops against the latest version anyway and let the translator resolve.

Q18. Bugfix: what does a tap on the board do while a toolbox is open? (section 3.8)
- A. With the strip, a popup or the side panel open, a pen or finger tap (or drag) on the board dismisses
  them all and is consumed: no ink. (MVP, Recommended)
- B. Dismiss and also draw the stroke.
- C. Consume only when a popup or the side panel is open; with only the strip shown the pen draws and the strip
  auto-hides.
