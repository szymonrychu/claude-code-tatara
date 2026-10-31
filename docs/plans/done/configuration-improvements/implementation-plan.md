# configuration improvements implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: spec config fields

- Status: done
- Files: `src/agent_orchestrator/spec.py`, `src/agent_orchestrator/settings.py`, `tests/test_spec_config.py`
- Verify: `uv run --frozen pytest -q tests/test_spec_config.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: effa0a3

#### Requirement

Add the create-time configuration fields every other task builds on (design D1, D4, D5, D6; approvals A1, A3, A4). In `src/agent_orchestrator/spec.py`:

- `ClusterSpec.wrapper: WrapperSettings | None = None`, with `extra="forbid"` models that mirror the claude-code-wrapper 0.2.0 shapes (`code/claude-code-wrapper/src/claude_code_wrapper/config.py`; the wrapper is only a dev dependency, so the orchestrator defines its own models): `hooks` (a map whose keys are the 21 wrapper `HOOK_EVENTS`, copied as a module constant, each a list of at most 20 actions; action `command` {run (1..16384 chars), env (keys `[A-Z_][A-Z0-9_]*`)} or `webhook` {url (http or https with a host), secret, headers, retries >= 0}, discriminated by `type`; common keys timeout_seconds > 0, blocking, on_error allow|deny, matcher (compiling regex, only on onAgentToolCall and onToolResult), interval_seconds > 0 and when busy|always (only on onTick, interval required there)); `auto_compact` {idle_seconds >= 0, instructions (one line, no control characters, at most 2000 chars), min_context_tokens >= 0}; `system_append` (at most 16384 chars); `permissions` {allow: list[str], deny: list[str]}; `mcp_servers` (name `[A-Za-z0-9_-]{1,64}`, `any-mcp` refused as reserved; stdio {command, args, env} or http|sse {url, headers}); `plugins` {marketplaces [{name, source}], install [{plugin `name@marketplace`, scope user|project|local, required}], every install marketplace listed or `claude-plugins-official`}; `turn_stall_seconds` >= 0; `max_restarts` 0..10; `restart_continue_prompt`; `turn_max_seconds` >= 0; `agent_commands` (each one of compact, context, mcp, reload-plugins, reload-skills).
- `ClusterSpec.leader_lease_seconds: int | None` (60..604800); a model validator refuses it unless the spec is a hive (`max_replicas > 1`) with the message `leader_lease_seconds requires a hive cluster (max_replicas > 1)`.
- `ClusterSpec.autoclose_after_seconds: int | None` (1..2592000); `validate_spec` refuses a value below `settings.autoclose_min_seconds` with `autoclose_after_seconds <n> is below the minimum <m>`.

In `src/agent_orchestrator/settings.py` add `autoclose_min_seconds: int = 300` (env `ORCH_AUTOCLOSE_MIN_SECONDS`, >= 1). Validation errors name the field path (for example `wrapper.hooks.onTick.0.interval_seconds`). Unset fields dump to nothing (`model_dump(exclude_none=True)`), so presets stay sparse. The fields are create-time only: no new in-place spec writer; MEMORY's list of runtime-mutable fields stays `replicas` and `init_scripts`.

#### Acceptance conditions

- AC1: a wrapper block with every key of design D1 validates and round-trips through model_dump(exclude_none=True) unchanged [evidence: test:tests/test_spec_config.py::test_wrapper_block_round_trips]
- AC2: unknown hook event, matcher outside the tool events, onTick without interval_seconds, interval_seconds or when outside onTick, a non-http webhook url and more than 20 actions are refused, each naming its field path [evidence: test:tests/test_spec_config.py::test_hook_rules_refused]
- AC3: multi-line or over-long auto_compact instructions, an any-mcp MCP server name, a plugin from an unlisted marketplace and an unknown agent command are refused [evidence: test:tests/test_spec_config.py::test_wrapper_value_rules_refused]
- AC4: leader_lease_seconds is accepted from 60 to 604800 on hive specs only, and validate_spec refuses autoclose_after_seconds below settings.autoclose_min_seconds (default 300, overridden by ORCH_AUTOCLOSE_MIN_SECONDS) [evidence: test:tests/test_spec_config.py::test_lease_and_autoclose_bounds]
- AC5: a spec without the new fields dumps none of their keys, so presets stay sparse [evidence: test:tests/test_spec_config.py::test_unset_fields_stay_sparse]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/spec.py`
- `src/agent_orchestrator/settings.py`
- `tests/test_spec_config.py`

#### Interfaces

Builds part `orch-spec-config-fields` (`spec.py::WrapperSettings`, `ClusterSpec.wrapper`, `ClusterSpec.leader_lease_seconds`, `ClusterSpec.autoclose_after_seconds`, `Settings.autoclose_min_seconds`), used by render-wrapper-settings, leader-lease-expiry, autoclose-sweeper and config-cluster-views. Adds env name `ORCH_AUTOCLOSE_MIN_SECONDS` to contract `agent-orchestrator-settings-env`.

#### Expected outcome

`ClusterSpec` accepts `wrapper`, `leader_lease_seconds` and `autoclose_after_seconds` with named validation errors, and `ORCH_AUTOCLOSE_MIN_SECONDS` sets the autoclose floor (default 300).

#### Steps

- Red, write `tests/test_spec_config.py` with the five tests named in the acceptance conditions and run `uv run --frozen pytest -q tests/test_spec_config.py` (fails on unknown fields)
- Green, add the models, fields and setting
- Run the verify command.

#### Notes

Follow the existing `_env` and `_hook_url` validator style in `spec.py`. The `_cap` validator resolves `max_replicas` first, so the lease validator runs after it. Postgres-backed tests need Docker; these tests are pure model tests.

- 2026-10-25 done

### S2: autoclose sweeper

- Status: done
- Files: `src/agent_orchestrator/db/clusters.py`, `src/agent_orchestrator/api/autoclose.py`, `src/agent_orchestrator/api/app.py`, `tests/test_autoclose.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q tests/test_autoclose.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: a95909b

#### Requirement

Close clusters whose autoclose time has come, through the existing discard path (design D5; approval A4). 

- `src/agent_orchestrator/db/clusters.py`: `close_expired(conn) -> list[uuid.UUID]` runs one statement, `UPDATE clusters SET desired = 'deleting', generation = generation + 1 WHERE desired = 'active' AND spec ? 'autoclose_after_seconds' AND created_at + make_interval(secs => (spec->>'autoclose_after_seconds')::int) <= now() RETURNING id`, and NOTIFYs `cluster_changed` for each id in the same transaction (the same write `request_delete` makes). It writes no other column.
- `src/agent_orchestrator/api/autoclose.py`: `AUTOCLOSE_POLL_SECONDS = 10` (module constant) and a sweeper coroutine that calls `close_expired` every poll until stopped, logging each closed cluster id and surviving a failed pass (logged, retried next poll).
- `src/agent_orchestrator/api/app.py`: the lifespan starts the sweeper after the listener and cancels it cleanly on shutdown.

The reconciler is unchanged: it discards `deleting` clusters as today (quiesce, discard hook export, delete objects, purge). The api stays the only writer of `clusters.desired`; several api replicas are safe because the update is status-guarded.

README.md: `### Autoclose` under `## Discard`: the field, counted from `created_at`, the floor `ORCH_AUTOCLOSE_MIN_SECONDS` (default 300), the poll lag (about 10 s), that it is the same discard as `DELETE /api/v1/clusters/{id}` (discard hook export included, no handoff turn), and the single-writer table note that the api sweeper writes `desired`. MEMORY.md: a dated entry for choosing the api sweeper over a derived predicate or a reconciler write, with the why.

#### Acceptance conditions

- AC1: close_expired flips only active clusters past created_at plus autoclose_after_seconds to deleting with generation plus one, notifies cluster_changed, and leaves clusters without the field, not yet due or already deleting untouched, with no other column written [evidence: test:tests/test_autoclose.py::test_close_expired_flips_only_due_clusters]
- AC2: two concurrent close_expired calls flip each due cluster exactly once [evidence: test:tests/test_autoclose.py::test_close_expired_is_idempotent]
- AC3: the api lifespan runs the sweeper, a due cluster becomes deleting within one poll, and shutdown cancels the sweeper cleanly [evidence: test:tests/test_autoclose.py::test_sweeper_runs_in_api_lifespan]
- AC4: README documents autoclose and the single-writer note [evidence: doc-section:README.md#Autoclose]
- AC5: MEMORY.md records the writer choice with the date and why [evidence: judgement:MEMORY.md entry reviewed]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/db/clusters.py`
- `src/agent_orchestrator/api/autoclose.py`
- `src/agent_orchestrator/api/app.py`
- `tests/test_autoclose.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

Builds part `orch-cluster-autoclose` (`db/clusters.py::close_expired`, `api/autoclose.py::AUTOCLOSE_POLL_SECONDS`); uses `orch-spec-config-fields`.

#### Expected outcome

A cluster with `autoclose_after_seconds` turns `deleting` within about 10 s of its deadline and is discarded exactly as by `DELETE /api/v1/clusters/{id}`.

#### Steps

- Red, write `tests/test_autoclose.py` (backdate `created_at` with SQL; LISTEN on `cluster_changed`; two concurrent calls for the idempotence test; the app lifespan with a short poll patched in)
- Green, implement
- Run the verify command.

#### Notes

Decisions are in design.md; nothing beyond the requirement.

- 2026-10-25 done

### S3: config cluster views

- Status: done
- Files: `src/agent_orchestrator/api/schemas.py`, `src/agent_orchestrator/db/views.py`, `src/agent_orchestrator/api/clusters.py`, `README.md`, `openapi.json`, `tests/test_api_config.py`
- Verify: `uv run --frozen pytest -q tests/test_api_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 368c8b7

#### Requirement

Document and expose the new fields through the public API (design D9, D11; approvals A1, A3, A4, A6).

- `src/agent_orchestrator/api/schemas.py`: `ClusterView` adds `closes_at: datetime | None` (`created_at + autoclose_after_seconds`, null when unset), `leader_since: datetime | None` and `leader_reason: str | None` (from `cluster_leaders`, null without a leader).
- `src/agent_orchestrator/db/views.py` (the aggregates query) and `src/agent_orchestrator/api/clusters.py` (the view builder) fill them.
- The create and preset routes already validate `ClusterSpec` through `check_spec` and `validate_spec`; a refused new field answers 422 `invalid_request` whose message names the field, on `POST /api/v1/clusters`, `POST /api/v1/presets` and `PUT /api/v1/presets/{id}`, and a cluster created from a preset snapshots the preset's new fields.
- README.md: `### Cluster configuration` under `## API` documenting `spec.wrapper` (every key of design D1, its wrapper config path, the reserved entries and the `$` escaping), `leader_lease_seconds`, `autoclose_after_seconds`, `ORCH_AUTOCLOSE_MIN_SECONDS`, the three view fields and the refusal messages; the `POST /api/v1/clusters` field list and the ClusterView field list name the new fields.
- Regenerate `openapi.json` with `uv run python -m agent_orchestrator.api.openapi > openapi.json`.

#### Acceptance conditions

- AC1: a spec with a full wrapper block, a lease and an autoclose round-trips through POST /api/v1/clusters, the preset routes, and a cluster created from that preset [evidence: test:tests/test_api_config.py::test_config_fields_round_trip_through_presets_and_clusters]
- AC2: a bad hook, a lease on a single-agent spec and an autoclose below the floor answer 422 invalid_request naming the field on the cluster and preset routes [evidence: test:tests/test_api_config.py::test_config_fields_refused_with_named_errors]
- AC3: the cluster view shows closes_at as created_at plus autoclose_after_seconds or null, and leader_since and leader_reason from the leader row or null [evidence: test:tests/test_api_config.py::test_cluster_view_lease_and_autoclose_fields]
- AC4: README documents the cluster configuration fields for API callers [evidence: doc-section:README.md#Cluster configuration]
- AC5: openapi.json is regenerated and matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/db/views.py`
- `src/agent_orchestrator/api/clusters.py`
- `README.md`
- `openapi.json`
- `tests/test_api_config.py`

#### Interfaces

Builds part `orch-cluster-config-api` (README `### Cluster configuration` and the ClusterView fields; consumed by kind-e2e-config, web-form-config-fields, web-clusters-page and smoke-config-check); uses `orch-spec-config-fields` and the contracts `orch-presets-api` and `orch-cluster-create-api`.

#### Expected outcome

`GET /api/v1/clusters/{id}` shows the new spec fields plus `closes_at`, `leader_since` and `leader_reason`; README `### Cluster configuration` documents them; openapi.json is current.

#### Steps

- Red, write `tests/test_api_config.py` with the three tests
- Green, add the view fields and docs
- Regenerate openapi.json
- Run the verify command.

#### Notes

After frontend-decoupling the orchestrator repo has no `frontend/`, so no `schema.d.ts` is regenerated here; agents-web syncs its vendored copy in web-form-config-fields. `leader_reason` is set by test SQL here; the lease task produces `lease_expired` in production.

- 2026-10-25 done

### S4: leader lease expiry

- Status: done
- Files: `src/agent_orchestrator/db/leadership.py`, `tests/test_leadership_pass.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q tests/test_leadership_pass.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 7c02669

#### Requirement

Hand leadership over when a leader's lease runs out (design D4; approval A3; user decision and the hive "handover only, no takeovers" rule). In `src/agent_orchestrator/db/leadership.py`:

- `_CANDIDATES` adds clusters whose spec sets `leader_lease_seconds` and whose `cluster_leaders.since` is older than `now() - leader_lease_seconds` (database clock).
- `leadership_pass` gets step 4, after the lost-leader step and inside the same claim-lock transaction: when the spec sets `leader_lease_seconds`, the leader's term (`since`) is older than the lease, the leader is ready and not gone, the leader is at a turn boundary (its `agent_status.state` is `idle` and no `messages` row with its `agent_id` is `dispatching` or `verifying`), and `_free_longest(conn, cluster_id, leader)` finds another ready agent, then `_set_leader(conn, cluster_id, picked, "lease_expired")` moves leadership (epoch + 1, `since = now()`, NOTIFY `leader_changed`; the existing push loop sends `hive_state`). A busy leader keeps leadership and is handed over on the first pass after its turn ends. With no ready peer the leader stays, nothing is written, and the lease is re-checked on every pass. A leader chosen by a queued request in step 2 starts a fresh term. Nothing is interrupted, no message is re-routed, and no agent can trigger the change: it is a handover of the current leader's term, never a takeover.
- `LEADER_GRACE_SECONDS` stays the module constant 30 (hive D14).

README.md: `### Leader lease` under the hive `### Leadership` section: the field, the turn-boundary rule, reason `lease_expired`, the no-peer rule, and that clusters without the field keep today's indefinite leadership. MEMORY.md: a dated entry recording that the lease amends hive D26 ("no forced handover") for clusters that set `leader_lease_seconds`, keeps D21 (no takeovers), and why.

#### Acceptance conditions

- AC1: an idle leader past its lease is replaced by the ready agent free the longest, with reason lease_expired, epoch plus one, a new since and a leader_changed notification [evidence: test:tests/test_leadership_pass.py::test_lease_expiry_hands_over_idle_leader]
- AC2: a leader that is busy, or has a dispatching or verifying message, keeps leadership past its lease and is handed over on the first pass after it is idle [evidence: test:tests/test_leadership_pass.py::test_lease_waits_for_turn_boundary]
- AC3: with no other ready agent the leader stays and the epoch does not change [evidence: test:tests/test_leadership_pass.py::test_lease_without_peer_keeps_leader]
- AC4: a cluster with an expired lease is a leadership candidate, and a cluster without leader_lease_seconds never rotates [evidence: test:tests/test_leadership_pass.py::test_lease_candidates]
- AC5: a queued handover in the same pass is judged first and its new leader starts a fresh term [evidence: test:tests/test_leadership_pass.py::test_queued_handover_before_lease]
- AC6: LEADER_GRACE_SECONDS stays the module constant 30 [evidence: command:grep -qx 'LEADER_GRACE_SECONDS = 30' src/agent_orchestrator/db/leadership.py]
- AC7: README documents the leader lease [evidence: doc-section:README.md#Leader lease]
- AC8: MEMORY.md records the amendment of hive D26 for opted-in clusters, with the date and why [evidence: judgement:MEMORY.md entry reviewed]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/db/leadership.py`
- `tests/test_leadership_pass.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

Builds part `orch-leader-lease` (reason `lease_expired` in `cluster_leaders.reason`); uses `orch-spec-config-fields` and the hive contract `orch-leadership-pass`.

#### Expected outcome

In a hive with `leader_lease_seconds`, the cluster view shows a new leader with `leader_reason` `lease_expired` shortly after the lease runs out and the old leader's turn ends.

#### Steps

- Red, add the five tests to `tests/test_leadership_pass.py` (backdate `cluster_leaders.since` with SQL; set `agent_status.state` and a `dispatching` message for the busy case)
- Green, implement step 4 and the candidate clause
- Run the verify command.

#### Notes

The dispatcher runs `_drain_leadership` on every wake, at least every `dispatch_poll_seconds`, so no new timer is needed. Draining agents from cluster-scaling are never ready, so `_free_longest` never picks them. Concurrency-sensitive: keep every read inside the pass's transaction and lock.

- 2026-10-25 done

### S5: render wrapper settings

- Status: done
- Files: `src/agent_orchestrator/k8s/render.py`, `tests/test_render.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: b655a64

#### Requirement

Render `spec.wrapper` into the claude-code-wrapper config (design D2, D3; approvals A1, A2). In `src/agent_orchestrator/k8s/render.py:_ccw_config`:

- Reserved entries stay first and cannot be removed: user `hooks.onStart` actions are appended after the rendered `sh /etc/ccw/on-start.sh` entry; user `hooks.onAgentToolCall` actions are appended after `_lock_check_hook()` when it is rendered; every other user hook event becomes its own list; `claude.permissions.deny` is `EnterPlanMode, ExitPlanMode, AskUserQuestion` followed by the user denies not already listed; `claude.permissions.allow` is the user allow list; user `mcp_servers` are added beside `any-mcp`; `prompts.system_append` is `ASK_IN_WRITING_PROMPT`, a blank line, then the user text.
- Mapping: `auto_compact` to `sessions.auto_compact`, `turn_stall_seconds`, `max_restarts`, `restart_continue_prompt` to `sessions.*`, `agent_commands` to `sessions.commands.agent`, `turn_max_seconds` to `limits.turn_max_seconds`, `plugins` to `plugins`. The rendered `sessions` keys `max_sessions`, `resume_on_start`, `idle_timeout_seconds` and `ask_user_question` stay as today.
- Escaping (user decision): every string value that comes from `spec.wrapper` (lists and nested values included, mapping keys excluded because the wrapper never interpolates keys) has each `$` replaced by `$$`, so `claude_code_wrapper.interpolation.interpolate` yields the user's literal text and a command hook's shell still sees `$VAR` at run time. Rendered orchestrator values (`${CCW_AUTH_TOKEN}`, the lock-check headers) are not escaped.
- A spec without `wrapper` renders exactly the config it renders today.

README.md: under `## Security` add `### Hooks and credentials`: command hooks run `sh -c` in the agent pod with the wrapper's full environment (`CLAUDE_CODE_OAUTH_TOKEN`, `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN`, `ORCH_AGENT_TOKEN`); whoever edits a preset can already run code through terminals and init scripts; a webhook `secret` and headers are stored in the spec in plain text and returned by the API; `${VAR}` interpolation is disabled for every user value. MEMORY.md: a dated entry for the escaping rule and the reserved-first order, with the why.

#### Acceptance conditions

- AC1: reserved entries survive and stay first: the on-start hook, the lock-check hook, the three built-in denies, the any-mcp server and the ASK_IN_WRITING prompt, with user entries after them [evidence: test:tests/test_render.py::test_wrapper_settings_keep_reserved_entries]
- AC2: a ${CLAUDE_CODE_OAUTH_TOKEN} placed in a webhook url, a header, a command run, auto-compact instructions and system_append renders escaped and interpolates back to the literal text [evidence: test:tests/test_render.py::test_user_strings_escaped_against_interpolation]
- AC3: every wrapper settings key lands at its wrapper config path [evidence: test:tests/test_render.py::test_wrapper_settings_mapped]
- AC4: a config rendered from a full wrapper block loads with the wrapper's own load_config [evidence: test:tests/test_render.py::test_rendered_wrapper_settings_validate]
- AC5: a spec without a wrapper block renders the same config as before [evidence: test:tests/test_render.py::test_no_wrapper_block_renders_unchanged]
- AC6: README documents the hook credential exposure [evidence: doc-section:README.md#Hooks and credentials]
- AC7: MEMORY.md has a dated entry for the escaping rule and the reserved-first order [evidence: judgement:MEMORY.md entry reviewed]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agent_orchestrator/k8s/render.py`
- `tests/test_render.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

Uses part `orch-spec-config-fields`; keeps contract `orch-render-hash-invariant` (the new fields are create-time, so the config hash changes only with the spec).

#### Expected outcome

A cluster whose spec sets `wrapper` gets a wrapper config.yaml with its hooks and settings after every reserved entry, every user `$` doubled, and the wrapper accepts it.

#### Steps

- Red, add the five tests to `tests/test_render.py` (the escaping test calls the wrapper's `interpolate` with an env holding `CLAUDE_CODE_OAUTH_TOKEN=secret` and asserts the literal `${CLAUDE_CODE_OAUTH_TOKEN}` text comes back)
- Green, implement in `_ccw_config` with one recursive escape helper over the user subtree
- Run the verify command.

#### Notes

The existing `test_rendered_ccw_config_validates` shows how to load the rendered YAML with the wrapper's `load_config`; extend that pattern for a full wrapper block. Highest-risk surface: credentials. Keep the helper pure.

- 2026-10-25 done

### S6: kind e2e config

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`, `e2e/values-kind.yaml`
- Verify: `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: bcd6c9d

#### Requirement

Prove each capability on a real cluster through the API only (design D6, D9; approval A6). In `tests/e2e/test_e2e_kind.py` add three tests under the `e2e` marker, each creating its own cluster through `POST /api/v1/clusters` and deleting it in teardown:

- `test_wrapper_hook_and_idle_compact`: spec `wrapper` with an `onTurnComplete` command hook `echo "$POD_NAME" > hook-ran.txt` and `auto_compact {idle_seconds: 5}`; send one message, wait for its turn to finish, read `hook-ran.txt` through `GET /api/v1/clusters/{id}/files/content` and assert it holds the agent's pod name (proving the hook ran and the escaped `$` reached the shell); then assert a `compacted` event appears through `GET /api/v1/clusters/{id}/events?types=compacted` within a bounded wait.
- `test_leader_lease_hands_over`: a two-agent hive with `leader_lease_seconds: 60`; record `leader_agent_id` and `leader_epoch`, wait (bounded at 180 s) until the view shows another leader, a higher epoch and `leader_reason` `lease_expired`.
- `test_autoclose_discards_cluster`: `autoclose_after_seconds: 30`; the view shows `closes_at` equal to `created_at + 30 s`; within a bounded wait the cluster is `deleting` and then `GET` answers 404.

`e2e/values-kind.yaml` sets `ORCH_AUTOCLOSE_MIN_SECONDS: "30"`. Every wait is bounded and fails with a named message.

#### Acceptance conditions

- AC1: the three new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: the hook test proves a command hook ran with the shell seeing $POD_NAME and an idle compact happened, through the files and events APIs only [evidence: judgement:tests/e2e/test_e2e_kind.py::test_wrapper_hook_and_idle_compact reviewed; executed by the PR CI e2e job]
- AC3: the lease test sees a new leader with reason lease_expired and a higher epoch through the cluster view [evidence: judgement:tests/e2e/test_e2e_kind.py::test_leader_lease_hands_over reviewed; executed by the PR CI e2e job]
- AC4: the autoclose test sees closes_at, then deleting, then 404, with ORCH_AUTOCLOSE_MIN_SECONDS 30 in the kind values [evidence: judgement:tests/e2e/test_e2e_kind.py::test_autoclose_discards_cluster reviewed; executed by the PR CI e2e job]
- AC5: every cluster an e2e test creates is deleted in its teardown and every wait is bounded [evidence: judgement:tests/e2e/test_e2e_kind.py teardown and waits reviewed]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/values-kind.yaml`

#### Interfaces

Uses parts `orch-cluster-config-api`, `orch-leader-lease`, `orch-cluster-autoclose`.

#### Expected outcome

The PR CI e2e job runs three new API-only tests that prove hooks and idle compact, the leader lease and autoclose on kind.

#### Steps

- Add the three tests and the kind value; run `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`: the three new tests are listed.
- Run the lint; the PR CI `e2e` job runs them on kind.

#### Notes

The agent test image runs the wrapper's fake claude, which handles `/compact` (`code/claude-code-wrapper/tests/fake_claude/fake_claude.py`). The e2e run is the PR CI `e2e` job; locally only collection is checked.

- 2026-10-25 done

### S7: smoke config check

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`, `README.md`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: b789904

#### Requirement

Extend the live smoke to prove the new configuration on the deployed orchestrator (design D9; approvals A6, A7). In `scripts/smoke.sh` the smoke cluster spec adds `wrapper {auto_compact {idle_seconds: 1800}, hooks {onTurnComplete: [{type: command, run: "true"}]}}`, `leader_lease_seconds: 3600` (the smoke cluster is a hive through `max_replicas: 2`) and `autoclose_after_seconds: 3600`; after create it reads the cluster view and fails with a named message unless the spec echoes the three fields and `closes_at` equals `created_at` plus 3600 s; once a leader exists, `leader_since` is set. Cleanup stays in the existing trap, so the autoclose never fires during a smoke. `tests/test_smoke_script.py`: the fake API serves the new fields; a happy-path test and a test where the view lacks `closes_at` (named failure, cleanup runs). README smoke section names the config step.

#### Acceptance conditions

- AC1: the happy path creates the cluster with the new fields, checks the spec echo, closes_at and leader_since, exits 0 and cleans up [evidence: test:tests/test_smoke_script.py::test_config_fields_checked]
- AC2: a view without closes_at fails with a named message and cleans up [evidence: test:tests/test_smoke_script.py::test_config_view_mismatch_fails]
- AC3: the script stays strict, bounded and shellcheck clean [evidence: test:tests/test_smoke_script.py::test_script_is_shellcheck_clean]
- AC4: lint passes [evidence: command:mise run lint]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

#### Interfaces

Uses `orch-cluster-config-api`.

#### Expected outcome

`mise run smoke` creates its cluster with the new fields and fails with a named message when the view does not reflect them.

#### Steps

- Red: add `test_config_fields_checked` and `test_config_view_mismatch_fails` to `tests/test_smoke_script.py` with the fake API serving the new fields; `uv run --frozen pytest -q tests/test_smoke_script.py`: fails.
- Green: extend `scripts/smoke.sh`; run the verify command and `mise run lint`: pass.

#### Notes

Decisions are in design.md; nothing beyond the requirement.

- 2026-10-25 done

### S8: web form config fields

- Status: done
- Files: `openapi/agent-orchestrator.json`, `src/api/schema.d.ts`, `src/clusters/clusterSpecForm.ts`, `src/presets/PresetForm.tsx`, `src/presets/PresetForm.test.tsx`
- Verify: `npx vitest run src/presets/PresetForm.test.tsx && npm run lint && npm run check:api`
- Verified head: 2752663

#### Requirement

Let users set every new field in the preset editor of agents-web (design D8, D12; approvals A1, A3, A4, A8).

- Sync the vendored orchestrator API description `openapi/agent-orchestrator.json` from agent-orchestrator main after config-cluster-views merged (recording the orchestrator commit it came from, per agents-web's sync convention) and regenerate `src/api/schema.d.ts`.
- `src/clusters/clusterSpecForm.ts`: form values and the spec mapping for `leader_lease_seconds`, `autoclose_after_seconds` and `wrapper` (auto-compact idle seconds, instructions and min context tokens; system append; restart continue prompt; turn stall seconds; max restarts; turn max seconds; agent commands; permissions allow and deny as comma lists; hooks, MCP servers and plugins as JSON text). Empty inputs stay unset so presets stay sparse; a stored preset spec loads back into the same values.
- `src/presets/PresetForm.tsx`: number inputs for the numeric fields, text inputs for the text fields, a multi-select for agent commands (compact, context, mcp, reload-plugins, reload-skills), JSON text areas for hooks, MCP servers and plugins (the existing any-mcp pattern: invalid JSON or a non-object shows an error and blocks save), and the leader lease input shown only when the spec is a hive (max replicas above 1). Help text says autoclose counts from creation with a 300 s minimum and that command hooks run with the agent's credentials. Server 422 messages show as today.

#### Acceptance conditions

- AC1: the vendored orchestrator openapi copy and the generated types match [evidence: command:npm run check:api]
- AC2: every new input maps to its spec key, empty inputs stay unset, and a stored preset loads back into the same values [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "config fields"]
- AC3: invalid JSON in hooks, MCP servers or plugins blocks save with an error, and the lease input shows only for hive specs [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "config validation"]
- AC4: lint passes [evidence: command:npm run lint]

#### Files

- `openapi/agent-orchestrator.json`
- `src/api/schema.d.ts`
- `src/clusters/clusterSpecForm.ts`
- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`

#### Interfaces

Builds part `web-orch-schema-config` (`src/api/schema.d.ts` with the new spec and view fields); uses `orch-cluster-config-api`.

#### Expected outcome

The preset editor in agents-web has inputs for every new field, saves a sparse spec and reloads it unchanged.

#### Steps

- Sync `openapi/agent-orchestrator.json` from orchestrator main and run `npm run gen:api`, then `npm run check:api`: exits 0.
- Red: add the `config fields` and `config validation` tests to `src/presets/PresetForm.test.tsx`; `npx vitest run src/presets/PresetForm.test.tsx`: fails.
- Green: add the form values, mapping and inputs; run the verify command: passes.

#### Notes

Paths assume frontend-decoupling moved `frontend/` to agents-web with its layout; if its plan names other paths, this task is amended with `ticket.py amend` before the run (design D12).

- 2026-10-25 done

### S9: web clusters page

- Status: done
- Files: `src/clusters/ClustersPage.tsx`, `src/clusters/ClustersPage.test.tsx`, `src/App.tsx`, `src/App.test.tsx`
- Verify: `npx vitest run src/clusters/ClustersPage.test.tsx src/App.test.tsx && npm run lint`
- Verified head: a6491e4

#### Requirement

Give Clusters its own page in the hamburger menu, above Presets (design D7; approvals A5, A8).

- `src/App.tsx`: `settingsCategories` lists `{id: 'clusters', label: 'Clusters'}` first and Presets second; the `view` state gains `'clusters'`, which renders the Clusters page in the main area. The Sessions quick-switch list stays.
- `src/clusters/ClustersPage.tsx`: lists every cluster from `GET /api/v1/clusters` with slug, preset name, state, pods ready of replicas, created time and autoclose time left (from `closes_at`, "never" when null), refreshed like the Presets page; actions: open (selects the cluster and returns to the cluster view), new (opens `NewClusterDialog`) and discard (opens `DiscardClusterDialog`, which calls `DELETE /api/v1/clusters/{id}`).
- Tests in `src/clusters/ClustersPage.test.tsx` and `src/App.test.tsx`.

#### Acceptance conditions

- AC1: the Settings section lists Clusters first and Presets after it, and Clusters opens the Clusters page [evidence: command:npx vitest run src/App.test.tsx -t "clusters entry"]
- AC2: the page lists every cluster with slug, preset, state, ready of replicas, created and time left or never [evidence: command:npx vitest run src/clusters/ClustersPage.test.tsx -t "lists clusters"]
- AC3: open selects the cluster view, new opens the new cluster dialog, and discard opens the discard dialog that calls DELETE [evidence: command:npx vitest run src/clusters/ClustersPage.test.tsx -t "actions"]
- AC4: lint passes [evidence: command:npm run lint]

#### Files

- `src/clusters/ClustersPage.tsx`
- `src/clusters/ClustersPage.test.tsx`
- `src/App.tsx`
- `src/App.test.tsx`

#### Interfaces

Builds cross-epic contract `web-settings-menu-order` (Clusters first, Presets last; the webhook and schedule epics insert their entries between them); uses `web-orch-schema-config`, `orch-cluster-config-api` and the menu contract `orch-settings-menu`.

#### Expected outcome

The hamburger menu's Settings list shows Clusters above Presets; Clusters opens a page listing every cluster with open, new and discard actions and the autoclose time left.

#### Steps

- Red: write `src/clusters/ClustersPage.test.tsx` (`lists clusters`, `actions`) and the `clusters entry` test in `src/App.test.tsx`; `npx vitest run src/clusters/ClustersPage.test.tsx src/App.test.tsx`: fails.
- Green: add the page and the menu entry; run the verify command: passes.

#### Notes

Reuse `PresetsPage` layout patterns, `NewClusterDialog` and `DiscardClusterDialog` unchanged. Paths assume frontend-decoupling's layout (design D12).

- 2026-10-25 done

### S10: deploy pin config

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agent-orchestrator/common.yaml`, `values/agents-web/common.yaml`, `tests/test_orchestrator_release.py`, `tests/test_agents_web_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_agents_web_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster" && uv run ruff check . && uv run ruff format --check .`
- Verified head: a128670

#### Requirement

Release and deploy this epic to the agents namespace (design D10; approval A7). The releases are the main builds of this epic's merged commits: the orchestrator chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` `0.1.0-main.<sha7>` with image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (contracts `agent-orchestrator-chart`, `agent-orchestrator-image`), and the agents-web chart and image published by agents-web CI on main (as frontend-decoupling defines them). No wrapper or any-mcp release (wrapper 0.2.0 already implements every setting). In agents-helmfile: `helmfile.yaml.gotmpl` pins both chart versions; `values/agent-orchestrator/common.yaml` and `values/agents-web/common.yaml` pin the image tags; `tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image` and `tests/test_agents_web_release.py::test_agents_web_pin_matches_image` assert each chart version and image tag carry the same sha (offline, text read). The shas are filled with `ticket.py amend` once the merges land on main. Then run `mise run diff` (only the two chart versions and image tags change), `mise run apply` and `mise run smoke` (which now includes the config step) against the expected kube context.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the merged sha, read offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the agents-web chart version and image tag agree on the merged sha, read offline [evidence: test:tests/test_agents_web_release.py::test_agents_web_pin_matches_image]
- AC3: the published orchestrator chart exists for the pinned version [evidence: command:v=$(grep -A3 'name: agent-orchestrator$' helmfile.yaml.gotmpl | sed -n 's/.*version: //p'); helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version "$v"]
- AC4: helmfile apply of the agents namespace succeeds [evidence: judgement:the apply output (helm revision and chart) quoted in the task notes; never run apply as AC evidence]
- AC5: the live smoke passes, including the config step [evidence: command:mise run smoke]
- AC6: only the two chart versions and image tags change [evidence: judgement:the task diff and mise run diff output reviewed]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_agents_web_release.py`

#### Interfaces

Uses the shared parts listed in the frontmatter `uses`; builds no new interface.

#### Expected outcome

The agents namespace runs this epic's orchestrator and agents-web builds, and the live smoke, including the config step, passes.

#### Steps

- Update the two pin tests to the merged shas; run them: fail.
- Change the pins; run the verify command: passes.
- `mise run diff`: only the two chart versions and image tags change. `mise run apply`, then `mise run smoke`: both exit 0.

#### Notes

The agents-web values and release test file names follow frontend-decoupling's deploy task; amend if they differ (design D12). `test_release_chart_version_and_needs` and `test_db_secret_matches_rendered_cnpg_cluster` pull charts and are deselected in the verify. `mise run apply` is guarded by lint, test and the kube-context check.

Orchestrator notes (2026-10-25; the orchestrator runs live applies): pins e3b2f3c + 7a1654e (agents-web tag quoted; all-digit 1343836 rendered as 1.343836e+06). Pre-apply `mise run diff`, every non-label line: 8x orchestrator image a4be86b -> 60cb11c, agents-web image cedcbbc -> 1343836, checksum/settings (derived), Secret content suppressed (label bump); affected releases agent-orchestrator and agents-web. `mise run apply`: agents-web 0.1.0-main.1343836 and agent-orchestrator 0.1.0-main.60cb11c deployed. Post-apply diff: `No affected releases`. `mise run smoke` last line `smoke: OK` (includes the config check). MEMORY line: agents-helmfile PR #20.

- 2026-10-25 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
