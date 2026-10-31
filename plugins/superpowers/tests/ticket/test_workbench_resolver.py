"""ticket.py finds the workbench plugin from a source tree and from a plugin cache (D6)."""

import shutil
import subprocess
import sys
from pathlib import Path

PLUGINS = Path(__file__).resolve().parents[3]
SUPERPOWERS = PLUGINS / "superpowers"
WORKBENCH = PLUGINS / "workbench"
SCRIPT = SUPERPOWERS / "scripts" / "ticket.py"
IGNORE = shutil.ignore_patterns("__pycache__", ".venv", "tests")
CALL_RESOLVER = (
    "import importlib.util, sys\n"
    "spec = importlib.util.spec_from_file_location('ticket', sys.argv[1])\n"
    "mod = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(mod)\n"
    "print(mod.workbench_plugin_root())\n"
)


def cached_superpowers(cache: Path) -> Path:
    """Copy the superpowers plugin to <cache>/mkt/superpowers/1.0.0 and return its ticket.py."""
    dest = cache / "mkt" / "superpowers" / "1.0.0"
    shutil.copytree(SUPERPOWERS, dest, ignore=IGNORE)
    return dest / "scripts" / "ticket.py"


def test_source_tree_slug():
    r = subprocess.run([sys.executable, str(SCRIPT), "slug", "A b"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "a-b"


def test_cache_resolves_highest_workbench_version(tmp_path):
    cache = tmp_path / "cache"
    ticket = cached_superpowers(cache)
    for version in ("3.0.0", "4.0.0"):
        shutil.copytree(WORKBENCH, cache / "mkt" / "workbench" / version, ignore=IGNORE)
    r = subprocess.run(
        [sys.executable, "-c", CALL_RESOLVER, str(ticket)], capture_output=True, text=True
    )
    assert r.returncode == 0, r.stderr
    assert Path(r.stdout.strip()) == (cache / "mkt" / "workbench" / "4.0.0").resolve()


def test_no_workbench_sibling_is_a_named_error(tmp_path):
    ticket = cached_superpowers(tmp_path / "cache")
    r = subprocess.run([sys.executable, str(ticket), "slug", "A b"], capture_output=True, text=True)
    assert r.returncode != 0
    assert "ticket.py: workbench plugin not found" in r.stderr
