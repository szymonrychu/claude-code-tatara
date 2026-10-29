---
title: helmfile orchestration pins
status: todo
repo: agents-helmfile
value: "agents-helmfile pins the orchestrator, schedule and web builds of this epic and wires the relay"
files: [values/agents-orchestrator/common.yaml, values/agents-schedule/common.yaml, values/agents-web/common.yaml, helmfile.yaml.gotmpl, tests/test_orchestrator_release.py, tests/test_schedule_release.py, tests/test_web_release.py]
verify: "uv run pytest tests/test_orchestrator_release.py tests/test_schedule_release.py tests/test_web_release.py && mise run check-pins && mise run lint"
depends_on: [helmfile-relay-secrets, orch-orchestration-tools-pin, sched-chart-relay-port, sched-release-0-2-0, web-created-by, web-schedule-owner, plugins-release-orch-tools]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile orchestration pins

## Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Design D15, verbatim: "The orchestrator values set `schedule.url: http://agents-schedule-api-relay:8001`."

Design D17, verbatim: "agents-schedule is pinned by its release tag v0.2.0 (negotiated, user answer pending): chart `0.2.0`, published by the tag's `chart-publish-tag` job, and image `<sha7>` of the tagged commit, published by its main build, the way v0.1.0 is pinned today (chart `0.1.0`, image `6cfa955`). The orchestrator and agents-web are pinned by main sha7 as today; the agent image stays on its release tag. `mise run check-pins` resolves `0.2.0` through tag `v0.2.0` and must pass before any apply."

Standing user rule (2026-10-27), verbatim from the lead: "Deploy whenever possible: live applies need no approval, so include the agents-helmfile values, apply and live smoke tasks in this epic."

Design D16 (staleness refresh 2026-10-29), verbatim: "`ORCH_SCHEDULE_URL` and `ORCH_SCHEDULE_TOKEN` are env of the api main container only, always together, rendered by one `agents-orchestrator.scheduleEnv` helper next to `agents-orchestrator.chatEnv`, never in the shared settings ConfigMap, the migrate init containers or the other components (orchestrator MEMORY 2026-10-28, orch-chat-env-scope: the chart once put `ORCH_CHAT_URL` in the shared ConfigMap with the token on the api only, and every migrate init container crash-looped on a URL without its token)."

Scope (agents-helmfile): `values/agents-orchestrator/common.yaml` (image tag, `schedule.url`, `ORCH_ANY_MCP_PLUGINS_REF` `v0.6.0`, was `v0.5.1` after the slash-commands-from-chat deploy), `values/agents-schedule/common.yaml` (image tag the sha7 of the commit tagged v0.2.0, relay on), `values/agents-web/common.yaml` (image tag), `helmfile.yaml.gotmpl` (orchestrator and web chart versions `0.1.0-main.<sha7>`, schedule chart version `0.2.0`), `tests/test_orchestrator_release.py`, `tests/test_schedule_release.py`, `tests/test_web_release.py`.

Tests no longer accurate (named): `tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image` (its `PIN`) and `::test_any_mcp_configured_for_new_sessions` (the plugins ref), `tests/test_schedule_release.py::test_release_declared` and `::test_schedule_pin_matches_release` (they pin chart `0.1.0` and image `6cfa955`), `tests/test_web_release.py::test_web_pin_matches_image` (its pin); each asserts the new pin.

## Acceptance conditions

- ac1: the orchestrator image tag and chart version name the same orchestrator main sha7 (updated) [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac2: the orchestrator values set schedule.url to http://agents-schedule-api-relay:8001 and no plaintext schedule token, the token coming from the encrypted schedule-token.secrets.yaml listed in the release [evidence: test:tests/test_orchestrator_release.py::test_schedule_relay_wired]
- ac3: new sessions install the orchestrator plugin at v0.6.0 (updated) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac4: the schedule chart version is 0.2.0 and the image tag the sha7 of the commit tagged v0.2.0, and the release still needs its database and the orchestrator (updated) [evidence: test:tests/test_schedule_release.py::test_schedule_pin_matches_release]
- ac5: the schedule release is still declared with its chart, namespace, labels and the orchestrator service token file (updated) [evidence: test:tests/test_schedule_release.py::test_release_declared]
- ac6: the schedule values turn the relay listener on with its hash from relay-token.secrets.yaml and no plaintext hash [evidence: test:tests/test_schedule_release.py::test_relay_listener_enabled]
- ac7: the web image tag and chart version name the same agents-web main sha7 (updated) [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- ac8: the pinned orchestrator sha7 contains orch-orchestration-tools-pin and orch-chart-schedule-relay, the commit tagged v0.2.0 contains sched-release-0-2-0 and sched-chart-relay-port, and the web sha7 contains web-created-by and web-schedule-owner, each on its repo's main [evidence: judgement:reviewer checks git merge-base --is-ancestor of each task's verified_head against the pinned sha or the tagged commit]
- ac9: the rendered agents-orchestrator release has no ORCH_SCHEDULE_URL in any ConfigMap and puts ORCH_SCHEDULE_URL and ORCH_SCHEDULE_TOKEN together on the api main container only, with one -schedule Secret [evidence: test:tests/test_orchestrator_release.py::test_schedule_url_and_token_render_together]
- ac10: every pinned build, the schedule chart 0.2.0 through tag v0.2.0 included, has all-green check runs [evidence: command:mise run check-pins]
- ac11: the targeted tests, check-pins and lint pass [evidence: command:uv run pytest tests/test_orchestrator_release.py tests/test_schedule_release.py tests/test_web_release.py && mise run check-pins && mise run lint]

## Files

- `values/agents-orchestrator/common.yaml`
- `values/agents-schedule/common.yaml`
- `values/agents-web/common.yaml`
- `helmfile.yaml.gotmpl`
- `tests/test_orchestrator_release.py`
- `tests/test_schedule_release.py`
- `tests/test_web_release.py`

## Interfaces

- `values/agents-orchestrator/common.yaml`: `image.tag` the orchestrator main sha7, `schedule.url: http://agents-schedule-api-relay:8001`, `env.ORCH_ANY_MCP_PLUGINS_REF: v0.6.0`; the token from `schedule-token.secrets.yaml` (helmfile-relay-secrets lists it in the release).
- `helmfile.yaml.gotmpl`: agents-orchestrator `version: 0.1.0-main.<sha7>`, agents-web `version: 0.1.0-main.<sha7>`, agents-schedule `version: 0.2.0`.
- `values/agents-schedule/common.yaml`: `image.tag` the sha7 of the commit tagged v0.2.0, relay on (`relay.port: 8001`), hash from `relay-token.secrets.yaml`.
- `tests/test_orchestrator_release.py::test_schedule_url_and_token_render_together` mirrors `::test_chat_url_and_token_render_together` (helmfile template of the release, no ConfigMap carrier, the pair together on `agents-orchestrator-api/api` only, one `-schedule` Secret).

## Expected outcome

agents-helmfile pins the orchestrator and web main builds and the agents-schedule v0.2.0 release of this epic, the plugins v0.6.0 ref, and wires the relay with the URL and token on the orchestrator api main container only.

## Steps

- Read each repo's main sha7 carrying the tasks named in ac8 and the commit tagged v0.2.0 (`git rev-parse --short=7 v0.2.0^{commit}` in agents-schedule); confirm CI green on each; stop and report if not.
- Red: update the named tests and add `test_schedule_relay_wired`, `test_relay_listener_enabled` and `test_schedule_url_and_token_render_together`; run `uv run pytest tests/test_orchestrator_release.py tests/test_schedule_release.py tests/test_web_release.py`: they fail.
- Green: values and chart versions; run the task's verify (including `mise run check-pins`, which needs `gh` auth). Quote the summary lines.

## Notes

- The images and charts are checked in Harbor by orchestration-live-smoke before any apply; this task does not apply.
- Builds on the orchestrator values the slash-commands-from-chat deploy leaves (plugins ref v0.5.1, wrapper agent image 0.4.1 or 0.4.2; live today before it: orchestrator 2d6d722, plugins v0.4.0, agent image 0.3.3): keep the chat and other settings, change only what this task names.
- The schedule image stays a sha7 tag (agents-schedule CI pushes images only on main); Harbor retention pruned sha7 image tags within hours on 2026-10-28, chart versions survive. orchestration-live-smoke checks the image in Harbor right before the apply.
- agents-helmfile has no CI on main (agents-helmfile-ci-test-job is in progress): the local verify, check-pins included, is the evidence.

- 2026-10-29 amended: staleness refresh: schedule pinned by release v0.2.0 (negotiated, user answer pending); plugins v0.6.0; check-pins; schedule pair render test
