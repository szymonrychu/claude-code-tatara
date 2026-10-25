---
title: cache transfer cli
status: done
repo: agents-orchestrator
value: a Job can restore or save a workspace through one presigned URL with no credential
files: [src/agents_orchestrator/cache/transfer.py, src/agents_orchestrator/cli.py, tests/test_cache_cli.py]
verify: "uv run pytest -q tests/test_cache_cli.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [cache-archive]
model: opus
review: ""
verified_head: 53a14e9
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: 3
actual_minutes: 19
actual_tokens: 2574263
actual_roles: impl 19
actual_role_tokens: impl 2574263
---

# cache transfer cli

## Requirement

Add the Job-side transfer CLI `orch cache restore|save` (contract orch-cache-job-cli; design D1, D5, D11). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

`src/agents_orchestrator/cache/transfer.py` and `cli.py` (register `cache` with a positional `restore` or `save`). The command reads only these env variables and never constructs `Settings()` or reads `ORCH_*`: `CACHE_URL` (a presigned URL), `CACHE_DIR` (the workdir), `CACHE_MAX_BYTES`, `CACHE_EXCLUDE` (a JSON list of globs, default `[]`), `CACHE_SCRATCH` (directory for the save archive, default `/scratch`). Its last stdout line is one JSON object `{"outcome", "bytes", "reason"}`.

- `restore`: GET `CACHE_URL` streamed with httpx into `archive.unpack`. 200: `{"outcome": "restored", "bytes": <n>}`, exit 0. 404: `{"outcome": "miss", "bytes": 0}`, exit 0, the workdir untouched. An HTTP status other than 200 or 404, or a network error, before any byte was extracted: `{"outcome": "failed", "reason": "download_failed: <detail>"}`, exit 1. `ExtractError` or any failure after extraction began: `{"outcome": "failed", "reason": "extract_failed: <detail>"}`, exit 1.
- `save`: `CACHE_DIR` missing: `{"outcome": "skipped", "reason": "no_workdir"}`, exit 0, no request. Else `archive.pack` into `<CACHE_SCRATCH>/archive.tar.zst`; `TooLarge`: `{"outcome": "failed", "reason": "too_large"}`, exit 1, no request. Else one PUT of the file with `Content-Length` and `Content-Type: application/zstd`; 2xx: `{"outcome": "saved", "bytes": <n>}`, exit 0; anything else: `{"outcome": "failed", "reason": "upload_failed: <status or error>"}`, exit 1. The archive file is removed afterwards.
- No output line, reason or log contains the URL's query string (the signature).

## Acceptance conditions

- AC1: restore of a 200 body extracts into CACHE_DIR and prints restored with the byte count [evidence: test:tests/test_cache_cli.py::test_restore_restored]
- AC2: restore of a 404 prints miss, exits 0 and leaves the workdir untouched [evidence: test:tests/test_cache_cli.py::test_restore_miss]
- AC3: a 500 or a connection error before extraction prints download_failed and exits 1 [evidence: test:tests/test_cache_cli.py::test_restore_download_failed]
- AC4: a corrupt body prints extract_failed and exits 1 [evidence: test:tests/test_cache_cli.py::test_restore_extract_failed]
- AC5: save PUTs one archive with Content-Length and prints saved [evidence: test:tests/test_cache_cli.py::test_save_saved]
- AC6: save with no workdir prints skipped no_workdir and sends no request [evidence: test:tests/test_cache_cli.py::test_save_no_workdir]
- AC7: save over CACHE_MAX_BYTES prints too_large, exits 1 and sends no request [evidence: test:tests/test_cache_cli.py::test_save_too_large_no_put]
- AC8: an upload failure reason never contains the URL query string [evidence: test:tests/test_cache_cli.py::test_save_upload_failed_hides_signature]
- AC9: orch cache runs with no ORCH_* variable set [evidence: test:tests/test_cache_cli.py::test_cli_needs_no_settings]
- AC10: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/cache/transfer.py`
- `src/agents_orchestrator/cli.py`
- `tests/test_cache_cli.py`

## Interfaces

- `orch cache restore|save` env and JSON outcome line (contract `orch-cache-job-cli`); `cache/transfer.py:restore(env) -> int`, `save(env) -> int`.
- Consumes `cache/archive.py` from cache-archive.

## Expected outcome

`CACHE_URL=http://127.0.0.1:<port>/o CACHE_DIR=/tmp/w orch cache save` PUTs one zstd body and prints `{"outcome": "saved", "bytes": N, "reason": null}` last; `restore` of the same URL recreates the tree.

## Steps

- Red: write `tests/test_cache_cli.py` (the nine named tests) against a local HTTP fake (stdlib `http.server` in a thread, or `httpx.MockTransport` injected into the transfer functions); run it: fails.
- Green: write `transfer.py` and register the command in `cli.py`; run the verify command.

## Notes

- Keep the import of `transfer` lazy inside the command, like the other subcommands, so `orch --help` stays light.
- Strip the query string from any URL in errors (`httpx.URL(url).copy_with(query=None)`).
- httpx is already a dependency; no new one here.

- 2026-10-26 done
