# agent-preset-editing step 1: retro

This is the final review on 2026-11-03 of agents-orchestrator PR #61 (branch `session-orchestration-mcp`, head 01dbec0) and any-mcp-tatara-plugins PR #14 (head 72e5666). Inputs:

- the spec `docs/future/agent-preset-editing.md` (section 4, step 1);
- the plan `docs/plans/agent-preset-editing/implementation.md`;
- the ledger `.superpowers/sdd/implementation-agent-preset-editing/progress.md` (the T-4 answers and rulings P-R1 to P-R4).

Full findings: `.superpowers/sdd/implementation-agent-preset-editing/final-review.md`.

## Verdict

At review time the branch was ready to merge, with five Minor findings and no blocker. The review
listed four steps for before the merge:

- merge `origin/main` (#65);
- regenerate `openapi.json`;
- wait for CI `test` and `e2e` to pass;
- release under the next free minor.

## State (updated 2026-11-03)

Step 1 is merged, released and live.

- **Merged and released.**
  - #61 merged as 4d0f6de and released agents-orchestrator v3.10.0.
  - any-mcp-tatara-plugins #14 released v0.12.0, which carries the `preset_patch` tool.
- **The follow-up, #67.** It added the delete guard (next section) and merged as d21da00.
  - It released v4.0.1: hive-inactivity-limits #66 had made v4.0.0 in the meantime.
- **Live through helmfile.**
  - #89 (df2c9b6) pinned orchestrator 3.10.0 and plugins v0.12.0.
  - #90 (508a2e1) pinned orchestrator 4.0.1, together with hive-inactivity-limits.
- **Superleader live check.** It ran `preset_patch` on a manageable test preset and passed.
- **Residuals.** Of the out-of-scope gaps listed under "What was overlooked", the admin DELETE of
  a privileged preset is now closed by #67. The other two are still open:
  - cross-session messaging to a privileged leader;
  - the agent init-scripts write-back.

## Follow-up PR #67: superleader DELETE of a privileged preset

Reviewed with `git diff c3ae718 d21da00` in agents-orchestrator; full notes are in
`.superpowers/sdd/implementation-hive-inactivity-limits/final-review-wh.md`. Verdict: correct and
consistent with the #61 guard. No findings above Minor.

- **What it does.**
  - `DELETE /agent/v1/admin/presets/{ref}` now calls `remove(..., superleader=True)`.
  - On a preset with `kube_access`, `session_messaging` or `docker` on, it answers 403
    `privileged_target`, with `error.fields` set to the sorted flags that are on. The refusal is
    audited.
  - `privileged()` uses the same `PRIVILEGED` set as the PUT and PATCH guard.
- **Lock discipline as #61 asked.**
  - The check is a `recheck(spec)` callback that `db/presets.delete` runs on the row it reads
    under `FOR UPDATE`.
  - So the check runs before the delete and before any Secret cleanup, and a human turning a flag
    on concurrently is still refused.
  - A TOCTOU test flips `kube_access` between the route's read and the delete.
- **What stays unchanged.**
  - The main-port delete and a non-privileged admin delete are unchanged, and tests pin both.
  - README and MEMORY.md were updated; `openapi.json` is unchanged.
- **Minor residual.** `_manageable_preset` still checks `superleader_manageable` before the lock.
  A human who hides the preset between the lookup and the delete does not stop the delete. This is
  the same residual as recommendation 1, and the risk is low: only a non-privileged preset can be
  deleted that way.
- **Minor ordering.** On a privileged default preset, the 403 now wins over 409
  `preset_default`. Harmless.

## What came up during implementation

1. **We took over an in-flight branch from another hive.** Two of its commits reversed security decisions, and neither cited a user ruling:
   - `bc370b7` reverted the guard on privileged presets;
   - `fbed869` dropped decision 7b.

   Each needed a leader ruling (P-R3) and its own fix round (O1-fix, O3). The gap audit in O1 caught both. Without it, PR #61 would have shipped a path to code execution as cluster-admin: a superleader editing the init scripts or hooks of a `kube_access` preset.
2. **The guard grew beyond spec section 4.** Read literally, T-4 Q1 ("minus sensitive security wise options") required a guard on the privileged stored preset, a guard on chat routing rules and refusals in the relay. None of these is in the spec's step 1 table. The privileged-target rule is now the largest part of the security surface.
3. **TOCTOU had to be fixed three times on the same route:**
   - the privileged flag on the secret route (e476e91);
   - the stale `found.spec` protected check (O4 review Minor1);
   - the declared-entry check (01dbec0).

   All three come from one pattern: the route decides on a row it read before the lock. The fix that finally holds puts every decision in a `recheck` callback under `FOR UPDATE`. One residual remains: `superleader_manageable` is still not part of that recheck.
4. **The lock order changed.** `set_secret` now takes the preset row lock before the advisory lock. That order is consistent everywhere, but it is a cross-cutting change that went in as part of a "small" TOCTOU fix.
5. **Version and migration numbers drifted while the work was in flight.**
   - The plan expected v3.8.0. v3.8.0 and v3.8.1 were taken by other merges, and #65 will take v3.9.0.
   - hive-inactivity-limits collided on migration 0029 with #65.

   Merge-time numbering (P0, P-R2) worked, but only because each merge re-checked.

## What was overlooked in discovery and planning

1. **The ownership history of the security decisions in PR #61.** The plan treated #61 as "CLEAN, CI green" and listed only `fbed869` as a known deviation. It did not diff the commit history for reverts (`bc370b7`). A takeover plan should list every commit that loosens a guard and ask for its ruling up front.
2. **The privileged-preset threat model.** The spec's human-only table guards the grant fields themselves. It did not consider an agent editing the other fields (init scripts, hooks, MCP, env, secrets) of a preset that a human has already granted. On such a preset, those fields are an escalation path. This should have been a spec section, not a review finding.
3. **TOCTOU between the route's read and the write.** The plan's review focus covered the compare-and-swap on PUT and PATCH but not the secret route, which writes outside `db/presets.update`. Every write route should list "which decisions are taken on which read, and is that read under the lock".
4. **T-4 answers that diverge from the spec.**
   - Q1: a regular hive leader edits its own preset.
   - Q2 A: no gate.

   The spec's step 4 (decision 4b, a human-only `leader_editable` switch) does not match these answers. Step 1 does not touch it, but the step-4 plan must reconcile the two before any design work.
5. **Out-of-scope gaps that were not scheduled at review time:**
   - admin DELETE of a privileged preset answers 204 (closed afterwards by #67, v4.0.1);
   - cross-session messaging to a privileged leader is not filtered;
   - the agent init-scripts write-back has no privileged check (ledger residual b).

   They were noted and not scheduled.

## Recommendations

1. **Put every authz decision of a write route in one recheck under the row lock**, including `superleader_manageable`. Add a test helper that flips the row from a second connection between the read and the write, for each admin write route. Today `test_secret_route_*_between_check_and_write` does this for two flags. Generalise it the way `GUARDED_PRESET_WRITES` is generalised.
2. **Takeover checklist.** Before adopting another hive's branch, list every commit that relaxes a guard or reverts a fix (`git log -G` on the policy modules, plus `Revert` subjects). Get a user or leader ruling for each before the gap audit, not after the first review.
3. **Write the privileged-preset rule into the spec** (section 3.1, a "privileged target" subsection) together with the T-4 Q1 answer. Have the step-3, step-4 and step-6 plans (revisions, leader self-edit, webhook fire-time check) derive their guards from it, so later steps do not rediscover it in review.
4. **Fix the Minor findings in one small follow-up after the merge:**
   - the stale `MEMORY.md:6`;
   - the empty PATCH name (`api/presets.py:329`);
   - a main-port twin of the 01dbec0 race test;
   - the manageable recheck.
5. **Propose versions from `scripts/next_version.py` on the merge with the current main**, not from the plan. Main may hold untagged feat commits (1561a68 does today).
