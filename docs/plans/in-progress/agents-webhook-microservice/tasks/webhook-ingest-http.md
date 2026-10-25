---
title: webhook ingest http
status: in-progress
repo: agents-webhook
value: "GitHub, GitLab and Grafana can deliver events to a public endpoint that only accepts signed requests"
files: [src/agents_webhook/ingest/__init__.py, src/agents_webhook/ingest/app.py, src/agents_webhook/ingest/verify.py, tests/test_ingest_http.py]
verify: "uv run pytest tests/test_ingest_http.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-event-store]
model: ""
review: full
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook ingest http

## Requirement

The public ingest app (design D3, D4, D12). Paths are in code/agents-webhook.

- `ingest/verify.py`: `verify_github(secret, raw, header)` (HMAC-SHA256 hex of the raw body vs `X-Hub-Signature-256` after `sha256=`), `verify_gitlab(token, header)` (`X-Gitlab-Token`), `verify_grafana(token, header)` (`Authorization: Bearer`); all `hmac.compare_digest`; an empty secret never verifies.
- `ingest/app.py`: `create_ingest_app(settings, pool)` with routes `POST /webhooks/github`, `POST /webhooks/gitlab`, `POST /webhooks/grafana`, `GET /healthz`, `GET /readyz` (DB reachable), nothing else (404). Per request, in this order:
  1. Source not configured (secret empty) -> 404 `not_found`.
  2. Read the raw body in chunks and stop at `max_body_bytes`: 413 `payload_too_large` before any parse.
  3. Signature or token mismatch -> 401 `unauthorized`.
  4. GitHub `X-GitHub-Event` / GitLab `X-Gitlab-Event` missing -> 400 `bad_request`; GitHub `ping` -> 202 `{status: "pong"}` (not stored).
  5. Parse JSON (400 on invalid), normalise; `Unsupported` -> store `ignored`, `unsupported_event`.
  6. `classify`, `mappings.match`, `events.record`; NOTIFY `webhook_events`; 202 `{id, status, reason}`.
  7. A DB error -> 503 `unavailable` (the forge retries). Accepted and ignored are both 202.
- Logs carry source, event id, status, reason; never the body, a signature or a secret.
- `tests/test_ingest_http.py` (DB fixture, signed requests built in the test): every status code path above for each source; 413 is returned without the body being parsed (a 6 MiB non-JSON body gets 413, not 400); a valid GitHub PR event with a mapping is stored `new`; an unmapped one `ignored`/`no_mapping`; a bad signature stores nothing; an unknown path 404; a DB failure 503.

## Acceptance conditions

- AC1: signatures and tokens are checked in constant time and an unconfigured source answers 404 [evidence: command:uv run pytest tests/test_ingest_http.py -q -k signature]
- AC2: bodies over 5 MiB get 413 before parsing [evidence: command:uv run pytest tests/test_ingest_http.py -q -k too_large]
- AC3: accepted and ignored events both answer 202 and are stored with status and reason [evidence: command:uv run pytest tests/test_ingest_http.py -q -k accepted]
- AC4: only a DB failure answers 5xx [evidence: command:uv run pytest tests/test_ingest_http.py -q -k unavailable]
- AC5: the ingest app serves only the three webhook paths and health [evidence: command:uv run pytest tests/test_ingest_http.py -q -k routes]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_webhook/ingest/__init__.py`
- `src/agents_webhook/ingest/app.py`
- `src/agents_webhook/ingest/verify.py`
- `tests/test_ingest_http.py`

## Interfaces

- Owns `webhook-ingest-api`: `POST /webhooks/{github,gitlab,grafana}` -> 202 `{id, status, reason}` | 400 | 401 | 404 | 413 | 503; documented in README by webhook-docs-memory.

## Expected outcome

Forges and Grafana can be pointed at `https://lab.szymonrichert.pl/webhooks/<source>` with their secret.

## Steps

- Red: tests; run: fail. Green: verify, then app; run the verify command.

## Notes

- Parity: `TN/internal/webhook/server.go:handle` L138-207, `readBody` L1640-1658, `github.go:verifyGitHubSig` L281-299, `gitlab.go:DetectAndVerify` L101-111, `server.go:handleGrafanaAlert` L1233-1246.
