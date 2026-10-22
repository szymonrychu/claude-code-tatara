"""init, component-add and component-remove skills: frontmatter, engine calls, confirmation."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[2]
ROOT = SKILLS.parents[2]
CLI = ROOT / "scripts" / "init_engine" / "cli.py"

# mise task -> engine subcommand
TASKS = {
    "init:new": ["new"],
    "init:adopt": ["adopt"],
    "component:add": ["component", "add"],
    "component:remove": ["component", "remove"],
}
NAMES = ["init", "component-add", "component-remove"]


def text(name):
    return (SKILLS / name / "SKILL.md").read_text()


def help_of(sub):
    out = subprocess.run(
        [sys.executable, str(CLI), *sub, "--help"], capture_output=True, text=True, check=True
    )
    return out.stdout


def calls(body):
    """Yield (task, flags) for every `mise run <task> -- <flags>` line."""
    for m in re.finditer(r"mise run ([\w:-]+)(?: -- ([^\n`]*))?", body):
        yield m.group(1), re.findall(r"--[a-z][a-z-]*", m.group(2) or "")


@pytest.mark.parametrize("name", NAMES)
def test_frontmatter(name):
    body = text(name)
    m = re.match(r"---\nname: (.+)\ndescription: >\n((?:  .+\n)+)---\n", body)
    assert m, "frontmatter"
    assert m.group(1) == name
    assert len(m.group(2)) > 80


@pytest.mark.parametrize("name", NAMES)
def test_engine_only_through_mise_tasks(name):
    body = text(name)
    assert "cli.py" not in body
    assert "init_engine" not in body
    assert "CLAUDE_PLUGIN_ROOT" not in body


@pytest.mark.parametrize("name", NAMES)
def test_flags_exist_in_cli_help(name):
    seen = 0
    for task, flags in calls(text(name)):
        if task not in TASKS:
            continue
        seen += 1
        helptext = help_of(TASKS[task])
        for flag in flags:
            assert flag in helptext, f"{name}: {task} uses unknown {flag}"
    assert seen


def used(name):
    return {t for t, _ in calls(text(name))}


def test_each_skill_calls_its_tasks():
    assert {"init:new", "init:adopt"} <= used("init")
    assert "harness-setup" not in used("init")
    assert "component:add" in used("component-add")
    assert "component:remove" in used("component-remove")


def test_mise_tasks_exist():
    for task in TASKS:
        assert (ROOT / "mise-tasks" / task.replace(":", "/")).is_file()
    assert (ROOT / "mise-tasks" / "harness-setup").is_file()


@pytest.mark.parametrize("name", ["init", "component-add"])
def test_forge_creation_is_confirmed_first(name):
    body = text(name)
    assert "--confirm-forge" in body
    pos = body.index("--confirm-forge")
    before = body[:pos].lower()
    assert "confirm" in before and "explicit" in before
    assert "only after" in body.lower()


def test_init_commits_harness_and_fills_placeholders_once():
    body = text("init")
    assert not re.search(r"mise run harness-setup", body)
    assert "--purpose" in body and "--risk" in body
    assert "workbench:project" in body
    assert "mise run doctor" in body
    for ask in ["new", "adopt", "license", "pack", "harness", "deploy"]:
        assert ask in body.lower()


def test_remove_explains_refusals():
    body = text("component-remove").lower()
    for word in ["uncommitted", "stash", "worktree", "not on any remote", "staged"]:
        assert word in body


FORGE = ["--confirm-forge", "--forge-owner", "--public"]


def test_skills_call_real_flags():
    """Every flag named in prose or commands exists for the subcommand it is attached to."""
    body = text("init")
    for task, flags in calls(body):
        if task in TASKS:
            helptext = help_of(TASKS[task])
            for flag in flags:
                assert flag in helptext
    adopt_help = help_of(TASKS["init:adopt"])
    for line in re.findall(r"[^\n]*init:adopt[^\n]*", body):
        for flag in re.findall(r"--[a-z][a-z-]*", line):
            assert flag in adopt_help, f"adopt line uses {flag}: {line}"
    assert not any(f in adopt_help for f in FORGE)
    assert "`init:adopt` has no forge flags" in body
    for f in FORGE:
        assert f in help_of(TASKS["init:new"])


def test_confirmation_and_harness_setup():
    body = text("init")
    assert body.index("## 2. Confirm forge creation") < body.index("## 3. Run the engine")
    assert "explicit" in body and "only after" in body.lower()
    assert "init:new" in body[body.index("## 2.") : body.index("## 3.")]
    assert not re.search(r"mise run harness-setup", body)


def flat(name):
    return " ".join(text(name).split())


def test_init_skill_states_local_bare_and_move():
    body = flat("init")
    assert "only with `--path` on a checkout that has no origin" in body
    assert "never with `--url`" in body
    assert "moves the checkout into `code/<name>`" in body
    assert "original path no longer exists" in body


def test_component_add_skill_states_move():
    body = flat("component-add")
    assert "only with `--path` on a checkout that has no origin" in body
    assert "never with `--url`" in body
    assert "moves the checkout into `code/<name>`" in body
    assert "original path no longer exists" in body
