#!/usr/bin/env bash
# Plain-bash fallback for test_push.bats, for use when bats is unavailable.
set -u

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/scripts/push.sh"
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

assert_eq() {
  if [ "$1" = "$2" ]; then
    ok "$3"
  else
    fail "$3 (expected [$2] got [$1])"
  fi
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

new_workbench() {
  local wb="$TMPDIR_ROOT/workbench_$$_$RANDOM"
  mkdir -p "$wb/code"
  : > "$wb/.gitmodules"
  echo "$wb"
}

make_worktree() {
  local wb="$1" branch="$2" repo="$3" bare="$4" wt
  wt="$wb/.worktrees/$branch/$repo"
  mkdir -p "$wt"
  git init -q -b "$branch" "$wt"
  git -C "$wt" config user.email "test@example.com"
  git -C "$wt" config user.name "Test"
  echo "content" > "$wt/file.txt"
  git -C "$wt" add file.txt
  git -C "$wt" commit -q -m "initial commit"
  git -C "$wt" remote add origin "$bare"
}

diverge_remote() {
  local bare="$1" branch="$2"
  local scratch="$TMPDIR_ROOT/scratch_$$_$RANDOM"
  git clone -q "$bare" "$scratch"
  git -C "$scratch" checkout -q -b "$branch"
  git -C "$scratch" config user.email "test@example.com"
  git -C "$scratch" config user.name "Test"
  echo "other" > "$scratch/other.txt"
  git -C "$scratch" add other.txt
  git -C "$scratch" commit -q -m "diverging commit"
  git -C "$scratch" push -q origin "$branch"
}

# --- test 1: successful push ---
WB="$(new_workbench)"
BARE="$TMPDIR_ROOT/remote1.git"
git init -q --bare "$BARE"
make_worktree "$WB" feature-a repo1 "$BARE"
out="$(cd "$WB" && bash "$SCRIPT" --branch feature-a --repos repo1)"
status=$?
assert_status "$status" 0 "successful push exits 0"
assert_contains "$out" "repo1" "successful push report mentions repo1"
assert_contains "$out" "ok" "successful push report mentions ok"
remote_sha="$(git --git-dir="$BARE" rev-parse feature-a 2>/dev/null)"
wt_sha="$(git -C "$WB/.worktrees/feature-a/repo1" rev-parse HEAD)"
assert_eq "$remote_sha" "$wt_sha" "remote branch matches worktree HEAD after push"

# --- test 2: missing worktree ---
WB="$(new_workbench)"
out="$(cd "$WB" && bash "$SCRIPT" --branch feature-b --repos repo1)"
status=$?
assert_status "$status" 1 "missing worktree exits non-zero"
assert_contains "$out" "repo1" "missing worktree report mentions repo1"
assert_contains "$out" "failed" "missing worktree report mentions failed"
assert_contains "$out" "no worktree at" "missing worktree report mentions reason"

# --- test 3: rejected non-fast-forward push ---
WB="$(new_workbench)"
BARE="$TMPDIR_ROOT/remote3.git"
git init -q --bare "$BARE"
make_worktree "$WB" feature-c repo1 "$BARE"
diverge_remote "$BARE" feature-c
remote_sha_before="$(git --git-dir="$BARE" rev-parse feature-c)"
out="$(cd "$WB" && bash "$SCRIPT" --branch feature-c --repos repo1)"
status=$?
assert_status "$status" 1 "rejected push exits non-zero"
assert_contains "$out" "repo1" "rejected push report mentions repo1"
assert_contains "$out" "failed" "rejected push report mentions failed"
remote_sha_after="$(git --git-dir="$BARE" rev-parse feature-c)"
assert_eq "$remote_sha_after" "$remote_sha_before" "remote branch unchanged after rejected push"

# --- test 4: continue on error, aggregate report ---
WB="$(new_workbench)"
BARE="$TMPDIR_ROOT/remote4.git"
git init -q --bare "$BARE"
make_worktree "$WB" feature-d repo1 "$BARE"
out="$(cd "$WB" && bash "$SCRIPT" --branch feature-d --repos repo1,repo2)"
status=$?
assert_status "$status" 1 "mixed result exits non-zero"
assert_contains "$out" "repo1" "mixed result report mentions repo1"
assert_contains "$out" "repo2" "mixed result report mentions repo2"

# --- test 5: default to all_repos ---
WB="$(new_workbench)"
BARE="$TMPDIR_ROOT/remote5.git"
git init -q --bare "$BARE"
printf '[submodule "repo1"]\n\tpath = code/repo1\n\turl = https://example.com/repo1.git\n' > "$WB/.gitmodules"
make_worktree "$WB" feature-e repo1 "$BARE"
out="$(cd "$WB" && bash "$SCRIPT" --branch feature-e)"
status=$?
assert_status "$status" 0 "default repos exits 0"
assert_contains "$out" "repo1" "default repos report mentions repo1"

echo "----"
echo "passed: $PASS failed: $FAIL"
[ "$FAIL" -eq 0 ]
