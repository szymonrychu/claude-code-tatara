"""release skill: judge semver from commits, changelog, commit and local tag."""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "release.py"
NAME = "workbench"
PD = "plugins/workbench"
PLUGIN_JSON = ".claude-plugin/plugin.json"
SKILLS = SKILL.parent
IGNORE = shutil.ignore_patterns("tests", "__pycache__")
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def git(repo, *args, check=True):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    if check and r.returncode:
        raise AssertionError(f"git {args}: {r.stderr}")
    return r.stdout.strip()


def commit(repo, subject, body="", path=None, text="x"):
    p = repo / (path or f"f{len(list(repo.iterdir()))}_{abs(hash(subject)) % 9999}.txt")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text + subject)
    git(repo, "add", "-A")
    msg = subject + (f"\n\n{body}" if body else "")
    git(repo, "commit", "-q", "-m", msg)


def make_repo(parent, name="r"):
    r = parent / name
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "T")
    plugin = r / PD
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / PLUGIN_JSON).write_text(
        json.dumps({"name": NAME, "version": "1.0.0", "hooks": {"a": 1}}, indent=2) + "\n"
    )
    (r / ".claude-plugin").mkdir()
    (r / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps({"plugins": [{"name": NAME, "version": "1.0.0"}]}, indent=2) + "\n"
    )
    scripts = plugin / "skills" / "release" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(SCRIPT, scripts / "release.py")
    shutil.copytree(SKILLS / "_lib", plugin / "skills" / "_lib", ignore=IGNORE)
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "chore: init 1.0.0")
    return r


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path)


def rel(repo, *args, check=True):
    r = subprocess.run(
        [sys.executable, str(repo / PD / "skills/release/scripts/release.py"), *args],
        capture_output=True,
        text=True,
        env=ENV,
    )
    if check:
        assert r.returncode == 0, r.stdout + r.stderr
    return r


def level_of(repo, *args):
    out = rel(repo, "--dry-run", *args).stdout
    return re.search(r"^level: (\w+)", out, re.M).group(1), out


def test_no_commits_refuses(repo):
    r = rel(repo, "--dry-run", check=False)
    assert r.returncode != 0
    assert "nothing to release" in r.stderr + r.stdout


def test_dry_run_writes_nothing(repo):
    commit(repo, "feat: a")
    before = git(repo, "rev-parse", "HEAD")
    out = rel(repo, "--dry-run").stdout
    assert re.search(r"^## v1\.1\.0 - \d{4}-\d\d-\d\d$", out, re.M)
    assert "### Features" in out
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "rev-parse", "HEAD") == before
    assert git(repo, "tag") == ""
    assert not (repo / PD / "CHANGELOG.md").exists()


def test_real_run(repo):
    commit(repo, "feat(a): shiny")
    commit(repo, "fix(b): crash")
    commit(repo, "chore(ticket): epic x done")
    commit(repo, "docs(record): epic x")
    commit(repo, "docs(plan): epic x")
    commit(repo, "refactor: tidy")
    rel(repo)
    plugin = (repo / PD / PLUGIN_JSON).read_text()
    assert '"version": "1.1.0"' in plugin
    assert '"hooks": {\n    "a": 1\n  }' in plugin
    mk = json.loads((repo / ".claude-plugin" / "marketplace.json").read_text())
    assert mk["plugins"][0]["version"] == "1.1.0"
    cl = (repo / PD / "CHANGELOG.md").read_text()
    assert re.search(r"^## v1\.1\.0 - \d{4}-\d\d-\d\d$", cl, re.M)
    assert "### Features" in cl and "shiny" in cl
    assert "### Fixes" in cl and "crash" in cl
    assert "### Other" in cl and "tidy" in cl
    assert "### Breaking" not in cl
    assert "epic x" not in cl
    assert git(repo, "log", "-1", "--format=%s") == "chore(release): v1.1.0"
    assert git(repo, "cat-file", "-t", "v1.1.0") == "tag"
    section = cl.split("# Changelog")[-1].strip()
    assert git(repo, "tag", "-l", "--format=%(contents)", "v1.1.0").strip() == section
    assert git(repo, "status", "--porcelain") == ""


def test_changelog_groups_breaking(repo):
    commit(repo, "feat!: gone")
    rel(repo)
    cl = (repo / PD / "CHANGELOG.md").read_text()
    assert "### Breaking" in cl and "gone" in cl
    assert "### Features" not in cl


def test_changelog_prepended_to_existing(repo):
    (repo / PD / "CHANGELOG.md").write_text("# Changelog\n\n## v1.0.0 - 2026-01-01\n\n- old\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "docs: changelog")
    commit(repo, "fix: z")
    rel(repo)
    cl = (repo / PD / "CHANGELOG.md").read_text()
    assert cl.index("## v1.0.1") < cl.index("## v1.0.0")
    assert cl.startswith("# Changelog")


def test_level_override_recorded(repo):
    commit(repo, "fix: tiny")
    out = rel(repo, "--level", "major").stdout
    assert "override" in out and "major" in out
    assert (repo / PD / PLUGIN_JSON).read_text().count('"version": "2.0.0"') == 1
    assert "override" in git(repo, "log", "-1", "--format=%B")
    assert "override" in git(repo, "tag", "-l", "--format=%(contents)", "v2.0.0")


def test_ascii_only(repo):
    commit(repo, "feat: café → ok")
    out = rel(repo, "--dry-run").stdout
    out.encode("ascii")
    rel(repo)
    (repo / PD / "CHANGELOG.md").read_text().encode("ascii")


def test_skill_md_contract():
    text = (SKILL / "SKILL.md").read_text()
    assert text.startswith("---\nname: release\n")
    for needle in ("release.py", "--dry-run", "--level", "never pushes", "v*"):
        assert needle in text, needle


def test_judge_major(tmp_path):
    repo = make_repo(tmp_path, "bang_subject")
    commit(repo, "feat(x)!: drop")
    lvl, out = level_of(repo)
    assert lvl == "major"
    assert "next: 2.0.0" in out

    repo = make_repo(tmp_path, "breaking_footer")
    commit(repo, "fix: a", body="why\n\nBREAKING CHANGE: format changed")
    assert level_of(repo)[0] == "major"

    repo = make_repo(tmp_path, "deleted_skill_dir")
    commit(repo, "feat: add", path=f"{PD}/skills/old/SKILL.md")
    git(repo, "tag", "-a", "v1.1.0", "-m", "x")
    git(repo, "rm", "-rq", f"{PD}/skills/old")
    git(repo, "commit", "-q", "-m", "refactor: remove old skill")
    lvl, out = level_of(repo)
    assert lvl == "major"
    assert "refactor: remove old skill" in out

    repo = make_repo(tmp_path, "deleted_agent")
    commit(repo, "feat: add", path=f"{PD}/agents/foo.md")
    git(repo, "tag", "-a", "v1.1.0", "-m", "x")
    git(repo, "rm", "-q", f"{PD}/agents/foo.md")
    git(repo, "commit", "-q", "-m", "chore: drop foo")
    assert level_of(repo)[0] == "major"


def test_judge_minor_patch_reasons(tmp_path):
    repo = make_repo(tmp_path, "patch_for_fixes_only")
    commit(repo, "fix(a): thing")
    commit(repo, "docs: words")
    assert level_of(repo)[0] == "patch"

    repo = make_repo(tmp_path, "minor_for_feat")
    commit(repo, "fix: a")
    commit(repo, "feat(x): new")
    lvl, out = level_of(repo)
    assert lvl == "minor"
    assert "feat(x): new" in out
    assert "next: 1.1.0" in out

    repo = make_repo(tmp_path, "deleting_other_files_is_not_major")
    commit(repo, "feat: add", path=f"{PD}/skills/s/scripts/x.py")
    git(repo, "tag", "-a", "v1.1.0", "-m", "x")
    git(repo, "rm", "-q", f"{PD}/skills/s/scripts/x.py")
    git(repo, "commit", "-q", "-m", "fix: drop script")
    assert level_of(repo)[0] == "patch"


def test_range_start(tmp_path):
    repo = make_repo(tmp_path, "range_starts_after_newest_tag")
    commit(repo, "feat: old")
    git(repo, "tag", "-a", "v1.1.0", "-m", "x")
    commit(repo, "fix: new")
    lvl, out = level_of(repo)
    assert lvl == "patch"
    assert "feat: old" not in out

    repo = make_repo(tmp_path, "range_starts_at_last_version_commit_without_tag")
    commit(repo, "feat!: before")
    p = repo / PD / PLUGIN_JSON
    p.write_text(p.read_text().replace("1.0.0", "1.0.1"))
    git(repo, "commit", "-qam", "chore: bump")
    commit(repo, "fix: after")
    lvl, out = level_of(repo)
    assert lvl == "patch"
    assert "before" not in out
    assert "next: 1.0.2" in out


def test_refusals_and_no_push(tmp_path):
    repo = make_repo(tmp_path, "refuses_dirty_tree")
    commit(repo, "fix: a")
    (repo / "junk.txt").write_text("x")
    r = rel(repo, check=False)
    assert r.returncode != 0 and "dirty" in r.stderr + r.stdout
    assert git(repo, "tag") == ""

    repo = make_repo(tmp_path, "refuses_other_branch")
    commit(repo, "fix: a")
    git(repo, "checkout", "-q", "-b", "feature")
    r = rel(repo, check=False)
    assert r.returncode != 0 and "main" in r.stderr + r.stdout
    assert git(repo, "tag") == ""

    repo = make_repo(tmp_path, "refuses_existing_tag")
    git(repo, "tag", "-a", "v1.0.1", "-m", "x")
    commit(repo, "fix: a")
    r = rel(repo, check=False)
    assert r.returncode != 0
    assert "exists" in r.stderr + r.stdout

    repo = make_repo(tmp_path, "never_pushes")
    bare = tmp_path / "bare.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    git(repo, "remote", "add", "origin", str(bare))
    commit(repo, "fix: a")
    rel(repo)
    assert git(bare, "tag") == ""
    assert git(bare, "branch", "-a") == ""


def test_readme_names_release():
    readme = (SKILL.parents[1] / "README.md").read_text()
    assert re.search(r"^release\s+judge major/minor/patch", readme, re.M)
    assert "skills/release/scripts/release.py --dry-run" in readme
    assert "chore(release): vX.Y.Z" in readme


def test_rename_still_judges_major(tmp_path):
    repo = make_repo(tmp_path, "renamed")
    commit(repo, "feat: add", path=f"{PD}/skills/old/SKILL.md", text="same body " * 20)
    commit(repo, "feat: add agent", path=f"{PD}/agents/foo.md", text="agent body " * 20)
    git(repo, "tag", "-a", "v1.1.0", "-m", "x")
    git(repo, "mv", f"{PD}/skills/old", f"{PD}/skills/new")
    git(repo, "commit", "-q", "-m", "refactor: rename skill")
    assert level_of(repo)[0] == "major"

    repo = make_repo(tmp_path, "renamed_agent")
    commit(repo, "feat: add agent", path=f"{PD}/agents/foo.md", text="agent body " * 20)
    git(repo, "tag", "-a", "v1.1.0", "-m", "x")
    git(repo, "mv", f"{PD}/agents/foo.md", f"{PD}/agents/bar.md")
    git(repo, "commit", "-q", "-m", "refactor: rename agent")
    assert level_of(repo)[0] == "major"


def test_changelog_dedupes_identical_subjects(repo):
    commit(repo, "feat(a): shiny", path="one.txt")
    commit(repo, "fix(b): crash", path="two.txt")
    commit(repo, "feat(a): shiny", path="three.txt")
    out = level_of(repo)[1]
    assert out.count("a: shiny") == 1
    assert out.count("b: crash") == 1


def test_failed_release_leaves_tree_clean(tmp_path):
    repo = make_repo(tmp_path, "nomarket")
    (repo / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps({"plugins": [{"name": "other", "version": "1.0.0"}]}, indent=2) + "\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "chore: market")
    commit(repo, "feat: a")
    r = rel(repo, check=False)
    assert r.returncode != 0
    assert "marketplace.json has no plugin entry" in r.stderr
    assert git(repo, "status", "--porcelain") == ""
    assert not (repo / PD / "CHANGELOG.md").exists()
    assert git(repo, "tag") == ""


def test_bumps_root_marketplace_and_manifest(repo):
    commit(repo, "feat: a")
    rel(repo)
    assert not (repo / PD / ".claude-plugin" / "marketplace.json").exists()
    mk = json.loads((repo / ".claude-plugin" / "marketplace.json").read_text())
    assert mk["plugins"][0]["version"] == "1.1.0"
    assert (repo / PD / "CHANGELOG.md").is_file()
    assert not (repo / "CHANGELOG.md").exists()
    changed = git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert sorted(changed) == [
        ".claude-plugin/marketplace.json",
        f"{PD}/.claude-plugin/plugin.json",
        f"{PD}/CHANGELOG.md",
    ]


def test_refuses_outside_template(tmp_path):
    outside = tmp_path / "plugins" / "workbench" / "skills" / "release" / "scripts"
    outside.mkdir(parents=True)
    shutil.copy(SCRIPT, outside / "release.py")
    shutil.copytree(SKILLS / "_lib", outside.parents[1] / "_lib", ignore=IGNORE)
    r = subprocess.run(
        [sys.executable, str(outside / "release.py"), "--dry-run"],
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert r.returncode != 0
    assert "not inside a workbench template tree" in r.stderr


def test_real_script_resolves_this_template_root():
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"], capture_output=True, text=True, env=ENV
    )
    assert "not inside a workbench template tree" not in r.stderr


def test_skill_md_for_maintainers():
    assert "maintainers of the template's" in (SKILL / "SKILL.md").read_text()
