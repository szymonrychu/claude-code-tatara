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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
