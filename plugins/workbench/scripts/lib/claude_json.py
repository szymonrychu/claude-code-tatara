"""Single-turn `claude -p` call that returns schema-checked JSON, on the subscription.

Spawns `claude -p --output-format json --json-schema ... --tools ""` with the
prompt on stdin. The child inherits the caller's environment, so API-key,
Bedrock and Vertex auth work. WORKBENCH_CLAUDE_JSON_STRIP_KEYS=1 removes
ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN to force the subscription login.
`--bare` is never passed (it needs an API key).
WORKBENCH_CLAUDE_JSON_CHILD=1 guards against recursion.

Envelope probe (claude CLI, real call): the JSON envelope carries the typed
answer in the `structured_output` field (an object); `result` holds the same
answer as a JSON string and is the fallback. Other fields used: `is_error`,
`total_cost_usd`, `usage.input_tokens`, `usage.output_tokens`, and the key of
`modelUsage` (the resolved model id).

CLI: `python3 scripts/lib/claude_json.py smoke`
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from typing import Any

CHILD_ENV = "WORKBENCH_CLAUDE_JSON_CHILD"
STRIP_KEYS_ENV = "WORKBENCH_CLAUDE_JSON_STRIP_KEYS"
STRIPPED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
Runner = Callable[[list, str, dict, float], tuple]


class ClaudeJsonError(Exception):
    """Any failure of a claude_json call."""


def run_subprocess(argv: list, stdin: str, env: dict, timeout: float) -> tuple:
    """Default runner: returns (exit, stdout, stderr); kills the process group on timeout."""
    proc = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.communicate()
        raise ClaudeJsonError(f"timeout after {timeout}s") from None
    return proc.returncode, out, err


def _tail(stderr: str) -> str:
    return (stderr or "")[-400:]


_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
}


def _bad(path: str, msg: str) -> ClaudeJsonError:
    return ClaudeJsonError(f"schema mismatch at {path}: {msg}")


def validate(value: Any, schema: dict, path: str = "$") -> None:
    """Check value against the supported schema subset; raise ClaudeJsonError naming the path."""
    t = schema.get("type")
    if t is not None and not _TYPES[t](value):
        raise _bad(path, f"expected {t}, got {type(value).__name__}")
    if "enum" in schema and value not in schema["enum"]:
        raise _bad(path, f"{value!r} not in {schema['enum']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise _bad(path, f"{value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise _bad(path, f"{value} > maximum {schema['maximum']}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                raise _bad(f"{path}.{key}", "required property missing")
        for key, sub in value.items():
            if key in props:
                validate(sub, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                raise _bad(f"{path}.{key}", "additional property not allowed")
    if isinstance(value, list) and "items" in schema:
        for i, sub in enumerate(value):
            validate(sub, schema["items"], f"{path}[{i}]")


def call_with_meta(
    prompt: str,
    schema: dict,
    *,
    model: str = "haiku",
    effort: str = "low",
    system: str | None = None,
    timeout: float = 120,
    runner: Runner | None = None,
) -> tuple:
    """Run one tool-less turn; return (validated data, meta {usage, model, ms})."""
    if os.environ.get(CHILD_ENV):
        raise ClaudeJsonError("recursion: claude_json called from inside a claude_json child")
    argv = [
        "claude",
        "-p",
        "--model",
        model,
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema, separators=(",", ":")),
        "--tools",
        "",
        "--strict-mcp-config",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--effort",
        effort,
    ]
    if system is not None:
        argv += ["--system-prompt", system]
    strip = os.environ.get(STRIP_KEYS_ENV) == "1"
    env = {k: v for k, v in os.environ.items() if not (strip and k in STRIPPED_ENV)}
    env[CHILD_ENV] = "1"
    start = time.monotonic()
    code, out, err = (runner or run_subprocess)(argv, prompt, env, timeout)
    ms = int((time.monotonic() - start) * 1000)
    if code != 0:
        raise ClaudeJsonError(f"claude exit {code}: {_tail(err)}")
    try:
        env_json = json.loads(out)
    except (json.JSONDecodeError, TypeError):
        raise ClaudeJsonError(f"unparseable envelope: {_tail(err)}") from None
    if not isinstance(env_json, dict):
        raise ClaudeJsonError(f"unparseable envelope: {_tail(err)}")
    if env_json.get("is_error"):
        detail = str(env_json.get("result"))[:200]
        raise ClaudeJsonError(f"claude reported is_error: {detail} {_tail(err)}")
    data = env_json.get("structured_output")
    if data is None:
        raw = env_json.get("result")
        if not raw:
            raise ClaudeJsonError(f"no structured output in envelope: {_tail(err)}")
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raise ClaudeJsonError(f"result is not JSON: {_tail(err)}") from None
    validate(data, schema)
    usage = dict(env_json.get("usage") or {})
    meta = {
        "usage": {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_cost_usd": env_json.get("total_cost_usd"),
        },
        "model": next(iter(env_json.get("modelUsage") or {}), model),
        "ms": ms,
    }
    return data, meta


def call(prompt: str, schema: dict, **kwargs: Any) -> Any:
    """Like call_with_meta, returning only the validated data."""
    return call_with_meta(prompt, schema, **kwargs)[0]


def main(argv: list) -> int:
    if argv[:1] != ["smoke"]:
        print("usage: claude_json.py smoke")
        return 2
    schema = {
        "type": "object",
        "properties": {"word": {"type": "string"}},
        "required": ["word"],
        "additionalProperties": False,
    }
    try:
        _, meta = call_with_meta("Reply with the word pong.", schema, model="haiku", timeout=120)
    except ClaudeJsonError as e:
        print(f"error: {e}")
        return 1
    print(f"ok {meta['model']} {meta['ms']}ms")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
