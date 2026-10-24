# agent init scripts design

## Summary

Clusters and presets gain `init_scripts`, a list of shell scripts. The reconciler runs them exactly once per cluster as one Job on the shared workdir and records the run in `clusters.status.init`; agent sessions start after it. The agent sees how it was initialised through `.agent-init/init.sh` and `init.log` in its workdir and the `orchestrator_init_scripts_get` tool, and edits them with `orchestrator_init_scripts_edit`, which writes the cluster's stored spec and its source preset, so the next cluster runs the new list. Every capability has a documented public route, an API-only e2e test, and UI (preset form rows, a cluster "Init scripts" dialog). The release is the orchestrator main merge, then a helmfile pin, apply and an extended smoke.

Binding architecture: the foundation decisions of 2026-10-24 (D1-D6 there; its D5 is this epic). The shared parts F1-F5 (orchestrator any-mcp plugin with the init tools, agent API socket and `require_agent()`, token, render gating, hash pin test) are built by hive-mode-leadership-handove; this epic consumes them and builds none of them.

## Intent and why

User request (2026-10-24): init scripts must be exposed to an agent that was initialised with them, so it knows how it was initialised and can edit them for next time, and they run once per cluster. Today only the wrapper's per-pod `init.setup_commands` exist, which run per session, not per cluster. An agent that can read and improve its environment recipe makes each new cluster from a preset better than the last.

## Goals

- `ClusterSpec.init_scripts` exists, is valid in presets, and is snapshotted into a cluster created from a preset.
- A cluster with scripts runs them once (one Job, never again for that cluster: not per pod, not per restart, not after scaling, not after an edit); a cluster without scripts records `skipped` and never runs any later.
- Sessions start only after the run ends; a failed run starts sessions anyway with phase `degraded` and message `init failed`.
- The agent can read the scripts, the run state and the log (tool and workdir files) and can edit the scripts; an edit writes the cluster spec and the source preset (when one exists, the Default preset included), never rolls a pod and never re-runs.
- Public routes `GET|PUT /api/v1/clusters/{id}/init-scripts` are documented and covered by an API-only kind e2e; the UI edits scripts in presets and shows and edits them per cluster.
- The live `agents` namespace runs the build, proven by the smoke.

## Non-goals

- Re-running init on a running cluster, or a "run again" button.
- Per-pod setup (the wrapper's `init.setup_commands` stays as it is).
- Changes to any-mcp or claude-code-wrapper: the plugin tools and the main-agent-only gate come from hive F1 and F2.
- Secrets for the Job beyond `spec.env`.

## Anti-goals

- An init-scripts edit or the field itself changing the rendered ConfigMap, Secret or pod template (it would roll every agent; the hash pin test guards it).
- Init running twice for one cluster, or racing across pods.
- A cluster stuck forever because a script failed.
- A second writer of `clusters` or `presets` (both stay api-written; `status` stays reconciler-written).

## Constraints

- Single writer per table: `clusters.spec`/`presets.spec` by the api process only; `clusters.status` by the reconciler only.
- Spec immutability rule (MEMORY 2026-10-23) with the foundation D4 exception: `spec.replicas` and `spec.init_scripts` are mutable in place without a generation bump; PATCH stays 405.
- The api never imports `k8s` or the wrapper (`tests/test_api_clusters.py::test_api_never_imports_k8s_or_wrapper`).
- Every route, frame and table is in README, openapi.json and schema.d.ts (`tests/test_readme_api.py`).
- Executes after the hive foundation tasks it needs (F1, F3, F4) are on main (README blocker).
- Python only except the TypeScript frontend; theme tokens only in the UI.

## Decisions

### D1: init_scripts is a ClusterSpec field, never rendered
`ClusterSpec.init_scripts: list[str] = []`, at most 20 entries, each non-empty and at most 16384 characters, in `spec.py` with `INIT_DIR = ".agent-init"` and `init_scripts_hash()` (sha256 of compact JSON) as the one shared definition. Presets store ClusterSpec, so they get it for free (sparse). The field never reaches a rendered object; the hive hash pin test is extended to vary it. Alternatives: a separate table (rejected: duplicates the spec, precedence rules in every reader); scripts in the ConfigMap (rejected: every edit rolls all pods). Limits are (my call). Serves A1, C1.

### D2: once per cluster is a reconciler Job recorded in status.init
Foundation D5. `reconciler/init.py` creates Job `agent-<slug>-init` (agent image, cluster PVC with the workdir mount, uid 1000, `spec.env`, agent resources, backoffLimit 0, 30 min deadline) on the first converge that sees non-empty scripts and no `status.init`; the first converge with empty scripts writes `skipped`, so a later edit never triggers a run on that cluster (my call: closes the hole where "no status.init" plus an edit would run scripts mid-life). State `{state skipped|running|succeeded|failed, scripts_hash, started_at, finished_at, exit_code, log_tail, reason, job}` is written before the create, `job` after it, mirroring checks crash safety. The Job is deleted after its outcome is recorded and has no TTL (my call: a TTL could expire before an offline reconciler reads the outcome). Sessions are held while `status.init` is absent or `running` (phase `pending`, `init running`); `failed` starts them with phase `degraded`, `init failed`. Alternatives: a marker on the RWX PVC from the first pod (rejected: mkdir race and wait loops under Parallel pods); wrapper `init.setup_commands` with a marker (rejected: per session dir, so per pod); block agents on failure (rejected: a stuck cluster cannot self-repair). Pod-local installs by a script do not reach agent pods; only the shared workdir is shared (README and the tool description say so). Serves C1.

### D3: exposure through workdir files and the agent route
The Job writes `<workdir>/.agent-init/init.sh` (the scripts as run, under a header that says edits apply to the next cluster), `init.log` and a `.gitignore` of `*` (my call: keeps the agent's repo status clean). `GET /agent/v1/init-scripts` returns the scripts, the run state, `edited_since_run`, the preset and both file paths; the hive F1 tool `orchestrator_init_scripts_get` calls it and its description names the file path and the next-cluster semantics (Q7: awareness from tool descriptions, no CLAUDE.md fragment). Serves C2.

### D4: an edit writes the cluster spec and its source preset in one transaction
`db/clusters.set_init_scripts` locks the clusters row, then the preset row, sets both `spec.init_scripts` (no generation bump, NOTIFY `cluster_changed`) and reports whether a preset was written. A missing or deleted preset (`preset_id` null) writes only the cluster. The Default preset is written like any other source preset (C3 to the letter, my call on reading "when there is one"). The running cluster never re-runs; `edited_since_run` (hash differs from `status.init.scripts_hash`) surfaces it in views. Any agent of the cluster may edit; subagents are refused by the hive-rendered `claude.main_agent_only_tools` gate. Serves C3.

### D5: public routes, view flag and UI
`GET|PUT /api/v1/clusters/{id}/init-scripts` (InitScriptsView), `ClusterView.init_edited_since_run`, README H3s, openapi and schema. UI: preset form "Init scripts" rows (create and edit presets; clusters are created from presets in the UI) and a cluster "Init scripts" dialog from the TopBar cluster menu showing the run and editing the scripts through the public route. Serves A1, X2.

### D6: consume the hive foundation, register only this epic's contracts
The plugin tools (F1), the agent socket and `require_agent()` (F4), the token and env (F3/F4) and the hash pin test (F3) are used, not rebuilt. This epic adds two agent routes in `api/agent.py` and a parity test that runs the pinned `OrchestratorPlugin` init tools against them; a mismatch is reported against hive F1, not patched in any-mcp here. No any-mcp or wrapper release. Serves X1.

### D7: release, pin, apply and smoke are tasks
The orchestrator release is the merge of this epic's PR to main (CI publishes chart `0.1.0-main.<sha7>` and the image; no chart version bump). agents-helmfile pins that build, the smoke creates its cluster with an init script, picks the agent pod by name (the init Job pod carries the cluster label) and checks `status.init` succeeded, then `mise run apply` and `mise run smoke` run against the live namespace. Serves A2.

### D8: API-only kind e2e
Run once with files in every pod, edit through the public and the agent route writing cluster and preset with no pod roll and no re-run, failure starting sessions degraded, and skipped; agent routes via `kubectl exec` with the pod's token (the fake claude cannot call MCP tools). Serves X2.

### D9: C1 init scripts field, once per cluster
Init scripts are new: ClusterSpec + preset field; run once per cluster (not per pod, not per restart). (user decision)

### D10: C2 exposed to the agent
Exposed to the agent initialised with them, so it knows how it was initialised. (user decision)

## Research

| Lens | Status | Adopted | Rejected |
|---|---|---|---|
| code-internal | ran (brief-orchestrator.md, brief-wrapper-anymcp.md) | checks-as-Jobs shape (`reconciler/checks.py`), merging `_write_status` (`reconciler/loop.py:500`), session gate (`loop.py:238-249`), preset sparse spec (`api/presets.py:42-54`) | wrapper `init.setup_commands` (per pod, `workdir.py:149-170`), PVC marker (race) |
| architecture | ran (foundation.md D5) | Job plus status.init, api-written spec field | separate runtime table, generation bump |
| external, papers, docs | skipped: no new library; Kubernetes Job semantics already used by checks | | |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| brief-orchestrator C plan inputs | spec + preset field, bounded size | init-scripts-spec-field |
| brief-orchestrator C plan inputs | one init Job modelled on checks, status.init, session gate | init-job-runner |
| brief-orchestrator C risk 1 | keep scripts out of config.yaml and on-start.sh | init-scripts-spec-field (hash pin) |
| brief-orchestrator C risk 2 | narrow api-written exception to immutability | init-scripts-public-api |
| brief-orchestrator C risk 3 | pod-local installs not shared | init-job-runner (README, MEMORY) |
| brief-orchestrator C risk 4 | Job lacks spec.env | init-job-runner |
| brief-orchestrator C risk 5 | preset deleted since (preset_id null) | init-scripts-public-api |
| brief-wrapper-anymcp init plan inputs | do not reuse init.setup_commands | rejected: per pod (D2) |
| brief-wrapper-anymcp init plan inputs | init_scripts_get / init_scripts_edit tools in the plugin | do-not-build here: hive F1; parity test in init-scripts-agent-api |
| brief-wrapper-anymcp init risks | preset blast radius of agent edits | D4 (C3 to the letter, Default included) |
| foundation D5 | Job, status.init, exposure, edit, edited-since-run | init-job-runner, init-scripts-public-api, init-scripts-agent-api |
| smoke.sh pod selection by label | init Job pod carries the cluster label | smoke-init-scripts |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 init_scripts field, never rendered | init-scripts-spec-field, fe-preset-init-scripts |
| D2 once per cluster Job and status.init | init-job-runner, init-scripts-kind-e2e |
| D3 exposure through files and agent route | init-job-runner, init-scripts-agent-api |
| D4 edit writes cluster and preset | init-scripts-public-api, init-scripts-agent-api |
| D5 public routes, view flag, UI | init-scripts-public-api, fe-preset-init-scripts, fe-cluster-init-dialog |
| D6 consume hive foundation | init-scripts-agent-api |
| D7 release, pin, apply, smoke | smoke-init-scripts, deploy-pin-init-scripts, apply-smoke-init-scripts |
| D8 API-only kind e2e | init-scripts-kind-e2e |
| D9 C1 init scripts field, once per cluster | init-scripts-spec-field, init-job-runner, init-scripts-kind-e2e |
| D10 C2 exposed to the agent | init-job-runner, init-scripts-agent-api |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `orch-cluster-spec-init-scripts` | init-scripts-spec-field | init-job-runner, init-scripts-public-api, fe-preset-init-scripts | `code/agent-orchestrator/src/agent_orchestrator/spec.py` |
| `orch-cluster-status-init` | init-job-runner | init-scripts-kind-e2e | `code/agent-orchestrator/src/agent_orchestrator/reconciler/init.py` |
| `orch-init-workdir-files` | init-job-runner | init-scripts-kind-e2e | `code/agent-orchestrator/src/agent_orchestrator/reconciler/init.py` |
| `orch-cluster-init-scripts-api` | init-scripts-public-api | init-scripts-agent-api, fe-cluster-init-dialog, init-scripts-kind-e2e | `code/agent-orchestrator/README.md` |
| `orch-agent-init-scripts-api` | init-scripts-agent-api | init-scripts-kind-e2e | `code/agent-orchestrator/src/agent_orchestrator/api/agent.py` |

Outside this epic's tasks: the agents-helmfile smoke (smoke-init-scripts) reads `orch-cluster-status-init` and `orch-cluster-init-scripts-api` over HTTP against the deployed build; the hive F1 plugin tools and description consume `orch-agent-init-scripts-api` and `orch-init-workdir-files` (registered with consumer any-mcp).

Consumed from hive-mode-leadership-handove (not rebuilt): `/agent/v1` auth and `require_agent()`, `ORCH_AGENT_TOKEN`/`ORCH_AGENT_URL`/`ORCH_CLUSTER_ID` pod env, `OrchestratorPlugin` tools `orchestrator_init_scripts_get|edit` (any-mcp v0.2.0, always in `allow`), wrapper `claude.main_agent_only_tools`, hash invariant test, README `## API` Versioning sentence.

## Review focus

- `reconciler/init.py`: the once guarantee across crashes, the `skipped` rule, the session gate, the Job never pruned by converge and deleted after its outcome.
- `db/clusters.set_init_scripts`: one transaction, lock order clusters then presets, no generation bump, nothing rendered changes.
- Agent routes: only `require_agent()`, cluster from the token, no new auth path.
- The hash pin test must cover `init_scripts`.

## Left to the builder

- The exact shell of the Job wrapper, within: files written as listed, `sh -eu`, the Job's exit code equals the script's.
- UI layout details of the script rows and the dialog, within theme tokens and the existing env-row pattern.
- Whether the checks helpers are renamed public when imported, keeping checks behaviour unchanged.

## Assumptions and unknowns

- Hive F1 builds the init tools against `orch-agent-init-scripts-api` and names `.agent-init/init.sh` in the description; confirmed by the parity test in init-scripts-agent-api.
- Hive F3 lands `test_runtime_fields_change_only_statefulset_replicas`; if named differently on main, init-scripts-spec-field adds `test_init_scripts_never_rendered`.
- `WORKDIR_ROOT` lives in `k8s/render.py`; the api computes paths without importing k8s (probe at build time, the boundary test enforces it).
- Kind e2e runs in PR CI, not in the task container.

## Open questions

none

## Irreversible operations in scope

- `mise run apply` of the agents namespace (task apply-smoke-init-scripts): a live deploy, reversible by re-pinning and re-applying; guarded by lint, test and the kube-context check, preceded by a diff that must show only the orchestrator chart and image changing.
- An agent or user edit writes the source preset, the Default preset included (C3); reversible by another edit.
