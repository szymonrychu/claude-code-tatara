---
title: fe presets page
status: in-progress
repo: agent-orchestrator
value: "Presets is the first settings category in the hamburger menu, with create, copy, edit and delete"
files: [frontend/src/presets/PresetsPage.tsx, frontend/src/presets/PresetsPage.test.tsx, frontend/src/App.tsx, frontend/src/App.test.tsx]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetsPage.test.tsx src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-preset-form]
owns: []
uses: [fe-preset-form, fe-preset-client, orch-presets-api, orch-settings-menu]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/cluster-presets-fe-presets-page/agent-orchestrator
branch: cluster-presets-fe-presets-page
verified_head: ""
run: ""
provides: []
---

# fe presets page

## Requirement

Add Presets as the first settings category and its page (design D7; user Q5, Q10), test-first.

- New `frontend/src/presets/PresetsPage.tsx`: `PresetsPage({onBack})`, a full main-area view: a "Presets" heading, a "Back" button calling `onBack`, a "New preset" button, and the preset list from `listPresets()` (default first, marked with a "Default" chip). Each row offers Edit, Copy and Delete; the default row has no Delete. New, Edit and Copy open `PresetForm` (new, `preset`, `copyOf`); Delete asks through `ConfirmDialog` and then calls `deletePreset`; the list reloads after every save or delete; a server error (409 `preset_default`, `last_preset`, `conflict`) shows in an outlined Alert.
- `frontend/src/App.tsx`: passes `settingsCategories=[{id: 'presets', label: 'Presets', onOpen}]` through `TopBar` to `SessionsMenu` (cross-epic contract `orch-settings-menu`); `onOpen` replaces the main-area content with `PresetsPage` (App `view` state `cluster` or `presets`, no router); Back, or choosing a session in the menu, returns to the cluster view. The top bar stays visible.
- Tests: new `frontend/src/presets/PresetsPage.test.tsx`; `frontend/src/App.test.tsx` gains `presets_from_settings_menu`. All pass `designRules`.

## Acceptance conditions

- AC1: the page lists presets with the default marked and without a Delete action on it [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetsPage.test.tsx -t lists_presets_default_marked_without_delete]
- AC2: New preset, Edit and Copy open the preset form in the matching mode and the list reloads after save [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetsPage.test.tsx -t new_edit_copy_open_form_and_reload]
- AC3: Delete confirms, calls deletePreset and reloads; a 409 is shown [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetsPage.test.tsx -t delete_confirms_and_shows_conflict]
- AC4: Back calls onBack [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetsPage.test.tsx -t back_calls_on_back]
- AC5: the hamburger menu's Settings section lists Presets, which shows the page in the main area, and Back returns to the cluster tab [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/App.test.tsx -t presets_from_settings_menu]
- AC6: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetsPage.test.tsx src/App.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/presets/PresetsPage.tsx`
- `frontend/src/presets/PresetsPage.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`

## Interfaces

- `PresetsPage({onBack: () => void})` in `frontend/src/presets/PresetsPage.tsx`.
- Uses `SessionsMenu` `settingsCategories: {id, label, onOpen}[]` through `TopBar` (cross-epic contract `orch-settings-menu`), `PresetForm` (fe-preset-form), the preset client functions (fe-preset-client), `ConfirmDialog` (`layout/ConfirmDialog.tsx`).

## Expected outcome

Opening the hamburger menu shows Presets under Settings; it opens a page listing every preset where the user creates, copies, edits and deletes presets, and Back returns to the cluster tabs.

## Steps

- Write `PresetsPage.test.tsx` and add `presets_from_settings_menu` to `App.test.tsx` (titles as in the AC refs); run `mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetsPage.test.tsx src/App.test.tsx`: fails.
- Build the page and the App view switch; run the verify command: passes.

## Notes

- web-ui-cluster-tabs-with-fil passes an empty `settingsCategories` from App; this task supplies the one entry.
- Delete is offered only for non-default presets, but the page still shows a 409 from the server (for example `last_preset`).
