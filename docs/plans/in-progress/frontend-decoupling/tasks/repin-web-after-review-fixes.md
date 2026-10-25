---
title: repin web after review fixes
status: todo
repo: agents-helmfile
value: the live UI runs the chart with config.json parity checks and a working helm test
files: [helmfile.yaml.gotmpl, values/agents-web/common.yaml, tests/test_web_release.py]
verify: "uv run pytest -q -p no:cacheprovider && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 728948
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# repin web after review fixes

## Requirement

Epic review findings (agents-web PRs #3 regctl pin, #4 chart config.json validation parity and helm test bypassing the SSO sidecar) merged as cedcbbcd72f82c6ff9ff6cb5251412cbda5a90ad and published (run 40189450653). Re-pin the agents-web release in agents-helmfile from db1f482 to cedcbbc (chart 0.1.0-main.cedcbbc and image tag), update the pin test, confirm `helm show chart` for the new version, keep every test green. The orchestrator applies live and runs the smoke; the implementer never applies.

## Acceptance conditions

- AC1: the agents-web chart and image are pinned to cedcbbc and the pin test asserts it [evidence: command:grep -q "0.1.0-main.cedcbbc" helmfile.yaml.gotmpl && grep -q "cedcbbc" values/agents-web/common.yaml]
- AC2: the offline suite and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider && uv run ruff check .]
- AC3: applied live with no drift and a green smoke [evidence: judgement:the apply, post-apply diff and smoke last line quoted in the task notes]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-web/common.yaml`
- `tests/test_web_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

Orchestrator notes (2026-10-25): implementer re-pinned (c99cfdc, red: `assert 'db1f482' == 'cedcbbc'`), agents-helmfile PR #19 merged (cc33dd2). Pre-apply diff: agents-web image db1f482 -> cedcbbc, new Service agents-web-test, labels. `mise run apply`: agents-web 0.1.0-main.cedcbbc deployed. Post-apply diff: `No affected releases`. `mise run smoke` last line: `smoke: OK`.
