# Boox sketch app - plan

Status: future work, not started. A sibling hive builds it later; nothing here is to be built now.

Research briefs (read these, do not duplicate them):
- SDK brief: `.scratchpad/boox-sketch-app/research-boox-sdk.md` (cited below as SDK-n.n)
- Feasibility brief: `.scratchpad/boox-sketch-app/research-feasibility.md` (cited below as FEAS-A/B)

## 1. What and why

An Android app for the BOOX Note Air 6C to sketch with pen brushes close to the official Boox
apps, press "send" to push the sketch to an agent for analysis, and read the agent's feedback,
deduced text and graphs. The conversation is one continuous agent session (same model as a
Matrix room bound to a session today), so the app needs its own connector. The screen is split
into a drawing board and a chat/preview panel. Fast pen input through the Onyx SDK is mandatory.

## 2. Decisions (user answers, 2026-11-01)

1. Kotlin is allowed for the Android app. This is an explicit exception to "Python only,
   except web frontends"; record it in the new repo's AGENTS.md and MEMORY.md.
2. No Matrix-client shortcut (this overrides the FEAS-A recommendation). A new Python
   connector service with its own Postgres DB, shaped like agents-matrix-connector, with a
   client-plugin shape so more clients/apps can be added later.
3. The connector service owns images: sketch PNG + stroke JSON in, agent graphs/images out.
   There is no separate pictures epic.
4. Accept the Onyx SDK brushes only (fountain, brush, ballpoint, charcoal x2, marker; pressure
   and tilt). Not full Boox Notes parity (SDK-2.5, SDK-2.6).
5. The hive generates the signing keystore; it lives only as GitHub Actions secrets plus a SOPS
   backup (use the `workbench-secrets:sops-secret-helper` flow).
6. Distribution: sideloaded signed APKs from GitHub Releases. No Play Store.
7. Accept the unclear SDK licence and plain-HTTP repo.boox.com for personal use; pin and
   checksum the AARs (Gradle dependency verification, or vendored AARs).
8. Target device: BOOX Note Air 6C. Shop page extracts say Android 16 and 4,096 pressure levels
   with tilt (SDK-4.3, SDK-2.5; medium confidence). To verify on the device: Android version,
   firmware, that `TouchHelper` delivers raw events, which stroke styles work.
9. This is a plan for later.

## 3. Research findings (summary)

- SDK: `onyxsdk-pen` 1.5.8, `onyxsdk-device` 1.3.6, `onyxsdk-base` 1.8.9 on
  `repo.boox.com` Nexus, maintained through Sep-Oct 2026 (SDK-1.2..1.4, SDK-1.11). Written docs
  are stale; the official demo source is the reference (SDK-1.8, SDK-1.9).
- Live-preview styles cover the accepted brush set; the app renders committed strokes itself
  (SDK-2.2, SDK-2.3). Custom brushes unsupported (SDK-2.6).
- POMs say BSD-3, demo repo Apache-2.0, Onyx never answered the licence question (SDK-3.1..3.3).
  No API key or signing requirement found (SDK-3.4).
- The SDK uses hidden APIs (HiddenApiBypass) and is firmware dependent; known breakages exist
  (SDK-4.1, SDK-4.5). Packaging defects: `-dontshrink`, `libc++_shared` and mmkv collisions
  (SDK-4.7..4.9). Sideloading avoids the Play target-SDK and 16 KB page constraints (SDK-4.6).
- No emulator story. Maintained apps gate Onyx paths on manufacturer and class presence and fall
  back to normal rendering (SDK-5.3, SDK-5.5). A real Boox is mandatory for latency and brush
  checks.
- Headless CI build and signing work (SDK-6.2..6.5). Modern reference consumer: Notable
  (AGP 9.5, Kotlin 2.4, JDK 17, pen SDK 1.5.8).
- Existing system gaps (FEAS-A): orchestrator `POST /sessions/{id}/messages` takes text only;
  the wrapper turn `files` map is text only and not passed by the dispatcher; any-mcp returns
  text content only; agents-web never renders images; the orchestrator chat relay forwards to a
  single upstream (`ORCH_CHAT_URL`); `files/download` is not on the service-token port.
- Pod (FEAS-B): no JDK, Android SDK, Docker or KVM; JDK/SDK installable via mise in user space;
  repo.boox.com over HTTPS fails TLS here, plain HTTP works; JVM screenshot tests are possible.

## 4. Design

### 4.1 Connector service `agents-app-connector` (Python, own Postgres)

Modelled on agents-matrix-connector: same layout, agents-common for settings, pool, migrator,
status-guarded queue transitions, orchestrator client and run tracker. One writer per table.

Client-plugin shape: a small `ClientPlugin` interface (authenticate, normalise inbound into a
common `InboundMessage` with attachments, deliver outbound `OutboundMessage`, optional push
channel). The sketch app is plugin `sketch`; a second plugin later reuses the same core
(conversations, session mapping, attachment store, queue, dispatch, deliver). Plugin id is part
of every conversation row and URL (`/client/v1/<plugin>/...`).

Tables (sketch, all with timestamps): `devices` (id, name, token_hash, created, revoked),
`conversations` (id, plugin, device_id, session_id, state), `inbound` (queue: id,
conversation_id, text, status, attempts), `attachments` (id, owner message, direction in/out,
kind sketch_png | sketch_strokes | image, mime, size, sha256, storage path, created, expires),
`outbound` (queue: id, conversation_id, text, status), `runs` (idempotent dispatch markers).

Session mapping onto the orchestrator: one conversation = one orchestrator session. First
message starts a `first` run (session `app-<run id>` from the sketch preset); later messages
are `follow` runs into the same running session; a deleted session is released and the next
message starts a new one (same behaviour as the Matrix connector's room binding, FEAS-A).
Reuse the agents-common `dispatch`/`deliver` idempotent markers. Reply text is the final turn
text, chunked only if a client plugin needs it. A conversation list is minimal in MVP: one
conversation per device, "new conversation" button later.

Auth (personal device): pairing token. An admin route (behind the existing oauth2-proxy and
CIDR allowlist, like the matrix connector UI API) mints a device token once; the user types or
scans it into the app; only its sha256 is stored; stored on device in Keystore-backed
EncryptedSharedPreferences; revocation by deleting the device row. The device-facing API is a
public ingress path with bearer auth, rate limits, size caps and TLS (cluster ingress and
cert-manager; confirm public exposure with the user before deploying).

API (JSON, versioned, `/client/v1/sketch`):
- `POST /messages` multipart: `meta` (JSON: client message id for idempotency, text, canvas
  info), `sketch.png`, `strokes.json`. Returns `{message_id, conversation_id}`; 202 once stored
  and queued.
- `GET /messages?after=<cursor>&wait=<s>` long-poll of the conversation (user and agent
  messages with status `queued|running|done|failed`, text, attachment refs).
- `GET /attachments/{id}` raw bytes (bearer auth), with `ETag`.
- `GET /events` SSE stream with the same cursor semantics (preferred push channel, falls
  back to long-poll). `POST /messages/{id}/cancel` later.

Upload formats (from FEAS-A): `sketch.png` grayscale 8-bit, long edge <= 1568 px; `strokes.json`
`{version, canvas:{w,h,dpi}, strokes:[{tool,width,points:[[x,y,pressure,t_ms]]}]}`. SVG skipped.
Caps: PNG 4 MiB, strokes 2 MiB, enforced server side.

Reply formats: markdown text plus image attachments. The agent renders graphs to PNG in its
workdir (matplotlib via `uv run --with matplotlib`, graphviz) and references them; the connector
fetches via orchestrator `files/download`, validates PNG/JPEG magic bytes and size, and stores
them as outbound attachments. The sketch preset tells the agent: grayscale, high contrast,
thick lines, no colour-only encoding. The app renders markdown natively (Markwon) and images
inline; ```mermaid and ```vega-lite fences are shown as code in MVP, rendered offline in a
WebView with bundled mermaid.js / vega-embed in the complete scope.

Push channel to the app: SSE `/events` while foreground, with long-poll fallback and a
catch-up `GET /messages?after=` on every reconnect. No FCM (no GMS dependence). Optional
foreground-service notification while a run is in progress.

Image storage and retention: bytes on a PVC mounted by the connector (not in Postgres), path
by attachment id, sha256 recorded; DB holds metadata. Default retention 30 days for sketches
and outbound images (setting), a daily purge job, per-device disk quota; deletion of a
conversation deletes its files. Own DB, no sharing with other services.

### 4.2 Orchestrator and wrapper changes (attachments)

- claude-code-wrapper: binary turn files (a `files_b64` map or `{content, encoding}`), per-file
  cap, written under `.attachments/<message id>/` in the workdir.
- agents-orchestrator: `attachments: [{name, mime, data_b64}]` on message create (capped, about
  4 MiB total), stored with the message, passed by the dispatcher to the wrapper turn;
  the prompt names the paths so the agent `Read`s the PNG (vision) and parses the JSON.
  `files/download` added to the service-token port. openapi and migration updated.
- agents-common: orchestrator client support for attachments and file download.
- Orchestrator chat relay multi-upstream routing is NOT needed in MVP (the app connector replies
  through its own queue); it is needed only for agent-initiated pushes to the app (complete).
- any-mcp-tatara-plugins: `orchestrator_chat_send` `attachments` param (complete scope).

### 4.3 The Android app (Kotlin, new repo `agents-boox-sketch`)

Layout: a split screen, drawing board plus chat/preview panel, landscape (board left, chat
right) and portrait (stacked), draggable divider, panel collapsible to full-screen board.
Send button and a clear/undo/eraser/brush toolbar sit on the board. Chat panel shows the
conversation (markdown, images, status line "sent / analysing / replied") and previews a
tapped reply image full size.

Input abstraction: `StrokeInput` interface with two implementations.
1. Onyx fast path: `TouchHelper.create(view, RawInputCallback)` with `setLimitRect` and
   exclude rects (toolbar, divider), raw drawing enabled while the pen is on the board, stroke
   style set from the chosen brush, tilt via device stroke parameters, `closeRawDrawing` on
   pause. Raw input points feed the local stroke model; committed strokes are drawn by the app
   with SDK wrappers where available (SDK-2.3), otherwise plain polylines with width by pressure.
2. Normal-touch fallback: `MotionEvent` with `getPressure` and `AXIS_TILT` onto a plain
   Canvas. Selected at runtime: manufacturer is ONYX and `TouchHelper` class present and a
   first raw event arrives within a probe; any exception disables the fast path for the
   session (SDK-5.3). This also makes the app runnable and testable off-device.

Local stroke model (pure Kotlin, no Android types): `Stroke(tool, width, points[x,y,pressure,t])`,
`Document(strokes, canvas size)`, undo/redo stack, erase by stroke, JSON serialisation
matching `strokes.json`, PNG export by a renderer interface (grayscale, white background,
long edge capped). Autosave of the document to app storage so a crash loses nothing.

Send flow: tap Send, freeze input, export PNG and strokes, enqueue in a local outbox
(survives restarts and offline), upload with the client message id (idempotent retry with
backoff), show "sent", start SSE, render the reply when it arrives, keep the sketch editable
and allow "send again" as a follow-up in the same session; optional text caption field.

Build: AGP/Gradle current stable, JDK 17, Onyx AARs pinned with checksums, minimal transitive
set (exclude geometry and mmkv as Notable does only if testing shows they are safe; see
SDK-6.2), `pickFirsts` for `libc++_shared` (SDK-4.9). Do not enable R8 shrinking assumptions
because of `-dontshrink` (SDK-4.8). NOTICE file for transitive licences (SDK-3.5).

## 5. Components and repos touched

| Repo | Change |
|---|---|
| agents-app-connector (new, Python) | connector service, plugin core, `sketch` plugin, Postgres schema, PVC storage |
| agents-boox-sketch (new, Kotlin) | the Android app, mise tasks, CI, signed release |
| claude-code-wrapper | binary turn files |
| agents-orchestrator | message attachments, `files/download` on service-token port, openapi |
| agents-common | client support for attachments and download |
| agents-helmfile | release for the connector (CNPG DB, PVC, ingress), pins, sketch preset/preamble, caps |
| any-mcp-tatara-plugins | `orchestrator_chat_send` attachments (complete scope) |
| agents-web (optional) | show image attachments and the app connector in the Chats page |
| workbench (this repo) | AGENTS.md components table, hard-rule exception note for Kotlin |

New repos need `workbench:component-add`; it only knows python/typescript/generic scaffolds, so
the Android repo is added as generic and then scaffolded by hand.

## 6. Test approach

- Connector, orchestrator, wrapper, common: normal pytest suites per component (`mise run
  --cd code/<name> test`), plus a connector e2e with a fake orchestrator for image in / image
  out, idempotent retries, caps, retention purge and auth.
- App: JVM unit tests for the stroke model, serialisation, PNG export, outbox, API client
  against a fake server (MockWebServer); Robolectric + Roborazzi screenshot tests for the split
  layout (landscape, portrait) and chat rendering, which the agent can read as PNGs; lint
  (ktlint/detekt, Android lint). CI: build + test on PR; signed release only on main.
- No emulator or cloud device reproduces Onyx raw drawing or e-ink (SDK-5.1). Device test rounds
  by the user: install the APK, ink latency, brush feel, ghosting and refresh modes, split
  layout, battery, SSE across sleep. Each round ends with a short written checklist from the
  user; the app carries a "send debug info" path to the session to make reports cheap.

## 7. Risks

- Onyx SDK: hidden APIs, firmware-dependent breakage, no device matrix, poor maintainer
  responsiveness, unclear licence (SDK-4.5, SDK-3.3, SDK-1.12). Mitigation: fallback input
  path, pinned versions, device checks first.
- Brush parity is partial by decision; calligraphy and custom brushes unavailable (SDK-2.5).
- repo.boox.com is plain HTTP and single-vendor (SDK-6.6). Mitigation: checksums, vendored AARs
  in a private cache if it goes down.
- Public ingress for a device API on a home cluster: abuse, token leakage. Mitigation: hashed
  tokens, rate limits, size caps, revocation, no other routes exposed.
- Keystore loss: secrets are write-only. Mitigation: SOPS backup, tested restore.
- Android developer verification for sideloaded apps (FEAS-A "Distribution"): check on the
  Note Air 6C before relying on browser installs; `adb install` is exempt.
- Large images through the orchestrator (b64 in JSON) can bloat messages; caps and retention
  keep it bounded.
- E-ink SSE across device sleep: reconnect plus cursor catch-up, tested on device.
- Hard-rule conflicts: Kotlin exception (granted) and the "services talk only via queue or HTTP"
  rule, which the design respects (the app only calls the connector's HTTP API).

## 8. Scope

MVP: connector with the `sketch` plugin, pairing-token auth, upload PNG + strokes, text reply
by long-poll, attachments through orchestrator and wrapper; app with split layout, Onyx fast
path plus fallback, pen/eraser/undo, the accepted brushes, send flow with outbox, markdown
reply, inline image reply, CI-signed sideloadable APK.

Recommended: SSE push, agent-generated graph images, retention job and quotas, offline
autosave, conversation reset, debug-info path, helmfile deploy with ingress and alerts.

Complete: mermaid/vega offline rendering, agent-initiated pushes (chat relay multi-upstream,
`orchestrator_chat_send` attachments), agents-web view of app conversations, multiple
conversations per device, second client plugin as a proof of the plugin shape.

## 9. Task groups and estimate

Agent wall-clock estimate, one hive working sequentially with parallel review:
1. Wrapper binary files, orchestrator attachments and download route, common client: 3 tasks, ~3 h.
2. agents-app-connector scaffold, schema, plugin core, sketch plugin, auth, storage, e2e:
   ~8 tasks, ~8 h.
3. Helmfile release, ingress, preset, secrets, deploy: ~3 tasks, ~2 h (plus user approval of
   public exposure).
4. Android scaffold, mise/CI, keystore and release pipeline, dependency pinning: ~3 tasks, ~3 h.
5. App stroke model, renderer, export, outbox, API client, SSE: ~6 tasks, ~6 h.
6. App drawing board (Onyx path, fallback, brushes), split layout, chat rendering: ~6 tasks, ~7 h.
7. Device test rounds: 2-4 rounds of user installs; each fix cycle ~1-2 h agent time, plus the
   user's availability.
Total about 30 tasks, roughly 30-35 h of agent time excluding user device rounds.
Order: 1, 2, 3 (testable with curl), 4, 5, 6, then device rounds, then Recommended/Complete.

## 10. Open questions for the sibling hive

1. Does the Note Air 6C actually run Android 16 and does `TouchHelper` deliver raw events on its
   firmware? Verify first with the official demo APK before any app work.
2. Public exposure of the device API: dedicated hostname and Cloudflare/ingress path, or a
   private network path (VPN) only? Needs the user's decision before deploy.
3. Orchestrator attachment transport: base64 in JSON (simple, MVP) or multipart/raw upload?
4. Is gradle dependency verification enough for the HTTP-only Onyx repo, or vendor the AARs in
   a repo/cache (licence unclear)? Is the TLS failure from the pod also present on GitHub runners?
5. Retention defaults (30 days) and per-device quota values; should the user be able to delete
   a conversation from the app?
6. Does the "send" button send only the current page, or a multi-page notebook? MVP assumes one
   canvas per message.
7. Keystore SOPS backup location (which workbench file) and rotation policy.
