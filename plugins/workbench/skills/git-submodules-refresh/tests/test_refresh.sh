#!/usr/bin/env bash
# Plain-bash fallback for test_refresh.bats, for use when bats is unavailable.
set -u

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/scripts/refresh.sh"
TMPDIR_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

PASS=0
FAIL=0

ok() {
  PASS=$((PASS + 1))
  echo "ok - $1"
}

fail() {
  FAIL=$((FAIL + 1))
  echo "not ok - $1"
}

assert_status() {
  if [ "$1" -eq "$2" ]; then
    ok "$3"
  else
    fail "$3 (expected status $2 got $1)"
  fi
}

assert_contains() {
  case "$1" in
    *"$2"*) ok "$3" ;;
    *) fail "$3 (expected [$1] to contain [$2])" ;;
  esac
}

assert_eq() {
  if [ "$1" = "$2" ]; then
    ok "$3"
  else
    fail "$3 (expected [$2] got [$1])"
  fi
}

new_fixture() {
  local wb="$TMPDIR_ROOT/workbench_$$_$RANDOM"
  local src="$TMPDIR_ROOT/src_$$_$RANDOM"
  local bare="$TMPDIR_ROOT/remote_$$_$RANDOM.git"

  mkdir -p "$wb/code" "$src"
  git -C "$src" init -q -b main
  git -C "$src" config user.email test@test.local
  git -C "$src" config user.name test

  echo one > "$src/file.txt"
  git -C "$src" add file.txt
  git -C "$src" commit -q -m "first"

  git clone -q --bare "$src" "$bare"
  git -C "$src" remote add origin "$bare"

  git clone -q "$bare" "$wb/code/foo"

  cat > "$wb/.gitmodules" <<EOF
[submodule "foo"]
	path = code/foo
	url = $bare
	branch = main
EOF

  echo "$wb|$src|$bare"
}

advance_remote() {
  local src="$1"
  echo two >> "$src/file.txt"
  git -C "$src" commit -q -am "second"
  git -C "$src" push -q origin main
}

fixture="$(new_fixture)"
WB="${fixture%%|*}"
rest="${fixture#*|}"
SRC="${rest%%|*}"

old_sha="$(git -C "$WB/code/foo" rev-parse --short HEAD)"
advance_remote "$SRC"
new_sha="$(git -C "$SRC" rev-parse --short HEAD)"

out="$(cd "$WB" && bash "$SCRIPT" --repos foo 2>&1)"
status=$?
assert_status "$status" 0 "refresh exits 0 on successful fast-forward"
assert_contains "$out" "$old_sha -> $new_sha" "refresh reports old -> new SHA"

checked_out="$(git -C "$WB/code/foo" rev-parse --short HEAD)"
assert_eq "$checked_out" "$new_sha" "refresh fast-forwards the checkout"

out="$(cd "$WB" && bash "$SCRIPT" --repos foo 2>&1)"
status=$?
assert_status "$status" 0 "refresh exits 0 when up to date"
assert_contains "$out" "up to date" "refresh reports up to date on second run"

out="$(cd "$WB" && bash "$SCRIPT" 2>&1)"
status=$?
assert_status "$status" 0 "refresh defaults to all repos"
assert_contains "$out" "foo" "refresh default run mentions foo"

out="$(cd "$WB" && bash "$SCRIPT" --repos bogus 2>&1)"
status=$?
assert_status "$status" 1 "refresh exits non-zero for unknown repo"
assert_contains "$out" "bogus" "refresh report mentions unknown repo"
assert_contains "$out" "failed" "refresh report marks unknown repo failed"

out="$(cd "$WB" && bash "$SCRIPT" --repos foo,bogus 2>&1)"
status=$?
assert_status "$status" 1 "mixed known/unknown repos exits non-zero"
assert_contains "$out" "up to date" "known repo still reported when sibling fails"

echo "----"
echo "passed: $PASS failed: $FAIL"
[ "$FAIL" -eq 0 ]
