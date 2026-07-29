#!/usr/bin/env python3
"""Persist and enforce bounded Developer assignment lifecycle state."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from handoff_packet import ValidationError, sha256_file, validate_handoff


ACTIVE_STATES = {"running", "interrupt_required", "retry_required"}
TERMINAL_STATES = {"succeeded", "exhausted"}


class MonitorError(Exception):
    """One concrete assignment-monitor failure."""


def _now(value: float | None) -> float:
    return time.time() if value is None else value


def _inside(root: Path, value: Path, label: str) -> Path:
    candidate = value.resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise MonitorError(f"{label} must be inside the repository") from exc
    return candidate


def _state_path(root: Path, packet: dict[str, Any]) -> Path:
    identifiers = packet["identifiers"]
    return (
        root
        / ".orchestration"
        / "assignments"
        / identifiers["mvp"]
        / identifiers["slice"]
        / "devops_developer.json"
    )


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MonitorError(f"assignment state does not exist: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MonitorError(f"cannot read assignment state {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MonitorError("assignment state must be a JSON object")
    return value


def _save(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    except OSError as exc:
        raise MonitorError(f"cannot persist assignment state {path}: {exc}") from exc


def _handoff(root: Path, value: Path) -> tuple[Path, dict[str, Any]]:
    path = value if value.is_absolute() else root / value
    path = _inside(root, path, "handoff")
    try:
        packet = validate_handoff(root, path)
    except ValidationError as exc:
        raise MonitorError(f"handoff validation failed: {exc}") from exc
    if packet["role"] != "devops_developer":
        raise MonitorError("assignment monitor accepts only devops_developer handoffs")
    return path, packet


def _record_failure(
    state: dict[str, Any],
    *,
    timestamp: float,
    last_action: str,
    exact_error: str,
) -> None:
    if not last_action.strip():
        raise MonitorError("last completed action is required when an assignment fails")
    if not exact_error.strip():
        raise MonitorError("exact error is required when an assignment fails")
    state["last_completed_action"] = last_action
    state["exact_error"] = exact_error
    state["last_transition_at"] = timestamp
    state["failures"] += 1
    if state["failures"] <= state["max_automatic_retries"]:
        state["status"] = "retry_required"
        state["terminal_result"] = ""
    else:
        state["status"] = "exhausted"
        state["terminal_result"] = "failed"
        state["defect"] = (
            "Developer assignment failed twice; inspect the recorded handoff or runtime defect: "
            f"{exact_error}"
        )


def command_start(args: argparse.Namespace) -> tuple[int, str]:
    root = args.repo_root.resolve()
    handoff_path, packet = _handoff(root, args.handoff)
    state_path = _state_path(root, packet)
    if state_path.exists():
        previous = _load(state_path)
        if previous.get("status") in ACTIVE_STATES:
            raise MonitorError(
                f"another Developer assignment is already active for {packet['identifiers']['slice']}"
            )
    timestamp = _now(args.now)
    state = {
        "schema_version": 1,
        "assignment_id": args.assignment_id,
        "role": "devops_developer",
        "mvp": packet["identifiers"]["mvp"],
        "slice": packet["identifiers"]["slice"],
        "cycle": packet["identifiers"]["cycle"],
        "status": "running",
        "attempt": 1,
        "failures": 0,
        "max_automatic_retries": packet["runtime"]["max_automatic_retries"],
        "heartbeat_seconds": packet["runtime"]["heartbeat_seconds"],
        "silent_timeout_seconds": packet["runtime"]["silent_timeout_seconds"],
        "handoff_path": handoff_path.relative_to(root).as_posix(),
        "handoff_id": packet["handoff_id"],
        "handoff_digest": sha256_file(handoff_path),
        "started_at": timestamp,
        "last_heartbeat_at": timestamp,
        "last_transition_at": timestamp,
        "last_completed_action": "validated handoff before dispatch",
        "exact_error": "",
        "terminal_result": "",
        "defect": "",
    }
    _save(state_path, state)
    relative = state_path.relative_to(root).as_posix()
    return 0, f"ASSIGNMENT_RUNNING: {relative}"


def command_heartbeat(args: argparse.Namespace) -> tuple[int, str]:
    root = args.repo_root.resolve()
    state_path = _inside(root, args.state if args.state.is_absolute() else root / args.state, "state")
    state = _load(state_path)
    if state.get("status") != "running":
        raise MonitorError(f"heartbeat rejected because assignment is {state.get('status')}")
    action = args.last_action.strip()
    if not action:
        raise MonitorError("heartbeat requires the last completed action")
    timestamp = _now(args.now)
    if timestamp < state["last_heartbeat_at"]:
        raise MonitorError("heartbeat timestamp cannot move backwards")
    state["last_heartbeat_at"] = timestamp
    state["last_completed_action"] = action
    _save(state_path, state)
    return 0, "ASSIGNMENT_HEARTBEAT_RECORDED"


def command_check(args: argparse.Namespace) -> tuple[int, str]:
    root = args.repo_root.resolve()
    state_path = _inside(root, args.state if args.state.is_absolute() else root / args.state, "state")
    state = _load(state_path)
    status = state.get("status")
    if status in TERMINAL_STATES:
        return 0, f"ASSIGNMENT_TERMINAL: {status}"
    if status != "running":
        return 2, f"ASSIGNMENT_ACTION_REQUIRED: {status}"
    timestamp = _now(args.now)
    silence = timestamp - state["last_heartbeat_at"]
    if silence >= state["silent_timeout_seconds"]:
        state["status"] = "interrupt_required"
        state["last_transition_at"] = timestamp
        state["exact_error"] = (
            f"silent-agent timeout after {int(silence)} seconds without a heartbeat"
        )
        _save(state_path, state)
        return 2, f"ASSIGNMENT_INTERRUPT_REQUIRED: {state['exact_error']}"
    if silence > state["heartbeat_seconds"]:
        return 2, (
            "ASSIGNMENT_HEARTBEAT_OVERDUE: "
            f"silent_for={int(silence)}s; required_interval={state['heartbeat_seconds']}s"
        )
    return 3, f"ASSIGNMENT_RUNNING: silent_for={int(silence)}s"


def command_interrupt(args: argparse.Namespace) -> tuple[int, str]:
    root = args.repo_root.resolve()
    state_path = _inside(root, args.state if args.state.is_absolute() else root / args.state, "state")
    state = _load(state_path)
    if state.get("status") != "interrupt_required":
        raise MonitorError(
            f"safe interruption may be recorded only after timeout detection, not {state.get('status')}"
        )
    exact_error = args.error.strip() or str(state.get("exact_error", "")).strip()
    _record_failure(
        state,
        timestamp=_now(args.now),
        last_action=args.last_action,
        exact_error=exact_error,
    )
    _save(state_path, state)
    if state["status"] == "exhausted":
        return 0, f"ASSIGNMENT_TERMINAL: exhausted; {state['defect']}"
    return 2, "ASSIGNMENT_RETRY_REQUIRED: regenerate and revalidate a new handoff"


def command_retry(args: argparse.Namespace) -> tuple[int, str]:
    root = args.repo_root.resolve()
    state_path = _inside(root, args.state if args.state.is_absolute() else root / args.state, "state")
    state = _load(state_path)
    if state.get("status") != "retry_required":
        raise MonitorError(
            f"retry rejected because assignment is {state.get('status')}; overlapping retries are forbidden"
        )
    handoff_path, packet = _handoff(root, args.handoff)
    if packet["identifiers"]["mvp"] != state["mvp"] or packet["identifiers"]["slice"] != state["slice"]:
        raise MonitorError("retry handoff must target the same MVP and slice")
    if packet["identifiers"]["cycle"] != state["cycle"]:
        raise MonitorError("retry handoff must target the same cycle")
    digest = sha256_file(handoff_path)
    relative = handoff_path.relative_to(root).as_posix()
    if digest == state["handoff_digest"] or relative == state["handoff_path"]:
        raise MonitorError("retry requires a regenerated, incremented, and revalidated handoff")
    timestamp = _now(args.now)
    state.update(
        {
            "status": "running",
            "attempt": state["attempt"] + 1,
            "handoff_path": relative,
            "handoff_id": packet["handoff_id"],
            "handoff_digest": digest,
            "last_heartbeat_at": timestamp,
            "last_transition_at": timestamp,
            "last_completed_action": "regenerated and revalidated handoff before retry dispatch",
            "exact_error": "",
            "terminal_result": "",
        }
    )
    _save(state_path, state)
    return 0, f"ASSIGNMENT_RUNNING: retry_attempt={state['attempt']}"


def command_finish(args: argparse.Namespace) -> tuple[int, str]:
    root = args.repo_root.resolve()
    state_path = _inside(root, args.state if args.state.is_absolute() else root / args.state, "state")
    state = _load(state_path)
    if state.get("status") != "running":
        raise MonitorError(f"terminal result rejected because assignment is {state.get('status')}")
    timestamp = _now(args.now)
    if args.result == "succeeded":
        action = args.last_action.strip()
        if not action:
            raise MonitorError("successful terminal result requires the last completed action")
        state.update(
            {
                "status": "succeeded",
                "terminal_result": "succeeded",
                "last_completed_action": action,
                "exact_error": "",
                "last_transition_at": timestamp,
            }
        )
    else:
        _record_failure(
            state,
            timestamp=timestamp,
            last_action=args.last_action,
            exact_error=args.error,
        )
    _save(state_path, state)
    if state["status"] == "retry_required":
        return 2, "ASSIGNMENT_RETRY_REQUIRED: regenerate and revalidate a new handoff"
    if state["status"] == "exhausted":
        return 0, f"ASSIGNMENT_TERMINAL: exhausted; {state['defect']}"
    return 0, "ASSIGNMENT_TERMINAL: succeeded"


def command_status(args: argparse.Namespace) -> tuple[int, str]:
    root = args.repo_root.resolve()
    state_path = _inside(root, args.state if args.state.is_absolute() else root / args.state, "state")
    return 0, json.dumps(_load(state_path), indent=2, sort_keys=True)


def _add_common_state(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--now", type=float)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start")
    start.add_argument("--repo-root", type=Path, default=Path.cwd())
    start.add_argument("--handoff", type=Path, required=True)
    start.add_argument("--assignment-id", required=True)
    start.add_argument("--now", type=float)
    start.set_defaults(handler=command_start)

    heartbeat = subparsers.add_parser("heartbeat")
    _add_common_state(heartbeat)
    heartbeat.add_argument("--last-action", required=True)
    heartbeat.set_defaults(handler=command_heartbeat)

    check = subparsers.add_parser("check")
    _add_common_state(check)
    check.set_defaults(handler=command_check)

    interrupt = subparsers.add_parser("interrupt")
    _add_common_state(interrupt)
    interrupt.add_argument("--last-action", required=True)
    interrupt.add_argument("--error", default="")
    interrupt.set_defaults(handler=command_interrupt)

    retry = subparsers.add_parser("retry")
    _add_common_state(retry)
    retry.add_argument("--handoff", type=Path, required=True)
    retry.set_defaults(handler=command_retry)

    finish = subparsers.add_parser("finish")
    _add_common_state(finish)
    finish.add_argument("--result", choices=("succeeded", "failed"), required=True)
    finish.add_argument("--last-action", required=True)
    finish.add_argument("--error", default="")
    finish.set_defaults(handler=command_finish)

    status = subparsers.add_parser("status")
    _add_common_state(status)
    status.set_defaults(handler=command_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        code, message = args.handler(args)
    except MonitorError as exc:
        print(f"ASSIGNMENT_INVALID: {exc}", file=sys.stderr)
        return 1
    print(message)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
