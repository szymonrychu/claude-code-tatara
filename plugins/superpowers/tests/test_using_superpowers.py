"""Pins using-superpowers and its SessionStart hook: a fresh session routes to this flow."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_checks import PLUGIN, SKILLS, flat, problems, skill_files  # noqa: E402

NAME = "using-superpowers"
HOOKS = PLUGIN / "hooks"
REFERENCES = {
    "claude-code-tools.md",
    "codex-tools.md",
    "gemini-tools.md",
    "antigravity-tools.md",
}
HOOK_COMMAND = 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/session-start"'


def text() -> str:
    return flat((SKILLS / NAME / "SKILL.md").read_text())


def test_structure():
    assert problems(NAME) == []


def test_brainstorming_is_the_entry_for_non_trivial_work():
    t = text()
    assert "Non-trivial work" in t
    assert "starts with superpowers:brainstorming" in t
    assert "one gate" in t
    assert "scope ladder" in t
    assert "two fix rounds" in t


def test_user_instructions_take_precedence():
    assert "User instructions" in text()
    assert "take precedence over skills" in text()


def test_only_the_four_harness_references_ship():
    refs = {p.name for p in (SKILLS / NAME / "references").iterdir()}
    assert refs == REFERENCES
    for ref in REFERENCES:
        assert f"`references/{ref}`" in text(), ref


def test_no_dropped_harness_or_windows_wrapper():
    files = [*skill_files(NAME), *HOOKS.iterdir()]
    for path in files:
        body = path.read_text()
        low = body.lower()
        assert "hermes" not in low, path.name
        assert "muse" not in low, path.name
        assert "pi-tools" not in low, path.name
        assert not re.search(r"\bPi\b", body), path.name
        assert "run-hook.cmd" not in body, path.name
    assert not (HOOKS / "run-hook.cmd").exists()


def test_hooks_json_runs_session_start_on_startup_clear_compact():
    hooks = json.loads((HOOKS / "hooks.json").read_text())["hooks"]
    assert list(hooks) == ["SessionStart"]
    (entry,) = hooks["SessionStart"]
    assert entry["matcher"] == "startup|clear|compact"
    (hook,) = entry["hooks"]
    assert hook["type"] == "command"
    assert hook["command"] == HOOK_COMMAND


def test_session_start_injects_the_skill_text(tmp_path):
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN)}
    done = subprocess.run(
        ["bash", str(HOOKS / "session-start")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr
    out = json.loads(done.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    context = out["hookSpecificOutput"]["additionalContext"]
    assert (SKILLS / NAME / "SKILL.md").read_text().strip() in context
