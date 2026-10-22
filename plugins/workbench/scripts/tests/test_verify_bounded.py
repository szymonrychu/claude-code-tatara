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


def test_main_command_timeout_kills_and_reports(repo):
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


def test_prev_head_not_a_sha_is_a_json_result(repo):
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


def test_targeted_builds_from_changed_test_files(repo):
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


def test_no_targeted_tests_is_a_failed_result(repo):
    branch(repo)
    commit(repo, {"lib.py": "x\n"})
    out = verify(repo, None, "--no-triage")
    assert out["passed"] is False and out["error"] == "no targeted tests"
    assert out["commandScope"] == "targeted"


def test_tdd_runs_command_at_most_twice_and_reuses_head_exit(repo, monkeypatch):
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
