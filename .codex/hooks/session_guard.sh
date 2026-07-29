#!/bin/sh
# Advisory Codex SessionStart hook. This hook intentionally does not claim to
# be an authorization boundary; repository and provider controls remain active.

set -u

# Codex sends the hook event as JSON on stdin. The current advisory does not
# need transcript or prompt data, so discard it instead of persisting it.
cat >/dev/null 2>&1 || true

messages="Portable orchestration guardrails are active. Treat approval phrases as exact, proposal-bound capabilities."

root=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$root" ]; then
  messages="$messages Git metadata is unavailable; do not bootstrap or mutate a repository until preflight resolves it."
else
  branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)
  case "$branch" in
    main|master|dev)
      messages="$messages The current branch is protected; do not edit, commit, merge, or push directly on it."
      ;;
    "")
      messages="$messages HEAD is detached; confirm this is an isolated read-only or test worktree before acting."
      ;;
  esac

  hooks_path=$(git config --local --get core.hooksPath 2>/dev/null || true)
  case "$hooks_path" in
    .codex/git-hooks|"$root/.codex/git-hooks") ;;
    *)
      messages="$messages The versioned Git hooks are not the configured core.hooksPath; bootstrap must inspect existing hooks before activating them."
      ;;
  esac

  if [ ! -f "$root/.codex/policies/workflow.toml" ]; then
    messages="$messages Required orchestration policy files are missing; stop instead of improvising."
  fi
fi

messages="$messages Codex hooks and local Git hooks are bypassable guardrails, not a security boundary; require remote branch protection for main and dev."

printf '{"continue":true,"systemMessage":"%s"}\n' "$messages"
