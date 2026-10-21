"""deploy-hook.py runs the configured deploy command then its verify."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "deploy-hook.py"


def make_repo(tmp_path, deploy=None):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    if deploy is not None:
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "workbench.json").write_text(json.dumps({"deploy": deploy}))
    return tmp_path


def run(repo, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), *args],
        capture_output=True,
        text=True,
    )


def test_none_configured(tmp_path):
    r = run(make_repo(tmp_path))
    assert r.returncode == 0
    assert r.stdout.strip() == "deploy: none configured"


def test_deploy_then_verify(tmp_path):
    repo = make_repo(tmp_path, {"command": "pwd > deployed.txt", "verify": "test -f deployed.txt"})
    r = run(repo)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DEPLOY ok" in r.stdout and "VERIFY ok" in r.stdout
    assert (repo / "deployed.txt").is_file()


def test_failed_deploy_skips_verify(tmp_path):
    repo = make_repo(tmp_path, {"command": "echo boom; exit 3", "verify": "touch verified.txt"})
    r = run(repo)
    assert r.returncode == 1
    assert "DEPLOY FAIL exit 3" in r.stdout and "boom" in r.stdout
    assert "VERIFY" not in r.stdout
    assert not (repo / "verified.txt").exists()


def test_verify_failure_shows_last_20_lines(tmp_path):
    repo = make_repo(tmp_path, {"command": "true", "verify": "seq 1 50; exit 2"})
    r = run(repo)
    assert r.returncode == 1
    assert "DEPLOY ok" in r.stdout and "VERIFY FAIL exit 2" in r.stdout
    lines = r.stdout.splitlines()
    assert "50" in lines and "31" in lines and "30" not in lines


def test_dry_run(tmp_path):
    repo = make_repo(tmp_path, {"command": "touch ran.txt", "verify": "touch ran2.txt"})
    r = run(repo, "--dry-run")
    assert r.returncode == 0
    assert "touch ran.txt" in r.stdout and "touch ran2.txt" in r.stdout
    assert not (repo / "ran.txt").exists() and not (repo / "ran2.txt").exists()
