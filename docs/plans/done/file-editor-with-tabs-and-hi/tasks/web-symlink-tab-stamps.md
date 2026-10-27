---
title: web symlink tab stamps
status: done
repo: agents-web
value: "symlink tabs get no false changed-on-disk notice and keep undo history; one stamp helper"
files: [src/files/useFileTabs.ts, src/files/useFileTabs.test.ts, src/files/FilesPanel.tsx]
verify: "mise exec -- npx vitest run src/files && mise exec -- npx tsc -b && mise run lint"
depends_on: [web-files-split-layout]
model: sonnet
review: ""
verified_head: 4c2690c948c72b6690bebf8dff55375f63a9100b
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: 2
actual_minutes: 4
actual_tokens: 414142
actual_roles: "impl 3, review 1"
actual_role_tokens: "impl 346491, review 67651"
---

# web symlink tab stamps

## Requirement

Epic review finding (whole-epic reviewer, 2026-10-27), verbatim: "src/files/useFileTabs.ts:123 (`answer` seeds `e.seen`; `observe` at ~l.281). The first stamp comes from the content answer, which is the target's `mtime|size`. The tree listing stamps a symlink entry by itself (wrapper `files.py` `entry.stat(follow_symlinks=False)`, size null), so the first `observe` always sees a change. A dirty RW tab on a symlink gets a false "changed on disk" notice. A clean RW tab is refetched, which resets the editor and its undo history. Later edits to the target are never detected through the listing. The save's 409 still protects the file. Fix: seed `seen` from the first listing stamp, as the old FilesPanel did, or skip `observe` for symlinks."

Scope audit duplicate (2026-10-27), verbatim: "The `mtime|size` stamp format is spelled twice: src/files/FilesPanel.tsx:113 builds it as `${e.mtime}|${e.size}`; src/files/useFileTabs.ts:97 has `stampKey`, which is not exported. Suggested task: export `stampKey` and use it in `FilesPanel`."

Scope (agents-web): a tab opened on a symlink never gets a false "changed on disk" notice or a refetch from the first listing observation; the live-refresh comparison uses the same stamp source on both sides (listing stamp vs listing stamp), so a change to the listed entry is still detected; `stampKey` is exported from useFileTabs.ts and FilesPanel.tsx uses it instead of its own template string. The existing test at useFileTabs.test.ts:332 ("refetches once") is no longer accurate for symlinks and is updated with the reason stated in the commit.

## Acceptance conditions

- ac1: a dirty RW tab opened on a symlink gets no "changed on disk" notice from the first listing observation, and a clean one is not refetched [evidence: test:src/files/useFileTabs.test.ts::symlink tab first observation is not a change]
- ac2: after the first observation, a changed listing stamp for the same entry still triggers the live-refresh behaviour (notice when dirty, refetch when clean) [evidence: test:src/files/useFileTabs.test.ts::symlink tab later listing change is detected]
- ac3: FilesPanel builds stamps only through the exported stampKey [evidence: command:grep -q 'export function stampKey\|export const stampKey' src/files/useFileTabs.ts && ! grep -qE '\$\{[a-z]+\.mtime\}\|\$\{[a-z]+\.size\}' src/files/FilesPanel.tsx]
- ac4: the targeted suites, type check and lint pass [evidence: command:mise exec -- npx vitest run src/files && mise exec -- npx tsc -b && mise run lint]

## Files

- `src/files/useFileTabs.ts`
- `src/files/useFileTabs.test.ts`
- `src/files/FilesPanel.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-27 done
