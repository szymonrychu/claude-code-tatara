---
title: helmfile orch release rename
status: done
repo: agents-helmfile
value: the orchestrator is declared as agents-orchestrator and the old app release is retired
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/, values/agents-orchestrator/, scripts/bootstrap-secrets.sh, tests/test_orchestrator_release.py, tests/test_secrets.py]
verify: "uv run pytest -q tests/test_orchestrator_release.py tests/test_secrets.py && mise run lint"
depends_on: [helmfile-orch-db-import, orch-docs-e2e-sessions]
model: opus
review: ""
verified_head: 6361a57
points: 5
expected_minutes: 14
expected_tokens: 1883475
points_actual: 5
actual_minutes: 4
actual_tokens: 1099592
actual_roles: "impl 4, review 1"
actual_role_tokens: "impl 988743, review 110849"
---

# helmfile orch release rename

## Requirement

Declare the orchestrator under its new release name and retire the old app release (design D1, D7, D9, D11; contracts `agents-orchestrator-chart` / `-image`, `any-mcp-release-v0-3-0`). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agents-orchestrator PR is merged to main and its CI published chart `0.1.0-main.<sha7>` and image `<sha7>` under the new names (`helm show chart oci://harbor.szymonrichert.pl/charts/agents-orchestrator --version 0.1.0-main.<sha7>`). The orchestrator writes `<sha7>` into this task with `ticket.py amend` once the PR merges; otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-orchestrator PR and wait for its main CI".

- `helmfile.yaml.gotmpl`: the old `agent-orchestrator` release keeps only name, namespace, chart and `installed: false` (helmfile uninstalls it on apply; no values or secrets listed); new release `agents-orchestrator` (chart `oci://harbor.szymonrichert.pl/charts/agents-orchestrator`, version `0.1.0-main.<sha7>`, timeout 600, `needs: [agents/agents-orchestrator-db]`, labels `application: agents-orchestrator`, the default template, `secrets:` `values/agents-orchestrator/default.secrets.yaml` then `values/agents-orchestrator/service-token-agents-webhook.secrets.yaml`).
- `git mv values/agent-orchestrator values/agents-orchestrator` (the encrypted files move byte-identical: the master key, Claude token and service token hashes keep their values, so derived tokens do not change).
- `values/agents-orchestrator/common.yaml`: image `harbor.szymonrichert.pl/containers/agents-orchestrator` tag `<sha7>`; `postgres.existingSecret: agents-orchestrator-db-cluster-app`; `ORCH_ANY_MCP_REF: v0.3.0`; any ORCH_* name renamed by D2 (none set today: confirm); podAnnotations `oauth2-proxy-admission/secret-name: agents-orchestrator-proxy` (D9, created by user step U1); ingress TLS `secretName: agents-orchestrator-tls` with the cert-manager annotations kept (this ingress owns the certificate); comments name agents-orchestrator.
- `scripts/bootstrap-secrets.sh`: the moved paths and new names.
- tests/: `tests/test_orchestrator_release.py` (`REL = "agents-orchestrator"`, every assertion on the new names, the db template test on `agents-orchestrator-db`; new `test_old_release_uninstalled` and `test_values_dir_moved` (`git ls-files values/agent-orchestrator` prints nothing)); `tests/test_secrets.py` paths. Tests first.

## Acceptance conditions

- AC1: the old app release is declared installed false with nothing else [evidence: test:tests/test_orchestrator_release.py::test_old_release_uninstalled]
- AC2: the values directory moved and the old path is gone from git [evidence: test:tests/test_orchestrator_release.py::test_values_dir_moved]
- AC3: chart version and image tag agree on the merged agents-orchestrator sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC4: the release reads the new DB, SSO and TLS Secret names and any-mcp v0.3.0 [evidence: command:uv run pytest -q tests/test_orchestrator_release.py tests/test_secrets.py]
- AC5: the pinned chart and image exist in Harbor [evidence: judgement:the task notes quote helm show chart and docker manifest inspect for the pinned sha]
- AC6: lint passes [evidence: command:mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/`
- `values/agents-orchestrator/`
- `scripts/bootstrap-secrets.sh`
- `tests/test_orchestrator_release.py`
- `tests/test_secrets.py`

## Interfaces

- Release `agents-orchestrator` values (Services `agents-orchestrator`, `-agents`, `-services:8002`; Secrets `agents-orchestrator-{claude,master-key,services}`); old release `agent-orchestrator` `installed: false`.

## Expected outcome

The helmfile declares the renamed orchestrator release and the old app release as uninstalled; nothing is applied here.

## Steps

- Check the precondition (merged sha and Harbor artefacts) first.
- Red: update `tests/test_orchestrator_release.py` and `tests/test_secrets.py` to the new names and add the two new tests; they fail.
- Green: helmfile release blocks, `git mv` the values dir, values and bootstrap script; the verify passes.

## Notes

- `git mv` keeps the encrypted files byte-identical; never re-encrypt them (the master key value must not change).
- Never apply: deploy-cutover sequences the applies (design D7).

- 2026-10-25 done
