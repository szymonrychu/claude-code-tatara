"""Pins secret scanning: exact gitleaks pin, empty allowlist, local hook, lint task, CI job."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]


def _fake_token() -> str:
    # built at run time so this file never contains a secret-shaped literal
    return "ghp_" + "".join(chr(ord("a") + (i * 7) % 26) for i in range(36))


def test_pinned_and_no_allowlist():
    tools = tomllib.loads((ROOT / ".mise.toml").read_text())["tools"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", tools["gitleaks"])
    assert tools["gitleaks"] == "8.30.1"
    test_gitleaks_config_extends_default_with_no_allowlist()


def test_gitleaks_config_extends_default_with_no_allowlist():
    cfg = tomllib.loads((ROOT / ".gitleaks.toml").read_text())
    assert cfg["extend"]["useDefault"] is True
    assert set(cfg) == {"extend"}
    text = (ROOT / ".gitleaks.toml").read_text()
    assert "allowlist" not in text.lower()


def test_precommit_hook():
    text = (ROOT / ".pre-commit-config.yaml").read_text()
    m = re.search(r"^.*id: gitleaks.*$", text, re.M)
    assert m, "no gitleaks hook"
    line = m.group(0)
    assert "gitleaks git --pre-commit --staged --redact" in line
    assert "mise exec --" in line
    assert "repo: local" in text
    assert not re.search(r"repo:\s*https?://", text)


def test_lint_task_detects_and_tree_is_clean(tmp_path):
    path = ROOT / "mise-tasks" / "lint" / "secrets"
    assert path.stat().st_mode & 0o111
    text = path.read_text()
    assert text.startswith("#!/usr/bin/env bash")
    assert "#MISE description=" in text
    assert "git ls-files -coz --exclude-standard" in text
    assert "--redact" in text and "--config" in text
    task = tmp_path / "mise-tasks" / "lint" / "secrets"
    task.parent.mkdir(parents=True)
    shutil.copy(path, task)
    shutil.copy(ROOT / ".gitleaks.toml", tmp_path / ".gitleaks.toml")
    (tmp_path / "leak.txt").write_text(f"token = {_fake_token()}\n")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    bad = _run_task(task)
    assert bad.returncode != 0, bad.stdout + bad.stderr
    assert "leaks found" in bad.stdout + bad.stderr
    assert _fake_token() not in bad.stdout + bad.stderr
    good = subprocess.run(
        ["mise", "exec", "--", "bash", str(path)], capture_output=True, text=True, cwd=ROOT
    )
    assert good.returncode == 0, good.stdout + good.stderr


def test_ci_secrets_job():
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    job = text.split("  secrets:\n", 1)[1]
    assert "fetch-depth: 0" in job
    assert "jdx/mise-action@" in job
    assert re.search(r"^\s*-\s*run:\s*mise install\s*$", job, re.M)
    assert "gitleaks dir . --redact" in job
    assert "gitleaks git . --redact" in job
    assert re.search(r"permissions:\s*\n\s*contents: read", text)


def test_scanner_detects_runtime_built_token(tmp_path):
    (tmp_path / "leak.txt").write_text(f"token = {_fake_token()}\n")
    r = subprocess.run(
        [
            "mise",
            "exec",
            "--",
            "gitleaks",
            "dir",
            str(tmp_path),
            "--redact",
            "--no-banner",
            "--config",
            str(ROOT / ".gitleaks.toml"),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode != 0, r.stdout + r.stderr
    assert _fake_token() not in r.stdout + r.stderr


def _run_task(task):
    """Run a copied task with the pinned gitleaks on PATH (the temp repo has no mise config)."""
    gl = subprocess.run(
        ["mise", "exec", "--", "which", "gitleaks"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    ).stdout.strip()
    env = {**os.environ, "PATH": f"{Path(gl).parent}{os.pathsep}{os.environ['PATH']}"}
    return subprocess.run(["bash", str(task)], capture_output=True, text=True, cwd=ROOT, env=env)


def _scan_repo(tmp_path, files, ignored_dirs=("wt",)):
    task = tmp_path / "mise-tasks" / "lint" / "secrets"
    task.parent.mkdir(parents=True)
    shutil.copy(ROOT / "mise-tasks" / "lint" / "secrets", task)
    shutil.copy(ROOT / ".gitleaks.toml", tmp_path / ".gitleaks.toml")
    (tmp_path / ".gitignore").write_text("".join(f"{d}/\n" for d in ignored_dirs))
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for rel, tracked in files.items():
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"token = {_fake_token()}\n")
        if tracked:
            subprocess.run(["git", "add", "-f", rel], cwd=tmp_path, check=True)
    r = _run_task(task)
    assert _fake_token() not in r.stdout + r.stderr
    return r


def test_lint_scans_git_view_not_ignored_dirs(tmp_path):
    ok = _scan_repo(tmp_path / "a", {"wt/old/leak.txt": False})
    assert ok.returncode == 0, ok.stdout + ok.stderr
    tracked = _scan_repo(tmp_path / "b", {"src/leak.txt": True})
    assert tracked.returncode != 0
    untracked = _scan_repo(tmp_path / "c", {"src/new.txt": False})
    assert untracked.returncode != 0


def _scan_with_vanishing_file(tmp_path, leak_in_other_file):
    """Run the task; tar/cp shims delete vanish.txt after listing, before the copy."""
    task = tmp_path / "mise-tasks" / "lint" / "secrets"
    task.parent.mkdir(parents=True)
    shutil.copy(ROOT / "mise-tasks" / "lint" / "secrets", task)
    shutil.copy(ROOT / ".gitleaks.toml", tmp_path / ".gitleaks.toml")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "vanish.txt").write_text("transient\n")
    (tmp_path / "other.txt").write_text(
        f"token = {_fake_token()}\n" if leak_in_other_file else "clean\n"
    )
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    for tool in ("tar", "cp"):
        # delete the file after it was listed and checked, right before the copy tool runs
        shim = shim_dir / tool
        shim.write_text(
            "#!/usr/bin/env bash\n"
            f'rm -f "{tmp_path}/vanish.txt"\n'
            f'exec "{shutil.which(tool)}" "$@"\n'
        )
        shim.chmod(0o755)
    gl = subprocess.run(
        ["mise", "exec", "--", "which", "gitleaks"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    ).stdout.strip()
    path = f"{shim_dir}{os.pathsep}{Path(gl).parent}{os.pathsep}{os.environ['PATH']}"
    return subprocess.run(
        ["bash", str(task)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={**os.environ, "PATH": path},
    )


def test_vanished_file_does_not_fail_scan(tmp_path):
    ok = _scan_with_vanishing_file(tmp_path / "a", leak_in_other_file=False)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "no leaks found" in ok.stdout + ok.stderr
    bad = _scan_with_vanishing_file(tmp_path / "b", leak_in_other_file=True)
    assert bad.returncode != 0
    assert "leaks found" in bad.stdout + bad.stderr
    assert _fake_token() not in bad.stdout + bad.stderr


def _gitlink_repo(tmp_path):
    """Temp repo with a real nested checkout `code/sub` recorded as a gitlink, plus code/.gitkeep."""
    task = tmp_path / "mise-tasks" / "lint" / "secrets"
    task.parent.mkdir(parents=True)
    shutil.copy(ROOT / "mise-tasks" / "lint" / "secrets", task)
    shutil.copy(ROOT / ".gitleaks.toml", tmp_path / ".gitleaks.toml")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    sub = tmp_path / "code" / "sub"
    sub.mkdir(parents=True)
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", "init", "-q"], cwd=sub, check=True)
    (sub / "leak.txt").write_text(f"token = {_fake_token()}\n")
    subprocess.run(["git", "add", "leak.txt"], cwd=sub, check=True)
    subprocess.run([*git, "commit", "-qm", "x"], cwd=sub, check=True)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=sub, capture_output=True, text=True, check=True
    ).stdout.strip()
    subprocess.run(
        ["git", "update-index", "--add", "--cacheinfo", f"160000,{sha},code/sub"],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / "code" / ".gitkeep").write_text("")
    return task


def test_lint_task_skips_gitlink_checkouts(tmp_path):
    task = _gitlink_repo(tmp_path)
    r = _run_task(task)
    assert r.returncode == 0, r.stdout + r.stderr
    assert _fake_token() not in r.stdout + r.stderr


def test_lint_task_scans_non_gitlink_files_under_code(tmp_path):
    task = _gitlink_repo(tmp_path)
    (tmp_path / "code" / "notes.txt").write_text(f"token = {_fake_token()}\n")
    r = _run_task(task)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "leaks found" in r.stdout + r.stderr
    assert _fake_token() not in r.stdout + r.stderr
