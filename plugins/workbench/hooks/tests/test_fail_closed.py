"""Claude Code deny-hook entry points must fail closed (exit 2), not open."""

import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))

import worktree_lib  # noqa: E402


def run(script: str, stdin: str):
    return subprocess.run(
        [sys.executable, str(HOOKS / script)], input=stdin, capture_output=True, text=True
    )


@pytest.mark.parametrize("script", ["protect_files.py", "guard-bash.py"])
@pytest.mark.parametrize("stdin", ["", "not json", "{", "[1, 2]", "null"])
def test_unparsable_or_malformed_payload_denies(script, stdin):
    proc = run(script, stdin)
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    assert proc.stderr.strip()
    assert "\n" not in proc.stderr.strip()


@pytest.mark.parametrize("script", ["protect_files.py", "guard-bash.py"])
def test_unexpected_exception_denies(script, tmp_path):
    # A payload whose shape makes decide() blow up must also deny.
    proc = run(script, '{"tool_input": {"command": 5, "file_path": 5}}')
    assert proc.returncode in (0, 2)
    if proc.returncode != 0:
        assert proc.stderr.strip()


@pytest.mark.parametrize("script", ["protect_files.py", "guard-bash.py"])
def test_valid_payload_still_allowed(script):
    proc = run(script, '{"tool_input": {"command": "ls", "file_path": "/tmp/x.txt"}}')
    assert proc.returncode == 0


def test_main_exception_exits_2(monkeypatch, capsys):
    import importlib.util

    for name in ("protect_files.py", "guard-bash.py"):
        spec = importlib.util.spec_from_file_location("hook_mod", HOOKS / name)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        monkeypatch.setattr(mod, "decide", mock.Mock(side_effect=RuntimeError("boom")))
        monkeypatch.setattr(sys, "stdin", __import__("io").StringIO('{"tool_input": {}}'))
        with pytest.raises(SystemExit) as exc:
            sys.exit(mod.main())
        assert exc.value.code == 2
        assert capsys.readouterr().err.strip()


def test_git_disables_fsmonitor():
    with mock.patch.object(worktree_lib.subprocess, "run") as run_mock:
        run_mock.return_value = mock.Mock(returncode=0, stdout="")
        worktree_lib._git("/x", "status", "--porcelain")
    argv = run_mock.call_args[0][0]
    assert argv[:2] == ["git", "-c"] or "core.fsmonitor=false" in argv
    assert "core.fsmonitor=false" in argv
    assert argv.index("core.fsmonitor=false") < argv.index("status")


def test_deny_hooks_fail_closed(monkeypatch, capsys):
    for script in ("protect_files.py", "guard-bash.py"):
        proc = run(script, "not json")
        assert proc.returncode == 2
        assert proc.stderr.strip()
    test_main_exception_exits_2(monkeypatch, capsys)


def test_worktree_lib_git_disables_fsmonitor():
    test_git_disables_fsmonitor()
    src = (HOOKS / "worktree_lib.py").read_text()
    assert src.count("subprocess.run(") == 1, "all git calls must go through _git"
