"""End-to-end fixtures: a template copy built from HEAD plus the working-tree changes under
test, with a local git identity and no remote except local bare repos."""

import io
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from helpers import REPO, git, run  # noqa: E402


def overlay_working_tree(dest: Path) -> None:
    """Apply tracked modifications, deletions and new (untracked, not ignored) files."""
    out = run("git", "diff", "--name-status", "-z", "HEAD", cwd=REPO).stdout.split("\0")
    deleted, changed = [], []
    it = iter(x for x in out if x)
    for status in it:
        if status[0] in "RC":
            old, new = next(it), next(it)
            deleted.append(old)
            changed.append(new)
        else:
            path = next(it)
            (deleted if status[0] == "D" else changed).append(path)
    new = run("git", "ls-files", "-o", "--exclude-standard", "-z", cwd=REPO).stdout.split("\0")
    changed += [p for p in new if p]
    for rel in deleted:
        (dest / rel).unlink(missing_ok=True)
    for rel in changed:
        src = REPO / rel
        if not (src.is_file() or src.is_symlink()):
            continue  # a submodule gitlink or a directory entry
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        if (dest / rel).is_symlink() or (dest / rel).exists():
            (dest / rel).unlink()
        shutil.copy2(src, dest / rel, follow_symlinks=False)


@pytest.fixture(autouse=True)
def git_env(monkeypatch, tmp_path):
    """Local identity, no user git config, and the file transport allowed for local bare
    submodules (e2e only; production code never sets protocol.file.allow)."""
    empty = tmp_path / "gitconfig"
    empty.write_text("")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    for k, v in {
        "GIT_AUTHOR_NAME": "E2E",
        "GIT_AUTHOR_EMAIL": "e2e@example.com",
        "GIT_COMMITTER_NAME": "E2E",
        "GIT_COMMITTER_EMAIL": "e2e@example.com",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "protocol.file.allow",
        "GIT_CONFIG_VALUE_0": "always",
        "MISE_TRUSTED_CONFIG_PATHS": str(tmp_path),
        "MISE_YES": "1",
    }.items():
        monkeypatch.setenv(k, v)
    for k in ("WORKBENCH_ROOT", "CLAUDE_PROJECT_DIR"):
        monkeypatch.delenv(k, raising=False)


@pytest.fixture
def template(tmp_path) -> Path:
    """tmp_path/proj: git archive HEAD + working-tree changes, a git repo with one commit."""
    dest = tmp_path / "proj"
    dest.mkdir()
    data = subprocess.run(
        ["git", "archive", "HEAD"], cwd=REPO, capture_output=True, check=True
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        tf.extractall(dest, filter="tar")
    overlay_working_tree(dest)
    git("init", "-q", "-b", "main", cwd=dest)
    git("config", "user.name", "E2E", cwd=dest)
    git("config", "user.email", "e2e@example.com", cwd=dest)
    git("add", "-A", cwd=dest)
    git("commit", "-q", "-m", "template", cwd=dest)
    return dest


@pytest.fixture
def engine(template):
    def call(*args, check=True):
        return run(
            "python3", str(template / "scripts/init_engine/cli.py"), *args,
            cwd=template, check=check,
        )  # fmt: skip

    return call


@pytest.fixture
def mise(template):
    def call(*args, check=True):
        return run("mise", *args, cwd=template, check=check)

    return call
