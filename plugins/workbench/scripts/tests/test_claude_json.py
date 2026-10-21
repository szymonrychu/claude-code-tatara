"""claude_json.call: argv shape, stdin-only prompt, env, envelope, errors, timeout."""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import claude_json  # noqa: E402
from claude_json import ClaudeJsonError, call, call_with_meta  # noqa: E402

SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
    "additionalProperties": False,
}


def envelope(**over):
    env = {
        "type": "result",
        "is_error": False,
        "result": '{"answer":"from-result"}',
        "structured_output": {"answer": "from-structured"},
        "total_cost_usd": 0.002,
        "usage": {"input_tokens": 6, "output_tokens": 153},
        "modelUsage": {"claude-haiku-5-5": {"inputTokens": 6}},
    }
    env.update(over)
    return env


class Fake:
    def __init__(self, out=None, code=0, err=""):
        self.out = json.dumps(envelope()) if out is None else out
        self.code, self.err, self.calls = code, err, []

    def __call__(self, argv, stdin, env, timeout):
        self.calls.append({"argv": argv, "stdin": stdin, "env": env, "timeout": timeout})
        return self.code, self.out, self.err


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("WORKBENCH_CLAUDE_JSON_CHILD", raising=False)


def test_argv_shape_and_stdin_only_prompt():
    fake = Fake()
    call("SECRET-PROMPT", SCHEMA, model="haiku", effort="low", runner=fake)
    c = fake.calls[0]
    assert c["argv"] == [
        "claude",
        "-p",
        "--model",
        "haiku",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(SCHEMA, separators=(",", ":")),
        "--tools",
        "",
        "--strict-mcp-config",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--effort",
        "low",
    ]
    assert c["stdin"] == "SECRET-PROMPT"
    assert not any("SECRET-PROMPT" in a for a in c["argv"])
    assert "--bare" not in c["argv"]
    assert "--system-prompt" not in c["argv"]


def test_system_prompt_added_only_when_given():
    fake = Fake()
    call("p", SCHEMA, system="be terse", runner=fake)
    argv = fake.calls[0]["argv"]
    assert argv[argv.index("--system-prompt") + 1] == "be terse"


def _stub_claude(tmp_path, monkeypatch):
    """Put a `claude` stub on PATH that dumps its environment and prints an envelope."""
    dump = tmp_path / "env.json"
    stub = tmp_path / "bin" / "claude"
    stub.parent.mkdir()
    stub.write_text(
        f"#!{sys.executable}\nimport json, os, sys\nsys.stdin.read()\n"
        f"json.dump(dict(os.environ), open({str(dump)!r}, 'w'))\n"
        "print(json.dumps({'is_error': False, 'structured_output': {'answer': 'ok'}}))\n"
    )
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{stub.parent}{os.pathsep}{os.environ['PATH']}")
    return dump


def test_env_inherited_by_default(tmp_path, monkeypatch):
    dump = _stub_claude(tmp_path, monkeypatch)
    monkeypatch.delenv("WORKBENCH_CLAUDE_JSON_STRIP_KEYS", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "t")
    monkeypatch.setenv("CLAUDE_CODE_USE_BEDROCK", "1")
    monkeypatch.setenv("KEEP_ME", "1")
    assert call("p", SCHEMA) == {"answer": "ok"}
    env = json.loads(dump.read_text())
    assert env["ANTHROPIC_API_KEY"] == "k" and env["ANTHROPIC_AUTH_TOKEN"] == "t"
    assert env["CLAUDE_CODE_USE_BEDROCK"] == "1" and env["KEEP_ME"] == "1"
    assert env["WORKBENCH_CLAUDE_JSON_CHILD"] == "1"


def test_strip_keys_opt_in(tmp_path, monkeypatch):
    dump = _stub_claude(tmp_path, monkeypatch)
    monkeypatch.setenv("WORKBENCH_CLAUDE_JSON_STRIP_KEYS", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "t")
    monkeypatch.setenv("KEEP_ME", "1")
    assert call("p", SCHEMA) == {"answer": "ok"}
    env = json.loads(dump.read_text())
    assert "ANTHROPIC_API_KEY" not in env and "ANTHROPIC_AUTH_TOKEN" not in env
    assert env["KEEP_ME"] == "1"
    assert env["WORKBENCH_CLAUDE_JSON_CHILD"] == "1"


def test_recursion_refused(monkeypatch):
    monkeypatch.setenv("WORKBENCH_CLAUDE_JSON_CHILD", "1")
    fake = Fake()
    with pytest.raises(ClaudeJsonError, match="recursion"):
        call("p", SCHEMA, runner=fake)
    assert fake.calls == []


def test_structured_output_preferred():
    assert call("p", SCHEMA, runner=Fake()) == {"answer": "from-structured"}


def test_falls_back_to_result_json():
    out = json.dumps(envelope(structured_output=None))
    assert call("p", SCHEMA, runner=Fake(out)) == {"answer": "from-result"}


def test_is_error_carries_stderr_tail():
    out = json.dumps(envelope(is_error=True))
    with pytest.raises(ClaudeJsonError) as e:
        call("p", SCHEMA, runner=Fake(out, err="x" * 1000 + "TAILEND"))
    assert "TAILEND" in str(e.value) and "x" * 401 not in str(e.value)


def test_nonzero_exit():
    with pytest.raises(ClaudeJsonError, match="exit 3.*boom"):
        call("p", SCHEMA, runner=Fake("", code=3, err="boom"))


def test_unparseable_envelope():
    with pytest.raises(ClaudeJsonError, match="envelope"):
        call("p", SCHEMA, runner=Fake("not json", err="E"))


def test_missing_result():
    out = json.dumps({"type": "result", "is_error": False})
    with pytest.raises(ClaudeJsonError, match="no structured"):
        call("p", SCHEMA, runner=Fake(out))


def test_result_not_json():
    out = json.dumps(envelope(structured_output=None, result="plain words"))
    with pytest.raises(ClaudeJsonError, match="not JSON"):
        call("p", SCHEMA, runner=Fake(out))


def test_schema_mismatch_names_path():
    schema = {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {"type": "integer", "minimum": 1}}},
        "required": ["items"],
    }
    out = json.dumps(envelope(structured_output={"items": [1, 0]}))
    with pytest.raises(ClaudeJsonError, match=r"\$\.items\[1\]"):
        call("p", schema, runner=Fake(out))


@pytest.mark.parametrize(
    "schema,value,path",
    [
        ({"type": "object", "required": ["a"]}, {}, "$.a"),
        ({"type": "object", "properties": {}, "additionalProperties": False}, {"b": 1}, "$.b"),
        ({"type": "object", "properties": {"a": {"enum": ["x", "y"]}}}, {"a": "z"}, "$.a"),
        ({"type": "object", "properties": {"a": {"maximum": 5}}}, {"a": 6}, "$.a"),
        ({"type": "object", "properties": {"a": {"type": "integer"}}}, {"a": True}, "$.a"),
        ({"type": "object", "properties": {"a": {"type": "boolean"}}}, {"a": 1}, "$.a"),
        ({"type": "object", "properties": {"a": {"type": "string"}}}, {"a": 1}, "$.a"),
        ({"type": "array", "items": {"type": "string"}}, ["a", 2], "$[1]"),
    ],
)
def test_validator_rejects(schema, value, path):
    out = json.dumps(envelope(structured_output=value))
    with pytest.raises(ClaudeJsonError, match=re.escape(path)):
        call("p", schema, runner=Fake(out))


def test_validator_accepts_number_and_integer():
    schema = {"type": "object", "properties": {"n": {"type": "number"}, "i": {"type": "integer"}}}
    out = json.dumps(envelope(structured_output={"n": 1.5, "i": 2}))
    assert call("p", schema, runner=Fake(out)) == {"n": 1.5, "i": 2}


def test_call_with_meta():
    data, meta = call_with_meta("p", SCHEMA, runner=Fake())
    assert data == {"answer": "from-structured"}
    assert meta["usage"]["input_tokens"] == 6 and meta["usage"]["output_tokens"] == 153
    assert meta["usage"]["total_cost_usd"] == 0.002
    assert meta["model"] == "claude-haiku-5-5"
    assert isinstance(meta["ms"], int) and meta["ms"] >= 0


def test_timeout_passed_to_runner():
    fake = Fake()
    call("p", SCHEMA, timeout=7, runner=fake)
    assert fake.calls[0]["timeout"] == 7


def test_default_runner_timeout_kills_group(tmp_path):
    marker = tmp_path / "survivor"
    script = f"sleep 2; touch {marker}"
    start = time.monotonic()
    with pytest.raises(ClaudeJsonError, match="timeout"):
        argv = ["sh", "-c", f"sh -c '{script}' & wait"]
        claude_json.run_subprocess(argv, "", dict(os.environ), 0.3)
    assert time.monotonic() - start < 1.5
    time.sleep(2.3)
    assert not marker.exists()


def test_default_runner_pipes_stdin():
    code, out, _ = claude_json.run_subprocess(["cat"], "hello", dict(os.environ), 5)
    assert (code, out) == (0, "hello")


def test_smoke_failure_exits_1(monkeypatch, capsys):
    def boom(*a, **k):
        raise ClaudeJsonError("nope")

    monkeypatch.setattr(claude_json, "call_with_meta", boom)
    assert claude_json.main(["smoke"]) == 1
    assert "nope" in capsys.readouterr().out


def test_smoke_success_prints_ok(monkeypatch, capsys):
    monkeypatch.setattr(
        claude_json,
        "call_with_meta",
        lambda *a, **k: ({"word": "pong"}, {"model": "claude-haiku-5-5", "ms": 12, "usage": {}}),
    )
    assert claude_json.main(["smoke"]) == 0
    assert capsys.readouterr().out.strip() == "ok claude-haiku-5-5 12ms"


def test_cli_smoke_runs_as_script_error_path():
    env = dict(os.environ, WORKBENCH_CLAUDE_JSON_CHILD="1")
    p = subprocess.run(
        [sys.executable, str(Path(claude_json.__file__)), "smoke"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert p.returncode == 1 and "recursion" in (p.stdout + p.stderr)
