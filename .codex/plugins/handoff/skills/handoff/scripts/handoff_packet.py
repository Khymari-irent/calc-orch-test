#!/usr/bin/env python3
"""Validate durable orchestration handoff packets before an agent is spawned."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any


ROLES = {
    "devops_prd",
    "devops_developer",
    "devops_reviewer",
    "devops_tester",
    "devops_security",
    "devops_docs",
}
HANDOFF_SKILL = ".codex/plugins/handoff/skills/handoff/SKILL.md"
DIRTY_OWNERS = ROLES | {"devops_orchestrator", "user"}
PROTECTED_BRANCHES = {
    "main",
    "master",
    "dev",
    "develop",
    "development",
    "integration",
    "production",
    "prod",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PERSONAL_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+|/"
    + r"Users/[^/\s]+|/"
    + r"home/[^/\s]+)"
)
PARENT_DEPENDENCY_RE = re.compile(
    r"\b(?:see|read|use|refer to|continue from|as stated in|as discussed in)\s+"
    r"(?:the\s+)?(?:parent|previous|original|earlier)\s+"
    r"(?:chat|conversation|thread|transcript|messages?)\b|"
    r"\b(?:context|details?|requirements?|approval)\s+"
    r"(?:is|are|comes?|came)\s+from\s+(?:the\s+)?"
    r"(?:parent|previous|original|earlier)\s+(?:chat|conversation|thread|messages?)\b",
    re.IGNORECASE,
)
SECRET_RE = re.compile(
    r"(?:-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"\bAKIA[0-9A-Z]{16}\b|\bgh[opusr]_[A-Za-z0-9_]{20,}\b|"
    r"\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*[\"']?[^ \r\n\"']{12,})",
    re.IGNORECASE,
)
RAW_TRANSCRIPT_RE = re.compile(
    r"(?:^|\n)##\s+Raw (?:Chat )?Transcript\b|"
    r"(?:^|\n)(?:User|Assistant|System):[^\n]*\n"
    r"(?:User|Assistant|System):",
    re.IGNORECASE,
)
REUSABLE_APPROVAL_RE = re.compile(
    r"\b(?:standing|blanket|reusable|permanent)\s+approval\b|"
    r"\bapproved\s+(?:forever|for all future)\b",
    re.IGNORECASE,
)
FORBIDDEN_COMMAND_RE = re.compile(
    r"\b(?:git\s+(?:reset\s+--hard|clean\s+-[^\s]*f|stash|checkout\s+--)|"
    r"rm\s+-rf|Remove-Item\b[^\r\n]*-Recurse)\b",
    re.IGNORECASE,
)
FORBIDDEN_EFFECT_RE = re.compile(
    r"\b(?:merge(?:\s+to|\s+into)?\s+(?:main|master|production)|"
    r"deploy(?:ment)?\s+(?:to\s+)?production|risk acceptance|accept security risk|"
    r"delete repository|force[- ]push)\b",
    re.IGNORECASE,
)
JSON_BLOCK_RE = re.compile(
    r"```handoff-json[ \t]*\r?\n(?P<body>.*?)\r?\n```", re.DOTALL
)
PATCH_BLOCK_RE = re.compile(
    r"## Exact patch[ \t]*\r?\n+```diff[ \t]*\r?\n(?P<body>.*?)\r?\n```",
    re.DOTALL,
)
FULL_FILE_BLOCK_RE = re.compile(
    r"## Full-file addition[ \t]*\r?\n+```[^\r\n]*\r?\n(?P<body>.*?)\r?\n```",
    re.DOTALL,
)


class ValidationError(Exception):
    """One concrete pre-spawn validation failure."""


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise ValidationError(f"cannot read digest source {path}: {exc}") from exc


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise ValidationError(f"cannot execute git: {exc}") from exc
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValidationError(f"git {' '.join(args)} failed: {detail}")
    return result


def _required(mapping: dict[str, Any], key: str, label: str) -> Any:
    if key not in mapping:
        raise ValidationError(f"missing required field: {label}.{key}")
    return mapping[key]


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be an object")
    return value


def _list(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be a list")
    if nonempty and not value:
        raise ValidationError(f"{label} must not be empty")
    return value


def _string(value: Any, label: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be a string")
    if nonempty and not value.strip():
        raise ValidationError(f"{label} must not be empty")
    if "REPLACE" in value:
        raise ValidationError(f"{label} still contains a template placeholder")
    return value


def _digest(value: Any, label: str, *, allow_missing: bool = False) -> str:
    text = _string(value, label)
    if allow_missing and text == "MISSING":
        return text
    if not DIGEST_RE.fullmatch(text):
        raise ValidationError(f"{label} must be a sha256 digest")
    return text


def _repo_path(
    root: Path,
    value: Any,
    label: str,
    *,
    must_exist: bool = False,
    require_file: bool = False,
) -> tuple[str, Path]:
    text = _string(value, label)
    if PERSONAL_PATH_RE.search(text) or Path(text).is_absolute():
        raise ValidationError(f"{label} must be repository-relative, not a personal absolute path")
    normalized = text.replace("\\", "/")
    if normalized.startswith("../") or "/../" in f"/{normalized}/":
        raise ValidationError(f"{label} escapes the repository")
    candidate = (root / normalized).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValidationError(f"{label} escapes the repository") from exc
    if must_exist and not candidate.exists():
        raise ValidationError(f"{label} does not exist: {normalized}")
    if require_file and not candidate.is_file():
        raise ValidationError(f"{label} is not a file: {normalized}")
    return normalized, candidate


def parse_handoff(path: Path) -> tuple[dict[str, Any], str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValidationError(f"cannot read handoff document: {exc}") from exc
    matches = list(JSON_BLOCK_RE.finditer(text))
    if len(matches) != 1:
        raise ValidationError("handoff must contain exactly one fenced handoff-json block")
    try:
        value = json.loads(matches[0].group("body"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"handoff-json is invalid JSON at line {exc.lineno}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValidationError("handoff-json must contain a JSON object")
    return value, text


def _parse_dirty(root: Path) -> dict[str, str]:
    output = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    tokens = output.split(b"\0")
    dirty: dict[str, str] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token:
            continue
        decoded = token.decode("utf-8", errors="surrogateescape")
        if len(decoded) < 4:
            raise ValidationError("git returned an unreadable dirty-worktree entry")
        status = decoded[:2]
        path = decoded[3:].replace("\\", "/")
        dirty[path] = status
        if status[0] in {"R", "C"} and index < len(tokens):
            original = tokens[index].decode("utf-8", errors="surrogateescape").replace("\\", "/")
            index += 1
            dirty[original] = status
    return dirty


def _commit_exists(root: Path, value: Any, label: str, *, allow_empty: bool = False) -> str:
    text = _string(value, label, nonempty=not allow_empty)
    if allow_empty and not text:
        return ""
    if not SHA_RE.fullmatch(text):
        raise ValidationError(f"{label} must be a full 40- or 64-character Git commit SHA")
    result = _git(root, "cat-file", "-e", f"{text}^{{commit}}", check=False)
    if result.returncode:
        raise ValidationError(f"{label} does not identify a commit in this repository")
    return text


def _validate_approval_command(root: Path, command: str) -> None:
    registry_path = root / ".codex" / "policies" / "commands.toml"
    try:
        with registry_path.open("rb") as handle:
            registry = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValidationError(f"cannot read canonical approval registry: {exc}") from exc
    if registry.get("case_sensitive") is not True or registry.get("full_line_match") is not True:
        raise ValidationError("canonical approval registry must require case-sensitive full-line matching")
    matches: list[str] = []
    for entry in registry.get("command", []):
        if not isinstance(entry, dict):
            continue
        pattern = entry.get("pattern")
        key = entry.get("key")
        if not isinstance(pattern, str) or not isinstance(key, str):
            continue
        try:
            matched = re.fullmatch(pattern, command) is not None
        except re.error as exc:
            raise ValidationError(f"canonical approval pattern {key} is invalid: {exc}") from exc
        if matched:
            matches.append(key)
    if len(matches) != 1:
        raise ValidationError(
            "proposal.approval_command must match exactly one canonical commands.toml pattern"
        )


def _verify_digest_map(
    root: Path,
    mapping: Any,
    label: str,
    *,
    base_sha: str | None = None,
) -> dict[str, str]:
    values = _mapping(mapping, label)
    if not values:
        raise ValidationError(f"{label} must contain at least one path digest")
    normalized: dict[str, str] = {}
    for raw_path, raw_digest in values.items():
        path, candidate = _repo_path(root, raw_path, f"{label} path")
        expected = _digest(raw_digest, f"{label}.{path}", allow_missing=base_sha is not None)
        if base_sha is None:
            if not candidate.is_file():
                raise ValidationError(f"{label}.{path} cannot be verified because the file is missing")
            actual = sha256_file(candidate)
        else:
            result = _git(root, "show", f"{base_sha}:{path}", check=False)
            if result.returncode:
                actual = "MISSING"
            else:
                actual = sha256_bytes(result.stdout)
        if actual != expected:
            raise ValidationError(f"{label}.{path} is stale: expected {expected}, found {actual}")
        normalized[path] = expected
    return normalized


def _verify_evidence(root: Path, evidence: Any) -> None:
    for index, item in enumerate(_list(evidence, "evidence_references")):
        entry = _mapping(item, f"evidence_references[{index}]")
        _, path = _repo_path(
            root,
            _required(entry, "path", f"evidence_references[{index}]"),
            f"evidence_references[{index}].path",
            must_exist=True,
            require_file=True,
        )
        expected = _digest(
            _required(entry, "digest", f"evidence_references[{index}]"),
            f"evidence_references[{index}].digest",
        )
        _string(
            _required(entry, "description", f"evidence_references[{index}]"),
            f"evidence_references[{index}].description",
        )
        actual = sha256_file(path)
        if actual != expected:
            raise ValidationError(
                f"evidence_references[{index}].digest is stale: expected {expected}, found {actual}"
            )


def _verify_change(root: Path, change: dict[str, Any], text: str, allowed: set[str]) -> None:
    mode = _string(_required(change, "mode", "change"), "change.mode")
    artifact_path = _string(
        _required(change, "artifact_path", "change"), "change.artifact_path", nonempty=False
    )
    artifact_digest = _string(
        _required(change, "artifact_digest", "change"), "change.artifact_digest", nonempty=False
    )
    patch_digest = _string(
        _required(change, "patch_sha256", "change"), "change.patch_sha256", nonempty=False
    )
    if mode == "inline_patch":
        match = PATCH_BLOCK_RE.search(text)
        if not match:
            raise ValidationError("change.mode inline_patch requires a complete ## Exact patch diff block")
        if not patch_digest:
            raise ValidationError("change.patch_sha256 is required for inline_patch")
        _digest(patch_digest, "change.patch_sha256")
        actual = sha256_text(match.group("body"))
        if actual != patch_digest:
            raise ValidationError(
                f"change.patch_sha256 is stale: expected {patch_digest}, found {actual}"
            )
        patch_paths = {
            value.replace("\\", "/")
            for value in re.findall(r"^(?:---|\+\+\+)\s+(?:a/|b/)?(.+)$", match.group("body"), re.MULTILINE)
            if value != "/dev/null"
        }
        outside = sorted(patch_paths - allowed)
        if outside:
            raise ValidationError(f"exact patch touches path outside scope.allowed_paths: {outside[0]}")
    elif mode == "full_file":
        match = FULL_FILE_BLOCK_RE.search(text)
        if not match:
            raise ValidationError("change.mode full_file requires a complete ## Full-file addition block")
        path, _ = _repo_path(root, artifact_path, "change.artifact_path")
        if path not in allowed:
            raise ValidationError("change.artifact_path is outside scope.allowed_paths")
        if not patch_digest:
            raise ValidationError("change.patch_sha256 is required for full_file")
        _digest(patch_digest, "change.patch_sha256")
        actual = sha256_text(match.group("body"))
        if actual != patch_digest:
            raise ValidationError(
                f"change.patch_sha256 is stale: expected {patch_digest}, found {actual}"
            )
    elif mode == "artifact_reference":
        _, path = _repo_path(
            root,
            artifact_path,
            "change.artifact_path",
            must_exist=True,
            require_file=True,
        )
        expected = _digest(artifact_digest, "change.artifact_digest")
        actual = sha256_file(path)
        if actual != expected:
            raise ValidationError(
                f"change.artifact_digest is stale: expected {expected}, found {actual}"
            )
    else:
        raise ValidationError("change.mode must be inline_patch, full_file, or artifact_reference")


def validate_handoff(repo_root: Path, handoff_path: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    try:
        handoff = handoff_path.resolve()
        handoff_relative = handoff.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValidationError("handoff document must be inside the repository") from exc
    expected_prefix = ".orchestration/handoffs/"
    if not handoff_relative.startswith(expected_prefix):
        raise ValidationError(
            "handoff document must be under .orchestration/handoffs/mvpNNN/sliceNNN/<agent>/"
        )
    packet, text = parse_handoff(handoff)
    if PERSONAL_PATH_RE.search(text):
        raise ValidationError("handoff contains a personal absolute path runtime dependency")
    if PARENT_DEPENDENCY_RE.search(text):
        raise ValidationError("handoff relies on parent conversation history")
    if RAW_TRANSCRIPT_RE.search(text):
        raise ValidationError("handoff contains a forbidden raw conversation transcript")
    if REUSABLE_APPROVAL_RE.search(text):
        raise ValidationError("handoff contains a forbidden reusable approval")
    if SECRET_RE.search(text):
        raise ValidationError("handoff appears to contain a credential or secret")

    if _required(packet, "schema_version", "handoff") != 1:
        raise ValidationError("schema_version must be 1")
    handoff_id = _string(_required(packet, "handoff_id", "handoff"), "handoff_id")
    role = _string(_required(packet, "role", "handoff"), "role")
    if role not in ROLES:
        raise ValidationError(f"role is not a supported orchestration role: {role}")
    _string(_required(packet, "objective", "handoff"), "objective")

    identifiers = _mapping(_required(packet, "identifiers", "handoff"), "identifiers")
    mvp = _string(_required(identifiers, "mvp", "identifiers"), "identifiers.mvp")
    slice_id = _string(_required(identifiers, "slice", "identifiers"), "identifiers.slice")
    cycle = _string(_required(identifiers, "cycle", "identifiers"), "identifiers.cycle")
    _list(_required(identifiers, "findings", "identifiers"), "identifiers.findings")
    if not re.fullmatch(r"mvp\d{3}", mvp):
        raise ValidationError("identifiers.mvp must use mvpNNN")
    if not re.fullmatch(r"slice\d{3}", slice_id):
        raise ValidationError("identifiers.slice must use sliceNNN")
    if not re.fullmatch(r"cycle\d{3}", cycle):
        raise ValidationError("identifiers.cycle must use cycleNNN")
    path_match = re.fullmatch(
        r"\.orchestration/handoffs/(mvp\d{3})/(slice\d{3})/"
        r"(devops_(?:prd|developer|reviewer|tester|security|docs))/handoff(\d{3})\.md",
        handoff_relative,
    )
    if not path_match:
        raise ValidationError("handoff path does not match the canonical zero-padded pattern")
    if (path_match.group(1), path_match.group(2), path_match.group(3)) != (mvp, slice_id, role):
        raise ValidationError("handoff path conflicts with its MVP, slice, or role identifiers")
    expected_id = f"{mvp}-{slice_id}-{role}-handoff{path_match.group(4)}"
    if handoff_id != expected_id:
        raise ValidationError(f"handoff_id must be {expected_id}")

    proposal = _mapping(_required(packet, "proposal", "handoff"), "proposal")
    _string(_required(proposal, "id", "proposal"), "proposal.id")
    _, proposal_path = _repo_path(
        root,
        _required(proposal, "artifact_path", "proposal"),
        "proposal.artifact_path",
        must_exist=True,
        require_file=True,
    )
    expected_proposal_digest = _digest(
        _required(proposal, "digest", "proposal"), "proposal.digest"
    )
    actual_proposal_digest = sha256_file(proposal_path)
    if actual_proposal_digest != expected_proposal_digest:
        raise ValidationError(
            "proposal.digest is stale: "
            f"expected {expected_proposal_digest}, found {actual_proposal_digest}"
        )
    approval_required = _required(proposal, "approval_required", "proposal")
    if not isinstance(approval_required, bool):
        raise ValidationError("proposal.approval_required must be true or false")
    approval_command = _string(
        _required(proposal, "approval_command", "proposal"),
        "proposal.approval_command",
        nonempty=approval_required,
    )
    if approval_required:
        if "\n" in approval_command or approval_command.strip() != approval_command:
            raise ValidationError("proposal.approval_command must be one exact full-line literal")
        if approval_command in {"APPROVED", "YES", "APPROVE", "NOT_REQUIRED"}:
            raise ValidationError("proposal.approval_command is not a bound literal approval")
        _validate_approval_command(root, approval_command)
    elif approval_command not in {"", "NOT_REQUIRED"}:
        raise ValidationError(
            "proposal.approval_command must be empty or NOT_REQUIRED when approval is not required"
        )
    authorized_effect = _string(
        _required(proposal, "authorized_effect", "proposal"), "proposal.authorized_effect"
    )
    if FORBIDDEN_EFFECT_RE.search(authorized_effect):
        raise ValidationError("proposal.authorized_effect exceeds an orchestration agent's authority")

    scope = _mapping(_required(packet, "scope", "handoff"), "scope")
    allowed_values = _list(
        _required(scope, "allowed_paths", "scope"), "scope.allowed_paths"
    )
    forbidden_values = _list(
        _required(scope, "forbidden_paths", "scope"), "scope.forbidden_paths"
    )
    identical_values = _list(
        _required(scope, "byte_identical_paths", "scope"), "scope.byte_identical_paths"
    )
    allowed = {_repo_path(root, item, "scope.allowed_paths item")[0] for item in allowed_values}
    forbidden = {
        _repo_path(root, item, "scope.forbidden_paths item")[0] for item in forbidden_values
    }
    identical = {
        _repo_path(root, item, "scope.byte_identical_paths item")[0]
        for item in identical_values
    }
    if len(allowed) != len(allowed_values):
        raise ValidationError("scope.allowed_paths contains a duplicate path")
    overlap = allowed & (forbidden | identical)
    if overlap:
        raise ValidationError(f"allowed path is also forbidden or byte-identical: {sorted(overlap)[0]}")
    if role in {"devops_developer", "devops_docs", "devops_prd"} and not allowed:
        raise ValidationError(f"scope.allowed_paths must not be empty for {role}")
    if role in {"devops_reviewer", "devops_tester", "devops_security"} and allowed:
        raise ValidationError(f"{role} is read-only and must have an empty allowed-path list")

    git = _mapping(_required(packet, "git", "handoff"), "git")
    branch = _string(_required(git, "branch", "git"), "git.branch")
    current_branch = _git(root, "branch", "--show-current").stdout.decode().strip() or "DETACHED"
    if branch != current_branch:
        raise ValidationError(f"git.branch is stale: expected {branch}, found {current_branch}")
    base_sha = _commit_exists(root, _required(git, "base_sha", "git"), "git.base_sha")
    candidate_sha = _commit_exists(
        root, _required(git, "candidate_sha", "git"), "git.candidate_sha", allow_empty=True
    )
    target_sha = _commit_exists(
        root, _required(git, "target_sha", "git"), "git.target_sha", allow_empty=True
    )
    if not candidate_sha and not target_sha:
        raise ValidationError("one of git.candidate_sha or git.target_sha must identify an immutable commit")
    head_sha = _git(root, "rev-parse", "HEAD").stdout.decode().strip()
    assigned_sha = candidate_sha or target_sha
    if assigned_sha != head_sha:
        raise ValidationError(
            f"assigned candidate or target SHA is stale: expected {assigned_sha}, found HEAD {head_sha}"
        )
    ancestor = _git(root, "merge-base", "--is-ancestor", base_sha, head_sha, check=False)
    if ancestor.returncode:
        raise ValidationError("git.base_sha is not an ancestor of the assigned HEAD")
    if role == "devops_developer" and (
        branch.lower() in PROTECTED_BRANCHES
        or branch.lower().startswith(("release/", "production/", "prod/"))
    ):
        raise ValidationError(f"protected-branch edits cannot be assigned to Developer: {branch}")

    change = _mapping(_required(packet, "change", "handoff"), "change")
    _verify_change(root, change, text, allowed)

    digests = _mapping(_required(packet, "digests", "handoff"), "digests")
    source_digests = _verify_digest_map(
        root,
        _required(digests, "source", "digests"),
        "digests.source",
        base_sha=base_sha,
    )
    result_digests = _verify_digest_map(
        root,
        _required(digests, "expected_result", "digests"),
        "digests.expected_result",
    )
    if role in {"devops_developer", "devops_docs", "devops_prd"}:
        missing_source = allowed - set(source_digests)
        missing_result = allowed - set(result_digests)
        if missing_source:
            raise ValidationError(
                f"digests.source is missing allowed path: {sorted(missing_source)[0]}"
            )
        if missing_result:
            raise ValidationError(
                f"digests.expected_result is missing allowed path: {sorted(missing_result)[0]}"
            )
    grill_digest = _string(
        _required(digests, "grill_log", "digests"), "digests.grill_log", nonempty=False
    )
    grill_path = root / ".orchestration/grillme.md"
    if grill_path.is_file():
        _digest(grill_digest, "digests.grill_log")
        actual_grill_digest = sha256_file(grill_path)
        if grill_digest != actual_grill_digest:
            raise ValidationError(
                f"digests.grill_log is stale: expected {grill_digest}, found {actual_grill_digest}"
            )
        if role != "devops_prd" and ".orchestration/grillme.md" not in identical:
            raise ValidationError(
                ".orchestration/grillme.md must be listed in scope.byte_identical_paths"
            )
    elif grill_digest:
        raise ValidationError("digests.grill_log is set but .orchestration/grillme.md is missing")

    actual_dirty = _parse_dirty(root)
    inventory_values = _list(
        _required(packet, "dirty_worktree", "handoff"), "dirty_worktree"
    )
    inventory: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(inventory_values):
        entry = _mapping(item, f"dirty_worktree[{index}]")
        path, _ = _repo_path(
            root,
            _required(entry, "path", f"dirty_worktree[{index}]"),
            f"dirty_worktree[{index}].path",
        )
        if path in inventory:
            raise ValidationError(f"dirty_worktree contains duplicate ownership for {path}")
        status = _string(
            _required(entry, "status", f"dirty_worktree[{index}]"),
            f"dirty_worktree[{index}].status",
        )
        owner = _string(
            _required(entry, "owner", f"dirty_worktree[{index}]"),
            f"dirty_worktree[{index}].owner",
        )
        if owner not in DIRTY_OWNERS:
            raise ValidationError(
                f"dirty_worktree[{index}].owner is not a recognized workflow owner"
            )
        remains_identical = _required(
            entry, "must_remain_byte_identical", f"dirty_worktree[{index}]"
        )
        if not isinstance(remains_identical, bool):
            raise ValidationError(
                f"dirty_worktree[{index}].must_remain_byte_identical must be true or false"
            )
        inventory[path] = {
            "status": status,
            "owner": owner,
            "must_remain_byte_identical": remains_identical,
        }
    missing_dirty = sorted(set(actual_dirty) - set(inventory))
    if missing_dirty:
        raise ValidationError(f"dirty path has no declared owner: {missing_dirty[0]}")
    extra_dirty = sorted(set(inventory) - set(actual_dirty))
    if extra_dirty:
        raise ValidationError(f"dirty_worktree lists a clean or missing path: {extra_dirty[0]}")
    protected_dirty = set(actual_dirty) - allowed
    missing_forbidden = sorted(protected_dirty - forbidden)
    if missing_forbidden:
        raise ValidationError(
            f"dirty path outside the assignment is missing from scope.forbidden_paths: {missing_forbidden[0]}"
        )
    missing_identical = sorted(protected_dirty - identical)
    if missing_identical:
        raise ValidationError(
            f"dirty path outside the assignment is missing from scope.byte_identical_paths: {missing_identical[0]}"
        )
    for path, status in actual_dirty.items():
        entry = inventory[path]
        if entry["status"] != status:
            raise ValidationError(
                f"dirty_worktree status is stale for {path}: expected {entry['status']!r}, found {status!r}"
            )
        if not entry["owner"].strip():
            raise ValidationError(f"dirty path has no declared owner: {path}")
        if path in identical and not entry["must_remain_byte_identical"]:
            raise ValidationError(f"byte-identical dirty path is not protected in its inventory: {path}")
        if path in protected_dirty and not entry["must_remain_byte_identical"]:
            raise ValidationError(f"dirty path outside the assignment is not byte-identical: {path}")
        if role in {"devops_developer", "devops_docs", "devops_prd"} and path in allowed and entry["owner"] != role:
            raise ValidationError(
                f"{role} assignment conflicts with dirty path owned by {entry['owner']}: {path}"
            )
    if handoff_relative not in inventory:
        raise ValidationError("persisted handoff itself is missing from dirty-worktree ownership")
    if inventory[handoff_relative]["owner"] != "devops_orchestrator":
        raise ValidationError("persisted handoff must be owned by devops_orchestrator")

    commands = _list(
        _required(packet, "verification_commands", "handoff"),
        "verification_commands",
        nonempty=True,
    )
    for index, command in enumerate(commands):
        value = _string(command, f"verification_commands[{index}]")
        if FORBIDDEN_COMMAND_RE.search(value):
            raise ValidationError(f"verification_commands[{index}] is destructive")

    skills = _list(
        _required(packet, "required_skills", "handoff"), "required_skills", nonempty=True
    )
    attached_paths: set[str] = set()
    for index, item in enumerate(skills):
        entry = _mapping(item, f"required_skills[{index}]")
        _string(
            _required(entry, "name", f"required_skills[{index}]"),
            f"required_skills[{index}].name",
        )
        path, _ = _repo_path(
            root,
            _required(entry, "path", f"required_skills[{index}]"),
            f"required_skills[{index}].path",
            must_exist=True,
            require_file=True,
        )
        if not path.startswith(".codex/"):
            raise ValidationError(f"required_skills[{index}].path must resolve inside .codex")
        attached_paths.add(path)
    if HANDOFF_SKILL not in attached_paths:
        raise ValidationError(f"required_skills must explicitly attach {HANDOFF_SKILL}")

    _list(
        _required(packet, "completion_criteria", "handoff"),
        "completion_criteria",
        nonempty=True,
    )
    _list(
        _required(packet, "stop_conditions", "handoff"), "stop_conditions", nonempty=True
    )
    _verify_evidence(root, _required(packet, "evidence_references", "handoff"))

    context = _mapping(_required(packet, "context", "handoff"), "context")
    if _required(context, "parent_conversation_required", "context") is not False:
        raise ValidationError("context.parent_conversation_required must be false")
    if _required(context, "single_slice", "context") is not True:
        raise ValidationError("context.single_slice must be true")

    runtime = _mapping(_required(packet, "runtime", "handoff"), "runtime")
    heartbeat = _required(runtime, "heartbeat_seconds", "runtime")
    timeout = _required(runtime, "silent_timeout_seconds", "runtime")
    retries = _required(runtime, "max_automatic_retries", "runtime")
    if not isinstance(heartbeat, int) or isinstance(heartbeat, bool) or not 1 <= heartbeat <= 60:
        raise ValidationError("runtime.heartbeat_seconds must be an integer from 1 through 60")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < heartbeat * 2:
        raise ValidationError(
            "runtime.silent_timeout_seconds must allow at least two heartbeat intervals"
        )
    if retries != 1:
        raise ValidationError("runtime.max_automatic_retries must be exactly 1")

    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate one persisted packet")
    validate_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    validate_parser.add_argument("--handoff", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        handoff = args.handoff
        if not handoff.is_absolute():
            handoff = args.repo_root / handoff
        packet = validate_handoff(args.repo_root, handoff)
    except ValidationError as exc:
        print(f"HANDOFF_INVALID: {exc}", file=sys.stderr)
        return 1
    print(f"HANDOFF_VALID: {packet['handoff_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
