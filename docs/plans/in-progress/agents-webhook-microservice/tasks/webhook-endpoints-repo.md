---
title: webhook endpoints repo
status: in-progress
repo: agents-webhook
value: "each webhook gets its own URL, type, preset and basic-auth credentials stored as hashes"
files: [src/agents_webhook/credentials.py, src/agents_webhook/db/__init__.py, src/agents_webhook/db/endpoints.py, tests/test_endpoints_repo.py]
verify: "uv run pytest tests/test_endpoints_repo.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-schema-settings]
model: opus
review: full
verified_head: ""
points: 3
expected_minutes: 16
expected_tokens: 723362
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook endpoints repo

## Requirement

Per-webhook endpoints and their credentials (design D3, D7, D18; user request 2026-10-25: "Add an ability to create webhook url in form of https://<base>/webhook/<random string>. Such webhook will be defined as one of the supported types on creation. When creating such webhook url user can provide: <random string> url suffix (by default it's random, user can supply any unique string); basic-auth credentials (by default random u/p are provided, user can override both). User is required to provide a preset that will be used to run the webhook along with a type of the webhook (grafana alert/gitlab-issue/gitlab-mr/github-issue/github-pr). only these sink endpoints will be used onwards for any webhooks and such url will be unique for each assignment."). Paths are in code/agents-webhook.

- `credentials.py` (no I/O): `generate_suffix()` (`secrets.token_urlsafe(24)`, 32 chars), `generate_username()` (`wh-` + `secrets.token_hex(4)`), `generate_password()` (`secrets.token_urlsafe(32)`); `hash_password(pw) -> str` with `hashlib.scrypt` (n=2**14, r=8, p=1, 16-byte random salt), stored as `scrypt$16384$8$1$<salt b64>$<hash b64>`; `verify_password(pw, stored) -> bool` with `hmac.compare_digest`; `DUMMY_HASH` (computed once) so an unknown suffix costs the same scrypt work; `parse_basic(header) -> (username, password) | None` (malformed or non-Basic -> None).
- `db/endpoints.py`: `Endpoint{id, suffix, type, preset_id, prompt_template, username, created_at, credentials_rotated_at}` (never the hash), `EndpointIn{type, preset_id, suffix?, username?, password?, prompt_template?}`, `Credentials{username, password}`:
  - `create(conn, data, *, min_password_length) -> (Endpoint, Credentials)`: missing suffix, username or password generated; a user suffix must match `^[A-Za-z0-9._~-]{1,128}$` (`ValueError` naming `suffix`), a user password must be at least `min_password_length` (`ValueError` naming `password`), a username 1-64 printable chars without `:`; a taken suffix raises `SuffixTaken`; only the hash is stored.
  - `rotate(conn, id, *, username=None, password=None, min_password_length) -> Credentials | None`: same rules, sets `credentials_rotated_at`.
  - `authenticate(conn, suffix, authorization) -> Endpoint | None`: constant-time username compare and scrypt verify; an unknown suffix or malformed header still verifies against `DUMMY_HASH`; one code path returns None for every failure.
  - `get`, `get_by_suffix`, `list_all`, `delete(conn, id) -> bool` (events keep `endpoint_suffix`; `endpoint_id` goes null by FK).
- `tests/test_endpoints_repo.py`: defaults generated with the documented lengths and charset; user suffix and credentials stored; a taken suffix; bad suffix, short password and bad username named; the stored hash is scrypt with a per-endpoint salt and never the password; authenticate succeeds only with the right suffix, username and password; unknown suffix, wrong username, wrong password and malformed header all return None through the dummy-hash path (the verify function is called once in each case); rotate invalidates the old password; delete keeps events with their suffix.

## Acceptance conditions

- AC1: an endpoint is created with a random or user-supplied unique suffix, one of the five types, a preset and random or user-supplied credentials [evidence: command:uv run pytest tests/test_endpoints_repo.py -q -k create]
- AC2: passwords are stored only as salted scrypt hashes and checked in constant time [evidence: command:uv run pytest tests/test_endpoints_repo.py -q -k hash]
- AC3: unknown suffixes, wrong credentials and malformed headers fail through the same path with the same hash work [evidence: command:uv run pytest tests/test_endpoints_repo.py -q -k authenticate]
- AC4: rotate replaces the credentials and invalidates the old password [evidence: command:uv run pytest tests/test_endpoints_repo.py -q -k rotate]
- AC5: invalid suffixes, short passwords and bad usernames are rejected naming the field [evidence: command:uv run pytest tests/test_endpoints_repo.py -q -k invalid]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/credentials.py`
- `src/agents_webhook/db/__init__.py`
- `src/agents_webhook/db/endpoints.py`
- `tests/test_endpoints_repo.py`

## Interfaces

- Owns `webhook-endpoints` (internal): `agents_webhook.credentials.{generate_suffix, generate_username, generate_password, hash_password, verify_password, parse_basic, DUMMY_HASH}`, `agents_webhook.db.endpoints.{Endpoint, EndpointIn, Credentials, SuffixTaken, create, rotate, authenticate, get, get_by_suffix, list_all, delete}`.

## Expected outcome

Endpoints exist in the database with a unique suffix, a type, a preset and hashed credentials, and a request can be authenticated against them in constant time.

## Steps

- Red: `tests/test_endpoints_repo.py`; run `uv run pytest tests/test_endpoints_repo.py -q`: fail.
- Green: `credentials.py`, then `db/endpoints.py`; run the verify command.

## Notes

- The api is the only writer of `endpoints`; ingest only reads.
- scrypt from the standard library (`hashlib.scrypt`), no new dependency.

- 2026-10-25 in-progress: re-plan 2026-10-25: added; not started
