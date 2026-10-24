---
title: pane divider lines
status: in-progress
repo: agent-orchestrator
value: "files, chat and terminal panes are visibly separated"
files: [frontend/src/layout/Workspace.tsx, frontend/src/layout/Workspace.test.tsx]
verify: "cd frontend && npx vitest run src/layout/Workspace.test.tsx src/layout/designRules.test.ts && npm run lint"
depends_on: []
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/workspace-ui-fixes-pane-divider-lines/agent-orchestrator
branch: workspace-ui-fixes-pane-divider-lines
verified_head: ""
run: ""
provides: []
---

# pane divider lines

## Requirement

The separators between the files, chat and terminal panes in frontend/src/layout/Workspace.tsx render as visible vertical lines. Root cause: react-resizable-panels 4.14.8 Separator writes an inline style `flex-basis: auto` (styleDefaults) that beats the emotion `flex: 0 0 4px` shorthand, so the div is 0px wide. Fix by giving the Divider an explicit size the inline style cannot override (pass `style={{ flexBasis: ... }}` on the Separator, since props.style is spread after styleDefaults, and/or width in the styled rule), coloured from theme tokens only (TOKENS.borderStrong, not a colour literal), keeping hover/active/focus primary colour, drag, double-click reset and keyboard resize working. Applies to both separators, including next to the minimized strip. Phone layout is unchanged.

## Acceptance conditions

- AC1: each of the two separators has an inline flex-basis that is a pixel size, not auto [evidence: command:cd frontend && npx vitest run src/layout/Workspace.test.tsx -t "divider"]
- AC2: existing Workspace layout, double-click reset and keyboard resize tests still pass, and the design rules test passes [evidence: command:cd frontend && npx vitest run src/layout/Workspace.test.tsx src/layout/designRules.test.ts]
- AC3: the dividers are visibly drawn in the real browser (user smoke after deploy) [evidence: judgement:]

## Files

- `frontend/src/layout/Workspace.tsx`
- `frontend/src/layout/Workspace.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

Both separators render as visible lines of the intended pixel width.

## Steps

- Red: add a divider test asserting each separator inline flex-basis is a px size; run it and see it fail on 'auto'.
- Green: size the Divider, colour from TOKENS.borderStrong; run the verify command.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

- Divider is `styled(Separator)` in Workspace.tsx (flex `0 0 spacing(0.5)`, background `palette.divider`); TOKENS from '../theme' is already imported. Size: 2px line (my call), pass `style={{ flexBasis: 2 }}` (px) on both `<Divider>` uses, background `TOKENS.borderStrong`, hover/active/focus keep primary.
