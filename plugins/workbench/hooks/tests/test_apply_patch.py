"""Tests for `hooks/lib/apply_patch.py`: target paths of a Codex apply_patch envelope."""

import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))

from lib.apply_patch import patch_paths  # noqa: E402


def _patch(*body: str) -> str:
    return "\n".join(["*** Begin Patch", *body, "*** End Patch"]) + "\n"


def test_add():
    assert patch_paths(_patch("*** Add File: a/new.txt", "+hello")) == ["a/new.txt"]


def test_update():
    text = _patch("*** Update File: src/x.py", "@@ def f():", "-    old", "+    new")
    assert patch_paths(text) == ["src/x.py"]


def test_delete():
    assert patch_paths(_patch("*** Delete File: gone.txt")) == ["gone.txt"]


def test_move_returns_source_and_destination():
    text = _patch("*** Update File: old.py", "*** Move to: new/place.py", "@@", "-a", "+b")
    assert patch_paths(text) == ["old.py", "new/place.py"]


def test_multi_file_order():
    text = _patch(
        "*** Add File: one.txt",
        "+1",
        "*** Update File: two.txt",
        "@@",
        "-x",
        "+y",
        "*** Update File: one.txt",
        "@@",
        "-1",
        "+2",
        "*** Delete File: three.txt",
    )
    assert patch_paths(text) == ["one.txt", "two.txt", "three.txt"]


def test_header_lookalikes_inside_hunks_are_ignored():
    text = _patch(
        "*** Update File: real.md",
        "@@",
        " context",
        "+*** Add File: fake.md",
        "-*** Delete File: fake2.md",
        " *** Update File: fake3.md",
    )
    assert patch_paths(text) == ["real.md"]


def test_add_file_body_lookalike_ignored():
    text = _patch("*** Add File: real.md", "+*** Delete File: fake.md")
    assert patch_paths(text) == ["real.md"]


def test_malformed():
    assert patch_paths("*** Update File: a.txt\n@@\n-a\n+b\n") == []
    assert patch_paths("") == []
    assert patch_paths("just text") == []


def test_heredoc_wrapped_command():
    text = "apply_patch <<'EOF'\n" + _patch("*** Add File: h.txt", "+x") + "EOF\n"
    assert patch_paths(text) == ["h.txt"]


def test_all_operations():
    text = (
        "*** Begin Patch\n"
        "*** Add File: a.txt\n+x\n"
        "*** Update File: b.txt\n@@\n-o\n+n\n"
        "*** Delete File: c.txt\n"
        "*** Update File: d.txt\n*** Move to: e.txt\n@@\n-o\n+n\n"
        "*** End Patch\n"
    )
    assert patch_paths(text) == ["a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]
