"""Hook entry points must work without tomllib (python < 3.11) and deny on an unsupported python."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]


def run(script, stdin, tmp_path, shim):
    d = tmp_path / "shim"
    d.mkdir(exist_ok=True)
    (d / "sitecustomize.py").write_text(shim)
    env = dict(os.environ, PYTHONPATH=str(d))
    return subprocess.run(
        [sys.executable, str(HOOKS / script)], input=stdin, capture_output=True, text=True, env=env
    )


NO_TOMLLIB = "import sys\nsys.modules['tomllib'] = None\n"
OLD_PYTHON = "import sys\nsys.version_info = (3, 8, 0, 'final', 0)\n"

DENY = [
    ("guard-bash.py", {"tool_name": "Bash", "tool_input": {"command": "terraform destroy"}}),
    ("protect_files.py", {"tool_name": "Write", "tool_input": {"file_path": ".env"}}),
]
ALL = [
    "guard-bash.py",
    "protect_files.py",
    "subagent-commit-guard.py",
    "verify-recorder.py",
    "bash-output-filter.py",
    "agent-usage-recorder.py",
]


@pytest.mark.parametrize("script,payload", DENY)
def test_deny_hooks_still_deny_without_tomllib(script, payload, tmp_path):
    proc = run(script, json.dumps(payload), tmp_path, NO_TOMLLIB)
    assert "ModuleNotFoundError" not in proc.stderr, proc.stderr
    denied = proc.returncode == 2 or '"deny"' in proc.stdout
    assert denied, (proc.returncode, proc.stdout, proc.stderr)


@pytest.mark.parametrize("script", ALL)
def test_every_hook_imports_without_tomllib(script, tmp_path):
    assert (HOOKS / script).is_file(), script
    proc = run(script, "{}", tmp_path, NO_TOMLLIB)
    assert "ModuleNotFoundError" not in proc.stderr, proc.stderr
    assert "Traceback" not in proc.stderr, proc.stderr


@pytest.mark.parametrize("script,payload", DENY)
def test_deny_hooks_exit_2_on_unsupported_python(script, payload, tmp_path):
    proc = run(script, json.dumps(payload), tmp_path, OLD_PYTHON)
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    assert proc.stderr.strip() and "\n" not in proc.stderr.strip()


HOOK_PATH_FILES = [
    *sorted(HOOKS.glob("*.py")),
    *sorted((HOOKS / "lib").glob("*.py")),
    HOOKS.parent / "scripts" / "lib" / "workbench.py",
    HOOKS.parent / "scripts" / "lib" / "agent_usage.py",
]


@pytest.mark.parametrize("path", HOOK_PATH_FILES, ids=lambda p: p.name)
def test_hook_path_files_defer_annotations(path):
    # `X | None` in a def signature is evaluated at import on 3.9 unless annotations are deferred.
    text = path.read_text()
    if "def " in text:
        assert "from __future__ import annotations" in text, path


@pytest.mark.skipif(
    not Path("/usr/bin/python3").exists()
    or subprocess.run(
        ["/usr/bin/python3", "-c", "import sys;sys.exit(sys.version_info >= (3, 11))"]
    ).returncode,
    reason="no system python older than 3.11",
)
@pytest.mark.parametrize("script,payload", DENY)
def test_deny_hooks_deny_on_system_python(script, payload):
    proc = subprocess.run(
        ["/usr/bin/python3", str(HOOKS / script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    assert "Traceback" not in proc.stderr, proc.stderr
    assert proc.returncode == 2 or '"deny"' in proc.stdout, (proc.stdout, proc.stderr)
