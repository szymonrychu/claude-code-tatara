import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def git_env(monkeypatch, tmp_path):
    """Local identity, no user config, and the file transport allowed (tests only)."""
    empty = tmp_path / "gitconfig"
    empty.write_text("")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    for k, v in {
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def allow_file(monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "protocol.file.allow")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "always")


@pytest.fixture
def workbench(tmp_path):
    """A temp workbench with the engine copied in and no git history, under <tmp>/wb."""
    dest = tmp_path / "wb"
    shutil.copytree(
        REPO / "scripts" / "init_engine",
        dest / "scripts" / "init_engine",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    for rel in ("AGENTS.md", ".mise.toml", "MEMORY.md", "ROADMAP.md", "docs/architecture.md"):
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest / rel)
    for rel in (
        ".claude/settings.json",
        ".claude/workbench.json",
        ".claude-plugin/marketplace.json",
        "LICENSE",
        "scripts/doctor.py",
        "plugins/workbench/scripts/lib/workbench.py",
        "docs/plans/todo/.gitkeep",
        "docs/plans/done/.gitkeep",
        "docs/plans/in-progress/.gitkeep",
    ):
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest / rel)
    stub = dest / "scripts" / "harness" / "setup.py"  # the real writer is covered by e2e
    stub.parent.mkdir(parents=True)
    stub.write_text(
        "import sys\nfrom pathlib import Path\n"
        "out = Path(__file__).resolve().parents[3] / 'harness-args'\n"
        "out.write_text(' '.join(sys.argv[1:]))\n"
    )
    (dest / "code").mkdir()
    (dest / "code" / ".gitkeep").write_text("")
    return dest


@pytest.fixture
def run_cli(workbench):
    def run(*args, cwd=None):
        return subprocess.run(
            [sys.executable, str(workbench / "scripts/init_engine/cli.py"), *args],
            cwd=cwd or workbench,
            capture_output=True,
            text=True,
        )

    return run
