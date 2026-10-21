---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
---

# Python

Verify before claiming done: use the repo's own wrapper first
(`mise run fmt && mise run lint && mise run test`).

- Inside a uv-managed component (a `pyproject.toml` with `uv.lock`), run
  `uv run ruff format . && uv run ruff check --fix . && uv run mypy . && uv run pytest`
  and invoke Python through `uv run`, not bare `python`. Never
  `pip install` - it breaks lockfile reproducibility. Add deps with `uv add`.
- Template tooling under `plugins/` and `scripts/` runs with `python3` by
  design (stdlib only, no uv); verify it with the mise tasks.
- Type hints on public functions (new or changed code only). Do not silence a
  checker with `# type: ignore`; fix the type.
- No mutable default arguments.
- Config lives in `pyproject.toml`.
