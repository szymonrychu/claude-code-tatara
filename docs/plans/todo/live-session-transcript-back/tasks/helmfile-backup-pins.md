---
title: helmfile backup pins
status: todo
repo: agents-helmfile
value: The live namespace is pinned to the orchestrator and web releases that back up live sessions
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_orchestrator_release.py, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint"
depends_on: [orch-archive-live-files, orch-sessions-live-backup, orch-discard-stops-backup, orch-backup-view-latest, web-discard-latest-backup]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile backup pins

## Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G5, verbatim: "released and deployed (orchestrator image, web image, helmfile pins), and proven live: a running session's transcripts object appears in S3 with a recent `last_transcripts_backup`."

Design D8 (the deploy part), verbatim: "agents-helmfile pins the new orchestrator and web images; no value change needed for the default."

User decision (repos), verbatim: "agents-helmfile (pins plus a live check after the apply under the deploy lease [...])".

Scope (agents-helmfile): pin agents-orchestrator to the merge commit `<ORCH_SHA>` of its epic PR (chart `0.1.0-main.<ORCH_SHA>` in helmfile.yaml.gotmpl, `image.tag` `<ORCH_SHA>` in values/agents-orchestrator/common.yaml) and agents-web to the merge commit `<WEB_SHA>` of its epic PR (chart `0.1.0-main.<WEB_SHA>`, `image.tag` `<WEB_SHA>` in values/agents-web/common.yaml). Wait until each main CI run for those shas is green including chart and image publish. Keep every other pin and value unchanged (no ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS value: the default applies). Update tests/test_orchestrator_release.py and tests/test_web_release.py to the new pins. `mise run check-pins` must pass. Never run an apply. `<ORCH_SHA>` and `<WEB_SHA>` are placeholders: the orchestrator replaces them with the real merge shas through `ticket.py amend` before this task starts.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the orchestrator merge sha `<ORCH_SHA>` [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the agents-web chart version and image tag agree on the agents-web merge sha `<WEB_SHA>` [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the pins name the merge shas [evidence: command:grep -q "0.1.0-main.<ORCH_SHA>" helmfile.yaml.gotmpl && grep -q "0.1.0-main.<WEB_SHA>" helmfile.yaml.gotmpl]
- AC4: every pin's main CI is green [evidence: command:mise run check-pins]
- AC5: the release test files and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`

## Interfaces

- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.<ORCH_SHA>`, agents-web chart `0.1.0-main.<WEB_SHA>`.
- `values/agents-orchestrator/common.yaml`: `image.tag` `<ORCH_SHA>`; `values/agents-web/common.yaml`: `image.tag` `<WEB_SHA>`. No other value changes.

## Expected outcome

agents-helmfile main pins the orchestrator and web releases of this epic (which also carry decouple-s3-session-cache-fr, open question Q7), ready for the apply in helmfile-backup-live-check.

## Steps

- Read helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_orchestrator_release.py and tests/test_web_release.py in one pass.
- Red: change the pin assertions in the two test files to `<ORCH_SHA>` and `<WEB_SHA>`; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py`; expect the pin tests to fail.
- Green: change the pins; rerun the verify; expect passed and lint exit 0; `mise run check-pins`; expect every pin green.

## Notes

- (my call, builder Q4) `<ORCH_SHA>` and `<WEB_SHA>` mean the 7-character short merge sha (the pin tests require `[0-9a-f]{7}`), never the full 40.
- (my call, builder Q5) the orchestrator session amends the placeholders with `ticket.py amend` after both epic PRs (agents-orchestrator, agents-web) have merged and their main CI runs are green; the Red step then edits the test literals first.
- `<ORCH_SHA>` and `<WEB_SHA>` are placeholders; the orchestrator replaces them with `ticket.py amend` once both epic PRs merged and their main CI runs (images and chart publish) are green. Never pin an epic-branch commit.
- Chart-pull tests blocked by a container network policy may be deselected locally (precedent); they run unblocked before the apply.
- Never run an apply in this task.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes.
