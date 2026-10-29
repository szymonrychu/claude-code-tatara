---
title: orch cache pins
status: todo
repo: agents-orchestrator
value: "The Cache section's in-use badge and the reconciler's delete refusal come from one rule, so they never disagree"
files: [src/agents_orchestrator/cache/pins.py, tests/test_cache_pins.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_pins.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 8
expected_tokens: 1003544
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch cache pins

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G2, verbatim: "each object's class is current on every view: `in_use` (with the session slugs), `preset` (with the preset name), `legacy` (old `preset-*` copy, with how many live sessions copied it), `saved` or `other`; the object list itself is at most `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` old (default 900), shows when it was listed, and a Refresh lists again at once."

Design D3 (One pin rule, `cache.pins`), verbatim: "A pure module importable by the api and the reconciler (like `save_rule.py`): a session row pins its `status.cache.key`/`object`/`sessions_object`, the names it will pin from `spec.cache.key`, and, while its decouple migration is pending, the legacy `sessions/<slug>` and `from_key` sources; any row saving, backing up, restoring or migrating pins its object. Rows of every `desired` state count until purged."

Design D4 (Classes computed at read time), verbatim: "`in_use` (session slugs; not deletable), `preset` (named by a preset whose template renders without the session variables; preset name; deletable: the D11 repair, user Q5), `legacy` (`preset-[0-9a-f]{16}.tar.zst`; "copied by N live sessions" from `migration` records in state `done`; deletable, user Q2), `saved` (other names in the scheme, usually a discarded session restorable on recreate; deletable), `other` (outside the scheme: smoke objects, strays; deletable)."

Design anti-goal, verbatim: "The list badge and the reconciler's refusal disagreeing (two copies of the pin rule)."

This task delivers D3 and the class rule of D4 in agents-orchestrator as the new pure module `src/agents_orchestrator/cache/pins.py`. It imports nothing from `agents_orchestrator.reconciler`, `k8s`, `db` or `api` (the api may import `cache.*`; the legacy preset key formula stays in `reconciler/cache_migration.py`).

- Object names are relative to `cache_s3_prefix`, as the inventory stores them: a workspace object `<name>.tar.zst`, a transcripts object `sessions/<name>.tar.zst`. A `status.cache` value that carries the prefix is compared without it.
- A session row, in every `desired` state until purged, pins: `status.cache.object` and `status.cache.sessions_object`; `<k>.tar.zst` and `sessions/<k>.tar.zst` for `k` = `status.cache.key`; while `status.cache.key` is absent, the same two names for `spec.cache.key` (the names it will pin at its first restore); while `status.cache.sessions_object` is unset (decouple keeps it unset while the session's migration is pending, decouple design D7 amendment item 3), the legacy `sessions/<slug>.tar.zst`; while `status.cache.migration` exists and is not in state `done`, `<from_key>.tar.zst` of its `from_key`. A row saving, backing up, restoring or migrating pins its object through these same fields.
- Classes, first match wins: `in_use` (pinned by at least one row; carries the sorted slugs of every pinning row), `preset` (the workspace or transcripts name of a preset whose `spec.cache` template, or `naming.DEFAULT_CACHE_NAME_TEMPLATE` when its key is empty, renders the same name for any `session` and `created_by`; carries the preset name; a preset whose template fails to render names nothing), `legacy` (fullmatch `preset-[0-9a-f]{16}\.tar\.zst`; carries the number of session rows whose `status.cache.migration` is in state `done` with that `from_key`), `saved` (any other `<k>.tar.zst` or `sessions/<k>.tar.zst` with `k` matching `spec.CACHE_KEY_RE`), `other` (every other key).
- Kind: `transcripts` for a name under `sessions/`, else `workspace`.

## Acceptance conditions

- AC1: a live row pins status.cache.object, status.cache.sessions_object, and the workspace and transcripts names of status.cache.key [evidence: test:tests/test_cache_pins.py::test_session_row_pins_every_cache_field]
- AC2: spec.cache.key names are pinned while status.cache.key is absent and no longer once status.cache.key names another object (a repointed pre-epic session no longer pins its old preset-* object) [evidence: test:tests/test_cache_pins.py::test_spec_key_pins_before_first_restore_only]
- AC3: the legacy sessions/<slug>.tar.zst is pinned while status.cache.sessions_object is unset, and <from_key>.tar.zst while the migration record is not done; neither once sessions_object is set and the record is done [evidence: test:tests/test_cache_pins.py::test_pending_migration_pins_legacy_sources]
- AC4: rows in desired active and deleting pin alike, and pins_by_object maps each object to the sorted slugs of every pinning row [evidence: test:tests/test_cache_pins.py::test_pins_by_object_counts_every_row_state]
- AC5: status values carrying the prefix are compared without it [evidence: test:tests/test_cache_pins.py::test_prefixed_status_values_are_stripped]
- AC6: presets with a literal key or `{{ preset }}` name their workspace and transcripts objects; presets with the default template, a `{{ session }}` or `{{ created_by }}` template, no cache, or a template that fails to render name none [evidence: test:tests/test_cache_pins.py::test_preset_objects_only_for_session_independent_templates]
- AC7: classify applies in_use, preset, legacy, saved, other in that order, including a preset-named or legacy object that a row pins reading in_use [evidence: test:tests/test_cache_pins.py::test_classify_precedence]
- AC8: legacy_copies counts the rows whose migration record is done with that from_key, ignoring failed records [evidence: test:tests/test_cache_pins.py::test_legacy_copies_count_done_migrations]
- AC9: object_kind is transcripts under sessions/ and workspace otherwise [evidence: test:tests/test_cache_pins.py::test_object_kind]
- AC10: the module imports nothing from reconciler, k8s, db or api [evidence: command:! grep -nE "agents_orchestrator\.(reconciler|k8s|db|api)|from \.\.(reconciler|k8s|db|api)" src/agents_orchestrator/cache/pins.py]
- AC11: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/cache/pins.py`
- `tests/test_cache_pins.py`

## Interfaces

- `src/agents_orchestrator/cache/pins.py` (new, pure, synchronous):
  - `ObjectKind = Literal["workspace", "transcripts"]`, `CacheClass = Literal["in_use", "preset", "legacy", "saved", "other"]`, `LEGACY_RE` (fullmatch `preset-[0-9a-f]{16}\.tar\.zst`).
  - `class PinRow(Protocol)`: `slug: str`, `spec` (a `SessionSpec`: `spec.cache` is None or has `.key`), `status: Mapping[str, Any]`; `db.sessions.Session` satisfies it, so callers pass rows from `sessions.list_sessions` unchanged.
  - `object_kind(name: str) -> ObjectKind`.
  - `session_pins(row: PinRow, prefix: str) -> frozenset[str]`.
  - `pins_by_object(rows: Iterable[PinRow], prefix: str) -> dict[str, tuple[str, ...]]` (object name -> sorted slugs).
  - `preset_objects(presets: Iterable[PresetLike]) -> dict[str, str]` (object name -> preset name), `PresetLike` having `id`, `name`, `spec` (`db.presets.Preset` satisfies it); trial-renders each template with `cache.naming.render_cache_name` twice with different `session` and `created_by` values (`preset=spec.slugify(name)`, `preset_id=str(id)`), equal output = a fixed name.
  - `legacy_copies(rows: Iterable[PinRow]) -> dict[str, int]` (`<from_key>.tar.zst` -> count).
  - `classify(name: str, pins: Mapping[str, tuple[str, ...]], presets: Mapping[str, str]) -> CacheClass`.
- Consumers: `reconciler/cache_requests.py` (task orch-cache-requests) and `api/cache.py` (task orch-cache-api).

## Expected outcome

One importable rule decides which objects session rows pin and which class every object name has; the api badge and the reconciler refusal both call it, so they cannot disagree.

## Steps

- Read `cache/save_rule.py` (the pure-module shape), `cache/naming.py`, `cache/presign.py` (`object_name`, `sessions_object_name`), `reconciler/cache_migration.py` (the `migration` record and the pending rule), `reconciler/cache.py` (where `key`, `object`, `sessions_object` are pinned), `spec.py` (`CACHE_KEY_RE`, `slugify`, `WorkspaceCache`), `db/sessions.py` (`Session`) and `db/presets.py` (`Preset`) in one pass.
- Red: write `tests/test_cache_pins.py` with every test named in the acceptance conditions (plain `Session`/`Preset` instances, no database); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_pins.py`; expect collection to fail on the missing module.
- Green: write `cache/pins.py`; rerun; expect all passed.
- `mise run lint`; expect exit 0.

## Notes

- (my call) The class rule is structural: smoke objects whose names fit the scheme (for example `smoke-workspace-cache.tar.zst`, `sessions/smoke-123.tar.zst`) read `saved`; only keys outside the scheme read `other` (open question Q7, planned on its recommended answer).
- Over-pinning is safe (a refusal), under-pinning loses data: when a field's shape is ambiguous, pin.
- No database read, no S3 call, no clock: everything comes in as arguments.
- These tests need no Postgres, so they run locally.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
