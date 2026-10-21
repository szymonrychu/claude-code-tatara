"""Pins the uninitialised template's root stub files."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUBS = [
    "MEMORY.md",
    "ROADMAP.md",
    "docs/architecture.md",
    "code/.gitkeep",
    "LICENSE",
    "plugins/workbench/LICENSE",
]


def _tracked() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return set(out.splitlines())


def test_stub_files_tracked():
    tracked = _tracked()
    for rel in STUBS:
        assert (ROOT / rel).is_file(), rel
        assert rel in tracked, rel


def test_gitmodules_is_not_tracked():
    assert ".gitmodules" not in _tracked()


def test_memory_keeps_header_and_import_entry():
    text = (ROOT / "MEMORY.md").read_text()
    assert text.startswith("# MEMORY")
    assert re.search(r"^\d{4}-\d{2}-\d{2}: plugins/workbench imported", text, re.M)


def test_roadmap_has_no_entries():
    text = (ROOT / "ROADMAP.md").read_text()
    assert text.startswith("# ROADMAP")
    assert "human-owned" in text and "never invents" in text
    assert not re.search(r"^\s*(?:[-*+]|\d+\.)\s", text, re.M)
    assert not re.search(r"^#{2,}\s", text, re.M)


def test_architecture_stub_has_components_heading():
    text = (ROOT / "docs/architecture.md").read_text()
    assert re.search(r"^#+\s+Components\s*$", text, re.M)
    assert "init fills the component map" in text


def test_license_mit_identical():
    root = (ROOT / "LICENSE").read_text()
    plugin = (ROOT / "plugins/workbench/LICENSE").read_text()
    assert root == plugin
    assert root.startswith("MIT License")
    assert "Copyright (c) 2026 " + "Szy" + "mon Rich" + "ert" in root
    assert "Permission is hereby granted, free of charge" in root
