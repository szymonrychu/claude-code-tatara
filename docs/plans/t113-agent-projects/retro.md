# T-113 retro: agent projects

## Verdict

Delivered to the user's decision (decision 363): superleader-only project create (orchestrator 7.6.0,
plugins v0.33.0) and superleader preset move including privileged presets (plugins #39 -> v0.34.0,
orchestrator #108 -> v7.7.0, agents-helmfile #149, deployed 2026-11-11 08:58Z, helm rev 62).
Move goes through admin PUT/PATCH, audited as admin_call, unknown target project is 422, vault
recheck reused, sessions keep their project, no rename/archive tool. HUMAN_ONLY_COLUMNS removed.
Part 3 (apply the T-112 mapping) is handed to tatara-orch-epics-2, not part of this delivery.

## Under- and over-delivery

- Under: plan.md still describes the first-answer design (privileged presets refused) and was not
  updated after decision 363; it now disagrees with the code. plugins #39 touches preset_patch and
  preset_replace only; preset_copy already carried `project`, so the plan row was stale.
- Over: none found. The built-then-removed privileged switch left no residue in src.

## What came up during implementation

- The privileged-preset question was not resolvable from the first answer (it superseded the earlier
  S3 B answer) and needed a second ask.
- A privileged-preset switch (setting) was built, then removed once the decision was final.
- Review found three missing tests (move audit, vault mismatch on move, unknown project).
- Release ordering: the plugin version bump and the uv relock had to land before the orchestrator
  ref and helmfile pins; relock order caused a re-push.
- Auto-mode blocked a compound apply command; it had to be split into single steps.
- The T-112 mapping file lives in another session's workdir, so part 3 needed a hand-off message.

## What discovery and planning overlooked

- That the privileged rule was a policy question, not a technical one; the first questionnaire
  offered "refused for privileged" as MVP and Recommended without asking about the blast radius.
- Test files that encode the old refusal were listed, but the vault-on-move test was not.
- Cross-session data dependency (mapping file location) for the follow-up part.

## Recommendations

1. When a question touches a privilege boundary, ask it as its own question with the escalation
   consequence stated, and re-open plan.md after every answer so it matches the code.
2. Put the release order (plugin version + relock, tag, orchestrator ref, helmfile pin) in the
   implementation plan as an explicit checklist with the relock as a step.
3. List new-behaviour tests in the plan per risk (audit, vault, unknown target), not only the
   rewritten refusal tests.
4. Hand off cross-session inputs by copying them to a shared path or the taskboard, not a workdir.
5. Prefer single-command apply steps in auto-mode.
