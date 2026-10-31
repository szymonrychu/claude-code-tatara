"""bash-output-filter's wrapper must be reversible by `worktree_lib.unwrap_output_filter`."""

import importlib.util
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))
import worktree_lib as wl  # noqa: E402

spec = importlib.util.spec_from_file_location("bash_output_filter", HOOKS / "bash-output-filter.py")
bof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bof)


def test_unwrap_returns_original_command():
    original = "cd /x/.claude/worktrees/a && mise run test"
    assert wl.unwrap_output_filter(bof.build_new_cmd(original)) == original


def test_unwrap_returns_pytest_with_added_flags():
    wrapped = bof.build_new_cmd("cd /x && pytest -q")
    inner = wl.unwrap_output_filter(wrapped)
    assert inner.startswith("cd /x && pytest -q")
    assert "TMP_OUT" not in inner


def test_unwrap_multiline_command():
    original = "cd /x && mise run test\n# trailing comment"
    assert wl.unwrap_output_filter(bof.build_new_cmd(original)) == original


@pytest.mark.parametrize(
    "command",
    [
        "pytest -q",
        "cd /x && ls",
        "",
        "TMP_OUT=1; echo hi",
        bof.build_kubectl_tail_cmd("kubectl logs pod"),
    ],
)
def test_unwrap_leaves_other_commands_unchanged(command):
    assert wl.unwrap_output_filter(command) == command


def test_unwrap_any_spill_dir():
    original = "cd /x && mise run test"
    spill_dirs = (None, "/main/.logs/bash-output", "/main with space/.logs/b", "/it's/.logs")
    for spill_dir in spill_dirs:
        wrapped = wl.wrap_output_filter(original, 4000, spill_dir)
        assert wrapped != original
        assert wl.unwrap_output_filter(wrapped) == original
    assert wl.unwrap_output_filter("pytest -q") == "pytest -q"
