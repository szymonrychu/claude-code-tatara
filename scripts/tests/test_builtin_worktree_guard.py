"""No workbench file uses or instructs the harness built-in worktree feature (U1, D1)."""

import json
import re
import subprocess
from pathlib import Path

from harness.emit import registry
from harness.sources import load_sources

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [
    "plugins/workbench/skills",
    "plugins/workbench/agents",
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
    is_test = bool(TEST_FILE.search(rel))
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        for pat in PATTERNS:
            if not re.search(pat, line) or line_ok(line):
                continue
            if is_test and any(
                ABSENCE_ASSERT.search(prev) and re.search(pat, prev)
                for prev in lines[max(0, n - 4) : n]
            ):
                continue
            yield f"{rel}:{n}: {pat}: {line.strip()}"


def tracked():
    out = subprocess.run(
        ["git", "ls-files", *SCAN_DIRS], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.split("\n")
    return [p for p in out if p and (ROOT / p).is_file()]


def test_matcher_flags_use_and_passes_guards():
    assert list(hits("x.md", 'isolation: "worktree"'))
    assert list(hits("x.md", "Use EnterWorktree to enter the tree"))
    assert not list(hits("x.md", "Do not call the built-in EnterWorktree"))
    # absence exemption is per pattern: asserting one pattern absent does not cover another
    t = 'assert "EnterWorktree with path" not in text\nuse ExitWorktree here'
    assert len(list(hits("a/tests/test_x.py", t))) == 1


def test_no_builtin_worktree_instructions():
    bad = []
    for rel in tracked():
        try:
            text = (ROOT / rel).read_text()
        except UnicodeDecodeError:
            continue
        bad += hits(rel, text)
    for target in sorted(registry()):
        out = registry()[target].render(load_sources(ROOT))
        for rel, text in out.items():
            bad += hits(f"[{target}] {rel}", text)
    assert not bad, "built-in worktree feature referenced:\n" + "\n".join(bad)


def test_manifest_and_agents_declare_no_builtin_worktree():
    data = json.loads((ROOT / "plugins/workbench/.claude-plugin/plugin.json").read_text())
    assert not re.search(r"Worktree(Create|Remove)", json.dumps(data.get("hooks", {})))
    hooks_json = ROOT / "plugins/workbench/hooks/hooks.json"
    if hooks_json.exists():
        assert not re.search(r"Worktree(Create|Remove)", hooks_json.read_text())
    for f in (ROOT / "plugins/workbench/agents").glob("*.md"):
        m = re.match(r"---\n(.*?)\n---", f.read_text(), re.S)
        front = m.group(1) if m else ""
        assert not re.search(r"^isolation\s*:", front, re.M), f.name
