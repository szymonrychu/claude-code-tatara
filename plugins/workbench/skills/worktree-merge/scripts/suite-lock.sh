#!/usr/bin/env bash
# Run a full test suite while holding one of N machine-wide lock slots, so
# only SUITE_LOCK_SLOTS full suites run at once. Contention killed two runs
# mid-way in one session.
#
#   suite-lock.sh -- mise run test
#
# SUITE_LOCK_DIR   lock path prefix (default: $TMPDIR/claude-suite-lock)
# SUITE_LOCK_WAIT  seconds to wait for a live holder before failing (default 1200)
# SUITE_LOCK_SLOTS number of concurrent holders allowed. Falls back to the
#                  first ".suite-lock-slots" file found walking up from $PWD,
#                  then to 1 (the legacy single-lock behaviour, unchanged for
#                  any caller that never sets either).
#
# All slot counts share one namespace: slot 0 is always the unsuffixed
# $SUITE_LOCK_DIR path, the same one legacy (SLOTS=1) callers have always
# used, so a shell that runs without a workbench's mise env (and so never
# saw SUITE_LOCK_SLOTS) still occupies a real slot that higher-SLOTS callers
# see and count. Slot N>=1 is "$SUITE_LOCK_DIR.slotN". A SLOTS=1 caller has
# only ever tried slot 0, but since it can't know whether some other process
# on the machine is running with a higher SLOTS and already holds slot 1+,
# it treats ANY occupied slot as busy and waits - it never assumes it has the
# whole namespace to itself.
#
# mkdir is the lock primitive because it is atomic and exists everywhere;
# flock(1) and timeout(1) are not on stock macOS.
set -uo pipefail

[ "${1:-}" = "--" ] && shift
[ $# -gt 0 ] || { echo "usage: suite-lock.sh -- <command...>" >&2; exit 2; }

LOCK_BASE="${SUITE_LOCK_DIR:-${TMPDIR:-/tmp}/claude-suite-lock}"
WAIT="${SUITE_LOCK_WAIT:-1200}"

slots_from_file() {
  local dir="$PWD" f val
  while :; do
    f="$dir/.suite-lock-slots"
    if [ -f "$f" ]; then
      read -r val < "$f" 2>/dev/null || val=""
      [ -n "$val" ] && { printf '%s' "$val"; return 0; }
    fi
    [ "$dir" = "/" ] && return 1
    dir="$(dirname "$dir")"
  done
  return 1
}

SLOTS="${SUITE_LOCK_SLOTS:-}"
if [ -z "$SLOTS" ]; then
  SLOTS="$(slots_from_file)" || SLOTS=""
fi
SLOTS="${SLOTS:-1}"

start=$(date +%s)

# Slot 0 is always the bare legacy path - same path a pre-SLOTS copy of this
# script, or a SLOTS=1 caller, has always used.
slot_dir() {
  if [ "$1" -eq 0 ]; then
    echo "$LOCK_BASE"
  else
    echo "${LOCK_BASE}.slot$1"
  fi
}

# Every lock dir that currently exists anywhere in the shared namespace,
# regardless of which SLOTS value created it.
existing_slots() {
  local d
  [ -d "$LOCK_BASE" ] && echo "$LOCK_BASE"
  for d in "${LOCK_BASE}".slot*; do
    [ -d "$d" ] && echo "$d"
  done
}

acquire() {
  if [ "$SLOTS" -eq 1 ]; then
    # A SLOTS=1 caller wants sole use of the whole namespace, since it has no
    # way to know how many slots a concurrent higher-SLOTS caller is using.
    [ -z "$(existing_slots)" ] || return 1
    if mkdir "$LOCK_BASE" 2>/dev/null; then
      LOCK="$LOCK_BASE"
      return 0
    fi
    return 1
  fi
  local i=0 slot
  while [ "$i" -lt "$SLOTS" ]; do
    slot="$(slot_dir "$i")"
    if mkdir "$slot" 2>/dev/null; then
      LOCK="$slot"
      return 0
    fi
    i=$((i + 1))
  done
  return 1
}

reclaim_stale() {
  local slot holder
  while IFS= read -r slot; do
    [ -n "$slot" ] || continue
    holder="$(cat "$slot/pid" 2>/dev/null || true)"
    if [ -n "$holder" ] && ! kill -0 "$holder" 2>/dev/null; then
      echo "suite-lock: reclaiming stale lock from dead pid $holder ($slot)" >&2
      rm -rf "$slot"
    fi
  done < <(existing_slots)
}

while ! acquire; do
  reclaim_stale
  acquire && break
  if [ $(( $(date +%s) - start )) -ge "$WAIT" ]; then
    holders=""
    while IFS= read -r slot; do
      [ -n "$slot" ] || continue
      h="$(cat "$slot/pid" 2>/dev/null || true)"
      [ -n "$h" ] && holders="${holders}${holders:+ }${h}"
    done < <(existing_slots)
    echo "suite-lock: gave up after ${WAIT}s, all ${SLOTS} lock slot(s) held by pid(s): ${holders:-unknown}" >&2
    exit 75
  fi
  sleep 1
done

echo $$ > "$LOCK/pid"
trap 'rm -rf "$LOCK"' EXIT INT TERM
"$@"
