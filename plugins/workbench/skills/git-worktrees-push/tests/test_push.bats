#!/usr/bin/env bats

setup() {
  SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/scripts/push.sh"
  WB="$BATS_TEST_TMPDIR/workbench"
  BARE="$BATS_TEST_TMPDIR/remote.git"
  mkdir -p "$WB/code"
  : > "$WB/.gitmodules"
  git init -q --bare "$BARE"
}

make_worktree() {
  local branch="$1" repo="$2" wt
  wt="$WB/.claude/worktrees/$branch/$repo"
  mkdir -p "$wt"
  git init -q -b "$branch" "$wt"
  git -C "$wt" config user.email "test@example.com"
  git -C "$wt" config user.name "Test"
  echo "content" > "$wt/file.txt"
  git -C "$wt" add file.txt
  git -C "$wt" commit -q -m "initial commit"
  git -C "$wt" remote add origin "$BARE"
}

diverge_remote() {
  local branch="$1"
  local scratch="$BATS_TEST_TMPDIR/scratch"
  git clone -q "$BARE" "$scratch"
  git -C "$scratch" checkout -q -b "$branch"
  git -C "$scratch" config user.email "test@example.com"
  git -C "$scratch" config user.name "Test"
  echo "other" > "$scratch/other.txt"
  git -C "$scratch" add other.txt
  git -C "$scratch" commit -q -m "diverging commit"
  git -C "$scratch" push -q origin "$branch"
}

@test "pushes new branch to remote successfully" {
  make_worktree feature-a repo1
  cd "$WB"
  run bash "$SCRIPT" --branch feature-a --repos repo1
  [ "$status" -eq 0 ]
  [[ "$output" == *"repo1"*"ok"* ]]
  run git --git-dir="$BARE" rev-parse feature-a
  [ "$status" -eq 0 ]
  local wt_sha
  wt_sha="$(git -C "$WB/.claude/worktrees/feature-a/repo1" rev-parse HEAD)"
  [ "$output" = "$wt_sha" ]
}

@test "reports failed and exits non-zero when worktree is missing" {
  cd "$WB"
  run bash "$SCRIPT" --branch feature-b --repos repo1
  [ "$status" -ne 0 ]
  [[ "$output" == *"repo1"*"failed"*"no worktree at"* ]]
}

@test "reports failed for a rejected non-fast-forward push" {
  make_worktree feature-c repo1
  diverge_remote feature-c
  cd "$WB"
  run bash "$SCRIPT" --branch feature-c --repos repo1
  [ "$status" -ne 0 ]
  [[ "$output" == *"repo1"*"failed"* ]]
  run git --git-dir="$BARE" rev-parse feature-c
  local wt_sha
  wt_sha="$(git -C "$WB/.claude/worktrees/feature-c/repo1" rev-parse HEAD)"
  [ "$output" != "$wt_sha" ]
}

@test "continues on error across multiple repos and aggregates report" {
  make_worktree feature-d repo1
  cd "$WB"
  run bash "$SCRIPT" --branch feature-d --repos repo1,repo2
  [ "$status" -ne 0 ]
  [[ "$output" == *"repo1"*"ok"* ]]
  [[ "$output" == *"repo2"*"failed"*"no worktree at"* ]]
}

@test "defaults to all_repos when --repos is omitted" {
  echo -e '[submodule "repo1"]\n\tpath = code/repo1\n\turl = https://example.com/repo1.git' > "$WB/.gitmodules"
  make_worktree feature-e repo1
  cd "$WB"
  run bash "$SCRIPT" --branch feature-e
  [ "$status" -eq 0 ]
  [[ "$output" == *"repo1"*"ok"* ]]
}
