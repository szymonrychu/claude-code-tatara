---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/package.json"
  - "**/tsconfig.json"
---

# TypeScript / React

Verify before claiming done:
`npm run lint && npm test && npm run build`
(`tsc --noEmit` where there is no typecheck script). Never leave `tsc` errors.

- Do not invent props, hooks, or exports on a third-party component. Read its
  `.d.ts` or fetch current docs (context7) first. This is the most common
  failure in generated frontend code, and it type-checks as an error only if
  the types are actually installed.
- No `any`. Use `unknown` plus narrowing. `@ts-expect-error` requires a comment
  naming the reason.
- Hooks at the top level only. Keep `exhaustive-deps` clean rather than
  disabling it.
- ESLint complexity rules: complexity 15, max-depth 4, max-lines-per-function 80 (skip blanks and comments),
  max-params 4, max-lines 400; bulk suppressions are the only baseline.
- Named exports over default exports.
