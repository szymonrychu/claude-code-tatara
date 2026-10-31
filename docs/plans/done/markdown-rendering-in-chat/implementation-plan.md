# markdown rendering in chat implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: chat markdown renderer

- Status: done
- Files: `package.json`, `package-lock.json`, `src/chat/Markdown.tsx`, `src/chat/Markdown.test.tsx`, `src/theme.ts`, `MEMORY.md`
- Verify: `mise exec -- npx vitest run src/chat/Markdown.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint`
- Verified head: c2693f2310c7808442dabe7ae0e16315bf7bed62

#### Requirement

User request (2026-10-27), verbatim: "## markdown rendering in the chat

as title implies, render markdown in chat window (both for my input and agent's responses)"

Epic README goals, verbatim: "Chat messages render as markdown (GFM: headings, lists, emphasis, links, inline code, fenced code blocks, tables), for the user's own messages and the agents' responses." and "Raw HTML in message text is not rendered (shown as text), so message content cannot inject markup."

User decision 1, verbatim: "(my call) react-markdown 10.1.0 + remark-gfm 4.0.1 + remark-breaks 4.0.0 (single newlines stay line breaks, as chat text is typed today); raw HTML not rendered (shown as text, ChatLog.test.tsx 'hello <b>' case stays green); links open in a new tab with rel noopener noreferrer, URLs through defaultUrlTransform; elements mapped to MUI Typography/Link/Table with colours only from src/theme.ts and the designRules guard green."

User decision 3, verbatim: "(my call) Fenced code blocks render monospace with a language label, no syntax highlighting in this epic (the editor epic adds a highlighter later; no shared highlighter dependency here)."

User decision 4, verbatim: "Check every new dependency's package-lock entries against src/nomenclature.test.ts FORBIDDEN before adding it; an addition that trips it is a question back to me, never an edit of the guard."

User decision 5, verbatim: "Environment: the agents-web full suite has 10 load-dependent 5000 ms timeouts (PresetForm, ScheduleForm, Endpoints, FiltersEditor tests) that pass alone; keep task verifies targeted, and note in design.md that the full-suite run in epic review must account for it."

Design D1, verbatim: "agents-web renders chat markdown with `react-markdown` 10.1.0, `remark-gfm` 4.0.1 and `remark-breaks` 4.0.0 through the synchronous default `Markdown` component (not `MarkdownHooks` or `MarkdownAsync`), declared in package.json `dependencies` as `~10.1.0`, `~4.0.1` and `~4.0.0`, with the matching package-lock.json entries."

Design D2, verbatim: "Raw HTML in message text is shown as text: react-markdown's default, which turns every raw HTML node into a text node, is kept; `skipHtml` is not set and no `rehype-raw` or other rehype plugin is added. `hello <b>` renders as the literal text `hello <b>` and no `<b>` element exists."

Design D3, verbatim: "A link whose URL `defaultUrlTransform` keeps renders as an MUI `Link` with `target="_blank"` and `rel="noopener noreferrer"`; `urlTransform` stays the default `defaultUrlTransform`, so a `javascript:` or `data:` URL leaves the link with no `href`. Fragment-only links (`#...`: the GFM footnote references and back-references) stay in-page, with no `target` and no `rel`. (my call for the fragment rule)"

Design D4, verbatim: "Markdown images never render an `<img>` element: `![alt](url)` renders as an MUI `Link` to the transformed URL (new tab, `rel="noopener noreferrer"`) labelled with the alt text, or with the URL when the alt text is empty; an image whose URL `defaultUrlTransform` drops renders its alt text as plain text. (my call; Q1)"

Design D5, verbatim: "Elements map to MUI through react-markdown's `components` prop: paragraphs `Typography` body1 (component `p`, no margin); headings h1-h6 `Typography` variants h1-h6 with the matching component; `a` MUI `Link` (underline always); `strong` with weight `TOKENS.fontWeights.medium` (500, the theme's fontWeightBold); `em` italic; `del` strikethrough; `ul`, `ol` and `li` as lists with left padding on the spacing grid; `blockquote` with a left border in the `divider` colour and `text.secondary` text; `hr` MUI `Divider`; `table`, `thead`, `tbody`, `tr`, `th` and `td` as MUI `Table` (size small, inside a horizontally scrollable `TableContainer`), `TableHead`, `TableBody`, `TableRow` and `TableCell` keeping the GFM column alignment; inline `code` in MONO_FONT on a raised background; GFM task-list checkboxes as a disabled small MUI `Checkbox`. No mapped component spreads react-markdown's `node` prop. Colours come only from theme palette paths or `src/theme.ts` exports, and `src/layout/designRules.test.ts` stays green."

Design D7, verbatim: "A fenced code block renders as a `<pre>` in MONO_FONT (white-space pre-wrap, overflowWrap anywhere, scrollable when long) with its language, taken from the `language-<name>` class of its `code` child, shown as a caption label above the code; a fence without a language shows no label. No syntax highlighting and no highlighter dependency (the editor epic adds one later)."

Design D8, verbatim: "Single newlines stay line breaks through `remark-breaks` (one `<br>` per soft line ending). Markdown paragraphs use normal white-space with `overflowWrap: 'anywhere'` instead of today's `pre-wrap`, since line breaks are now explicit elements; runs of spaces collapse as markdown defines. (my call for the white-space)"

Design D10, verbatim: "Before adding each dependency, its package-lock.json entries are checked against `FORBIDDEN` in `src/nomenclature.test.ts`; an addition that trips it is a question back to the user, never an edit of the guard. Planning probe (2026-10-27, a lockfile-only install of the three packages into a scratch copy of package.json and package-lock.json): 99 new lockfile packages, zero matches for `c[l]uster|agent[-_]orchestrator`."

Design D11, verbatim: "One new module `src/chat/Markdown.tsx` exports `ChatMarkdown({ text, sx })` (`sx` optional, applied to its root element); `src/chat/entries.tsx` uses it for the four markdown item kinds. (my call)"

Design D13, verbatim: "MEMORY.md gets a dated entry (2026-10-27, markdown-rendering-in-chat) recording the library choice and why, raw HTML as text, the link and image rules, and the `npm run build` bundle size before and after the dependencies. (my call)"

Scope (agents-web), this task:
- `package.json`, `package-lock.json`: the three dependencies, added with `mise exec -- npm install react-markdown@~10.1.0 remark-gfm@~4.0.1 remark-breaks@~4.0.0` after the D10 lockfile check.
- `src/chat/Markdown.tsx` (new): `ChatMarkdown`, the `components` map of D5, the code block of D7, the link and image rules of D3 and D4, `remarkPlugins={[remarkGfm, remarkBreaks]}`.
- `src/chat/Markdown.test.tsx` (new, first line `// @vitest-environment jsdom`, rendered under `<ThemeProvider theme={theme}>`): the tests named in the acceptance conditions.
- `src/theme.ts`: only if a colour or size token is missing for the mapping (for example a code background); every colour literal stays in this file.
- `MEMORY.md`: the D13 entry.
- Not in this task: `src/chat/entries.tsx` and `src/chat/ChatLog.test.tsx` (task chat-rows-render-markdown), `src/chat/chatModel.ts` (never changed in this epic).

Interfaces:
- `src/chat/Markdown.tsx:ChatMarkdown(props: { text: string; sx?: SxProps<Theme> }): JSX.Element`, synchronous, renders react-markdown's `Markdown` with `remarkPlugins={[remarkGfm, remarkBreaks]}`, the default `urlTransform`, no `rehypePlugins`, no `skipHtml`, no `allowedElements`/`disallowedElements` except as needed to drop `img` per D4 (mapping `img` in `components` is the preferred route).
- Mapped text elements (`p`, `li`, `td`, `th`) inherit colour and font weight from the `sx` root (`color: 'inherit'`, `fontWeight: 'inherit'`) so a caller can keep a row's colour and weight; `strong` sets weight 500.

Rulings and their pin tests (Markdown.test.tsx, all new):
- raw HTML as text (D2): `raw_html_renders_as_text`.
- new-tab links, dropped unsafe URLs, in-page fragments (D3): `links_open_in_new_tab_and_unsafe_urls_drop`.
- images as links, alt text or URL label, dropped URL as plain alt text (D4): `images_render_as_links`.
- single newline as `<br>` (D8): `single_newline_is_a_line_break`.
- code block label and no highlighting (D7): `fenced_code_block_shows_language_without_highlighting`.
- MUI mapping of every GFM element in the README goal plus strikethrough and task lists (D5): `renders_gfm_elements_as_mui`.

Steps:
- Baseline: `mise exec -- npm run build` before any change; note the reported bundle sizes for MEMORY.md.
- Dependency check (D10): add the three dependencies, then `grep -inE 'c[l]uster|agent[-_]orchestrator' package-lock.json` must print nothing. If it prints anything, stop, revert package.json and package-lock.json, and return the matching lines as a question; never edit `src/nomenclature.test.ts`.
- Red: write `src/chat/Markdown.test.tsx` with the six tests above and an empty `ChatMarkdown` stub; run `mise exec -- npx vitest run src/chat/Markdown.test.tsx`: the six fail.
- Green: implement `ChatMarkdown`; rerun: the six pass.
- `mise exec -- npm run build` again, record both sizes in the MEMORY.md entry.
- Run the task's verify once; quote the vitest summary line (test files and tests counts) and the head sha it ran on.

#### Acceptance conditions

- ac1: package.json `dependencies` declare `react-markdown` `~10.1.0`, `remark-gfm` `~4.0.1` and `remark-breaks` `~4.0.0`, and the installed tree resolves exactly 10.1.0, 4.0.1 and 4.0.0 [evidence: command:mise exec -- npm ls react-markdown@10.1.0 remark-gfm@4.0.1 remark-breaks@4.0.0]
- ac2: package-lock.json with the new entries holds no match for the nomenclature guard's `FORBIDDEN` pattern, and `src/nomenclature.test.ts` is unchanged [evidence: test:src/nomenclature.test.ts::guarded paths name the unit session only]
- ac3: `ChatMarkdown` renders headings h1-h6 as MUI Typography headings, unordered and ordered lists with list items, emphasis, strong (weight 500), strikethrough, links as MUI Link, inline code in MONO_FONT, blockquote, horizontal rule as MUI Divider, GFM tables as MUI Table with header and body cells and column alignment, and GFM task lists with disabled checkboxes (new) [evidence: command:mise exec -- npx vitest run src/chat/Markdown.test.tsx -t 'renders_gfm_elements_as_mui']
- ac4: raw HTML in the text (`hello <b>`, `<b>x</b>`, `<script>alert(1)</script>`, `<img src=x onerror=alert(1)>`) renders as literal text: no `b`, `script` or `img` element exists and the source text is visible (new) [evidence: command:mise exec -- npx vitest run src/chat/Markdown.test.tsx -t 'raw_html_renders_as_text']
- ac5: an `https:` link and a GFM autolink literal render with `target="_blank"` and `rel="noopener noreferrer"`; a `javascript:` link and a `data:` link render with no `href`; a footnote reference link (`#...`) has no `target` (new) [evidence: command:mise exec -- npx vitest run src/chat/Markdown.test.tsx -t 'links_open_in_new_tab_and_unsafe_urls_drop']
- ac6: `![logo](https://example.com/a.png)` renders a new-tab link named `logo` to that URL, an image with empty alt text a link labelled with its URL, and `![x](javascript:alert(1))` the plain text `x`; no `img` element exists (new) [evidence: command:mise exec -- npx vitest run src/chat/Markdown.test.tsx -t 'images_render_as_links']
- ac7: `line one\nline two` renders one paragraph holding one `<br>` between the two lines (new) [evidence: command:mise exec -- npx vitest run src/chat/Markdown.test.tsx -t 'single_newline_is_a_line_break']
- ac8: a ```` ```python ```` fence renders a `pre` in MONO_FONT whose code text is exact and a visible `python` label; a fence without a language shows no label; the code element holds text only (no token spans) (new) [evidence: command:mise exec -- npx vitest run src/chat/Markdown.test.tsx -t 'fenced_code_block_shows_language_without_highlighting']
- ac9: `src/chat/Markdown.tsx` and any `src/theme.ts` change pass the design rules (colours only from the theme, weights 400 and 500, spacing grid, no decorative Unicode) [evidence: test:src/layout/designRules.test.ts::source files follow the design rules]
- ac10: the production build passes with the ESM-only dependencies and MEMORY.md has the dated markdown-rendering-in-chat entry with the bundle size before and after [evidence: command:mise exec -- npm run build && grep -q 'markdown-rendering-in-chat' MEMORY.md]
- ac11: the task's targeted suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/chat/Markdown.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint]

#### Files

- `package.json`
- `package-lock.json`
- `src/chat/Markdown.tsx`
- `src/chat/Markdown.test.tsx`
- `src/theme.ts`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Baseline: `mise exec -- npm run build` before any change; expect a successful build, and note the reported bundle sizes for MEMORY.md.
- Dependency check (D10): `mise exec -- npm install react-markdown@~10.1.0 remark-gfm@~4.0.1 remark-breaks@~4.0.0`, then `grep -inE 'c[l]uster|agent[-_]orchestrator' package-lock.json`; expect no output. If it prints anything, stop, revert package.json and package-lock.json, and return the lines as a question; never edit `src/nomenclature.test.ts`. Then `mise exec -- npm ls react-markdown@10.1.0 remark-gfm@4.0.1 remark-breaks@4.0.0`; expect the three packages resolved, exit 0.
- Red: write `src/chat/Markdown.test.tsx` (first line `// @vitest-environment jsdom`, rendered under `<ThemeProvider theme={theme}>`) with `renders_gfm_elements_as_mui`, `raw_html_renders_as_text`, `links_open_in_new_tab_and_unsafe_urls_drop`, `images_render_as_links`, `single_newline_is_a_line_break` and `fenced_code_block_shows_language_without_highlighting`, plus an empty `ChatMarkdown` stub in `src/chat/Markdown.tsx`; run `mise exec -- npx vitest run src/chat/Markdown.test.tsx`; expect the six tests to fail on their assertions, not on import errors.
- Green: implement `ChatMarkdown` (D5 components map, D7 code block, D3 links, D4 images, `remarkPlugins={[remarkGfm, remarkBreaks]}`, default `urlTransform`, no `rehypePlugins`, no `skipHtml`); add a `src/theme.ts` token only if a code background is missing; rerun `mise exec -- npx vitest run src/chat/Markdown.test.tsx`; expect 6 passed.
- Guards: `mise exec -- npx vitest run src/layout/designRules.test.ts src/nomenclature.test.ts`; expect both files pass with `src/nomenclature.test.ts` unchanged.
- Build and MEMORY.md: `mise exec -- npm run build`; expect success and record both bundle sizes (before and after) in the dated D13 entry; then `grep -q 'markdown-rendering-in-chat' MEMORY.md`; expect exit 0.
- Verify once: run the task's `verify` command; expect all test files and tests pass, `tsc -b` and lint exit 0; quote the vitest summary line (test files and tests counts) and the head sha it ran on.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-27 done

### S2: chat rows render markdown

- Status: done
- Files: `src/chat/entries.tsx`, `src/chat/ChatLog.test.tsx`
- Verify: `mise exec -- npx vitest run src/chat/ChatLog.test.tsx src/chat/chatModel.test.ts src/chat/Markdown.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint`
- Verified head: 12e1b773d6d5025bae927ca354712825cb2970ac

#### Requirement

User request (2026-10-27), verbatim: "## markdown rendering in the chat

as title implies, render markdown in chat window (both for my input and agent's responses)"

Epic README goals, verbatim: "Chat messages render as markdown (GFM: headings, lists, emphasis, links, inline code, fenced code blocks, tables), for the user's own messages and the agents' responses." and "Raw HTML in message text is not rendered (shown as text), so message content cannot inject markup."

User decision 1 (part), verbatim: "raw HTML not rendered (shown as text, ChatLog.test.tsx 'hello <b>' case stays green)"

User decision 2, verbatim: "(my call) Markdown applies to user, assistant, superleader session-message and peer rows; the session-message frame parsing in chatModel.ts stays byte-exact and only the inner text renders as markdown; tool/status rows unchanged."

User decision 5, verbatim: "Environment: the agents-web full suite has 10 load-dependent 5000 ms timeouts (PresetForm, ScheduleForm, Endpoints, FiltersEditor tests) that pass alone; keep task verifies targeted, and note in design.md that the full-suite run in epic review must account for it."

Design D6, verbatim: "Markdown renders for the `user_message`, `assistant`, `session` and `peer` chat items in `src/chat/entries.tsx`. `src/chat/chatModel.ts` (the `SESSION_FRAME` parse and `unescapeBody`) is not changed: only the parsed inner text of a session message is rendered as markdown. `thinking`, `tool`, `denied`, `turn_end`, `error` and `gap` rows render exactly as before."

Design D9, verbatim: "On markdown rows the label (`you`, the origin, `session <from>`, `peer from <from>`) and the markdown body sit side by side in one flex row (label `flexShrink: 0`, body `minWidth: 0` and `flexGrow: 1`), so a block-level body does not push the label onto its own line; user rows keep `text.primary` and medium weight on their body text. Rows of other kinds keep the current `Row` markup. (my call)"

Design D11, verbatim: "One new module `src/chat/Markdown.tsx` exports `ChatMarkdown({ text, sx })` (`sx` optional, applied to its root element); `src/chat/entries.tsx` uses it for the four markdown item kinds. (my call)"

Scope (agents-web), this task:
- `src/chat/entries.tsx`: the `user_message`, `assistant`, `session` and `peer` cases render `<ChatMarkdown text={item.text} />` (user rows with `sx` keeping `text.primary` and `TOKENS.fontWeights.medium`) instead of the plain `Typography` span; `Row` gains the D9 side-by-side layout for these four kinds only (for example an optional prop); every other case is unchanged. Remove `bodyText` only if no remaining case uses it (thinking and error still do).
- `src/chat/ChatLog.test.tsx`: the new tests named in the acceptance conditions; existing tests are not edited.
- Not in this task: `src/chat/chatModel.ts` and `src/chat/chatModel.test.ts` (never changed in this epic), `src/chat/Markdown.tsx` (task chat-markdown-renderer).

Interfaces:
- Uses `src/chat/Markdown.tsx:ChatMarkdown(props: { text: string; sx?: SxProps<Theme> })` from chat-markdown-renderer.
- Kept: `src/chat/entries.tsx:ChatEntry({ item })` signature; the row `aria-label` `agent <n> row` and `role="listitem"`; labels `you`, the origin, `session <from>`, `peer from <from>`; `src/chat/chatModel.ts` byte for byte.

Rulings and their pin tests (ChatLog.test.tsx, new unless marked):
- user and assistant rows render markdown: `user_and_assistant_rows_render_markdown`.
- session (inner text only, frame and trailer not shown) and peer rows render markdown: `session_and_peer_rows_render_markdown`.
- thinking, tool, denied and error rows stay plain text: `tool_and_status_rows_stay_plain`.
- raw `hello <b>` inside a session frame stays literal text: the existing `session message labelled with its sender session` (unchanged).
- session frame parse stays byte-exact: the existing chatModel.test.ts `session frames` tests (unchanged).

Steps:
- Red: add the three new ChatLog tests; run `mise exec -- npx vitest run src/chat/ChatLog.test.tsx`: the three fail, every existing test passes.
- Green: switch the four cases to `ChatMarkdown` and add the D9 layout; rerun: all pass.
- Run the task's verify once; quote the vitest summary line (test files and tests counts) and the head sha it ran on.

#### Acceptance conditions

- ac1: a `user_message` event with origin `user` whose text holds `**bold**` and an inline code span renders under the label `you` a `strong` element `bold` and a `code` element; an `assistant_text` event with a GFM table and a bullet list renders a table with its header cells and list items (new) [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx -t 'user_and_assistant_rows_render_markdown']
- ac2: a framed `<session-message>` user_message whose body is `# Plan` and `- step one` renders under `session <from>` a heading `Plan` and a list item `step one`, without the frame tags or the trailer line; a `peer_message_received` event with `*hi*` renders an `em` element under `peer from <from>` (new) [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx -t 'session_and_peer_rows_render_markdown']
- ac3: thinking text, tool input and output, a denied reason and an error message holding `**x**` show the literal `**x**` and no `strong` element (new) [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx -t 'tool_and_status_rows_stay_plain']
- ac4: the existing session test still finds the literal text `hello <b>` and the label `session beta-2` [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx -t 'session message labelled with its sender session']
- ac5: the session-message frame parse is byte-exact and unchanged: `src/chat/chatModel.ts` has no diff against the epic base and its session frame tests pass [evidence: command:git diff --quiet origin/main...HEAD -- src/chat/chatModel.ts src/chat/chatModel.test.ts && mise exec -- npx vitest run src/chat/chatModel.test.ts -t 'session frame|without a leading frame|escaped closing tag']
- ac6: on the four markdown row kinds the label and the markdown body sit side by side and a multi-paragraph body does not move the label onto its own line; user rows keep primary colour and medium weight; the other row kinds look as before [evidence: judgement:src/chat/entries.tsx Row and the four markdown cases read against design D9]
- ac7: every existing ChatLog test passes unedited, and the design rules and nomenclature guards hold [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts]
- ac8: the task's targeted suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx src/chat/chatModel.test.ts src/chat/Markdown.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint]

#### Files

- `src/chat/entries.tsx`
- `src/chat/ChatLog.test.tsx`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: add `user_and_assistant_rows_render_markdown`, `session_and_peer_rows_render_markdown` and `tool_and_status_rows_stay_plain` to `src/chat/ChatLog.test.tsx` without editing existing tests; run `mise exec -- npx vitest run src/chat/ChatLog.test.tsx`; expect the first two new tests to fail on missing `strong`, `code`, table, heading, list and `em` elements, and every existing test to pass (`tool_and_status_rows_stay_plain` may already pass: it pins unchanged behaviour).
- Green: in `src/chat/entries.tsx` switch the `user_message`, `assistant`, `session` and `peer` cases to `<ChatMarkdown text={item.text} />` (user rows with `sx` keeping `text.primary` and `TOKENS.fontWeights.medium`) and give `Row` the D9 side-by-side layout for these four kinds only; leave `chatModel.ts` untouched and other cases as before; rerun `mise exec -- npx vitest run src/chat/ChatLog.test.tsx`; expect all tests pass, including `session message labelled with its sender session`.
- Frame guard: `git diff --quiet origin/main...HEAD -- src/chat/chatModel.ts src/chat/chatModel.test.ts && mise exec -- npx vitest run src/chat/chatModel.test.ts -t 'session frame|without a leading frame|escaped closing tag'`; expect exit 0 and the session frame tests passing.
- Verify once: run the task's `verify` command; expect all test files and tests pass, `tsc -b` and lint exit 0; quote the vitest summary line (test files and tests counts) and the head sha it ran on.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-27 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
