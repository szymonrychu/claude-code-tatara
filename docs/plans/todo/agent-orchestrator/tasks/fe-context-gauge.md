---
title: fe context gauge
status: todo
repo: agent-orchestrator
value: "The circular 0-100% context indicator the user asked for, honest about unknown values and the auto-compact point."
files: [frontend/src/ribbon/ContextGauge.tsx, frontend/src/ribbon/ContextGauge.test.tsx]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/ribbon/ContextGauge.test.tsx src/layout/designRules.test.ts && npm run lint"
depends_on: [fe-theme-port]
owns: [context-gauge]
uses: [fe-theme]
model: ""
estimate: 5
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

# fe context gauge

## Requirement

`ContextGauge {value: number | null, autoCompactPct?: number, size?: 'small' | 'medium', label?: string}` (D13).

- It draws a determinate MUI CircularProgress over a track ring, with the rounded percentage as a centred label.
- The value is clamped to 0-100.
- `null` draws an empty ring with label `-` and aria-label `context unknown`.
- When `autoCompactPct` is given, a tick mark is drawn at that angle.
- At or above autoCompactPct the arc uses the warning token.
- Colours come only from theme TOKENS.
- `role=progressbar` with aria-valuenow.

## Acceptance conditions

- AC1: renders the rounded percentage and aria-valuenow [evidence: test:frontend/src/ribbon/ContextGauge.test.tsx::renders rounded percentage]
- AC2: null renders an unknown empty ring [evidence: test:frontend/src/ribbon/ContextGauge.test.tsx::null renders unknown]
- AC3: values clamp to 0-100 [evidence: test:frontend/src/ribbon/ContextGauge.test.tsx::clamps values]
- AC4: the auto-compact tick is drawn and the arc warns past it [evidence: test:frontend/src/ribbon/ContextGauge.test.tsx::draws auto compact tick and warns past it]
- AC5: design rules still hold [evidence: test:frontend/src/layout/designRules.test.ts::source files follow the design rules]

## Files

- `frontend/src/ribbon/ContextGauge.tsx`
- `frontend/src/ribbon/ContextGauge.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
