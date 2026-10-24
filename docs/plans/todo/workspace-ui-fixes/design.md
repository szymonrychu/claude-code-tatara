# workspace ui fixes design

## Summary

Two frontend fixes in agent-orchestrator. Dividers: the react-resizable-panels Separator writes an inline `flex-basis: auto` that makes our 4px divider 0px wide; give it an explicit size. File tree: drop the refresh button and keep the tree current with the existing instant stream path (fixed for new directories and NotebookEdit) plus a visible-tab poll of the root and expanded directories that commits only real changes. No backend or API change.

## Intent and why

The user cannot see where the panes end, and the file tree shows stale files; a manual refresh button is not acceptable (U2).

## Goals

- Visible vertical lines between files, chat and terminal (U1).
- The tree reflects writes from agents, terminals and any other writer without a click, including new directories and notebook edits (U2).
- No refresh button.

## Non-goals

- No wrapper file-watch or inotify, no new event type, no new endpoint (X2: the tree reads the existing files API).
- Phone layout unchanged.

## Anti-goals

- Idle polling that re-renders the tree or swallows a pending "Load more".
- Polling while the tab is hidden.

## Constraints

Design guard `designRules.ts`: tokens only, no colour literals, spacing grid. Frontend only, one repo, no openapi regen.

## Decisions

### D1: Explicit divider size, borderStrong colour (U1)
Pass an explicit pixel flex-basis on the Separator (props.style wins over styleDefaults) and colour from `TOKENS.borderStrong`. Alternative: width in the styled rule only (loses to nothing, but basis still auto). Serves A1.

### D2: Frontend stream plus visible-tab poll, no inotify (U2, GATE) (my call)
Keep `fileEvents` for instant reaction, fix nearest-loaded-ancestor and `notebook_path`, add a 3 s poll while the tab is visible plus a pass on visibilitychange and stream open; commit state only when a listing differs; skip in-flight directories. Alternative: wrapper inotify pushing `files_changed` events (three repos, reverses prior D25 "no inotify", watch limits on node_modules, misses check Jobs). The poll covers terminals and every writer with one repo. Amends prior D25: the manual button half is reversed, no inotify stays. Serves A2.

### D3: Headless parity (X2)
The tree uses the existing public files API; no new capability needs a new endpoint. Serves A2.

## Research

| Lens | Status | Adopted | Rejected |
|---|---|---|---|
| code-internal | ran (brief-frontend.md) | option A | option B inotify, option C server-side poll |
| external, papers, docs | skipped: library behaviour verified in node_modules source | | |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| brief section 1 | Separator inline flex-basis pitfall | pane-divider-lines |
| brief section 3 gaps 2, 3, 5 | ancestor refresh, notebook_path, error recovery | tree-change-only-refresh |
| brief section 4 option A | poll, change-only commit, preview mtime refetch | tree-change-only-refresh, files-auto-poll-no-button |
| brief plan inputs | MEMORY.md entries | files-auto-poll-no-button |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 Explicit divider size | pane-divider-lines |
| D2 Stream plus poll | tree-change-only-refresh, files-auto-poll-no-button |
| D3 Headless parity | files-auto-poll-no-button |

## Contracts

None. `pollExpanded` is internal to the files module (tree-change-only-refresh to files-auto-poll-no-button via dependsOn).

## Review focus

Poll cost and in-flight skip in useFileTree; fake-timer tests; no timer leak on unmount.

## Left to the builder

Exact divider pixel size (2 to 4px, hit area stays the library's) and poll implementation detail (hook vs effect).

## Assumptions and unknowns

Real-browser divider pixels and live refresh are unverifiable by agents; confirmed by user smoke after deploy.

## Open questions
