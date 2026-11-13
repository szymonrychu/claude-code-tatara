# superleader-access: retro

## Verdict

Slice 3 (S-31, tools T-169..T-184) is implemented, merged and live-smoked on orchestrator 7.20.1, with one gap:
`project_update` archiving `default` (expected 422) was not tried. The deploy needed another hive because
`mise run apply` is not runnable from an agent pod.

## Slice 3 (2026-11-13)

Scope: S-31, tools T-169..T-184

What came up during implementation:
- Release numbering moved under the slice: the plan claimed orchestrator 7.18.0 and plugins v0.42.0; other
  hives tagged first, so the claims became 7.21.0 and v0.47.0. The orchestrator auto-releases the next free
  version at merge, and it produced 7.20.1 (a patch) where 7.21.0 was expected, so a claim in the room is not
  binding on the version CI picks. The plugin OpenAPI fixture had to be re-vendored from the final tag.
- The preflight scan found 6 conflicts between the plan text and the code (e.g. no Sess.spec fixture, CopyPreset
  has no false field, file locks keyed by path); rulings were recorded per conflict. Cheap and effective.
- A review found a real defect before merge: gate_scale_up takes its own pool connection, so scaling while
  holding one nested two connections. Fixed by gating before taking the connection, with a nesting-spy test.
- Message cancel and lock reassign through a slug needed the session_id predicate in the guarded UPDATE
  (IDOR); tested both ways.
- Deploy did not complete: `mise run apply` from an agent pod fails its pre-apply step because the helm
  plugins (helm-secrets) are not installed in the pod, and installing them was denied by the auto-mode
  classifier ([Code from External]). Another hive had to apply. The classifier also denies apply commands
  with output redirection (`| tee`, `>`, `2>&1`); run the apply bare, standalone, without `cd &&` chaining.
- The helmfile apply window is shared by several hives (mindmaps, matrix-mentions, spec-auto-approve), each
  waiting hours; the cluster was CPU-requests-exhausted (95-99%) which risks a Pending rolling update.

What was overlooked in discovery and planning:
- That `mise run apply` is not runnable from an agent pod (helm plugins missing) and that the classifier gates
  production applies; the plan's "release, pin, apply, smoke" tail assumed an agent could apply.
- Version claims for a shared component: the plan treated a claimed minor as reserved, but the orchestrator
  auto-release picks the next free tag at merge and other hives release it too.
- The scale gate's own pool connection (a nesting hazard) was not in the research brief on `gate_scale_up`.
- The agent spec relay's `_ALLOWED` and docstring needed updating alongside the new admin routes.

Recommendations:
1. Add the helm plugins (helm-secrets, diff) to the agent image (or a documented pre-installed toolbox) and
   record the sanctioned apply command in the helmfile AGENTS.md, so an agent hive can apply without a human.
2. Plan the deploy step with an explicit owner (hive with apply rights or the user) and a fallback; put the
   classifier rules (bare standalone command, no redirection, no `cd &&`) in the helmfile README.
3. Do not claim an exact orchestrator version in the plan; claim "next free at merge", and read the tag from
   the release run before re-vendoring the plugin fixture. Expect the auto-release bump size (patch vs
   minor) to follow the commit types, and use `feat:` commits when a minor is intended.
4. For pool-based services, add a nesting-spy pool helper to the test kit so any code holding a connection
   while calling a gate/helper that takes its own is caught in the first test.
5. Close the low minors in the next slice that touches these files: type `conn` in sessions.scale and
   messages.cancel, test the `detail=` log suffix, pin label bounds in the plugin tests, exercise 413 on the
   admin spec routes, and add a concurrency test for the preset flip.

### Live smoke

After the apply by tatara-mindmaps (agents-helmfile main b329d58, orchestrator 7.20.1), the 8 slice 3 tools
were smoked on a throwaway project, plus the preset_patch superleader_manageable=false case. All cases tried
passed, including spec_suggestion_dismiss and, in a later addendum run, the 409 open_proposals refusal.

Not tried: `project_update` archiving `default` (expected 422); skipped for production risk and denied by the
classifier. So the 422 guard on `default` is untested live.

Cleanup: the normal session discard got stuck on a failing "settings" discard hook (ConnectError, already
broken before this work, worth a follow-up). The smoke sessions were force-discarded and their PVCs deleted by
hand. The throwaway project is left archived because there is no project delete route.
