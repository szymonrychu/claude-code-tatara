"""ticket.py facts: the generated repo facts pack docs/plans/facts.md (D8)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GITIGNORE = Path(__file__).resolve().parents[5] / ".gitignore"  # repo root; plugin has none
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


def git(repo, *a):
    return subprocess.run(
        ["git", "-C", str(repo), *a], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    (r / "docs" / "plans" / "todo" / "alpha" / "tasks").mkdir(parents=True)
    (r / "docs" / "plans" / "in-progress" / "beta" / "tasks").mkdir(parents=True)
    (r / "docs" / "plans" / "done" / "gone" / "tasks").mkdir(parents=True)
    (r / "pkg").mkdir()
    (r / "pkg" / "pyproject.toml").write_text("[project]\nname='p'\n")
    (r / "web").mkdir()
    (r / "web" / "package.json").write_text('{"devDependencies": {"vitest": "1"}}')
    (r / ".mise.toml").write_text(
        '[tasks.test]\nrun = "pytest -q"\n[tasks.lint]\nrun = "ruff check"\n'
        '[tasks.other]\nrun = "x"\n'
    )
    (r / ".claude").mkdir()
    (r / ".claude" / "workbench.json").write_text(
        json.dumps({"suites": ["make test"], "refRunners": {"*.go": "go test -run {name}"}})
    )
    p = r / "docs" / "plans"
    (p / "todo" / "alpha" / "README.md").write_text("---\ntitle: alpha\nrepos: [proj]\n---\n")
    (p / "todo" / "alpha" / "tasks" / "t1.md").write_text(
        "---\ntitle: t1\nstatus: todo\nowns: [thing]\nfiles: [src/a.py]\n---\nb\n"
    )
    (p / "todo" / "alpha" / "tasks" / "t2.md").write_text(
        "---\ntitle: t2\nstatus: done\nfiles: [src/z.py]\n---\nb\n"
    )
    (p / "in-progress" / "beta" / "README.md").write_text("---\ntitle: beta\n---\n")
    (p / "in-progress" / "beta" / "tasks" / "t3.md").write_text(
        "---\ntitle: t3\nstatus: in-progress\nfiles: [src/a.py]\n---\nb\n"
    )
    (p / "done" / "gone" / "README.md").write_text("---\ntitle: gone\n---\n")
    (p / "done" / "gone" / "tasks" / "t4.md").write_text(
        "---\ntitle: t4\nstatus: todo\nfiles: [src/q.py]\n---\nb\n"
    )
    (p / "contracts.json").write_text(
        json.dumps(
            [
                {
                    "name": "cfg",
                    "kind": "node",
                    "owner": "alpha",
                    "file": "src/a.py",
                    "consumers": ["beta"],
                    "note": "",
                }
            ]
        )
    )
    (r / ".gitignore").write_text(GITIGNORE.read_text())
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    for k, v in (("user.email", "a@b"), ("user.name", "n")):
        git(r, "config", k, v)
    git(r, "add", "-A")
    git(r, "commit", "-qm", "init")
    return r


def run(repo):
    return cli("facts", "--root", repo / "docs" / "plans")


def test_facts_sections(repo):
    r = run(repo)
    assert r.returncode == 0, r.stderr
    f = repo / "docs" / "plans" / "facts.md"
    assert r.stdout.strip() == str(f.resolve())
    text = f.read_text()
    for h in ("## Verify commands", "## AC ref conventions", "## Registries", "## File owners"):
        assert h in text
    assert git(repo, "rev-parse", "HEAD") in "\n".join(text.splitlines()[:3])


def test_package_runners_listed(repo):
    run(repo)
    text = (repo / "docs/plans/facts.md").read_text()
    assert "test: pytest -q" in text and "lint: ruff check" in text
    assert "other" not in text.split("## AC ref")[0]
    assert "suite: make test" in text
    assert "pkg/pyproject.toml" in text and "web/package.json" in text
    assert "vitest" in text
    # runners come from workbench.runner_for: PATH pytest unless the package locks pytest
    pkg_line = next(ln for ln in text.splitlines() if "pkg/pyproject.toml" in ln)
    assert "cd pkg && pytest tests/test_sample.py" in pkg_line, pkg_line


def test_ac_ref_conventions(repo):
    run(repo)
    text = (repo / "docs/plans/facts.md").read_text()
    sec = text.split("## AC ref conventions")[1].split("## Registries")[0]
    for k in ("test", "symbol", "command", "doc-section", "judgement"):
        assert f"`{k}`" in sec
    assert "package root" in sec
    assert "*.go" in sec and "go test -run {name}" in sec


def test_file_owners_open_only(repo):
    run(repo)
    text = (repo / "docs/plans/facts.md").read_text()
    assert "cfg" in text.split("## Registries")[1].split("## File owners")[0]
    owners = text.split("## File owners")[1]
    assert "src/a.py alpha/t1" in owners and "src/a.py beta/t3" in owners
    assert "thing alpha/t1" in owners
    assert "src/z.py" not in owners and "src/q.py" not in owners


def test_facts_not_committed(repo):
    run(repo)
    f = repo / "docs/plans/facts.md"
    f.write_text(f.read_text() + "JUNK\n")
    run(repo)
    assert "JUNK" not in f.read_text()
    assert "docs/plans/facts.md" in GITIGNORE.read_text().splitlines()
    assert git(repo, "check-ignore", "docs/plans/facts.md") == "docs/plans/facts.md"
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "log", "--format=%s") == "init"
