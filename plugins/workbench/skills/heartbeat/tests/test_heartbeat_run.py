"""heartbeat.py --run <id>: resolve the run's paths, wait for the journal, end with the run."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import heartbeat  # noqa: E402

HB = [sys.executable, str(SCRIPTS / "heartbeat.py")]
RUN = "wf-abc123"


def layout(projects, record=None, journal=None):
    sess = projects / "-proj" / "sess1"
    if record is not None:
        (sess / "workflows").mkdir(parents=True, exist_ok=True)
        (sess / "workflows" / f"{RUN}.json").write_text(json.dumps(record))
    if journal is not None:
        d = sess / "subagents" / "workflows" / RUN
        d.mkdir(parents=True, exist_ok=True)
        (d / "journal.jsonl").write_text("".join(json.dumps(e) + "\n" for e in journal))
    return sess


def run(projects, *extra, timeout=30):
    return subprocess.run(
        [
            *HB,
            "--run",
            RUN,
            "--projects-dir",
            str(projects),
            "--no-eta",
            "--interval",
            "0.05",
            *extra,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_run_paths_none_while_absent(tmp_path):
    assert heartbeat.run_paths(RUN, tmp_path) == (None, None)


def test_run_paths_resolve(tmp_path):
    sess = layout(tmp_path, {"status": "completed"}, [])
    rec, jr = heartbeat.run_paths(RUN, tmp_path)
    assert rec == sess / "workflows" / f"{RUN}.json"
    assert jr == sess / "subagents" / "workflows" / RUN / "journal.jsonl"


def test_run_paths_reads_env_default(tmp_path, monkeypatch):
    layout(tmp_path, None, [])
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(tmp_path))
    rec, jr = heartbeat.run_paths(RUN)
    assert rec is None and jr is not None


def test_run_and_journal_are_mutually_exclusive(tmp_path):
    p = subprocess.run([*HB, "--run", RUN, "--journal", "x"], capture_output=True, text=True)
    assert p.returncode == 2


def test_waits_for_journal(tmp_path):
    p = run(tmp_path, "--wait-max", "0.001")
    assert f"waiting for run {RUN}" in p.stdout.splitlines()[0]


def test_wait_max_clear_error(tmp_path):
    p = run(tmp_path, "--wait-max", "0.001")
    assert p.returncode == 2
    assert p.stdout.splitlines()[-1] == (
        f"END run {RUN} not found under {tmp_path}: the runtime layout may have changed"
    )


def test_exits_on_run_record(tmp_path):
    ret = {
        "tasks": [
            {"id": "a", "verified": True, "clean": True},
            {"id": "b", "verified": True, "processOnly": True},
            {"id": "c", "verified": False},
        ]
    }
    layout(
        tmp_path,
        {"status": "completed", "durationMs": 125000, "result": ret},
        [{"type": "started", "agentId": "1", "label": "r:impl:a"}],
    )
    p = run(tmp_path)
    assert p.returncode == 0
    assert p.stdout.splitlines()[-1] == "END completed 2/3 tasks 2m05s"


def test_beats_use_digest_until_the_record_exists(tmp_path):
    layout(tmp_path, None, [{"type": "started", "agentId": "1", "label": "r:impl:a"}])
    p = run(tmp_path, "--beats", "2")
    assert p.returncode == 0
    assert "0/1 agents" in p.stdout


def test_waiting_line_prints_once_per_report_interval(tmp_path):
    p = run(tmp_path, "--wait-max", "0.002", "--report-every", "3600")
    assert p.stdout.count("waiting for run") == 1


def test_failed_run_without_result_still_ends(tmp_path):
    layout(tmp_path, {"status": "failed", "durationMs": 5000})
    p = run(tmp_path)
    assert p.returncode == 0
    assert p.stdout.splitlines()[-1] == "END failed 0/0 tasks 5s"


def _journal(tmp_path, events):
    p = tmp_path / "journal.jsonl"
    p.write_text("".join(json.dumps(e) + "\n" for e in events))
    return p


def _started(agent_id, label):
    return {"type": "started", "agentId": agent_id, "label": label}


def loop(j, *extra):
    return subprocess.run(
        [*HB, "--journal", str(j), "--interval", "0", *extra],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()


def test_unchanged_digest_prints_nothing(tmp_path):
    j = _journal(tmp_path, [_started("a1", "fq:impl:alpha")])
    assert len(loop(j, "--beats", "3", "--stall-beats", "9", "--report-every", "0")) == 1


def test_stall_and_end_print_immediately(tmp_path):
    j = _journal(tmp_path, [_started("a1", "fq:impl:alpha")])
    out = loop(j, "--beats", "5", "--stall-beats", "3", "--report-every", "999999")
    assert [line.split()[0] for line in out[1:]] == ["STALL", "STALL"]
    p = subprocess.run(
        HB + ["--journal", str(tmp_path / "gone.jsonl"), "--report-every", "999999"],
        capture_output=True,
        text=True,
    )
    assert p.stdout.strip() == "END no journal"


def test_progress_line_at_most_every_report_interval():
    d1, d2 = {"started": 1}, {"started": 2}
    assert heartbeat.report_due(d1, None, 0, 5, 1800)  # first beat after arming
    assert not heartbeat.report_due(d1, d1, 0, 9999, 1800)  # unchanged
    assert not heartbeat.report_due(d2, d1, 100, 200, 1800)  # changed, too soon
    assert heartbeat.report_due(d2, d1, 100, 1900, 1800)  # changed and due


def test_keepalive_still_prints_every_beat(tmp_path):
    j = _journal(tmp_path, [_started("a1", "fq:impl:alpha")])
    assert len(loop(j, "--beats", "2", "--stall-beats", "9", "--keepalive")) == 2
