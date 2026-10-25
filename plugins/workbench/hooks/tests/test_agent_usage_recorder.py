"""Tests for the SubagentStart/SubagentStop usage recorder (agent-usage-recorder.py).

The recorder writes one record per agent to `<main checkout>/.logs/agents/<agentId>.json`,
recomputed from the whole subagent transcript on every stop, and never blocks or prints.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]
HOOK = HOOKS / "agent-usage-recorder.py"
PLUGIN_JSON = HOOKS.parent / ".claude-plugin" / "plugin.json"
RECORDER_CMD = 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/agent-usage-recorder.py"'
GUARD_GROUP = {
    "hooks": [
        {
            "type": "command",
            "command": 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/subagent-commit-guard.py"',
            "timeout": 15,
            "statusMessage": "Checking for uncommitted work...",
        }
    ]
}


def run_hook(stdin, root=None):
    """Run the recorder as Claude Code does; `root` pins the main checkout via WORKBENCH_ROOT."""
    env = {k: v for k, v in os.environ.items() if k not in ("WORKBENCH_ROOT", "CLAUDE_PROJECT_DIR")}
    if root is not None:
        env["WORKBENCH_ROOT"] = str(root)
    if isinstance(stdin, (dict, list)):
        stdin = json.dumps(stdin)
    if isinstance(stdin, str):
        stdin = stdin.encode("utf-8")
    proc = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, env=env)
    return subprocess.CompletedProcess(
        proc.args,
        proc.returncode,
        proc.stdout.decode("utf-8", "replace"),
        proc.stderr.decode("utf-8", "replace"),
    )


def assistant(msg_id, stamp, usage, model="claude-test-1"):
    return {
        "type": "assistant",
        "timestamp": stamp,
        "requestId": f"req-{msg_id}",
        "message": {"id": msg_id, "model": model, "role": "assistant", "usage": usage},
    }


def usage(inp, cc, cr, out):
    return {
        "input_tokens": inp,
        "cache_creation_input_tokens": cc,
        "cache_read_input_tokens": cr,
        "output_tokens": out,
    }


def first_round(prompt="[wb my-epic/my-task/impl]\n\nImplement the task."):
    return [
        {
            "type": "user",
            "timestamp": "2026-10-24T10:00:00.000Z",
            "message": {"role": "user", "content": prompt},
        },
        assistant("m1", "2026-10-24T10:00:05.000Z", usage(10, 100, 1000, 5)),
        # One message split over two lines carries the same usage: counted once.
        assistant("m1", "2026-10-24T10:00:06.000Z", usage(10, 100, 1000, 5)),
        assistant("m2", "2026-10-24T10:05:00.000Z", usage(1, 2, 3, 4)),
    ]


def fix_round():
    return [
        {
            "type": "user",
            "timestamp": "2026-10-24T11:00:00.000Z",
            "message": {"role": "user", "content": "Fix review findings"},
        },
        assistant("m3", "2026-10-24T11:10:00.000Z", usage(20, 0, 30, 50), model="claude-test-2"),
    ]


def write_transcript(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for line in lines:
            fh.write(json.dumps(line) + "\n")
    return path


class Session:
    """A projects dir laid out like Claude Code's: <dir>/<session>.jsonl and its subagents."""

    def __init__(self, base, session_id="sess-1"):
        self.dir = base / "projects" / "-proj"
        self.session_id = session_id
        self.main_transcript = self.dir / f"{session_id}.jsonl"

    def agent_transcript(self, agent_id):
        return self.dir / self.session_id / "subagents" / f"agent-{agent_id}.jsonl"

    def payload(self, event, agent_id, agent_type, cwd, **extra):
        data = {
            "session_id": self.session_id,
            "transcript_path": str(self.main_transcript),
            "cwd": str(cwd),
            "hook_event_name": event,
            "agent_id": agent_id,
            "agent_type": agent_type,
        }
        if event == "SubagentStop":
            data.update(
                stop_hook_active=False,
                agent_transcript_path=str(self.agent_transcript(agent_id)),
                last_assistant_message="done",
            )
        data.update(extra)
        return data


def record_path(root, agent_id):
    return root / ".logs" / "agents" / f"{agent_id}.json"


def load(root, agent_id):
    return json.loads(record_path(root, agent_id).read_text())


def assert_silent(proc):
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert proc.stdout == "", proc.stdout
    assert proc.stderr == "", proc.stderr


def test_stop_writes_record(tmp_path):
    root = tmp_path / "main"
    root.mkdir()
    s = Session(tmp_path)
    write_transcript(s.agent_transcript("a1"), first_round())

    proc = run_hook(s.payload("SubagentStop", "a1", "workbench:implementer", root), root)

    assert_silent(proc)
    rec = load(root, "a1")
    assert rec["agentId"] == "a1"
    assert rec["agentType"] == "workbench:implementer"
    assert rec["model"] == "claude-test-1"
    assert (rec["epic"], rec["task"], rec["role"]) == ("my-epic", "my-task", "impl")
    assert rec["start"] == "2026-10-24T10:00:00.000Z"
    assert rec["end"] == "2026-10-24T10:05:00.000Z"
    assert rec["transcript"] == str(s.agent_transcript("a1"))
    assert rec["tokens"] == {
        "input": 11,
        "cache_creation": 102,
        "cache_read": 1003,
        "output": 9,
        "total": 1125,
    }
    assert rec["updatedAt"]


def test_second_stop_overwrites(tmp_path):
    root = tmp_path / "main"
    root.mkdir()
    s = Session(tmp_path)
    transcript = write_transcript(s.agent_transcript("a2"), first_round())
    payload = s.payload("SubagentStop", "a2", "workbench:implementer", root)

    assert_silent(run_hook(payload, root))
    assert load(root, "a2")["tokens"]["total"] == 1125

    # A fix round continues the same agent: its transcript grows and it stops again.
    write_transcript(transcript, fix_round())
    assert_silent(run_hook(payload, root))
    # Stopping again with nothing new must not count anything twice.
    assert_silent(run_hook(payload, root))

    rec = load(root, "a2")
    assert rec["tokens"] == {
        "input": 31,
        "cache_creation": 102,
        "cache_read": 1033,
        "output": 59,
        "total": 1225,
    }
    assert rec["end"] == "2026-10-24T11:10:00.000Z"
    assert rec["model"] == "claude-test-2"
    assert sorted(p.name for p in (root / ".logs" / "agents").iterdir()) == ["a2.json"]


def test_start_then_stop_keeps_start(tmp_path):
    root = tmp_path / "main"
    root.mkdir()
    s = Session(tmp_path)

    # Spawn: the agent transcript may not exist yet; the record still gets its start.
    early = s.payload("SubagentStart", "a3", "workbench:reviewer", root)
    assert_silent(run_hook(early, root))
    rec = load(root, "a3")
    assert rec["agentId"] == "a3"
    assert rec["agentType"] == "workbench:reviewer"
    assert rec["transcript"] == str(s.agent_transcript("a3"))
    assert rec["role"] == "review"
    assert rec["epic"] is None and rec["task"] is None
    start = rec["start"]
    assert start and start.endswith("Z") and start > "2026-10-24T10:00:00.000Z"

    # Resume fires SubagentStart again; the first start stays, and the marker is now readable.
    write_transcript(
        s.agent_transcript("a3"), first_round("[wb my-epic/my-task/review]\nReview it.")
    )
    assert_silent(run_hook(early, root))
    rec = load(root, "a3")
    assert rec["start"] == start
    assert (rec["epic"], rec["task"], rec["role"]) == ("my-epic", "my-task", "review")

    assert_silent(run_hook(s.payload("SubagentStop", "a3", "workbench:reviewer", root), root))
    rec = load(root, "a3")
    assert rec["start"] == start
    assert rec["end"] == "2026-10-24T10:05:00.000Z"
    assert rec["tokens"]["total"] == 1125
    assert (rec["epic"], rec["task"], rec["role"]) == ("my-epic", "my-task", "review")


def test_internal_agent_writes_nothing(tmp_path):
    root = tmp_path / "main"
    root.mkdir()
    s = Session(tmp_path)
    write_transcript(s.agent_transcript("i1"), first_round())

    for event in ("SubagentStart", "SubagentStop"):
        assert_silent(run_hook(s.payload(event, "i1", "", root), root))
        payload = s.payload(event, "i1", "", root)
        del payload["agent_type"]
        assert_silent(run_hook(payload, root))

    assert not (root / ".logs" / "agents").exists() or not any(
        (root / ".logs" / "agents").iterdir()
    )


def test_fails_open(tmp_path):
    root = tmp_path / "main"
    root.mkdir()
    s = Session(tmp_path)

    for stdin in ("", "not json", "{", "[1, 2]", "null", b"\xff\xfe{garbage"):
        assert_silent(run_hook(stdin, root))

    # Missing transcript.
    assert_silent(run_hook(s.payload("SubagentStop", "gone", "workbench:implementer", root), root))
    assert not record_path(root, "gone").exists()

    # Garbled transcript.
    garbled = s.agent_transcript("bad")
    garbled.parent.mkdir(parents=True, exist_ok=True)
    garbled.write_bytes(b"\x00\xff not json\n{\"type\": \n[]\n")
    assert_silent(run_hook(s.payload("SubagentStop", "bad", "workbench:implementer", root), root))
    assert not record_path(root, "bad").exists()

    # Unwritable logs dir: the main checkout is a file, so nothing can be created under it.
    write_transcript(s.agent_transcript("ok"), first_round())
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("x")
    for event in ("SubagentStart", "SubagentStop"):
        assert_silent(run_hook(s.payload(event, "ok", "workbench:implementer", blocker), blocker))

    # An agent id that cannot name a file.
    assert_silent(run_hook(s.payload("SubagentStop", "../x", "workbench:implementer", root), root))
    assert not (root / ".logs" / "x.json").exists()

    # Wrong field types.
    assert_silent(run_hook({"hook_event_name": "SubagentStop", "agent_type": 5, "agent_id": []}))


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_record_lands_in_main_checkout(tmp_path):
    main = tmp_path / "main"
    main.mkdir()
    git(main, "init", "-q", "-b", "main")
    git(main, "config", "user.email", "t@example.com")
    git(main, "config", "user.name", "T")
    (main / "seed.txt").write_text("seed\n")
    git(main, "add", "seed.txt")
    git(main, "commit", "-qm", "seed")
    tree = main / ".claude" / "worktrees" / "epic-x"
    git(main, "worktree", "add", "-q", "-b", "epic-x", str(tree))
    s = Session(tmp_path)

    cases = [
        # No meta.json yet: the role comes from the marker.
        ("w1", False, first_round(), "workbench:implementer", "impl", "my-epic"),
        # meta.json beside an unmarked transcript: the role comes from agent_type.
        ("w2", True, first_round("no marker here"), "workbench:reviewer", "review", None),
    ]
    for agent_id, meta, lines, agent_type, role, epic in cases:
        transcript = write_transcript(s.agent_transcript(agent_id), lines)
        if meta:
            transcript.with_name(f"agent-{agent_id}.meta.json").write_text(
                json.dumps({"agentType": agent_type, "description": "d", "model": "opus"})
            )
        for event in ("SubagentStart", "SubagentStop"):
            assert_silent(run_hook(s.payload(event, agent_id, agent_type, tree)))

        rec = load(main, agent_id)
        assert rec["role"] == role, agent_id
        assert rec["epic"] == epic, agent_id
        assert rec["tokens"]["total"] == 1125, agent_id
        assert not (tree / ".logs").exists(), agent_id


def _commands(hooks, event):
    return [h for group in hooks[event] for h in group["hooks"]]


def test_plugin_json_registers_recorder():
    hooks = json.loads(PLUGIN_JSON.read_text())["hooks"]
    for event in ("SubagentStart", "SubagentStop"):
        entries = [h for h in _commands(hooks, event) if "agent-usage-recorder" in h["command"]]
        assert len(entries) == 1, event
        assert entries[0]["command"] == RECORDER_CMD
        assert entries[0]["type"] == "command"
        assert entries[0]["timeout"] == 10
    # A separate entry: the commit guard group and its decision are untouched.
    assert GUARD_GROUP in hooks["SubagentStop"]
    assert [h["command"] for h in _commands(hooks, "SubagentStart")] == [RECORDER_CMD]
