# markdown rendering in chat design

## Summary

The agents-web chat panel renders message text as GFM markdown: the user's own messages, the agents' answers, superleader session messages (inner text only) and peer messages. One new component, `ChatMarkdown` in `src/chat/Markdown.tsx`, wraps react-markdown 10.1.0 with remark-gfm 4.0.1 and remark-breaks 4.0.0 and maps every element to MUI components themed from `src/theme.ts`. Raw HTML stays text, links open in a new tab with `rel="noopener noreferrer"` through `defaultUrlTransform`, images never load, and code blocks are monospace with a language label and no highlighting. Tool and status rows, the session frame parser and the backend are untouched.

## Intent and why

User request (2026-10-27), verbatim: "render markdown in chat window (both for my input and agent's responses)". Agent answers arrive as markdown (code fences, lists, tables) and today show as raw text with `pre-wrap` (`src/chat/entries.tsx:32`), which makes long answers hard to read. The user types markdown too and wants it shown the same way.

## Goals

- Chat messages render as markdown (GFM: headings, lists, emphasis, links, inline code, fenced code blocks, tables), for the user's own messages and the agents' responses (README goal 1).
- Raw HTML in message text is not rendered (shown as text), so message content cannot inject markup (README goal 2).
- Session messages and peer messages render markdown too; tool and status rows stay as they are (user decision 2).

## Non-goals

- No change to how messages are stored or sent by the backend (README).
- No markdown editing toolbar or live preview in the composer (README).
- No syntax highlighting of code blocks and no highlighter dependency (user decision 3; the editor epic adds one).
- Noted, not doing now: memoizing `ChatEntry` so markdown is not re-parsed on every ChatLog render (brief web-libs-docs.md ideas); Virtuoso renders only visible rows.

## Anti-goals

- Any path that renders raw HTML or a `javascript:`/`data:` URL from message text (XSS).
- A remote image load triggered by message text.
- A changed byte of the session frame contract (`src/chat/chatModel.ts:SESSION_FRAME`, agents-orchestrator `dispatcher/session_frame.py`).
- An edit of `src/nomenclature.test.ts` or of any existing test to make the epic green.
- Colour literals outside `src/theme.ts`, or a designRules violation.

## Constraints

- Python only except web frontends: this epic is TypeScript in agents-web only.
- `src/layout/designRules.ts` rules for every non-test source: colours only in `theme.ts`, font weights 400 and 500, spacing on the 0.5 grid, no decorative Unicode.
- `src/nomenclature.test.ts` FORBIDDEN `/c[l]uster|agent[-_]orchestrator/i` scans every tracked file, package-lock.json included.
- Vitest runs in `node`; component tests opt into jsdom with `// @vitest-environment jsdom` and render under `<ThemeProvider theme={theme}>`; react-virtuoso is replaced by the render-all stand-in in ChatLog.test.tsx.
- TDD: each task's tests are written and seen failing first.
- No backward compatibility shims.

## Decisions

### D1: Library and versions

agents-web renders chat markdown with `react-markdown` 10.1.0, `remark-gfm` 4.0.1 and `remark-breaks` 4.0.0 through the synchronous default `Markdown` component (not `MarkdownHooks` or `MarkdownAsync`), declared in package.json `dependencies` as `~10.1.0`, `~4.0.1` and `~4.0.0`, with the matching package-lock.json entries.

- Alternatives: `markdown-to-jsx` 9.10.3 (renders raw HTML as JSX by default, safe only with `disableParsingRawHTML`); `marked` 18.1.2 plus `dompurify` (HTML string through `dangerouslySetInnerHTML`, cannot map to MUI); `MarkdownHooks` (delayed render, only for async plugins).
- Why: user decision 1; React elements map to MUI; secure by default; the synchronous render suits Virtuoso row measuring and synchronous Testing Library assertions (web-libs-docs.md A1-A3, A9, A18-A20). The tilde ranges follow the repo's convention for UI libraries (react, @mui/material) (my call for the range).

### D2: Raw HTML is text

Raw HTML in message text is shown as text: react-markdown's default, which turns every raw HTML node into a text node, is kept; `skipHtml` is not set and no `rehype-raw` or other rehype plugin is added. `hello <b>` renders as the literal text `hello <b>` and no `<b>` element exists.

- Alternatives: `skipHtml` (deletes the `<b>` text and breaks ChatLog.test.tsx's `hello <b>` case); `rehype-raw` plus `rehype-sanitize` (renders an allow-list of HTML, against the README goal).
- Why: user decision 1 and README goal 2; web-libs-docs.md A10, A13.

### D3: Links

A link whose URL `defaultUrlTransform` keeps renders as an MUI `Link` with `target="_blank"` and `rel="noopener noreferrer"`; `urlTransform` stays the default `defaultUrlTransform`, so a `javascript:` or `data:` URL leaves the link with no `href`. Fragment-only links (`#...`: the GFM footnote references and back-references) stay in-page, with no `target` and no `rel`. (my call for the fragment rule)

- Alternatives: every link in a new tab, footnotes included (a footnote click would open a blank copy of the app); a custom `urlTransform` (widens the XSS surface, web-libs-docs.md anti-patterns).
- Why: user decision 1; web-libs-docs.md A11. Footnotes are part of remark-gfm and point inside the same message.

### D4: Images do not load

Markdown images never render an `<img>` element: `![alt](url)` renders as an MUI `Link` to the transformed URL (new tab, `rel="noopener noreferrer"`) labelled with the alt text, or with the URL when the alt text is empty; an image whose URL `defaultUrlTransform` drops renders its alt text as plain text. (my call; Q1)

- Alternatives: render `<img>` with the default transform (agent or peer text could load remote resources, a tracking and layout-jump risk in a virtualised list); drop images entirely (`disallowedElements: ['img']`, loses the URL).
- Why: images are not in the README goals; a link keeps the information without a remote load (web-libs-docs.md ideas, A11, A12). Open as Q1.

### D5: MUI mapping and colours

Elements map to MUI through react-markdown's `components` prop: paragraphs `Typography` body1 (component `p`, no margin); headings h1-h6 `Typography` variants h1-h6 with the matching component; `a` MUI `Link` (underline always); `strong` with weight `TOKENS.fontWeights.medium` (500, the theme's fontWeightBold); `em` italic; `del` strikethrough; `ul`, `ol` and `li` as lists with left padding on the spacing grid; `blockquote` with a left border in the `divider` colour and `text.secondary` text; `hr` MUI `Divider`; `table`, `thead`, `tbody`, `tr`, `th` and `td` as MUI `Table` (size small, inside a horizontally scrollable `TableContainer`), `TableHead`, `TableBody`, `TableRow` and `TableCell` keeping the GFM column alignment; inline `code` in MONO_FONT on a raised background; GFM task-list checkboxes as a disabled small MUI `Checkbox`. No mapped component spreads react-markdown's `node` prop. Colours come only from theme palette paths or `src/theme.ts` exports, and `src/layout/designRules.test.ts` stays green.

- Alternatives: plain HTML elements styled by a global stylesheet (bypasses the theme and the designRules guard); MUI `List`/`ListItem` for lists (heavier, list semantics differ from markdown nesting).
- Why: user decision 1; web-libs-docs.md A14, A17; agents-web.md conventions (designRules, theme tokens). The checkbox, list and blockquote details are my call.

### D6: Which rows render markdown

Markdown renders for the `user_message`, `assistant`, `session` and `peer` chat items in `src/chat/entries.tsx`. `src/chat/chatModel.ts` (the `SESSION_FRAME` parse and `unescapeBody`) is not changed: only the parsed inner text of a session message is rendered as markdown. `thinking`, `tool`, `denied`, `turn_end`, `error` and `gap` rows render exactly as before.

- Alternatives: user and assistant rows only (the session and peer rows carry the same agent-written markdown); thinking rows too (user decision 2 keeps every non-message row unchanged).
- Why: user decision 2; agents-orchestrator.md "Epic 2" (stored text is raw, the frame is applied at send only).

### D7: Code blocks

A fenced code block renders as a `<pre>` in MONO_FONT (white-space pre-wrap, overflowWrap anywhere, scrollable when long) with its language, taken from the `language-<name>` class of its `code` child, shown as a caption label above the code; a fence without a language shows no label. No syntax highlighting and no highlighter dependency (the editor epic adds one later).

- Alternatives: Lezer `highlightCode` shared with the editor (web-libs-docs.md A21, deferred by the user); react-syntax-highlighter (ESM-broken README example, A16).
- Why: user decision 3; web-libs-docs.md A15.

### D8: Line breaks and white-space

Single newlines stay line breaks through `remark-breaks` (one `<br>` per soft line ending). Markdown paragraphs use normal white-space with `overflowWrap: 'anywhere'` instead of today's `pre-wrap`, since line breaks are now explicit elements; runs of spaces collapse as markdown defines. (my call for the white-space)

- Alternatives: keep `pre-wrap` on paragraphs (doubles every line break next to the `<br>` and keeps source indentation inside lists); no remark-breaks (single newlines would join lines, unlike how chat text is typed today).
- Why: user decision 1; web-libs-docs.md A7.

### D9: Row layout of markdown rows

On markdown rows the label (`you`, the origin, `session <from>`, `peer from <from>`) and the markdown body sit side by side in one flex row (label `flexShrink: 0`, body `minWidth: 0` and `flexGrow: 1`), so a block-level body does not push the label onto its own line; user rows keep `text.primary` and medium weight on their body text. Rows of other kinds keep the current `Row` markup. (my call)

- Alternatives: label above the body (every message grows one line); first paragraph inline after the label (needs a custom root renderer, fragile with lists and code).
- Why: today the label and the text share one line (`entries.tsx:14-31`); markdown output is block-level.

### D10: Dependency guard check

Before adding each dependency, its package-lock.json entries are checked against `FORBIDDEN` in `src/nomenclature.test.ts`; an addition that trips it is a question back to the user, never an edit of the guard. Planning probe (2026-10-27, a lockfile-only install of the three packages into a scratch copy of package.json and package-lock.json): 99 new lockfile packages, zero matches for `c[l]uster|agent[-_]orchestrator`.

- Alternatives: add phrases to `ALLOWED` when a name trips (a guard edit, refused by user decision 4).
- Why: user decision 4; web-libs-docs.md F0.7 (full transitive tree unresolved there, settled by the probe).

### D11: One component module

One new module `src/chat/Markdown.tsx` exports `ChatMarkdown({ text, sx })` (`sx` optional, applied to its root element); `src/chat/entries.tsx` uses it for the four markdown item kinds. (my call)

- Alternatives: the components map inline in `entries.tsx` (grows a 176-line row file and mixes concerns); a shared `src/markdown/` directory (no second consumer yet; the editor epic can move it if its preview needs it).
- Why: one tested unit with its own test file, reused by four row kinds.

### D12: Targeted verifies, full-suite caveat

Task verifies are targeted (named test files, `tsc -b`, lint). The full-suite run in epic review must account for the 10 load-dependent 5000 ms timeouts in the PresetForm, ScheduleForm, Endpoints and FiltersEditor tests that pass alone: a full run whose only failures are those timeouts is re-checked by running those four test files alone, and any other failure is real.

- Alternatives: raising the Vitest timeout or sharding in this epic (out of scope; a test-config change unrelated to markdown).
- Why: user decision 5; agents-web.md Verification (`.logs/agents-web-discovery-test.log` against `-rerun.log`).

### D13: MEMORY.md entry

MEMORY.md gets a dated entry (2026-10-27, markdown-rendering-in-chat) recording the library choice and why, raw HTML as text, the link and image rules, and the `npm run build` bundle size before and after the dependencies. (my call)

- Alternatives: no entry (the bundle cost and the image rule would be undocumented).
- Why: house rule (MEMORY.md on every non-obvious decision); web-libs-docs.md A25 (react-markdown publishes no bundle size).

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| Codebase (agents-web) | ran: .scratchpad/discovery/agents-web.md | ChatEntry kinds and `bodyText` (entries.tsx:32, :66-99); pinned `hello <b>` (ChatLog.test.tsx:144-156); designRules and nomenclature guards (designRules.ts, nomenclature.test.ts:30); test mocks (ChatLog.test.tsx:46-60) | none |
| Libraries and docs | ran: .scratchpad/discovery/web-libs-docs.md | react-markdown 10.1.0 safe defaults (A9-A11), `components` mapping without spreading `node` (A14, A17), remark-gfm (A5, A6), remark-breaks (A7), sync `Markdown` (A18), images not loaded (ideas, A12) | markdown-to-jsx (A19), marked plus DOMPurify (A20), Lezer highlighting now (A21, deferred by user decision 3), `skipHtml` and `rehype-raw` (anti-patterns) |
| Backend (agents-orchestrator) | ran: .scratchpad/discovery/agents-orchestrator.md | stored text is raw, frame applied at send only, chatModel.ts parses it byte-exact (Epic 2 section) | text rewriting in storage (do-not-build) |
| Dependency guard | ran: planning probe 2026-10-27, lockfile-only install into a scratch copy | zero FORBIDDEN matches across 99 new lockfile packages (D10) | none |
| Prior retros | ran: `ticket.py retro --history` | see Research inputs | live apply/smoke seeds and port-forward proposals (no deploy in this epic) |

## Research inputs

- Recurring (paste-env-contents-into-the, matrix-read-receipts): a ruling not pinned by a test was found only in review; each task's Requirement lists every ruling with its named pin test. Acts: chat-markdown-renderer, chat-rows-render-markdown.
- Recurring (cross-session-messaging-and, agents-matrix-connector-depl, paste-env-contents-into-the): late defects and false pass claims; each task's Steps require quoting the vitest summary line with counts and the head sha it ran on. Acts: chat-markdown-renderer, chat-rows-render-markdown.
- Recurring (paste-env-contents-into-the, agents-matrix-connector-depl): flat seeds far off for UI tasks; sized by points only, the tool's calibration fills minutes and tokens. Acts: chat-markdown-renderer, chat-rows-render-markdown.
- One-off (cross-session-messaging-and): ACs must name existing tests or mark new ones; new-test ACs are marked "(new)" and use `command:` evidence, existing ones `test:` refs that `workbench.py runner` resolves. Acts: chat-markdown-renderer, chat-rows-render-markdown.
- One-off (generic-any-mcp-with-git-and): fakes must match captured real output; the guard check rests on a real lockfile probe, not the registry listing (D10). Acts: chat-markdown-renderer.
- `hello <b>` must stay literal text (agents-web.md Chat view; web-libs-docs.md A10). Acts: chat-markdown-renderer, chat-rows-render-markdown.
- Session frame parsing stays byte-exact; only the inner text renders (agents-orchestrator.md Epic 2). Acts: chat-rows-render-markdown.
- Record the bundle-size delta in MEMORY.md (web-libs-docs.md A25). Acts: chat-markdown-renderer.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 Library and versions | chat-markdown-renderer |
| D2 Raw HTML is text | chat-markdown-renderer, chat-rows-render-markdown |
| D3 Links | chat-markdown-renderer |
| D4 Images do not load | chat-markdown-renderer |
| D5 MUI mapping and colours | chat-markdown-renderer |
| D6 Which rows render markdown | chat-rows-render-markdown |
| D7 Code blocks | chat-markdown-renderer |
| D8 Line breaks and white-space | chat-markdown-renderer |
| D9 Row layout of markdown rows | chat-rows-render-markdown |
| D10 Dependency guard check | chat-markdown-renderer |
| D11 One component module | chat-markdown-renderer, chat-rows-render-markdown |
| D12 Targeted verifies, full-suite caveat | chat-markdown-renderer, chat-rows-render-markdown |
| D13 MEMORY.md entry | chat-markdown-renderer |

## Review focus

- XSS surface in `src/chat/Markdown.tsx`: no `skipHtml`, no rehype plugin, default `urlTransform`, no `<img>`, no `dangerouslySetInnerHTML`, no spread of `node`.
- `src/chat/chatModel.ts` and `chatModel.test.ts` have no diff; ChatLog.test.tsx existing tests are unedited.
- Rows other than the four markdown kinds render byte-identical markup.
- package-lock.json: only the three dependencies and their transitive tree added; nomenclature guard green without an `ALLOWED` edit.
- designRules on the new module: no colour literal, weights 400 and 500 only.

## Left to the builder

- The exact `sx` values (spacing between blocks, list indent, code padding, table cell density) within the spacing grid and theme tokens.
- Whether `src/theme.ts` gains a token for the code background or the existing `TOKENS.bgRaised` and `TOKENS.border` suffice.
- How `Row` takes the D9 layout (an optional prop or a sibling component), as long as other kinds keep their markup.
- How the code language label is extracted from the `pre` child (className of the `code` element), within D7.

## Assumptions and unknown facts

- GFM footnote ids repeat across messages (`user-content-fn-1` in two messages); a footnote jump then lands on the first. Accepted; confirmed only if a reviewer sees it matter.
- `defaultUrlTransform` returns `''` for unsafe URLs; the builder confirms whether React drops the empty `href` or the `a` mapping must omit it; ac5 of chat-markdown-renderer pins the outcome either way.
- Vitest handles the ESM-only packages in node and jsdom without config (web-libs-docs.md A8, A24); confirmed by the first red run.
- The bundle size cost is unknown until the first build (A25); recorded in MEMORY.md by chat-markdown-renderer.

## Open questions

none

## Irreversible operations in scope

none
