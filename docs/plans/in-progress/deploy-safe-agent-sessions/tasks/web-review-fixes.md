---
title: web-review-fixes
status: todo
repo: agents-web
value: a red web build never publishes a tagged chart and the discard notice names the right data
files: [.github/workflows/ci.yaml, scripts/ci.test.mjs, src/sessions/DiscardSessionDialog.tsx, src/sessions/DiscardSessionDialog.test.tsx, src/chat/ChatView.test.tsx]
verify: "npx vitest run src/sessions/DiscardSessionDialog.test.tsx src/chat/ChatView.test.tsx && node --test scripts/ci.test.mjs"
depends_on: [web-discard-backup-notice]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 950968
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web-review-fixes

## Requirement

Epic review findings for agents-web (.scratchpad/session-loss/review/web.md and security.md), my call to fix before merge:
1. `.github/workflows/ci.yaml` job `chart-publish-tag` needs only `[chart]`, so a tag build publishes the chart even when the `web` job (lint, tests) or `images` is red; make it need `[chart, images, web]` like `chart-publish`, and add a top-level `permissions: contents: read` block (raise per job only where needed). Extend scripts/ci.test.mjs so the gate is asserted for the tag job too.
2. `src/sessions/DiscardSessionDialog.tsx` (about lines 30-36): the `restore_failed` / `restore_skipped` wording always says the workspace is not saved, even when the side that is not backed up is the transcripts; name the right subject (workspace files vs chat history) per side.
3. No test asserts that `src/chat/ChatView.tsx` mounts `AgentUnavailableBanner`; add one.
Test first.

## Acceptance conditions

- AC1: chart-publish-tag needs web, images and chart [evidence: command:node --test scripts/ci.test.mjs]
- AC2: the discard dialog names the chat history when the transcripts side is not backed up [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the chat history when transcripts are not backed up"]
- AC3: the discard dialog names the workspace files when the workdir side is not backed up [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the workspace files when the workdir is not backed up"]
- AC4: ChatView renders the agent-unavailable banner when messages are queued and no agent is alive [evidence: command:npx vitest run src/chat/ChatView.test.tsx -t "mounts the agent unavailable banner"]
- AC5: the workflow declares top-level permissions [evidence: command:grep -q "^permissions:" .github/workflows/ci.yaml]

## Files

- `.github/workflows/ci.yaml`
- `scripts/ci.test.mjs`
- `src/sessions/DiscardSessionDialog.tsx`
- `src/sessions/DiscardSessionDialog.test.tsx`
- `src/chat/ChatView.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
