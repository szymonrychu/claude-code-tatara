# File download in file browser design

## Summary

Every downloadable row of the Files tree gets a small right-aligned download icon (MUI `FileDownloadOutlined`) that saves
the workspace file to the user's computer, byte-exact, for text and binary files of any size. claude-code-wrapper gains
a raw-bytes route `GET /v1/sessions/{id}/files/download?path=` built on the existing path guards; agents-orchestrator
streams it through `GET /api/v1/sessions/{session_id}/files/download?path=&agent_id=` in the one wrapper seam
(`api/workspace.py`); agents-web triggers it with a plain anchor to the relative basePath URL (no blob buffering). The
listing gains a `target_type` field so the UI can tell a symlink to a file from a symlink to a directory.

## Intent and why

User request (2026-10-27), verbatim: "In file browser, I need to be able to download a file. I expect small "arrow
down" icon aligned with right side of the file browser, that's going to download a file to my computer from agent's
workspace." Implementation order given by the user: 1. download, 2. markdown, 3. editor.

Today the only file read is `files/content`, JSON only: binary and over-1-MiB files carry `content: null`, so no file
can leave the workspace through the UI except by copying preview text.

## Goals

- G1: A small download (arrow down) icon on every file row of the Files tree, aligned to the right edge of the file
  browser.
- G2: Clicking it downloads that file from the agent's workspace to the user's computer, byte-exact, for text and binary
  files of any size (no 1 MiB preview cap).
- G3: New raw-bytes download route in claude-code-wrapper and an orchestrator route forwarding it, with the existing
  workspace path guards.

## Non-goals

- No directory or multi-file (archive) download.
- No upload.
- No expanding of symlinks to directories in the tree (they stay unexpandable, as today). Noted, not doing now.
- No deploy: this epic's repos are claude-code-wrapper, agents-orchestrator and agents-web; agents-helmfile pins are
  not in it (open question Q1).
- No fix of the 10 load-dependent agents-web timeouts (PresetForm, ScheduleForm, Endpoints, FiltersEditor) that pass
  alone; task verifies stay targeted (user decision). Noted, not doing now.

## Anti-goals

- A download that buffers the whole file in the wrapper, the orchestrator or the browser (breaks "any size").
- Any new way to read outside the workdir: the download must refuse exactly what `files/content` refuses today.
- The derived wrapper bearer in a URL, a response header, a body or a log line.
- A listing field that reveals anything about paths outside the workdir.
- Clicking the icon also opening the preview or selecting the row.

## Constraints

- Python only for services; TypeScript for agents-web. No backward-compatibility shims.
- Orchestrator layering pin: only `api/workspace.py` may import `agents_orchestrator.wrapper`
  (`tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper`).
- Orchestrator `openapi.json` is generated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`) and every
  route is documented in README `## API` (`tests/test_readme_api.py`); the wrapper README documents every route and error
  code (`tests/test_readme_api.py` there).
- agents-web: backends only through the relative `basePath` (`src/api/client.ts:base`); `src/api/schema.d.ts` is
  generated, never hand-edited; designRules (`src/layout/designRules.ts`): no `title=` on IconButton (aria-label), no
  colour literals outside `theme.ts`, spacing on the 0.5 grid.
- Environment (user decision U5): this container has no Docker. Every task `verify` runs without Docker. Checks only CI
  can run:
  - agents-orchestrator DB-backed tests (testcontainers Postgres), including `tests/test_api_files.py` (525 errors
    locally in the full run);
  - the contract suite's real-wrapper leg (`pytest -m integration tests/test_fake_wrapper_contract.py`, real wrapper
    image) and the kind e2e (`mise run test:e2e`, `tests/e2e/test_e2e_kind.py`);
  - claude-code-wrapper `tests/test_container.py` (docker) and the 3 process-group tests (`tests/test_manager.py::test_shutdown_stops_all`,
    `tests/test_pty_proc.py::test_exit_without_eof_still_fires`, `tests/test_pty_proc.py::test_close_terminates_group_then_kill`)
    that fail here because the container PID 1 is not an init reaper (environment, not code).
- pytest verify commands never add `-q`: both Python repos already set `-q` in `addopts`, and `-qq` hides the pass
  counts a hand-back must quote.

## Decisions

### D1: Wrapper raw-bytes route `GET /v1/sessions/{id}/files/download`

Decision (user decision U1): a new route in `api/files.py`, query `path` (relative to the workdir), bearer auth like
every `/v1` route. A new helper in `files.py` resolves with the existing `_resolve` (`resolve_in_workdir`), opens with
`_open_nofollow` (`O_RDONLY | O_NOFOLLOW | O_NONBLOCK`) and checks `S_ISREG` on `fstat` of that descriptor, all before
any response byte, so every refusal is today's JSON error: `400 invalid_path` (absolute, NUL, `..` or symlink escape,
unfollowable final symlink), `400 not_a_file` (directory, FIFO, socket, device, the workdir itself), `404 not_found`
(unknown session, missing path, vanished workdir), `401 unauthorized`. No new error code. A `200` streams the bytes
read from that descriptor in chunks of at most 1 MiB, in a worker thread, up to the `fstat` size, with
`Content-Length` set to that size; the descriptor is closed when the stream ends, fails or is abandoned. No size cap
(`limits.file_preview_max_bytes` does not apply); content is not passed through the redactor, as for `files/content`.

Alternatives: a `raw` flag on `files/content` (rejected: one route answering JSON or bytes, and the preview cap is its
contract); base64 inside JSON (rejected: buffers the whole file, a third larger, needs a cap).
Why: one route per representation, and the guards that already pin `files/content` (`tests/test_api_files.py::test_escapes_refused`,
`test_content_open_nofollow_and_fstat`) are reused rather than re-implemented.

### D2: Download response headers

Decision (U1, details my call): `Content-Type` is `mimetypes.guess_type` of the resolved file name (the preview's
`mime`), else `application/octet-stream`; `X-Content-Type-Options: nosniff`; `Cache-Control: no-store` (my call:
workspace files change under the agent); `Content-Disposition: attachment; filename="<fallback>"; filename*=UTF-8''<encoded>`
(RFC 6266 with the RFC 5987 extended value). The name is the last segment of the normalised requested path, so a
symlink downloads under the link's name, not the target's (my call: it is the name the user clicked). `<encoded>` is the
name's UTF-8 bytes (undecodable bytes replaced as the listing's `_printable` does) percent-encoded except RFC 5987
`attr-char`; `<fallback>` is the name with every character outside printable ASCII (0x20 to 0x7E), `"` and `\` replaced
by `_`.

Alternatives: always `application/octet-stream` (rejected: loses the type the preview already reports; `attachment`
plus `nosniff` already stops inline rendering); only `filename=` (rejected: non-ASCII names break).

### D3: Listing field `target_type`

Decision (my call, serves user decision U2; open question Q2): every listing entry gains `target_type`. For a `symlink`
entry it is `dir`, `file` or `other` (the `_entry_type` of the followed target) when the link resolves through
`resolve_in_workdir` to an existing path inside the workdir; `null` when the link is dangling, loops or resolves outside
the workdir (nothing about outside paths is revealed). For every non-symlink entry it is `null`. The orchestrator
`FileEntry` schema and the fake wrapper carry it; agents-web shows the download icon for `type == "file"` and for
`type == "symlink"` with `target_type == "file"`.

Alternatives: show the icon on every symlink and let the guard refuse (rejected: U2 says symlinks to directories show no
icon); probe each symlink from the UI with `files/content` (rejected: one request per symlink on every 3 s poll); new
`type` values such as `symlink_dir` (rejected: changes the enum every consumer switches on).
Why: the listing is the only place the UI learns entry types, and the wrapper is the only process that can stat the
target.

### D4: Orchestrator streaming route `GET /api/v1/sessions/{session_id}/files/download`

Decision (U1): in `api/workspace.py` (the layering pin), query `path` and optional `agent_id`, agent choice by the
existing `resolve_agent` (404 `not_found`, 409 `agent_not_ready`, 503 `unavailable`). A new `WrapperClient.open_download`
(`wrapper/client.py`, modelled on `events`) sends the streamed GET with the bearer only in `Authorization` and inspects
the status before any byte reaches the browser: wrapper 4xx is re-raised with the wrapper's status and code (token
scrubbed), 5xx is 502 `wrapper_error`, transport failure is 502 `wrapper_unreachable`, the same map as `forward`
(share one mapping helper rather than copying it). A 2xx becomes a `StreamingResponse` relaying the raw upstream chunks
(`aiter_raw`, so bytes and `Content-Length` stay exact) with the wrapper's `Content-Type`, `Content-Length` and
`Content-Disposition`, plus `X-Content-Type-Options: nosniff` and `Cache-Control: no-store` set by the orchestrator.
The upstream response is closed when the relay ends, fails or the browser goes away. No total timeout (any size);
connect and each read keep the client's `DEFAULT_TIMEOUT`. A failure after the first byte aborts the connection, so
the browser marks the download failed instead of saving a short file. OpenAPI: a `200` with
`application/octet-stream`, schema `string`/`binary`. README `## API` gets the route section. Not on the service-port
allowlist (my call: no service needs it, as for the other file routes); no Origin guard (top-level GET, like the other
file GETs).

Alternatives: redirect the browser to the wrapper (rejected: pod URLs are cluster-internal and the bearer must stay in a
header); buffer in the orchestrator (rejected: any size).

### D5: UI trigger is a plain anchor

Decision (user decision U3, kept): the icon is `IconButton component="a"` with `href` = the relative URL
`${base()}/sessions/<id>/files/download?path=<rel>` (new `fileDownloadUrl` in `src/api/files.ts`), the `download`
attribute set to the entry name, `size="small"`, `aria-label="Download <name>"`, icon `FileDownloadOutlined`
(`fontSize="small"`). It is the last element of the tree row and the name grows, so the icon sits on the right edge.
Its click handler calls `stopPropagation`, so the click neither opens the preview nor selects the row. Shown per D3; no
icon on `dir`, `other`, or `symlink` rows whose `target_type` is not `file`. No `agent_id`: the same first usable agent
the listing uses.

How errors surface (U3): a plain anchor cannot read the response, so a 4xx/5xx (403 at the ingress, 404 `not_found`,
409 `agent_not_ready`, 502) is shown by the browser (its download UI or error page), and the Files panel shows nothing.
Accepted because the file was just listed by the same agent choice, so errors are rare (a file removed between listing
and click, an agent restarting).
Alternative rejected: fetch plus blob (`URL.createObjectURL`), which could show the error inline but buffers the whole
file in browser memory (breaks "any size") and shows no browser progress.

### D6: Fake wrapper parity, one contract suite

Decision: `tests/fakes/fake_wrapper.py` gets the download route and `target_type`, and `tests/test_fake_wrapper_contract.py`
gets cases that run on both legs (fake locally, real image in CI), plus fake-only cases for what the real image cannot
set up (symlinks, a file over the preview cap). Why: orchestrator route tests run against the fake, so the fake must be
held to the real wrapper's contract (retro of generic-any-mcp-with-git-and: fakes encoded a wrong assumption).

### D7: Docker-free orchestrator route tests

Decision (U5): the orchestrator route's behaviour tests live in a new `tests/test_api_file_download.py` that needs no
database: a real `FakeWrapper`, `workspace.resolve_agent` monkeypatched to return a `WrapperTarget` for it (or to raise
`ApiError`), and a stub pool whose `connection()` is an async context manager. The DB-backed `tests/test_api_files.py`
is extended for agent choice and scoping on the new route and the listing key set; it runs in CI only.

### D8: Web client schema regenerated

Decision (user decision U4): after the orchestrator route lands, `npm run sync:api -- orchestrator` (vendors
`openapi/orchestrator.json`, `openapi/orchestrator.source`, regenerates `src/api/schema.d.ts`) and `npm run check:api`
stays green. The sync takes everything between the current pin (ff54218) and the orchestrator head.

### D9: Orchestrator pins the wrapper commit carrying the route

Decision: once the wrapper change is merged on claude-code-wrapper `main`, the orchestrator pins that merge commit in
the dev dependency (`pyproject.toml`, `uv.lock`), README `## Images` and `e2e/agent-test.Dockerfile` (`BASE_IMAGE`,
`WRAPPER_SHA`), and the kind e2e gets a download case, so CI's integration leg and e2e run the real route. Precedent:
done epic web-ui-cluster-tabs-with-fil task `wrapper-sha-pin`.

## Research

| Lens | Ran / skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| discovery (cartographer per repo) | ran: `.scratchpad/discovery/agents-orchestrator.md`, `.scratchpad/discovery/agents-web.md`; the claude-code-wrapper brief covers the slash-commands epic, so wrapper facts come from the orchestrator brief's `ccw:` references and direct reads of `src/claude_code_wrapper/files.py` and `api/files.py` | reuse `resolve_in_workdir`/`_resolve`/`_open_nofollow` (ccw files.py:30,57,68); `resolve_agent`, `forward`, `get_client` (orchestrator api/workspace.py:88,206,179); `events` streaming pattern (wrapper/client.py:234); `Row` label and the stopPropagation precedent (agents-web FilesPanel.tsx:39, TerminalPanel.tsx:146) | client-side download from `FileContent` (agents-web brief do-not-build: content is null for binary and too_large) |
| research-code-internal | skipped: the plan adds no parser or subsystem; one helper and one route per repo, all callers grepped | - | - |
| research-code-external | skipped: no open fork; raw file download behind an authenticated proxy is a standard shape | - | - |
| research-papers | skipped: no algorithmic core | - | - |
| research-docs | skipped: `StreamingResponse` (wrapper api/turns.py:166, api/events.py:103) and httpx streaming (orchestrator wrapper/client.py:234) are already used the same way; RFC 6266 section 4.3 and RFC 5987 section 3.2 define `filename*` | RFC 6266 `filename*=UTF-8''` with an ASCII `filename` fallback (D2) | - |

## Research inputs

Workflow proposals from the retros of recently done epics, recurring first:

- Recurring (generic-any-mcp-with-git-and, cross-session-messaging-and, paste-env-contents-into-the): defects found late
  because test fakes encoded the same wrong assumption; ACs must tie fakes to the real output. Acted on by
  fake-wrapper-download (one contract suite over the fake and the real image, D6).
- Recurring (cross-session-messaging-and): hand-backs must quote the verify summary line with counts; run pytest with a
  summary-printing flag, not bare `-q`. Acted on by every Python task (`verify` adds no `-q` on top of `addopts`):
  wrapper-file-download-route, fake-wrapper-download, wrapper-client-download, orch-file-download-route,
  orch-wrapper-pin-download.
- Recurring (paste-env-contents-into-the, matrix-read-receipts): a ruling not pinned by a test was found only in
  review; each ruling in Notes names its pin test. Acted on by wrapper-file-download-route (filename fallback, symlink
  name, `target_type` null cases) and web-download-icon (which rows get the icon).
- Recurring (agents-matrix-connector-depl and later): live apply and smoke tasks run far over the seed. Not applicable:
  no live task in this epic (Q1).
- One-off (cross-session-messaging-and): task ACs must name existing files; new tests are marked "(new)" in every AC
  of this plan.

Brief plan inputs:

- reuse `resolve_in_workdir`, `_resolve`, `_open_nofollow` - ccw files.py - wrapper-file-download-route.
- reuse `resolve_agent`, `forward` error map, `get_client` - orchestrator api/workspace.py - orch-file-download-route.
- reuse `events` streaming pattern - orchestrator wrapper/client.py:234 - wrapper-client-download.
- reuse Rig/FakeWrapper/`put` - orchestrator tests/test_api_files.py - orch-file-download-route; fake routes and contract suite - fake-wrapper-download.
- reuse `Row`, stopPropagation precedent, `base()`/`query`, FilesPanel test mocks - agents-web - web-download-icon.
- do-not-build: Kubernetes `pods/exec` file access, S3 cache reads, a second wrapper-calling api module, client-side
  download from `FileContent`, hand edits to `schema.d.ts`, absolute backend URLs - honoured by D4, D5, D8.
- fix-as-ac (agents-web): 10 load-dependent timeouts in the full run - not fixed here (user decision U5: keep verifies
  targeted); noted, not doing now.
- fix-as-ac (agents-orchestrator, slash commands, `/compact` allowlist): belongs to epic slash-commands-from-chat.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 Wrapper raw-bytes route | wrapper-file-download-route |
| D2 Download response headers | wrapper-file-download-route, orch-file-download-route |
| D3 Listing field target_type | wrapper-file-download-route, fake-wrapper-download, orch-file-download-route, web-download-icon |
| D4 Orchestrator streaming route | wrapper-client-download, orch-file-download-route |
| D5 UI trigger is a plain anchor | web-download-icon |
| D6 Fake wrapper parity | fake-wrapper-download |
| D7 Docker-free orchestrator route tests | orch-file-download-route |
| D8 Web client schema regenerated | web-sync-orchestrator-api |
| D9 Orchestrator pins the wrapper commit | orch-wrapper-pin-download |

## Review focus

- Wrapper: no byte of a refused path is ever sent; open, `O_NOFOLLOW` and `fstat` happen once, before the response
  starts; the descriptor is closed on every path (complete, error, abandoned).
- `target_type` never distinguishes outside targets (escaping links are `null` whatever they point at).
- Orchestrator: upstream status mapped before headers; the token never in a header, body or log; upstream response
  closed on browser disconnect; raw chunks relayed (no decoding), `Content-Length` exact.
- `Content-Disposition` quoting for names with quotes, backslashes, control and non-ASCII characters.
- UI: the icon click does not open the preview or select the row; the URL is relative and percent-encoded.

## Left to the builder

- Chunk size up to 1 MiB, and whether the wrapper stream is a sync generator in the threadpool or an async generator
  over `asyncio.to_thread` reads, as long as the event loop never blocks on a read and the descriptor is closed on
  every exit.
- How the orchestrator keeps the upstream response open across `StreamingResponse` (a `BackgroundTask`, a generator
  `finally`, or both), as long as it is closed on every exit.
- Whether `forward` and the download share an extracted error-mapping helper or the download calls one `forward` uses;
  copying the map is not allowed.
- The exact MUI layout props that keep the icon on the row's right edge (for example `flexGrow: 1` on the name), as
  long as the row test pins it.

## Assumptions and unknown facts

- Assumed: browsers report a non-2xx answer to an anchor with `download` in their own UI rather than saving the error
  body as the file. Behaviour differs by browser and is not tested here; the gate reviewer confirms by hand in one
  browser after deploy (and Q1 decides when that is).
- Assumed: the ingress (oauth2-proxy) passes streamed responses and the SSO cookie on a top-level GET, as it does for
  the existing file GETs. Confirmed only by a live download after deploy.
- Assumed: the Harbor image `claude-code-wrapper:<sha7>` exists for the wrapper merge commit (built on every wrapper
  `main` push); orch-wrapper-pin-download checks it with `regctl image digest` or falls back to `scripts/e2e.sh`
  building from source, as in the precedent.

## Open questions

none
- Q1: Deploy is not part of this epic (no agents-helmfile task), so the download works live only after a later deploy pins the new wrapper, orchestrator and web images; is that right? [recommended: yes, deploy the four queued epics (download, markdown, editor, slash commands) together in one agents-helmfile deploy epic afterwards]
- Q2: To hide the icon on symlinks to directories (U2), the file listing gains target_type (dir, file, other; null for non-symlinks and for dangling or workdir-escaping links), and symlinks whose target escapes the workdir show no icon; acceptable? [recommended: yes]

## Irreversible operations in scope

none (no tag, release, migration or deploy; PRs merge through the normal flow).
