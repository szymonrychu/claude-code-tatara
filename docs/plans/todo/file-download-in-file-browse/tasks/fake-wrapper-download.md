---
title: fake wrapper download
status: todo
repo: agents-orchestrator
value: orchestrator tests exercise a fake wrapper held to the real download and listing contract
files: [tests/fakes/fake_wrapper.py, tests/test_fake_wrapper_contract.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest tests/test_fake_wrapper_contract.py && mise run lint"
depends_on: [wrapper-file-download-route]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# fake wrapper download

## Requirement

Design D6, verbatim: "`tests/fakes/fake_wrapper.py` gets the download route and `target_type`, and `tests/test_fake_wrapper_contract.py` gets cases that run on both legs (fake locally, real image in CI), plus fake-only cases for what the real image cannot set up (symlinks, a file over the preview cap). Why: orchestrator route tests run against the fake, so the fake must be held to the real wrapper's contract (retro of generic-any-mcp-with-git-and: fakes encoded a wrong assumption)."

The contract the fake mirrors is the claude-code-wrapper one built by task wrapper-file-download-route (design D1, D2, D3): `GET /v1/sessions/{id}/files/download?path=` streams the raw bytes with `Content-Type` (guessed mime, else `application/octet-stream`), `Content-Length`, `Content-Disposition: attachment; filename="<fallback>"; filename*=UTF-8''<encoded>` (name = last segment of the normalised requested path), `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`; it refuses with the same codes as `files/content`; every listing entry carries `target_type` (`dir`, `file`, `other` for a symlink resolving inside the workdir, else null; null for non-symlinks). Read the wrapper's README section and `src/claude_code_wrapper/api/files.py` on its epic branch before writing the fake, and copy the header construction semantics exactly.

Scope (agents-orchestrator):
- `tests/fakes/fake_wrapper.py`: the download route (streamed, honours `_auth`, `_get`, `_locate`, no `file_preview_max_bytes` cap) and `target_type` in `list_files`.
- `tests/test_fake_wrapper_contract.py`: new both-leg cases `test_files_download` and `test_files_download_errors`; new fake-only cases `test_fake_files_download_ignores_preview_cap` and `test_fake_files_symlink_target_type`. `test_files_list` asserts the entry key set `{"name", "type", "size", "mtime"}`, which is no longer accurate because the listing contract gains `target_type` (D3): it asserts the five keys and `target_type` null for the file and directory entries.

Notes: the real leg (`-m integration`, real wrapper image) runs only in CI and only passes once orch-wrapper-pin-download pins the wrapper commit carrying the route; locally the verify runs the fake leg. `_tree` writes files through the turn `files` field (text only) on both legs; symlinks and the over-cap file are written straight into `fake.workdir(sid)` in the fake-only cases.

## Acceptance conditions

- ac1: on both legs, `files/download` returns the exact bytes of a text file and of the `blob.bin` file of `_tree`, with Content-Length, Content-Type (`text/x-python` for `src/main.py`), Content-Disposition `attachment; filename="main.py"; filename*=UTF-8''main.py`, nosniff and no-store (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_files_download]
- ac2: on both legs, the download refuses `../outside`, `/etc/passwd`, a NUL path and `src/../../x` with 400 invalid_path, `src` and the empty path with 400 not_a_file, `missing` and an unknown session with 404 not_found, and no bearer with 401 (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_files_download_errors]
- ac3: on the fake, a file larger than `file_preview_max_bytes` downloads fully and byte-exact (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_files_download_ignores_preview_cap]
- ac4: on the fake, listing `target_type` is `file`, `dir`, `other` for links to a file, a directory, a FIFO inside the workdir, null for a dangling link and a link escaping the workdir, null for non-symlinks (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_files_symlink_target_type]
- ac5: the listing contract case asserts the five entry keys including `target_type` [evidence: test:tests/test_fake_wrapper_contract.py::test_files_list]
- ac6: the contract suite (fake leg) and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_fake_wrapper_contract.py && mise run lint]

## Files

- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
