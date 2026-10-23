---
title: scaffold repo
status: done
repo: agents-helmfile
value: "A tested, secret-safe repo skeleton with lint, test and the helmfile repo's mise tooling, so every later task has tooling and the guarantee that nothing sensitive is committed."
files: [pyproject.toml, uv.lock, mise.toml, .gitignore, .sops.yaml, .gitleaks.toml, .pre-commit-config.yaml, tests/test_repo_hygiene.py]
verify: "uv run pytest tests/test_repo_hygiene.py -q && mise run lint"
depends_on: []
owns: []
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agents-helmfile-scaffold-repo/agents-helmfile
branch: agents-helmfile-scaffold-repo
verified_head: 4f155da761f11325817e9d628bce76eb0d80a1cb
run: agents-helmfile
provides: []
acs_for_audit: []
process_gaps: ["No red run was recorded. The implementer says tests were written together with the config, and the verifier asked for a revert-to-merge-base red/green proof in tests.red and verification.evidence.", The independent verify-task.py call was blocked by the guard-bash hook because the requirement text mentions sops. It needs a re-run or a hand verification.]
fork_point: 3224685
---

# scaffold repo

## Requirement

Create the repo skeleton of code/agents-helmfile (public GitHub origin szymonrychu/agents-helmfile; the orchestrator creates the empty repo, its origin and the superrepo submodule pointer before the run). Mirror ~/Documents/infrastructure/code/helmfile but only what one namespace needs.

- `pyproject.toml` (uv project `agents-helmfile`, Python 3.12, no package; dev group pytest, pyyaml, ruff) and `uv.lock`; pytest config `testpaths = ["tests"]`, `addopts = "-q"`; ruff line length 100.
- `mise.toml`: tools helm 4.3.1, helmfile 1.8.2, sops 3.13.3, kubectl 1.33.13, shellcheck 0.11.0, gitleaks, pre-commit 4.7.0, python 3.12, uv, jq; `[env]` optionally loads a local `.env` if present (`_.file = { path = ".env", redact = true }` or equivalent that tolerates absence); the helm plugin postinstall hooks copied from the infrastructure helmfile `.mise.toml` (helm-secrets v4.7.4 incl. secrets-getter and post-renderer, helm-diff); tasks `lint` (`uv run ruff check . && uv run ruff format --check .`, shellcheck `--severity=error` over tracked `*.sh` and `.hook.sh`, then `gitleaks detect --no-git --source . --redact`) and `test` (`uv run pytest`).
- `.sops.yaml` copied from the infrastructure helmfile (PGP D39E46932A270AA3BA490B9DB9FE928D3E8BCED8; rules for `default.secrets.yaml`, `.*.secret.*.yaml`, plus one for `.*\.secrets\.yaml`).
- `.gitignore`: `.env`, `.venv`, `__pycache__`, `.pytest_cache`, `.ruff_cache`.
- `.gitleaks.toml` (default ruleset extended; allowlist only paths of SOPS-encrypted files) and `.pre-commit-config.yaml` (trailing-whitespace, end-of-file-fixer, check-yaml with multiple documents, gitleaks, conventional-pre-commit) copied and trimmed from the infrastructure helmfile.
- `.envrc` (`use mise`) mirrored from the infrastructure helmfile repo; no `.env` file is created. User decision (2026-10-23): ~/Documents/infrastructure/code/helmfile has no .env (its .envrc is `use mise`); do not copy any .env. Mirror that repo's `.envrc` (`use mise`) and `.mise.toml` instead: its tools (helm 4.3.1, helmfile 1.8.2, sops 3.13.3, kubectl 1.33.13, kubectx, stern, shellcheck, pre-commit) and its postinstall hooks (helm-secrets 4.7.4 plugins, helm-diff, pre-commit install), plus python/uv/gitleaks for tests. Keep `.env` in .gitignore for local overrides, but create none.
- `tests/test_repo_hygiene.py`: (1) `.env` is git-ignored (`git check-ignore .env`) and no `.env` is tracked; (2) every tracked file whose name matches `*.secrets.yaml` or `*.secret.*.yaml` has a top-level `sops` key with a `pgp` entry and its scalar leaves start with `ENC[`; (3) no tracked file contains a plaintext secret pattern (`sk-ant-`, `-----BEGIN .*PRIVATE KEY-----`, a `CLAUDE_CODE_OAUTH_TOKEN:` value that is not `ENC[`); (4) `gitleaks detect --no-git --source . --redact` exits 0.

## Acceptance conditions

- AC1: .env is git-ignored and never tracked [evidence: command:uv run pytest tests/test_repo_hygiene.py -q -k env_ignored_and_untracked]
- AC2: every tracked secrets file is encrypted [evidence: command:uv run pytest tests/test_repo_hygiene.py -q -k secrets_files_are_encrypted]
- AC3: no tracked file holds a plaintext secret pattern [evidence: command:uv run pytest tests/test_repo_hygiene.py -q -k no_plaintext_secrets]
- AC4: gitleaks finds nothing in the tree [evidence: command:uv run pytest tests/test_repo_hygiene.py -q -k gitleaks_clean]
- AC5: mise defines the lint and test tasks and loads .env [evidence: command:mise tasks ls | grep -q '^lint' && mise tasks ls | grep -q '^test' && grep -q '\.env' mise.toml]
- AC6: .env exists locally with mode 600 and is untracked [evidence: command:test -f .env && test "$(stat -f %Lp .env 2>/dev/null || stat -c %a .env)" = 600 && ! git ls-files --error-unmatch .env 2>/dev/null]
- AC7: lint passes [evidence: command:mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `mise.toml`
- `.gitignore`
- `.sops.yaml`
- `.gitleaks.toml`
- `.pre-commit-config.yaml`
- `tests/test_repo_hygiene.py`

## Interfaces

none (no shared parts owned).

## Expected outcome

The repo has working lint and test tasks, a local mode-600 untracked `.env`, and hygiene tests that guard every later commit.

## Steps

- Write tests/test_repo_hygiene.py; run `uv run pytest tests/test_repo_hygiene.py -q`; expect failures (no .gitignore yet, gitleaks missing).
- Write pyproject.toml, mise.toml, .gitignore, .sops.yaml, .gitleaks.toml, .pre-commit-config.yaml; `uv lock`; `cp` the .env and chmod 600 (never print it).
- Rerun the tests and `mise run lint`; expect `passed` and a clean lint.

## Notes

Copy from ~/Documents/infrastructure/code/helmfile (`.mise.toml`, `.sops.yaml`, `.gitleaks.toml`, `.pre-commit-config.yaml`). Reading `.env` is forbidden: copy only. The tests assert on `git ls-files`, never the filesystem, for tracked-ness.
