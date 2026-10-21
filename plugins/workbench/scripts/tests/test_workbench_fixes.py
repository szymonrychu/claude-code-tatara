"""workbench.py refRunners: basename globs and {pkg} semantics."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS / "lib"))
import workbench  # noqa: E402


def repo(tmp_path, cfg):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "workbench.json").write_text(json.dumps(cfg))
    return tmp_path


def test_ref_runner_glob_matches_basename(tmp_path):
    r = repo(tmp_path, {"refRunners": {"*.go": "go test -run {name} {file}"}})
    (r / "pkg").mkdir()
    (r / "pkg" / "x_test.go").write_text("package pkg\n")
    out = workbench.runner_for("pkg/x_test.go::TestA", r)
    assert out is not None and out["source"] == "refRunners"
    assert out["argv"][-1] == "go test -run TestA pkg/x_test.go"


def test_pkg_placeholder_matches_doc(tmp_path):
    r = repo(tmp_path, {"refRunners": {"*.go": "echo {pkg}"}})
    (r / "svc").mkdir()
    (r / "svc" / "package.json").write_text("{}")
    out = workbench.runner_for("svc/a_test.go::T", r)
    assert out["argv"][-1] == "echo svc"
    assert out["cwd"] == str((r / "svc").resolve())
