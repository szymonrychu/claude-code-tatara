---
paths:
  - "**/*.go"
  - "**/go.mod"
---

# Go

Verify before claiming done:
`gofumpt -l . && go build ./... && go vet ./... && golangci-lint run && go test ./...`
(or `mise run lint && mise run test` where the repo defines them).

- Run `go doc <pkg>.<Symbol>` before using a stdlib or third-party API you are
  not certain of. Cheaper than a wrong guess and it is the main defence against
  invented signatures.
- Wrap errors: `fmt.Errorf("context: %w", err)`. Match with `errors.Is` /
  `errors.As`. Never discard with `_`.
- Every goroutine takes a `context.Context` and has a defined exit path. Prefer
  `errgroup` over a bare `go func`.
- Table-driven tests with `t.Run`.
- Go modules only, no GOPATH.
