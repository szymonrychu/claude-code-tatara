"""user-run-step.py: prepare prints the pasteable command, check parses the result."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "user-run-step.py"
REF = ROOT / "skills" / "start-development" / "references" / "user-run-steps.md"


def spec(tmp_path, **kw):
    data = {"name": "s", "command": "echo hi", "pre": [], "post": [], "expect": ""}
    data.update(kw)
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(data))
    return str(p)


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_prepare_prints_command(tmp_path):
    r = run("prepare", spec(tmp_path, pre=["true"], command="uname -r"))
    assert r.returncode == 0
    assert "PRE ok true" in r.stdout
    assert "! uname -r" in r.stdout.splitlines()


def test_prepare_failure_exit_1_no_command(tmp_path):
    r = run("prepare", spec(tmp_path, pre=["exit 3"]))
    assert r.returncode == 1
    assert "PRE FAIL exit 3 exit 3" in r.stdout
    assert "! echo hi" not in r.stdout


def test_check_parses_result(tmp_path):
    ok = run("check", spec(tmp_path, post=["echo kernel 6.1"], expect=r"kernel 6\.\d"))
    assert ok.returncode == 0 and "RESULT pass" in ok.stdout
    bad = run("check", spec(tmp_path, post=["echo nope"], expect="kernel"))
    assert bad.returncode == 1
    assert "RESULT fail:" in bad.stdout and "nope" in bad.stdout


def test_check_tail_is_last_20_lines(tmp_path):
    r = run("check", spec(tmp_path, post=["seq 1 50"], expect="zzz"))
    assert "\n30\n" not in r.stdout and "\n31\n" in r.stdout


def test_check_failing_post_command_fails(tmp_path):
    r = run("check", spec(tmp_path, post=["exit 2"], expect=""))
    assert r.returncode == 1 and "RESULT fail:" in r.stdout


@pytest.mark.parametrize(
    "bad",
    [
        "echo x > /tmp/f",
        "echo x > file",
        "cmd 2>err.log",
        "echo >> f",
        "echo x >/dev/nullx",
        "echo x >/dev/null >f",
        "sudo ls",
        "rm -f x",
        "echo a | tee f",
        "dd if=/dev/zero",
    ],
)
@pytest.mark.parametrize("sub,field", [("prepare", "pre"), ("check", "post")])
def test_file_redirects_still_refused(tmp_path, bad, sub, field):
    marker = tmp_path / "ran"
    kw = {field: [f"touch {marker}", bad]}
    r = run(sub, spec(tmp_path, **kw))
    assert r.returncode == 2
    assert not marker.exists()


@pytest.mark.parametrize(
    "ok",
    [
        "ls >/dev/null",
        "ls > /dev/null",
        "ls 2>/dev/null",
        "ls 2> /dev/null",
        "ls &>/dev/null",
        "ls &> /dev/null",
        "ls 2>&1",
        "ls 2> &1",
        "ls >/dev/null 2>&1",
        "ls 2>/dev/null | cat",
    ],
)
@pytest.mark.parametrize("sub,field", [("prepare", "pre"), ("check", "post")])
def test_dev_null_redirects_allowed(tmp_path, ok, sub, field):
    r = run(sub, spec(tmp_path, **{field: [ok]}))
    assert r.returncode != 2, r.stderr


def test_reference_doc_names_flow():
    t = REF.read_text()
    for s in (
        "user-run-step.py prepare",
        "user-run-step.py check",
        "auto-mode classifier",
        "expect",
        "read-only",
    ):
        assert s in t
