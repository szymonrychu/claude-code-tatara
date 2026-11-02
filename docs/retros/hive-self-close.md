# hive-self-close: retro

Final review, 2026-11-02, against `plan.md` (agreed scope, answers Q1-Q5 accepted as HS-D1),
`implementation.md`, the SDD ledger (`.superpowers/sdd/implementation-hive-self-close/progress.md`,
rulings H-R1 to H-R9, `preflight.md`, `merge-pr-report.md`) and agents-orchestrator PR #62 (head
cd82a51, open). The plugins side shipped earlier: any-mcp-tatara-plugins v0.10.0 (#10, the
`self_close` tool), pinned now at v0.11.1. The web (W1, W2) is reviewed on its own branch, and
helmfile (H1, H2) has not started.
Full findings: `.superpowers/sdd/implementation-hive-self-close/final-review.md`.

## Verdict

Group O is complete in code against the agreed scope. Nothing substantive was over-delivered, and
there are no Critical or Important defects. There are five Minor findings. CI lint, chart and
GitGuardian pass; test and e2e were still running at review time.

| User requirement | Delivered | Where |
|---|---|---|
| Leader closes its session when idle, with a grace (Q1) | yes, `LEAST` threshold inside the existing idle predicate, 30 s default | `db/sessions.py`, `api/autoclose.py`, `settings.py` |
| Stored request and reason, shown and exported (Q2) | yes, migration 0026, `SessionView`, discard-hook `session` record | `0026_session_close_request.sql`, `api/sessions.py`, `db/export.py` |
| Leader only, alone agent counts (Q3) | yes | `api/agent.py` `close` via `_leads` |
| Superleader refused, tool not offered (Q4) | yes, 422 `own_session`, allow list without `self_close` | `api/agent.py`, `k8s/on_start.py` |
| User cancel (Q5) | API yes; web button in agents-web W2 | `DELETE /api/v1/sessions/{id}/close` |
| Deployed | no: helmfile still pins `ORCH_ANY_MCP_PLUGINS_REF: v0.4.0` and the old orchestrator | H1, H2 pending |

## Findings (summary)

Minor:
1. `ORCH_CLOSE_GRACE_SECONDS=0` is allowed. With grace 0, a session can flip in the short gap
   between a message going `sent` and the ingester recording the turn start, and that kills the
   turn. The default of 30 s is safe.
2. No migration test pins 0026 applying to a database already at 0027, which is the live case.
3. The `db/export.py` module docstring omits the two new `session` record fields.
4. The merge commit f6ff804 carries non-merge content: a plugins re-pin and a spec re-vendor.
5. Commit 01337f4 has the subject type `docs,test`, which is not a single conventional type.

PR #60 (discard-hook timeout) merges clean with this branch. The pure suites pass on the merged
tree, and the two changes do not clash in meaning.

## What came up during implementation

- Preflight paid off again. It found 14 plan gaps before any code was written:
  - the 14 hard-coded migration version lists (HS-1);
  - a log line that `discard_idle`'s return type could not support (HS-3);
  - undefined test helpers (HS-4);
  - `TAIL_TOOLS` shared with the superleader expectations (HS-7);
  - an O5/O6 ordering that would have left main red until the plugins tag existed (HS-8);
  - a README heading form the drift test rejects (HS-6);
  - a web schema synced from an unmerged sha (HS-12);
  - a missing helmfile test file (HS-14).

  All of these were ruled up front, and none caused rework later.
- The plugin version moved four times. The plan said v0.7.0. H-R7 made it "next free" (0.10.0,
  because tatara-2 took 0.9.0). H-R8 moved it to v0.11.0 once session-history merged its history
  tools. A final hotfix made it v0.11.1. Every move touched five places: `pyproject.toml`,
  `uv.lock`, the settings default, README and `test_settings`.
- The migration number was contested across three epics: cache-retention took 0025, taskboard
  took 0027 and tatara-2 holds 0028. The set-based migrator meant nothing was renumbered (#842,
  H-R9), but every sibling merge rewrote the version lists in `tests/test_migrations.py`.
- Two merges of main were needed (109832d, f6ff804). The second carried real content: the
  re-pin, the agents-history spec re-vendor, and the export SELECT union with session-history's
  provenance columns (X-01). The merge-main agent was stopped mid-way and its follow-up was
  re-dispatched twice, the second time for the v0.11.1 hotfix.
- Local Postgres replaced testcontainers in the task loop (a private PG16 per task), so every DB
  test ran before push. This repeated session-history's improvement. The only recurring red was
  `test_lightkube_default_client_uses_env_config`, which fails in any agent pod because of the
  in-cluster `KUBERNETES_SERVICE_*` environment. Every report had to explain it again.
- The cancel-versus-flip race test first relied on lock arrival order (`sleep(0.3)`). It was made
  deterministic with a `pg_stat_activity` lock-waiter probe (54df870), which other lock-race
  tests can reuse.
- Process friction:
  - One commit used `--no-verify` because "gitleaks is not installed". gitleaks and pre-commit
    are in fact on PATH through `/opt/mise/shims`.
  - A stash made for a quick check (26dc3a7) is still on the shared stash stack, because the
    guard hook blocks `stash drop`.

## What was overlooked in discovery and planning

- Plugin versions were fixed in the plan (v0.7.0). This is the third retro to say versions
  should be reserved at merge time.
- Cross-epic ordering was not modelled. The plan knew about cache-retention, but not about
  session-history (which changed the export SELECT, the plugins version and the vendored spec)
  or taskboard (0027). The X-01 union and the H-R8 re-pin were found at merge time.
- The predicate's blind spot for a `sent` message without a recorded turn start was not
  examined. Discovery reused the idle-discard predicate as proven, but that predicate is only
  safe because its minimum is 60 s. The new grace setting allows 0.
- The deploy coupling was stated, but not as a check: the orchestrator's settings default is not
  what pods install. The helmfile value is (`v0.4.0` today). If H1 misses it, `self_close` is
  allowed but absent, and that fails silently.
- No "closing but blocked" state was considered. A session with a stuck or unready member never
  becomes idle, so the pending close is shown forever with no hint why.

## Recommendations

1. Before merging #62, raise the lower bound of `ORCH_CLOSE_GRACE_SECONDS` to at least 10.
   Alternatively, count a `sent` message without a completed turn as activity in
   `_IDLE_PREDICATE`. Add one test for the grace-0 gap. This is one small commit.
2. Make H1 move `ORCH_ANY_MCP_PLUGINS_REF` to v0.11.1 together with the orchestrator image, and
   add a helmfile test that the plugins ref equals the orchestrator's settings default for the
   pinned release. Then run the live check from plan section 5 (close fires 30 to 40 s after the
   turn ends; cancel from the UI keeps the session).
3. Add the missing migration test "0026 applies after a database already at 0027", and fix the
   `db/export.py` docstring. Both can ride in the commit of recommendation 1.
4. Make `test_lightkube_default_client_uses_env_config` clear `KUBERNETES_SERVICE_HOST` and
   `KUBERNETES_SERVICE_PORT` with monkeypatch, so the full suite is green in agent pods and
   reports stop carrying the same "known failure" line.
5. Reduce version-pin churn:
   - Reserve versions at merge (repeat).
   - Keep the plugins pin in one place that the tests, README and `uv.lock` check against.
   - Have the plugins release bump `orchestration/orchestrator/pyproject.toml`. v0.11.1 still
     says 0.11.0 in `uv.lock`.
6. Process:
   - Never put content changes in a merge commit; commit them separately after the merge.
   - Use one conventional type per subject.
   - Find tools through `mise which` before using `--no-verify`.
   - Drop scratch stashes by SHA, or give the guard hook an allow rule for `stash drop` of
     entries the session created.
   - Clear the leftover stash 26dc3a7.
7. Web follow-up (agents-web, next touch): when a close is pending but an agent is not idle, say
   why ("waiting for agent N to become idle") in the closing banner.
