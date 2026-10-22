---
title: fe theme port
status: todo
repo: agent-orchestrator
value: "The look the user asked for: the ros2 web UI's dark, flat theme, with its design rules enforced by a test from day one."
files: [frontend/src/theme.ts, frontend/src/theme.test.ts, frontend/src/index.css, frontend/src/main.tsx, frontend/src/layout/designRules.ts, frontend/src/layout/designRules.test.ts, frontend/src/layout/useLayout.ts, frontend/src/layout/ConfirmDialog.tsx]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/layout/designRules.test.ts src/theme.test.ts && npm run lint"
depends_on: [fe-scaffold]
owns: [fe-theme]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# fe theme port

## Requirement

Port the ros2 web_ui theme and layout primitives (D12). Sources: `/Users/szymonri/Documents/ros2-lerobot-sverve-platform/nodes/web_ui/frontend/src`.

Files to port:
- `theme.ts`: the TOKENS (bgCanvas #0f1013, bgPanel #16181d, bgRaised #1d2026, border #2a2e36, text levels, single grey accent #e8eaed, error #e5484d, warning #e2a336, radius 2, control 32 px, touch 44 px), the font stacks, the typography and the component overrides, adapted to the MUI 9 API. It stays dark only.
- `theme.test.ts`.
- `index.css`, which pins #root to 100dvh, a flex column, overflow hidden.
- `main.tsx`: wraps App in ThemeProvider and `CssBaseline enableColorScheme`.
- `layout/designRules.ts` and its test. The rules: no colour literals outside theme.ts, no shadows or gradients, font weights 400 and 500 only, a 0.5 spacing grid, no decorative unicode, no `title=` on buttons. The test scans every file under src/.
- `layout/useLayout.ts` (phone, tablet and desktop breakpoints).
- `layout/ConfirmDialog.tsx` (destructive confirm).

## Acceptance conditions

- AC1: the design rules hold across the whole src tree [evidence: test:frontend/src/layout/designRules.test.ts::source files follow the design rules]
- AC2: the theme is dark with the ported tokens [evidence: test:frontend/src/theme.test.ts::theme uses the dark ported tokens]
- AC3: lint passes [evidence: command:cd frontend && npm ci --no-audit --no-fund && npm run lint]

## Files

- `frontend/src/theme.ts`
- `frontend/src/theme.test.ts`
- `frontend/src/index.css`
- `frontend/src/main.tsx`
- `frontend/src/layout/designRules.ts`
- `frontend/src/layout/designRules.test.ts`
- `frontend/src/layout/useLayout.ts`
- `frontend/src/layout/ConfirmDialog.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
