#!/bin/sh
# Shared helpers for the versioned orchestration Git hooks.

guard_git_dir() {
  git rev-parse --git-dir 2>/dev/null
}

guard_receipt_path() {
  git rev-parse --git-path "orchestration/receipts/$1" 2>/dev/null
}

guard_branch() {
  git symbolic-ref --quiet --short HEAD 2>/dev/null
}

guard_production_branch() {
  git config --get orchestration.productionBranch 2>/dev/null || printf '%s\n' main
}

guard_integration_branch() {
  git config --get orchestration.integrationBranch 2>/dev/null || printf '%s\n' dev
}

guard_is_protected_branch() {
  candidate=$1
  production=$(guard_production_branch) || return 1
  integration=$(guard_integration_branch) || return 1
  [ "$candidate" = "$production" ] \
    || [ "$candidate" = "$integration" ] \
    || [ "$candidate" = main ] \
    || [ "$candidate" = master ] \
    || [ "$candidate" = dev ]
}

guard_protected_branch_from_ref() {
  case "$1" in
    refs/heads/*) candidate=${1#refs/heads/} ;;
    *) return 1 ;;
  esac
  guard_is_protected_branch "$candidate" || return 1
  printf '%s\n' "$candidate"
}

guard_receipt_value() {
  receipt_file=$1
  receipt_key=$2
  # A duplicated key is invalid; never source a receipt as shell code.
  receipt_count=$(grep -c "^${receipt_key}=" "$receipt_file" 2>/dev/null || true)
  [ "$receipt_count" = "1" ] || return 1
  sed -n "s/^${receipt_key}=//p" "$receipt_file"
}

guard_receipt_has() {
  receipt_file=$1
  receipt_key=$2
  receipt_expected=$3
  receipt_actual=$(guard_receipt_value "$receipt_file" "$receipt_key") || return 1
  [ "$receipt_actual" = "$receipt_expected" ]
}

guard_receipt_header_is_valid() {
  receipt_file=$1
  [ -f "$receipt_file" ] || return 1
  guard_receipt_has "$receipt_file" format orchestration-guard-receipt-v1 || return 1
  guard_receipt_has "$receipt_file" operation repository-bootstrap || return 1
  guard_receipt_has "$receipt_file" approval "APPROVE REPOSITORY BOOTSTRAP" || return 1
  preview=$(guard_receipt_value "$receipt_file" preview_sha256) || return 1
  case "$preview" in
    *[!0-9a-fA-F]*|"") return 1 ;;
  esac
  [ "${#preview}" -eq 64 ]
}

guard_empty_tree() {
  git mktree </dev/null 2>/dev/null
}

guard_is_parentless_empty_commit() {
  candidate=$1
  [ -n "$candidate" ] || return 1
  commit_line=$(git rev-list --parents -n 1 "$candidate" 2>/dev/null) || return 1
  [ "$commit_line" = "$candidate" ] || return 1
  candidate_tree=$(git show -s --format=%T "$candidate" 2>/dev/null) || return 1
  empty_tree=$(guard_empty_tree) || return 1
  [ "$candidate_tree" = "$empty_tree" ]
}

guard_is_initial_dev_bootstrap_commit() {
  candidate=$1
  commit_line=$(git rev-list --parents -n 1 "$candidate" 2>/dev/null) || return 1
  set -- $commit_line
  [ "$#" -eq 2 ] || return 1
  [ "$1" = "$candidate" ] || return 1
  parent=$2
  guard_is_parentless_empty_commit "$parent" || return 1
  commit_count=$(git rev-list --count "$candidate" 2>/dev/null) || return 1
  [ "$commit_count" = "2" ]
}

guard_error() {
  printf '%s\n' "orchestration guard: $*" >&2
}
