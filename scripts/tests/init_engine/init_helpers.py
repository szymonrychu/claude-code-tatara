"""Shared git helpers for the init_engine update tests."""

import subprocess

LINT = ["--lint-command", "true"]


def sh(*args, cwd, check=True):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def upstream_of(project):
    return project.parent / "upstream.git"


def template_commit(project, tmp_path, files, name="up"):
    work = tmp_path / name
    sh("clone", str(upstream_of(project)), str(work), cwd=tmp_path)
    for rel, text in files.items():
        write(work, rel, text)
    sh("add", "-A", cwd=work)
    sh("commit", "-m", "template change", cwd=work)
    sh("push", "origin", "HEAD:main", cwd=work)
    return sh("rev-parse", "HEAD", cwd=work).stdout.strip()
