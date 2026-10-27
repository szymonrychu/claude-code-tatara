---
title: fake wrapper file write
status: todo
repo: agents-orchestrator
value: orchestrator tests exercise a fake wrapper held to the real write contract
files: [tests/fakes/fake_wrapper.py, tests/test_fake_wrapper_contract.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest tests/test_fake_wrapper_contract.py && mise run lint"
depends_on: [wrapper-file-write-route]
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

# fake wrapper file write

## Requirement

Design D6, verbatim: "`tests/fakes/fake_wrapper.py` gets the PUT route with the wrapper's contract (body validation, cap from its `file_preview_max_bytes` control, existing regular files only, `file_changed`, response keys), and `tests/test_fake_wrapper_contract.py` gets cases on both legs (fake locally, real image in CI) plus fake-only cases for what the real image cannot set up (a lowered cap, symlinks). Why: the orchestrator route tests run against the fake (recurring retro finding: fakes encoded a wrong assumption)."

Design D4, verbatim (the contract part): "the editor sends back the `mtime` and `size` of the `files/content` answer it loaded (or of its last save answer); the wrapper refuses with 409 `file_changed` when the file on disk differs. `expected: null` is an explicit unconditional overwrite, sent only after the user chose Overwrite on a conflict."

The contract the fake mirrors is the claude-code-wrapper one built by task wrapper-file-write-route (design D3): `PUT /v1/sessions/{id}/files/content?path=` with body `{"content": str, "expected": {"mtime": str, "size": int >= 0} | null}` (both keys required, no other key, else 422 `invalid_request`); 413 `too_large` over `file_preview_max_bytes` (UTF-8 bytes); only an existing regular file inside the workdir (missing 404 `not_found`, nothing created; directory or workdir root 400 `not_a_file`; escapes 400 `invalid_path`); 409 `file_changed` when `expected` differs from the file's `mtime` (the listing's ISO milliseconds) or `size`; 200 `{session_id, path, size, mtime}`. Read the wrapper's README section and `src/claude_code_wrapper/api/files.py` on its epic branch before writing the fake.

Scope (agents-orchestrator):
- `tests/fakes/fake_wrapper.py`: the PUT route (honours `_auth`, `_get`, `_locate`, the `file_preview_max_bytes` control), writing through a temporary file and `os.replace` as the wrapper does, and keeping the permission bits.
- `tests/test_fake_wrapper_contract.py`: new both-leg cases `test_files_write`, `test_files_write_conflict`, `test_files_write_errors`; new fake-only cases `test_fake_files_write_cap` and `test_fake_files_write_through_symlink`.

## Acceptance conditions

- ac1: on both legs, a PUT of new UTF-8 text (non-ASCII letters, CRLF) to `src/main.py` of `_tree` answers 200 with exactly the keys `session_id`, `path`, `size`, `mtime`, and a following `files/content` returns the new content with that `size` and `mtime` (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_files_write]
- ac2: on both legs, `expected` equal to the loaded `mtime` and `size` writes; a stale `mtime` or `size` answers 409 `file_changed` and the content is unchanged; `expected: null` overwrites (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_files_write_conflict]
- ac3: on both legs, `../outside`, `/etc/passwd`, a NUL path and `src/../../x` answer 400 `invalid_path`; `src` and the empty path 400 `not_a_file`; `missing` 404 `not_found` and a following listing does not show it; an unknown session 404 `not_found`; no bearer 401; a body without `expected`, with an extra key or with a non-string `content` 422 `invalid_request` (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_files_write_errors]
- ac4: on the fake, with `file_preview_max_bytes` lowered, content over the cap answers 413 `too_large` and the file is unchanged, content at the cap is written (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_files_write_cap]
- ac5: on the fake, a symlink inside the workdir to a file writes the target and stays a link; a symlink escaping the workdir answers 400 `invalid_path` and the outside file is unchanged (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_files_write_through_symlink]
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
