---
title: web-review-fixes
status: done
repo: agents-web
value: a red web build never publishes a tagged chart and the discard notice names the right data
files: [.github/workflows/ci.yaml, scripts/ci.test.mjs, src/sessions/DiscardSessionDialog.tsx, src/sessions/DiscardSessionDialog.test.tsx, src/chat/ChatView.test.tsx]
verify: "npx vitest run src/sessions/DiscardSessionDialog.test.tsx src/chat/ChatView.test.tsx && node --test scripts/ci.test.mjs"
depends_on: [web-discard-backup-notice]
model: sonnet
review: ""
verified_head: 454e1aa2a40f252bfdcbca82a5ebabe74140195c
points: 3
expected_minutes: 6
expected_tokens: 950968
points_actual: 2
actual_minutes: 6
actual_tokens: 644127
actual_roles: "impl 6, review 1"
actual_role_tokens: "impl 555731, review 88396"
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

- Red: write the tests the acceptance conditions name; run `npx vitest run src/sessions/DiscardSessionDialog.test.tsx src/chat/ChatView.test.tsx && node --test scripts/ci.test.mjs` and see them fail for the expected reason.
- Green: implement the requirement as written; run `npx vitest run src/sessions/DiscardSessionDialog.test.tsx src/chat/ChatView.test.tsx && node --test scripts/ci.test.mjs` and expect every test to pass.
- Refactor with the verify green; add a dated MEMORY.md entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done
