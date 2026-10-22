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


def personal_lint(root, *terms, patterns=()):
    """Give a temp workbench the real personal lint with a denylist of these hashed terms
    (and literal patterns); return a callable that runs the lint and returns the process."""
    import hashlib
    import json
    import shutil
    import sys
    from pathlib import Path

    repo = Path(__file__).resolve().parents[3]
    shutil.copy2(repo / "scripts" / "check_personal.py", root / "scripts" / "check_personal.py")
    hashes = sorted(hashlib.sha256(t.encode()).hexdigest() for t in terms)
    write(
        root,
        "scripts/personal-denylist.json",
        json.dumps({"patterns": list(patterns), "hashes": hashes, "allow": []}),
    )

    def run():
        return subprocess.run(
            [sys.executable, str(root / "scripts" / "check_personal.py"), "--root", str(root)],
            capture_output=True,
            text=True,
        )

    return run
