"""Pins the em dash lint on fixture trees in temp git repos.

The banned character is never written literally here: EM is the escape.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_em_dash.py"
TASK = ROOT / "mise-tasks" / "lint" / "em-dash"
EM = "\u2014"


def _repo(tmp_path: Path, files: dict[str, str | bytes], *, untracked=()) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for name, body in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body if isinstance(body, bytes) else body.encode())
        if name not in untracked:
            subprocess.run(["git", "-C", str(tmp_path), "add", name], check=True)
    return tmp_path


def _run(root: Path):
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True
    )
    return r.returncode, r.stdout.splitlines()


def test_reports_tracked_em_dash(tmp_path):
    clean = _repo(tmp_path / "clean", {"a.md": "plain - hyphen only\n"})
    assert _run(clean) == (0, [])
    dirty = _repo(tmp_path / "dirty", {"a.md": "ok\n", "b.py": f"x = 1\n# a {EM} b\n"})
    assert _run(dirty) == (1, ["b.py:2: em dash"])


def test_ignores_untracked_and_binary(tmp_path):
    root = _repo(
        tmp_path,
        {
            "tracked.md": "fine\n",
            "loose.md": f"untracked {EM}\n",
            "blob.bin": b"\0binary" + EM.encode(),
        },
        untracked=("loose.md",),
    )
    assert _run(root) == (0, [])


def test_no_path_is_exempt(tmp_path):
    root = _repo(
        tmp_path,
        {
            "docs/plans/in-progress/x/design.md": f"a {EM} b\n",
            "scripts/init_engine/engine.py": f"# {EM}\n",
        },
    )
    code, out = _run(root)
    assert code == 1
    assert out == [
        "docs/plans/in-progress/x/design.md:1: em dash",
        "scripts/init_engine/engine.py:1: em dash",
    ]


def test_lint_task_runs_checker():
    assert TASK.is_file()
    assert os.access(TASK, os.X_OK)
    body = TASK.read_text()
    assert "#MISE description=" in body
    assert "scripts/check_em_dash.py" in body
    proc = subprocess.run([str(TASK)], cwd="/", capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
