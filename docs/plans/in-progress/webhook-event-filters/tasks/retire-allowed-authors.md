---
title: retire allowed authors
status: in-progress
repo: agents-webhook
value: "one way to allowlist authors: per-endpoint rules, with the global env var gone"
files: [src/agents_webhook/settings.py, src/agents_webhook/normalize.py, src/agents_webhook/ingest/app.py, README.md, tests/test_normalize.py, tests/test_schema_settings.py, tests/test_readme_config.py, MEMORY.md]
verify: "uv run pytest tests/test_normalize.py tests/test_schema_settings.py tests/test_readme_config.py tests/test_ingest_http.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [e2e-endpoint-filters]
model: opus
review: ""
verified_head: ""
points: 2
expected_minutes: 9
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# retire allowed authors

## Requirement

Retire the global `WEBHOOK_ALLOWED_AUTHORS` setting and its reason `author_not_allowed`; per-endpoint `allow` rules on `author` replace them (design D7, gate Q1 working answer; brief: "Global env lists WEBHOOK_BOT_LOGINS and WEBHOOK_ALLOWED_AUTHORS already exist. Decide whether per-endpoint filters replace them. The house rule is no backward compatibility"). `WEBHOOK_BOT_LOGINS` and `self_event` stay. Paths are in code/agents-webhook.

- `settings.py`: `allowed_authors` removed from `WebhookSettings`; no alias, no deprecation path.
- `normalize.py:classify(event, *, bot_logins)`: the `allowed_authors` parameter and the `author_not_allowed` branch removed; the module docstring updated.
- `ingest/app.py`: the call no longer passes `allowed_authors`.
- README: the `WEBHOOK_ALLOWED_AUTHORS` row leaves `## Configuration`, `author_not_allowed` leaves `## Statuses and reasons`, and `## Filters` says that an author allowlist is an endpoint `allow` rule on `author`.
- Tests no longer accurate after the retirement, changed and named: `tests/test_normalize.py::test_classify_author_not_allowed` (removed: it tests the retired branch; `_classify` drops its `allowed` argument), `tests/test_schema_settings.py` default-values test (drops the `allowed_authors == []` clause), `tests/test_readme_config.py` (`REASONS` drops `author_not_allowed`).
- New retirement tests: `WebhookSettings` has no `allowed_authors` field and `WEBHOOK_ALLOWED_AUTHORS` set in the environment changes nothing (extra env is ignored); README mentions neither `WEBHOOK_ALLOWED_AUTHORS` nor `author_not_allowed`; `classify` has no `allowed_authors` parameter.
- MEMORY.md: a dated line: per-endpoint filters (allow and deny rules, RE2 regex, filtered deliveries stored ignored `filter_denied`/`filter_not_allowed`) replace `WEBHOOK_ALLOWED_AUTHORS`; `WEBHOOK_BOT_LOGINS` stays global as the self-loop guard; why.

## Acceptance conditions

- AC1: WebhookSettings has no allowed_authors field [evidence: test:tests/test_schema_settings.py::test_allowed_authors_retired]
- AC2: classify takes no allowed_authors parameter and never returns author_not_allowed [evidence: test:tests/test_normalize.py::test_classify_has_no_author_allowlist]
- AC3: README no longer mentions WEBHOOK_ALLOWED_AUTHORS or author_not_allowed [evidence: test:tests/test_readme_config.py::test_retired_author_allowlist_not_documented]
- AC4: no source or chart file and no README line references allowed_authors or author_not_allowed [evidence: command:! git grep -n -e allowed_authors -e ALLOWED_AUTHORS -e author_not_allowed -- src chart README.md]
- AC5: self_event and WEBHOOK_BOT_LOGINS keep working [evidence: test:tests/test_normalize.py::test_classify_self_event]
- AC6: MEMORY.md records the replacement and why [evidence: command:grep -q 'WEBHOOK_ALLOWED_AUTHORS' MEMORY.md && grep -q 'filter' MEMORY.md]
- AC7: the touched suites and lint pass [evidence: command:uv run pytest tests/test_normalize.py tests/test_schema_settings.py tests/test_readme_config.py tests/test_ingest_http.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/settings.py`
- `src/agents_webhook/normalize.py`
- `src/agents_webhook/ingest/app.py`
- `README.md`
- `tests/test_normalize.py`
- `tests/test_schema_settings.py`
- `tests/test_readme_config.py`
- `MEMORY.md`

## Interfaces

- Contract `webhook-settings-env` loses `WEBHOOK_ALLOWED_AUTHORS` (consumer deploy-pin-webhook-filters drops it from the helmfile values).
- `normalize.classify(event, *, bot_logins: Collection[str]) -> str | None`.

## Expected outcome

The only author allowlist is a per-endpoint filter rule; the service no longer reads `WEBHOOK_ALLOWED_AUTHORS`.

## Steps

- Red: add the three retirement tests and apply the named test changes. Run `uv run pytest tests/test_normalize.py tests/test_schema_settings.py tests/test_readme_config.py -q`: the retirement tests fail (field, parameter and README rows still present).
- Green: remove the setting, the parameter and branch, the ingest kwarg and the README rows; add the MEMORY.md line. Run the verify: all pass, lint clean.

## Notes

- Removal with a pinning test, not a file deletion, so the TDD cycle applies normally.
- e2e-endpoint-filters already moved the e2e stack and its reasons test off the setting; `tests/test_event_store.py` was moved by ingest-applies-filters.
- Ask of every removed line (retro proposal): what reads this value if it is still set in a live environment? `extra="ignore"` in `WebhookSettings.model_config` makes a leftover env var inert; the helmfile values drop it in deploy-pin-webhook-filters.
