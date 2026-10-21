#!/usr/bin/env bats

setup() {
  SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/scripts/doc_path.sh"
  WB="$BATS_TEST_TMPDIR/workbench"
  mkdir -p "$WB/code/foo"
  cat > "$WB/.gitmodules" <<EOF2
[submodule "foo"]
	path = code/foo
	url = x
	branch = main
EOF2
  today="$(date +%F)"
}

@test "doc_path design/plan/record build dated .md paths under docs/plans" {
  cd "$WB"
  for kind in design plan record; do
    run bash "$SCRIPT" "$kind" "My Topic"
    [ "$status" -eq 0 ]
    [ "$output" = "$WB/docs/plans/$today-my-topic-$kind.md" ]
  done
  [ -d "$WB/docs/plans" ]
}

@test "doc_path tasks ends in .json" {
  cd "$WB"
  run bash "$SCRIPT" tasks "My Topic"
  [ "$status" -eq 0 ]
  [ "$output" = "$WB/docs/plans/$today-my-topic-tasks.json" ]
}

@test "doc_path approvals ends in .json" {
  cd "$WB"
  run bash "$SCRIPT" approvals "My Topic"
  [ "$status" -eq 0 ]
  [ "$output" = "$WB/docs/plans/$today-my-topic-approvals.json" ]
}

@test "doc_path research uses the research dir" {
  cd "$WB"
  run bash "$SCRIPT" research "My Topic"
  [ "$status" -eq 0 ]
  [ "$output" = "$WB/docs/research/$today-my-topic.md" ]
  [ -d "$WB/docs/research" ]
}

@test "doc_path from code/<repo> resolves to the workbench docs/plans" {
  cd "$WB/code/foo"
  run bash "$SCRIPT" plan "My Topic"
  [ "$status" -eq 0 ]
  [ "$output" = "$WB/docs/plans/$today-my-topic-plan.md" ]
  [ ! -d "$WB/code/foo/docs" ]
}

@test "doc_path works in a plain git repo" {
  REPO="$BATS_TEST_TMPDIR/plain"
  mkdir -p "$REPO"
  git -C "$REPO" init -q
  top="$(git -C "$REPO" rev-parse --show-toplevel)"
  cd "$REPO"
  run bash "$SCRIPT" design "My Topic"
  [ "$status" -eq 0 ]
  [ "$output" = "$top/docs/plans/$today-my-topic-design.md" ]
}

@test "doc_path fails on an unknown kind with usage" {
  cd "$WB"
  run bash "$SCRIPT" bogus "My Topic"
  [ "$status" -eq 1 ]
  [[ "$output" == *"usage:"* ]]
}

@test "doc_path fails on a missing or empty topic" {
  cd "$WB"
  run bash "$SCRIPT" plan
  [ "$status" -eq 1 ]
  run bash "$SCRIPT" plan ""
  [ "$status" -eq 1 ]
  [[ "$output" == *"usage:"* ]]
}

@test "doc_path fails when the topic has an empty slug" {
  cd "$WB"
  run bash "$SCRIPT" plan "!!!"
  [ "$status" -eq 1 ]
  [[ "$output" == *"usage:"* ]]
}
