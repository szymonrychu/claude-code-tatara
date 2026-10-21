"""`harness-setup` with no arguments syncs AGENTS.md blocks and regenerates recorded targets."""

import importlib.util
import subprocess
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "_test_setup", Path(__file__).with_name("test_setup.py")
)
_ts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ts)
clean_tree, fakes, run = _ts.clean_tree, _ts.fakes, _ts.run

SETUP = Path(__file__).resolve().parents[2] / "harness" / "setup.py"


def test_no_args_syncs_rules_block_without_targets(clean_tree):
    rules = clean_tree / "plugins/workbench/rules"
    rules.mkdir(parents=True, exist_ok=True)
    (rules / "tdd.md").write_text("---\nname: tdd\n---\n\n# Tests first\n\nRed, green.\n")
    agents = clean_tree / "AGENTS.md"
    before = agents.read_text()
    assert run(clean_tree) == 0
    after = agents.read_text()
    assert after != before
    assert "Generated from plugins/workbench/rules/" in after
    assert run(clean_tree) == 0  # idempotent
    assert agents.read_text() == after


def test_no_args_regenerates_recorded_targets(clean_tree):
    assert run(clean_tree, "cursor", "codex") == 0
    (clean_tree / ".cursor/a.txt").write_text("hand edited")
    assert run(clean_tree) == 0
    assert (clean_tree / ".cursor/a.txt").read_text() == "cursor a\n"
    assert run(clean_tree, "--check") == 0


def test_no_args_cli_exit_zero(clean_tree):
    r = subprocess.run(
        [sys.executable, str(SETUP), "--root", str(clean_tree)], capture_output=True, text=True
    )
    assert r.returncode == 0, r.stderr


def test_no_args_syncs_blocks_and_targets(clean_tree):
    rules = clean_tree / "plugins/workbench/rules"
    rules.mkdir(parents=True, exist_ok=True)
    (rules / "tdd.md").write_text("---\nname: tdd\n---\n\n# Tests first\n\nRed, green.\n")
    assert run(clean_tree, "cursor") == 0
    (clean_tree / ".cursor/a.txt").write_text("hand edited")
    agents = clean_tree / "AGENTS.md"
    assert run(clean_tree) == 0
    assert "Generated from" in agents.read_text()
    assert (clean_tree / ".cursor/a.txt").read_text() == "cursor a\n"
    snap = agents.read_text()
    assert run(clean_tree) == 0
    assert agents.read_text() == snap


def test_documented_invocations_parse(clean_tree):
    for args in (
        [],
        ["cursor"],
        ["cursor", "codex"],
        ["all"],
        ["--check"],
        ["--clean", "cursor"],
    ):
        assert run(clean_tree, *args) == 0, args
