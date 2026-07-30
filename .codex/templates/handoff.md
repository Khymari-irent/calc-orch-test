# Orchestration handoff

The `handoff-json` block is the machine-enforced contract. Replace every placeholder before validation.

```handoff-json
{
  "schema_version": 1,
  "handoff_id": "mvp001-slice001-devops_developer-handoff001",
  "role": "devops_developer",
  "objective": "REPLACE",
  "identifiers": {
    "mvp": "mvp001",
    "slice": "slice001",
    "cycle": "cycle001",
    "findings": []
  },
  "proposal": {
    "id": "REPLACE",
    "artifact_path": ".orchestration/proposals/REPLACE.md",
    "digest": "sha256:REPLACE",
    "approval_required": true,
    "approval_command": "REPLACE WITH LITERAL APPROVAL",
    "authorized_effect": "REPLACE WITH EXACT AUTHORIZED EFFECT"
  },
  "change": {
    "mode": "inline_patch",
    "artifact_path": "",
    "artifact_digest": "",
    "patch_sha256": "sha256:REPLACE"
  },
  "scope": {
    "allowed_paths": ["REPLACE"],
    "forbidden_paths": ["REPLACE"],
    "byte_identical_paths": ["REPLACE"]
  },
  "git": {
    "branch": "REPLACE",
    "base_sha": "REPLACE",
    "candidate_sha": "",
    "target_sha": "REPLACE"
  },
  "digests": {
    "source": {"REPLACE": "sha256:REPLACE"},
    "expected_result": {"REPLACE": "sha256:REPLACE"},
    "grill_log": ""
  },
  "dirty_worktree": [],
  "verification_commands": ["REPLACE"],
  "required_skills": [
    {
      "name": "handoff",
      "path": ".codex/plugins/handoff/skills/handoff/SKILL.md"
    }
  ],
  "completion_criteria": ["REPLACE"],
  "stop_conditions": ["REPLACE"],
  "evidence_references": [],
  "context": {
    "parent_conversation_required": false,
    "single_slice": true
  },
  "runtime": {
    "heartbeat_seconds": 60,
    "silent_timeout_seconds": 180,
    "max_automatic_retries": 1
  }
}
```

## Exact patch

```diff
REPLACE
```

## Bounded instructions

Use only this packet, its explicitly referenced repository files, its attached skills, and the immutable Git state named above. Stop if any field is stale or inconsistent.
