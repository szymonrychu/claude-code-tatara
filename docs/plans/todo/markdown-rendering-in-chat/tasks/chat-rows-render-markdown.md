---
title: chat rows render markdown
status: todo
repo: agents-web
value: "the user's messages, agent answers, session messages and peer messages in the chat show as rendered markdown"
files: [src/chat/entries.tsx, src/chat/ChatLog.test.tsx]
verify: "mise exec -- npx vitest run src/chat/ChatLog.test.tsx src/chat/chatModel.test.ts src/chat/Markdown.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint"
depends_on: [chat-markdown-renderer]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# chat rows render markdown

## Requirement

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

## Acceptance conditions

- ac1: a `user_message` event with origin `user` whose text holds `**bold**` and an inline code span renders under the label `you` a `strong` element `bold` and a `code` element; an `assistant_text` event with a GFM table and a bullet list renders a table with its header cells and list items (new) [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx -t 'user_and_assistant_rows_render_markdown']
- ac2: a framed `<session-message>` user_message whose body is `# Plan` and `- step one` renders under `session <from>` a heading `Plan` and a list item `step one`, without the frame tags or the trailer line; a `peer_message_received` event with `*hi*` renders an `em` element under `peer from <from>` (new) [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx -t 'session_and_peer_rows_render_markdown']
- ac3: thinking text, tool input and output, a denied reason and an error message holding `**x**` show the literal `**x**` and no `strong` element (new) [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx -t 'tool_and_status_rows_stay_plain']
- ac4: the existing session test still finds the literal text `hello <b>` and the label `session beta-2` [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx -t 'session message labelled with its sender session']
- ac5: the session-message frame parse is byte-exact and unchanged: `src/chat/chatModel.ts` has no diff against the epic base and its session frame tests pass [evidence: command:git diff --quiet origin/main...HEAD -- src/chat/chatModel.ts src/chat/chatModel.test.ts && mise exec -- npx vitest run src/chat/chatModel.test.ts -t 'session frame|without a leading frame|escaped closing tag']
- ac6: on the four markdown row kinds the label and the markdown body sit side by side and a multi-paragraph body does not move the label onto its own line; user rows keep primary colour and medium weight; the other row kinds look as before [evidence: judgement:src/chat/entries.tsx Row and the four markdown cases read against design D9]
- ac7: every existing ChatLog test passes unedited, and the design rules and nomenclature guards hold [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts]
- ac8: the task's targeted suites, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/chat/ChatLog.test.tsx src/chat/chatModel.test.ts src/chat/Markdown.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && mise exec -- npx tsc -b && mise run lint]

## Files

- `src/chat/entries.tsx`
- `src/chat/ChatLog.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: add `user_and_assistant_rows_render_markdown`, `session_and_peer_rows_render_markdown` and `tool_and_status_rows_stay_plain` to `src/chat/ChatLog.test.tsx` without editing existing tests; run `mise exec -- npx vitest run src/chat/ChatLog.test.tsx`; expect the first two new tests to fail on missing `strong`, `code`, table, heading, list and `em` elements, and every existing test to pass (`tool_and_status_rows_stay_plain` may already pass: it pins unchanged behaviour).
- Green: in `src/chat/entries.tsx` switch the `user_message`, `assistant`, `session` and `peer` cases to `<ChatMarkdown text={item.text} />` (user rows with `sx` keeping `text.primary` and `TOKENS.fontWeights.medium`) and give `Row` the D9 side-by-side layout for these four kinds only; leave `chatModel.ts` untouched and other cases as before; rerun `mise exec -- npx vitest run src/chat/ChatLog.test.tsx`; expect all tests pass, including `session message labelled with its sender session`.
- Frame guard: `git diff --quiet origin/main...HEAD -- src/chat/chatModel.ts src/chat/chatModel.test.ts && mise exec -- npx vitest run src/chat/chatModel.test.ts -t 'session frame|without a leading frame|escaped closing tag'`; expect exit 0 and the session frame tests passing.
- Verify once: run the task's `verify` command; expect all test files and tests pass, `tsc -b` and lint exit 0; quote the vitest summary line (test files and tests counts) and the head sha it ran on.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
