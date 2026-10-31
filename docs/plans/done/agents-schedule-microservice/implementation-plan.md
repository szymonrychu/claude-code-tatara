# agents-schedule microservice implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: scaffold project and cli

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `.mise.toml`, `src/agents_schedule/__init__.py`, `src/agents_schedule/cli.py`, `tests/test_cli.py`, `README.md`
- Verify: `uv run --frozen pytest tests/test_cli.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 827b2794d0fb890cbdcb82b7b13da095a5f340aa

#### Requirement

Create the Python project at the root of code/agents-schedule (design D1, D2, D4; approvals A1, A8). `code/agents-schedule` exists before the run: epic agents-schedule-component creates it with `workbench:component-add`.

- uv project `agents-schedule`, src layout, package `agents_schedule` with `__version__`, console script `sched = agents_schedule.cli:main`. Python version: the floor agents-common declares; the Dockerfile base image uses the same minor.
- Runtime dependencies, every one the epic needs, pinned: `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.3.0` (contracts `agents-common-lib` and `agents-common-reuse`, owned by agents-webhook-microservice; v0.3.0 carries the session names and `runs.deliver`), `croniter==6.2.4`, `tzdata` (so `zoneinfo` works in a slim image), `fastapi`, `uvicorn[standard]`, `httpx`, `psycopg[binary,pool]`, `pydantic`, `pydantic-settings`. Dev group: `pytest`, `pytest-asyncio`, `testcontainers[postgres]`, `ruff`. No later task edits pyproject.toml or uv.lock.
- pytest config: `pythonpath = ["src", "tests"]`, `asyncio_mode = "auto"`, marker `e2e`, `addopts = "-q -m 'not e2e'"`, and the agents-common pytest plugin `agents_common.testing` enabled. ruff: line length 100, rules E, F, I, UP, B, SIM.
- `.mise.toml` tasks: `test` (`uv run pytest`), `lint` (`uv run ruff check . && uv run ruff format --check .`), `fmt`, `test:e2e` (`bash scripts/e2e.sh`), `test:chart` (`uv run pytest tests/test_chart.py tests/test_chart_ingress.py`), `lint:chart` (`helm lint chart/agents-schedule --set postgres.url=postgresql://x/y --set orchestrator.url=http://o --set orchestrator.token=t`); the files they name arrive with `helm-chart`, `chart-ingress-and-test-hook` and `kind-e2e-api`.
- `cli.py`: argparse front end with `register(name, func, help, configure=None)`; `sched --version` prints the version; no command prints help and exits 2; an unknown command exits 2; a registered command's return code is the exit code.
- README `## Development` names the mise tasks.
- `tests/test_smoke.py` from the scaffold is removed in favour of `tests/test_cli.py`.

#### Acceptance conditions

- AC1: sched --version prints the package version [evidence: test:tests/test_cli.py::test_version_prints_package_version]
- AC2: a registered command is dispatched and its return code becomes the exit code [evidence: test:tests/test_cli.py::test_registered_command_dispatches]
- AC3: no command or an unknown command exits 2 with help [evidence: test:tests/test_cli.py::test_unknown_command_exits_2]
- AC4: the console script is installed [evidence: command:uv run sched --version]
- AC5: the shared library and the cron library import [evidence: command:uv run python -c 'import agents_common, croniter, zoneinfo; zoneinfo.ZoneInfo("Europe/Warsaw")']
- AC6: lint passes on the new project [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `.mise.toml`
- `src/agents_schedule/__init__.py`
- `src/agents_schedule/cli.py`
- `tests/test_cli.py`
- `README.md`

#### Interfaces

- `agents_schedule.cli:main(argv: list[str] | None = None) -> int`
- `agents_schedule.cli:register(name: str, func: Callable[[argparse.Namespace], int], help: str, configure: Callable[[argparse.ArgumentParser], None] | None = None) -> None` (part `sched-cli`; `service-entrypoints` registers `migrate`, `api`, `worker` through it).

#### Expected outcome

`uv run sched --version` prints the version; `uv run pytest tests/test_cli.py -q` and lint pass; agents-common and croniter import.

#### Steps

- Write tests/test_cli.py with the three named tests; `uv run pytest tests/test_cli.py -q` fails (module not found).
- Write pyproject.toml, `.mise.toml`, the package and cli.py; `uv lock`.
- `uv run --frozen pytest tests/test_cli.py -q`: `3 passed`.
- `uv run ruff check . && uv run ruff format --check .`: clean.

#### Notes

- Model on `code/agents-orchestrator/src/agents_orchestrator/cli.py` and its pyproject.
- The agents-common tag is the one `agents-common-lib` names (agents-webhook-microservice task common-release-v0-1-0); this epic runs after it (README blockers).

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S2: cron expressions

- Status: done
- Files: `src/agents_schedule/cron.py`, `tests/test_cron.py`
- Verify: `uv run --frozen pytest tests/test_cron.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 13b3e3c83368826891aa2802d195496a5584a3db

#### Requirement

Add `agents_schedule.cron` (design D4, D5; approvals A2, A3), pure functions over croniter and zoneinfo, no DB:

- `validate_cron(expr) -> str`: strips and collapses whitespace; exactly 5 fields (`^(\S+\s+){4}\S+$`, the tatara-new CRD pattern) and accepted by croniter; macros (`@daily`), seconds and year fields are refused. Raises `CronError(code="invalid_cron", message)` with the reason.
- `validate_timezone(name) -> ZoneInfo`: IANA name via zoneinfo; raises `CronError(code="invalid_timezone")`.
- `next_fires(expr, tz, after, n=3) -> list[datetime]`: the next n fire times strictly after `after`, tz-aware in `tz`.
- `due(expr, tz, stamp, now) -> Due(fire_time: datetime | None, skipped: int)`: tatara-new parity (`TN/internal/controller/projectscan.go:activityDue`): nothing is due while `next(stamp) > now`. Otherwise `fire_time` is the latest fire time in `(stamp, now]` (one catch-up run) and `skipped` counts the earlier fire times in that interval, which are not run. `stamp` is the latest scheduled fire time already recorded or the schedule's `armed_at`.
- DST in the schedule's zone: a wall time that does not exist on the spring-forward day fires once at croniter's resolution, and an ambiguous wall time on the fall-back day fires once, never twice.

#### Acceptance conditions

- AC1: a valid 5-field expression is normalised [evidence: test:tests/test_cron.py::test_validate_normalises]
- AC2: 4 or 6 fields, macros and nonsense are refused with invalid_cron [evidence: test:tests/test_cron.py::test_validate_refuses]
- AC3: an unknown timezone is refused with invalid_timezone [evidence: test:tests/test_cron.py::test_timezone_refused]
- AC4: next_fires returns 3 tz-aware times strictly after the given instant [evidence: test:tests/test_cron.py::test_next_fires]
- AC5: after downtime spanning several fire times exactly one is due, the latest, and the rest are counted as skipped [evidence: test:tests/test_cron.py::test_due_collapses_missed_runs]
- AC6: nothing is due before the next fire time [evidence: test:tests/test_cron.py::test_not_due_before_next]
- AC7: fall-back day fires once, spring-forward day does not crash or double fire in Europe/Warsaw [evidence: test:tests/test_cron.py::test_dst_transitions_fire_once]

#### Files

- `src/agents_schedule/cron.py`
- `tests/test_cron.py`

#### Interfaces

- `agents_schedule.cron:validate_cron(expr: str) -> str`, `validate_timezone(name: str) -> ZoneInfo`, `next_fires(expr: str, tz: ZoneInfo, after: datetime, n: int = 3) -> list[datetime]`, `due(expr: str, tz: ZoneInfo, stamp: datetime, now: datetime) -> Due`, `Due(fire_time: datetime | None, skipped: int)`, `CronError(code: str, message: str)` (part `sched-cron`).

#### Expected outcome

The api validates and previews schedules and the scheduler decides firings with the same functions.

#### Steps

- Write tests/test_cron.py with the seven named tests (fixed instants, no clock); run it: fails.
- Write cron.py; `uv run --frozen pytest tests/test_cron.py -q`: `7 passed`.
- Lint clean.

#### Notes

- croniter 6.2.4 is maintained (released 2026-07-10, probed on PyPI 2026-10-25); cronsim 2.7 was the alternative (my call, design D4).
- All datetimes are tz-aware; compare in UTC, compute in the schedule's zone.

- 2026-10-25 done

### S3: schedule settings model

- Status: done
- Files: `src/agents_schedule/settings.py`, `tests/test_settings.py`, `README.md`
- Verify: `uv run --frozen pytest tests/test_settings.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 75df33c7aa9d883494cf74c57d05551c8ca1eccc

#### Requirement

Add `agents_schedule.settings` (design D8, D11, D13; approval A1) on agents-common `BaseServiceSettings` (contract `agents-common-lib`: per-service env prefix, `SettingsError` naming each bad variable, `*_FILE` secrets), env prefix `SCHED_`:

- `SCHED_DATABASE_URL` (required), `SCHED_ORCHESTRATOR_URL` (required; the orchestrator's service port, contracts `orch-service-tokens` and `orch-services-service`, live `http://agents-orchestrator-services:8002`), `SCHED_ORCHESTRATOR_TOKEN` or `SCHED_ORCHESTRATOR_TOKEN_FILE` (exactly one required; the base's `*_FILE` rule), `SCHED_ALLOWED_CIDRS` (CSV, default `127.0.0.1/32`), `SCHED_PORT` (default 8000), `SCHED_MAX_IN_PROGRESS` (default 3, 1..50), `SCHED_MAX_PER_SCHEDULE` (default 1, 1..10), `SCHED_DEFAULT_TIMEZONE` (default `Europe/Warsaw`, must be a valid IANA zone), `SCHED_TICK_SECONDS` (default 15, 1..300), `SCHED_POLL_SECONDS` (default 10, 1..300), `SCHED_DISPATCH_MAX_ATTEMPTS` (default 5, 1..20), `SCHED_RUN_TIMEOUT_SECONDS` (default 3600, 60..86400; the webhook's D6 rule, so a stuck turn cannot hold a slot forever).
- `load_settings()` raises `SettingsError` naming every bad or missing variable at once.
- README `## Configuration` lists every variable with default and meaning; this is the contract `agents-schedule-settings-env` agents-helmfile consumes.

#### Acceptance conditions

- AC1: defaults load with only the required variables set [evidence: test:tests/test_settings.py::test_defaults]
- AC2: every bad or missing variable is named in one SettingsError [evidence: test:tests/test_settings.py::test_errors_name_each_variable]
- AC3: the token can come from a file and exactly one token source is required [evidence: test:tests/test_settings.py::test_token_sources]
- AC4: an unknown timezone is refused [evidence: test:tests/test_settings.py::test_default_timezone_must_be_iana]
- AC5: README documents every SCHED_ variable [evidence: doc-section:README.md#Configuration]

#### Files

- `src/agents_schedule/settings.py`
- `tests/test_settings.py`
- `README.md`

#### Interfaces

- `agents_schedule.settings:Settings` (pydantic-settings, `env_prefix="SCHED_"`), `load_settings() -> Settings`, `SettingsError` (contract `agents-schedule-settings-env`, file README.md `## Configuration`).

#### Expected outcome

Every process loads one Settings object; a misconfigured pod exits at startup naming each bad variable.

#### Steps

- Write tests/test_settings.py with the four named tests; run it: fails (no module).
- Write settings.py on the agents-common base; `uv run --frozen pytest tests/test_settings.py -q`: `4 passed`.
- Add README `## Configuration`; lint clean.

#### Notes

- Never log the token; `repr` of Settings masks it (SecretStr).
- `SCHED_ALLOWED_CIDRS` mirrors `ORCH_ALLOWED_CIDRS`: only the oauth2-proxy sidecar (127.0.0.1) or a port-forward reaches the api.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S4: schema migrations

- Status: done
- Files: `src/agents_schedule/db/__init__.py`, `src/agents_schedule/migrations/__init__.py`, `src/agents_schedule/migrations/0001_schedules.sql`, `src/agents_schedule/db/migrate.py`, `tests/conftest.py`, `tests/test_migrations.py`
- Verify: `uv run --frozen pytest tests/test_migrations.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: c56df70148b2125cc7081690ca7a40bfa25053a6

#### Requirement

Create the schema (design D3, D9; approvals A1, A3) as forward-only SQL in the package `agents_schedule.migrations`, run by agents-common `run_migrations(url, "agents_schedule.migrations")` under its advisory lock (contract `agents-common-lib`).

`0001_schedules.sql`, idempotent statements:
- `schedules` (writer: the api only): `id uuid pk`, `name text unique not null` (1..100 chars), `cron text not null`, `timezone text not null`, `preset_id uuid not null`, `prompt text not null` (1..16384 chars), `enabled boolean not null default true`, `armed_at timestamptz not null` (the instant from which firings count: create, enable, cron or timezone change), `created_at`, `updated_at`.
- `runs` (a queue table: the api inserts manual runs, the worker inserts scheduled runs; every status change is a status-guarded UPDATE): `id uuid pk`, `schedule_id uuid not null references schedules on delete cascade`, `trigger text check in ('scheduled','manual')`, `fire_time timestamptz not null`, `status text check in ('new','in-progress','handled','failed','ignored')`, `reason text`, `attempts int not null default 0`, `session_slug text` (the run's deterministic slug, set at claim), `session_id uuid`, `message_id text` (the RunRef carries it as a string), `reuse text check in ('delivered','fallback')` (null until the reuse decision of design D15: `delivered` = the prompt goes to the schedule's earlier running session, `fallback` = reuse did not work out and a new session is created), `created_at`, `updated_at`, `started_at`, `finished_at`; `unique (schedule_id, fire_time)`; index `(status, fire_time)`. Add any column the agents-common `RunStore` protocol requires (contract `preset-mapping-model`).
- `agents_schedule.db.migrate:migrate(settings) -> list[str]` applies pending files and returns their names.
- `tests/conftest.py`: the migrated template database and per-test clone from the `agents_common.testing` pytest plugin (`pg_url`, `migrated_db`), pointed at `agents_schedule.migrations`.

#### Acceptance conditions

- AC1: migrate applies 0001 on an empty database and is a no-op the second time [evidence: test:tests/test_migrations.py::test_migrate_idempotent]
- AC2: two concurrent migrate calls apply each file once [evidence: test:tests/test_migrations.py::test_concurrent_migrate_applies_once]
- AC3: a second run row for the same schedule and fire time is refused by the unique key [evidence: test:tests/test_migrations.py::test_runs_unique_schedule_fire_time]
- AC4: status and trigger outside their sets are refused [evidence: test:tests/test_migrations.py::test_runs_checks]
- AC5: deleting a schedule deletes its runs [evidence: test:tests/test_migrations.py::test_schedule_delete_cascades]
- AC6: reuse outside null, delivered and fallback is refused [evidence: test:tests/test_migrations.py::test_runs_reuse_check]

#### Files

- `src/agents_schedule/db/__init__.py`
- `src/agents_schedule/migrations/__init__.py`
- `src/agents_schedule/migrations/0001_schedules.sql`
- `src/agents_schedule/db/migrate.py`
- `tests/conftest.py`
- `tests/test_migrations.py`

#### Interfaces

- Tables `schedules`, `runs` (part `sched-schema`, file `src/agents_schedule/migrations/0001_schedules.sql`); later schema changes are 0002+.
- `agents_schedule.db.migrate:migrate(settings: Settings) -> list[str]`.
- Fixtures `db_url`, `conn` in tests/conftest.py (part `sched-db-fixture`).

#### Expected outcome

`migrate` creates both tables once, concurrently safe, and every DB test gets a fresh migrated database.

#### Steps

- Write tests/test_migrations.py and conftest.py; run: fails (no migration).
- Write 0001_schedules.sql and migrate.py; `uv run --frozen pytest tests/test_migrations.py -q`: `6 passed`.
- Lint clean.

#### Notes

- The last-fired stamp is not a column on `schedules`: it is the latest `runs.fire_time` with `trigger = 'scheduled'`, else `schedules.armed_at`, so `schedules` keeps one writer (the api) (design D3).
- Tests need Docker for testcontainers; in a cloud session start dockerd first (superrepo MEMORY 2026-10-23).
- do-not-build: a DB layer; agents-common provides pool, migrate, transition and claim.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S5: runs repository

- Status: done
- Files: `src/agents_schedule/db/runs.py`, `tests/test_runs_repo.py`
- Verify: `uv run --frozen pytest tests/test_runs_repo.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 587efb110ef5737c2e67bffdfabb721bf7dc5951

#### Requirement

Add `agents_schedule.db.runs` (design D3, D6, D8, D9, D15; approval A3); every status change goes through agents-common `transition()` and the claim through its `claim()` with `FOR UPDATE SKIP LOCKED` (contract `agents-common-lib`):

- `insert_scheduled(conn, schedule_id, fire_time, status, reason=None) -> Run | None`: `INSERT ... ON CONFLICT (schedule_id, fire_time) DO NOTHING RETURNING`; None means the fire was already recorded. `status` is `new` or `ignored`.
- `insert_manual(conn, schedule_id, now, status, reason=None) -> Run` (fire_time = now, trigger manual).
- `last_scheduled_fire(conn, schedule_id) -> datetime | None`.
- `in_flight(conn, schedule_id) -> int`: runs in `new` or `in-progress`.
- `claim_next(conn, max_in_progress, max_per_schedule, now) -> Run | None`: moves the oldest `new` run by `(fire_time, created_at)` to `in-progress` (`started_at = now`), only when the global `in-progress` count is below `max_in_progress` and its schedule has fewer than `max_per_schedule` runs `in-progress`.
- `transition(conn, run_id, expected, new, **fields) -> bool` (False when the row was not in `expected`); `set_fields(conn, run_id, expected, **fields) -> bool` for `session_slug`, `session_id`, `message_id`, `reuse`, `attempts` without a status change.
- `latest_with_session(conn, schedule_id, exclude_run_id) -> Run | None`: the newest run of the schedule by `(fire_time, created_at)` other than `exclude_run_id` whose status is not `ignored` (the run the reuse rule of design D15 looks at; its `session_id` may be null, then there is nothing to reuse).
- `claim_next` claims the runs of one schedule strictly in `(fire_time, created_at)` order: it never claims a run of a schedule while an older run of that schedule is `new`, so the earlier run's session is decided before the later run looks for it.
- `list_for_schedule(conn, schedule_id, limit)`, `list_recent(conn, status=None, limit=50)`, `get(conn, run_id)`, `list_in_progress(conn)`.

#### Acceptance conditions

- AC1: a second insert_scheduled for the same fire returns None and leaves one row [evidence: test:tests/test_runs_repo.py::test_insert_scheduled_once]
- AC2: a transition from a stale status changes nothing and returns False [evidence: test:tests/test_runs_repo.py::test_transition_is_status_guarded]
- AC3: claim_next honours the global and per-schedule caps and FIFO order [evidence: test:tests/test_runs_repo.py::test_claim_next_caps_and_fifo]
- AC4: two concurrent claimers never get the same run [evidence: test:tests/test_runs_repo.py::test_claim_skip_locked]
- AC5: last_scheduled_fire ignores manual runs [evidence: test:tests/test_runs_repo.py::test_last_scheduled_fire_ignores_manual]
- AC6: claim_next claims the runs of one schedule strictly in fire order [evidence: test:tests/test_runs_repo.py::test_claim_next_per_schedule_order]
- AC7: latest_with_session returns the schedule's newest non-ignored run other than the given one [evidence: test:tests/test_runs_repo.py::test_latest_with_session]

#### Files

- `src/agents_schedule/db/runs.py`
- `tests/test_runs_repo.py`

#### Interfaces

- `agents_schedule.db.runs`: `Run` dataclass, the functions above including `latest_with_session` (part `sched-runs-repo`).

#### Expected outcome

The scheduler, dispatcher, tracker and api share one runs module whose writes are exactly-once and status-guarded.

#### Steps

- Write tests/test_runs_repo.py; run: fails.
- Write runs.py; `uv run --frozen pytest tests/test_runs_repo.py -q`: `7 passed`.
- Lint clean.

#### Notes

- `runs` is the only multi-writer table (api inserts manual runs, worker the rest), and every change is status-guarded (AGENTS.md hard rule).

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S6: schedules repository

- Status: done
- Files: `src/agents_schedule/db/schedules.py`, `tests/test_schedules_repo.py`
- Verify: `uv run --frozen pytest tests/test_schedules_repo.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 96559369e583329419cb210f600dd12b139a81ea

#### Requirement

Add `agents_schedule.db.schedules` (design D3; approval A2): `create`, `get`, `list_all` (by name), `list_enabled`, `update` (full replace of name, cron, timezone, preset_id, prompt, enabled), `delete`. `armed_at` is set to now on create, and on update when `enabled` goes false to true or when `cron` or `timezone` changes; otherwise it is unchanged, so editing the prompt never triggers a catch-up run. A duplicate name raises `ScheduleConflict`; a missing id returns None (get) or raises `ScheduleNotFound` (update, delete). Values arrive validated (the api calls `sched-cron`); the repository does not parse cron.

#### Acceptance conditions

- AC1: create, get, list and delete round-trip a schedule [evidence: test:tests/test_schedules_repo.py::test_crud_round_trip]
- AC2: a duplicate name raises ScheduleConflict [evidence: test:tests/test_schedules_repo.py::test_duplicate_name_conflicts]
- AC3: armed_at moves on enable and on cron or timezone change, and stays on a prompt edit [evidence: test:tests/test_schedules_repo.py::test_armed_at_rules]
- AC4: update or delete of a missing id raises ScheduleNotFound [evidence: test:tests/test_schedules_repo.py::test_missing_id]

#### Files

- `src/agents_schedule/db/schedules.py`
- `tests/test_schedules_repo.py`

#### Interfaces

- `agents_schedule.db.schedules`: `Schedule` (dataclass of the row), `create(conn, *, name, cron, timezone, preset_id, prompt, enabled) -> Schedule`, `get(conn, id) -> Schedule | None`, `list_all(conn)`, `list_enabled(conn)`, `update(conn, id, **fields) -> Schedule`, `delete(conn, id) -> None`, `ScheduleConflict`, `ScheduleNotFound` (part `sched-schedules-repo`).

#### Expected outcome

Schedules are stored and edited with armed_at semantics the scheduler relies on.

#### Steps

- Write tests/test_schedules_repo.py; run: fails.
- Write schedules.py; `uv run --frozen pytest tests/test_schedules_repo.py -q`: `4 passed`.
- Lint clean.

#### Notes

- Only the api process calls the write functions (one writer per table).

- 2026-10-25 done

### S7: run dispatcher

- Status: done
- Files: `src/agents_schedule/dispatcher.py`, `src/agents_schedule/prompt.py`, `tests/test_dispatcher.py`
- Verify: `uv run --frozen pytest tests/test_dispatcher.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: cb7d3ab8277bae6596e4803de999467e3243425b

#### Requirement

Add `agents_schedule.dispatcher` and `agents_schedule.prompt` (design D7, D8, D9, D15; approvals A3, A8) on agents-common v0.3.0 `runs.dispatch`, `runs.running_session`, `runs.deliver` and `OrchestratorClient` (contracts `preset-mapping-model`, `agents-common-lib`, `agents-common-reuse`, `preset-reuse-running-agent`; bearer service token on the orchestrator service port, `orch-service-tokens`). No second HTTP client and no second dispatch algorithm is written here.

- `render_prompt(template, schedule_name, fired_at) -> str`: replaces exactly `{schedule_name}` and `{fired_at}` (ISO 8601 in the schedule's zone); every other brace is left as written (no `str.format`).
- `session_slug(schedule_name, run_id) -> str`: DNS-1123 label `<schedule name slug, at most 24>-<first 8 hex of run id>`, at most 40 chars (`code/agents-orchestrator/src/agents_orchestrator/spec.py:validate_slug`).
- A `RunStore` over the runs table (the agents-common protocol), so `runs.dispatch` records `session_id` and `message_id` on the run with guarded updates.
- `dispatch_once(pool, client, settings) -> bool`: `runs.claim_next` under the caps (`new -> in-progress`); a claimed run whose schedule is now disabled goes `in-progress -> ignored` reason `schedule_disabled`. Otherwise the run is sent in one of two ways, each at most once, with the rendered prompt carrying `marker("schedule", run_id)` (`<!-- agents-schedule:<id> -->`):
  - Reuse (design D15): when the run's `reuse` is null, `client.get_preset(preset_id)` reports `reuse_running_agent` true, and the schedule's `latest_with_session` run has a `session_id` for which `runs.running_session(client, session_id)` returns a session, set `reuse = delivered` (guarded) and post the prompt there with `runs.deliver(client, store, run, session_id, text, marker)`. A returned RunRef (message recorded) ends the pass; `None` (session gone or being deleted) sets `reuse = fallback` and falls through to creation. The overlap rule D6 keeps at most one new or in-progress run per schedule, so reuse applies when the previous run is already finished but its session is still running.
  - Create: `runs.dispatch` with the slug (the run's `session_slug`) and the `PresetBinding` of the schedule's `preset_id`, with `session_id` cleared on the RunRef after a fallback: create the session from the preset (409 resolves the existing session by slug), record `session_id`, look for a message with the marker before posting, post, record `message_id`.
  A restart at any point resumes the same run: `reuse = delivered` without `message_id` re-runs `runs.deliver` (adopt-before-post, so no second prompt), `reuse = fallback` or null with the session already created resumes `runs.dispatch`. No second session is created and no second prompt is posted.
- Errors: preset gone (404 on `get_preset` or on create) -> `failed` reason `preset_not_found` (set by `runs.dispatch`); the orchestrator refuses (422) -> `failed` reason `orchestrator_refused: <code>`; transient (connection error, 5xx, 503) -> stays `in-progress` with `attempts + 1` and is resumed on a later pass with backoff; at `SCHED_DISPATCH_MAX_ATTEMPTS` -> `failed` reason `orchestrator_unavailable`.
- `run_dispatcher(pool, client, settings, stop)` resumes in-progress runs without `message_id`, then loops `dispatch_once` until it returns False, then sleeps `SCHED_POLL_SECONDS` or wakes on a new run.

#### Acceptance conditions

- AC1: a new run creates a session from its preset, posts the rendered prompt and records both ids [evidence: test:tests/test_dispatcher.py::test_dispatch_happy_path]
- AC2: a restart after create, or after post, never creates a second session or posts a second prompt [evidence: test:tests/test_dispatcher.py::test_resume_never_repeats]
- AC3: a 409 on create resolves the existing session [evidence: test:tests/test_dispatcher.py::test_conflict_resolves_existing_session]
- AC4: at most SCHED_MAX_IN_PROGRESS runs are in-progress and later runs wait FIFO [evidence: test:tests/test_dispatcher.py::test_global_cap_fifo]
- AC5: a missing preset fails the run with reason preset_not_found; transient errors retry then fail orchestrator_unavailable [evidence: test:tests/test_dispatcher.py::test_error_mapping]
- AC6: placeholders render and other braces are left alone [evidence: test:tests/test_dispatcher.py::test_render_prompt]
- AC7: the slug is a DNS-1123 label of at most 40 characters for any schedule name [evidence: test:tests/test_dispatcher.py::test_slug_is_dns_label]
- AC8: with the preset opting in and the schedule's previous run's session running, the run posts its prompt there and creates no session [evidence: test:tests/test_dispatcher.py::test_reuse_posts_to_running_session]
- AC9: a preset that does not opt in creates a new session even when the previous session is running [evidence: test:tests/test_dispatcher.py::test_no_reuse_when_preset_not_opted_in]
- AC10: reuse falls back to a new session when the previous session is gone or deliver returns None [evidence: test:tests/test_dispatcher.py::test_reuse_falls_back_when_session_gone]
- AC11: a restart after the reuse post never posts a second prompt [evidence: test:tests/test_dispatcher.py::test_reuse_resume_never_reposts]

#### Files

- `src/agents_schedule/dispatcher.py`
- `src/agents_schedule/prompt.py`
- `tests/test_dispatcher.py`

#### Interfaces

- `agents_schedule.prompt:render_prompt(template: str, schedule_name: str, fired_at: datetime) -> str`, `session_slug(schedule_name: str, run_id: UUID) -> str`, the marker from agents-common `marker("schedule", run_id)`.
- `agents_schedule.dispatcher:RunsStore` (agents-common `RunStore`), `dispatch_once(pool, client, settings) -> bool`, `run_dispatcher(pool, client, settings, stop) -> None` (part `sched-dispatch`).
- Consumes `agents_common.runs.dispatch`, `running_session`, `deliver`, `PresetBinding`, `agents_common.orchestrator.OrchestratorClient` (`get_preset`, `Preset.reuse_running_agent`), and `db.runs.latest_with_session`.

#### Expected outcome

Each new run yields exactly one prompt, in a new session or (preset opt-in) in the schedule's still-running earlier session, under the caps, and every failure has a reason.

#### Steps

- Write tests/test_dispatcher.py against `agents_common.fake_orchestrator` (contract `agents-common-lib`) and a migrated DB; run: fails.
- Write prompt.py and dispatcher.py; `uv run --frozen pytest tests/test_dispatcher.py -q`: `11 passed`.
- Lint clean.

#### Notes

- The prompt goes as a message after create; presets carry no prompt (`code/agents-orchestrator/src/agents_orchestrator/spec.py:SessionSpec`). do-not-build: a prompt field on presets.
- Same dispatch as agents-webhook (its design D8), with this service's marker and slug; the reuse branch is the agents-webhook rule keyed by the schedule (its design "Cross-epic impact"). The overlap rule D6 means the earlier run is finished by the time the later one is claimed.
- If an agents-common signature differs from the names above, use the library's as released; never re-implement dispatch here.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S8: run outcome tracker

- Status: done
- Files: `src/agents_schedule/tracker.py`, `tests/test_tracker.py`
- Verify: `uv run --frozen pytest tests/test_tracker.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 62423619011ecd53c0245e7b8e6898f5c371a97b

#### Requirement

Add `agents_schedule.tracker` (design D10, D15; approval A3) on agents-common v0.3.0 `runs.track`, `runs.track_delivery` and `OrchestratorClient` (contracts `preset-mapping-model`, `agents-common-lib`, `agents-common-reuse`; reference poller `code/agents-orchestrator/bench/runner.py:_finished`).

- `track_once(pool, client, settings, now) -> int`: for each `in-progress` run with a `message_id`, `GET /api/v1/messages/{message_id}`: `turn.status = completed` -> `handled`, `finished_at = turn.completed_at`; message `failed` or `cancelled` -> `failed` reason `message_<status>`; `turn.status = failed` -> `failed` reason `turn_failed`; 404 -> `failed` reason `session_not_found`; in progress longer than `SCHED_RUN_TIMEOUT_SECONDS` -> `failed` reason `timeout`; anything else leaves the run in-progress. A run with `reuse = delivered` is tracked with `runs.track_delivery(client, store, run, timeout_seconds=SCHED_RUN_TIMEOUT_SECONDS, now=now)` instead: `handled` when its message is `sent`; `timeout` finishes it failed; `"gone"` (message cancelled, failed or missing, the reused session went away) sets `reuse = fallback` and clears `session_id` and `message_id` through one guarded update, so the dispatcher resumes the run and creates a new session; still queued leaves it in-progress. Transient orchestrator errors leave it unchanged and are logged once per run per minute.
- Every change is the guarded `in-progress -> handled|failed` transition; a run already moved by another process is left alone.
- `run_tracker(pool, client, settings, stop)` loops every `SCHED_POLL_SECONDS`.
- The service never deletes sessions (gate Q8); cleanup is the preset's autoclose from configuration-improvements (contract `orch-cluster-autoclose`).

#### Acceptance conditions

- AC1: a completed first turn marks the run handled with finished_at [evidence: test:tests/test_tracker.py::test_completed_turn_handled]
- AC2: failed or cancelled messages, failed turns and timeouts mark the run failed with the reason [evidence: test:tests/test_tracker.py::test_failures_have_reasons]
- AC3: a running turn or a transient error leaves the run in-progress [evidence: test:tests/test_tracker.py::test_running_unchanged]
- AC4: the tracker never calls DELETE on the orchestrator [evidence: test:tests/test_tracker.py::test_never_deletes_sessions]
- AC5: a reused run whose message is sent is handled, and a reused run whose message is gone is reset to reuse fallback with session and message cleared [evidence: test:tests/test_tracker.py::test_reused_run_tracked_by_delivery]

#### Files

- `src/agents_schedule/tracker.py`
- `tests/test_tracker.py`

#### Interfaces

- `agents_schedule.tracker:track_once(pool, client, settings, now) -> int`, `run_tracker(pool, client, settings, stop) -> None` (part `sched-tracker`); consumes `agents_common.runs.track` and `runs.track_delivery`.

#### Expected outcome

Runs reach a terminal status that matches the orchestrator's view of their first turn.

#### Steps

- Write tests/test_tracker.py against `agents_common.fake_orchestrator`; run: fails.
- Write tracker.py; `uv run --frozen pytest tests/test_tracker.py -q`: `5 passed`.
- Lint clean.

#### Notes

- do-not-build: a turn-completion callback in the orchestrator; polling the message gives the outcome (`code/agents-orchestrator/src/agents_orchestrator/api/messages.py` L99).

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S9: scheduler loop

- Status: done
- Files: `src/agents_schedule/scheduler.py`, `tests/test_scheduler.py`
- Verify: `uv run --frozen pytest tests/test_scheduler.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 12de0cd34863c31b16cd2e896661d50f536ba5b8

#### Requirement

Add `agents_schedule.scheduler` (design D5, D6, D9; approval A3). `tick(pool, settings, now) -> TickResult` runs one pass; `run_scheduler(pool, settings, stop)` loops it.

- For each enabled schedule: `stamp = max(last_scheduled_fire, armed_at)`; `cron.due(expr, tz, stamp, now)`. Nothing due: skip. Due: in one transaction, when `in_flight(schedule) >= SCHED_MAX_PER_SCHEDULE` insert the run as `ignored` with reason `previous_running`, else as `new`. Either insert advances the stamp, because the stamp is the latest scheduled fire time (tatara-new: the stamp advances even when a run is skipped).
- `skipped > 0` logs one line per schedule `missed <n> fire times of <name> before <fire_time>` and creates no rows for them (one catch-up run, gate Q2).
- Exactly once: the insert is keyed on `(schedule_id, fire_time)`, so a restart or a second process re-running the same tick never creates a second row; `run_scheduler` runs only under the advisory singleton (`service-entrypoints`).
- Wake-up: sleep until the earliest next fire time over enabled schedules or `SCHED_TICK_SECONDS`, whichever is sooner, and wake early on the agents-common LISTEN channel `schedules_changed` when the api notifies it (if the library has no LISTEN helper, the tick interval alone is the bound).
- One schedule failing (bad stored cron after a library upgrade) logs and is skipped; the others still fire.

#### Acceptance conditions

- AC1: a due schedule gets one new run at the fire time [evidence: test:tests/test_scheduler.py::test_due_schedule_creates_new_run]
- AC2: running the same tick twice, or from two connections at once, creates one row [evidence: test:tests/test_scheduler.py::test_tick_is_exactly_once]
- AC3: after downtime over several fire times one run is created for the latest and the rest are logged [evidence: test:tests/test_scheduler.py::test_missed_runs_collapse]
- AC4: a fire while the previous run is in flight is recorded ignored previous_running and the stamp advances [evidence: test:tests/test_scheduler.py::test_overlap_recorded_ignored_and_stamp_advances]
- AC5: disabled schedules and a re-enabled schedule's disabled period never fire [evidence: test:tests/test_scheduler.py::test_disabled_and_rearmed]
- AC6: one broken schedule does not stop the others [evidence: test:tests/test_scheduler.py::test_bad_schedule_isolated]

#### Files

- `src/agents_schedule/scheduler.py`
- `tests/test_scheduler.py`

#### Interfaces

- `agents_schedule.scheduler:tick(pool, settings, now: datetime) -> TickResult(created: int, ignored: int, skipped: int)`, `run_scheduler(pool, settings, stop: asyncio.Event) -> None` (part `sched-scheduler`).

#### Expected outcome

Schedules fire on time exactly once per fire time; overlaps and missed runs behave per the gate answers.

#### Steps

- Write tests/test_scheduler.py driving `tick` with fixed `now` values; run: fails.
- Write scheduler.py; `uv run --frozen pytest tests/test_scheduler.py -q`: `6 passed`.
- Lint clean.

#### Notes

- Prior art: `TN/internal/controller/projectscan.go:activityDue` (L480) and `inflightRefineTask` (L1807).
- Per-repo phase-shift jitter (`scanOffset`) is not built: not requested (design Research).

- 2026-10-25 done

### S10: schedules api routes

- Status: done
- Files: `src/agents_schedule/api/__init__.py`, `src/agents_schedule/api/app.py`, `src/agents_schedule/api/schemas.py`, `src/agents_schedule/api/schedules.py`, `tests/test_api_schedules.py`
- Verify: `uv run --frozen pytest tests/test_api_schedules.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 0a5e30924cd023fe1c5bdf3d73c333423eb29044

#### Requirement

Add the FastAPI app (design D11; approvals A2, A5). Every route is under `/schedules/api/v1` (gate Q9; the path layout contract of frontend-decoupling); `/healthz` and `/readyz` sit at the root for probes.

- `create_app(settings, pool, client) -> FastAPI` with a source allowlist middleware on `SCHED_ALLOWED_CIDRS` that checks the socket peer only, never forwarded headers (the agents-common one if it ships it, else the pattern of `code/agents-orchestrator/src/agents_orchestrator/api/allowlist.py:SourceAllowlist`). Errors use `{"error": {"code", "message"}}` (as `code/agents-orchestrator/src/agents_orchestrator/api/errors.py`).
- `GET /schedules` -> `list[ScheduleView]` by name; `POST /schedules` -> 201; `GET /schedules/{id}`; `PUT /schedules/{id}` (full replace of `name, cron, timezone, preset_id, prompt, enabled`); `DELETE /schedules/{id}` -> 204; `POST /schedules/preview {cron, timezone}` -> `{next_fires: [3 ISO times]}`.
- `ScheduleIn {name, cron, timezone (default SCHED_DEFAULT_TIMEZONE), preset_id, prompt, enabled = true}`; `ScheduleView {id, name, cron, timezone, preset_id, prompt, enabled, next_fires (3, empty when disabled), last_run: RunView | null, created_at, updated_at}`; `RunView {id, schedule_id, trigger, fire_time, status, reason, session_id, session_slug, message_id, reuse, created_at, updated_at, started_at, finished_at}`.
- Validation on every write: cron via `sched-cron` (422 `invalid_cron` with the reason), timezone (422 `invalid_timezone`), prompt 1..16384 chars and name 1..100 (422 `invalid_request`), preset exists via the orchestrator client `GET /api/v1/presets/{id}` (contract `orch-presets-api`; 422 `unknown_preset`; orchestrator unreachable 503 `orchestrator_unavailable`). Duplicate name 409 `conflict`; missing id 404 `not_found`.
- Each write notifies `schedules_changed` so the scheduler wakes.
- `/readyz` checks the DB; `/healthz` is liveness only.

#### Acceptance conditions

- AC1: create, list, get, replace and delete round-trip a schedule [evidence: test:tests/test_api_schedules.py::test_crud]
- AC2: an invalid cron or timezone answers 422 with its code and reason [evidence: test:tests/test_api_schedules.py::test_validation_422]
- AC3: an unknown preset answers 422 unknown_preset and an unreachable orchestrator 503 [evidence: test:tests/test_api_schedules.py::test_preset_checked]
- AC4: preview returns the next 3 fire times in the given zone [evidence: test:tests/test_api_schedules.py::test_preview]
- AC5: a duplicate name answers 409 and a missing id 404 [evidence: test:tests/test_api_schedules.py::test_conflict_and_not_found]
- AC6: a peer outside SCHED_ALLOWED_CIDRS gets 403 and X-Forwarded-For is ignored [evidence: test:tests/test_api_schedules.py::test_source_allowlist]

#### Files

- `src/agents_schedule/api/__init__.py`
- `src/agents_schedule/api/app.py`
- `src/agents_schedule/api/schemas.py`
- `src/agents_schedule/api/schedules.py`
- `tests/test_api_schedules.py`

#### Interfaces

- `agents_schedule.api.app:create_app(settings, pool, client) -> FastAPI` (part `sched-api-app`), routers mounted under `/schedules/api/v1`.
- `agents_schedule.api.schemas`: `ScheduleIn`, `ScheduleView`, `RunView`, `PreviewIn`, `PreviewView`.

#### Expected outcome

Schedules are managed headlessly over HTTP with the same validation the UI shows.

#### Steps

- Write tests/test_api_schedules.py with httpx ASGI transport, a migrated DB and a fake orchestrator client; run: fails.
- Write the api package; `uv run --frozen pytest tests/test_api_schedules.py -q`: `6 passed`.
- Lint clean.

#### Notes

- The api is the only writer of `schedules`.
- `/schedules/api/v1` is the reserved prefix of the frontend-decoupling URL layout (contract `agents-web-url-layout`: each later service owns `/<prefix>/`, its UI-facing API at `/<prefix>/api/v1`, reserved `schedules`).
- Tests use `agents_common.fake_orchestrator` for the preset check.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S11: ignored runs finished at

- Status: done
- Files: `src/agents_schedule/db/runs.py`, `tests/test_runs_repo.py`
- Verify: `uv run --frozen pytest tests/test_runs_repo.py tests/test_scheduler.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: adc6cf13dd97435999d67e850aa84aa4a4179a59

#### Requirement

A run inserted directly as `ignored` (the scheduler's overlap path, reason `previous_running`, through `agents_schedule.db.runs.insert_scheduled`) gets `finished_at` set at insert, the same as a run the dispatcher moves to `ignored` (`schedule_disabled`), so every terminal run (handled, failed, ignored) carries `finished_at` and the runs API and UI can show when it ended. Discovered by task scheduler-loop.

- `insert_scheduled` (and `insert_manual` if it can insert a terminal status) sets `finished_at = now()` whenever the inserted status is `ignored`.
- No change to the partial unique index or the ON CONFLICT target.

#### Acceptance conditions

- AC1: a scheduled run inserted as ignored has finished_at set [evidence: test:tests/test_runs_repo.py::test_ignored_insert_sets_finished_at]
- AC2: a scheduled run inserted as new has no finished_at [evidence: test:tests/test_runs_repo.py::test_new_insert_has_no_finished_at]

#### Files

- `src/agents_schedule/db/runs.py`
- `tests/test_runs_repo.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-25 done

### S12: runs api routes

- Status: done
- Files: `src/agents_schedule/api/runs.py`, `src/agents_schedule/api/app.py`, `src/agents_schedule/api/schemas.py`, `tests/test_api_runs.py`
- Verify: `uv run --frozen pytest tests/test_api_runs.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 08a4b344760cb681f653ba9ea1af9446be3915c1

#### Requirement

Add the run routes under `/schedules/api/v1` (design D6, D11; approvals A3, A5):

- `POST /schedules/{id}/run` -> 202 `RunView`: inserts a manual run (`trigger manual`, `fire_time` now) as `new`, or as `ignored` with reason `previous_running` when the schedule already has `SCHED_MAX_PER_SCHEDULE` runs in flight (same rule as a scheduled fire, so history shows it). Allowed on a disabled schedule (my call, design D11). Notifies the dispatcher.
- `GET /schedules/{id}/runs?limit=20` (1..100, newest first); `GET /runs?status=&limit=50` (1..200, newest first, status filter one of the five); `GET /runs/{id}`.
- 404 `not_found` for a missing schedule or run; 422 `invalid_request` for a bad limit or status.

#### Acceptance conditions

- AC1: run now creates a manual new run and answers 202 [evidence: test:tests/test_api_runs.py::test_run_now_creates_manual_run]
- AC2: run now while a run is in flight records ignored previous_running [evidence: test:tests/test_api_runs.py::test_run_now_overlap_ignored]
- AC3: per-schedule and global run lists are newest first, limited and filtered [evidence: test:tests/test_api_runs.py::test_run_lists]
- AC4: missing ids answer 404 and bad parameters 422 [evidence: test:tests/test_api_runs.py::test_run_errors]

#### Files

- `src/agents_schedule/api/runs.py`
- `src/agents_schedule/api/app.py`
- `src/agents_schedule/api/schemas.py`
- `tests/test_api_runs.py`

#### Interfaces

- Router `agents_schedule.api.runs:router` included by `create_app`; `RunView` from `api/schemas.py` (part `sched-runs-api`).

#### Expected outcome

Every run and the run-now control are reachable headlessly.

#### Steps

- Write tests/test_api_runs.py; run: fails.
- Write runs.py and include it in app.py; `uv run --frozen pytest tests/test_api_runs.py -q`: `4 passed`.
- Lint clean.

#### Notes

- The api inserts only `new` or `ignored` manual runs; the worker moves them on.

- 2026-10-25 done

### S13: api docs and openapi

- Status: done
- Files: `openapi.json`, `README.md`, `src/agents_schedule/api/openapi.py`, `tests/test_readme_api.py`
- Verify: `uv run --frozen pytest tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 2b5ab47badff7a4bdbe495fb4f751fe9690f0518

#### Requirement

Document the API (design D11, D15; approval A5), the pattern of `code/agents-orchestrator/tests/test_readme_api.py`:

- `python -m agents_schedule.api.openapi` prints the OpenAPI document; `openapi.json` is committed.
- `tests/test_readme_api.py`: the committed `openapi.json` equals the generated one (drift test), and every route in it is named in README `## API` with method and path.
- README `## API`: base path `/schedules/api/v1`, each route with request body, response, status codes and error codes; the run statuses and reasons (`previous_running`, `schedule_disabled`, `preset_not_found`, `session_not_found`, `orchestrator_refused`, `orchestrator_unavailable`, `message_failed`, `message_cancelled`, `turn_failed`); the reuse rule (a run posts its prompt to the schedule's previous run's session instead of creating one when the preset sets `reuse_running_agent` and that session is still running, with `reuse` `delivered`, or `fallback` when it fell back to a new session); the placeholders `{schedule_name}`, `{fired_at}`; and a `### Versioning` note that `/schedules/api/v1` is additive-only. README `## Commands` names `sched migrate|api|worker`.

#### Acceptance conditions

- AC1: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_matches_app]
- AC2: every route is documented in README ## API [evidence: test:tests/test_readme_api.py::test_every_route_documented]
- AC3: README documents the API, run reasons, the reuse rule and versioning [evidence: doc-section:README.md#API]

#### Files

- `openapi.json`
- `README.md`
- `src/agents_schedule/api/openapi.py`
- `tests/test_readme_api.py`

#### Interfaces

- Contract `agents-schedule-api` (file `code/agents-schedule/README.md`, `openapi.json`): consumed by agents-web (vendored as `openapi/agents-schedule.json`) and the agents-helmfile smoke.

#### Expected outcome

Anything the UI can do is documented as an HTTP call, including the run reasons and the reuse rule, and a route change without regenerating openapi.json fails the tests.

#### Steps

- Write tests/test_readme_api.py; run: fails (no openapi.json).
- Write openapi.py, generate openapi.json, write README ## API; `uv run --frozen pytest tests/test_readme_api.py -q`: `2 passed`.
- Lint clean.

#### Notes

- `/schedules/api/v1` is additive-only from its first release; agents-web vendors this file.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S14: service entrypoints

- Status: done
- Files: `src/agents_schedule/cli.py`, `src/agents_schedule/runtime.py`, `tests/test_entrypoints.py`
- Verify: `uv run --frozen pytest tests/test_entrypoints.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 200e17c6b3a08e5c92350a6ea606c65cbb75c4e1

#### Requirement

Register the service commands (design D9, D13; approval A1) through `sched-cli`, on agents-common `runtime.run_service` and `runtime.advisory_singleton` (contract `agents-common-lib`):

- `sched migrate`: runs `db.migrate.migrate`, exits 0, prints applied file names.
- `sched api`: uvicorn on `SCHED_PORT` serving `create_app`.
- `sched worker`: under the advisory singleton lock `agents-schedule-worker` runs `run_scheduler`, `run_dispatcher` and `run_tracker` concurrently; a second worker process waits for the lock and takes over when the first dies (heartbeat loss); SIGTERM stops all three and releases the lock.
- A bad configuration exits 78 with the SettingsError lines.

#### Acceptance conditions

- AC1: sched migrate applies the schema and exits 0 [evidence: test:tests/test_entrypoints.py::test_migrate_command]
- AC2: two worker processes against one database: only the lock holder fires a due schedule [evidence: test:tests/test_entrypoints.py::test_single_worker_fires]
- AC3: the standby worker takes over after the holder stops [evidence: test:tests/test_entrypoints.py::test_standby_takes_over]
- AC4: a bad configuration exits 78 naming the variable [evidence: test:tests/test_entrypoints.py::test_bad_config_exits_78]
- AC5: sched --help lists migrate, api and worker [evidence: command:uv run sched --help | grep -q worker]

#### Files

- `src/agents_schedule/cli.py`
- `src/agents_schedule/runtime.py`
- `tests/test_entrypoints.py`

#### Interfaces

- Commands `sched migrate`, `sched api`, `sched worker` (part `sched-entrypoints`); `agents_schedule.runtime:worker_main(settings) -> int`, `api_main(settings) -> int`.

#### Expected outcome

The image's three commands run the service; firing is single-instance with failover.

#### Steps

- Write tests/test_entrypoints.py; run: fails.
- Write runtime.py and register the commands in cli.py; `uv run --frozen pytest tests/test_entrypoints.py -q`: `4 passed`.
- Lint clean.

#### Notes

- The singleton plus the unique `(schedule_id, fire_time)` key together make a double fire impossible (design D9).

- 2026-10-25 done

### S15: dockerfile and ci

- Status: done
- Files: `Dockerfile`, `.dockerignore`, `.github/workflows/ci.yaml`, `scripts/chart-version.sh`, `tests/test_ci_workflow.py`
- Verify: `uv run --frozen pytest tests/test_ci_workflow.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 7eb60e5abf264a4bdbae2cd986353cdd0fa4506b

#### Requirement

Add the image and CI (design D13; approvals A1, A6), modelled on `code/agents-orchestrator/Dockerfile` and `.github/workflows/ci.yaml`:

- Dockerfile: `python:<agents-common minor>-slim`, uv sync from the lock (no dev group), `USER 1000`, entrypoint `sched`; no node stage.
- ci.yaml on pull requests and push to main and tags `v*`: jobs `lint` (`mise run lint`), `test` (`mise run test`, Docker available for testcontainers), `images` (docker build, `docker run --rm <image> --help` smoke, push `harbor.szymonrichert.pl/containers/agents-schedule:<sha7>` on main with secrets `HARBOR_USERNAME`/`HARBOR_PASSWORD`, regctl chunked push as the orchestrator does), `chart` (`mise run lint:chart` and `mise run test:chart`), `e2e` (`mise run test:e2e`, kind), `chart-publish` (`<version>-main.<sha7>` on main via `scripts/chart-version.sh`), `chart-publish-tag` (`X.Y.Z` on tag `vX.Y.Z`) to `oci://harbor.szymonrichert.pl/charts/agents-schedule`.
- `tests/test_ci_workflow.py` parses ci.yaml and asserts the jobs, triggers, image name and chart repo, and that `scripts/chart-version.sh` prints `<chart version>-main.<sha7>` for a sha.

#### Acceptance conditions

- AC1: the workflow has every job, trigger and publish target [evidence: test:tests/test_ci_workflow.py::test_workflow_jobs_and_targets]
- AC2: chart-version.sh prints the main build version [evidence: test:tests/test_ci_workflow.py::test_chart_version_script]
- AC3: the image builds and its entrypoint answers --help [evidence: command:docker build -t agents-schedule:ci . && docker run --rm agents-schedule:ci --help]
- AC4: the image runs as uid 1000 without a dev dependency [evidence: command:test "$(docker run --rm --entrypoint id agents-schedule:ci -u)" = 1000 && ! docker run --rm --entrypoint python agents-schedule:ci -c 'import pytest']

#### Files

- `Dockerfile`
- `.dockerignore`
- `.github/workflows/ci.yaml`
- `scripts/chart-version.sh`
- `tests/test_ci_workflow.py`

#### Interfaces

- Contract `agents-schedule-image`: `harbor.szymonrichert.pl/containers/agents-schedule:<sha7>` (file `code/agents-schedule/.github/workflows/ci.yaml`), consumed by agents-helmfile.

#### Expected outcome

Main builds publish the image and a `-main.<sha7>` chart; a `v*` tag publishes the release chart.

#### Steps

- Write tests/test_ci_workflow.py; run: fails.
- Write Dockerfile, .dockerignore, ci.yaml, chart-version.sh; `uv run --frozen pytest tests/test_ci_workflow.py -q`: `2 passed`.
- `docker build` and the --help smoke pass.

#### Notes

- The CI secrets are set by epic agents-schedule-component (task create-agents-schedule-repo).
- The chart and e2e jobs call mise tasks that `helm-chart` and `kind-e2e-api` fill; CI on the epic branch is green only once those land.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done: AC3/AC4 (image build, uid 1000, no pytest) not runnable locally (Docker VM disk full); verified by PR CI images job before close

### S16: helm chart

- Status: done
- Files: `chart/agents-schedule/Chart.yaml`, `chart/agents-schedule/values.yaml`, `chart/agents-schedule/templates/_helpers.tpl`, `chart/agents-schedule/templates/_config.tpl`, `chart/agents-schedule/templates/deployment.yaml`, `chart/agents-schedule/templates/service.yaml`, `chart/agents-schedule/templates/configmap.yaml`, `tests/test_chart.py`
- Verify: `uv run --frozen pytest tests/test_chart.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 1504e8202ca2afd30e290b0192835d4735748307

#### Requirement

Add `chart/agents-schedule` (design D13; approval A1), modelled on `code/agents-orchestrator/chart/agents-orchestrator` (components loop in `templates/deployment.yaml`, postgres source in `_config.tpl`):

- values: `image {repository: harbor.szymonrichert.pl/containers/agents-schedule, tag}`, `postgres {url | existingSecret, existingSecretKey | host, port, database, user, password}` (required), `orchestrator {url, token | tokenSecret {name, key}}` (url and one token source required; the agents-webhook chart shape), `env` (extra `SCHED_*`), `components {api {replicas, port 8000, podAnnotations, resources}, worker {replicas: 1, resources}}`, `service`, `serviceAccount`, `ingress` (see `chart-ingress-and-test-hook`).
- One Deployment per component: api runs `sched api`, worker `sched worker`; both have a `sched migrate` initContainer (the advisory-locked migrator makes concurrent runs safe); readiness `/readyz` and liveness `/healthz` on the api; the worker has no Service.
- ConfigMap of the non-secret `SCHED_*` settings; `SCHED_DATABASE_URL` comes from the postgres Secret; the orchestrator token is rendered into the chart's own Secret from `orchestrator.token` (or taken from `orchestrator.tokenSecret`) and mounted as the file `SCHED_ORCHESTRATOR_TOKEN_FILE` names.
- Service `<fullname>-api` port name `http` (the oauth2-proxy injector hands that port to the sidecar).
- `mise run test:chart` and `mise run lint:chart` (defined by `scaffold-project-and-cli`) pass once this task and `chart-ingress-and-test-hook` land.
- tests/test_chart.py renders with `helm template` and asserts the Deployments, commands, initContainers, env sources and that a missing postgres or orchestrator value fails the render.

#### Acceptance conditions

- AC1: the api and worker Deployments render with their commands and migrate initContainers [evidence: test:tests/test_chart.py::test_components_render]
- AC2: database URL and orchestrator token reach the pods only through Secrets, never the ConfigMap [evidence: test:tests/test_chart.py::test_secrets_wired]
- AC3: a missing postgres or orchestrator value fails the render [evidence: test:tests/test_chart.py::test_required_values]
- AC4: helm lint passes [evidence: command:helm lint chart/agents-schedule --set postgres.url=postgresql://x/y --set orchestrator.url=http://o --set orchestrator.token=t]

#### Files

- `chart/agents-schedule/Chart.yaml`
- `chart/agents-schedule/values.yaml`
- `chart/agents-schedule/templates/_helpers.tpl`
- `chart/agents-schedule/templates/_config.tpl`
- `chart/agents-schedule/templates/deployment.yaml`
- `chart/agents-schedule/templates/service.yaml`
- `chart/agents-schedule/templates/configmap.yaml`
- `tests/test_chart.py`

#### Interfaces

- Part `agents-schedule-chart-core`: chart values listed above (file `chart/agents-schedule/values.yaml`).

#### Expected outcome

`helm template` renders a working api and worker from values, with no secret in a ConfigMap.

#### Steps

- Write tests/test_chart.py; run: fails (no chart).
- Write the chart; `uv run --frozen pytest tests/test_chart.py -q`: `3 passed`.
- `helm lint` clean.

#### Notes

- do-not-build: an in-chart CNPG; agents-helmfile deploys `agents-schedule-db` as a separate cnpg/cluster release.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S17: chart ingress and test hook

- Status: done
- Files: `chart/agents-schedule/templates/ingress.yaml`, `chart/agents-schedule/templates/tests/test-connection.yaml`, `chart/agents-schedule/values.yaml`, `tests/test_chart_ingress.py`
- Verify: `uv run --frozen pytest tests/test_chart_ingress.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: e2b75eb99625dbc15c2ca39e02708ad02bd6dfe8

#### Requirement

Finish the chart (design D13; approvals A1, A6):

- `ingress {enabled: false, className, annotations, denySourceRanges, hosts[].paths[] {path, pathType}, tls}` renders an Ingress to the api Service port `http` (as `code/agents-orchestrator/chart/agents-orchestrator/templates/ingress.yaml`). The chart adds no cert-manager annotation of its own: per the URL layout of frontend-decoupling (contract `agents-web-url-layout`), only one Ingress of the host carries it and the others reference the same TLS secret.
- `templates/tests/test-connection.yaml`: a helm test Pod hitting `/healthz` on the api Service.
- Chart `version: 0.1.0`, `appVersion` set by CI.
- tests/test_chart_ingress.py asserts the Ingress host, path `/schedules` (Prefix) and TLS secret from values, the deny annotation, no cert-manager annotation by default, and the test hook.

#### Acceptance conditions

- AC1: an enabled ingress routes the configured host and path to the api Service [evidence: test:tests/test_chart_ingress.py::test_ingress_routes_path]
- AC2: the chart adds no cert-manager annotation by default [evidence: test:tests/test_chart_ingress.py::test_no_cert_manager_annotation]
- AC3: the helm test hook hits /healthz [evidence: test:tests/test_chart_ingress.py::test_connection_hook]

#### Files

- `chart/agents-schedule/templates/ingress.yaml`
- `chart/agents-schedule/templates/tests/test-connection.yaml`
- `chart/agents-schedule/values.yaml`
- `tests/test_chart_ingress.py`

#### Interfaces

- Contract `agents-schedule-chart`: `oci://harbor.szymonrichert.pl/charts/agents-schedule` (versions `X.Y.Z` on tag, `X.Y.Z-main.<sha7>` on main), values as in `helm-chart` plus `ingress` (file `code/agents-schedule/chart/agents-schedule/values.yaml`), consumed by agents-helmfile.

#### Expected outcome

The chart is complete and publishable; agents-helmfile can route `/schedules` to it on the lab host.

#### Steps

- Write tests/test_chart_ingress.py; run: fails.
- Write ingress.yaml, the test hook and the values; `uv run --frozen pytest tests/test_chart_ingress.py -q`: `3 passed`.
- `helm lint` clean.

#### Notes

- Prefix `/schedules` owns the service's whole path space per `agents-web-url-layout`; the API answers at `/schedules/api/v1`.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done

### S18: kind e2e api

- Status: done
- Files: `scripts/e2e.sh`, `e2e/values-kind.yaml`, `e2e/fake-orchestrator.yaml`, `tests/e2e/__init__.py`, `tests/e2e/test_e2e_kind.py`
- Verify: `bash -n scripts/e2e.sh && uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e && uv run ruff check . && uv run ruff format --check .`
- Verified head: fc99d8cd9f28eaf0788e219d42a84c624ca9e7e2

#### Requirement

Add the API-only kind e2e (design D11, D15; approval A5), modelled on `code/agents-orchestrator/scripts/e2e.sh` and `tests/e2e/test_e2e_kind.py`. Every capability of the API is exercised over HTTP through a port-forward to the api Service; no UI is touched.

- `scripts/e2e.sh`: creates a kind cluster, builds and loads the image, installs a Postgres (the orchestrator e2e's approach), deploys the agents-common fake orchestrator (contract `agents-common-lib`, a Starlette app) from the agents-schedule image with `uvicorn agents_common.fake_orchestrator:app` (`e2e/fake-orchestrator.yaml`), installs the chart with `e2e/values-kind.yaml` (`components.worker.replicas: 2`, `SCHED_TICK_SECONDS: 2`, `SCHED_POLL_SECONDS: 1`), runs `pytest -m e2e tests/e2e`, deletes the session on exit.
- `test_e2e_kind.py` covers: create with validation 422s (cron, timezone, unknown preset), list, get, replace, preview, disable and enable, run now -> handled, a `* * * * *` schedule fires within 90 s and is handled, an overlapping fire while a turn is held running -> `ignored previous_running`, a failed turn -> `failed turn_failed`, reuse on (a preset with `reuse_running_agent` true: a second run after the first finished posts its prompt to the first run's still-running session, `reuse delivered`, no second session create) and reuse off (a preset without the flag: every run creates its own session), run lists and get, delete -> 404; with 2 worker replicas each fire time has exactly one run and one session create. Turn outcomes are steered through the fake's own controls.
- `mise run test:e2e` (defined by `scaffold-project-and-cli`) runs `bash scripts/e2e.sh`.

#### Acceptance conditions

- AC1: the e2e suite collects and the script parses [evidence: command:bash -n scripts/e2e.sh && uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e]
- AC2: the kind e2e passes end to end [evidence: command:mise run test:e2e]
- AC3: the e2e hits every route in openapi.json [evidence: judgement:test_every_route_exercised compares the routes the e2e client recorded with openapi.json paths and passes inside mise run test:e2e]
- AC4: two workers produce exactly one run and one session per fire time [evidence: judgement:the e2e asserts one run per (schedule, fire_time) and one create call per run via the fake orchestrator /_calls]
- AC5: with reuse on a later run posts to the earlier run's running session and with reuse off it creates its own [evidence: judgement:the e2e asserts, via the fake orchestrator /_calls, zero create calls for the reused run and one create per run for the preset without the flag]

#### Files

- `scripts/e2e.sh`
- `e2e/values-kind.yaml`
- `e2e/fake-orchestrator.yaml`
- `tests/e2e/__init__.py`
- `tests/e2e/test_e2e_kind.py`

#### Interfaces

- `mise run test:e2e` (part `sched-kind-e2e`); CI job `e2e` runs it.

#### Expected outcome

A headless e2e in kind proves create, validate, preview, fire, overlap, failure, reuse on and off, run now, history and delete.

#### Steps

- Write test_e2e_kind.py and the fake orchestrator; `uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e` collects.
- Write e2e.sh and the values; `mise run test:e2e`: all e2e tests pass.
- Lint clean.

#### Notes

- `test_every_route_exercised` compares the routes hit (recorded by the test client wrapper) with `openapi.json` paths; it runs inside the e2e session.
- do-not-build: a second fake orchestrator; agents-common ships one. If it cannot hold a turn running or fail one, that is a gap in `agents-common-lib`: report it as `discovered` against agents-common and cover those two cases in tests/test_dispatcher.py and tests/test_tracker.py only.
- Real orchestrator coverage is the live smoke (`smoke-schedule-check`).

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule

- 2026-10-25 done: kind run verified statically; real run in the PR CI e2e job before close

### S19: epic review fixes

- Status: done
- Files: `src/agents_schedule/dispatcher.py`, `src/agents_schedule/tracker.py`, `src/agents_schedule/scheduler.py`, `src/agents_schedule/db/runs.py`, `src/agents_schedule/api/runs.py`, `src/agents_schedule/runtime.py`, `Dockerfile`, `tests/test_dispatcher.py`, `tests/test_tracker.py`, `tests/test_entrypoints.py`, `tests/test_ci_workflow.py`
- Verify: `uv run --frozen pytest tests/test_dispatcher.py tests/test_tracker.py tests/test_scheduler.py tests/test_api_runs.py tests/test_entrypoints.py tests/test_ci_workflow.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: d4f6a925b17988e300da312ac8fa3b2a70d6744e

#### Requirement

Fix the findings of the phase 5 epic review and security review of agents-schedule-microservice (design D9, D11; review focus: exactly-once, the allowlist reads only the socket peer).

- Per-run fault isolation: in `agents_schedule.dispatcher` (`resume_pending`, `dispatch_once`) and `agents_schedule.tracker` (the `track_once` loop), an unexpected exception while handling one run (anything other than the orchestrator errors already handled, for example a malformed orchestrator payload or a DB error on that run) is logged with `log.exception` naming the run id and the loop continues with the next run; it never escapes into the worker TaskGroup (`runtime.py:_hold_and_run`) and never kills the scheduler, dispatcher and tracker together. The same run is retried on a later pass, not skipped forever and not posted twice.
- The per-schedule fire lock shared by the scheduler and the run-now route is a public helper, `agents_schedule.db.runs.fire_lock(conn, schedule_id)` (or a public `FIRE_LOCK` in `scheduler.py`), used by both `scheduler.py` and `api/runs.py`; no module imports a private name of another.
- The api server never rewrites the client address from forwarded headers: `runtime.py` builds `uvicorn.Config(..., proxy_headers=False)`, so `SourceAllowlist` sees the socket peer (the oauth2-proxy sidecar on 127.0.0.1) even when the request carries `X-Forwarded-For`.
- The Dockerfile pins the uv build image to an exact version tag (no `:latest`).

#### Acceptance conditions

- AC1: an unexpected exception on one run is logged and the dispatcher continues with the next run [evidence: test:tests/test_dispatcher.py::test_unexpected_error_isolated_per_run]
- AC2: an unexpected exception on one run is logged and the tracker continues with the next run [evidence: test:tests/test_tracker.py::test_unexpected_error_isolated_per_run]
- AC3: the scheduler and the run-now route share one public fire-lock helper [evidence: judgement:no `_FIRE_LOCK` or other private cross-module import in src/agents_schedule/api/runs.py]
- AC4: a request through a real uvicorn server from 127.0.0.1 carrying X-Forwarded-For of an outside address is admitted by the default allowlist, and the allowlist decision uses the socket peer [evidence: test:tests/test_entrypoints.py::test_api_ignores_forwarded_headers]
- AC5: the Dockerfile pins the uv image to an exact version [evidence: test:tests/test_ci_workflow.py::test_dockerfile_pins_uv]

#### Files

- `src/agents_schedule/dispatcher.py`
- `src/agents_schedule/tracker.py`
- `src/agents_schedule/scheduler.py`
- `src/agents_schedule/db/runs.py`
- `src/agents_schedule/api/runs.py`
- `src/agents_schedule/runtime.py`
- `Dockerfile`
- `tests/test_dispatcher.py`
- `tests/test_tracker.py`
- `tests/test_entrypoints.py`
- `tests/test_ci_workflow.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-25 done

### S20: release v0.1.0

- Status: done
- Files: `README.md`, `MEMORY.md`
- Verify: `git ls-remote --exit-code --tags origin v0.1.0 && uv run ruff check .`
- Verified head: 7b17349b71b1dd2c74e13fe97735259089f2e8c2

#### Requirement

Release agents-schedule v0.1.0 (design D14; approval A6). Runs after this epic's agents-schedule branch has merged to main and the main CI run is green. Tag the merged main commit `v0.1.0` and push the tag; CI `chart-publish-tag` publishes chart `0.1.0` and the main `images` job has published `harbor.szymonrichert.pl/containers/agents-schedule:<sha7>` for that commit. README `## Releases` records `v0.1.0` with the image sha7 and chart version; MEMORY.md records the release with the date.

#### Acceptance conditions

- AC1: tag v0.1.0 is on origin and points at a commit on main [evidence: command:git fetch origin --tags && git merge-base --is-ancestor v0.1.0 origin/main]
- AC2: chart 0.1.0 is published [evidence: command:helm show chart oci://harbor.szymonrichert.pl/charts/agents-schedule --version 0.1.0]
- AC3: the image for the tagged commit is published [evidence: command:docker manifest inspect harbor.szymonrichert.pl/containers/agents-schedule:$(git rev-parse --short=7 'v0.1.0^{}')]
- AC4: README records the release [evidence: doc-section:README.md#Releases]

#### Files

- `README.md`
- `MEMORY.md`

#### Interfaces

- Part `agents-schedule-release`: chart `0.1.0`, image `<sha7>` of tag v0.1.0; consumed by `deploy-schedule`.

#### Expected outcome

Chart 0.1.0 and its image are published and recorded.

#### Steps

- Confirm main CI is green on the merged commit (`gh run list -R szymonrychu/agents-schedule -b main -L 1`).
- `git tag v0.1.0 <merged sha> && git push origin v0.1.0`; wait for `chart-publish-tag` to succeed.
- AC2 and AC3 commands exit 0; write README ## Releases and the MEMORY entry.

#### Notes

- Irreversible: published chart versions are immutable and the tag is public (listed at the gate).
- The release sha is filled with `ticket.py amend` once the merge lands, as the precedent deploy-pin tasks do.

- 2026-10-25 amended: AC3 evidence resolved the annotated tag object, not its commit; peel with ^{}

- 2026-10-25 done

### S21: ci image checks and worker test flake

- Status: done
- Files: `.github/workflows/ci.yaml`, `tests/test_ci_workflow.py`, `tests/test_entrypoints.py`
- Verify: `uv run --frozen pytest tests/test_ci_workflow.py tests/test_entrypoints.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 814ba207c6aefac7bd672185812afe27dfc3c476

#### Requirement

Close two gaps found while verifying the epic (dockerfile-and-ci AC4, the full suite).

- The CI `images` job, after the existing `--help` smoke step and before any push, also asserts the image runs as uid 1000 and carries no dev dependency: `test "$(docker run --rm --entrypoint id agents-schedule:ci -u)" = 1000` and `! docker run --rm --entrypoint python agents-schedule:ci -c 'import pytest'`, so dockerfile-and-ci AC4 is checked on every PR, not only by hand.
- `tests/test_entrypoints.py::test_single_worker_fires` is deterministic: today it uses an every-minute schedule and a fixed sleep, so it fires twice when the run crosses a minute boundary (seen as `assert 2 == 1` in a full-suite run). Make the expected fire count independent of wall-clock minute boundaries (for example a schedule armed so exactly one fire time falls in the observed window, or asserting one run per fire_time and one lock holder) while still proving that a second worker never fires.

#### Acceptance conditions

- AC1: the images job asserts uid 1000 and no pytest in the image before any push [evidence: test:tests/test_ci_workflow.py::test_images_job_checks_uid_and_no_dev_deps]
- AC2: the single-worker test passes regardless of minute boundaries [evidence: test:tests/test_entrypoints.py::test_single_worker_fires]

#### Files

- `.github/workflows/ci.yaml`
- `tests/test_ci_workflow.py`
- `tests/test_entrypoints.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-25 done: CI images job green on 814ba20 incl. uid/no-pytest step

### S22: e2e two worker failure

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`, `scripts/e2e.sh`, `MEMORY.md`
- Verify: `bash -n scripts/e2e.sh && uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e && uv run --frozen pytest -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 4d085b85d05f8ab542e4a4ad3fd9794cd1089e82

#### Requirement

The kind e2e on PR #1 head 814ba20 failed (CI log: /Users/szymonri/Documents/claude-code-tatara/.logs/sched-pr1-e2e-814ba20.log; the same suite passed on fc99d8c): `test_two_workers_one_run_and_one_session_per_fire` got a 500 from the fake orchestrator control route `POST /_messages/None/complete` (the test asked to complete a run whose `message_id` was still None), and the next test, `test_delete_removes_the_schedule_and_its_runs`, failed with `Server disconnected without sending a response`. Find the root cause (a test race, a regression from the epic-review-fixes or ci-image-checks commits, or a port-forward or api pod failure) from the log and the code, prove it with a deterministic reproduction where one is possible, and fix the cause (product code if the product is wrong, the test if the test is inaccurate), without weakening the exactly-once assertions. The e2e is deterministic enough to pass on repeated CI runs, and a test does not complete a message before the run has a `message_id`.

#### Acceptance conditions

- AC1: the two-worker test never asks the fake orchestrator to complete a message that does not exist yet [evidence: judgement:tests/e2e/test_e2e_kind.py waits for a run's message_id before completing it, and the root cause is named in the component MEMORY.md]
- AC2: the e2e suite still collects every test [evidence: command:bash -n scripts/e2e.sh && uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e]
- AC3: the kind e2e passes in PR CI on the fixed head [evidence: judgement:PR #1 CI e2e job green on the head that contains this task]

#### Files

- `tests/e2e/test_e2e_kind.py`
- `scripts/e2e.sh`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-25 done: PR #1 CI e2e green on 4d085b8

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
