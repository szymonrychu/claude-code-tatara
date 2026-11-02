# session-history: retro

Final review, 2026-11-02, against `plan.md` (agreed scope, answers Q1-Q6), `implementation.md`,
the SDD ledger (`.superpowers/sdd/implementation-session-history/progress.md`, rulings S-R1 to
S-R11, `preflight.md`) and the merged code: agents-history v0.1.0 and v0.1.1,
agents-orchestrator v3.5.0 (#58), any-mcp-tatara-plugins v0.11.0 (#11), agents-web v0.15.0 to
v0.15.2 (#41), agents-helmfile #77 (merged, applied) and the open #80 (H2) and #81 (H3).
Full findings: `.superpowers/sdd/implementation-session-history/final-review.md`.

## Verdict

Complete in code against the agreed scope, nothing substantive over-delivered. Two Important
defects in the integrated system, both outside what any single task review could see. Live
delivery waits on #80 and #81 (infra hive).

| User requirement | Delivered | Where |
|---|---|---|
| Searchable history of discarded sessions (Q1, Q2) | yes: full JSONL export stored per session, re-delivery replaces | agents-history ingest; orchestrator pre-discard hook fan-out |
| No backfill (Q3) | respected | - |
| Substring and regex search, date, preset, session filters (Q4) | yes, pg_trgm, statement timeout 8 s | agents-history `db/read.py` |
| Retention editable in the UI, default 90 days (Q5) | yes, sweep with advisory lock | agents-history `sweep.py`, web `RetentionCard` |
| Superleader read and search only, delete user-only (Q6) | yes, pinned at service listener, relay and tool list | agents-history `api/app.py`, orchestrator `admin_relay.py`, plugins `admin.py` |
| Web History page with chat view, records, delete | yes | agents-web `src/history/*` |
| Deployed | history service yes (#77); orchestrator wiring and web pin open (#80, #81) | agents-helmfile |

## Findings (summary)

Important:
1. The superleader's `history_search` loses `next_before_id` on a full search page: the plugin
   puts the cursor last, the default page is 50, and any-mcp cuts tool output at 40000 chars
   (and the body at 160 KB). A 50-hit page with snippets is about 60k chars.
2. A slow or hung agents-history stalls the whole orchestrator reconciler for up to 600 s per
   deleting session per pass: sessions reconcile sequentially, the hook is now always on, the
   timeout went from 120 s to 600 s and the HTTP client has no idle timeout.

Minor: the trigram EXPLAIN test does not explain the real search query; the orchestrator's
vendored history spec is stale (int agent id); the web page shows nothing until Search; tabs
unmount and refetch; the relay filters after paging instead of upstream; the plugins fixture is
stitched from two branches.

## What came up during implementation

- Preflight found four behaviour gaps before any code: relay paging after filtering (P-07),
  helmfile staging across three leader stops (P-22), "stop at the first failing hook" contra the
  spec (T-O1), and a wrong record count (T-A3). All were ruled up front (S-R1 to S-R4), and none
  caused rework later. The preflight paid for itself.
- The new repo could not merge for about three hours: CI Harbor push secrets had to be requested
  from the infra hive (S-R6, mx-99 #697, landed with #712).
- Real data broke assumptions the plan did not state. NUL and lone surrogates in export strings
  needed scrubbing before jsonb (S-R7, A2/A3). Concurrent re-delivery of one session needed an
  advisory lock (A3 to A4). Python `re` for snippets broke the 8 s search bound (25 s measured),
  so snippet positions moved into Postgres (A4 fix round).
- The agent id type was wrong. The plan described `agents [{id, ordinal, pod_name}]` without
  types; agents-history was built and released with integer ids, and only the web task (W3)
  noticed that the orchestrator exports uuids. That cost a hotfix release (v0.1.1), a web
  re-vendor, and a stale orchestrator fixture that is still open.
- Paging needed three layers to agree. The relay ruling (S-R1) added `X-Next-Before-Id`. The
  plugin had to read a response header and wrap the page (P1). The web first ended paging only
  on an empty page and needed a fix round (W2). Each layer was tested on its own; the any-mcp
  output budget between the plugin and the superleader was never tested, which is how
  Important 1 slipped through.
- Version numbers moved again: orchestrator planned 3.4.0, shipped 3.5.0; plugins planned 0.7.0
  then 0.8.0 (S-R5), shipped 0.11.0; web planned 0.14.0, shipped 0.15.0, pinned 0.15.2 (S-R10).
  Cross-epic coupling forced S-R11 (web 0.16.0 needs orchestrator 3.6.0, so H3 stays on 0.15.2).
- The helmfile add-a-component guards were not in the plan. The H1 review caught that the
  semver-pin guard and `check-pins` did not cover agents-history (fix round 1). After #77 merged,
  `test_values_dir_moved` still left helmfile main red; another hive fixed it in #79, and H2/H3
  had to wait for it.
- Other work was folded in on request: the usage quota default 95 (S-R9, user #888) rode along
  in H2 because it touches the same values file.
- Leadership changed mid-run (epoch 10, tatara-1). The ledger carried the state; no task was
  redone.
- Postgres tests ran locally this time (local PG), so DB failures surfaced in the task loop and
  not first in PR CI. This is an improvement on the previous epic.

## What was overlooked in discovery and planning

- No real export sample was taken. The plan cited the export code but not a real export line,
  so field types (uuid agent ids) and content hazards (NUL, surrogates, huge tool results) were
  found during implementation and one of them only after release.
- The MCP tool output budget was not considered. Discovery mapped the relay (10 s, 256 KiB
  request cap) but not any-mcp's response shaping (40000 chars, 160 KB read cap). The page size
  and cursor placement were therefore chosen blind.
- The reconciler's execution model was not looked at. Risk 1 covered "an outage blocks
  discards" but not "a slow hook blocks every other session", which becomes reachable once the
  hook is always on and its timeout is raised to 600 s.
- The relay guard design reused "filter the list answer", which does not fit a paged upstream.
  Preflight caught it (P-07), but an upstream preset-set filter was never weighed against the
  header-cursor workaround.
- Search performance was planned as "an EXPLAIN test" on a toy statement. The real statement
  shape (EXISTS per session under an id-ordered LIMIT, plus a per-session hit count) was not
  checked against the index.
- Prerequisites of a new component were not listed: CI registry secrets for a new repo, and the
  helmfile guards (semver pins, check-pins, values-dir test, secrets bootstrap).
- Operability: there is no alert for discards stuck behind the hook, and no alert on the 10Gi
  history volume filling. When ingest fails, every discard waits forever by design.
- Versions were fixed in the plan again, though the previous retro said to reserve them at merge.

## Recommendations

1. Fix the superleader search cursor in the plugins:
   - Emit `next_before_id` first.
   - Give `history_search` its own default `limit` of 20, capped at about 50.
   - Give `history_records` a default of 50.
   - Add a test that drives a realistic 50-row, 3-snippet page through any-mcp `shape_default`.
   This is one plugin patch release plus an `ORCH_ANY_MCP_PLUGINS_REF` bump.
2. Bound the discard hook's effect on the reconciler:
   - Add an idle read timeout to the hook's HTTP client (for example `connect=10, read=120`) and
     keep 600 s only as the total.
   - Deliver hooks outside the sequential reconcile pass (a per-session task with its result in
     status).
   - Alert on `discard_hook_failures > 3`, or on a session in `deleting` for more than 30 min.
   Decide before #80 applies, or right after it with the alert in place.
3. Run the open live checks once #80 and #81 apply:
   - Discard a throwaway session and confirm it appears in history.
   - Confirm `history_search` with `q` finds it, a hidden-preset session stays 404, and a
     DELETE through the relay returns 405.
   - Confirm the web page lists, searches, opens the chat, deletes and edits retention.
   - After a few weeks of data, run `EXPLAIN ANALYZE` of the real search statement on live data.
4. Put a real orchestrator export (sanitised) into agents-history's test fixtures as the
   contract sample. Re-vendor the history spec into the orchestrator from v0.1.1 (fake and
   upstream fixture), as the ledger planned for hive-self-close PR prep.
5. Write an "add a component" checklist for helmfile and new repos:
   - CI registry secrets requested when the repo is created.
   - Semver-pin guard, `check-pins` and the values-dir test updated in the first helmfile PR.
   - `bootstrap-secrets.sh` entries.
   Put it in `workbench:component-add` or the helmfile AGENTS.md.
6. Process:
   - In discovery, read the consumer's output limits for any new MCP tool, and the execution
     model of any loop that gains always-on work.
   - Sample real data for every cross-repo payload.
   - Reserve versions at merge, not in the plan (repeat from the claude-usage-monitor retro).
7. Clear the web minors in the next agents-web touch:
   - Load the newest sessions when the History page opens.
   - Keep the Chat and Records tabs mounted.
