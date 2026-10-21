#!/usr/bin/env bats

setup() {
  SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/scripts/refresh.sh"
  WB="$BATS_TEST_TMPDIR/workbench"
  SRC="$BATS_TEST_TMPDIR/src"
  BARE="$BATS_TEST_TMPDIR/remote.git"

  mkdir -p "$WB/code" "$SRC"
  git -C "$SRC" init -q -b main
  git -C "$SRC" config user.email test@test.local
  git -C "$SRC" config user.name test

  echo one > "$SRC/file.txt"
  git -C "$SRC" add file.txt
  git -C "$SRC" commit -q -m "first"

  git clone -q --bare "$SRC" "$BARE"
  git -C "$SRC" remote add origin "$BARE"

  git clone -q "$BARE" "$WB/code/foo"

  cat > "$WB/.gitmodules" <<EOF
[submodule "foo"]
	path = code/foo
	url = $BARE
	branch = main
EOF
}

advance_remote() {
  echo two >> "$SRC/file.txt"
  git -C "$SRC" commit -q -am "second"
  git -C "$SRC" push -q origin main
}

@test "refresh fast-forwards a repo behind its tracked branch" {
  old_sha="$(git -C "$WB/code/foo" rev-parse --short HEAD)"
  advance_remote
  new_sha="$(git -C "$SRC" rev-parse --short HEAD)"

  cd "$WB"
  run bash "$SCRIPT" --repos foo
  [ "$status" -eq 0 ]
  [[ "$output" == *"$old_sha -> $new_sha"* ]]

  checked_out="$(git -C "$WB/code/foo" rev-parse --short HEAD)"
  [ "$checked_out" = "$new_sha" ]
}

@test "refresh reports up to date when nothing changed" {
  cd "$WB"
  run bash "$SCRIPT" --repos foo
  [ "$status" -eq 0 ]
  [[ "$output" == *"foo"*"up to date"* ]]
}

@test "refresh defaults to all repos when --repos omitted" {
  cd "$WB"
  run bash "$SCRIPT"
  [ "$status" -eq 0 ]
  [[ "$output" == *"foo"* ]]
}

@test "refresh reports failed for an unknown repo and exits non-zero" {
  cd "$WB"
  run bash "$SCRIPT" --repos bogus
  [ "$status" -ne 0 ]
  [[ "$output" == *"bogus"*"failed"* ]]
}

@test "refresh continues other repos after one unknown repo fails" {
  cd "$WB"
  run bash "$SCRIPT" --repos foo,bogus
  [ "$status" -ne 0 ]
  [[ "$output" == *"foo"*"up to date"* ]]
  [[ "$output" == *"bogus"*"failed"* ]]
}
