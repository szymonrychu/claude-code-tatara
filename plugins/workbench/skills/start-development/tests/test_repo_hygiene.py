"""Repo hygiene: ASCII-only sources, documented frontmatter keys, shell lint coverage."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GITIGNORE = Path(__file__).resolve().parents[5] / ".gitignore"  # repo root; plugin has none

# scripts/run-tests.sh greps node's own non-ASCII status glyphs, so it must contain them.
EXCLUDED = ("scripts/run-tests.sh",)

# Documented subagent frontmatter fields, transcribed from
# https://code.claude.com/docs/en/sub-agents . The page also lists mcpServers,
# omitClaudeMd, initialPrompt and experimental, which are added here beyond the
# base tuple.
AGENT_KEYS = (
    "name",
    "description",
    "tools",
    "disallowedTools",
    "model",
    "maxTurns",
    "skills",
    "hooks",
    "permissionMode",
    "effort",
    "color",
    "memory",
    "background",
    "mcpServers",
    "omitClaudeMd",
    "initialPrompt",
    "experimental",
)

# Documented skill frontmatter fields, transcribed from
# https://code.claude.com/docs/en/skills . The page also lists when_to_use, arguments,
# disallowed-tools, background, shell, metadata, license and compatibility, which are
# added here beyond the base tuple.
SKILL_KEYS = (
    "name",
    "description",
    "argument-hint",
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",
    "model",
    "effort",
    "context",
    "agent",
    "hooks",
    "paths",
    "when_to_use",
    "arguments",
    "disallowed-tools",
    "background",
    "shell",
    "metadata",
    "license",
    "compatibility",
)


def _scanned_files():
    files = []
    for d in ("agents", "skills", "rules", "commands"):
        files += sorted((ROOT / d).rglob("*.md"))
    files += sorted((ROOT / "docs" / "plans").glob("*.md"))
    files.append(ROOT / "README.md")
    files += sorted((ROOT / "workflows").glob("*.js")) + sorted((ROOT / "workflows").glob("*.mjs"))
    for d in ("hooks", "scripts"):
        for pat in ("*.py", "*.sh"):
            files += sorted((ROOT / d).glob(pat))
    return [f for f in files if f.relative_to(ROOT).as_posix() not in EXCLUDED]


def test_ascii_only():
    bad = []
    for f in _scanned_files():
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if not line.isascii():
                bad.append(f"{f.relative_to(ROOT).as_posix()}:{n}")
    assert not bad, "non-ASCII lines:\n" + "\n".join(bad)


def test_no_doubled_space_dash_from_ascii_sweep():
    # an em dash maps to " - "; keeping the spaces around it gave "word  -  word"
    bad = []
    for f in _scanned_files():
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if "  -  " in line:
                bad.append(f"{f.relative_to(ROOT).as_posix()}:{n}")
    assert not bad, "doubled spaces around a dash:\n" + "\n".join(bad)


def _frontmatter_keys(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0] == "---", f"{path}: no frontmatter"
    keys = []
    for line in lines[1:]:
        if line == "---":
            return keys
        m = re.match(r"^([A-Za-z_][\w-]*):", line)
        if m:
            keys.append(m.group(1))
    raise AssertionError(f"{path}: unterminated frontmatter")


def test_agent_frontmatter_keys():
    files = sorted((ROOT / "agents").glob("*.md"))
    assert files
    for f in files:
        extra = set(_frontmatter_keys(f)) - set(AGENT_KEYS)
        assert not extra, f"{f.name}: undocumented keys {sorted(extra)}"


def test_skill_frontmatter_keys():
    files = sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert files
    for f in files:
        extra = set(_frontmatter_keys(f)) - set(SKILL_KEYS)
        assert not extra, f"{f.parent.name}: undocumented keys {sorted(extra)}"


def test_mise_lint_covers_every_shell_file():
    toml = (ROOT / ".mise.toml").read_text()
    lint = toml.split("[tasks.lint]")[1].split("\n[")[0]
    assert "shellcheck scripts/*.sh skills/*/scripts/*.sh skills/_lib/*.sh hooks/*.sh" in lint


def test_gitignore_covers_uv_run_leftovers():
    """uv-run tooling drops .venv/; the repo root ignores it (uv.lock is deliberately tracked)."""
    assert ".venv/" in GITIGNORE.read_text().splitlines()


RETIRED_SCM_SKILLS = (
    "github-pullrequests-update",
    "github-pullrequests-watch",
    "github-pullrequests-review-loop",
    "gitlab-mergerequests-list",
    "gitlab-mergerequests-update",
    "gitlab-mergerequests-watch",
)


def test_retired_scm_skills_are_gone():
    """The six host-specific skills are deleted with no aliases; no tracked file outside
    docs/plans/ (history) and this test names them."""
    import subprocess

    for name in RETIRED_SCM_SKILLS:
        assert not (ROOT / "skills" / name).exists(), f"skills/{name} still exists"
    this = Path(__file__).resolve().relative_to(ROOT).as_posix()
    pattern = "|".join(RETIRED_SCM_SKILLS)
    out = subprocess.run(
        ["git", "grep", "-lE", pattern, "--", ".", ":!docs/plans", ":!CHANGELOG.md", f":!{this}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert out.returncode == 1 and not out.stdout, f"retired names still referenced:\n{out.stdout}"
