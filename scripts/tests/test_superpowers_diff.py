"""superpowers-diff: report the vendored skill files an upstream release changed, never apply."""

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "superpowers_diff.py"
UPSTREAM_MD = REPO / "plugins" / "superpowers" / "UPSTREAM.md"
TASK = REPO / "mise-tasks" / "superpowers-diff"
SKILLS = REPO / "plugins" / "superpowers" / "skills"
ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "t@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}


def git(*args: str, cwd: Path) -> str:
    """Run git in cwd with a fixed identity and no user config.

    Args:
        *args (str): git arguments.
        cwd (Path): the working directory.

    Returns:
        str: stdout.
    """
    return subprocess.run(
        ["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True, check=True
    ).stdout


def write(root: Path, files: dict[str, str | None]) -> None:
    """Write (or, for None, delete) each repo-relative file under root."""
    for rel, text in files.items():
        path = root / rel
        if text is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


@pytest.fixture
def upstream(tmp_path: Path) -> Path:
    """A local upstream repo tagged v7.0.0 and v7.1.0."""
    up = tmp_path / "upstream"
    up.mkdir()
    git("init", "-q", "-b", "main", cwd=up)
    write(
        up,
        {
            "README.md": "readme\n",
            "skills/brainstorming/SKILL.md": "brainstorm v1\n",
            "skills/brainstorming/kept.md": "kept\n",
            "skills/writing-plans/SKILL.md": "plans\n",
            "skills/writing-plans/gone.md": "gone\n",
            "skills/writing-skills/SKILL.md": "not vendored v1\n",
        },
    )
    git("add", "-A", cwd=up)
    git("commit", "-qm", "v7.0.0", cwd=up)
    git("tag", "v7.0.0", cwd=up)
    write(
        up,
        {
            "README.md": "readme v2\n",
            "skills/brainstorming/SKILL.md": "brainstorm v2\n",
            "skills/writing-plans/gone.md": None,
            "skills/systematic-debugging/new.md": "new\n",
            "skills/writing-skills/SKILL.md": "not vendored v2\n",
            "skills/visual-companion/new.md": "not vendored\n",
        },
    )
    git("add", "-A", cwd=up)
    git("commit", "-qm", "v7.1.0", cwd=up)
    git("tag", "v7.1.0", cwd=up)
    return up


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A committed copy of the script and UPSTREAM.md, so writes would show in git status."""
    root = tmp_path / "repo"
    for src in (SCRIPT, UPSTREAM_MD):
        dest = root / src.relative_to(REPO)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    git("init", "-q", "-b", "main", cwd=root)
    git("add", "-A", cwd=root)
    git("commit", "-qm", "base", cwd=root)
    return root


def run(repo: Path, version: str, upstream: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(repo / "scripts/superpowers_diff.py"),
            version,
            "--upstream",
            str(upstream),
        ],
        cwd=repo,
        env=ENV,
        capture_output=True,
        text=True,
    )


def test_prints_changed_added_and_removed_vendored_files(repo, upstream):
    r = run(repo, "7.1.0", upstream)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [
        "skills/brainstorming/SKILL.md",
        "skills/systematic-debugging/new.md",
        "skills/writing-plans/gone.md",
    ]
    assert git("status", "--porcelain", cwd=repo) == ""


def test_prints_nothing_on_no_change(repo, upstream):
    r = run(repo, "7.0.0", upstream)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""
    assert git("status", "--porcelain", cwd=repo) == ""


def test_unknown_version_fails_named(repo, upstream):
    r = run(repo, "9.9.9", upstream)
    assert r.returncode != 0
    assert "v9.9.9" in r.stderr


def test_upstream_md_records_source_base_and_vendored_skills():
    text = UPSTREAM_MD.read_text()
    assert "https://github.com/obra/superpowers" in text
    assert "`v{version}`" in text
    assert "Base version: `7.0.0`" in text
    assert "mise run superpowers-diff" in text
    for skill in sorted(p.name for p in SKILLS.iterdir() if p.is_dir()):
        assert f"- `{skill}`: " in text, skill


def test_vendored_skills_parsed_from_upstream_md():
    sys.path.insert(0, str(SCRIPT.parent))
    import superpowers_diff

    info = superpowers_diff.read_upstream(UPSTREAM_MD)
    assert info.url == "https://github.com/obra/superpowers"
    assert info.tag_pattern == "v{version}"
    assert info.base == "7.0.0"
    assert sorted(info.skills) == sorted(p.name for p in SKILLS.iterdir() if p.is_dir())


def test_mise_task_wraps_the_script():
    assert TASK.stat().st_mode & stat.S_IXUSR
    text = TASK.read_text()
    assert "#MISE description=" in text
    assert "scripts/superpowers_diff.py" in text
    assert '"$@"' in text
