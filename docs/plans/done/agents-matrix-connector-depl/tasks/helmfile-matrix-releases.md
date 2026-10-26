---
title: helmfile matrix releases
status: done
repo: agents-helmfile
value: "the connector and its own database are declared in namespace agents, logged in as the bot, behind SSO"
files: [helmfile.yaml.gotmpl, values/agents-matrix-connector/common.yaml, values/agents-matrix-connector-db/common.yaml, tests/test_matrix_connector_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py -k \"not helmfile_build\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [helmfile-matrix-secrets]
model: sonnet
review: ""
verified_head: 20589c35949fe4779fe943118de4eb569919acf5
points: 3
expected_minutes: 7
expected_tokens: 907602
points_actual: 3
actual_minutes: 11
actual_tokens: 610173
actual_roles: "impl 8, review 3"
actual_role_tokens: "impl 511401, review 98772"
---

# helmfile matrix releases

## Requirement

The release pair for the connector (design D13, D15, revision R1). Paths are in code/agents-helmfile.

Preconditions, checked first: (a) this epic's agents-matrix-connector PR is merged to main and chart `oci://harbor.szymonrichert.pl/charts/agents-matrix-connector` `0.1.0-main.<sha7>` and image `<sha7>` exist (the orchestrator amends `<sha7>` in); otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-matrix-connector PR and wait for its main CI". (b) Hermes runs 0 replicas (read-only `kubectl -n ai get deploy hermes-agent`, after the infrastructure helmfile MR that scales Hermes to 0 is merged); otherwise end `blocked`, whoCanClear "orchestrator: merge the Hermes scale-to-0 MR in the infrastructure helmfile".

- `helmfile.yaml.gotmpl`: `agents-matrix-connector-db` (`cnpg/cluster`, the version and options of `agents-webhook-db`) and `agents-matrix-connector` (OCI chart pinned `0.1.0-main.<sha7>`, `needs: [agents/agents-matrix-connector-db, agents/agents-orchestrator]`), namespace `agents`, labels `application: agents-matrix-connector`; the agents-orchestrator release's values gain `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`.
- `values/agents-matrix-connector-db/common.yaml`: initdb database and owner `agents_matrix_connector`, storage and backups as `agents-webhook-db` with its own backup path.
- `values/agents-matrix-connector/common.yaml`: `image.tag <sha7>`; `postgres.existingSecret: agents-matrix-connector-db-cluster-app`, key `uri`; `orchestrator.url: http://agents-orchestrator-services:8002`; `matrix.homeserverUrl: http://matrix-synapse.messaging.svc.cluster.local:8008`; `matrix.userId: "@hermes:szymonrichert.pl"`; `matrix.deviceId: hermes-agent`; `matrix.selfIdentities: ["@facebook_61594633049360:szymonrichert.pl"]`; `matrix.bridgeBots: ["@facebookbot:szymonrichert.pl"]`; `policy.default: deny`; `components.api.podAnnotations`: the same oauth2-proxy annotations as the agents-webhook api; `components.bot.podAnnotations: {}`; `ingress`: enabled, host `lab.szymonrichert.pl`, the shared TLS secret the agents-webhook api ingress uses, no cert-manager annotation, the same node-IP `denySourceRanges` as the agents-webhook api ingress.
- `tests/test_matrix_connector_release.py` (offline, reading the layered values as the existing release tests do): pins agree; the DB secret name matches the CNPG release; SSO annotations on the api pod only; the orchestrator URL is the services Service; the homeserver URL, user id, self identities and bridge bots are set; the policy is deny; the ingress host, TLS secret and source ranges match the agents-webhook api's; the orchestrator release reads the connector's token-hash file; no plaintext secret in common values; a test that needs `helmfile build` is named `test_*_helmfile_build`.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: the connector and its database are declared with the pinned chart and needs [evidence: test:tests/test_matrix_connector_release.py::test_matrix_connector_pin_and_needs]
- AC2: database, orchestrator and homeserver wiring, the bot identity and default deny are set [evidence: test:tests/test_matrix_connector_release.py::test_wiring_identity_and_policy]
- AC3: SSO annotations are on the api pod only and the ingress matches the webhook api's host, TLS and source ranges [evidence: test:tests/test_matrix_connector_release.py::test_sso_and_ingress]
- AC4: the orchestrator release reads the connector's token-hash file and no plaintext secret is in common values [evidence: test:tests/test_matrix_connector_release.py::test_token_hash_wired_and_no_plaintext]
- AC5: the offline release tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-matrix-connector/common.yaml`
- `values/agents-matrix-connector-db/common.yaml`
- `tests/test_matrix_connector_release.py`

## Interfaces

- Consumes contracts `agents-matrix-connector-chart`, `agents-matrix-connector-image`, `matrix-connector-settings-env`, `orch-service-tokens`, `orch-services-service`.

## Expected outcome

`mise run diff` (run later by apply-smoke-matrix) shows the two new releases and the orchestrator's added token hash.

## Steps

- Red: `tests/test_matrix_connector_release.py` with the four tests. Fails: no releases.
- Green: edit the helmfile and write the values. Run the verify.

## Notes

- Same shape as agents-webhook-microservice task helmfile-webhook-releases; copy the oauth2-proxy annotations and source ranges from `values/agents-webhook/common.yaml` rather than retyping them.
- No NetworkPolicy exists in `agents` or `messaging` (probed 2026-10-25); none is added.
- 2026-10-25 split: depends_on mxc-dockerfile-and-ci, mxc-chart-network, mxc-e2e-api, mxc-operations-docs live in epic agents-matrix-connector; that epic is a blocker of this one, so they are done before this task runs.

- 2026-10-25 amended: revision R1 (user 2026-10-25): the connector takes over Hermes' Matrix user and Facebook account, Hermes scaled to 0; only the Hermes home-channel owner DM is allowed

- 2026-10-26 done
