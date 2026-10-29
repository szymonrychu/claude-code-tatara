---
title: helmfile cache pins
status: todo
repo: agents-helmfile
value: The live namespace is pinned to the orchestrator and web releases with the Cache section and the bucket quota
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_orchestrator_release.py, tests/test_web_release.py, tests/test_workspace_cache.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py tests/test_workspace_cache.py && mise run lint"
depends_on: [orch-cache-pins, orch-cache-tables, orch-cache-inventory, orch-cache-requests, orch-cache-api, orch-chart-cache-quota, web-cache-client, web-cache-section]
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

# helmfile cache pins

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G5, verbatim: "a quota gauge shows bytes and objects against the bucket quota set in agents-helmfile; released and deployed, and proven live by listing the bucket and deleting one disposable object."

Design D7 (Quota settings), verbatim: "`ORCH_CACHE_QUOTA_BYTES` and `ORCH_CACHE_QUOTA_OBJECTS` (default unset, gauge hidden), set in agents-helmfile values from the OBC quota (100G, 100000). User Q4."

Design D9 (Deploy and live check), verbatim: "Release orchestrator and web, pin in agents-helmfile with the quota values, apply under the deploy lease; the live check lists the bucket in the section and deletes one disposable object created for the check (a smoke object, never a session's cache) (my call)."

User decision (repos), verbatim: "Repos: agents-orchestrator, agents-web, agents-helmfile (quota values, image pins, and a live check after the apply under the deploy lease [...])".

Scope (agents-helmfile): pin agents-orchestrator to the merge commit `<ORCH_SHA>` of its epic PR (chart `0.1.0-main.<ORCH_SHA>` in helmfile.yaml.gotmpl, `image.tag` `<ORCH_SHA>` in values/agents-orchestrator/common.yaml) and agents-web to the merge commit `<WEB_SHA>` of its epic PR (chart `0.1.0-main.<WEB_SHA>`, `image.tag` `<WEB_SHA>` in values/agents-web/common.yaml), after each main CI run for those shas is green including chart and image publish. Set `cache.quota.bytes: 100000000000` and `cache.quota.objects: 100000` in values/agents-orchestrator/common.yaml, the quota of raw/workspace-cache-bucket.pre.yaml (`maxSize: 100G`, `maxObjects: "100000"`), with a test that keeps the two equal. Keep every other pin and value unchanged. Update tests/test_orchestrator_release.py and tests/test_web_release.py to the new pins. `mise run check-pins` must pass. Never run an apply. `<ORCH_SHA>` and `<WEB_SHA>` are placeholders: the orchestrator replaces them with the real 7-character merge shas through `ticket.py amend` before this task starts.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the orchestrator merge sha `<ORCH_SHA>` [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the agents-web chart version and image tag agree on the agents-web merge sha `<WEB_SHA>` [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the pins name the merge shas [evidence: command:grep -q "0.1.0-main.<ORCH_SHA>" helmfile.yaml.gotmpl && grep -q "0.1.0-main.<WEB_SHA>" helmfile.yaml.gotmpl]
- AC4: the orchestrator cache.quota values equal the bucket claim's maxSize (as a Kubernetes quantity, 100G = 100000000000 bytes) and maxObjects [evidence: test:tests/test_workspace_cache.py::test_orchestrator_cache_quota_matches_bucket_claim]
- AC5: every pin's main CI is green [evidence: command:mise run check-pins]
- AC6: the release and cache test files and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py tests/test_workspace_cache.py && mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`
- `tests/test_workspace_cache.py`

## Interfaces

- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.<ORCH_SHA>`, agents-web chart `0.1.0-main.<WEB_SHA>`.
- `values/agents-orchestrator/common.yaml`: `image.tag` `<ORCH_SHA>`; under `cache`, `quota: {bytes: 100000000000, objects: 100000}` (chart values from task orch-chart-cache-quota). `values/agents-web/common.yaml`: `image.tag` `<WEB_SHA>`. No other value changes.

## Expected outcome

agents-helmfile main pins the orchestrator and web releases of this epic with the bucket quota set, ready for the apply in helmfile-cache-live-check.

## Steps

- Read helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, raw/workspace-cache-bucket.pre.yaml, tests/test_orchestrator_release.py, tests/test_web_release.py, tests/test_workspace_cache.py and tests/conftest.py (`layered_values`) in one pass; confirm `<ORCH_SHA>` and `<WEB_SHA>` were amended to real shas.
- Red: change the pin assertions to the amended shas and add `test_orchestrator_cache_quota_matches_bucket_claim` (parse maxSize as a Kubernetes quantity: decimal suffixes k, M, G, T and binary Ki, Mi, Gi, Ti); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py tests/test_workspace_cache.py`; expect the pin and quota tests to fail.
- Green: change the pins and add the quota values; rerun the verify; expect passed and lint exit 0; `mise run check-pins`; expect every pin green.

## Notes

- `<ORCH_SHA>` and `<WEB_SHA>` mean the 7-character short merge sha (the pin tests require `[0-9a-f]{7}`). If either still reads as a placeholder, stop and return it as a question. Never pin an epic-branch commit.
- (my call) Rook reads `maxSize: 100G` as a Kubernetes quantity, so 100G is 100000000000 bytes (decimal), not 100 GiB; the test parses the claim rather than restating the number.
- Retro (file-editor-with-tabs-and-hi, generic-any-mcp-with-git-and): Harbor prunes sha7 image tags; the live check verifies the pinned tags exist before the apply.
- Chart-pull tests blocked by a container network policy may be deselected locally (precedent); they run unblocked before the apply.
- Never run an apply in this task. `gh` must be authenticated for check-pins.
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
