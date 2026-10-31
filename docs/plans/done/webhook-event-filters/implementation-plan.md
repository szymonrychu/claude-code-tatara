# webhook event filters implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: filters off event loop

- Status: done
- Files: `src/agents_webhook/filters.py`, `src/agents_webhook/ingest/app.py`, `src/agents_webhook/api/routes.py`, `tests/test_filters.py`, `tests/test_ingest_http.py`, `README.md`
- Verify: `uv run pytest tests/test_filters.py tests/test_ingest_http.py -o addopts= && uv run ruff check .`
- Verified head: 9f048aa

#### Requirement

Epic security review 2026-10-25 (medium): filter validation and evaluation, and regex compilation on a `_rule_set` cache miss, run synchronously inside the async ingest handler (ingest/app.py `verdict`, filters.py). The validated bounds allow 20 rules x 50 values = 1000 RE2 patterns per list, each searching every field text up to 65536 chars and every list element. One authenticated delivery against a large rule set can stall the event loop for seconds, blocking other endpoints' ingest and the probes. RE2 itself stays linear.

Fix in agents-webhook:
1. Run the filter verdict (classify plus filters.evaluate, including any compile on a cache miss) off the event loop via `asyncio.to_thread` in ingest, and in the api preview route.
2. Add a total budget per endpoint, enforced in `filters.validate`: at most 200 values summed across all allow and deny rules (`MAX_TOTAL_VALUES = 200`). The error carries the path, as other validation errors do. Keep the per-rule and per-list bounds.
3. Cap the number of list elements evaluated per field (`MAX_LIST_ITEMS = 100`). Past the cap, fail closed exactly like the oversize text rule: a regex or equals rule on a list longer than the cap cannot satisfy allow, and counts as a deny match.
4. Document both limits and the fail-closed list rule in the filters.py docstring and the README `## Filters`.

#### Acceptance conditions

- AC1: ingest and preview evaluate filters off the event loop [evidence: test:tests/test_ingest_http.py::test_filter_verdict_runs_off_event_loop]
- AC2: validation refuses more than 200 values in total, naming the path [evidence: test:tests/test_filters.py::test_total_values_budget]
- AC3: a list longer than MAX_LIST_ITEMS fails closed for allow and deny [evidence: test:tests/test_filters.py::test_oversized_list_fails_closed]
- AC4: the suite and lint pass [evidence: command:mise run test && mise run lint]

#### Files

- `src/agents_webhook/filters.py`
- `src/agents_webhook/ingest/app.py`
- `src/agents_webhook/api/routes.py`
- `tests/test_filters.py`
- `tests/test_ingest_http.py`
- `README.md`

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

### S2: normalize branch fields

- Status: done
- Files: `src/agents_webhook/normalize.py`, `tests/test_normalize.py`, `tests/payloads.py`
- Verify: `uv run pytest tests/test_normalize.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: efacbaa

#### Requirement

Add the PR/MR branch names to the normalized event, so endpoint filters can match them (design D3; user follow-up 2026-10-25, verbatim: "other fields: title regex, branch name, etc"; user decision: "branch name (source/target for PR/MR)"). Paths are in code/agents-webhook.

- `NormalizedEvent` gains `source_branch: str | None = None` and `target_branch: str | None = None` (defaults, so `ingest/app.py:_unparsed` and `db/events.py:to_normalized` keep constructing it unchanged).
- GitHub (`github-pr` endpoints): `pull_request`, `pull_request_review` and `pull_request_review_comment` set `source_branch` from `pull_request.head.ref` and `target_branch` from `pull_request.base.ref`. `issue_comment` on a PR carries no branch: both stay None. `github-issue` events: both None.
- GitLab (`gitlab-mr` endpoints): `Merge Request Hook` sets them from `object_attributes.source_branch` and `object_attributes.target_branch`; `Note Hook` on a merge request from `merge_request.source_branch` and `merge_request.target_branch`. `gitlab-issue` events: both None.
- Grafana: both None.
- A missing or non-string ref yields None, never an exception.
- The branches are not stored as event columns and not added to the prompt context (design D3: the payload already holds them).

#### Acceptance conditions

- AC1: a GitHub pull_request event carries head.ref as source_branch and base.ref as target_branch [evidence: test:tests/test_normalize.py::test_github_pr_branches]
- AC2: GitHub pull_request_review and pull_request_review_comment events carry both branches; issue_comment on a PR and github-issue events carry None [evidence: test:tests/test_normalize.py::test_github_branches_per_event]
- AC3: a GitLab Merge Request Hook and a Note Hook on a merge request carry both branches; gitlab-issue events carry None [evidence: test:tests/test_normalize.py::test_gitlab_mr_branches]
- AC4: grafana-alert events and payloads with a missing or non-string ref carry None without raising [evidence: test:tests/test_normalize.py::test_branches_absent_are_none]
- AC5: the existing normalize suite and lint pass [evidence: command:uv run pytest tests/test_normalize.py -q && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_webhook/normalize.py`
- `tests/test_normalize.py`
- `tests/payloads.py`

#### Interfaces

- `src/agents_webhook/normalize.py:NormalizedEvent`: adds `source_branch: str | None = None`, `target_branch: str | None = None` after `changed` (contract `webhook-normalized-event`, consumed by filter-rules-engine).
- `normalize(endpoint_type, headers, payload)` signature unchanged.

#### Expected outcome

`normalize("github-pr", ...)` and `normalize("gitlab-mr", ...)` return events whose `source_branch` and `target_branch` are the PR/MR head and base branch names; every other event has None.

#### Steps

- Red: add the four tests to `tests/test_normalize.py`, extending the builders in `tests/payloads.py` with `head`/`base` refs (GitHub) and `source_branch`/`target_branch` (GitLab MR attrs and the Note Hook `merge_request`). Run `uv run pytest tests/test_normalize.py -q`: the new tests fail with `AttributeError` or `TypeError` on the missing fields.
- Green: add the two fields and set them in `_github` and `_gitlab`. Run the verify: all pass, lint clean.

#### Notes

- `_event(...)` passes `**fields` into `NormalizedEvent`; add the branches as keyword fields there.
- GitHub: in `_github`, `item` is `payload["pull_request"]` for the three PR events; for `issue_comment`, `item` is the issue and has no `head`.
- GitLab: in `_gitlab`, `item` is `object_attributes` for MR hooks and `payload["merge_request"]` for notes.
- Use a small helper that returns the value only when it is a non-empty `str`.

- 2026-10-25 done

### S3: web preview stale on filter edit

- Status: done
- Files: `src/webhooks/CreateEndpointDialog.tsx`, `src/webhooks/Endpoints.test.tsx`
- Verify: `npx vitest run src/webhooks/Endpoints.test.tsx && npx tsc -b && npm run lint`
- Verified head: da936ab

#### Requirement

Epic whole-diff review 2026-10-25 (medium, /Users/szymonri/Documents/claude-code-tatara/.scratchpad/wef-epic-review.md): in agents-web src/webhooks/CreateEndpointDialog.tsx the FiltersEditor is wired as `onChange={setFilters}`, so editing a rule does not clear the preview's `filterResult` or `rendered`. Template edits do clear them, and so does FiltersDialog's edit. After a Preview shows "Passes the filters", changing a deny rule so it would match leaves the stale green verdict until Preview is pressed again, so the user can create the endpoint believing it. Fix: any filter change clears the preview result and the rendered prompt, the same way a template edit does. Add a test: preview passes, a rule is edited, and the verdict and the rendered prompt are gone.

#### Acceptance conditions

- AC1: editing a filter rule clears the create dialog's preview verdict and rendered prompt [evidence: test:src/webhooks/Endpoints.test.tsx::clears the preview result when a filter rule changes]
- AC2: the suite, typecheck and lint pass [evidence: command:npx vitest run && npx tsc -b && npm run lint]

#### Files

- `src/webhooks/CreateEndpointDialog.tsx`
- `src/webhooks/Endpoints.test.tsx`

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

### S4: filter rules engine

- Status: done
- Files: `src/agents_webhook/filters.py`, `tests/test_filters.py`, `pyproject.toml`, `uv.lock`
- Verify: `uv sync && uv run pytest tests/test_filters.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 07aba14

#### Requirement

Build the filter rules engine: per-endpoint allow and deny rules over the normalized event fields, validated on save and evaluated without any I/O (design D2, D3, D4). User request 2026-10-25, verbatim: "for each of supported webhooks add whiltelisting/blacklisting ability- e.g. grafana webhooks should blacklist if a label X consist of value Y, or issue/mr webhook will be received but internall ignorred if author is not one of the usernames from the list (or repos)- in general whitelist/blacklist capability for webhooks allowing for greater granularity in how to react to webhook events." Follow-up, verbatim: "other fields: title regex, branch name, etc". Constraint: "user-supplied regex on a public ingest path must not allow ReDoS. Pick a safe engine or bounds, and name it." Paths are in code/agents-webhook.

New module `src/agents_webhook/filters.py`:

- `FIELDS: dict[str, tuple[str, ...]]`, exactly design D3: `github-issue` and `gitlab-issue`: author, actor, repo, labels, title, body, comment, kind, action; `github-pr` and `gitlab-mr`: the same plus source_branch, target_branch; `grafana-alert`: labels, title, body. Field to event attribute: author -> `author`, actor -> `actor`, repo -> `repo`, labels -> `labels`, title -> `title`, body -> `body`, comment -> `comment_body`, kind -> `kind`, action -> `action`, source_branch -> `source_branch`, target_branch -> `target_branch`.
- `MATCHES = ("equals", "regex")`; `EMPTY = {"allow": [], "deny": []}`; `DENIED = "filter_denied"`; `NOT_ALLOWED = "filter_not_allowed"`; bounds `MAX_RULES = 20` per list, `MAX_VALUES = 50` per rule, `MAX_VALUE_LENGTH = 256`, `MAX_TEXT = 65536` characters read from a text field.
- `validate(endpoint_type: str, data: Any) -> dict`: returns the canonical form `{"allow": [{"field", "match", "values"}], "deny": [...]}` (`match` defaults to `"equals"`, `None` or a missing list means empty) or raises `ValueError` whose message starts with the path, for example `filters.deny[0].field: 'repo' does not apply to grafana-alert`, `filters.allow[1].values[2]: not a valid RE2 pattern (...)`. It refuses: a non-object, unknown top-level keys, an unknown rule key, a field outside `FIELDS[endpoint_type]`, a match outside `MATCHES`, more than `MAX_RULES` rules in a list, zero or more than `MAX_VALUES` values, a value that is not a string or is empty or longer than `MAX_VALUE_LENGTH`, a Grafana `labels` value without `=` or with an empty key, and any regex RE2 does not compile (backreferences, lookaround).
- `evaluate(event: NormalizedEvent, filters: Mapping) -> str | None` (filters in the canonical form, the endpoint type is `event.type`): the first deny rule in order that matches returns `"filter_denied: <field>"`; otherwise the first allow rule that does not match returns `"filter_not_allowed: <field>"`; otherwise None. Compiled rule sets are cached per canonical JSON (bounded).
- Matching, design D2: a rule matches when any of its values matches. An absent field value (None) never matches. List fields (forge `labels`) match when any element matches. `equals` is case-insensitive (casefold) for author, actor, repo and forge labels and case-sensitive for every other field. `regex` is an unanchored RE2 search on the first `MAX_TEXT` characters. Grafana `labels` (a dict): a value `key=value` splits on the first `=`; `equals` compares `labels[key]` exactly, `regex` searches `labels[key]` with the part after `=`; a key absent from the dict never matches.
- The regex engine is RE2 through the `google-re2` package (module `re2`), added to `pyproject.toml` dependencies and `uv.lock`. stdlib `re` is never used on a user pattern.

#### Acceptance conditions

- AC1: FIELDS lists exactly the fields of design D3 for each of the five endpoint types [evidence: test:tests/test_filters.py::test_fields_per_type]
- AC2: validate returns the canonical form with match defaulting to equals and missing lists empty [evidence: test:tests/test_filters.py::test_validate_canonical_form]
- AC3: validate refuses each invalid input listed in the requirement with a ValueError whose message starts with the rule path [evidence: test:tests/test_filters.py::test_validate_rejects_with_path]
- AC4: validate refuses a field that does not apply to the endpoint type (repo on grafana-alert, source_branch on github-issue) [evidence: test:tests/test_filters.py::test_validate_rejects_field_for_type]
- AC5: validate refuses patterns RE2 does not support, a backreference and a lookahead [evidence: test:tests/test_filters.py::test_validate_rejects_non_re2_patterns]
- AC6: validate enforces MAX_RULES, MAX_VALUES and MAX_VALUE_LENGTH [evidence: test:tests/test_filters.py::test_validate_bounds]
- AC7: a matching deny rule returns filter_denied: <field>, the first in list order, before any allow rule is checked [evidence: test:tests/test_filters.py::test_deny_first_match_wins]
- AC8: allow rules AND together and a rule's values OR together; the first failing allow rule returns filter_not_allowed: <field> [evidence: test:tests/test_filters.py::test_allow_rules_and_values_or]
- AC9: an absent field fails an allow rule and never matches a deny rule [evidence: test:tests/test_filters.py::test_absent_field_fails_allow_not_deny]
- AC10: equals is case-insensitive for author, actor, repo and forge labels and case-sensitive for branches and title [evidence: test:tests/test_filters.py::test_equals_case_rules]
- AC11: regex is an unanchored search, honours (?i), and reads only the first MAX_TEXT characters of a text field [evidence: test:tests/test_filters.py::test_regex_search_semantics]
- AC12: Grafana label rules match key=value with equals and key=<regex> with regex, and a missing key never matches [evidence: test:tests/test_filters.py::test_grafana_label_rules]
- AC13: the pattern (a+)+$ against 100000 'a' characters followed by '!' evaluates in under one second [evidence: test:tests/test_filters.py::test_catastrophic_pattern_is_linear]
- AC14: no stdlib re call compiles a user pattern in filters.py [evidence: command:! grep -nE '^\s*import re$|re\.(compile|search|match|fullmatch)\(' src/agents_webhook/filters.py]
- AC15: google-re2 is a locked runtime dependency [evidence: command:grep -q 'google-re2' pyproject.toml && grep -q 'name = "google-re2"' uv.lock]
- AC16: the filters suite and lint pass [evidence: command:uv run pytest tests/test_filters.py -q && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_webhook/filters.py`
- `tests/test_filters.py`
- `pyproject.toml`
- `uv.lock`

#### Interfaces

- `src/agents_webhook/filters.py` (contract `webhook-filters`): `FIELDS`, `MATCHES`, `EMPTY`, `DENIED`, `NOT_ALLOWED`, `MAX_RULES`, `MAX_VALUES`, `MAX_VALUE_LENGTH`, `MAX_TEXT`, `validate(endpoint_type: str, data: Any) -> dict`, `evaluate(event: NormalizedEvent, filters: Mapping[str, Any]) -> str | None`. Consumed by endpoint-filters-storage (validate on write), ingest-applies-filters (evaluate), api-endpoint-filters (validate, FIELDS for `/meta`, evaluate for the preview).
- Reads `NormalizedEvent` including `source_branch`/`target_branch` from normalize-branch-fields.

#### Expected outcome

`validate("grafana-alert", {"deny": [{"field": "labels", "values": ["env=staging"]}]})` returns the canonical dict; `evaluate` of a Grafana event whose `commonLabels` has `env: staging` returns `"filter_denied: labels"`; a GitHub PR by `mallory` against `{"allow": [{"field": "author", "values": ["alice"]}]}` returns `"filter_not_allowed: author"`; a catastrophic pattern runs in linear time.

#### Steps

- `uv add google-re2` (writes pyproject.toml and uv.lock); confirm `uv run python -c "import re2; re2.compile('a+')"` works.
- Red: write `tests/test_filters.py` with the thirteen named tests, building events with `NormalizedEvent(...)` directly (no payload parsing). Run `uv run pytest tests/test_filters.py -q`: collection fails on the missing module.
- Green: write `filters.py`. Run the verify: all pass, lint clean.

#### Notes

- RE2 Python API: `re2.compile(pattern)` raises `re2.error` on an unsupported pattern; compiled objects have `.search(text)`. Map `re2.error` to `ValueError` with the rule path.
- The ReDoS test must bound wall time (`time.monotonic()` around `evaluate`, assert < 1.0 s) so it would fail on a backtracking engine; do not mark it slow or skip it.
- Grafana `labels` is a `dict[str, str]`; forge `labels` is a `list[str]` (see `normalize.py`). The type of `event.labels` follows `event.type`.
- Keep `filters.py` free of I/O and of FastAPI/pydantic imports; the API layer has its own schema (api-endpoint-filters).
- No stored filter JSON exists yet; storage is the next task.

- 2026-10-25 done

### S5: endpoint filters storage

- Status: done
- Files: `src/agents_webhook/migrations/0004_endpoint_filters.sql`, `src/agents_webhook/db/endpoints.py`, `tests/test_endpoints_repo.py`
- Verify: `uv run pytest tests/test_endpoints_repo.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 54502c4

#### Requirement

Store each endpoint's filters and load them with the endpoint (design D1). User decision: "Filters are per webhook endpoint and cover every supported type." Paths are in code/agents-webhook.

- Migration `src/agents_webhook/migrations/0004_endpoint_filters.sql`: `ALTER TABLE endpoints ADD COLUMN filters jsonb NOT NULL DEFAULT '{"allow": [], "deny": []}'::jsonb;` with a header comment that the api stays the only writer of `endpoints` (create, rotate credentials, replace filters, delete). Existing rows get empty filters. 0001-0003 are not edited.
- `db/endpoints.py`: `Endpoint` gains `filters: dict` (the canonical form of `filters.validate`); `_COLUMNS` includes `filters` and `authenticate` keeps `password_hash` as the last selected column, so its single compare-and-verify path is unchanged. `EndpointIn` gains `filters: Any = None`; `create` stores `filters.validate(data.type, data.filters)` (None stores `filters.EMPTY`) and lets its `ValueError` propagate with the `filters...` path, before any hashing or insert.
- New `set_filters(conn, id: int, data: Any) -> Endpoint | None`: in one transaction reads the endpoint's type (`FOR UPDATE`), validates `data` against it (`ValueError` propagates, nothing written), writes the canonical JSON and returns the updated `Endpoint`; None when the endpoint does not exist.
- `get`, `get_by_suffix`, `list_all` and `authenticate` return `filters`.

#### Acceptance conditions

- AC1: a migrated database has endpoints.filters, and an endpoint created without filters reads back {"allow": [], "deny": []} [evidence: test:tests/test_endpoints_repo.py::test_filters_default_empty]
- AC2: create stores the canonical filters and get, list_all and authenticate return them [evidence: test:tests/test_endpoints_repo.py::test_create_stores_filters]
- AC3: create with invalid filters raises ValueError starting with the filters path and inserts no row [evidence: test:tests/test_endpoints_repo.py::test_create_invalid_filters_inserts_nothing]
- AC4: set_filters replaces the filters and returns the updated endpoint; None for a missing id [evidence: test:tests/test_endpoints_repo.py::test_set_filters_replaces]
- AC5: set_filters validates against the endpoint's own type and writes nothing on a ValueError [evidence: test:tests/test_endpoints_repo.py::test_set_filters_validates_against_type]
- AC6: authenticate still returns None identically for an unknown suffix and a wrong password with the new column [evidence: test:tests/test_endpoints_repo.py::test_authenticate_failures_unchanged_with_filters]
- AC7: the endpoints repo suite and lint pass [evidence: command:uv run pytest tests/test_endpoints_repo.py -q && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_webhook/migrations/0004_endpoint_filters.sql`
- `src/agents_webhook/db/endpoints.py`
- `tests/test_endpoints_repo.py`

#### Interfaces

- `src/agents_webhook/db/endpoints.py` (contract `webhook-endpoints`): `Endpoint.filters: dict`, `EndpointIn.filters: Any = None`, `create(...)` unchanged signature, new `set_filters(conn, id, data) -> Endpoint | None`. Consumed by ingest-applies-filters (`authenticate` returns filters) and api-endpoint-filters (create, set_filters).
- Uses `filters.validate`, `filters.EMPTY` (filter-rules-engine).
- Schema: `endpoints.filters jsonb NOT NULL` (migration 0004).

#### Expected outcome

Every endpoint row carries its filters; the repo validates them on create and on replace; ingest gets them from the one `authenticate` query it already runs.

#### Steps

- Red: add the six tests to `tests/test_endpoints_repo.py` (they use the existing `db` fixture with migrations applied). Run `uv run pytest tests/test_endpoints_repo.py -q`: the new tests fail (no column, no `set_filters`). Docker must be running (testcontainers Postgres).
- Green: the migration, the dataclass fields, `_COLUMNS`, `create`, `set_filters`. Run the verify: all pass, lint clean.

#### Notes

- `Endpoint(*row[:-1])` in `authenticate` is positional over `_COLUMNS`; put `filters` in `_COLUMNS` (and in the dataclass at the same position) so the slice still drops only `password_hash`. `expected_username = row[5]` indexes the username: keep `username` at index 5 or update the index.
- Write JSON with `psycopg.types.json.Jsonb` (as `db/events.py` does).
- `Endpoint` is frozen; a `dict` field is fine for reading. Callers never mutate it.
- The row-level writer rule (api only) is unchanged: ingest still only reads.

- 2026-10-25 done

### S6: ingest applies filters

- Status: done
- Files: `src/agents_webhook/ingest/app.py`, `tests/test_ingest_http.py`, `README.md`, `tests/test_readme_config.py`, `tests/test_event_store.py`
- Verify: `uv run pytest tests/test_ingest_http.py tests/test_readme_config.py tests/test_event_store.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 5afc237

#### Requirement

Apply each endpoint's filters at ingest (design D1, D3, D5, D10). User decision: "A delivery that fails a filter is accepted and stored as ignored with a reason, not rejected." Gate Q2 working answer: the built-in rules run first. Paths are in code/agents-webhook.

- `ingest/app.py:_deliver`: after `normalize` and `classify`, when classify returns None, `reason = filters.evaluate(event, endpoint.filters)`. The delivery is recorded through `events.record(..., ignore_reason=reason)` exactly as other ignore reasons, answers 202 `{id, status: "ignored", reason}`, sends no NOTIFY and never reaches the queue. The order before it (429, 401, 413, ping, 400) is unchanged; `type_mismatch` and `unsupported_event` deliveries skip filters.
- Logs: the existing `ingest: recorded ... reason=...` line carries the filter reason; no rule, value or payload text is logged.
- README: `## Statuses and reasons` gains `filter_denied` (a deny rule of the endpoint matched; the reason names the field, `filter_denied: <field>`) and `filter_not_allowed` (an allow rule of the endpoint did not match, `filter_not_allowed: <field>`); `## Ingest` names the filter step after classify. A new `## Filters` section documents design D2-D4: the rule shape, deny-then-allow order, AND across allow rules and OR within values, absent fields, the case rules, RE2 search semantics and syntax limits (no backreferences or lookaround), Grafana `key=value`, the bounds, and the field table per type from design D3 including which fields do not apply to which type and why.
- `tests/test_readme_config.py`: `REASONS` gains `filter_denied` and `filter_not_allowed`; `test_sections_exist` gains `Filters`; a new test asserts every field of every type in `filters.FIELDS` appears in the `## Filters` section.
- `tests/test_event_store.py::test_record_ignore_reason_is_ignored_with_fields`: its sample reason `author_not_allowed` is replaced by `filter_not_allowed: author` (the store accepts any reason; this keeps the sample list on reasons that will still exist after retire-allowed-authors).

#### Acceptance conditions

- AC1: a delivery matching an endpoint deny rule answers 202 ignored with reason filter_denied: <field> and is stored ignored [evidence: test:tests/test_ingest_http.py::test_deny_filter_ignores_delivery]
- AC2: a delivery failing an endpoint allow rule answers 202 ignored with reason filter_not_allowed: <field> [evidence: test:tests/test_ingest_http.py::test_allow_filter_miss_ignores_delivery]
- AC3: a delivery passing the filters is stored new and notified as before [evidence: test:tests/test_ingest_http.py::test_passing_filters_queues_delivery]
- AC4: a delivery the built-in rules ignore keeps its built-in reason even when a filter would also match [evidence: test:tests/test_ingest_http.py::test_builtin_reason_wins_over_filter]
- AC5: an unauthenticated request to an endpoint with filters is 401 before any filter runs [evidence: test:tests/test_ingest_http.py::test_filters_never_run_before_auth]
- AC6: README documents filter_denied and filter_not_allowed under Statuses and reasons [evidence: test:tests/test_readme_config.py::test_every_status_and_reason_is_documented]
- AC7: README has a Filters section naming every field of every type in filters.FIELDS [evidence: test:tests/test_readme_config.py::test_filters_section_lists_every_field]
- AC8: the record store test samples filter_not_allowed: author instead of author_not_allowed [evidence: test:tests/test_event_store.py::test_record_ignore_reason_is_ignored_with_fields]
- AC9: the ingest, README config and event store suites and lint pass [evidence: command:uv run pytest tests/test_ingest_http.py tests/test_readme_config.py tests/test_event_store.py -q && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_webhook/ingest/app.py`
- `tests/test_ingest_http.py`
- `README.md`
- `tests/test_readme_config.py`
- `tests/test_event_store.py`

#### Interfaces

- `src/agents_webhook/ingest/app.py:create_ingest_app` behaviour: 202 `{id, status, reason}` with `reason` in `filter_denied: <field>` / `filter_not_allowed: <field>` (contract `webhook-ingest-url`, response shape unchanged).
- Uses `filters.evaluate` (filter-rules-engine) and `Endpoint.filters` from `endpoints.authenticate` (endpoint-filters-storage).

#### Expected outcome

An endpoint with `{"deny": [{"field": "title", "match": "regex", "values": ["^WIP"]}]}` answers a `WIP: x` PR with 202 ignored `filter_denied: title`; the README explains every field and rule.

#### Steps

- Red: add the five ingest tests (create the endpoint with filters through `endpoints.create`), the README tests and the store sample change. Run `uv run pytest tests/test_ingest_http.py tests/test_readme_config.py tests/test_event_store.py -q`: the new ingest tests fail (delivery stored new), the README tests fail (no reasons, no section). Docker must be running.
- Green: the evaluate call in `_deliver`, the README sections. Run the verify: all pass, lint clean.

#### Notes

- `classify` still takes `allowed_authors` here; retire-allowed-authors removes it later. Do not touch it in this task.
- Keep the module docstring's step list accurate (it names the per-request order).
- The README field table is design D3's table; copy its applicability and the "not offered" list.

- 2026-10-25 done

### S7: api endpoint filters

- Status: done
- Files: `src/agents_webhook/api/schemas.py`, `src/agents_webhook/api/routes.py`, `tests/test_api.py`, `README.md`, `openapi.json`
- Verify: `uv run pytest tests/test_api.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 3685ee0

#### Requirement

Expose endpoint filters in the UI API (design D6, D10). User decision: "Configurable in the endpoints API and the agents-web Webhooks UI, including in the existing example-JSON preview flow if cheap: show whether the example passes the filters." Paths are in code/agents-webhook.

- `api/schemas.py`: `FilterRule {field: str, match: "equals" | "regex" = "equals", values: list[str]}`, `Filters {allow: list[FilterRule] = [], deny: list[FilterRule] = []}`, `FilterResult {passed: bool, reason: str | None}`. `EndpointIn.filters: Filters | None = None`; `EndpointView.filters: Filters` (always present, so `EndpointCreated` carries it too); `PreviewIn.template: str | None = None` and `PreviewIn.filters: Filters | None = None`; `PreviewOut {prompt: str | None, filters: FilterResult | None}`; `Meta.filter_fields: dict[str, list[str]]`.
- `POST /webhooks/api/v1/endpoints`: passes `filters` to `endpoints.create`; a `ValueError` from validation is 422 `invalid_request` with the message naming the rule path (as other field errors).
- New `PUT /webhooks/api/v1/endpoints/{id}/filters` with body `Filters`: `endpoints.set_filters`; 200 `EndpointView`; 404 `not_found` for an unknown id; 422 `invalid_request` naming the rule path. Logs `api: endpoint filters replaced id=<id>` without the rules.
- `POST /webhooks/api/v1/templates/preview`: `template` and `filters` are each optional, at least one is required (else 422 `invalid_request`, message `template or filters: required`). When `filters` is given it is validated against `type` (422 naming the path) and evaluated with `filters.evaluate` on the normalized example: `filters = {passed: reason is None, reason}`; when absent, `filters` is null. When `template` is given the prompt renders as today; when absent, `prompt` is null. Nothing is stored.
- `GET /webhooks/api/v1/meta`: `filter_fields` is `filters.FIELDS` as lists, keyed by type.
- README `## API`: the `filters` body field and the `filters` view field, a `### PUT /webhooks/api/v1/endpoints/{id}/filters` section with a curl example, the new preview body and response, and `filter_fields` in meta. `openapi.json` regenerated with `uv run python -m agents_webhook.api.openapi > openapi.json`.

#### Acceptance conditions

- AC1: POST /endpoints with filters stores them and the 201 answer and GET /endpoints show them; without filters they show empty lists [evidence: test:tests/test_api.py::test_create_endpoint_with_filters]
- AC2: POST /endpoints with an invalid rule is 422 invalid_request naming the rule path and creates nothing [evidence: test:tests/test_api.py::test_create_endpoint_invalid_filters_422]
- AC3: PUT /endpoints/{id}/filters replaces the filters and returns the endpoint view [evidence: test:tests/test_api.py::test_put_filters_replaces]
- AC4: PUT /endpoints/{id}/filters is 404 not_found for an unknown id and 422 naming the path for a rule that does not apply to the type [evidence: test:tests/test_api.py::test_put_filters_errors]
- AC5: preview with filters only returns prompt null and filters {passed, reason} for a passing and a denied example, storing nothing [evidence: test:tests/test_api.py::test_preview_reports_filters]
- AC6: preview with neither template nor filters is 422 invalid_request [evidence: test:tests/test_api.py::test_preview_requires_template_or_filters]
- AC7: meta reports filter_fields equal to filters.FIELDS [evidence: test:tests/test_api.py::test_meta_reports_filter_fields]
- AC8: every route, including the PUT, is documented with a curl example and openapi.json has no drift [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC9: the API suite and lint pass [evidence: command:uv run pytest tests/test_api.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_webhook/api/schemas.py`
- `src/agents_webhook/api/routes.py`
- `tests/test_api.py`
- `README.md`
- `openapi.json`

#### Interfaces

- Contract `webhook-api` (README `## API`, `openapi.json`), extended: `EndpointIn.filters`, `EndpointView.filters`, `PUT /webhooks/api/v1/endpoints/{id}/filters` (body `Filters`, 200 `EndpointView`, 404, 422), `PreviewIn {template?, type, example, filters?}`, `PreviewOut {prompt: str | null, filters: {passed, reason} | null}`, `Meta.filter_fields`. Consumed by web-vendor-filters-api, smoke-webhook-filters, e2e-endpoint-filters.
- Uses `endpoints.create`, `endpoints.set_filters` (endpoint-filters-storage), `filters.validate`, `filters.evaluate`, `filters.FIELDS` (filter-rules-engine).

#### Expected outcome

`curl -X PUT -d '{"deny":[{"field":"labels","values":["env=staging"]}]}' $API/endpoints/3/filters` on a grafana-alert endpoint returns its view with the rule; the preview tells whether an example passes.

#### Steps

- Red: add the seven tests to `tests/test_api.py`. Run `uv run pytest tests/test_api.py -q`: they fail (no field, no route, preview requires template). Docker must be running.
- Green: schemas, routes, README API sections, regenerate `openapi.json`. Run the verify: all pass, `tests/test_readme_api.py` green (route documented, curl example, no drift), lint clean.

#### Notes

- Validate filters in the route with the endpoint type; pass the pydantic model as `model_dump()` into the repo, which validates again (single source `filters.validate`).
- Existing preview tests send `template`; they must keep passing unchanged (the response gains `filters: null`, `prompt` stays a string).
- `FilterRule.field` stays a plain `str` in the schema; the per-type check is `filters.validate`'s, so the error names the type.

- 2026-10-25 done

### S8: e2e endpoint filters

- Status: done
- Files: `tests/e2e/test_e2e_api.py`, `tests/e2e/conftest.py`
- Verify: `uv run pytest tests/e2e/test_e2e_api.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 2616d24

#### Requirement

Prove endpoint filters end to end through the API only (design D5, D7, D10), and move the e2e stack off `WEBHOOK_ALLOWED_AUTHORS` ahead of its retirement. Paths are in code/agents-webhook.

- `tests/e2e/test_e2e_api.py`, new tests on the real stack (Postgres, the three processes, the fake orchestrator): an endpoint created with a deny rule ignores a matching delivery with `filter_denied: <field>` and runs a non-matching one (handled, one cluster); an endpoint with an author allow rule ignores a stranger with `filter_not_allowed: author`; `PUT /endpoints/{id}/filters` with empty lists makes the next equal delivery run; the preview reports `passed` and `reason` for the endpoint's rules; a Grafana endpoint denying `env=staging` ignores a staging alert and runs a production one.
- `tests/e2e/test_e2e_api.py::test_ignore_reasons_are_listed`: the `author_not_allowed` case is no longer accurate once `WEBHOOK_ALLOWED_AUTHORS` is retired (design D7); it becomes a `github-issue` endpoint created with `{"allow": [{"field": "author", "values": ["alice", "bob"]}]}` whose stranger delivery is `filter_not_allowed: author`.
- `tests/e2e/conftest.py`: the stack no longer sets `WEBHOOK_ALLOWED_AUTHORS`; `WEBHOOK_BOT_LOGINS` stays.

#### Acceptance conditions

- AC1: a deny rule ignores a matching delivery with filter_denied and a non-matching delivery is handled [evidence: test:tests/e2e/test_e2e_api.py::test_deny_filter_ignores_and_others_run]
- AC2: an author allow rule ignores a stranger with filter_not_allowed: author [evidence: test:tests/e2e/test_e2e_api.py::test_allow_filter_ignores_stranger]
- AC3: replacing the filters through PUT makes the next equal delivery run [evidence: test:tests/e2e/test_e2e_api.py::test_put_filters_changes_the_outcome]
- AC4: a grafana-alert endpoint denying env=staging ignores the staging alert and runs the production one [evidence: test:tests/e2e/test_e2e_api.py::test_grafana_label_deny]
- AC5: the preview reports passed and reason for an endpoint's rules [evidence: test:tests/e2e/test_e2e_api.py::test_preview_reports_filter_outcome]
- AC6: the ignore-reasons test lists filter_not_allowed: author from an endpoint rule instead of author_not_allowed [evidence: test:tests/e2e/test_e2e_api.py::test_ignore_reasons_are_listed]
- AC7: the e2e stack no longer sets WEBHOOK_ALLOWED_AUTHORS [evidence: command:! grep -rn WEBHOOK_ALLOWED_AUTHORS tests/e2e]
- AC8: the e2e API suite and lint pass [evidence: command:uv run pytest tests/e2e/test_e2e_api.py -q && uv run ruff check . && uv run ruff format --check .]

#### Files

- `tests/e2e/test_e2e_api.py`
- `tests/e2e/conftest.py`

#### Interfaces

- Consumes contract `webhook-api` (api-endpoint-filters) and the ingest behaviour of ingest-applies-filters; no production code changes. `tests/e2e/conftest.py:Stack.create_endpoint(type, **body)` already forwards extra body keys, so `filters=` passes through.

#### Expected outcome

The API-only e2e suite proves deny, allow miss, pass, PUT replacement, Grafana label deny and the preview on the real stack, and nothing in it relies on `WEBHOOK_ALLOWED_AUTHORS`.

#### Steps

- Write the five new tests, change `test_ignore_reasons_are_listed` and drop the env line from the conftest.
- Red, by mutation: temporarily make `filters.evaluate` return None (do not commit this), run `uv run pytest tests/e2e/test_e2e_api.py -q -k "filter or ignore_reasons or grafana_label"`: the new tests and the changed reasons test fail on the missing `filter_*` reason. Restore the function. Docker must be running.
- Green: run the verify: all pass, lint clean.

#### Notes

- Test-only task: production behaviour came with ingest-applies-filters and api-endpoint-filters, so the red step is the mutation above; report it as such, with the failing output.
- The handled path needs the fake orchestrator to complete the turn, as `test_create_endpoint_receive_event_and_complete` does; reuse its waiting helpers.
- Payload builders are in `tests/payloads.py` (`gh_issues`, `gh_pull_request`, `grafana_alert(labels=...)`).

- 2026-10-25 done

### S9: smoke webhook filters

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`
- Verify: `uv run pytest tests/test_smoke_script.py -q && mise run lint`
- Verified head: 76b75ff

#### Requirement

Extend the live smoke with an endpoint filter check that cannot start a cluster (design D9). Paths are in code/agents-helmfile.

- `scripts/smoke.sh` step 8c: the temporary github-issue endpoint is created with `filters: {"deny": [{"field": "title", "match": "regex", "values": ["^smoke-deny"]}]}`; the create answer must echo that rule (`.filters.deny[0].field == "title"`), else fail `webhook: endpoint create did not store the filters`.
- New step after 8e: `POST /webhooks/api/v1/templates/preview` with `{type: "github-issue", example: <an opened issue titled "smoke-deny check">, filters: <the same rule>}` must answer `.filters.passed == false and .filters.reason == "filter_denied: title"` and `.prompt == null`; then `PUT /webhooks/api/v1/endpoints/<id>/filters` with `{"allow": [], "deny": []}` must answer `.filters.deny == []`. Each failure is a named `fail`. Log lines name each check.
- The existing closed-issue delivery stays the only ingested delivery (still `ignored/action_ignored`: built-in rules run before filters). No step ingests a delivery the built-in rules would pass, so a broken filter can never start a cluster. The trap still deletes the temporary endpoint on every exit path, including a failure in the new steps.
- `tests/test_smoke_script.py`: the fake API answers the new calls; the happy path asserts the new log lines; the failure table gains the filter-not-stored, preview-passed and PUT-not-applied cases, each asserting the endpoint is still deleted.

#### Acceptance conditions

- AC1: the happy path creates the endpoint with the deny rule, checks the preview reason and the PUT, and logs each check [evidence: test:tests/test_smoke_script.py::test_webhook_checks_happy_path]
- AC2: a create answer without the filters, a preview that passes, and a PUT that does not clear the rules each fail with a named message and still delete the endpoint [evidence: test:tests/test_smoke_script.py::test_webhook_filter_check_failures]
- AC3: the smoke still ingests only the closed-issue delivery [evidence: test:tests/test_smoke_script.py::test_webhook_smoke_ingests_only_the_closed_issue]
- AC4: the smoke prints no secret [evidence: test:tests/test_smoke_script.py::test_webhook_smoke_prints_no_secret]
- AC5: the smoke tests, shellcheck and lint pass [evidence: command:uv run pytest tests/test_smoke_script.py -q && mise run lint]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`

#### Interfaces

- Consumes contract `webhook-api` (api-endpoint-filters): `POST /endpoints` with `filters`, `PUT /endpoints/{id}/filters`, `POST /templates/preview` with `filters`.

#### Expected outcome

`mise run smoke` proves on the live namespace that filters are stored, evaluated and replaceable, with no new side effect beyond the temporary endpoint and the one ignored event.

#### Steps

- Red: extend `tests/test_smoke_script.py` (happy path, the new failure cases, the only-one-delivery test). Run `uv run pytest tests/test_smoke_script.py -q`: they fail on the missing calls and log lines.
- Green: the smoke.sh steps. Run the verify: all pass, shellcheck clean.

#### Notes

- Retro proposal (recurring): for every cleanup path ask what runs if the producing step fails or a variable is empty. Here: `ENDPOINT_ID` is set only after a successful create; the new steps run after it, so the trap's delete has an id; a failed create leaves `ENDPOINT_ID` empty and the trap must skip the delete (existing behaviour, keep it).
- Credentials stay on curl stdin as today; the new calls go to the api port-forward, which needs no credentials.

- 2026-10-25 done

### S10: web vendor filters api

- Status: done
- Files: `openapi/webhooks.json`, `openapi/webhooks.source`, `src/api/webhooks-schema.d.ts`, `src/webhooks/api.ts`, `src/webhooks/api.test.ts`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/webhooks/api.test.ts && npm run check:api && npx tsc -b && npm run lint`
- Verified head: 20f1694

#### Requirement

Vendor the extended webhook API into agents-web and expose it in the typed client (design D6, D8). User decision: "Configurable in the endpoints API and the agents-web Webhooks UI". Paths are in code/agents-web.

- `npm run sync:api -- webhooks --from ../agents-webhook` (the sibling agents-webhook checkout of this epic's integration tree, at the commit of api-endpoint-filters or later, with `openapi.json` committed): updates `openapi/webhooks.json`, `openapi/webhooks.source` and `src/api/webhooks-schema.d.ts`. No hand edits to the vendored files.
- `src/webhooks/api.ts`: exports types `Filters`, `FilterRule`, `FilterResult` from the schema, and `setEndpointFilters(endpointId: string, filters: Filters)` -> `PUT /endpoints/{id}/filters` returning `EndpointView`, the id URL-encoded like the other calls. `previewTemplate` keeps its name and now takes the optional `template` and `filters`.

#### Acceptance conditions

- AC1: setEndpointFilters sends PUT /webhooks/api/v1/endpoints/<encoded id>/filters with the filters as the JSON body [evidence: command:npx vitest run src/webhooks/api.test.ts -t "replaces endpoint filters"]
- AC2: previewTemplate sends filters without a template [evidence: command:npx vitest run src/webhooks/api.test.ts -t "previews filters without a template"]
- AC3: the vendored document and generated types match agents-webhook's openapi.json and carry the filters route [evidence: command:npm run check:api && grep -q '/webhooks/api/v1/endpoints/{id}/filters' openapi/webhooks.json && grep -q 'agents-webhook ' openapi/webhooks.source]
- AC4: the api tests, type check and lint pass [evidence: command:npx vitest run src/webhooks/api.test.ts && npx tsc -b && npm run lint]

#### Files

- `openapi/webhooks.json`
- `openapi/webhooks.source`
- `src/api/webhooks-schema.d.ts`
- `src/webhooks/api.ts`
- `src/webhooks/api.test.ts`

#### Interfaces

- Contract `web-webhook-client` (`src/webhooks/api.ts`): adds `Filters`, `FilterRule`, `FilterResult`, `setEndpointFilters`; `EndpointView.filters`, `WebhookMeta.filter_fields`, `PreviewIn`/`PreviewOut` follow the schema. Consumed by web-filters-editor, web-create-endpoint-filters, web-edit-endpoint-filters.
- Consumes contract `webhook-api` (api-endpoint-filters) through `openapi/webhooks.json`.

#### Expected outcome

The UI code can read and write endpoint filters and preview them with full types.

#### Steps

- Run `npm ci --no-audit --no-fund`, then `npm run sync:api -- webhooks --from ../agents-webhook`; expect the three vendored files to change.
- Red: add the two tests to `src/webhooks/api.test.ts`; run `npx vitest run src/webhooks/api.test.ts`: they fail on the missing export.
- Green: the exports in `api.ts`. Run the verify: all pass.

#### Notes

- `sync-api.mjs` refuses when the source `openapi.json` has uncommitted changes; the agents-webhook commit of api-endpoint-filters is already in the tree.
- Existing callers of `previewTemplate` (CreateEndpointDialog) still type-check because `template` stays accepted; their behaviour changes in web-create-endpoint-filters.

- 2026-10-25 done

### S11: retire allowed authors

- Status: done
- Files: `src/agents_webhook/settings.py`, `src/agents_webhook/normalize.py`, `src/agents_webhook/ingest/app.py`, `README.md`, `tests/test_normalize.py`, `tests/test_schema_settings.py`, `tests/test_readme_config.py`, `MEMORY.md`
- Verify: `uv run pytest tests/test_normalize.py tests/test_schema_settings.py tests/test_readme_config.py tests/test_ingest_http.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: d11f887

#### Requirement

Retire the global `WEBHOOK_ALLOWED_AUTHORS` setting and its reason `author_not_allowed`; per-endpoint `allow` rules on `author` replace them (design D7, gate Q1 working answer; brief: "Global env lists WEBHOOK_BOT_LOGINS and WEBHOOK_ALLOWED_AUTHORS already exist. Decide whether per-endpoint filters replace them. The house rule is no backward compatibility"). `WEBHOOK_BOT_LOGINS` and `self_event` stay. Paths are in code/agents-webhook.

- `settings.py`: `allowed_authors` removed from `WebhookSettings`; no alias, no deprecation path.
- `normalize.py:classify(event, *, bot_logins)`: the `allowed_authors` parameter and the `author_not_allowed` branch removed; the module docstring updated.
- `ingest/app.py`: the call no longer passes `allowed_authors`.
- README: the `WEBHOOK_ALLOWED_AUTHORS` row leaves `## Configuration`, `author_not_allowed` leaves `## Statuses and reasons`, and `## Filters` says that an author allowlist is an endpoint `allow` rule on `author`.
- Tests no longer accurate after the retirement, changed and named: `tests/test_normalize.py::test_classify_author_not_allowed` (removed: it tests the retired branch; `_classify` drops its `allowed` argument), `tests/test_schema_settings.py` default-values test (drops the `allowed_authors == []` clause), `tests/test_readme_config.py` (`REASONS` drops `author_not_allowed`).
- New retirement tests: `WebhookSettings` has no `allowed_authors` field and `WEBHOOK_ALLOWED_AUTHORS` set in the environment changes nothing (extra env is ignored); README mentions neither `WEBHOOK_ALLOWED_AUTHORS` nor `author_not_allowed`; `classify` has no `allowed_authors` parameter.
- MEMORY.md: a dated line: per-endpoint filters (allow and deny rules, RE2 regex, filtered deliveries stored ignored `filter_denied`/`filter_not_allowed`) replace `WEBHOOK_ALLOWED_AUTHORS`; `WEBHOOK_BOT_LOGINS` stays global as the self-loop guard; why.

#### Acceptance conditions

- AC1: WebhookSettings has no allowed_authors field [evidence: test:tests/test_schema_settings.py::test_allowed_authors_retired]
- AC2: classify takes no allowed_authors parameter and never returns author_not_allowed [evidence: test:tests/test_normalize.py::test_classify_has_no_author_allowlist]
- AC3: README no longer mentions WEBHOOK_ALLOWED_AUTHORS or author_not_allowed [evidence: test:tests/test_readme_config.py::test_retired_author_allowlist_not_documented]
- AC4: no source or chart file and no README line references allowed_authors or author_not_allowed [evidence: command:! git grep -n -e allowed_authors -e ALLOWED_AUTHORS -e author_not_allowed -- src chart README.md]
- AC5: self_event and WEBHOOK_BOT_LOGINS keep working [evidence: test:tests/test_normalize.py::test_classify_self_event]
- AC6: MEMORY.md records the replacement and why [evidence: command:grep -q 'WEBHOOK_ALLOWED_AUTHORS' MEMORY.md && grep -q 'filter' MEMORY.md]
- AC7: the touched suites and lint pass [evidence: command:uv run pytest tests/test_normalize.py tests/test_schema_settings.py tests/test_readme_config.py tests/test_ingest_http.py -q && uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_webhook/settings.py`
- `src/agents_webhook/normalize.py`
- `src/agents_webhook/ingest/app.py`
- `README.md`
- `tests/test_normalize.py`
- `tests/test_schema_settings.py`
- `tests/test_readme_config.py`
- `MEMORY.md`

#### Interfaces

- Contract `webhook-settings-env` loses `WEBHOOK_ALLOWED_AUTHORS` (consumer deploy-pin-webhook-filters drops it from the helmfile values).
- `normalize.classify(event, *, bot_logins: Collection[str]) -> str | None`.

#### Expected outcome

The only author allowlist is a per-endpoint filter rule; the service no longer reads `WEBHOOK_ALLOWED_AUTHORS`.

#### Steps

- Red: add the three retirement tests and apply the named test changes. Run `uv run pytest tests/test_normalize.py tests/test_schema_settings.py tests/test_readme_config.py -q`: the retirement tests fail (field, parameter and README rows still present).
- Green: remove the setting, the parameter and branch, the ingest kwarg and the README rows; add the MEMORY.md line. Run the verify: all pass, lint clean.

#### Notes

- Removal with a pinning test, not a file deletion, so the TDD cycle applies normally.
- e2e-endpoint-filters already moved the e2e stack and its reasons test off the setting; `tests/test_event_store.py` was moved by ingest-applies-filters.
- Ask of every removed line (retro proposal): what reads this value if it is still set in a live environment? `extra="ignore"` in `WebhookSettings.model_config` makes a leftover env var inert; the helmfile values drop it in deploy-pin-webhook-filters.

- 2026-10-25 done

### S12: web filters editor

- Status: done
- Files: `src/webhooks/FiltersEditor.tsx`, `src/webhooks/FiltersEditor.test.tsx`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/webhooks/FiltersEditor.test.tsx && npx tsc -b && npm run lint`
- Verified head: 7c01ade

#### Requirement

Build the filters editor component of the Webhooks UI (design D8). User request 2026-10-25, verbatim: "in general whitelist/blacklist capability for webhooks allowing for greater granularity in how to react to webhook events." User decision: "Configurable in the endpoints API and the agents-web Webhooks UI". Paths are in code/agents-web.

New `src/webhooks/FiltersEditor.tsx`, `FiltersEditor({type, fields, value, onChange})`:

- `fields` is `meta.filter_fields[type]` (the backend's catalogue; the component holds no field list of its own); `value` and `onChange` carry a `Filters` value.
- Two sections, "Allow (every rule must match)" and "Deny (any matching rule ignores the event)", each listing its rules and an "Add allow rule" / "Add deny rule" button. A rule row has a Field select over `fields`, a Match select (`equals`, `regex`), a Values text area (one value per line; blank lines dropped), and a remove button.
- For `grafana-alert` with field `labels`, the values helper text says `key=value, one per line` (`key=regex` with match regex); for match `regex` the helper says the backend uses RE2 (no lookaround or backreferences).
- When `type` changes, rules whose field is not in the new `fields` are dropped and `onChange` reports the result.
- The component never validates a regex itself; validation errors come from the backend.

#### Acceptance conditions

- AC1: adding an allow rule and a deny rule, choosing field and match and typing values reports a Filters value with one value per non-blank line [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx -t "edits allow and deny rules"]
- AC2: the field select offers exactly the given fields [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx -t "offers only the type's fields"]
- AC3: removing a rule reports the remaining rules [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx -t "removes a rule"]
- AC4: a type change drops rules whose field no longer applies [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx -t "drops rules that do not apply to the new type"]
- AC5: Grafana label rules show the key=value hint and regex rules the RE2 hint [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx -t "shows the label and regex hints"]
- AC6: the component builds no RegExp [evidence: command:! grep -n -e 'new RegExp' -e 'RegExp(' src/webhooks/FiltersEditor.tsx]
- AC7: the editor tests, type check and lint pass [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx && npx tsc -b && npm run lint]

#### Files

- `src/webhooks/FiltersEditor.tsx`
- `src/webhooks/FiltersEditor.test.tsx`

#### Interfaces

- New `src/webhooks/FiltersEditor.tsx`: `export function FiltersEditor(props: {type: string; fields: string[]; value: Filters; onChange: (next: Filters) => void}): JSX.Element` and `export const EMPTY_FILTERS: Filters` (`{allow: [], deny: []}`). Consumed by web-create-endpoint-filters and web-edit-endpoint-filters.
- Uses `Filters`, `FilterRule` from `src/webhooks/api.ts` (web-vendor-filters-api).

#### Expected outcome

A controlled MUI component that edits allow and deny rules for one endpoint type and reports a valid-shaped `Filters` value.

#### Steps

- Red: write `src/webhooks/FiltersEditor.test.tsx` with the five named tests (Testing Library + user-event, as `Endpoints.test.tsx`). Run `npx vitest run src/webhooks/FiltersEditor.test.tsx`: fails on the missing module.
- Green: write the component. Run the verify: all pass.

#### Notes

- Keep values as one string per line in local state so typing a newline does not lose the cursor; report the split list through `onChange`.
- The drop-on-type-change can be an effect keyed on `type` and `fields`, or done by the parent; the test renders the editor, rerenders with a new `type`/`fields`, and expects `onChange` with the dropped rules.
- Follow the MUI imports style of `CreateEndpointDialog.tsx` (per-component default imports).

- 2026-10-25 done

### S13: web create endpoint filters

- Status: done
- Files: `src/webhooks/CreateEndpointDialog.tsx`, `src/webhooks/samples.ts`, `src/webhooks/Endpoints.test.tsx`, `src/webhooks/WebhooksPage.test.tsx`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/webhooks/Endpoints.test.tsx src/webhooks/WebhooksPage.test.tsx && npx tsc -b && npm run lint`
- Verified head: 1ac0880

#### Requirement

Set filters when creating an endpoint and check them in the example-JSON preview (design D8). User decision, verbatim: "Configurable in the endpoints API and the agents-web Webhooks UI, including in the existing example-JSON preview flow if cheap: show whether the example passes the filters." Paths are in code/agents-web.

- `src/webhooks/CreateEndpointDialog.tsx`: embeds `FiltersEditor` below the prompt template, its `fields` from `getMeta().filter_fields[type]` (fetched once when the dialog opens); a type change passes the new type and fields (the editor drops inapplicable rules). The create body carries `filters` when any rule exists.
- Preview: the button is enabled when the template is non-empty or any rule exists; it sends `template` only when non-empty and `filters` only when a rule exists. The result shows the rendered prompt when one was returned, and for `filters` either "Passes the filters" or "Ignored: <reason>" (the backend's reason text). A 422 shows through `FormError` as today.
- `src/webhooks/samples.ts`: the PR/MR samples carry branches (GitHub `head.ref`/`base.ref`, GitLab `source_branch`/`target_branch`) and every forge sample carries one label, the Grafana sample `commonLabels` with `env` and `severity`, so the preview exercises the D3 fields.

#### Acceptance conditions

- AC1: creating with a deny rule sends filters in the POST body; creating without rules sends no filters key [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t "sends filters on create"]
- AC2: the editor offers the fields of meta.filter_fields for the chosen type [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t "offers the meta fields of the type"]
- AC3: preview with rules and no template sends filters without template and shows Ignored with the reason [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t "previews filters without a template"]
- AC4: preview of a passing example shows Passes the filters next to the rendered prompt [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t "shows passes the filters"]
- AC5: the PR/MR samples carry branches and every sample carries labels [evidence: command:grep -q 'head' src/webhooks/samples.ts && grep -q 'source_branch' src/webhooks/samples.ts && grep -q 'commonLabels' src/webhooks/samples.ts]
- AC6: the endpoints tests, type check and lint pass [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx src/webhooks/WebhooksPage.test.tsx && npx tsc -b && npm run lint]

#### Files

- `src/webhooks/CreateEndpointDialog.tsx`
- `src/webhooks/samples.ts`
- `src/webhooks/Endpoints.test.tsx`
- `src/webhooks/WebhooksPage.test.tsx`

#### Interfaces

- Uses `FiltersEditor`, `EMPTY_FILTERS` (web-filters-editor), `getMeta`, `createEndpoint`, `previewTemplate` (web-vendor-filters-api). `CreateEndpointDialogProps` unchanged.

#### Expected outcome

The New endpoint dialog sets allow and deny rules, and Preview answers whether the example JSON passes them, with or without a template.

#### Steps

- Red: add the four tests to `src/webhooks/Endpoints.test.tsx` (its fetch mock gains `GET /meta` with `filter_fields`). Run `npx vitest run src/webhooks/Endpoints.test.tsx`: they fail (no editor, preview disabled without a template).
- Green: the dialog and samples changes. Run the verify: all pass, including the existing create, error and credentials tests.

#### Notes

- Existing tests that preview a template keep passing: the request still carries `template`, and `filters` is omitted when there are no rules.
- `WebhooksPage.test.tsx` renders the dialog through the page; its fetch mock may need the `/meta` route too.

- 2026-10-25 done

### S14: web edit endpoint filters

- Status: done
- Files: `src/webhooks/FiltersDialog.tsx`, `src/webhooks/FiltersDialog.test.tsx`, `src/webhooks/EndpointsList.tsx`, `src/webhooks/Endpoints.test.tsx`, `MEMORY.md`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/webhooks/FiltersDialog.test.tsx src/webhooks/Endpoints.test.tsx && npx tsc -b && npm run lint`
- Verified head: 5f9dc1e

#### Requirement

Edit an existing endpoint's filters from the endpoints list (design D6, D8). User decision: "Configurable in the endpoints API and the agents-web Webhooks UI, including in the existing example-JSON preview flow if cheap: show whether the example passes the filters." Paths are in code/agents-web.

- `src/webhooks/EndpointsList.tsx`: each row gets a "Filters (n)" button (n = allow plus deny rules) before Rotate credentials; it opens `FiltersDialog` for that endpoint.
- New `src/webhooks/FiltersDialog.tsx`, `FiltersDialog({endpoint, fields, open, onClose, onSaved})`: `FiltersEditor` prefilled from `endpoint.filters`; an Example JSON field prefilled with `sampleFor(endpoint.type)` and a Check button that calls the preview with `type`, `example` and `filters` only and shows "Passes the filters" or "Ignored: <reason>"; Save calls `setEndpointFilters` and on success calls `onSaved` (the list refreshes) and closes; a 422 shows its message through `FormError` and keeps the dialog open; Cancel discards.
- The list gets `fields` from `getMeta().filter_fields`.
- `MEMORY.md`: a dated line: endpoint filters are edited in a dialog from the endpoints list through `PUT /endpoints/{id}/filters`; the field catalogue comes from `GET /meta` and the UI never validates RE2 patterns itself; why.

#### Acceptance conditions

- AC1: each endpoint row shows Filters with its rule count and opens the dialog prefilled with the endpoint's rules [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx -t "opens prefilled from the list"]
- AC2: Save sends PUT /endpoints/<id>/filters with the edited rules, closes and refreshes the list [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx -t "saves and refreshes"]
- AC3: a 422 answer shows its message and keeps the dialog open [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx -t "shows the backend error"]
- AC4: Check previews the example with the filters only and shows Ignored with the reason [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx -t "checks the example"]
- AC5: Cancel sends nothing [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx -t "cancel sends nothing"]
- AC6: MEMORY.md records the edit flow and why [evidence: command:grep -q 'filters' MEMORY.md && grep -q 'PUT' MEMORY.md]
- AC7: the dialog and endpoints tests, type check and lint pass [evidence: command:npx vitest run src/webhooks/FiltersDialog.test.tsx src/webhooks/Endpoints.test.tsx && npx tsc -b && npm run lint]

#### Files

- `src/webhooks/FiltersDialog.tsx`
- `src/webhooks/FiltersDialog.test.tsx`
- `src/webhooks/EndpointsList.tsx`
- `src/webhooks/Endpoints.test.tsx`
- `MEMORY.md`

#### Interfaces

- New `src/webhooks/FiltersDialog.tsx`: `export function FiltersDialog(props: {endpoint: EndpointView; fields: string[]; open: boolean; onClose: () => void; onSaved: (updated: EndpointView) => void}): JSX.Element`.
- Uses `FiltersEditor` (web-filters-editor), `setEndpointFilters`, `previewTemplate`, `getMeta` (web-vendor-filters-api), `sampleFor` (`samples.ts`), `FormError` (`src/triggers`).

#### Expected outcome

An operator changes an endpoint's allow and deny rules without recreating it (same URL and credentials) and checks an example against them before saving.

#### Steps

- Red: write `src/webhooks/FiltersDialog.test.tsx` with the five named tests, rendering `EndpointsList` with a fetch mock for `/endpoints`, `/meta`, `/templates/preview` and the PUT. Run `npx vitest run src/webhooks/FiltersDialog.test.tsx`: fails on the missing module and button.
- Green: the dialog, the list button, the MEMORY.md line. Run the verify: all pass, including the existing list, rotate and delete tests in `Endpoints.test.tsx`.

#### Notes

- Keep the dialog body mounted only while open (as `CreateEndpointDialog` does with its inner `Body`) so reopening resets local state to the endpoint's saved rules.
- The existing `Endpoints.test.tsx` list tests may need the `/meta` route in their fetch mock; do not change their assertions.

- 2026-10-25 done

### S15: deploy pin webhook filters

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-webhook/common.yaml`, `values/agents-web/common.yaml`, `tests/test_webhook_release.py`, `tests/test_web_release.py`
- Verify: `uv run pytest tests/test_webhook_release.py tests/test_web_release.py -q && uv run ruff check . && uv run ruff format --check .`
- Verified head: 5ee3612

#### Requirement

Pin agents-helmfile to the agents-webhook and agents-web builds that carry endpoint filters, and drop the retired env var (design D7, D9). Brief: "agents-helmfile deploys it. The deploy task is pin bumps plus an apply and smoke." Paths are in code/agents-helmfile.

Precondition, checked first: the agents-webhook and agents-web PRs of this epic are merged to main and chart `oci://harbor.szymonrichert.pl/charts/agents-webhook` `0.1.0-main.<webhook sha7>` with image tag `<webhook sha7>`, and chart `oci://harbor.szymonrichert.pl/charts/agents-web` `0.1.0-main.<web sha7>` with image tag `<web sha7>`, exist in Harbor. Otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-webhook and agents-web PRs of webhook-event-filters and wait for their main CI".

- `helmfile.yaml.gotmpl`: `agents-webhook` version `0.1.0-main.<webhook sha7>`, `agents-web` version `0.1.0-main.<web sha7>`.
- `values/agents-webhook/common.yaml`: `image.tag <webhook sha7>`; the `WEBHOOK_ALLOWED_AUTHORS` env entry removed and the comment above `env` updated (author allowlists are per-endpoint filters now); `WEBHOOK_BOT_LOGINS` stays.
- `values/agents-web/common.yaml`: `image.tag <web sha7>`.
- `tests/test_webhook_release.py`: `SHA` is the new webhook sha7; a new test asserts the values set no `WEBHOOK_ALLOWED_AUTHORS`. `tests/test_web_release.py::test_web_pin_matches_image`: the expected tag is the new web sha7 (the old pin is no longer accurate).

#### Acceptance conditions

- AC1: the agents-webhook chart version and image tag agree on the new webhook sha [evidence: test:tests/test_webhook_release.py::test_webhook_pin_and_needs]
- AC2: the agents-web chart version and image tag agree on the new web sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: the agents-webhook values no longer set WEBHOOK_ALLOWED_AUTHORS and still set WEBHOOK_BOT_LOGINS [evidence: test:tests/test_webhook_release.py::test_allowed_authors_not_set]
- AC4: the pinned charts and images exist in Harbor [evidence: judgement:the task notes quote helm show chart or docker manifest inspect output for both pinned shas]
- AC5: the release tests and lint pass [evidence: command:uv run pytest tests/test_webhook_release.py tests/test_web_release.py -q && uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-webhook/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_webhook_release.py`
- `tests/test_web_release.py`

#### Interfaces

- Consumes contracts `agents-webhook-chart`, `agents-webhook-image` (agents-webhook main CI) and the agents-web chart and image; `webhook-settings-env` without `WEBHOOK_ALLOWED_AUTHORS` (retire-allowed-authors).

#### Expected outcome

`mise run diff` would show only the two version bumps, the two image tags and the removed env entry.

#### Steps

- Precondition: `git -C ../agents-webhook log origin/main -1` and `git -C ../agents-web log origin/main -1` contain this epic's merges; `helm show chart oci://harbor.szymonrichert.pl/charts/agents-webhook --version 0.1.0-main.<sha7>` and the same for agents-web succeed; quote them in the notes.
- Red: set the new shas in the two tests and add `test_allowed_authors_not_set`. Run `uv run pytest tests/test_webhook_release.py tests/test_web_release.py -q`: the pin tests and the new test fail.
- Green: the helmfile versions and the values. Run the verify: all pass, lint clean.

#### Notes

- Take the latest agents-webhook and agents-web main merges that contain this epic (another epic may have merged after).
- The migration 0004 runs in the migrate initContainer on apply (additive column, approved at the gate).
- Never run `mise run apply`; apply-smoke-webhook-filters and the orchestrator do.

- 2026-10-25 done

### S16: apply smoke webhook filters

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run diff && mise run smoke`
- Verified head: a8686f7

#### Requirement

Apply to the live `agents` namespace and prove it (design D9; brief: "The orchestrator (main session) runs `mise run apply`; never put apply in AC evidence."). Paths are in code/agents-helmfile.

- Implementer, before the apply: `mise run diff`; keep its output in the task notes. Expected: agents-webhook chart version and image tag, the removed `WEBHOOK_ALLOWED_AUTHORS` env entry, agents-web chart version and image tag. Anything else stops the task `blocked` with the diff, whoCanClear "user". Then end the implementer round with "ready for apply".
- Orchestrator (main session, never a subagent): `mise run apply` in code/agents-helmfile; a failing apply is not retried blindly: read the helm error and report it with its tail.
- After the apply, implementer: `mise run diff` again (no drift) and `mise run smoke` (exit 0, including the filter checks); `MEMORY.md`: a dated line: applied agents-webhook `0.1.0-main.<sha7>` (endpoint filters, migration 0004) and agents-web `0.1.0-main.<sha7>` (filters UI); `WEBHOOK_ALLOWED_AUTHORS` removed; smoke green (quote its last log line).
- No other file changes.

#### Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC2: the smoke passes, including the webhook filter checks [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied versions and the smoke result [evidence: command:grep -q 'filters' MEMORY.md && grep -q 'smoke' MEMORY.md]
- AC4: the pre-apply diff showed only the expected changes [evidence: judgement:the diff output quoted in the task notes]

#### Files

- `MEMORY.md`

#### Interfaces

- Consumes every release of this epic; writes only MEMORY.md.

#### Expected outcome

The live namespace runs the filter-capable agents-webhook and agents-web, the endpoints table has the `filters` column, and the smoke is green.

#### Steps

- `mise run diff`: only the expected changes; quote it in the notes; end the round with "ready for apply".
- The orchestrator runs `mise run apply` in the main session.
- `mise run diff`: no drift; `mise run smoke`: exit 0; add the MEMORY.md line.

#### Notes

- No TDD cycle applies: this task runs deploy checks and writes one MEMORY.md line (doc edit exception).
- The migration 0004 (additive column) runs on apply in the migrate initContainer; it was listed at the gate as the epic's irreversible operation.
- `mise run apply` never appears in AC evidence.

- 2026-10-25 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
