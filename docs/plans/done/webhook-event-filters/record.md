# webhook event filters record

## Asked

Per-endpoint allowlist/denylist filters for every webhook type (grafana-alert, github-issue, github-pr, gitlab-issue, gitlab-mr): allow and deny rules over normalized fields (author, repo, labels, title, PR/MR branches and more), `equals` or RE2 `regex`. A delivery that fails is accepted (202) and stored `ignored` with a reason instead of starting an agent. Managed through the endpoints API and the agents-web Webhooks UI, deployed through agents-helmfile. `WEBHOOK_ALLOWED_AUTHORS` retired.

## Shipped

All 16 tasks done. Epic review verdict: pass (2026-10-25); scope audit CLEAN (every type and D3 field covered across API, UI create/edit, preview, deploy, smoke; no duplicates). Whole-diff review: 1 medium (stale preview verdict), security review: 1 medium (filter evaluation on the event loop, no total work cap); both fixed by phase 5 tasks and reviewed PASS.

Merged:
- agents-webhook PR #5 (f63a19f) and #6 (206cf8e).
- agents-web PR #7 (e92326d) and #8 (bc47dee).
- agents-helmfile PR #22 (74cc577).

Live (agents namespace): agents-webhook 0.1.0-main.206cf8e (rev 4) and agents-web 0.1.0-main.bc47dee (rev 6). Post-apply diff: "No affected releases". Smoke: "smoke: OK" including the filter checks, exit 0 (logs: .logs/webhook-filters-postdiff2.log, .logs/webhook-filters-smoke2.log, .logs/webhook-filters-smoke2.rc).

Suites read: agents-helmfile `mise run test` 122 passed, lint clean; agents-webhook PR #6 CI green including e2e; agents-web PR #8 CI green. I ran no tests myself.

## Tasks

Status and verified head are from the task files (all `done`, all with a verified head). Review rounds and per-task verification tails were not in the files I was given: "unknown". Points are planned/actual. The plan-execute return value was not provided, so the independent verifier head, red evidence, declined, cannotVerify and forwardMerged entries could not be read: "unknown"; the head shown is the task file's verified_head.

| Task | Status | Verified head | Rounds | Verification tail |
|---|---|---|---|---|
| api-endpoint-filters | done | 3685ee0 | unknown | unknown (5/5) |
| apply-smoke-webhook-filters | done | a8686f7 | unknown | unknown (2/2) |
| deploy-pin-webhook-filters | done | 5ee3612 | unknown | unknown (2/2) |
| e2e-endpoint-filters | done | 2616d24 | unknown | unknown (3/3) |
| endpoint-filters-storage | done | 54502c4 | unknown | unknown (3/3) |
| filter-rules-engine | done | 07aba14 | unknown | unknown (5/5) |
| filters-off-event-loop | done | 9f048aa | unknown | unknown (3/3) |
| ingest-applies-filters | done | 5afc237 | unknown | unknown (3/3) |
| normalize-branch-fields | done | efacbaa | unknown | unknown (2/2) |
| retire-allowed-authors | done | d11f887 | unknown | unknown (2/2) |
| smoke-webhook-filters | done | 76b75ff | unknown | unknown (2/2) |
| web-create-endpoint-filters | done | 1ac0880 | unknown | unknown (3/3) |
| web-edit-endpoint-filters | done | 5f9dc1e | unknown | unknown (3/3) |
| web-filters-editor | done | 7c01ade | unknown | unknown (3/3) |
| web-preview-stale-on-filter | done | da936ab | unknown | unknown (1/1) |
| web-vendor-filters-api | done | 20f1694 | unknown | unknown (2/2) |
Approvals ledger: the epic dir has no approvals.json, so no ledger rows; the gate approval is recorded in the root MEMORY.md (2026-10-25): "unknown" per entry.

## Rulings

- Gate: Q1-Q3 at the recommended answers (user: 'Go for webhook filter'): retire WEBHOOK_ALLOWED_AUTHORS and keep WEBHOOK_BOT_LOGINS; built-in ignore rules run before filters; allow rules AND, values OR. The live apply and the additive filters column were approved at the gate. Cost if wrong: a removed env var is inert (`extra="ignore"`); an author allowlist moves to an endpoint allow rule.
- Regex: oversized text fails closed in both directions (a deny rule treats it as a match, an allow rule as a miss), so truncation never lets an event through. Cost if wrong: an oversized event that should pass is ignored with filter_error until the bound is raised.
- Preview: the preview verdict mirrors ingest (built-in rules first, then filters, fail closed to `filter_error`). Cost if wrong: the preview and live ingest would disagree on an example.
- Field list: the FiltersEditor is never mounted before /meta loads, so the UI has no copy of the field catalogue and never shows a wrong field set. Cost if wrong: the dialog shows nothing until /meta answers.
- Phase 5 fixes: filters-off-event-loop (to_thread, 200-value total budget MAX_TOTAL_VALUES, 100-item list cap MAX_LIST_ITEMS, fail closed) and web-preview-stale-on-filter (the stale preview cleared on a filter edit). Cost if wrong: ingest stalls under a large rule set, or the user creates an endpoint believing a stale verdict.
- Superrepo main is not pushed; pushing stays with the user.

## Discovered and blocked

- Not verifiable by the epic reviewer: live apply and smoke result, browser rendering (review was read-only); settled by the live post-diff and smoke above.
- The pre-apply diff log (.logs/webhook-filters-prediff.log) ends "[diff] ERROR task failed" because `mise run diff` exits non-zero when there are changes ("Identified at least one change"); the diff content was as expected per agents-helmfile MEMORY.md.
- The `.venv` editable install of agents_webhook still points at the removed worktree path (warning printed by ticket.py): the user or supervisor can reinstall.
- Nothing else open.

## Not pushed

The superrepo submodule pins and ticket moves are committed on main; main is not pushed; pushing the superrepo main stays with the user. Submodule PRs are all merged.

## Lessons routed to

- Preview and ingest could diverge: a test that runs the same examples through the preview endpoint and ingest and asserts equal verdicts (partly covered by the e2e and shared `verdict` function).
- Filter evaluation had no total work cap until review: a unit test asserting evaluation fails closed over MAX_TOTAL_VALUES and MAX_LIST_ITEMS (done in filters-off-event-loop).
- A UI preview verdict stayed after an input edit: a component test per dialog asserting every editable input clears the verdict (done for filters in web-preview-stale-on-filter).
- `mise run diff` returns non-zero on expected changes, which logs read as an error: a judgement call for the apply skill note, not a mechanical check.
