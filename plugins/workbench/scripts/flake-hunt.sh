#!/usr/bin/env bash
# Repeat one component's tests to hunt a flake, keeping every failing log.
#
# Usage: flake-hunt.sh <component> <runs> [parallel]
# Runs `scripts/run-tests.sh --only <component>` <runs> times, at most
# <parallel> at once (default 1), each with its own RUN_TESTS_LOG_DIR under one
# hunt dir. Prints run <i>: PASS|FAIL as each run finishes, then fails: k/<runs>
# and the kept log paths. Exit 1 when any run failed (the hunt dir is kept),
# else 0 (the hunt dir is removed).
set -uo pipefail

usage() {
  echo "usage: flake-hunt.sh <component> <runs> [parallel]" >&2
  exit 2
}

is_pos() { case "$1" in '' | *[!0-9]*) return 1 ;; esac; [ "$1" -gt 0 ]; }

[ $# -ge 2 ] && [ $# -le 3 ] || usage
component="$1"
runs="$2"
parallel="${3:-1}"
is_pos "$runs" || usage
is_pos "$parallel" || usage

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE" || exit 1

hunt="$(mktemp -d "${TMPDIR:-/tmp}/flake-hunt.XXXXXX")"

one_run() {
  local i="$1"
  mkdir -p "$hunt/run-$i"
  if RUN_TESTS_LOG_DIR="$hunt/run-$i" bash scripts/run-tests.sh --only "$component" \
    >"$hunt/run-$i.out" 2>&1; then
    : >"$hunt/run-$i.pass"
    echo "run $i: PASS"
  else
    : >"$hunt/run-$i.fail"
    echo "run $i: FAIL"
  fi
}

i=1
while [ "$i" -le "$runs" ]; do
  one_run "$i" &
  # Throttle: with `parallel` jobs in flight, wait for them all before the next
  # batch (bash 3.2 has no `wait -n`).
  if [ $((i % parallel)) -eq 0 ]; then wait; fi
  i=$((i + 1))
done
wait

fails=0
logs=()
i=1
while [ "$i" -le "$runs" ]; do
  if [ -e "$hunt/run-$i.fail" ]; then
    fails=$((fails + 1))
    logs+=("$hunt/run-$i.out")
    for f in "$hunt/run-$i"/*.log; do
      [ -e "$f" ] && logs+=("$f")
    done
  fi
  i=$((i + 1))
done

echo "fails: $fails/$runs"
if [ "$fails" -gt 0 ]; then
  for f in "${logs[@]}"; do echo "  $f"; done
  exit 1
fi
rm -rf "$hunt"
exit 0
