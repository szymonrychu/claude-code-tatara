"""Harness-neutral hook core.

Every harness (Claude Code, Copilot, Cursor, Codex, Gemini CLI, Antigravity)
delivers a different hook payload. The entry points normalize that payload into
a `NormalizedEvent`, call `decide(hook, event)`, and render the returned
`Decision` in their harness's own output shape. The guard logic lives here
once, so every harness gets the same rules.

Guards deny, they never ask: `ask` is unsupported or unenforced in several
harnesses, so `Decision` refuses it.

Stdlib only, and runnable by the system python 3 (3.9+) that hook processes get.
"""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .apply_patch import PATCH_KEYS, patch_added_lines

EVENTS = ("pre-tool", "post-tool")
TOOL_KINDS = ("shell", "edit", "write", "read", "other")
ACTIONS = ("allow", "deny")


@dataclass
class NormalizedEvent:
    """One hook invocation, independent of the harness that sent it."""

    event: str
    tool_kind: str
    command: str = ""
    paths: list[str] = field(default_factory=list)
    cwd: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.event not in EVENTS:
            raise ValueError(f"unknown event {self.event!r}; expected one of {EVENTS}")
        if self.tool_kind not in TOOL_KINDS:
            raise ValueError(f"unknown tool_kind {self.tool_kind!r}; expected one of {TOOL_KINDS}")


@dataclass(frozen=True)
class Decision:
    """What the harness should do: `allow` or `deny` a tool call."""

    action: str
    reason: str = ""

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise ValueError(f"unknown action {self.action!r}; expected one of {ACTIONS}")


ALLOW = Decision("allow")


# --- Claude Code payloads -------------------------------------------------

CLAUDE_TOOL_KINDS = {
    "Bash": "shell",
    "Edit": "edit",
    "MultiEdit": "edit",
    "NotebookEdit": "edit",
    "Write": "write",
    "Read": "read",
}


def from_claude_payload(payload: Any, event: str, default_kind: str = "other") -> NormalizedEvent:
    """Normalize a Claude Code hook payload.

    `default_kind` is used when the payload carries no `tool_name` (the hook's
    matcher already guarantees the tool). Anything malformed yields an event
    with no command and no paths, which every guard allows.
    """
    data = payload if isinstance(payload, dict) else {}
    tool_name = data.get("tool_name")
    if isinstance(tool_name, str) and tool_name:
        tool_kind = CLAUDE_TOOL_KINDS.get(tool_name, "other")
    else:
        tool_kind = default_kind
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = tool_input.get("command")
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    cwd = data.get("cwd")
    return NormalizedEvent(
        event=event,
        tool_kind=tool_kind,
        command=command if isinstance(command, str) else "",
        paths=[path] if isinstance(path, str) and path else [],
        cwd=cwd if isinstance(cwd, str) else "",
        raw=data,
    )


# --- guard-bash -------------------------------------------------------------
#
# Destructive or policy-violating shell commands. Unlike a settings.json `deny`
# entry, this inspects each segment of a compound command, so
# `foo && terraform destroy` is caught the same as a bare `terraform destroy`.
# Policy sources: the plugin's own rules/terraform.md and rules/sops.md.

# Split a compound command into the individual commands it will run.
# Deliberately naive about quoting edge cases: over-splitting only means we
# inspect more segments than strictly necessary, which is the safe direction.
SEPARATORS = re.compile(r"(?:\|\||&&|;|\||\n)")

# (pattern, reason). Patterns are matched against each stripped segment.
RULES = [
    # --- terraform ------------------------------------------------------
    (
        r"^terraform\s+(.*\s)?destroy\b",
        "terraform destroy is never run from an agent session. Target the "
        "specific resource with `terraform state rm` review + a plan, or run "
        "it yourself.",
    ),
    (
        r"^terraform\s+apply\b(?![^#]*\b(?:tfplan|\.plan|plan\.out)\b)",
        "terraform apply requires a saved plan file (rules/terraform.md: "
        "always plan before apply). Run `terraform plan -out=tfplan`, show me "
        "the diff, then `terraform apply tfplan`.",
    ),
    (
        r"^terraform\s+(state\s+rm|force-unlock|workspace\s+delete)\b",
        "terraform state surgery is destructive and unversioned. Show me the "
        "command and let me run it.",
    ),
    # --- sops -----------------------------------------------------------
    (
        r"^sops(?=\s|$)(?!.*sops-secret-helper)",
        "Raw sops is blocked (rules/sops.md): decrypting to stdout leaks "
        "secrets into the transcript. Use the project's secret helper (the "
        "workbench-secrets pack's sops-secret-helper skill when enabled).",
    ),
    # --- helm / helmfile ------------------------------------------------
    (
        r"^helmfile\s+(.*\s)?destroy\b",
        "helmfile destroy tears down live releases. Use `helmfile diff`; "
        "destroy is a manual operation.",
    ),
    (r"^helm\s+uninstall\b", "helm uninstall removes a live release. Run it yourself."),
    # --- kubernetes -----------------------------------------------------
    (
        r"^kubectl\s+delete\b.*(--all\b|\bns\b|\bnamespace\b|\bpv\b|"
        r"\bpersistentvolume|\bcrd\b|\bcustomresourcedefinition)",
        "Bulk / cluster-scoped kubectl delete is blocked. Delete a single "
        "named namespaced resource, or run this one yourself.",
    ),
    # --- git ------------------------------------------------------------
    (
        r"^git\s+push\b.*(--force(?!-with-lease)\b|\s-f\b)",
        "Force push without --force-with-lease is blocked. Use "
        "`git push --force-with-lease` if you really need to rewrite.",
    ),
    (
        r"^git\s+stash\s+(pop|drop|clear)\b",
        "The stash stack is shared state, and a nested or sibling agent in the "
        "same checkout can be holding an entry you did not create. Popping the "
        "top of a stack you do not own silently destroys someone else's work. "
        "Run `git stash list`, identify the entry, then `git stash apply "
        "stash@{n}` (non-destructive) and drop it explicitly once verified.",
    ),
    (
        r"^git\s+(reset\s+--hard|clean\s+-[a-z]*f[a-z]*d|"
        r"checkout\b[^|;&]*\s--\s|restore\b)",
        "This discards uncommitted work irreversibly, and a file-scoped restore "
        "is exactly as destructive as a whole-tree one - it has already cost an "
        "uncommitted fix in this workbench. If you meant to undo your own edit, "
        "check `git status` and `git diff` first, then name what you are "
        "discarding. If you meant to switch branches, use `git checkout <branch>` "
        "or `git switch` without the `--` separator.",
    ),
    # --- filesystem -----------------------------------------------------
    (
        r"^(sudo\s+)?rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?.*(/|~)\s*$",
        "rm -rf on a root-ish path is blocked.",
    ),
]

COMPILED = [(re.compile(p), r) for p, r in RULES]

# --- idle no-op / polling loops ------------------------------------------
#
# A peer-session token review found 2,108 Bash calls in one session that were
# bare `true` / `echo waiting` / `sleep 1` used to poll or wait out a
# background task - 504M cache-read tokens burned re-sending an unchanged
# context on every one of those turns. A command whose every top-level
# segment is one of these is not doing work; it is holding the turn open.
IDLE_NOOP_REASON = (
    "This looks like an idle wait, not work: end the turn instead. Use "
    "run_in_background for a long command, Monitor to stream a background "
    "process, or a bounded until-loop that checks a real condition (never a "
    "bare sleep/true/: /echo waiting)."
)

# A command containing a bounded loop construct is exempt: `sleep` inside
# `until ...; do sleep N; done` is the polling primitive itself, not idle.
LOOP_CONSTRUCT = re.compile(r"\b(?:until|while)\b")

_IDLE_NOOP_SEGMENT = re.compile(
    r"^(?:"
    r"true"
    r"|:"
    r"|sleep\s+[0-9]+(?:\.[0-9]+)?"
    r"|echo\s+(?:-[a-zA-Z]+\s+)*"
    r"""['"]?(?:waiting|idle|polling|still\s+waiting|\.\.\.)[.\s'"]*"""
    r")$",
    re.IGNORECASE,
)


def segments(cmd: str):
    for raw in SEPARATORS.split(cmd):
        seg = raw.strip()
        # strip leading env assignments and common prefixes so `FOO=1 sudo
        # terraform destroy` still matches the `terraform` rule
        while seg:
            head = seg.split(None, 1)
            if len(head) == 2 and (
                re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", head[0])
                or head[0] in ("sudo", "command", "nohup", "time", "env", "eval")
            ):
                seg = head[1].strip()
            else:
                break
        if seg:
            yield seg


def is_idle_noop(cmd: str) -> bool:
    if LOOP_CONSTRUCT.search(cmd):
        return False
    segs = list(segments(cmd))
    if not segs:
        return False
    return all(_IDLE_NOOP_SEGMENT.match(seg) for seg in segs)


_ARG = r"""(?:"[^"]*"|'[^']*'|\S+)"""
_GIT_GLOBALS = re.compile(
    r"^git(?:\s+(?:-[Cc]\s+"
    + _ARG
    + r"|--(?:git-dir|work-tree|namespace|exec-path)(?:=|\s+)"
    + _ARG
    + r"|--(?:no-pager|paginate|bare|no-replace-objects|literal-pathspecs)|-[pP]))+\s+"
)
_TF_CHDIR = re.compile(r"^terraform\s+-chdir(?:=|\s+)" + _ARG + r"\s+")
_QUOTED = r"""("(?:[^"\\]|\\.)*"|'[^']*')"""
_SHELL_C = re.compile(
    r"(?:^|[\s;&|(])(?:ba|z|da|k)?sh\s+(?:-\w+\s+)*?-\w*c\s+"
    + _QUOTED
    + r"|(?:^|[\s;&|(])eval\s+"
    + _QUOTED
)
_MAX_DEPTH = 5


def _normalize(seg: str) -> str:
    """Drop git global options and terraform -chdir so the anchored rules see the subcommand."""
    seg = _GIT_GLOBALS.sub("git ", seg)
    return _TF_CHDIR.sub("terraform ", seg)


def _substitutions(cmd: str):
    """Inner text of every `$(...)` (balanced) and backtick substitution in cmd."""
    i = 0
    while i < len(cmd):
        if cmd.startswith("$(", i):
            depth, j = 1, i + 2
            while j < len(cmd) and depth:
                depth += (cmd[j] == "(") - (cmd[j] == ")")
                j += 1
            yield cmd[i + 2 : j - (1 if depth == 0 else 0)]
            i += 2
        elif cmd[i] == "`":
            j = cmd.find("`", i + 1)
            if j == -1:
                j = len(cmd)
            yield cmd[i + 1 : j]
            i = j + 1
        else:
            i += 1


def _wrapped(cmd: str):
    """Inner strings of `bash -c`/`sh -c`/`zsh -c`/`eval` with a quoted argument."""
    for m in _SHELL_C.finditer(cmd):
        quoted = m.group(1) or m.group(2)
        inner = quoted[1:-1]
        yield inner.replace('\\"', '"') if quoted[0] == '"' else inner


def guard_segments(cmd: str, depth: int = 0):
    """Yield (original, normalized) segments, recursing into wrappers and substitutions."""
    if depth > _MAX_DEPTH:
        return
    for inner in (*_wrapped(cmd), *_substitutions(cmd)):
        yield from guard_segments(inner, depth + 1)
    for seg in segments(cmd):
        yield seg, _normalize(seg)


EM_DASH = "\u2014"

_COMMIT_RE = re.compile(r"^git\s+commit\b")
_COMMIT_FILE_RE = re.compile(r"(?:^|\s)(?:-F|--file)(?:=|\s*)(?![-\s])(\S+)")
COMMIT_EM_DASH_REASON = (
    "the commit message contains an em dash (U+2014). Use a plain hyphen (-) instead and retry."
)


def _commit_has_em_dash(cmd: str, commit: str, cwd: str) -> bool:
    """True when the commit message carries U+2014.

    Inline (`-m`, heredoc, `$(cat <<EOF)`) messages are part of the command text.
    A `-F <file>` or `--file=<file>` message is read relative to the event cwd.
    `-F -` (stdin) and a file that is missing or unreadable are out of scope and pass.
    """
    if EM_DASH in cmd:
        return True
    match = _COMMIT_FILE_RE.search(commit)
    if not match:
        return False
    path = Path(match.group(1).strip("'\""))
    if not path.is_absolute():
        path = Path(cwd or ".") / path
    try:
        return EM_DASH in path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return False


def guard_bash(event: NormalizedEvent) -> Decision:
    """Deny destructive shell commands and idle no-op polls.

    Advisory guardrail against agent mistakes, not a security sandbox.
    """
    cmd = event.command
    if event.event != "pre-tool" or event.tool_kind != "shell" or not cmd:
        return ALLOW
    for seg, norm in guard_segments(cmd):
        for pattern, reason in COMPILED:
            if pattern.search(norm):
                return Decision("deny", f"guard-bash: `{seg}` - {reason}")
    commit = next((seg for seg, norm in guard_segments(cmd) if _COMMIT_RE.match(norm)), None)
    if commit is not None and _commit_has_em_dash(cmd, commit, event.cwd):
        return Decision("deny", f"guard-bash: `{commit}` - {COMMIT_EM_DASH_REASON}")
    if is_idle_noop(cmd):
        return Decision("deny", f"guard-bash: `{cmd.strip()}` - {IDLE_NOOP_REASON}")
    return ALLOW


# --- protect-files ----------------------------------------------------------
#
# Blocks edits to secrets, terraform state, .git internals and encrypted secret
# files.

# (glob matched against the basename, what is being protected)
BASENAME_PATTERNS = [
    ("*.tfstate", "terraform state"),
    ("*.tfstate.*", "terraform state"),
    ("id_rsa", "a private key"),
    ("id_ed25519", "a private key"),
    ("*.pem", "a private key"),
    ("*.key", "a private key"),
    ("*.enc.*", "an encrypted secrets file"),
    ("*.secret.*", "a secrets file"),
    ("secrets.*.yaml", "a secrets file"),
    ("secrets.*.yml", "a secrets file"),
    ("default.secrets.yaml", "a secrets file"),
]

ENV_ALLOWED = ".env.example"


def blocked_reason(path: str) -> str | None:
    """Why editing `path` is blocked, or None when it is allowed."""
    norm = path.replace("\\", "/")
    base = norm.rsplit("/", 1)[-1]
    if "/.git/" in norm or norm.startswith(".git/"):
        return "editing .git internals"
    if base == ".env" or (base.startswith(".env.") and base != ENV_ALLOWED):
        return "editing an .env secrets file"
    for pattern, what in BASENAME_PATTERNS:
        if fnmatch.fnmatchcase(base, pattern):
            return f"editing {what}"
    return None


# Keys holding the new text of an edit or write, across every harness's tool
# schema: Claude Write/Edit/NotebookEdit, Copilot CLI create/edit, Antigravity
# write_to_file/replace_file_content. Lists of dicts (MultiEdit `edits`) are
# searched one level down for the same keys. `old_string` and its aliases are
# never read, so removing an em dash stays allowed.
_NEW_CONTENT_KEYS = (
    "content",
    "new_string",
    "new_source",
    "file_text",
    "new_str",
    "CodeContent",
    "ReplacementContent",
)


def new_content(tool_input: Any) -> list[str]:
    """Every string an edit or write would put into a file, from its tool input."""
    if not isinstance(tool_input, dict):
        return []
    found: list[str] = []
    items = [tool_input]
    for value in tool_input.values():
        if isinstance(value, list):
            items.extend(item for item in value if isinstance(item, dict))
    for item in items:
        for key in _NEW_CONTENT_KEYS:
            value = item.get(key)
            if isinstance(value, str):
                found.append(value)
    for key in PATCH_KEYS:
        text = tool_input.get(key)
        if isinstance(text, str) and "*** Begin Patch" in text:
            found.extend(patch_added_lines(text))
    return found


def protect_files(event: NormalizedEvent) -> Decision:
    """Deny an edit or write that touches a protected path or adds an em dash."""
    if event.event != "pre-tool" or event.tool_kind not in ("edit", "write"):
        return ALLOW
    for path in event.paths:
        if not path:
            continue
        reason = blocked_reason(path)
        if reason is not None:
            return Decision(
                "deny",
                f"BLOCKED by protect-files hook: {reason} ({path}). Use the proper "
                "tool: the project's secret helper for secrets (the workbench-secrets "
                "pack's sops-secret-helper skill when enabled), git for .git, "
                "terraform state commands for tfstate.",
            )
    if any(EM_DASH in text for text in new_content(event.raw.get("tool_input"))):
        target = f" ({', '.join(event.paths)})" if event.paths else ""
        return Decision(
            "deny",
            f"BLOCKED by protect-files hook: the new content{target} contains an em dash "
            "(U+2014). Use a plain hyphen (-) instead and retry the edit.",
        )
    return ALLOW


# --- dispatch -----------------------------------------------------------------

HOOKS: dict[str, Callable[[NormalizedEvent], Decision]] = {
    "guard-bash": guard_bash,
    "protect-files": protect_files,
}


def decide(hook: str, event: NormalizedEvent) -> Decision:
    """Run the named hook's logic over a normalized event."""
    try:
        handler = HOOKS[hook]
    except KeyError:
        raise ValueError(f"unknown hook {hook!r}; expected one of {sorted(HOOKS)}") from None
    return handler(event)
