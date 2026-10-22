"""heartbeat.py: one short line per beat, from a Monitor, at near-zero token cost.

Each line wakes the orchestrator for one turn, which re-reads its cached prefix;
on a 5-minute cache TTL that keeps the cache warm through an idle wait. The
optional haiku call adds a % done / ETA estimate for ~600 tokens.
"""

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import heartbeat  # noqa: E402

HB = [sys.executable, str(SCRIPTS / "heartbeat.py")]


def journal(tmp_path, events):
    p = tmp_path / "journal.jsonl"
    p.write_text("".join(json.dumps(e) + "\n" for e in events))
    return p


def started(aid, label):
    return {"type": "started", "agentId": aid, "label": label}


def result(aid, r=None):
    return {"type": "result", "agentId": aid, "result": r or {}}


# ---------------------------------------------------------------- ttl
@pytest.mark.parametrize(
    "env,settings,want",
    [
        ({}, {}, "1h"),  # subscription default for the main conversation
        ({"FORCE_PROMPT_CACHING_5M": "1", "CLAUDE_CODE_PROMPT_CACHE_TTL": "1h"}, {}, "5m"),
        ({"CLAUDE_CODE_PROMPT_CACHE_TTL": "5m"}, {"promptCacheTtl": "1h"}, "5m"),
        ({}, {"promptCacheTtl": "5m"}, "5m"),
        ({"ENABLE_PROMPT_CACHING_1H": "1"}, {}, "1h"),
        ({"ANTHROPIC_API_KEY": "x"}, {}, "5m"),  # API key default is 5m
    ],
)
def test_ttl_follows_the_documented_precedence(tmp_path, env, settings, want):
    s = tmp_path / "settings.json"
    s.write_text(json.dumps(settings))
    assert heartbeat.detect_ttl(env, [s]) == want


def test_keepalive_is_off_by_default_and_only_beats_fast_on_5m():
    assert heartbeat.default_interval("5m") == 600
    assert heartbeat.default_interval("5m", keepalive=True) == 270
    assert heartbeat.default_interval("1h", keepalive=True) == 600


def test_default_run_reports_at_the_bounded_wait_interval(tmp_path, monkeypatch):
    monkeypatch.setenv("FORCE_PROMPT_CACHING_5M", "1")
    assert heartbeat.resolve_interval(heartbeat.parse(["--journal", "j"])) == 600
    assert heartbeat.resolve_interval(heartbeat.parse(["--journal", "j", "--keepalive"])) == 270


# ---------------------------------------------------------------- digest
def test_digest_counts_agents_and_names_the_running_ones(tmp_path):
    j = journal(
        tmp_path,
        [
            started("a1", "fq:impl:alpha"),
            started("a2", "fq:impl:beta"),
            result("a1"),
            started("a3", "fq:review:alpha#1"),
        ],
    )
    d = heartbeat.digest(j)
    assert d["started"] == 3
    assert d["finished"] == 1
    assert d["running"] == ["impl:beta", "review:alpha#1"]


def test_fallback_line_is_short_ascii_and_has_no_estimate(tmp_path):
    j = journal(
        tmp_path, [started("a1", "fq:impl:alpha"), result("a1"), started("a2", "fq:impl:beta")]
    )
    line = heartbeat.beat_line(heartbeat.digest(j), estimate=None)
    assert line == "1/2 agents | run: impl:beta"
    assert line.isascii() and len(line) <= 100


def test_estimate_is_prefixed_when_present(tmp_path):
    j = journal(tmp_path, [started("a1", "fq:impl:alpha")])
    line = heartbeat.beat_line(heartbeat.digest(j), estimate="~40% done/12m left")
    assert line.startswith("~40% done/12m left | 0/1 agents")


# ---------------------------------------------------------------- haiku
def fake_claude(tmp_path, body):
    b = tmp_path / "bin"
    b.mkdir()
    c = b / "claude"
    c.write_text(f"#!/bin/sh\ncat >/dev/null\necho '{body}'\n")
    c.chmod(c.stat().st_mode | stat.S_IEXEC)
    return {**os.environ, "PATH": f"{b}:{os.environ['PATH']}"}


def test_haiku_estimate_is_parsed_from_the_cli(tmp_path):
    env = fake_claude(tmp_path, json.dumps({"result": "Estimate: 63% ETA 9m"}))
    j = journal(tmp_path, [started("a1", "fq:impl:alpha")])
    assert heartbeat.estimate(heartbeat.digest(j), total=4, env=env) == "~63% done/9m left"


def test_a_bad_haiku_answer_falls_back_to_no_estimate(tmp_path):
    env = fake_claude(tmp_path, json.dumps({"result": "I think it is going well"}))
    j = journal(tmp_path, [started("a1", "fq:impl:alpha")])
    assert heartbeat.estimate(heartbeat.digest(j), total=4, env=env) is None


# ---------------------------------------------------------------- loop
def test_loop_prints_one_line_per_beat_and_flags_a_stall(tmp_path):
    j = journal(tmp_path, [started("a1", "fq:impl:alpha")])
    out = subprocess.run(
        HB
        + [
            "--journal",
            str(j),
            "--interval",
            "0",
            "--beats",
            "4",
            "--stall-beats",
            "3",
            "--keepalive",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert len(out) == 4
    assert out[0].startswith("0/1 agents")
    assert out[3].startswith("STALL")


def loop(j, *extra):
    return subprocess.run(
        HB + ["--journal", str(j), "--interval", "0", *extra],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()


def test_quiet_by_default_prints_first_digest_then_stall_only(tmp_path):
    j = journal(tmp_path, [started("a1", "fq:impl:alpha")])
    out = loop(j, "--beats", "5", "--stall-beats", "3")
    assert out[0].startswith("0/1 agents")
    assert [line.split()[0] for line in out[1:]] == ["STALL", "STALL"]


def test_unchanged_digest_prints_nothing(tmp_path):
    j = journal(tmp_path, [started("a1", "fq:impl:alpha")])
    assert len(loop(j, "--beats", "3", "--stall-beats", "9", "--report-every", "0")) == 1


def test_stall_and_end_print_immediately(tmp_path):
    j = journal(tmp_path, [started("a1", "fq:impl:alpha")])
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


def test_eta_is_opt_in(tmp_path):
    marker = tmp_path / "called"
    b = tmp_path / "bin"
    b.mkdir()
    c = b / "claude"
    c.write_text(f'#!/bin/sh\ntouch {marker}\necho \'{{"result": "50% ETA 5m"}}\'\n')
    c.chmod(c.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{b}:{os.environ['PATH']}"}
    j = journal(tmp_path, [started("a1", "fq:impl:alpha")])
    cmd = HB + ["--journal", str(j), "--interval", "0", "--beats", "1"]
    out = subprocess.run(cmd, capture_output=True, text=True, env=env).stdout
    assert not marker.exists() and out.startswith("0/1 agents")
    out = subprocess.run(cmd + ["--no-eta"], capture_output=True, text=True, env=env).stdout
    assert not marker.exists()
    out = subprocess.run(cmd + ["--eta"], capture_output=True, text=True, env=env).stdout
    assert marker.exists() and out.startswith("~50% done/5m left")


def test_keepalive_still_prints_every_beat(tmp_path):
    j = journal(tmp_path, [started("a1", "fq:impl:alpha")])
    assert len(loop(j, "--beats", "2", "--stall-beats", "9", "--keepalive")) == 2


def test_loop_stops_by_itself_when_the_journal_is_gone(tmp_path):
    out = subprocess.run(
        HB
        + [
            "--journal",
            str(tmp_path / "missing.jsonl"),
            "--interval",
            "0",
            "--beats",
            "3",
            "--no-eta",
        ],
        capture_output=True,
        text=True,
    )
    assert out.stdout.strip() == "END no journal"
    assert out.returncode == 0


def test_digest_reports_each_tasks_latest_step(tmp_path):
    j = journal(
        tmp_path,
        [
            started("a1", "fq:impl:alpha"),
            result("a1"),
            started("a2", "fq:review:alpha#1"),
            result("a2"),
            started("a3", "fq:impl:beta+1"),
        ],
    )
    assert heartbeat.digest(j)["tasks"] == {"alpha": "review#1 done", "beta": "impl+1 running"}


def test_the_haiku_prompt_carries_per_task_state(tmp_path):
    seen = tmp_path / "prompt.txt"
    b = tmp_path / "bin"
    b.mkdir()
    c = b / "claude"
    c.write_text(f'#!/bin/sh\ncat > {seen}\necho \'{{"result": "50% ETA 5m"}}\'\n')
    c.chmod(c.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{b}:{os.environ['PATH']}"}
    j = journal(tmp_path, [started("a1", "fq:impl:alpha"), result("a1")])
    heartbeat.estimate(heartbeat.digest(j), total=2, env=env)
    assert "alpha: impl done" in seen.read_text()


def test_the_haiku_prompt_carries_remaining_estimate_minutes(tmp_path):
    seen = tmp_path / "prompt.txt"
    b = tmp_path / "bin"
    b.mkdir()
    c = b / "claude"
    c.write_text(f'#!/bin/sh\ncat > {seen}\necho \'{{"result": "50% ETA 5m"}}\'\n')
    c.chmod(c.stat().st_mode | stat.S_IEXEC)
    env = {**os.environ, "PATH": f"{b}:{os.environ['PATH']}"}
    j = journal(tmp_path, [started("a1", "fq:impl:alpha")])
    heartbeat.estimate(heartbeat.digest(j), total=4, remaining_min=75, env=env)
    text = seen.read_text()
    assert "Remaining estimate: 75 min" in text
    assert "Plan tasks" not in text


def test_remaining_min_flag_is_parsed():
    assert heartbeat.parse(["--journal", "j", "--remaining-min", "75"]).remaining_min == 75
