---
title: cache archive
status: todo
repo: agents-orchestrator
value: "a workspace packs into a capped tar.zst and unpacks safely, never outside the workdir"
files: [src/agents_orchestrator/cache/__init__.py, src/agents_orchestrator/cache/archive.py, pyproject.toml, uv.lock, tests/test_cache_archive.py]
verify: "uv run pytest -q tests/test_cache_archive.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# cache archive

## Requirement

Add the archive layer of the workspace cache (design D5, D6). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

New package `src/agents_orchestrator/cache/`; `cache/archive.py`:
- `pack(workdir: Path, out: BinaryIO, *, exclude: list[str], max_bytes: int) -> int`: a tar stream compressed with `zstandard` written to `out`; returns the compressed bytes written. Members are paths relative to `workdir`. Symlinks are stored as symlinks and never followed; sockets, FIFOs, block and character devices are skipped. `.agent-init` (`spec.CACHE_ALWAYS_EXCLUDE`) is always excluded, plus each `exclude` glob (fnmatch on the workdir-relative POSIX path; a matching directory prunes its whole subtree). Raises `TooLarge` as soon as the compressed output passes `max_bytes`.
- `unpack(src: BinaryIO, workdir: Path) -> int`: streaming zstd decompression and `tarfile` extraction with `filter="data"` into `workdir` (created when missing); returns the number of members extracted. It never deletes or empties anything already in `workdir`. A corrupt stream or a refused member (absolute path, `..`, a link escaping `workdir`, a device node) raises `ExtractError`.
- Both refuse a `workdir` that is empty or `/` with `ValueError` before touching the filesystem (retro: a computed path that came out empty must not be written into).
- `pyproject.toml`: dependency `zstandard`; `uv.lock` refreshed with `uv lock`.

## Acceptance conditions

- AC1: pack then unpack restores files, directories, modes and symlinks [evidence: test:tests/test_cache_archive.py::test_round_trip_keeps_files_modes_symlinks]
- AC2: .agent-init and the exclude globs are left out, and an excluded directory prunes its subtree [evidence: test:tests/test_cache_archive.py::test_excludes]
- AC3: a symlink to a file outside the workdir is stored as a link, never its content, and FIFOs are skipped [evidence: test:tests/test_cache_archive.py::test_symlinks_not_followed_specials_skipped]
- AC4: pack raises TooLarge once the compressed output passes max_bytes [evidence: test:tests/test_cache_archive.py::test_too_large]
- AC5: unpack refuses absolute, dot-dot and escaping-link members with ExtractError and writes nothing outside the workdir [evidence: test:tests/test_cache_archive.py::test_unpack_refuses_unsafe_members]
- AC6: unpack keeps existing files that are not in the archive [evidence: test:tests/test_cache_archive.py::test_unpack_keeps_existing_files]
- AC7: a corrupt stream raises ExtractError [evidence: test:tests/test_cache_archive.py::test_corrupt_stream]
- AC8: an empty or root workdir is refused before any filesystem access [evidence: test:tests/test_cache_archive.py::test_refuses_empty_or_root_workdir]
- AC9: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/cache/__init__.py`
- `src/agents_orchestrator/cache/archive.py`
- `pyproject.toml`
- `uv.lock`
- `tests/test_cache_archive.py`

## Interfaces

- `cache/archive.py:pack(workdir, out, *, exclude, max_bytes) -> int`, `unpack(src, workdir) -> int`, `TooLarge`, `ExtractError`.

## Expected outcome

A workdir with files, a symlink and an excluded `node_modules/` packs to a `.tar.zst` stream and unpacks to the same tree without `node_modules/` and `.agent-init/`; a crafted archive with `../escape` raises `ExtractError` and writes nothing outside.

## Steps

- `uv add zstandard` (writes pyproject.toml and uv.lock).
- Red: write `tests/test_cache_archive.py` with the eight named tests (craft unsafe archives with `tarfile` directly); run it: fails on the missing module.
- Green: write `archive.py`; run the verify command.

## Notes

- Python 3.12: `tarfile` `filter="data"` exists; open with `tarfile.open(fileobj=..., mode="r|")` over a `zstandard.ZstdDecompressor().stream_reader(src)`; write with `mode="w|"` over `ZstdCompressor().stream_writer(counting_out)`.
- Count compressed bytes in a small writer wrapper and raise `TooLarge` there.
- Walk with `os.scandir`/`os.walk(followlinks=False)`; use `lstat` to skip sockets, FIFOs and devices.
- Never `rmtree` or clear the workdir (retro: computed-path writes).
