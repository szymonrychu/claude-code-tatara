"""verify-task makes at most one triage call per run, in `verify` mode."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
spec = importlib.util.spec_from_file_location("vt", SCRIPTS / "verify-task.py")
vt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vt)


def git(root, *a):
    subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "r"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@t")
    git(root, "config", "user.name", "t")
    (root / "README.md").write_text("# r\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "base")
    git(root, "checkout", "-q", "-b", "feature")
    (root / "m.py").write_text("# fix later maybe\nx = 1\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "work")
    return root


class Stub:
    def __init__(self, result=None, exc=None):
        self.calls, self.result, self.exc = [], result, exc

    def __call__(self, mode, data, **_):
        self.calls.append((mode, data))
        if self.exc:
            raise self.exc
        return self.result


def run(root, tmp_path, stub, *extra, acs=None):
    argv = ["--worktree", str(root), "--cmd", "true", "--base", "main", "--markers", "XXMARK",
            "--test-re", r"test_", *extra]  # fmt: skip
    if acs:
        f = tmp_path / "acs.json"
        f.write_text(json.dumps(acs))
        argv += ["--acs", str(f)]
    code, out = vt.build(argv, triage_run=stub)
    assert code == 0
    return out


JUDGE = [{"id": "AC1", "text": "tidy", "evidence": {"kind": "judgement"}}]


def test_one_verify_call_carries_every_part(repo, tmp_path):
    stub = Stub(
        {
            "parking": [{"file": "m.py", "line": 1, "text": "# fix later maybe", "reason": "d"}],
            "acs": [{"id": "AC1", "verdict": "yes", "reason": "ok"}],
            "classifierTier": "full",
            "error": None,
        }
    )
    out = run(repo, tmp_path, stub, "--requirement", "r", acs=JUDGE)
    assert [m for m, _ in stub.calls] == ["verify"]
    assert set(stub.calls[0][1]) == {"parking", "acs", "tier"}
    assert out["parking"][0]["reason"] == "d"
    assert out["acs"][0]["plausible"] == "yes" and out["tierHint"] == "full"


def test_no_part_needed_means_no_call(repo, tmp_path):
    (repo / "m.py").write_text("x = 1\n")
    git(repo, "commit", "-qam", "clean")
    stub = Stub({})
    out = run(repo, tmp_path, stub, "--no-tier")
    assert stub.calls == [] and out["tierHint"] is None


def test_no_tier_drops_only_the_tier_part(repo, tmp_path):
    stub = Stub({"parking": [], "acs": [], "classifierTier": None, "error": None})
    run(repo, tmp_path, stub, "--no-tier")
    assert set(stub.calls[0][1]) == {"parking"}


def test_failed_call_falls_back_with_a_note(repo, tmp_path):
    stub = Stub({"parking": [], "acs": [], "classifierTier": None, "error": "classifier failed: x"})
    out = run(repo, tmp_path, stub, acs=JUDGE)
    assert len(stub.calls) == 1
    assert out["parking"] == [] and out["tierHint"] is None
    assert out["acs"][0]["plausible"] is None
    assert "triage verify failed" in out["note"] and "classifier failed" in out["note"]
    out = run(repo, tmp_path, Stub(exc=RuntimeError("boom")), acs=JUDGE)
    assert out["acs"][0]["plausible"] is None and "boom" in out["note"]


def test_usage_counts_the_one_call(repo, tmp_path, monkeypatch):
    import triage

    def fake(mode, data, **kw):
        assert mode == "verify"
        kw["usage"]["calls"] += 1
        return {"parking": [], "acs": [], "classifierTier": "light", "error": None}

    monkeypatch.setattr(triage, "run", fake)
    out = run(repo, tmp_path, None, acs=JUDGE)
    assert out["triageUsage"]["calls"] == 1
