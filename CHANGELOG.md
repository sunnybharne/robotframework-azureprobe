# Changelog

## 0.1.0 — initial alpha (release draft)

- Six Robot Framework keywords for Azure VM existence, normalized properties,
  tags, current power state, and polling for a desired power state.
- Bundled PowerShell script using `Az.Accounts` and `Az.Compute`.
- Explicit subscription and optional tenant selection with process-scoped context
  changes and optional saved context import.
- JSON argument transport, finite timeouts, and distinct missing-resource versus
  execution-error behavior.
- Robot examples, keyword reference, offline tests, and GitHub Actions checks.

Known limitation: live Azure validation has not yet been performed. The initial
automated suite uses test-only module stand-ins. This is a repository version;
no PyPI release is implied.
