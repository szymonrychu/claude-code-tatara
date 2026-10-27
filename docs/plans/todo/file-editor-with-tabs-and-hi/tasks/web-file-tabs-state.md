---
title: web file tabs state
status: todo
repo: agents-web
value: "open files, their mode, unsaved edits, saves and conflicts are tracked per session without losing edits"
files: [src/files/useFileTabs.ts, src/files/useFileTabs.test.ts]
verify: "mise exec -- npx vitest run src/files/useFileTabs.test.ts && mise exec -- npx tsc -b && mise run lint"
depends_on: [web-sync-write-api]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web file tabs state

## Requirement

Epic README goals, verbatim: "Multiple files open at once as tabs, styled like the terminal tabs (closable, scrollable)." and "RO/RW editor mode: read-only by default, RW lets the user edit and save the file back to the agent's workspace (new write route in claude-code-wrapper and orchestrator)."

Epic README non-goal, verbatim: "Open tabs are not persisted across page reloads."

User decision U3, verbatim: "(my call) 'RW editor mode': read-only by default with an RO/RW toggle per tab; RW enables editing and Save (button and Ctrl/Cmd+S); new write route in the wrapper (PUT file content, UTF-8 text only, size cap = the existing file_preview_max_bytes, existing workspace path guards, optimistic concurrency via the mtime/size the editor loaded: a changed file answers 409 and the UI offers reload or overwrite) and an orchestrator forwarding route, then `npm run sync:api -- orchestrator`. Binary and too_large files open read-only with the current note, no editor."

User decision U5 (tabs part), verbatim: "tabs mirror TerminalPanel (MUI Tabs scrollable, closable tab with IconButton aria-label 'Close <name>', closing picks the neighbour, all tabs stay mounted), one tab per path (re-opening focuses it), unsaved changes mark the tab and closing a dirty tab asks to confirm. Tabs are per session, not persisted across reloads."

User decision U6, verbatim: "(my call) Live refresh: an open RO tab refetches when the tree reports a changed mtime|size (existing behaviour); a dirty RW tab never auto-reloads, it shows a 'changed on disk' notice instead."

Design D12 (state part), verbatim: "`src/files/useFileTabs.ts` holds the tabs of one session: path, name, kind (`loading`, `text`, `binary`, `too_large`, `other`, `error`), mode (`ro` default, `rw`), the loaded or saved text and its stamp (the baseline `{mtime, size}`), dirty (current text differs from the baseline text), saving, save error, `conflict` (a save answered 409 `file_changed`), `changedOnDisk` (the file changed while dirty), `doc`/`docVersion` for the editor. One tab per path: opening an open path focuses it without a refetch. Closing picks the neighbour (`rest[min(index, len - 1)]`, as `TerminalPanel`). RO is refused while the tab is dirty (save, reload or close first) (my call). Save sends `writeFile(..., baseline)`; success makes the answer the new baseline; 409 `file_changed` sets `conflict`, offering Reload (refetch, edits discarded) or Overwrite (`expected: null`); any other error shows inline as `<code>: <message>`. Stale answers (a tab closed or reloaded again meanwhile) are dropped. Tabs are per session and in memory only: a module-level store keyed by session id keeps each session's tabs (text, mode, dirty state, baseline) for the page's lifetime, so switching to another session and back restores them (the Workspace remounts the panel per session); a reload starts empty (my call, so a session switch never loses edits silently)."

Design D14, verbatim: "for each open tab the panel feeds the hook the `mtime|size` stamp of its entry in the loaded tree listings. The hook acts when that stamp differs from the last stamp it saw for the path (initialised to the baseline when the tab opens) and from the tab's baseline: an RO tab or a clean RW tab refetches (mode kept); a dirty RW tab never auto-reloads, it sets `changedOnDisk`, shown as a notice with Reload and Keep editing (my call: clean RW tabs refetch too, no edit can be lost). A save's own new stamp equals the baseline, so it triggers nothing. An agent write event for the path (`fileEvents` `written`) applies the same rule. A refetch that answers another kind (binary, too_large, error) turns the tab into that note."

Scope (agents-web):
- `src/files/useFileTabs.ts` (new): `useFileTabs(sessionId)` and its types, built on `readFile` and `writeFile` (src/api/files.ts) and `errorText` (src/files/useFileTree.ts).
- `src/files/useFileTabs.test.ts` (new, `// @vitest-environment jsdom`, `renderHook`, `../api/files` mocked with `vi.hoisted`): the tests below.

## Acceptance conditions

- ac1: `open(path, type)` adds a tab named by the last path segment, makes it active and loads it with `readFile`; a `text` answer gives kind `text` with `doc` the content, mode `ro` and the baseline `{mtime, size}`; `binary` and `too_large` answers give those kinds; type `other` gives kind `other` without a `readFile` call; a rejected read gives kind `error` with `<code>: <message>`; opening an open path focuses it and calls `readFile` no more (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'open and focus']
- ac2: closing the active tab activates its right neighbour, or the left one when it was last, and none when it was the only one; closing an inactive tab keeps the active one; a read answering after its tab closed changes nothing (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'close picks the neighbour']
- ac3: `edit(path, text)` marks the tab dirty when the text differs from the baseline text and clean again when it equals it; `setMode(path, 'ro')` is refused while dirty and the tab stays `rw`; a clean tab switches both ways (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'dirty and mode']
- ac4: `save(path)` calls `writeFile(sessionId, path, text, baseline)` with `saving` true until it settles; success makes the answer the baseline and the tab clean; a 409 `file_changed` sets `conflict` and keeps the text and dirty mark; another error sets the save error to `<code>: <message>`; `overwrite(path)` calls `writeFile` with `null` and clears `conflict` on success; `reload(path)` refetches, bumps `docVersion`, drops the edits and clears `conflict` and `changedOnDisk` (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'save conflict overwrite reload']
- ac5: `observe(stampOf)` with a changed `mtime|size` stamp refetches an RO tab and a clean RW tab (mode kept, `docVersion` bumped); for a dirty RW tab it sets `changedOnDisk` and does not call `readFile`; the stamp of the tab's own save triggers nothing; an unchanged stamp, a null stamp (entry not listed) and a symlink entry's stable stamp after the first refetch trigger nothing more; a refetch answering `binary` turns the tab into that kind (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'live refresh rules']
- ac6: `written(path)` applies the same rule: refetch for a clean tab, `changedOnDisk` for a dirty one, nothing for a path with no tab (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'written events']
- ac7: unmounting and mounting the hook again for the same session restores its tabs, the active tab, each mode, dirty text and baseline without a `readFile` call; another session starts with no tab; a `sessionId` change on a mounted hook shows the other session's tabs and back (new) [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts -t 'tabs per session']
- ac8: the targeted suite, the type check and lint pass [evidence: command:mise exec -- npx vitest run src/files/useFileTabs.test.ts && mise exec -- npx tsc -b && mise run lint]

## Files

- `src/files/useFileTabs.ts`
- `src/files/useFileTabs.test.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
