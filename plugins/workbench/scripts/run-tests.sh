#!/usr/bin/env bash
# Run every skill's test suite, one skill per pytest process.
#
# Why per-skill instead of a single `pytest skills`:
# skills ship same-named scripts (`scripts/watch.py`, `scripts/update.py`).
# Their tests sys.path-insert their own scripts dir and `import watch`, so in
# one shared process whichever loads first wins and the other skill tests the
# wrong module. Each skill is
# independent, so a process per skill is both correct and honest.
#
# Usage: run-tests.sh [--only <component>]
# A component is a directory basename: a skill name, hooks or scripts.
#
# A failing component's full output is kept in $RUN_TESTS_LOG_DIR (default:
# <main checkout>/.logs/run-tests/<UTC timestamp>-<pid>/, else a fresh mktemp dir
# under TMPDIR when no main checkout is found) as <component>.log, or
# <component>-bats.log, and its path is printed after the 15-line tail.
# The suites' scratch space is a separate mktemp dir under TMPDIR, outside any
# git checkout, so a fake workbench built in a suite's temp dir cannot be mistaken
# for a repo nested in the real one. Every pytest process gets a private
# --basetemp under it (parallel runs never share pytest's per-user numbered
# basetemp) and every suite, pytest and bats alike, gets it as TMPDIR. Both the
# log dir and the temp dir are removed when everything passes; on a failure both
# are kept and the temp dir is printed as "temp dirs:" after the failure logs.
#
# Exit 0 only if every suite passes; 2 for a usage or environment error.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE" || exit 1

only=""
if [ "${1:-}" = "--only" ]; then
  only="${2:-}"
  if [ -z "$only" ]; then
    echo "run-tests: --only needs a component name" >&2
    exit 2
  fi
fi
if [ -n "$only" ]; then
  found=0
  for d in skills/*/ hooks/ scripts/; do
    [ -d "$d" ] && [ "$(basename "$d")" = "$only" ] && found=1
  done
  if [ "$found" -eq 0 ]; then
    echo "run-tests: no such component $only" >&2
    exit 2
  fi
fi

# Suites that commit need a git identity; CI runners have none, and a host's own
# (derived from the account name) must not be what makes a suite pass.
export GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-workbench-tests}"
export GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-workbench-tests@example.invalid}"
export GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-$GIT_AUTHOR_NAME}"
export GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-$GIT_AUTHOR_EMAIL}"

default_log_dir() {
  local base
  if base="$(python3 "$HERE/scripts/lib/workbench.py" logs 2>/dev/null)" && [ -n "$base" ]; then
    printf '%s/run-tests/%s-%s' "$base" "$(date -u +%Y%m%dT%H%M%SZ)" "$$"
  else
    mktemp -d "${TMPDIR:-/tmp}/run-tests.XXXXXX"
  fi
}
# Made before the log dir so a failure here leaves nothing behind. The path is
# resolved: a trailing slash on TMPDIR would leave a "//" that bats' own paths
# and a suite's PWD then disagree on.
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/run-tests-tmp.XXXXXX")" \
  && TMP_DIR="$(cd "$TMP_DIR" && pwd -P)" \
  && [ -n "$TMP_DIR" ] || {
  echo "run-tests: cannot create a temp dir under ${TMPDIR:-/tmp}" >&2
  exit 2
}
LOG_DIR="${RUN_TESTS_LOG_DIR:-$(default_log_dir)}"
mkdir -p "$LOG_DIR"
export TMPDIR="$TMP_DIR"
# The caller's root override only picks the log dir above. Suites build their own
# fake workbenches and must find those, not the caller's tree.
unset WORKBENCH_ROOT CLAUDE_PROJECT_DIR

# Resolve a pytest that actually runs. `command -v pytest` finds mise's shim,
# which fails with "No version is set for shim" unless a .mise.toml scopes it,
# so a real installed binary is preferred over anything under mise/shims.
resolve_pytest() {
  if [ -n "${PYTEST:-}" ] && [ -x "${PYTEST}" ]; then
    printf '%s' "$PYTEST"; return 0
  fi
  local c
  c="$(command -v pytest 2>/dev/null || true)"
  if [ -n "$c" ] && [[ "$c" != *"/mise/shims/"* ]]; then
    printf '%s' "$c"; return 0
  fi
  for c in "$HOME/.local/share/mise/installs/pipx-pytest"/*/bin/pytest; do
    [ -x "$c" ] && { printf '%s' "$c"; return 0; }
  done
  return 1
}

PYTEST="$(resolve_pytest)" || {
  echo "run-tests: no runnable pytest found. Install with:" >&2
  echo "  mise install pipx:pytest@9.1.1" >&2
  exit 2
}

failed=()
ran=0
total_pass=0

resolve_bats() {
  local c
  c="$(command -v bats 2>/dev/null || true)"
  if [ -n "$c" ] && [[ "$c" != *"/mise/shims/"* ]]; then printf '%s' "$c"; return 0; fi
  # mise unpacks the bats tarball, so the binary sits under
  # installs/bats/<ver>/bats-core-<ver>/bin/bats, not installs/bats/<ver>/bin.
  for c in "$HOME/.local/share/mise/installs/bats"/*/bin/bats \
           "$HOME/.local/share/mise/installs/bats"/*/*/bin/bats; do
    [ -x "$c" ] && { printf '%s' "$c"; return 0; }
  done
  return 1
}
BATS="$(resolve_bats || true)"

for d in skills/*/ hooks/ scripts/; do
  name="$(basename "$d")"
  [ -z "$only" ] || [ "$name" = "$only" ] || continue
  [ -d "$d/tests" ] || continue
  ran=$((ran + 1))

  # --- pytest, if this skill has any python tests
  if compgen -G "$d/tests/test_*.py" >/dev/null; then
    out="$("$PYTEST" "$d" -q --basetemp "$TMP_DIR/$name" 2>&1)"
    rc=$?
    line="$(printf '%s' "$out" | tail -n 1)"
    if [ $rc -eq 0 ]; then
      printf '  PASS  %-34s %s\n' "$name" "$line"
      n="$(printf '%s' "$line" | grep -oE '^[0-9]+' || echo 0)"
      total_pass=$((total_pass + n))
    else
      printf '  FAIL  %-34s %s\n' "$name" "$line"
      printf '%s\n' "$out" | tail -n 15 | sed 's/^/        /'
      printf '%s\n' "$out" > "$LOG_DIR/$name.log"
      printf '        full output: %s\n' "$LOG_DIR/$name.log"
      failed+=("$name")
    fi
  fi

  # --- bats, if this skill has any shell tests
  if compgen -G "$d/tests/*.bats" >/dev/null; then
    if [ -z "$BATS" ]; then
      printf '  SKIP  %-34s %s\n' "$name" "bats not installed (mise install bats@1.13.0)"
      continue
    fi
    out="$("$BATS" "$d"/tests/*.bats 2>&1)"
    rc=$?
    line="$(printf '%s' "$out" | tail -n 1)"
    if [ $rc -eq 0 ]; then
      printf '  PASS  %-34s bats: %s\n' "$name" "$line"
    else
      printf '  FAIL  %-34s bats: %s\n' "$name" "$line"
      printf '%s\n' "$out" | tail -n 15 | sed 's/^/        /'
      printf '%s\n' "$out" > "$LOG_DIR/$name-bats.log"
      printf '        full output: %s\n' "$LOG_DIR/$name-bats.log"
      failed+=("$name(bats)")
    fi
  fi
done

echo
echo "components with tests: $ran   assertions passed: $total_pass"
if [ ${#failed[@]} -gt 0 ]; then
  echo "FAILED: ${failed[*]}"
  echo "failure logs: $LOG_DIR"
  echo "temp dirs: $TMP_DIR"
  exit 1
fi
rm -rf "$LOG_DIR" "$TMP_DIR"
echo "all green"
