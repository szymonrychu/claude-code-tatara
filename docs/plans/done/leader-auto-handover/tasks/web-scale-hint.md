---
title: web scale hint
status: done
repo: agents-web
value: a refused scale-down tells the user the real reason
files: [src/chat/ScaleControl.tsx, src/chat/ScaleControl.test.tsx]
verify: "npx tsc -b && npx vitest run src/chat/ScaleControl.test.tsx && npm run lint"
depends_on: [scale-down-staying-peer]
model: sonnet
review: ""
verified_head: d3998572f4fab98cc417c48e0513bd67a83aba1e
points: 1
expected_minutes: 4
expected_tokens: 662742
points_actual: 1
actual_minutes: 2
actual_tokens: 375407
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 284246, review 91161"
---

# web scale hint

## Requirement

Goal G2, verbatim: "a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks; with no such agent it is refused as today." Goal G5: the UI shows it.

Design D11, verbatim: ScaleControl's `leader_would_leave` hint becomes "No ready agent that stays can take over leadership." (replacing "Make another agent leader first.").

Scope:
- `src/chat/ScaleControl.tsx`: the hint text on an `ApiError` with code `leader_would_leave`.
- Test no longer accurate, to update: `src/chat/ScaleControl.test.tsx` (around line 75) asserts the old hint "Make another agent leader first.", which no longer describes the refusal; it asserts the new text.

Notes: use the word "session", never "cluster" (`src/nomenclature.test.ts`). Retro: run `npx tsc -b` and the full `npm test` before handing back.

## Acceptance conditions

- AC1: a `leader_would_leave` refusal shows "No ready agent that stays can take over leadership." [evidence: command:npx vitest run src/chat/ScaleControl.test.tsx]
- AC2: the old hint is gone [evidence: command:test -z "$(git grep -n 'Make another agent leader first' -- src)"]
- AC3: types check and the full web suite passes [evidence: command:npx tsc -b && npm test]
- AC4: lint passes [evidence: command:npm run lint]

## Files

- `src/chat/ScaleControl.tsx`
- `src/chat/ScaleControl.test.tsx`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Red: update the hint assertion in `src/chat/ScaleControl.test.tsx` (no longer accurate); run `npx vitest run src/chat/ScaleControl.test.tsx`: fails.
- Green: change the hint in `ScaleControl.tsx`; run the task's verify command and `npm test`: pass.

## Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done
