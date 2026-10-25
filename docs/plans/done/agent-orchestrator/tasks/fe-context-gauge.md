---
title: fe context gauge
status: done
repo: agent-orchestrator
value: "The circular 0-100% context indicator the user asked for, honest about unknown values and the auto-compact point."
files: [frontend/src/ribbon/ContextGauge.tsx, frontend/src/ribbon/ContextGauge.test.tsx]
verify: "cd frontend && npm ci --no-audit --no-fund && npx vitest run src/ribbon/ContextGauge.test.tsx src/layout/designRules.test.ts && npm run lint"
depends_on: [fe-theme-port]
model: ""
review: ""
verified_head: 004aeb059e2a1e18a92bc9a0d6deb9e8e7b676c1
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 2
actual_tokens: 185190
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 146109, review 39081"
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

- AC1: renders the rounded percentage and aria-valuenow [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/ribbon/ContextGauge.test.tsx -t 'renders rounded percentage']
- AC2: null renders an unknown empty ring [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/ribbon/ContextGauge.test.tsx -t 'null renders unknown']
- AC3: values clamp to 0-100 [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/ribbon/ContextGauge.test.tsx -t 'clamps values']
- AC4: the auto-compact tick is drawn and the arc warns past it [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/ribbon/ContextGauge.test.tsx -t 'draws auto compact tick and warns past it']
- AC5: design rules still hold [evidence: command:cd frontend && (test -d node_modules || npm ci --no-audit --no-fund) && npx vitest run src/layout/designRules.test.ts -t 'source files follow the design rules']

## Files

- `frontend/src/ribbon/ContextGauge.tsx`
- `frontend/src/ribbon/ContextGauge.test.tsx`

## Interfaces

- `frontend/src/ribbon/ContextGauge.tsx:ContextGauge` (contract `context-gauge`)

## Expected outcome

A reusable gauge for cluster rows (max over agents) and agent rows.

## Steps

- Write ContextGauge.test.tsx with the four named tests (jsdom). Run it; expect failures.
- Implement ContextGauge.tsx.
- Rerun; expect `4 passed`.
- Run the designRules test and `npm run lint`.

## Notes

ros2 has no determinate CircularProgress (brief-ui section 2), so this component is new. The denominator is the full model window (wrapper `used_percentage`); the tick comes from the cluster's `auto_compact_pct`.
