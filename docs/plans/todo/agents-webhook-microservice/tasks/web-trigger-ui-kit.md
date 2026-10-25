---
title: web trigger ui kit
status: todo
repo: agents-web
value: "trigger pages (webhooks now, schedules next) share one status chip, preset picker, polling hook and form error display"
files: [src/triggers/index.ts, src/triggers/RunStatusChip.tsx, src/triggers/PresetSelect.tsx, src/triggers/usePoll.ts, src/triggers/FormError.tsx, src/triggers/triggers.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/triggers/triggers.test.tsx && npm run lint"
depends_on: []
owns: [trigger-ui-page-pattern]
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

# web trigger ui kit

## Requirement

The shared trigger page pattern in agents-web (design D11; contract `trigger-ui-page-pattern`, consumed by agents-schedule-microservice). Paths are in code/agents-web, following its MUI and test conventions.

- `RunStatusChip({status, reason?})`: MUI Chip per status `new` (default), `in-progress` (info, spinner icon), `handled` (success), `ignored` (default, outlined), `failed` (error); the reason as a tooltip and `aria-label` "<status>: <reason>".
- `PresetSelect({value, onChange, disabled?})`: loads presets through the orchestrator client the app already has (`GET /api/v1/presets` via the orchestrator backend's base path), shows name and a default mark, a loading and an error state.
- `usePoll(fn, intervalMs, deps)`: calls `fn` now and every `intervalMs` while the document is visible, stops on unmount, exposes `{data, error, loading, refresh}`; no overlapping calls.
- `FormError({error})`: renders the backend's `{error: {code, message}}` or a network error in an Alert.
- `index.ts` re-exports them.
- `src/triggers/triggers.test.tsx` (vitest, jsdom, fetch mocked as the existing tests do): each status renders its color and label; PresetSelect lists presets, shows the error state; usePoll polls with fake timers, pauses when hidden and never overlaps; FormError shows code and message.

## Acceptance conditions

- AC1: each run status renders its own chip with the reason [evidence: command:npx vitest run src/triggers/triggers.test.tsx -t RunStatusChip]
- AC2: PresetSelect lists orchestrator presets and shows load errors [evidence: command:npx vitest run src/triggers/triggers.test.tsx -t PresetSelect]
- AC3: usePoll polls on an interval, pauses when hidden and never overlaps calls [evidence: command:npx vitest run src/triggers/triggers.test.tsx -t usePoll]
- AC4: types and lint pass [evidence: command:npx tsc -b && npm run lint]

## Files

- `src/triggers/index.ts`
- `src/triggers/RunStatusChip.tsx`
- `src/triggers/PresetSelect.tsx`
- `src/triggers/usePoll.ts`
- `src/triggers/FormError.tsx`
- `src/triggers/triggers.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
