---
title: web cache section
status: todo
repo: agents-web
value: "Users get a Cache section beside Sessions and Presets to see, refresh and delete S3 cache objects one at a time"
files: [src/backends/registry.ts, src/backends/registry.test.ts, src/cache/CachePage.tsx, src/cache/DeleteCacheObjectDialog.tsx, src/cache/CachePage.test.tsx, src/layout/formatBytes.ts, src/layout/formatBytes.test.ts, src/sessions/DiscardSessionDialog.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/cache src/backends/registry.test.ts src/layout/formatBytes.test.ts src/sessions/DiscardSessionDialog.test.tsx src/layout/designRules.test.ts src/nomenclature.test.ts && npm run build && npm run lint"
depends_on: [web-cache-client]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1919629
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web cache section

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goals, verbatim:
- G1: "agents-web has a Cache section in the orchestrator menu (beside Sessions and Presets) listing every object under the cache prefix with object name, kind (workspace or transcripts), class, size and last modified, filterable by class and searchable by name, paged."
- G2: "each object's class is current on every view: `in_use` (with the session slugs), `preset` (with the preset name), `legacy` (old `preset-*` copy, with how many live sessions copied it), `saved` or `other`; the object list itself is at most `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` old (default 900), shows when it was listed, and a Refresh lists again at once."
- G3: "a user deletes one object after typing its name; the orchestrator's reconciler refuses an object pinned by any session row (live, starting or discarding) or rewritten since it was listed, and the outcome (done, refused with reason, failed with reason) is shown."
- G5 (the gauge): "a quota gauge shows bytes and objects against the bucket quota set in agents-helmfile; [...]"

Design D6 (Web Cache section), verbatim: "`BACKEND_MENUS.orchestrator` gains Cache at order 50 (`registry.test.ts` exact list updated). Summary bar (quota gauge when known, "listed <age>", Refresh); class filter chips and name search; table Object, Kind, Class, Size, Last modified, Delete (disabled for `in_use`, with a tooltip); `ConfirmDialog` with typed object name, size, "cannot be undone" and "a later session with this name starts empty"; the request is polled every 5 s (`usePoll`) to its outcome; `formatBytes` moves from `DiscardSessionDialog.tsx:45` to a shared module."

Design D8, verbatim: "This epic lists old copies and deletes them one at a time on explicit action. [...]" Non-goal, verbatim: "Bulk or multi-select deletion, and automatic deletion of old copies (the clean-up-old-s3-session-cach epic)."

Open questions Q1, Q5 and Q6 are planned on their recommended answers (user decision: "Q1-Q6 in design.md are open; plan on the recommended answers").

This task delivers D6 in agents-web:

- `src/backends/registry.ts`: `BACKEND_MENUS.orchestrator` gains `{ id: 'cache', label: 'Cache', order: 50 }` rendering `CachePage` with `onBack`; the reserved-orders header gains `50 Cache`.
- New `src/cache/CachePage.tsx`: summary bar with a quota gauge for bytes and for objects against `quota` when it is set (hidden when null), "listed <age>" from `listed_at` (and the listing's failure reason when the newest listing failed), and a Refresh button that calls `refreshCache` and polls the request to its end, then reloads the list; class filter chips (all five classes) and a name search; a table with Object, Kind, Class (the slugs for `in_use`, the preset name for `preset`, "copied by N live sessions" for `legacy`), Size (`formatBytes`), Last modified and Delete; Delete is disabled for `in_use` with a tooltip naming the sessions; "Load more" pages with `next_after`; when `available` is false the page says no S3 cache is configured and shows no table.
- New `src/cache/DeleteCacheObjectDialog.tsx` on `layout/ConfirmDialog.tsx`: the object name, its size, "cannot be undone" and "a later session with this name starts empty"; the confirm button stays disabled until the typed text equals the object name; confirm calls `requestCacheDeletion(object, etag)` and the request is polled every 5 s with `usePoll` (`triggers/usePoll.ts`) until `done`, `refused` or `failed`, showing the outcome and its reason; an api 409 `in_use` shows as refused with its message; on `done` the list reloads.
- `formatBytes` moves from `src/sessions/DiscardSessionDialog.tsx` to the new `src/layout/formatBytes.ts`, imported by both; no private copy remains.
- One object at a time: no bulk or multi-select.

Tests no longer accurate because each pins the exact orchestrator menu list, which now ends with `cache`: src/backends/registry.test.ts `default_orchestrator_has_sessions_at_10_and_presets_at_40` (renamed `default_orchestrator_has_sessions_10_presets_40_cache_50`), `webhooks_sits_between_sessions_and_presets_only_when_configured`, `schedules order`, `lists Chats only with the matrix backend`, `filters_by_configured_backends`, `orders_by_order_then_label` and `warns_once_for_unregistered_id`.

## Acceptance conditions

- AC1: the default orchestrator menu is sessions 10, presets 40, cache 50 [evidence: test:src/backends/registry.test.ts::default_orchestrator_has_sessions_10_presets_40_cache_50]
- AC2: the cache entry is labelled Cache, belongs to the orchestrator backend and renders CachePage with onBack [evidence: test:src/backends/registry.test.ts::cache_entry_renders_cache_page]
- AC3: the page lists each object with object name, kind, class with its slugs, preset name or copied-by count, size and last modified [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "lists objects with kind class size and age"]
- AC4: class chips and the name search reload the list with class and q [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "filters by class and searches by name"]
- AC5: Load more fetches the next page with after set to next_after [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "loads the next page"]
- AC6: the quota gauge shows bytes and objects against the quota when set and is absent when the quota is null; listed <age> is shown [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "shows the quota gauge only with a quota"]
- AC7: Refresh requests a listing, polls it to done and reloads the list [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "refresh requests a listing and reloads when done"]
- AC8: Delete is disabled for in_use objects with a tooltip naming the sessions [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "delete is disabled for objects in use"]
- AC9: the confirm dialog shows the object name, size, cannot be undone and a later session with this name starts empty, and confirm stays disabled until the typed name matches [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "confirm requires the typed object name and warns"]
- AC10: after confirm the request is polled every 5 s to done, refused or failed and the outcome with its reason is shown [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "polls the delete request to its outcome"]
- AC11: an api 409 in_use on confirm shows as refused with its message [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "shows refused when the api answers in use"]
- AC12: with available false the page says no S3 cache is configured and shows no table [evidence: command:npx vitest run src/cache/CachePage.test.tsx -t "says no S3 cache is configured"]
- AC13: formatBytes is shared and formats as before [evidence: test:src/layout/formatBytes.test.ts::formats_bytes_to_one_decimal]
- AC14: the discard dialog has no private formatBytes and its suite still passes [evidence: command:! grep -n "function formatBytes" src/sessions/DiscardSessionDialog.tsx && npx vitest run src/sessions/DiscardSessionDialog.test.tsx]
- AC15: no bulk or multi-select in the section [evidence: command:! grep -rniE "checkbox|multi-?select|selectAll" src/cache]
- AC16: the section, registry, design-rule and nomenclature suites, the type check of the build and lint pass [evidence: command:npx vitest run src/cache src/backends/registry.test.ts src/layout/formatBytes.test.ts src/layout/designRules.test.ts src/nomenclature.test.ts && npm run build && npm run lint]

## Files

- `src/backends/registry.ts`
- `src/backends/registry.test.ts`
- `src/cache/CachePage.tsx`
- `src/cache/DeleteCacheObjectDialog.tsx`
- `src/cache/CachePage.test.tsx`
- `src/layout/formatBytes.ts`
- `src/layout/formatBytes.test.ts`
- `src/sessions/DiscardSessionDialog.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
