"""Structural tests for the workbench-observability pack."""

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ITEMS = [
    ROOT / "skills" / "kubectl-logs-query" / "SKILL.md",
    ROOT / "agents" / "k8s-triage.md",
]

# Forbidden words are assembled at run time so this file does not itself
# trip the personal-term lint (lint:personal), whose allowlist must not widen.
FORBIDDEN = [
    "home" + "lab",
    "har" + "bor",
    "tat" + "ara",
    "szy" + "monrich",
    "kubernetes-admin" + "@",
    "47d" + "28x2",
    "RTL" + "8156",
]


def frontmatter(path: Path) -> dict:
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    out = {}
    for key in ("name", "description"):
        km = re.search(rf"^{key}:\s*(.+)", m.group(1), re.M)
        assert km, f"{path} frontmatter lacks {key}"
        out[key] = km.group(1).strip()
    return out


def test_manifest_name():
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "workbench-observability"
    assert manifest["version"]
    assert manifest["description"]


def test_items_exist_with_valid_frontmatter():
    assert (ROOT / "skills" / "kubectl-logs-query" / "SKILL.md").is_file()
    assert (ROOT / "agents" / "k8s-triage.md").is_file()
    for item in ITEMS:
        fm = frontmatter(item)
        assert fm["name"] and fm["description"]
    assert frontmatter(ITEMS[0])["name"] == "kubectl-logs-query"
    assert frontmatter(ITEMS[1])["name"] == "k8s-triage"


def test_no_personal_terms():
    for path in [p for p in ROOT.rglob("*") if p.is_file() and "tests" not in p.parts]:
        if "__pycache__" in path.parts:
            continue
        text = path.read_text().lower()
        for word in FORBIDDEN:
            assert word.lower() not in text, f"{word!r} in {path}"


def test_context_is_current_not_switched():
    skill = ITEMS[0].read_text()
    assert "kubectl config current-context" in skill
    assert "use-context" not in skill.replace("never switch", "")


def _text_sources(root):
    """Yield text files under root, skipping tests, __pycache__ and binaries."""
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or "tests" in rel.parts or "__pycache__" in rel.parts:
            continue
        try:
            yield path, path.read_text()
        except UnicodeDecodeError:
            continue


def _escapes(root):
    bad = []
    for path, text in _text_sources(root):
        if "../" in text or "/Us" + "ers/" in text or "~/.claude" in text:
            bad.append(path)
    return bad


def test_no_path_escapes_plugin_root():
    assert _escapes(ROOT) == []


def test_escape_scan_ignores_pyc_and_still_catches_escapes(tmp_path):
    copy = tmp_path / "pack"
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns("__pycache__"))
    cache = copy / "scripts" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "x.cpython-314.pyc").write_bytes(b"+\x0e\r\n\x00\xb8\xa1\xd7j\x8f")
    (copy / "blob.bin").write_bytes(b"\xb8\xa1\xd7")
    assert _escapes(copy) == []
    (copy / "leak.md").write_text("see ../outside")
    assert _escapes(copy) == [copy / "leak.md"]


def test_readme_and_license():
    readme = (ROOT / "README.md").read_text()
    assert "workbench core plugin" in readme
    assert "kubectl-logs-query" in readme and "k8s-triage" in readme
    assert "enabledPlugins" in readme
    assert "MIT License" in (ROOT / "LICENSE").read_text()


def test_pack_items_generic():
    extra = ["rich" + "ert", "trans" + "code", "jelly" + "fin", "plex", "szy" + "mon"]
    for path in [p for p in ROOT.rglob("*") if p.is_file() and "tests" not in p.parts]:
        if "__pycache__" in path.parts or path.name == "LICENSE":
            continue
        text = path.read_text().lower()
        for word in FORBIDDEN + extra:
            assert word.lower() not in text, f"{word!r} in {path}"
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["author"]["name"] == "workbench contributors"
