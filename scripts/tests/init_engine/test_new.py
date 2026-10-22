import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from init_helpers import personal_lint  # noqa: E402


def g(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def test_new_two_components_local_bare(workbench, run_cli, allow_file):
    r = run_cli(
        "new",
        "--name",
        "demo",
        "--component",
        "api:python",
        "--component",
        "web:typescript",
        "--remote",
        "local-bare",
    )
    assert r.returncode == 0, r.stderr
    remotes = workbench.parent / "wb-remotes"
    for name in ("api", "web"):
        assert (remotes / f"{name}.git").is_dir()
        assert g("rev-parse", "main", cwd=remotes / f"{name}.git").returncode == 0
        comp = workbench / "code" / name
        for f in (
            "AGENTS.md",
            "CLAUDE.md",
            "MEMORY.md",
            "ROADMAP.md",
            ".mise.toml",
            ".gitignore",
            "README.md",
        ):
            assert (comp / f).is_file(), f
        assert (comp / "CLAUDE.md").read_text().strip() == "@AGENTS.md"
        assert g("remote", "get-url", "origin", cwd=comp).stdout.strip() == str(
            (remotes / f"{name}.git").resolve()
        )
        assert g("rev-list", "--count", "HEAD", cwd=comp).stdout.strip() == "1"
    mods = (workbench / ".gitmodules").read_text()
    assert '[submodule "api"]' in mods and "branch = main" in mods
    assert g("submodule", "status", cwd=workbench).stdout.count("code/") == 2
    assert "[tasks.test]" in (workbench / "code/api/.mise.toml").read_text()
    assert 'python = "' in (workbench / "code/api/.mise.toml").read_text()


@pytest.mark.parametrize(
    "lang,tool",
    [("python", "uv"), ("go", "go"), ("typescript", "node"), ("generic", "[tasks.fmt]")],
)
def test_scaffold_per_language(workbench, run_cli, allow_file, lang, tool):
    r = run_cli(
        "new",
        "--name",
        "p",
        "--component",
        f"c:{lang}",
        "--remote",
        f"local-bare:{workbench.parent / 'bare'}",
    )
    assert r.returncode == 0, r.stderr
    text = (workbench / "code/c/.mise.toml").read_text()
    assert tool in text
    for t in ("test", "lint", "fmt"):
        assert f"[tasks.{t}]" in text


def test_url_mode(workbench, run_cli, allow_file, tmp_path):
    bare = tmp_path / "given.git"
    subprocess.run(
        ["git", "init", "--bare", "-b", "main", str(bare)], check=True, capture_output=True
    )
    r = run_cli("new", "--name", "p", "--component", "solo", "--remote", f"url:{bare}")
    assert r.returncode == 0, r.stderr
    assert g("rev-parse", "main", cwd=bare).returncode == 0
    assert g("remote", "get-url", "origin", cwd=workbench / "code/solo").stdout.strip() == str(bare)


def test_url_mode_several_needs_placeholder(workbench, run_cli):
    r = run_cli(
        "new", "--name", "p", "--component", "a", "--component", "b", "--remote", "url:/x/y.git"
    )
    assert r.returncode == 1 and r.stderr.count("\n") == 1
    assert not (workbench / "code/a").exists()


def test_git_init_and_template_remote(workbench, run_cli, allow_file):
    assert g("rev-parse", "--git-dir", cwd=workbench).returncode != 0
    run_cli("new", "--name", "p", "--component", "a", "--remote", "local-bare")
    assert g("symbolic-ref", "HEAD", cwd=workbench).stdout.strip() == "refs/heads/main"
    g("remote", "add", "origin", "https://github.com/szymonrychu/workbench", cwd=workbench)
    r = run_cli("new", "--name", "p", "--component", "b", "--remote", "local-bare")
    assert r.returncode == 0, r.stderr
    assert g("remote", cwd=workbench).stdout.split() == ["template"]


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/szymonrychu/workbench",
        "https://github.com/szymonrychu/workbench.git",
        "git@github.com:szymonrychu/workbench.git",
        "ssh://git@github.com/szymonrychu/workbench",
    ],
)
def test_template_origin_renamed(workbench, run_cli, allow_file, url):
    g("init", "-b", "main", cwd=workbench)
    g("remote", "add", "origin", url, cwd=workbench)
    r = run_cli("new", "--name", "p", "--component", "a", "--remote", "local-bare")
    assert r.returncode == 0, r.stderr
    remotes = g("remote", cwd=workbench).stdout.split()
    assert remotes == ["template"]
    assert g("remote", "get-url", "template", cwd=workbench).stdout.strip() == url


def test_other_origin_kept_unless_flagged(workbench, run_cli, allow_file):
    g("init", "-b", "main", cwd=workbench)
    g("remote", "add", "origin", "https://git.corp.example/mirror/workbench.git", cwd=workbench)
    run_cli("new", "--name", "p", "--component", "a", "--remote", "local-bare")
    assert g("remote", cwd=workbench).stdout.split() == ["origin"]
    run_cli(
        "new", "--name", "p", "--component", "b", "--remote", "local-bare", "--origin-is-template"
    )
    assert g("remote", cwd=workbench).stdout.split() == ["template"]


@pytest.mark.parametrize("bad", ["Api", "a_b", "-a", "a-", "a b", ""])
def test_refuses_bad_names(workbench, run_cli, bad):
    r = run_cli("new", "--name", "p", f"--component={bad}", "--remote", "local-bare")
    assert r.returncode == 1
    assert r.stderr.count("\n") == 1


def test_refuses_existing_component(workbench, run_cli):
    (workbench / "code" / "api").mkdir()
    r = run_cli("new", "--name", "p", "--component", "api", "--remote", "local-bare")
    assert r.returncode == 1 and "already exists" in r.stderr
    assert not (workbench.parent / "wb-remotes").exists()


def test_usage_errors_exit_2(run_cli):
    assert run_cli("new", "--name", "p").returncode == 2
    assert run_cli("bogus").returncode == 2


def test_unknown_remote_and_lang_refused(run_cli):
    assert run_cli("new", "--name", "p", "--component", "a", "--remote", "ftp:x").returncode == 1
    assert (
        run_cli("new", "--name", "p", "--component", "a:cobol", "--remote", "local-bare").returncode
        == 1
    )


def test_local_bare_without_file_allow_prints_command(workbench, run_cli):
    r = run_cli("new", "--name", "p", "--component", "a", "--remote", "local-bare")
    assert r.returncode == 1
    assert "-c protocol.file.allow=always submodule add" in r.stderr
    assert "protocol.file.allow" not in "".join(
        p.read_text()
        for p in (workbench / "scripts/init_engine").glob("*.py")
        if p.name != "gitops.py"
    )


def test_mise_task_present():
    task = Path(__file__).resolve().parents[3] / "mise-tasks/init/new"
    assert task.is_file() and task.stat().st_mode & 0o111


def test_doctor_sees_components(workbench, run_cli, allow_file):
    r = run_cli(
        "new", "--name", "p", "--component", "a", "--component", "b", "--remote", "local-bare"
    )
    assert r.returncode == 0, r.stderr
    lib = Path(__file__).resolve().parents[3] / "plugins/workbench/scripts/lib/workbench.py"
    d = subprocess.run(
        ["python3", str(lib), "doctor", "--from", str(workbench)],
        capture_output=True,
        text=True,
    )
    assert d.returncode == 0, d.stderr
    assert "kind:       metarepo" in d.stdout
    assert "components: 2" in d.stdout
    assert "NO REMOTE" not in d.stdout


def allow_entries(root):
    path = root / "scripts" / "personal-allow.local.json"
    return json.loads(path.read_text())["allow"] if path.is_file() else []


def test_init_allows_project_vocabulary(workbench, run_cli, allow_file):
    lint = personal_lint(workbench, "zorbaxproj")
    r = run_cli(
        "new", "--name", "zorbaxproj", "--component", "api:python", "--remote", "local-bare",
        "--purpose", "A zorbaxproj service.",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    digest = hashlib.sha256(b"zorbaxproj").hexdigest()
    assert allow_entries(workbench) == [{"path": "**", "pattern": digest}]
    assert lint().returncode == 0, lint().stdout
    assert g("status", "--porcelain", cwd=workbench).stdout == ""
    tracked = g("ls-files", "scripts/personal-allow.local.json", cwd=workbench).stdout
    assert tracked.strip() == "scripts/personal-allow.local.json"


def test_literal_hits_not_auto_allowed(workbench, run_cli, allow_file):
    lint = personal_lint(workbench, patterns=["litproj"])
    r = run_cli(
        "new", "--name", "litproj", "--component", "api:python", "--remote", "local-bare",
        "--purpose", "A litproj service.",
    )  # fmt: skip
    assert r.returncode == 0, r.stderr
    assert allow_entries(workbench) == []
    out = lint()
    assert out.returncode == 1 and "litproj" in out.stdout
