"""Tests for the workbench-infra pack: manifest, agents, no personal terms, no path escapes."""

import json
import re
import shutil
from pathlib import Path

PACK = Path(__file__).resolve().parent.parent
AGENTS = ["tf-planner", "helmfile-differ"]

# Forbidden words are built at run time so this file does not trip the personal lint.
FORBIDDEN = [
    "home" + "lab",
    "har" + "bor",
    "tat" + "ara",
    "key" + "cloak",
    "spell" + "slinger",
    "szy" + "mon",
    "/Us" + "ers/",
    "op_" + "env",
    "192." + "168.",
    "mik" + "rotik",
    "$HOME/" + ".claude",
    "~/Docu" + "ments",
]


def _frontmatter(text: str) -> dict:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, "missing frontmatter"
    out = {}
    for line in m.group(1).splitlines():
        if re.match(r"^[a-z]+:", line):
            k, _, v = line.partition(":")
            out[k] = v.strip()
    return out


def _is_text(p: Path) -> bool:
    try:
        p.read_text()
    except UnicodeDecodeError:
        return False
    return True


def _files(root: Path = PACK):
    """Text sources only: skips tests, __pycache__ and binary files."""
    return [
        p
        for p in sorted(root.rglob("*"))
        if p.is_file()
        and "tests" not in p.relative_to(root).parts
        and "__pycache__" not in p.relative_to(root).parts
        and _is_text(p)
    ]


def test_manifest_name():
    data = json.loads((PACK / ".claude-plugin" / "plugin.json").read_text())
    assert data["name"] == "workbench-infra"
    assert "core plugin" in data["description"]


def test_agents_exist_with_frontmatter():
    for name in AGENTS:
        fm = _frontmatter((PACK / "agents" / f"{name}.md").read_text())
        assert fm["name"] == name
        assert fm["description"] in (">", "|") or fm["description"]
        assert fm["tools"].startswith("[")
        assert fm["model"]


def test_no_personal_or_homelab_terms():
    for p in _files():
        if p.name == "LICENSE":  # holder line is allowlisted
            continue
        text = p.read_text().lower()
        for word in FORBIDDEN:
            assert word.lower() not in text, f"{word!r} in {p.relative_to(PACK)}"


def _escapes(root: Path) -> list:
    bad = []
    for p in _files(root):
        text = p.read_text()
        if "${CLAUDE_PLUGIN_ROOT}/.." in text or "$CLAUDE_PLUGIN_ROOT/.." in text:
            bad.append(p)
        elif "CLAUDE_PLUGIN_ROOT" in text and p.suffix == ".md" and "agents" in p.parts:
            bad.append(p)
    return bad


def test_no_path_escapes_plugin_root():
    assert _escapes(PACK) == []
    manifest = (PACK / ".claude-plugin" / "plugin.json").read_text()
    assert "../" not in manifest


def test_escape_scan_ignores_pyc_and_still_catches_escapes(tmp_path):
    copy = tmp_path / "pack"
    shutil.copytree(PACK, copy, ignore=shutil.ignore_patterns("__pycache__"))
    cache = copy / "scripts" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "x.cpython-314.pyc").write_bytes(b"+\x0e\r\n\x00\xb8\xa1\xd7j\x8f")
    (copy / "blob.bin").write_bytes(b"\xb8\xa1\xd7")
    assert _escapes(copy) == []
    (copy / "leak.md").write_text("run ${CLAUDE_PLUGIN_ROOT}/../x")
    assert _escapes(copy) == [copy / "leak.md"]


def test_agents_use_core_locator_from_workbench_root():
    for name in AGENTS:
        text = (PACK / "agents" / f"{name}.md").read_text()
        assert "--show-superproject-working-tree" in text
        assert "plugins/workbench/scripts/lib/workbench.py" in text


def test_license_and_readme():
    root_lic = PACK.parent.parent / "LICENSE"
    lic = (PACK / "LICENSE").read_text()
    assert "MIT License" in lic
    if root_lic.exists():
        assert lic == root_lic.read_text()
    readme = (PACK / "README.md").read_text()
    assert "requires the workbench core plugin" in readme.lower()
    assert "enabledPlugins" in readme
    assert "workbench-infra@" in readme


def test_agents_generic():
    for name in AGENTS:
        text = (PACK / "agents" / f"{name}.md").read_text()
        assert "secrets-env" in text
        assert "iscover" in text
        assert "CLAUDE_PLUGIN_ROOT" not in text
        assert "../" not in text
        assert "stage list" not in text.lower() or "discover" in text.lower()
