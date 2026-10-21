"""hook-evidence.py counts hook records and workbench block messages in transcripts."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "hook-evidence.py"


def run(*paths):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, paths)], capture_output=True, text=True
    )


def hook(command, event="PreToolUse", type_="hook_success"):
    return {"type": type_, "hookName": f"{event}:Bash", "hookEvent": event, "command": command}


def write(path, lines):
    path.write_text("\n".join(x if isinstance(x, str) else json.dumps(x) for x in lines) + "\n")


def test_counts_nested_hook_objects_sorted_by_count_then_key(tmp_path):
    f = tmp_path / "a.jsonl"
    write(
        f,
        [
            {"message": {"content": [hook("zz")]}},
            {"attachment": hook("aa")},
            {"deep": {"x": [{"y": hook("zz")}]}},
            {"attachment": hook("bb", event="Stop", type_="hook_blocking")},
            {"attachment": {"hookEvent": "PostToolUse"}},
        ],
    )
    r = run(f)
    assert r.returncode == 0
    lines = r.stdout.splitlines()
    assert lines[:4] == [
        "2  hook_success PreToolUse zz",
        "1  - PostToolUse -",
        "1  hook_blocking Stop bb",
        "1  hook_success PreToolUse aa",
    ]
    assert lines[-1] == "workbench hooks seen: none"


def test_block_strings_in_nested_content_and_hooks_seen(tmp_path):
    f = tmp_path / "a.jsonl"
    write(
        f,
        [
            {
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "content": "PreToolUse:Bash hook error: guard-bash: no stash pop",
                        }
                    ]
                }
            },
            {"x": ["guard-bash: again"]},
            {"x": "you have 3 uncommitted files"},
        ],
    )
    r = run(f)
    assert r.returncode == 0
    lines = r.stdout.splitlines()
    assert lines == [
        "2  block: guard-bash:",
        "1  block: uncommitted file",
        "workbench hooks seen: guard-bash, commit-guard",
    ]


def test_freshness_guard_marker(tmp_path):
    f = tmp_path / "a.jsonl"
    write(f, [{"r": "last verification ran on abc"}])
    assert run(f).stdout.splitlines()[-1] == "workbench hooks seen: freshness-guard"


def test_unparsable_and_empty_are_skipped(tmp_path):
    f = tmp_path / "a.jsonl"
    write(f, ["{not json", "", json.dumps({"a": hook("c")})])
    e = tmp_path / "empty.jsonl"
    e.write_text("")
    r = run(f, e)
    assert r.returncode == 0
    assert r.stdout.splitlines() == ["1  hook_success PreToolUse c", "workbench hooks seen: none"]


def test_directory_searched_recursively(tmp_path):
    sub = tmp_path / "d" / "e"
    sub.mkdir(parents=True)
    write(sub / "x.jsonl", [hook("c")])
    write(tmp_path / "d" / "ignored.txt", [hook("c")])
    r = run(tmp_path)
    assert r.stdout.splitlines()[0] == "1  hook_success PreToolUse c"


def test_missing_path_exits_2_after_processing_others(tmp_path):
    f = tmp_path / "a.jsonl"
    write(f, [hook("c")])
    r = run(tmp_path / "nope", f)
    assert r.returncode == 2
    assert f"no such path: {tmp_path / 'nope'}" in r.stderr
    assert "1  hook_success PreToolUse c" in r.stdout


def test_help_prints_usage():
    r = run("--help")
    assert r.returncode == 0
    assert "usage" in r.stdout.lower()
