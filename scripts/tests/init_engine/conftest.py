import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from init_helpers import sh, write  # noqa: E402


@pytest.fixture(autouse=True)
def git_env(monkeypatch, tmp_path):
    """Local identity, no user config, and the file transport allowed (tests only)."""
    empty = tmp_path / "gitconfig"
    empty.write_text("")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    # git reads $XDG_CONFIG_HOME/git/ignore by default even with no global config;
    # a user-level ignore there hid a missing .gitignore once, so point it at nothing.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
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
    for rel in (
        "AGENTS.md",
        ".gitignore",
        ".mise.toml",
        "MEMORY.md",
        "ROADMAP.md",
        "docs/architecture.md",
    ):
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


@pytest.fixture
def project(workbench, run_cli, allow_file, tmp_path):
    """An initialised project sharing history with a bare template upstream."""
    sh("init", "-b", "main", cwd=workbench)
    write(workbench, "tooling.txt", "v1\n")
    write(workbench, "docs/plans/todo/epic.md", "template epic\n")
    write(workbench, "docs/research/r.md", "template research\n")
    sh("add", "-A", cwd=workbench)
    sh("commit", "-m", "template base", cwd=workbench)
    upstream = tmp_path / "upstream.git"
    sh("clone", "--bare", str(workbench), str(upstream), cwd=tmp_path)
    r = run_cli(
        "new", "--name", "demo", "--component", "api:python", "--remote", "local-bare",
        "--purpose", "A booking service.",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    sh("rm", "-rq", "--cached", "--ignore-unmatch", "docs/research", cwd=workbench)
    sh("add", "-A", cwd=workbench)
    sh("commit", "-m", "init project", cwd=workbench, check=False)
    sh("remote", "add", "template", str(upstream), cwd=workbench)
    return workbench
