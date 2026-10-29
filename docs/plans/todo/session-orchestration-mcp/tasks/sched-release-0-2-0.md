---
title: sched release 0.2.0
status: todo
repo: agents-schedule
value: "the schedule relay ships as release v0.2.0, so agents-helmfile pins a published release chart instead of a main build"
files: [chart/agents-schedule/Chart.yaml, pyproject.toml, uv.lock, src/agents_schedule/__init__.py, README.md, tests/test_chart.py]
verify: "uv run pytest tests/test_chart.py tests/test_cli.py tests/test_ci_workflow.py && mise run lint"
depends_on: [sched-chart-relay-port]
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

# sched release 0.2.0

## Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Design D17, verbatim: "agents-schedule is pinned by its release tag v0.2.0 (negotiated, user answer pending): chart `0.2.0`, published by the tag's `chart-publish-tag` job, and image `<sha7>` of the tagged commit, published by its main build, the way v0.1.0 is pinned today (chart `0.1.0`, image `6cfa955`). The orchestrator and agents-web are pinned by main sha7 as today; the agent image stays on its release tag. `mise run check-pins` resolves `0.2.0` through tag `v0.2.0` and must pass before any apply."

Standing user rule (2026-10-29, design.md Constraints), verbatim: "every release tag is proposed via mx-34 and confirmed before tagging."

Negotiated (mx-34 #469/#470, 2026-10-29; tatara agreed, the user's direct answer is pending): agents-schedule v0.2.0, the next minor after the latest tag v0.1.0.

Scope (agents-schedule), after every other agents-schedule task of this epic has merged:
- Confirm the baseline: the latest tag on origin is v0.1.0 and `chart/agents-schedule/Chart.yaml` says 0.1.0 (baseline-facts); stop and report on a mismatch, never pick another number.
- `chart/agents-schedule/Chart.yaml`: `version: 0.2.0`, `appVersion: "0.2.0"`; `scripts/chart-version.sh` refuses a tag whose version differs from Chart.yaml, so the tag needs this bump on main first.
- `pyproject.toml` version 0.2.0, `src/agents_schedule/__init__.py` `__version__ = "0.2.0"`, `uv lock` updates `uv.lock`.
- README `## Releases`: a v0.2.0 line in the shape of the v0.1.0 line: tag v0.2.0 on the merge commit of this release, image `harbor.szymonrichert.pl/containers/agents-schedule:<sha7 of that commit>`, chart version 0.2.0 (the sha is not known before the merge, so the line names the rule, not the value).
- Test no longer accurate (named): `tests/test_chart.py::test_image_tag_defaults_to_app_version` asserts the default image ends with `:0.1.0` (the Chart.yaml appVersion); it asserts `:0.2.0`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI and the main build pushed the image `<sha7>` of the merge commit: propose the tag v0.2.0 on that merge commit on mx-34 and wait for the confirmation, then `git tag -a v0.2.0 <merge sha> -m v0.2.0 && git push origin v0.2.0` (irreversible, listed in design.md); the `chart-publish-tag` job then publishes chart 0.2.0. ac5, ac6 and ac7 are checked by the orchestrator after that push.

## Acceptance conditions

- ac1: Chart.yaml version and appVersion, pyproject.toml and __version__ all say 0.2.0, and the default image tag follows the appVersion (updated) [evidence: test:tests/test_chart.py::test_image_tag_defaults_to_app_version]
- ac2: README Releases has a v0.2.0 line naming the tag, the image rule and chart 0.2.0 [evidence: command:grep -q "v0.2.0" README.md]
- ac3: scripts/chart-version.sh accepts tag v0.2.0 and prints 0.2.0 [evidence: command:test "$(scripts/chart-version.sh tag v0.2.0 0123456789abcdef)" = 0.2.0 && grep -q '^version = "0.2.0"' pyproject.toml]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_chart.py tests/test_cli.py tests/test_ci_workflow.py && mise run lint]
- ac5: (orchestrator session) the tag v0.2.0 was proposed on mx-34 and confirmed there before it was pushed [evidence: judgement:orchestrator quotes the mx-34 proposal and confirmation message ids, both older than the tag push, in the task Notes]
- ac6: (orchestrator session) the tag v0.2.0 exists on origin at the merge commit, and its chart-publish-tag job and the merge commit's images job succeeded [evidence: command:git ls-remote --tags origin | grep -q 'refs/tags/v0.2.0']
- ac7: (orchestrator session) chart 0.2.0 and image <sha7 of the tagged commit> exist in Harbor [evidence: judgement:orchestrator quotes helm show chart oci://harbor.szymonrichert.pl/charts/agents-schedule --version 0.2.0 and the image digest in the task Notes]

## Files

- `chart/agents-schedule/Chart.yaml`
- `pyproject.toml`
- `uv.lock`
- `src/agents_schedule/__init__.py`
- `README.md`
- `tests/test_chart.py`

## Interfaces

- `chart/agents-schedule/Chart.yaml`: `version: 0.2.0`, `appVersion: "0.2.0"`.
- `pyproject.toml:version = "0.2.0"`, `src/agents_schedule/__init__.py:__version__ = "0.2.0"` (printed by `sched --version`, `tests/test_cli.py`).
- `scripts/chart-version.sh tag v0.2.0 <sha>` prints `0.2.0` (unchanged script; it refuses a tag that differs from Chart.yaml).
- Git tag `v0.2.0` (annotated, like v0.1.0) on the merge commit; chart `oci://harbor.szymonrichert.pl/charts/agents-schedule` 0.2.0 (appVersion the sha7) from `chart-publish-tag`; image `harbor.szymonrichert.pl/containers/agents-schedule:<sha7>` from the merge commit's main `images` job.

## Expected outcome

agents-schedule v0.2.0 exists as a tag, a published chart 0.2.0 and an image, carrying the owner columns, the relay listener and routes and the relay Service of this epic, for helmfile-orchestration-pins to pin.

## Steps

- Confirm the baseline: `git fetch --tags origin && git tag --sort=-v:refname | head -1` prints `v0.1.0`; `grep -n "^version" chart/agents-schedule/Chart.yaml` prints `0.1.0`; stop and report otherwise.
- Red: change `tests/test_chart.py::test_image_tag_defaults_to_app_version` to `:0.2.0`; run `uv run pytest tests/test_chart.py::test_image_tag_defaults_to_app_version`: fails on `:0.1.0`.
- Green: bump Chart.yaml, pyproject, `__version__`, `uv lock`, README `## Releases`; run the task's verify. Quote the summary line.
- After the merge (orchestrator session): wait for the main run green (images and chart-publish jobs), propose v0.2.0 on mx-34 and wait for the confirmation, push the annotated tag, wait for `chart-publish-tag` green, check ac5 to ac7.

## Notes

- Dependency-bump TDD exception for the version values beyond the named test.
- Runs last among the agents-schedule tasks (depends on sched-chart-relay-port, which depends on the routes, listener and owner tasks), so the tag carries all of them.
- The image stays a sha7 tag (CI pushes images only on main pushes); Harbor retention pruned sha7 image tags within hours in the 2026-10-28 incident while chart versions survive. orchestration-live-smoke checks the image in Harbor right before the apply; semver image tags are semver-image-tags-at-the-end's scope (it later removes `chart-publish-tag` and the tag mode of `chart-version.sh`, so this task must land before it).
- The README Releases line names the image rule, not the sha (unknown before the merge); the supervisor never edits repo files after the merge.
