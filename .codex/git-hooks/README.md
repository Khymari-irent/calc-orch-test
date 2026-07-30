# Versioned Git Guards

These hooks add local friction around protected branches. They are not a
security boundary: a user can pass `--no-verify`, replace the hooks, alter local
Git configuration, or push from another clone. Always configure provider-side
protection for `main` and `dev`.

Bootstrap may set `core.hooksPath` to `.codex/git-hooks` only after inspecting
and preserving any existing hook strategy. Do not silently replace another
hooks path. On POSIX, the bootstrap must also ensure the hook entry points are
executable.

Ordinary commits, merges, updates, and deletions on `main`, `master`, and `dev`
are blocked. A new repository has one narrow exception: an Orchestrator may
write a proposal-bound receipt beneath the current Git directory after the user
enters exactly `APPROVE REPOSITORY BOOTSTRAP`.

The commit receipt is `.git/orchestration/receipts/protected-commit` (or the
worktree-specific path reported by `git rev-parse --git-path`) and contains:

```text
format=orchestration-guard-receipt-v1
operation=repository-bootstrap
approval=APPROVE REPOSITORY BOOTSTRAP
preview_sha256=<64-hex-preview-digest>
branch=<main-or-dev>
baseline=<UNBORN-or-exact-HEAD>
expected_tree=<exact-staged-tree>
```

The push receipt at `orchestration/receipts/protected-push` uses
`expected_commit=<exact-tip>` and `remote_baseline=<all-zero-object-id>` in
place of `baseline` and `expected_tree`. Create one receipt per branch push.
Receipts never authorize updates to an existing protected remote branch.

The hooks validate receipt binding, but cannot prove that a chat approval was
authentic. The Orchestrator owns receipt creation and audit correlation; remote
branch protection remains authoritative.
