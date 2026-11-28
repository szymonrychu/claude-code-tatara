---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
---

# Python

Verify before claiming done: use the repo's own wrapper first
(`mise run fmt && mise run lint && mise run test`).

- Inside a uv-managed component (a `pyproject.toml` with `uv.lock`), run
  `uv run ruff format . && uv run ruff check --fix . && uv run pytest`
  and invoke Python through `uv run`, not bare `python`. Never
  `pip install` - it breaks lockfile reproducibility. Add deps with `uv add`.
- Template tooling under `plugins/` and `scripts/` runs with `python3` by
  design (stdlib only, no uv); verify it with the mise tasks.
- Type hints on public functions (new or changed code only). Do not silence a
  checker with `# type: ignore`; fix the type.
- No mutable default arguments.
- Config lives in `pyproject.toml`. Every component carries this ruff block:

  ```toml
  [tool.ruff.lint]
  extend-select = ["C90", "PLR0911", "PLR0912", "PLR0915", "RET", "ERA"]

  [tool.ruff.lint.mccabe]
  max-complexity = 10
  ```

  Complexity noqa only as the S-99 baseline; remove it when the function is touched.
- pytest markers: unit, integration, e2e, live, critical, with `--strict-markers`.
