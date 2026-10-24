# workspace-ui-fixes record

## Summary

Asked (2026-10-24): visible vertical dividers between the files, chat and terminal panes; file tree updates by itself with no refresh button.
Shipped in agent-orchestrator: 2px inline-flex-basis dividers, change-only tree refresh with pollExpanded, nearest-ancestor write refresh (incl. notebook_path), 3s visible-tab poll, preview refetch on mtime/size change, refresh button removed.
Build run wf_fb7b0769-f15: 3/3 clean, 0 escalated, 0 blocked. Epic-close audit wf_331aa193-0f3: gaps none, U1/U2/X2 landed. Reviewer verdict pass, no act-on findings.
Verification: pytest 530 passed, vitest 200 passed, lint clean. `mise run apply` finished, `mise run smoke`: "smoke: OK".
Open: live divider rendering/drag and live tree behaviour are not verified (user smoke).

## Planned vs built

| Task | Status | Review rounds | Continuations | Files | Verifier head | Verification tail | Red evidence (implementer tests.red) |
|---|---|---|---|---|---|---|---|
| pane-divider-lines | done | 1 | unknown | frontend/src/layout/Workspace.tsx, Workspace.test.tsx | f2b25e81b32c67ea6c32d03ca5b322d5c6f7fe98 | verify: pass `vitest Workspace.test.tsx designRules.test.ts && npm run lint` | `-t divider`: "Tests  1 failed | 16 skipped (17)" |
| tree-change-only-refresh | done | 2 | unknown | frontend/src/files/useFileTree.ts, fileEvents.ts, FilesPanel.test.tsx | e4a80eb32b3ee13487ab41bec896ec97412cbfa5 | verify: pass `vitest FilesPanel.test.tsx && npm run lint` | `-t multi-page` (round-2 fix test only): "expect(result.current.state).toBe(before) failed; Tests 1 failed | 18 skipped (19)". Result says wroteTestFirst true but processGaps says red-first not followed (implementer disclosed); files win: initial tests were written after the code |
| files-auto-poll-no-button | done | 1 | unknown | frontend/src/files/FilesPanel.tsx, FilesPanel.test.tsx, MEMORY.md | 0f99a786e0045e77d491887dac203a2ca6c1a98e | verify: pass `vitest FilesPanel.test.tsx && npm run lint`; self-run also build and check:api clean (26 passed) | "Tests  7 failed | 19 passed (26)" |

Git (code/agent-orchestrator): f2b25e8 (dividers), 4ea4e96 and 708cd7e (same subject, tree refresh; see Duplicates), e4a80eb (multi-page commit-once fix), 0f99a78 (auto poll), merge 964db9a (PR #7).

Approvals:

| id | text | decisions | tasks | status |
|---|---|---|---|---|
| U1 | Visible vertical divider lines between the files, chat and terminal panes. | D1 | pane-divider-lines | delivered (live rendering: user smoke) |
| U2 | File tree updates automatically on file changes; refresh button removed. | D2 | tree-change-only-refresh, files-auto-poll-no-button | delivered (live behaviour: user smoke) |
| X2 | Headless parity: no new UI capability without a documented public API; tree reads existing files API. | D3 | files-auto-poll-no-button | delivered (frontend + MEMORY.md only; check:api clean) |

## Deviations and rulings

- No rulings escalated; forwardMerged: none.
- Divider width 2px instead of earlier 4px. Why: requirement allows any explicit size; borderStrong token. Cost if wrong: cosmetic, one-line change.
- Full suite not run by the files-auto-poll task (targeted tests only). Why: task instructions. Cost if wrong: regression elsewhere; covered by the later full run (pytest 530, vitest 200 passed).
- Root retry in error/missing state uses mode 'first' (briefly flips loading each poll). Why: requirement only asks for retry. Cost if wrong: possible loading flicker while the root is in error; not verified against FilesPanel rendering.

## Duplicates reconciled

none reported by the audit. Git log shows 4ea4e96 and 708cd7e with identical subjects; not explained by the inputs (likely rebase/landing artifact); unknown.

## Discovered and blocked

- cannotVerify, cleared by user smoke after deploy: live divider rendering, drag/double-click/keyboard resize in a browser; live tree updates with terminal writes (AC8); real EventSource onOpen on reconnect (tested via mocked stream); 409 agent_not_ready / 404 workdir recovery timing against a real backend.
- Process gap: tree-change-only-refresh tests written after implementation (no red-first). Cleared by: none needed for this epic; see Lessons.
- Declined review nits (no action): dead branch `if (mode !== 'refresh') settle(false)` and unused `renders` counter in useFileTree code/tests; no test isolates the busy-ref in-flight guard from dirs[p].loading; panel-level no-rerender not tested (pinned in hook tests).
- Root cause found: react-resizable-panels 4.14.8 Separator writes inline `flex-basis: auto` that beats the emotion `flex` shorthand (recorded in MEMORY.md).

## Research that changed the plan

react-resizable-panels 4.14.8 inline styleDefaults flex-basis: auto overrides CSS shorthand; plan changed to set an explicit inline flex-basis on both Dividers (pane-divider-lines requirement). Amends design D25 (refresh button) per U2.

## Cost

Build run: 15 agents; audit run: 2 agents. Continuations: unknown. Wall-clock: README Actual 10 min vs estimate 15 agent-min.

| Task | estimate | actual | actual_roles |
|---|---|---|---|
| pane-divider-lines | 5 | 2 | impl 1, verify 1, review 1, land 1 |
| tree-change-only-refresh | 5 | 5 | impl 2, verify 1, review 2, fix 1, land 1 |
| files-auto-poll-no-button | 5 | 3 | impl 2, verify 1, review 1, land 1 |

README Time: Estimate 15 agent-min, critical path 10 min, Actual 10 min.

## MRs and deploy

- agent-orchestrator PR #7 (workspace-ui-fixes): merged, merge commit 964db9a.
- agents-helmfile PR #10: merged, bump to 964db9a.
- Deploy: `mise run apply` finished; `mise run smoke`: "smoke: OK". Pipeline state: unknown.

## Lessons routed to

- Tests written after code (tree-change-only-refresh): mechanical; the existing verify-task red check relies on implementer tests.red, and the result reported wroteTestFirst true against its own processGaps. Add a check that fails the task result when processGaps contains red-first and wroteTestFirst is true.
- Inline-style vs CSS shorthand library defaults: judgement call; MEMORY.md pitfall entry already added, no further rule.
