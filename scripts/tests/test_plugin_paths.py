"""Every skill and agent script call must be location independent."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BAD_CALL = re.compile(r"\b(?:python3?|bash)\s+(?:scripts|skills)/")
SKILL_DIRS = "|".join(sorted(d.name for d in (ROOT / "plugins").glob("*/skills/*") if d.is_dir()))
SKILL_SCRIPT = re.compile(rf"(?<![\w/}}.-])(?:skills/)?(?:{SKILL_DIRS})/scripts/")
FALLBACK = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT:-")
ROOT_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"'`)]*)")


def _files():
    out = subprocess.run(
        ["git", "ls-files", "plugins"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    found = []
    for rel in out:
        parts = rel.split("/")
        is_agent = len(parts) > 3 and parts[2] == "agents" and rel.endswith(".md")
        if parts[-1] == "SKILL.md" or is_agent:
            found.append(rel)
    return found


def _scan(pattern):
    hits = []
    for rel in _files():
        for n, line in enumerate((ROOT / rel).read_text().splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{rel}:{n}: {line.strip()}")
    return hits


def test_files_found():
    assert len(_files()) > 10


def test_no_relative_script_calls():
    assert _scan(BAD_CALL) == []
    assert _scan(SKILL_SCRIPT) == []


def test_no_plugin_root_fallback():
    assert _scan(FALLBACK) == []


def test_no_parent_traversal_in_plugin_root_paths():
    bad = []
    for rel in _files():
        for n, line in enumerate((ROOT / rel).read_text().splitlines(), 1):
            for m in ROOT_PATH.finditer(line):
                if ".." in m.group(1).split("/"):
                    bad.append(f"{rel}:{n}")
    assert bad == []


def test_plugin_root_paths_exist():
    missing = []
    for rel in _files():
        plugin = ROOT / "/".join(rel.split("/")[:2])
        for n, line in enumerate((ROOT / rel).read_text().splitlines(), 1):
            for m in ROOT_PATH.finditer(line):
                target = m.group(1).rstrip(".,;:")
                if "<" in target or "$" in target:
                    continue
                if not (plugin / target).exists():
                    missing.append(f"{rel}:{n}: {target}")
    assert missing == []
