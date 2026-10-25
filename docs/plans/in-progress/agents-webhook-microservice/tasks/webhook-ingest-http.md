---
title: webhook ingest http
status: in-progress
repo: agents-webhook
value: "GitHub, GitLab and Grafana deliver events to a per-webhook public URL that only accepts its own basic-auth credentials"
files: [src/agents_webhook/ingest/__init__.py, src/agents_webhook/ingest/app.py, src/agents_webhook/ingest/ratelimit.py, tests/test_ingest_http.py]
verify: "uv run pytest tests/test_ingest_http.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-event-store]
model: opus
review: full
verified_head: ""
points: 5
expected_minutes: 15
expected_tokens: 1836811
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook ingest http

## Requirement

The public ingest app: one URL per endpoint behind HTTP basic auth (design D3, D4, D12, D18; user request 2026-10-25: "only these sink endpoints will be used onwards for any webhooks"). Paths are in code/agents-webhook.

- `ingest/ratelimit.py`: `FailureLimiter(per_minute, max_keys=10000)`, an in-memory sliding 60 s window of failed authentications per client key (oldest keys evicted beyond `max_keys`); `blocked(key) -> float | None` (seconds until retry), `record_failure(key)`. `client_key(peer_ip, x_forwarded_for, trusted_proxies)`: the right-most `X-Forwarded-For` address not in `trusted_proxies` when the peer is in `trusted_proxies`, else the peer address.
- `ingest/app.py`: `create_ingest_app(settings, pool)` with routes `POST /webhook/{suffix}`, `GET /healthz`, `GET /readyz` (DB reachable), nothing else (404). Per request, in this order:
  1. Client key blocked by the limiter -> 429 `too_many_requests` with `Retry-After`, before any DB or hash work.
  2. `endpoints.authenticate(conn, suffix, Authorization)`; None -> record a failure, 401 `unauthorized` with `WWW-Authenticate: Basic realm="agents-webhook"`, the same body and headers for an unknown or deleted suffix, a missing or malformed header, a wrong username or a wrong password.
  3. Read the raw body in chunks and stop at `max_body_bytes`: 413 `payload_too_large` before any parse.
  4. GitHub `ping` -> 202 `{status: "pong"}` (not stored).
  5. Parse JSON (400 `bad_request` on invalid), `normalize(endpoint.type, headers, payload)`; `TypeMismatch` -> store `ignored`, `type_mismatch`; `Unsupported` -> store `ignored`, `unsupported_event`.
  6. `classify`, `events.record`; NOTIFY `webhook_events`; 202 `{id, status, reason}`.
  7. A DB error -> 503 `unavailable` (the forge retries). Accepted and ignored are both 202.
- Logs carry the endpoint id, event id, status, reason and client key; never the suffix of a failed request, the body, the Authorization header or a password.
- `tests/test_ingest_http.py` (DB fixture, endpoints created in the test): every status code path above for each of the five types; a GitHub PR event on a github-pr endpoint stored `new` with the endpoint's preset; a PR event on a github-issue endpoint `ignored`/`type_mismatch`; the identical 401 for unknown suffix and wrong credentials; 413 without the body being parsed (a 6 MiB non-JSON body gets 413, not 400); 11 failed attempts from one client in a minute -> 429 with Retry-After while another client still gets 401; `X-Forwarded-For` honoured only from a trusted proxy; an unknown path 404; a DB failure 503; the limiter unit cases.

## Acceptance conditions

- AC1: an endpoint accepts a request only with its own basic-auth credentials, and an unknown suffix gets the same 401 as wrong credentials [evidence: command:uv run pytest tests/test_ingest_http.py -q -k auth]
- AC2: repeated failed authentications from one client get 429 with Retry-After, keyed on the forwarded address only behind a trusted proxy [evidence: command:uv run pytest tests/test_ingest_http.py -q -k limit]
- AC3: bodies over 5 MiB get 413 before parsing [evidence: command:uv run pytest tests/test_ingest_http.py -q -k too_large]
- AC4: accepted, type-mismatched and ignored events answer 202 and are stored with status and reason [evidence: command:uv run pytest tests/test_ingest_http.py -q -k accepted]
- AC5: only a DB failure answers 5xx and the app serves only /webhook/<suffix> and health [evidence: command:uv run pytest tests/test_ingest_http.py -q -k "unavailable or routes"]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/ingest/__init__.py`
- `src/agents_webhook/ingest/app.py`
- `src/agents_webhook/ingest/ratelimit.py`
- `tests/test_ingest_http.py`

## Interfaces

- Owns `webhook-ingest-url` (cross-epic): `POST /webhook/{suffix}` with HTTP basic auth -> 202 `{id, status, reason}` | 400 | 401 | 404 | 413 | 429 | 503; documented in README by webhook-docs-memory.
- `agents_webhook.ingest.app.create_ingest_app(settings, pool)`, `agents_webhook.ingest.ratelimit.{FailureLimiter, client_key}`.

## Expected outcome

GitHub, GitLab and Grafana can be pointed at `https://lab.szymonrichert.pl/webhook/<suffix>` with the endpoint's credentials; nothing else is accepted.

## Steps

- Red: `tests/test_ingest_http.py`; run `uv run pytest tests/test_ingest_http.py -q`: fail.
- Green: ratelimit, then the app; run the verify command.

## Notes

- Parity for body reading and event detection: `TN/internal/webhook/server.go:handle` L138-207, `readBody` L1640-1658; the per-source signature checks of tatara-new are replaced by basic auth (re-plan 2026-10-25).
- Authenticate before reading the body, so an unauthenticated caller cannot make the pod buffer 5 MiB.

- 2026-10-25 in-progress: re-plan 2026-10-25: added; not started
