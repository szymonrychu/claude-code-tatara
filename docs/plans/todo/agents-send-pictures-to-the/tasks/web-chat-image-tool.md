---
title: web chat image tool
status: todo
repo: agents-web
value: the session web chat shows a picture the agent sent
files: [src/chat/ChatImage.tsx, src/chat/ChatImage.test.tsx, src/chat/entries.tsx, src/chat/ChatLog.tsx, src/chat/ChatLog.test.tsx, src/chat/ChatView.tsx, MEMORY.md]
verify: "npx vitest run src/chat/ChatImage.test.tsx src/chat/ChatView.test.tsx src/chat/ChatLog.test.tsx && npm run lint"
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

# web chat image tool

## Requirement

README Goal G3, verbatim: "the session web chat shows the sent picture inside the tool-call box from the same-origin session download route; message text still never renders images; the Chats page shows "picture: <name>"."

Design D8, verbatim:
"- Session ChatView: a renderer for tool items named `*orchestrator_chat_send_image*` with status ok and a JSON result containing `path` draws `<img src={fileDownloadUrl(sessionId, path)} loading="lazy">` at most 320 px wide, opening the full file on click, with "picture no longer in the workspace" on error; the tool JSON box stays below. Session-level download (all agents of a session share one workdir, probes.md). User Q1.
- Markdown.tsx unchanged; agents-web MEMORY.md records "the only `<img>` is the chat-image tool renderer, same-origin download route only, never markdown or remote URLs"."

Anti-goal, verbatim: "Any service of ours fetches remote content (SSRF surface), or the web renders an `<img>` from message text or a remote URL."

Open question Q1 (planned on its recommended answer): "Show pictures in the session web chat too? [recommended: yes]"

Scope (agents-web):
- `src/chat/ChatImage.tsx` (new; its own module so its test runs without react-markdown): `ChatImage({sessionId, item})` renders for a tool item whose name contains `orchestrator_chat_send_image`, status `ok` and an output that parses as a JSON object with a string `path`: an anchor to `fileDownloadUrl(sessionId, path)` opening in a new tab (`rel="noopener noreferrer"`, my call for "opening the full file on click") around `<img src={fileDownloadUrl(sessionId, path)} loading="lazy">` with `max-width: 320px` and the picture name as alt; on the image's error it shows "picture no longer in the workspace". Anything else renders nothing.
- `src/chat/entries.tsx`: the tool row shows `ChatImage` under its summary, visible without expanding (my call), with the expandable Input/Output box below as today; `ChatEntry` takes `sessionId`.
- `src/chat/ChatLog.tsx`, `src/chat/ChatView.tsx`: pass `sessionId` down.
- `src/chat/Markdown.tsx` unchanged. `MEMORY.md` records the rule above, dated.

## Acceptance conditions

- ac1: an ok orchestrator_chat_send_image tool item whose output is JSON with a path renders an img whose src is the relative session download URL of that path, lazy, at most 320 px wide, inside a link to the same URL [evidence: command:npx vitest run src/chat/ChatImage.test.tsx -t "renders the picture from the session download route"]
- ac2: nothing renders for a running or error item, another tool name, output that is not JSON or has no string path; any path only ever yields the same-origin download route [evidence: command:npx vitest run src/chat/ChatImage.test.tsx -t "renders nothing"]
- ac3: an image load error shows "picture no longer in the workspace" [evidence: command:npx vitest run src/chat/ChatImage.test.tsx -t "placeholder when the file is gone"]
- ac4: the tool row shows the picture without expanding and keeps the expandable Input and Output box below it [evidence: command:npx vitest run src/chat/ChatLog.test.tsx -t "image tool row"]
- ac5: Markdown.tsx is unchanged [evidence: command:git diff --quiet origin/main -- src/chat/Markdown.tsx]
- ac6: MEMORY.md records that the only img is the chat-image tool renderer [evidence: command:grep -qF 'the only `<img>` is the chat-image tool renderer' MEMORY.md]
- ac7: the chat tests and lint pass [evidence: command:npx vitest run src/chat/ChatImage.test.tsx src/chat/ChatView.test.tsx src/chat/ChatLog.test.tsx && npm run lint]

## Files

- `src/chat/ChatImage.tsx`
- `src/chat/ChatImage.test.tsx`
- `src/chat/entries.tsx`
- `src/chat/ChatLog.tsx`
- `src/chat/ChatLog.test.tsx`
- `src/chat/ChatView.tsx`
- `MEMORY.md`

## Interfaces

- `ChatImage({ sessionId: string, item: ChatItem }): JSX.Element | null` (`src/chat/ChatImage.tsx`).
- `ChatEntry({ item, sessionId })`; `ChatLog` gains a `sessionId` prop.
- Tool result contract: the connector's 202 body `{id, status, path}` relayed unchanged by the orchestrator and the plugin (orch-chat-images-route, mxc-images-route); `path` is workdir-relative.

## Expected outcome

The session web chat shows a picture the agent sent, from the session's own download route, and nothing else in the chat can render an image.

## Steps

- Read `entries.tsx`, `ChatLog.tsx`, `ChatView.tsx`, `chatModel.ts` (`toolItem`), `src/api/files.ts` and their tests as merged on main (slash-commands-from-chat edits `entries.tsx` and `chatModel.ts`).
- Red: `src/chat/ChatImage.test.tsx` (ac1-ac3) and the image tool row case in `ChatLog.test.tsx` (ac4); run `npx vitest run src/chat/ChatImage.test.tsx`: fails (no module).
- Green: `ChatImage.tsx`, the row, the prop threading, MEMORY.md; run the task's verify: passes. Quote the summary line.

## Notes

- `ChatLog.test.tsx` imports `entries.tsx`, which imports `react-markdown`; in agent pods `node_modules` lacks it (baseline 2026-10-29). Run `npm ci` first; when the install is not possible here, say so and let the PR CI be the gate for `ChatLog.test.tsx`, quoting both.
- `fileDownloadUrl` (`src/api/files.ts`) builds the relative URL from `base()`; no `agent_id` (session-level download, D8).
- The download route answers `X-Content-Type-Options: nosniff` and `Cache-Control: no-store` (orchestrator `_DownloadRelay`).
