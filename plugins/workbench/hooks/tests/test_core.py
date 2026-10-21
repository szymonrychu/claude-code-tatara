"""Tests for the harness-neutral hook core (`hooks/lib/core.py`).

The two PreToolUse guards used to hold their deny logic inside the Claude entry
scripts. That logic now lives in `decide(hook, event)` so a harness adapter can
serve it to every harness; the Claude scripts are thin wrappers. These tests
drive `decide` directly: one deny and one allow case for every guard-bash rule,
one case for every protect-files pattern, and a check that no guard ever asks.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))

import lib  # noqa: E402
from lib.core import (  # noqa: E402
    ACTIONS,
    BASENAME_PATTERNS,
    ENV_ALLOWED,
    EVENTS,
    IDLE_NOOP_REASON,
    RULES,
    TOOL_KINDS,
    Decision,
    NormalizedEvent,
    decide,
    from_claude_payload,
)


def shell(command: str, event: str = "pre-tool") -> NormalizedEvent:
    return NormalizedEvent(event=event, tool_kind="shell", command=command)


def edit(*paths: str, kind: str = "edit") -> NormalizedEvent:
    return NormalizedEvent(event="pre-tool", tool_kind=kind, paths=list(paths))


# --- guard-bash ---------------------------------------------------------
#
# (rule index into RULES, commands that rule must deny, commands it must allow).
# Every rule appears exactly once; the allow cases are near misses of that rule.
GUARD_BASH_CASES = [
    (
        0,  # terraform destroy
        ["terraform destroy", "terraform -chdir=infra destroy -auto-approve"],
        ["terraform plan -destroy -out=tfplan"],
    ),
    (
        1,  # terraform apply without a saved plan
        ["terraform apply", "terraform apply -auto-approve"],
        ["terraform apply tfplan", "terraform apply prod.plan", "terraform apply plan.out"],
    ),
    (
        2,  # terraform state surgery
        [
            "terraform state rm aws_instance.x",
            "terraform force-unlock 1234",
            "terraform workspace delete dev",
        ],
        ["terraform state list", "terraform workspace select dev"],
    ),
    (
        3,  # raw sops
        ["sops -d secrets.yaml", "sops secrets.yaml"],
        [
            "sops exec-file secrets.yaml 'sops-secret-helper {}'",
            "grep sops README.md",
            "sops-secret-helper get db",
            "sops-secret-helper",
        ],
    ),
    (
        4,  # helmfile destroy
        ["helmfile destroy", "helmfile -e prod destroy"],
        ["helmfile diff", "helmfile -e prod apply"],
    ),
    (
        5,  # helm uninstall
        ["helm uninstall release"],
        ["helm list", "helm template ./chart"],
    ),
    (
        6,  # bulk / cluster-scoped kubectl delete
        [
            "kubectl delete pods --all",
            "kubectl delete ns prod",
            "kubectl delete namespace prod",
            "kubectl delete pv data-0",
            "kubectl delete persistentvolume data-0",
            "kubectl delete crd widgets.example.com",
            "kubectl delete customresourcedefinition widgets.example.com",
        ],
        ["kubectl delete pod my-pod", "kubectl get ns"],
    ),
    (
        7,  # force push without lease
        ["git push --force", "git push -f origin main", "git push origin main --force"],
        ["git push --force-with-lease", "git push origin main"],
    ),
    (
        8,  # destructive stash operations
        ["git stash pop", "git stash drop", "git stash clear"],
        ["git stash list", "git stash apply stash@{0}", "git stash push -m wip"],
    ),
    (
        9,  # discarding uncommitted work
        [
            "git reset --hard origin/main",
            "git clean -fd",
            "git clean -xfd",
            "git checkout -- src/main.py",
            "git checkout HEAD -- src/main.py",
            "git restore src/main.py",
        ],
        ["git reset --soft HEAD~1", "git clean -n", "git checkout main", "git switch main"],
    ),
    (
        10,  # rm on a root-ish path
        ["rm -rf /", "rm -rf ~", "rm -rf ~/", "rm -r /"],
        ["rm -rf ./build", "rm -rf build/tmp", "rm -f stale.lock"],
    ),
]


def test_guard_bash_rules():
    covered = sorted(index for index, _, _ in GUARD_BASH_CASES)
    assert covered == list(range(len(RULES))), "every guard-bash rule needs a case"
    for index, denied, allowed in GUARD_BASH_CASES:
        reason_text = RULES[index][1]
        for cmd in denied:
            decision = decide("guard-bash", shell(cmd))
            assert decision.action == "deny", f"rule {index} failed to deny: {cmd}"
            assert decision.reason == f"guard-bash: `{cmd}` - {reason_text}", cmd
        for cmd in allowed:
            decision = decide("guard-bash", shell(cmd))
            assert decision == Decision("allow"), f"rule {index} wrongly denied: {cmd}"


def test_guard_bash_idle_noop_rule():
    for cmd in ["true", ":", "sleep 1", "echo waiting", "sleep 5 && true"]:
        decision = decide("guard-bash", shell(cmd))
        assert decision.action == "deny", cmd
        assert decision.reason == f"guard-bash: `{cmd}` - {IDLE_NOOP_REASON}"
    for cmd in [
        "until curl -sf http://localhost/health; do sleep 2; done",
        "sleep 5 && pytest",
        "echo waiting > /tmp/status.log",
        "mise run test || true",
    ]:
        assert decide("guard-bash", shell(cmd)) == Decision("allow"), cmd


def test_guard_bash_compound_and_prefixes():
    first = decide("guard-bash", shell("mise run test && git restore ."))
    assert first.action == "deny"
    assert first.reason.startswith("guard-bash: `git restore .` - ")
    for prefix in ("sudo ", "env FOO=1 ", "nohup ", "FOO=1 ", "command ", "time "):
        decision = decide("guard-bash", shell(prefix + "terraform destroy"))
        assert decision.action == "deny", prefix
        assert decision.reason.startswith("guard-bash: `terraform destroy` - "), prefix
    assert decide("guard-bash", shell("echo hi && git status")) == Decision("allow")


BYPASS_FORMS = [
    "git -C /repo reset --hard",
    "git -c core.editor=vi push --force",
    "git --git-dir=.git --work-tree=. clean -fd",
    "git -C /repo -c a=b stash pop",
    "terraform -chdir=infra destroy",
    "terraform -chdir=infra apply",
    'bash -c "terraform destroy"',
    "sh -c 'git reset --hard'",
    "zsh -c 'echo hi && terraform destroy'",
    "bash -lc 'helm uninstall x'",
    'eval "git restore ."',
    "eval git restore .",
    "echo $(terraform destroy)",
    "echo `git reset --hard`",
    "echo \"$(sh -c 'terraform destroy')\"",
]


def test_guard_bash_bypass_forms_denied():
    for cmd in BYPASS_FORMS:
        assert decide("guard-bash", shell(cmd)).action == "deny", cmd


def test_guard_bash_bypass_forms_near_misses_allowed():
    for cmd in [
        "git -C /repo status",
        "git -c a=b push --force-with-lease",
        "terraform -chdir=infra plan",
        "terraform -chdir=infra apply tfplan",
        'bash -c "echo hi"',
        "echo $(git rev-parse HEAD)",
        'eval "echo hi"',
    ]:
        assert decide("guard-bash", shell(cmd)) == Decision("allow"), cmd


def test_guard_bash_benign_forms_allowed():
    for cmd in [
        "grep terraform README.md",
        "git -C x status",
        'echo "destroy"',
        "echo terraform destroy",
    ]:
        assert decide("guard-bash", shell(cmd)) == Decision("allow"), cmd


def test_guard_bash_ignores_non_shell_and_non_pre_tool_events():
    assert decide("guard-bash", shell("")) == Decision("allow")
    assert decide("guard-bash", shell("terraform destroy", event="post-tool")) == Decision("allow")
    other = NormalizedEvent(event="pre-tool", tool_kind="other", command="terraform destroy")
    assert decide("guard-bash", other) == Decision("allow")


# --- protect-files ------------------------------------------------------
#
# (path, expected deny reason fragment). One entry per BASENAME_PATTERNS glob,
# plus the .git and .env rules that are not globs.
PROTECTED_BY_PATTERN = {
    "*.tfstate": "/repo/terraform/terraform.tfstate",
    "*.tfstate.*": "/repo/terraform/terraform.tfstate.backup",
    "id_rsa": "/opt/u/.ssh/id_rsa",
    "id_ed25519": "/opt/u/.ssh/id_ed25519",
    "*.pem": "/repo/certs/server.pem",
    "*.key": "/repo/certs/tls.key",
    "*.enc.*": "/repo/charts/app/values.enc.yaml",
    "*.secret.*": "/repo/charts/app/db.secret.yaml",
    "secrets.*.yaml": "/repo/secrets.prod.yaml",
    "secrets.*.yml": "/repo/secrets.dev.yml",
    "default.secrets.yaml": "/repo/charts/app/default.secrets.yaml",
}

PROTECTED_OTHER = {
    "/repo/.git/config": "editing .git internals",
    ".git/hooks/pre-commit": "editing .git internals",
    "C:\\repo\\.git\\config": "editing .git internals",
    "/repo/.env": "editing an .env secrets file",
    "/repo/app/.env.local": "editing an .env secrets file",
    ".env.production": "editing an .env secrets file",
}

NOT_PROTECTED = [
    "/repo/" + ENV_ALLOWED,
    "/repo/src/main.py",
    "/repo/.gitignore",
    "/repo/.github/workflows/ci.yml",
    "/repo/docs/environment.md",
    "/repo/charts/app/values.yaml",
    "/repo/secrets.py",
    "/repo/keyboard.keymap",
    "/repo/my.git/config",
]


def _expected_reason(what: str, path: str) -> str:
    return (
        f"BLOCKED by protect-files hook: {what} ({path}). Use the proper "
        "tool: the project's secret helper for secrets (the workbench-secrets "
        "pack's sops-secret-helper skill when enabled), git for .git, "
        "terraform state commands for tfstate."
    )


def test_protect_files_patterns():
    assert set(PROTECTED_BY_PATTERN) == {pattern for pattern, _ in BASENAME_PATTERNS}
    for pattern, what in BASENAME_PATTERNS:
        path = PROTECTED_BY_PATTERN[pattern]
        for kind in ("edit", "write"):
            decision = decide("protect-files", edit(path, kind=kind))
            assert decision == Decision("deny", _expected_reason(f"editing {what}", path)), (
                pattern,
                kind,
            )
    for path, what in PROTECTED_OTHER.items():
        decision = decide("protect-files", edit(path))
        assert decision == Decision("deny", _expected_reason(what, path)), path
    for path in NOT_PROTECTED:
        assert decide("protect-files", edit(path)) == Decision("allow"), path


def test_protect_files_checks_every_path():
    decision = decide("protect-files", edit("/repo/src/main.py", "/repo/.env", "/repo/a.pem"))
    assert decision == Decision(
        "deny", _expected_reason("editing an .env secrets file", "/repo/.env")
    )
    assert decide("protect-files", edit("/repo/a.py", "/repo/b.py")) == Decision("allow")
    assert decide("protect-files", edit()) == Decision("allow")
    assert decide("protect-files", edit("")) == Decision("allow")


def test_protect_files_ignores_reads_shell_and_post_tool():
    assert decide("protect-files", edit("/repo/.env", kind="read")) == Decision("allow")
    assert decide("protect-files", edit("/repo/.env", kind="shell")) == Decision("allow")
    post = NormalizedEvent(event="post-tool", tool_kind="edit", paths=["/repo/.env"])
    assert decide("protect-files", post) == Decision("allow")


# --- the contract -------------------------------------------------------


def test_never_ask():
    assert "ask" not in ACTIONS
    with pytest.raises(ValueError):
        Decision("ask", "should I?")
    events = [shell(cmd) for _, denied, allowed in GUARD_BASH_CASES for cmd in denied + allowed]
    events += [edit(p) for p in [*PROTECTED_BY_PATTERN.values(), *PROTECTED_OTHER, *NOT_PROTECTED]]
    for hook in ("guard-bash", "protect-files"):
        for event in events:
            assert decide(hook, event).action in {"allow", "deny"}


def test_contract_values_and_validation():
    assert EVENTS == ("pre-tool", "post-tool", "stop")
    assert TOOL_KINDS == ("shell", "edit", "write", "read", "other")
    assert ACTIONS == ("allow", "deny", "block")
    event = NormalizedEvent(event="stop", tool_kind="other")
    assert (event.command, event.paths, event.cwd, event.raw) == ("", [], "", {})
    assert Decision("allow").reason == ""
    with pytest.raises(ValueError):
        NormalizedEvent(event="session-start", tool_kind="shell")
    with pytest.raises(ValueError):
        NormalizedEvent(event="pre-tool", tool_kind="network")
    with pytest.raises(ValueError):
        decide("no-such-hook", shell("ls"))


def test_from_claude_payload():
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
        "cwd": "/repo",
    }
    event = from_claude_payload(payload, "pre-tool")
    assert event == NormalizedEvent(
        event="pre-tool", tool_kind="shell", command="ls", cwd="/repo", raw=payload
    )
    write = from_claude_payload(
        {"tool_name": "Write", "tool_input": {"file_path": "/repo/.env"}}, "pre-tool"
    )
    assert (write.tool_kind, write.paths) == ("write", ["/repo/.env"])
    assert from_claude_payload({"tool_name": "Edit", "tool_input": {}}, "pre-tool").paths == []
    assert from_claude_payload({"tool_name": "Read"}, "pre-tool").tool_kind == "read"
    assert from_claude_payload({"tool_name": "WebFetch"}, "pre-tool").tool_kind == "other"
    # Claude payloads without a tool name take the kind the matcher guarantees.
    bare = from_claude_payload({"tool_input": {"command": "ls"}}, "pre-tool", default_kind="shell")
    assert (bare.tool_kind, bare.command) == ("shell", "ls")
    for junk in ([], "x", None, {"tool_input": "x"}, {"tool_input": {"command": 3}}):
        event = from_claude_payload(junk, "pre-tool", default_kind="shell")
        assert (event.command, event.paths) == ("", [])


def test_lib_resolves_to_the_hooks_package():
    """No other module named `lib` may shadow the hooks package in this process."""
    assert Path(lib.__file__).resolve() == HOOKS / "lib" / "__init__.py"


@pytest.mark.parametrize(
    "script,stdin",
    [
        ("guard-bash.py", {"tool_input": {"command": "git stash pop"}}),
        ("protect_files.py", {"tool_input": {"file_path": "/repo/.env"}}),
    ],
)
def test_wrappers_render_the_core_decision(script, stdin):
    proc = subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=json.dumps(stdin),
        capture_output=True,
        text=True,
    )
    if script == "guard-bash.py":
        decision = decide("guard-bash", from_claude_payload(stdin, "pre-tool", "shell"))
        assert proc.returncode == 0
        assert json.loads(proc.stdout) == {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": decision.reason,
            }
        }
    else:
        decision = decide("protect-files", from_claude_payload(stdin, "pre-tool", "edit"))
        assert proc.returncode == 2
        assert proc.stdout == ""
        assert proc.stderr == decision.reason + "\n"
