---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/package.json"
  - "**/tsconfig.json"
---

# TypeScript / React

Verify before claiming done:
`pnpm typecheck && pnpm lint && pnpm test:run`
(`tsc --noEmit` where there is no typecheck script). Never leave `tsc` errors.

- Do not invent props, hooks, or exports on a third-party component. Read its
  `.d.ts` or fetch current docs (context7) first. This is the most common
  failure in generated frontend code, and it type-checks as an error only if
  the types are actually installed.
- No `any`. Use `unknown` plus narrowing. `@ts-expect-error` requires a comment
  naming the reason.
- Hooks at the top level only. Keep `exhaustive-deps` clean rather than
  disabling it.
- Accessibility is lintable, not aspirational: keep `jsx-a11y` rules passing
  rather than promising to remember alt text and labels.
- Named exports over default exports.
