"""No workbench file uses or instructs the harness built-in worktree feature (U1, D1)."""

import json
import re
import subprocess
from pathlib import Path

import pytest
from harness.emit import registry
from harness.sources import load_sources

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [
    "plugins/workbench/skills",
    "plugins/workbench/agents",
    "plugins/workbench/workflows",
    "plugins/workbench/hooks",
    "plugins/workbench/rules",
    "scripts/harness",
]
PATTERNS = [
    r"""isolation: "worktree\"""",
    r"""isolation: 'worktree'""",
    r"isolation: worktree",
    r"EnterWorktree",
    r"ExitWorktree",
    r"claude --worktree",
    r"claude -w ",
    r"WorktreeCreate",
    r"WorktreeRemove",
]
NEGATION = re.compile(r"\b(never|not|no|nor|without|forbid\w*|NOT)\b|n't", re.IGNORECASE)
ABSENCE_ASSERT = re.compile(r"\bnot in\b|doesNotMatch|doesNotInclude|assert_not")
TEST_FILE = re.compile(r"(^|/)(tests?/|test_[^/]*$)|\.test\.(mjs|js)$")


def line_ok(line: str) -> bool:
    return bool(NEGATION.search(line))


def hits(rel: str, text: str):
    is_test = bool(TEST_FILE.search(rel)) and bool(ABSENCE_ASSERT.search(text))
    for n, line in enumerate(text.splitlines(), 1):
        for pat in PATTERNS:
            if re.search(pat, line) and not line_ok(line) and not is_test:
                yield f"{rel}:{n}: {pat}: {line.strip()}"


def tracked():
    out = subprocess.run(
        ["git", "ls-files", *SCAN_DIRS], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.split("\n")
    return [p for p in out if p and (ROOT / p).is_file()]


def test_matcher_self_test():
    assert list(hits("x.md", 'isolation: "worktree"'))
    assert list(hits("x.md", "Use EnterWorktree to enter the tree"))
    assert not list(hits("x.md", "Do not call the built-in EnterWorktree"))


def test_tracked_files_do_not_use_builtin_worktrees():
    bad = []
    for rel in tracked():
        try:
            text = (ROOT / rel).read_text()
        except UnicodeDecodeError:
            continue
        bad += hits(rel, text)
    assert not bad, "built-in worktree feature referenced:\n" + "\n".join(bad)


@pytest.mark.parametrize("target", sorted(registry()))
def test_emitted_files_do_not_use_builtin_worktrees(target):
    out = registry()[target].render(load_sources(ROOT))
    bad = [h for rel, text in out.items() for h in hits(rel, text)]
    assert not bad, "built-in worktree feature emitted:\n" + "\n".join(bad)


def test_plugin_json_declares_no_worktree_hooks():
    data = json.loads((ROOT / "plugins/workbench/.claude-plugin/plugin.json").read_text())
    assert not re.search(r"Worktree(Create|Remove)", json.dumps(data.get("hooks", {})))
    hooks_json = ROOT / "plugins/workbench/hooks/hooks.json"
    if hooks_json.exists():
        assert not re.search(r"Worktree(Create|Remove)", hooks_json.read_text())


def test_agents_declare_no_isolation():
    for f in (ROOT / "plugins/workbench/agents").glob("*.md"):
        text = f.read_text()
        m = re.match(r"---\n(.*?)\n---", text, re.S)
        front = m.group(1) if m else ""
        assert not re.search(r"^isolation\s*:", front, re.M), f.name
