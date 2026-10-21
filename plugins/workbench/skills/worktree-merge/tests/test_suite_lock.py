"""suite-lock.sh: one full test suite at a time on this machine.

Two suite runs were killed mid-way by contention while sibling agents ran
theirs alongside Chrome and a docker build. Each lost ~7 minutes.
"""

import os
import subprocess
import time
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "suite-lock.sh"


def base_env(lock_dir):
    # A caller's SUITE_LOCK_SLOTS (a workbench .mise.toml sets it) must not leak
    # in: every test states its slot count explicitly or means the default.
    env = {k: v for k, v in os.environ.items() if k != "SUITE_LOCK_SLOTS"}
    env["SUITE_LOCK_DIR"] = str(lock_dir)
    return env


def run(tmp_path, *cmd, wait=None, slots=None):
    env = base_env(tmp_path / "lock")
    if wait is not None:
        env["SUITE_LOCK_WAIT"] = str(wait)
    if slots is not None:
        env["SUITE_LOCK_SLOTS"] = str(slots)
    return subprocess.Popen(
        ["bash", str(SCRIPT), "--", *cmd],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_runs_the_command_and_keeps_its_exit_code(tmp_path):
    ok = run(tmp_path, "true")
    assert ok.wait(10) == 0
    bad = run(tmp_path, "bash", "-c", "exit 3")
    assert bad.wait(10) == 3


def test_a_second_run_waits_for_the_first(tmp_path):
    log = tmp_path / "order"
    first = run(tmp_path, "bash", "-c", f"echo A-start >> {log}; sleep 1; echo A-end >> {log}")
    time.sleep(0.3)
    second = run(tmp_path, "bash", "-c", f"echo B >> {log}")
    assert first.wait(10) == 0
    assert second.wait(10) == 0
    assert log.read_text().split() == ["A-start", "A-end", "B"]


def test_the_lock_is_released_after_the_command(tmp_path):
    assert run(tmp_path, "true").wait(10) == 0
    assert not (tmp_path / "lock").exists()


def test_a_stale_lock_from_a_dead_process_is_reclaimed(tmp_path):
    lock = tmp_path / "lock"
    lock.mkdir()
    dead = subprocess.Popen(["true"])
    dead.wait()
    (lock / "pid").write_text(str(dead.pid))
    assert run(tmp_path, "true", wait=2).wait(10) == 0


def test_a_live_holder_past_the_wait_bound_fails_loudly(tmp_path):
    lock = tmp_path / "lock"
    lock.mkdir()
    (lock / "pid").write_text(str(os.getpid()))
    p = run(tmp_path, "true", wait=1)
    assert p.wait(10) != 0
    assert "held by pid" in p.communicate()[1]


def test_default_slots_is_one_and_uses_the_unsuffixed_lock_path(tmp_path):
    # SUITE_LOCK_SLOTS unset must behave exactly like before this change:
    # same single lock directory, no ".slot0" suffix, other projects unaffected.
    assert run(tmp_path, "true").wait(10) == 0
    lock = tmp_path / "lock"
    holder = subprocess.Popen(
        ["bash", str(SCRIPT), "--", "sleep", "1"],
        env=base_env(lock),
    )
    time.sleep(0.3)
    assert lock.is_dir()
    assert not (tmp_path / "lock.slot0").exists()
    holder.wait(10)


def test_two_slots_allow_two_concurrent_holders(tmp_path):
    log = tmp_path / "order"
    first = run(
        tmp_path, "bash", "-c", f"echo A-start >> {log}; sleep 1; echo A-end >> {log}", slots=2
    )
    time.sleep(0.3)
    second = run(tmp_path, "bash", "-c", f"echo B >> {log}", slots=2)
    assert second.wait(10) == 0
    assert first.wait(10) == 0
    # B ran to completion before A finished sleeping - both held a slot at once.
    lines = log.read_text().split()
    assert lines == ["A-start", "B", "A-end"]


def test_a_third_run_waits_when_both_slots_are_taken(tmp_path):
    log = tmp_path / "order"
    first = run(
        tmp_path, "bash", "-c", f"echo A-start >> {log}; sleep 1; echo A-end >> {log}", slots=2
    )
    second = run(
        tmp_path, "bash", "-c", f"echo B-start >> {log}; sleep 1; echo B-end >> {log}", slots=2
    )
    time.sleep(0.3)
    third = run(tmp_path, "bash", "-c", f"echo C >> {log}", slots=2)
    assert first.wait(10) == 0
    assert second.wait(10) == 0
    assert third.wait(10) == 0
    lines = log.read_text().split()
    # C only appears after both A and B have finished (no free slot until then).
    assert lines.index("C") > lines.index("A-end")
    assert lines.index("C") > lines.index("B-end")


def test_a_stale_slot_lock_is_reclaimed_independently(tmp_path):
    stale = tmp_path / "lock.slot0"
    stale.mkdir()
    dead = subprocess.Popen(["true"])
    dead.wait()
    (stale / "pid").write_text(str(dead.pid))
    # slot1 is free, so this should succeed immediately without needing the
    # stale slot0 to be reclaimed - but reclaim must not crash either.
    assert run(tmp_path, "true", wait=2, slots=2).wait(10) == 0


def test_legacy_holder_is_seen_as_a_slot_by_a_two_slot_requester(tmp_path):
    # A legacy caller (no SUITE_LOCK_SLOTS, or a shell that never activated
    # mise) takes the unsuffixed lock path. A SLOTS=2 requester must see that
    # as one of its two slots, take the other, and a third must then wait for
    # one of the first two to free up - never oversubscribe past 2.
    log = tmp_path / "order"
    legacy = run(tmp_path, "bash", "-c", f"echo L-start >> {log}; sleep 1; echo L-end >> {log}")
    time.sleep(0.3)
    assert (tmp_path / "lock").is_dir()

    second = run(
        tmp_path, "bash", "-c", f"echo S-start >> {log}; sleep 1; echo S-end >> {log}", slots=2
    )
    time.sleep(0.3)
    # second must have taken slot1, not blocked on the legacy slot0.
    assert (tmp_path / "lock.slot1").is_dir()

    third = run(tmp_path, "bash", "-c", f"echo T >> {log}", slots=2)
    time.sleep(0.3)
    # third has nowhere to go until legacy or second frees a slot.
    assert "T" not in log.read_text().split()

    assert legacy.wait(10) == 0
    assert second.wait(10) == 0
    assert third.wait(10) == 0
    lines = log.read_text().split()
    assert lines.index("T") > lines.index("L-end")


def test_slots_one_requester_waits_while_any_slot_of_a_two_slot_scheme_is_held(tmp_path):
    # A SLOTS=1 caller must not assume the legacy path is the only lock in
    # play - if some other process is holding slot1 of a SLOTS=2 scheme, the
    # SLOTS=1 caller must wait too, or the machine gets oversubscribed.
    log = tmp_path / "order"
    holder = run(
        tmp_path, "bash", "-c", f"echo H-start >> {log}; sleep 1; echo H-end >> {log}", slots=2
    )
    time.sleep(0.3)
    assert (tmp_path / "lock.slot1").is_dir() or (tmp_path / "lock").is_dir()

    waiter = run(tmp_path, "bash", "-c", f"echo W >> {log}")
    time.sleep(0.3)
    assert "W" not in log.read_text().split()

    assert holder.wait(10) == 0
    assert waiter.wait(10) == 0
    lines = log.read_text().split()
    assert lines.index("W") > lines.index("H-end")
