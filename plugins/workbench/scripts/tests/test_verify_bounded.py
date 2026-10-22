"""verify-task: bounded runs, sha-checked --prev-head, targeted commands, one base run."""

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_verify_task as base  # noqa: E402
from test_verify_task import SCRIPT, TEST_RE, branch, commit, git, vt  # noqa: E402
from test_verify_task import verify as _verify  # noqa: E402

repo = base.repo
SLEEP = "sleep 30"


def verify(root, command, *extra, acs=None):
    if command is not None:
        return _verify(root, command, *extra, acs=acs)
    argv = ["--worktree", str(root), "--base", "main", "--markers", "TODO", "--test-re", TEST_RE]
    if acs is not None:
        f = Path(root).parent / "acs.json"
        f.write_text(json.dumps(acs))
        argv += ["--acs", str(f)]
    code, out = vt.build([*argv, *extra])
    assert code == 0
    return out


def raw(root, *extra, cmd="true"):
    argv = ["--worktree", str(root), "--base", "main", "--markers", "TODO", "--test-re", TEST_RE]
    return vt.build([*argv, *(["--cmd", cmd] if cmd else []), *extra])


def test_command_timeout_reports_timeout_field(repo):
    branch(repo)
    t0 = time.time()
    out = verify(repo, "echo started; sleep 30", "--no-triage", "--timeout", "1")
    assert time.time() - t0 < 15
    assert out["timeout"] == {"command": "echo started; sleep 30", "seconds": 1.0}
    assert out["exit"] == 124 and out["passed"] is False
    assert "started" in out["evidence"]


def test_timeout_kills_the_process_group(repo, tmp_path):
    branch(repo)
    marker = tmp_path / "survivor"
    cmd = f"(sleep 3; touch {marker}) & sleep 30"
    verify(repo, cmd, "--no-triage", "--timeout", "1")
    time.sleep(4)
    assert not marker.exists()


def test_no_timeout_field_value_when_fast(repo):
    branch(repo)
    assert verify(repo, "true", "--no-triage")["timeout"] is None


def test_command_ac_timeout(repo):
    branch(repo)
    acs = [{"id": "C", "text": "slow", "evidence": {"kind": "command", "ref": SLEEP}}]
    out = verify(repo, "true", "--no-triage", "--timeout", "1", acs=acs)
    ac = out["acs"][0]
    assert ac["met"] is False and ac["timeout"] == {"command": SLEEP, "seconds": 1.0}


def test_run_argv_timeout():
    assert vt.run_argv(["sleep", "30"], ".", 1) == 124


def test_install_timeout(repo, tmp_path, monkeypatch):
    commit(repo, {"package.json": "{}\n", "package-lock.json": "{}\n"}, "pkg")
    branch(repo)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    npm = bindir / "npm"
    npm.write_text("#!/bin/sh\nsleep 30\n")
    npm.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:/usr/bin:/bin")
    out = verify(repo, "true", "--no-triage", "--install", "--timeout", "1")
    assert out["installed"][0]["exit"] == 124
    assert out["installed"][0]["timeout"]["seconds"] == 1.0


def test_non_sha_prev_head_is_a_json_error(repo):
    branch(repo)
    prose = "see the previous round please, it was fine and long"
    code, out = raw(repo, "--prev-head", prose)
    assert code == 2 and out["passed"] is False
    assert out["error"] == f"prev-head is not a sha: {prose[:40]}"
    assert len(out["error"]) == len("prev-head is not a sha: ") + 40


def test_prev_head_cli_prints_json_exit_2(repo):
    branch(repo)
    argv = ["--worktree", str(repo), "--cmd", "true", "--base", "main", "--markers", "TODO"]
    argv += ["--test-re", TEST_RE, "--prev-head", "HEAD~1"]
    r = subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)
    assert r.returncode == 2
    assert json.loads(r.stdout)["error"].startswith("prev-head is not a sha: HEAD~1")


def test_valid_prev_head_keeps_changed_since_previous(repo):
    branch(repo)
    prev = git(repo, "rev-parse", "--short", "HEAD")
    commit(repo, {"n.py": "1\n"})
    out = verify(repo, "true", "--no-triage", "--prev-head", prev)
    assert [c["file"] for c in out["changedSincePrevious"]] == ["n.py"]


def targeted_repo(repo):
    commit(repo, {"pyproject.toml": "[project]\nname='x'\n"}, "seed")
    branch(repo)
    commit(repo, {"tests/test_a.py": "def test_a():\n    pass\n", "lib.py": "x = 1\n"})


def test_targeted_builds_command_from_refs_and_changed_tests(repo):
    targeted_repo(repo)
    out = verify(repo, None, "--no-triage")
    assert out["commandScope"] == "targeted"
    assert out["command"] == "pytest tests/test_a.py -q"
    assert out["passed"] is True


def test_targeted_flag_overrides_cmd_and_dedupes_ac_refs(repo):
    targeted_repo(repo)
    acs = [
        {"id": "A", "text": "a", "evidence": {"kind": "test", "ref": "tests/test_a.py::test_a"}},
        {"id": "B", "text": "b", "evidence": {"kind": "test", "ref": "tests/test_a.py::test_a"}},
    ]
    out = verify(repo, "false", "--no-triage", "--targeted", acs=acs)
    assert out["command"] == "pytest tests/test_a.py -q"
    assert out["commandScope"] == "targeted"


def test_explicit_cmd_scope(repo):
    branch(repo)
    assert verify(repo, "true", "--no-triage")["commandScope"] == "command"


def test_targeted_without_tests_fails_with_error(repo):
    branch(repo)
    commit(repo, {"lib.py": "x\n"})
    out = verify(repo, None, "--no-triage")
    assert out["passed"] is False and out["error"] == "no targeted tests"
    assert out["commandScope"] == "targeted"


def test_tdd_revert_runs_at_most_twice(repo, monkeypatch):
    commit(repo, {"lib_a.py": "OLD\n"}, "seed")
    branch(repo)
    commit(repo, {"lib_a.py": "NEW\n"})
    calls = []
    real = vt.run_shell
    monkeypatch.setattr(vt, "run_shell", lambda c, d, t=None: calls.append(c) or real(c, d, t))
    out = verify(repo, "grep -q NEW lib_a.py", "--no-triage", "--tdd-revert")
    assert calls == ["grep -q NEW lib_a.py"] * 2
    assert out["tdd"]["baseCommand"] == "grep -q NEW lib_a.py"
    assert out["tdd"]["failedOnBase"] is True and out["tdd"]["passedOnHead"] is True


def test_tdd_base_runs_only_ref_runner_commands(repo, monkeypatch):
    files = {"pyproject.toml": "[project]\nname='x'\n", "lib_a.py": "OLD\n"}
    commit(repo, {**files, ".gitignore": ".pytest_cache\n__pycache__\n"}, "seed")
    branch(repo)
    commit(repo, {"lib_a.py": "NEW\n", "tests/test_a.py": "def test_a():\n    pass\n"})
    acs = [{"id": "A", "text": "a", "evidence": {"kind": "test", "ref": "tests/test_a.py::test_a"}}]
    calls = []
    real = vt.run_shell
    monkeypatch.setattr(vt, "run_shell", lambda c, d, t=None: calls.append(c) or real(c, d, t))
    out = verify(repo, "true", "--no-triage", "--tdd-revert", acs=acs)
    assert calls == ["true", "pytest tests/test_a.py -q"]
    assert out["tdd"]["baseCommand"] == "pytest tests/test_a.py -q"
    assert out["tdd"]["passedOnHead"] is True and out["clean"] is True


def test_tdd_base_timeout_is_bounded(repo):
    commit(repo, {"lib_a.py": "OLD\n"}, "seed")
    branch(repo)
    commit(repo, {"lib_a.py": "NEW\n"})
    cmd = "grep -q NEW lib_a.py || sleep 30"
    out = verify(repo, cmd, "--no-triage", "--tdd-revert", "--timeout", "1")
    assert out["tdd"]["timeout"] == {"command": cmd, "seconds": 1.0}
    assert out["tdd"]["failedOnBase"] is True and out["clean"] is True


def test_timeout_evidence_is_not_duplicated():
    code, out = vt.run_shell("echo a; echo b; sleep 30", ".", 1)
    assert code == 124 and out == "a\nb\n"


def test_steps_after_deadline_are_skipped(repo):
    branch(repo)
    acs = [{"id": "A1", "text": "t", "evidence": {"kind": "command", "ref": "sleep 30"}}]
    t0 = time.time()
    out = verify(repo, "sleep 30", "--no-triage", "--timeout", "2", acs=acs)
    assert time.time() - t0 < 10
    assert out["timeout"] == {"command": "sleep 30", "seconds": 2.0}
    assert out["passed"] is False
    assert out["skipped"] == ["ac A1: sleep 30"]
    assert out["acs"][0]["met"] is False


def test_deadline_spans_main_run_and_ac_run(repo):
    branch(repo)
    acs = [{"id": "A1", "text": "t", "evidence": {"kind": "command", "ref": "sleep 30"}}]
    t0 = time.time()
    out = verify(repo, "sleep 1.5", "--no-triage", "--timeout", "3", acs=acs)
    assert 2.5 < time.time() - t0 < 10
    assert out["exit"] == 0 and out["passed"] is False
    assert out["timeout"] == {"command": "sleep 30", "seconds": 3.0}
    assert out["skipped"] == []


def test_skips_tdd_revert_after_deadline(repo):
    commit(repo, {"lib_a.py": "OLD\n"}, "seed")
    branch(repo)
    commit(repo, {"lib_a.py": "NEW\n"})
    out = verify(repo, "sleep 30", "--no-triage", "--tdd-revert", "--timeout", "1")
    assert out["tdd"]["ran"] is False
    assert out["skipped"] == ["tdd-revert: sleep 30"]
    assert out["clean"] is True


def test_default_shared_deadline_is_540():
    assert vt.DEFAULT_TIMEOUT == 540


def test_shared_deadline_spans_main_and_tdd_runs(repo):
    commit(repo, {"lib_a.py": "OLD\n"}, "seed")
    branch(repo)
    commit(repo, {"lib_a.py": "NEW\n"})
    t0 = time.time()
    out = verify(repo, "sleep 2", "--no-triage", "--tdd-revert", "--timeout", "3")
    assert time.time() - t0 < 4
    assert out["passed"] is False
    assert out["timeout"] is not None


def test_triage_is_capped_by_remaining_deadline(repo, monkeypatch):
    import triage

    seen = {}

    def fake_run(mode, data, *, runner=None, log=None, usage=None, timeout=None):
        seen["timeout"] = timeout
        return {"parking": [], "acs": []}

    monkeypatch.setattr(triage, "run", fake_run)
    branch(repo)
    commit(repo, {"lib_a.py": "NEW\n"})
    verify(repo, "true", "--timeout", "100")
    assert seen["timeout"] is not None and 0 < seen["timeout"] <= 100


def test_triage_run_passes_timeout_to_the_model_call(monkeypatch):
    import triage

    got = {}

    def fake_call(prompt, schema, **kw):
        got.update(kw)
        raise triage.claude_json.ClaudeJsonError("stop")

    monkeypatch.setattr(triage.claude_json, "call_with_meta", fake_call)
    triage.run("parking", ["x"], timeout=7.5)
    assert got["timeout"] == 7.5
