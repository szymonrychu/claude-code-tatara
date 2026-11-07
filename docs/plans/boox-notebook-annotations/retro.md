# Retro: boox-notebook-annotations (T-46, P2-P7)

## Delivered vs scope
- Connector v2.1.0 (PR #14, tasks 2.1-2.8) and helmfile pin (PR #117, apply and rollout checked, migration 0006 applied). App v0.15.0 (4.x text rows, revert), v0.16.0 (5.1-5.4 edit ops), v0.17.0 (5.5-5.6 freehand loops/arrows), v0.17.1 (live ink fix), v0.18.0 (6.1-6.6 image regions, inline images, share zip). All on origin/main with tags.
- OQ1-OQ7 Recommended options were built (OQ3 and OQ5 isolated behind markers, OQ7 markers removed after approval).
- Under-delivery / unverified: 3.3 preset push was not done by P3 (admin token 401); the user's session patched it, so close but not verified by an agent. 7.2 device round, eval cases 12-15 run, and 7.1 workbench pointer bumps were not evidenced in the reports.
- Over-delivery: none of substance. Live ink fix (0.17.1) and the strip-never-auto-hides change were regression work outside the plan.

## Accepted limits
- Dropped: bitmap recycling (GC handles it), base_version removal (needed), unrelated test gaps, greedy arrow pick, overlapping notes. Acceptable, each reasoned.
- Pending-mark release: a second pending upload with the same base was a risk, later fixed by linking sketch ids. Poll give-up still releases all marks (acceptable).
- P4 persisted notebooks without TextRun.source are unsupported (P4 unshipped, no back-compat rule): acceptable.
- Offline-frozen versions now re-paginate via an images-missing marker: acceptable.

## What came up
- Harbor CI secrets blocked the first 2.1.0 build until fixed.
- Critical: base_version after a layout-less version would 409 forever; fixed by sending only runs present in the latest stored version's layout.
- Pending marks got stuck (ops and segments never cleared); needed baseVersion stamping and upload linking.
- Stacked PRs (P4, P5a, P5b, P6) needed rebuilds after each squash merge.
- Gradle allows one build at a time; parallel worktrees needed a shared ANDROID_HOME.
- public-check fails on commit identity in old branches; commits re-authored to the noreply identity.
- Live ink regression reappeared: the SDK resets the firmware pen on every raw-drawing open, so the brush must be reapplied after each open.
- ensure_preset needs an orchestrator admin token the agent session lacks.

## Overlooked in discovery and planning
- No Android SDK / gradle concurrency and worktree setup step in the plan.
- The base_version rule was specified against layout-bearing versions only.
- The pending-state lifecycle (release conditions) was not designed up front.
- Live ink behaviour on the device SDK was not in the research despite the earlier regressions.
- Privileged steps (CI secrets, admin token) were not listed as prerequisites.
- Stacked-PR strategy was not decided.

## Recommendations
1. Add a prerequisites task to every plan listing tokens, CI secrets and SDK paths, verified before dispatch.
2. Add a live-ink regression test or mandatory device checklist item for any change touching raw drawing open/enable.
3. Specify state-machine lifecycles (pending, released, failed) in the plan, with an invariant test list.
4. Merge stacked PRs bottom-up with one rebase script, or use one branch per phase off main.
5. Fix public-check to inspect only branch-local commits, and set the noreply identity at worktree creation.
6. Give agents a documented path to run ensure_preset (scoped admin token) or make it a user task upfront.
7. Close 7.1-7.2: verify pointer bumps, run eval cases 12-15 and the device checklist before marking T-46 done.
