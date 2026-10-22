"""init update safety: local notes survive, --url is honoured or refused, no option injection."""

import pytest
from init_helpers import LINT, sh, upstream_of, write


def forced_template_commit(project, tmp_path, files, name="up"):
    """Like template_commit, but adds gitignored paths too (the template may track them)."""
    work = tmp_path / name
    sh("clone", str(upstream_of(project)), str(work), cwd=tmp_path)
    for rel, text in files.items():
        write(work, rel, text)
    sh("add", "-A", "-f", cwd=work)
    sh("commit", "-m", "template change", cwd=work)
    sh("push", "origin", "HEAD:main", cwd=work)
    return sh("rev-parse", "HEAD", cwd=work).stdout.strip()


def state(project):
    return (
        sh("rev-parse", "HEAD", cwd=project).stdout,
        sh("status", "--porcelain", "--ignored", cwd=project).stdout,
        sh("remote", "get-url", "template", cwd=project, check=False).stdout,
    )


def has_commit(project, sha):
    return sh("cat-file", "-e", f"{sha}^{{commit}}", cwd=project, check=False).returncode == 0


def test_update_keeps_ignored_owned_files(project, run_cli, tmp_path):
    notes = {
        "docs/research/mine.md": "my research\n",
        "docs/handoffs/2026-10-22.md": "my handoff\n",
        "docs/plans/facts.md": "my facts\n",
    }
    for rel, text in notes.items():
        write(project, rel, text)
    assert sh("status", "--porcelain", cwd=project).stdout == ""  # all gitignored
    forced_template_commit(
        project,
        tmp_path,
        {"tooling.txt": "v2\n", "docs/research/more.md": "x\n", "docs/handoffs/t.md": "t\n"},
    )
    staged = ("docs/research/more.md", "docs/handoffs/t.md")

    aborted = run_cli("update", "--lint-command", "false")
    assert aborted.returncode == 1
    for rel, text in notes.items():
        assert (project / rel).read_text() == text, rel
    for gone in staged:
        assert not (project / gone).exists()
    assert (project / "tooling.txt").read_text() == "v1\n"

    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert (project / "tooling.txt").read_text() == "v2\n"
    for rel, text in notes.items():
        assert (project / rel).read_text() == text, rel
    tracked = sh("ls-files", cwd=project).stdout.split()
    for gone in staged:
        assert gone not in tracked
        assert not (project / gone).exists()
    assert sh("status", "--porcelain", cwd=project).stdout == ""


def test_update_restores_head_version_of_tracked_owned_file(project, run_cli, tmp_path):
    write(project, "docs/plans/todo/mine.md", "project epic\n")
    sh("add", "-A", cwd=project)
    sh("commit", "-m", "project epic", cwd=project)
    forced_template_commit(
        project, tmp_path, {"docs/plans/todo/mine.md": "template epic\n", "tooling.txt": "v2\n"}
    )
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert (project / "docs/plans/todo/mine.md").read_text() == "project epic\n"
    assert sh("status", "--porcelain", cwd=project).stdout == ""


def test_update_refuses_ignored_note_the_template_would_overwrite(project, run_cli, tmp_path):
    write(project, "docs/research/n.md", "my note\n")
    forced_template_commit(project, tmp_path, {"docs/research/n.md": "template note\n"})
    before = state(project)
    r = run_cli("update", *LINT)
    assert r.returncode == 1
    assert r.stderr.startswith("refused:")
    assert "docs/research/n.md" in r.stderr
    assert (project / "docs/research/n.md").read_text() == "my note\n"
    assert state(project) == before
    assert not (project / ".git" / "MERGE_HEAD").exists()


def test_update_refuses_url_mismatch_with_template_remote(project, run_cli, tmp_path):
    sha = forced_template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    url = sh("remote", "get-url", "template", cwd=project).stdout.strip()
    other = "https://example.invalid/other"
    before = state(project)
    r = run_cli("update", "--url", other, *LINT)
    assert r.returncode == 1
    assert r.stderr.startswith("refused:")
    assert url in r.stderr
    assert other in r.stderr
    assert f"git remote set-url template {other}" in r.stderr
    assert state(project) == before
    assert not has_commit(project, sha)
    assert (project / "tooling.txt").read_text() == "v1\n"


def test_update_accepts_url_equal_to_template_remote(project, run_cli, tmp_path):
    forced_template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    url = sh("remote", "get-url", "template", cwd=project).stdout.strip()
    r = run_cli("update", "--url", url, *LINT)
    assert r.returncode == 0, r.stderr
    assert (project / "tooling.txt").read_text() == "v2\n"


def test_update_prints_source(project, run_cli, tmp_path):
    sha = forced_template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    url = sh("remote", "get-url", "template", cwd=project).stdout.strip()
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    line = f"template: {url} main {sha}"
    assert line in r.stdout
    assert r.stdout.index(line) < r.stdout.index("committed ")
    again = run_cli("update", *LINT)
    assert again.returncode == 0, again.stderr
    assert line in again.stdout


@pytest.mark.parametrize(
    "flag",
    ["--branch=-x", "--branch=--upload-pack=touch pwned", "--base=-x", "--base=--all"],
)
def test_update_refuses_option_like_branch_and_base(project, run_cli, tmp_path, flag):
    sha = forced_template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    before = state(project)
    r = run_cli("update", flag, *LINT)
    assert r.returncode == 1
    assert r.stderr.startswith("refused:")
    assert flag.split("=")[0] in r.stderr
    assert state(project) == before
    assert not has_commit(project, sha)
    assert not (project / "pwned").exists()
