# Advisory Codex SessionStart hook. This hook intentionally does not claim to
# be an authorization boundary; repository and provider controls remain active.

$ErrorActionPreference = 'SilentlyContinue'

# Consume the hook event without writing transcript or prompt data to disk.
$null = [Console]::In.ReadToEnd()

$messages = [System.Collections.Generic.List[string]]::new()
$messages.Add('Portable orchestration guardrails are active. Treat approval phrases as exact, proposal-bound capabilities.')

$root = (& git rev-parse --show-toplevel 2>$null | Select-Object -First 1)
if ([string]::IsNullOrWhiteSpace($root)) {
    $messages.Add('Git metadata is unavailable; do not bootstrap or mutate a repository until preflight resolves it.')
}
else {
    $branch = (& git symbolic-ref --quiet --short HEAD 2>$null | Select-Object -First 1)
    if ($branch -in @('main', 'master', 'dev')) {
        $messages.Add('The current branch is protected; do not edit, commit, merge, or push directly on it.')
    }
    elseif ([string]::IsNullOrWhiteSpace($branch)) {
        $messages.Add('HEAD is detached; confirm this is an isolated read-only or test worktree before acting.')
    }

    $hooksPath = (& git config --local --get core.hooksPath 2>$null | Select-Object -First 1)
    $absoluteHooksPath = (Join-Path $root '.codex/git-hooks')
    if ($hooksPath -ne '.codex/git-hooks' -and $hooksPath -ne $absoluteHooksPath) {
        $messages.Add('The versioned Git hooks are not the configured core.hooksPath; bootstrap must inspect existing hooks before activating them.')
    }

    if (-not (Test-Path -LiteralPath (Join-Path $root '.codex/policies/workflow.toml') -PathType Leaf)) {
        $messages.Add('Required orchestration policy files are missing; stop instead of improvising.')
    }
}

$messages.Add('Codex hooks and local Git hooks are bypassable guardrails, not a security boundary; require remote branch protection for main and dev.')

@{
    continue = $true
    systemMessage = ($messages -join ' ')
} | ConvertTo-Json -Compress
