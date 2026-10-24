"""Target paths and added lines of a Codex `apply_patch` envelope.

Codex sends Edit and Write as `apply_patch` with the patch text in
`tool_input.command` and no `file_path`, so the protected-file guard needs the
paths, and the em dash guard the new content, out of the envelope. Header lines
are recognised only at column zero; hunk and added-file content lines always
start with ' ', '+', '-' or '@@', so text that merely looks like a header inside
a hunk is never matched.
"""

from __future__ import annotations

# Tool-input keys that may carry an envelope (Codex puts it in `command`).
PATCH_KEYS = ("command", "input", "patch")
_HEADERS = ("*** Add File: ", "*** Update File: ", "*** Delete File: ", "*** Move to: ")


def _body(text: str) -> list[str]:
    """The lines between `*** Begin Patch` and `*** End Patch`; [] if malformed."""
    lines = text.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.strip() == "*** Begin Patch")
    except StopIteration:
        return []
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.strip() == "*** End Patch":
            break
        body.append(line)
    return body


def patch_paths(text: str) -> list[str]:
    """Every target path of the patch, in order, de-duplicated; [] if malformed."""
    paths: list[str] = []
    for line in _body(text):
        for header in _HEADERS:
            if line.startswith(header):
                path = line[len(header) :].strip()
                if path and path not in paths:
                    paths.append(path)
                break
    return paths


def patch_added_lines(text: str) -> list[str]:
    """The text of every `+` line (hunk additions and Add File bodies); [] if malformed."""
    return [line[1:] for line in _body(text) if line.startswith("+")]
