---
title: orch-chat-env-scope
status: done
repo: agents-orchestrator
value: "the orchestrator starts with chat enabled: the chat URL and token reach only the api, always together"
files: [chart/agents-orchestrator/templates/configmap.yaml, chart/agents-orchestrator/templates/deployment.yaml, chart/agents-orchestrator/templates/_helpers.tpl, tests/test_chart_config.py, MEMORY.md]
verify: uv run pytest tests/test_chart_config.py -q
depends_on: []
model: sonnet
review: ""
verified_head: df3998301fecec1cf0a757c539bb8a6f423d7130
points: 3
expected_minutes: 6
expected_tokens: 962516
points_actual: 3
actual_minutes: 40
actual_tokens: 1224382
actual_roles: "impl 38, review 2"
actual_role_tokens: "impl 926540, review 297842"
---

# orch-chat-env-scope

## Requirement

Live apply of agents-orchestrator chart 0.1.0-main.37edd58 with chat enabled (agents-helmfile main f4be334, 2026-10-28 21:32Z) failed and helm rolled it back (revision 13 failed, 14 = rollback to 12): the `migrate` init container of every orchestrator Deployment (api, dispatcher, ingester, reconciler) crash-looped. Cause: `templates/configmap.yaml` renders `ORCH_CHAT_URL` into the ConfigMap that every container loads via `configMapRef`, but `templates/deployment.yaml` adds `ORCH_CHAT_TOKEN` (secretKeyRef to the chat Secret) only to the api container; `Settings._check_chat_pair` (settings.py) refuses a URL without its token ("set ORCH_CHAT_URL and ORCH_CHAT_TOKEN together, or neither"), so every process except the api main container fails to start. Evidence: .logs/matrix-deploy-2026-10-28/apply-agents-orchestrator.log and diff-agents-orchestrator.log (one `ORCH_CHAT_TOKEN` env entry).
Fix (my call, least privilege): the chat pair reaches only the containers that serve the chat relay. Render `ORCH_CHAT_URL` and `ORCH_CHAT_TOKEN` together, as env of the api main container only (both the inline-token and the `chat.existingSecret` paths), and never in the shared ConfigMap; the migrate init containers and the dispatcher, ingester and reconciler get neither. First read every template and the settings to confirm no other component needs `chat_url` (for example a reconciler render of agent pods or the plugin config); if one does, give that container the pair too and say why. Test first: a chart test renders with `chat.url` and `chat.token` (and with `chat.existingSecret`) and asserts that every container and init container that has one of the two variables has both, that the api main container has both, and that the ConfigMap has no `ORCH_CHAT_URL`. Record the incident and rule in MEMORY.md with the date and why.

## Acceptance conditions

- AC1: with chat.url and chat.token set, every rendered container and init container carries ORCH_CHAT_URL and ORCH_CHAT_TOKEN together or neither [evidence: test:tests/test_chart_config.py::test_chat_pair_rendered_together_per_container]
- AC2: the api main container carries both chat variables, for the inline token and for chat.existingSecret [evidence: test:tests/test_chart_config.py::test_api_container_has_chat_pair]
- AC3: the shared ConfigMap carries no ORCH_CHAT_URL [evidence: test:tests/test_chart_config.py::test_configmap_has_no_chat_url]
- AC4: MEMORY.md records the failed chat apply and the rule [evidence: command:grep -q "migrate init" MEMORY.md]

## Files

- `chart/agents-orchestrator/templates/configmap.yaml`
- `chart/agents-orchestrator/templates/deployment.yaml`
- `chart/agents-orchestrator/templates/_helpers.tpl`
- `tests/test_chart_config.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done
