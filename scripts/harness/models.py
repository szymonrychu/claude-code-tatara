"""Per-target subagent model map (design Q4: inherit by default, override in harness.models)."""

from __future__ import annotations

INHERIT = "inherit"
# True: write `model: inherit`; False: omit the field (the harness has no such key).
TARGET_DEFAULTS: dict[str, str | None] = {
    "copilot": None,
    "cursor": INHERIT,
    "codex": None,
    "gemini": INHERIT,
    "antigravity": INHERIT,
}


def model_for(target: str, claude_model: str | None, overrides: dict | None) -> str | None:
    """Model string for a target's agent, or None to omit the field.

    `overrides` is `harness.models` ({target: {alias: model}}) or one target's {alias: model}.
    """
    if target not in TARGET_DEFAULTS:
        raise ValueError(f"unknown target {target!r} (known: {', '.join(TARGET_DEFAULTS)})")
    aliases = overrides or {}
    if isinstance(aliases.get(target), dict):
        aliases = aliases[target]
    if claude_model is not None and isinstance(aliases.get(claude_model), str):
        return aliases[claude_model]
    return TARGET_DEFAULTS[target]
