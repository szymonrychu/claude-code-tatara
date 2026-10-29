---
title: plugins release orch tools
status: todo
repo: any-mcp-tatara-plugins
value: the orchestration tools ship as a plugins release tag the orchestrator can pin
files: [orchestration/orchestrator/pyproject.toml, uv.lock, orchestration/orchestrator/README.md, tests/test_source_install.py]
verify: "uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint"
depends_on: [plugin-orchestration-tools]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugins release orch tools

## Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Design D11, verbatim: "The release is any-mcp-tatara-plugins v0.6.0, the next minor after the latest tag v0.5.1 that slash-commands-from-chat leaves pinned (negotiated 2026-10-29, mx-34 #469/#470)."

Standing user rule (2026-10-29, design.md Constraints), verbatim: "every release tag is proposed via mx-34 and confirmed before tagging."

Repo README `## Releases`, verbatim: "Releases are `vX.Y.Z` tags on `main`; pin `?ref=` to a release tag. Nothing is published beyond the tag."

Scope (any-mcp-tatara-plugins):
- Confirm the baseline: the latest tag on origin is v0.5.1 and `orchestration/orchestrator/pyproject.toml` says 0.5.1 (baseline-facts); stop and report on a mismatch, never pick another number.
- `orchestration/orchestrator/pyproject.toml`: version 0.6.0; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=v0.6.0` (was `v0.5.1`).
- Tests no longer accurate (named): `tests/test_source_install.py::test_orchestrator_distribution_metadata` asserts version 0.5.1 for the pyproject metadata and the installed distribution; it asserts 0.6.0.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: propose the tag v0.6.0 on the merge commit on mx-34 and wait for the confirmation (the number was negotiated in mx-34 #469/#470; the tag itself is still proposed and confirmed before it is pushed), then `git tag v0.6.0 <merge sha> && git push origin v0.6.0` (irreversible, listed in design.md). ac3 and ac5 are checked by the orchestrator after that push.

User settlement B6 (2026-10-27), verbatim: "the build starts only after all three blockers have merged. The first task reads the real migration number, plugins version and tool counts from main and amends the dependent tasks. No assumed numbers in ACs." The version this task bumps from and to is the one baseline-facts confirmed (0.5.1 to 0.6.0).

## Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.6.0 (updated) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins ?ref=v0.6.0 and no older tag [evidence: command:grep -q 'ref=v0.6.0' orchestration/orchestrator/README.md && ! grep -q 'ref=v0.5' orchestration/orchestrator/README.md]
- ac3: (checked by the orchestrator session after it pushed the tag) the tag v0.6.0 exists on origin at the merge commit [evidence: command:git ls-remote --tags origin | grep -q "refs/tags/v$(sed -n 's/^version = .\([0-9.]*\)./\1/p' orchestration/orchestrator/pyproject.toml)$"]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]
- ac5: (orchestrator session) the tag v0.6.0 was proposed on mx-34 and confirmed there before it was pushed [evidence: judgement:orchestrator quotes the mx-34 proposal and confirmation message ids, both older than the tag push, in the task Notes]

## Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

## Interfaces

- Distribution `any-mcp-tatara-orchestrator` version 0.6.0 (was 0.5.1); git tag `v0.6.0` on the `main` merge commit, pushed only after its mx-34 confirmation.

## Expected outcome

The plugin with the orchestration tools is released as a tag the orchestrator can pin.

## Steps

- Confirm the baseline: `git ls-remote --tags origin` lists v0.5.1 as the highest tag and `orchestration/orchestrator/pyproject.toml` says 0.5.1; stop and report on a mismatch.
- Red: change `test_orchestrator_distribution_metadata` to the new version; run it: fails.
- Green: bump pyproject, `uv lock`, README example; run the task's verify. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, propose `v0.6.0 on <merge sha7>` on mx-34 and wait for the confirmation, push the tag, check ac3 and record ac5's message ids in Notes.

## Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- Standing rule since 2026-10-29 14:27Z: every tag is proposed on mx-34 and confirmed before it is pushed; v0.5.1 was once tagged without it and mx-34 reported it to the user (handover note 2026-10-29). The number negotiation (mx-34 #469/#470) does not replace the per-tag proposal.
- immediate-message-delivery-w takes v0.7.0 on top of this v0.6.0.
- `tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources` fails in this pod with git 2.39 (`--end-of-options`, environmental per Matrix); CI is its gate.

- 2026-10-27 amended: builder check B6: version from baseline-facts

- 2026-10-29 amended: staleness refresh: v0.6.0 from v0.5.1; mx-34 proposal and confirmation before tagging
