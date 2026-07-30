---
name: handoff
description: Create, persist, and validate compact self-contained handoff packets before spawning fresh DevOps orchestration agents. Use for every devops_prd, devops_developer, devops_reviewer, devops_tester, devops_security, and devops_docs assignment, including retries.
---

# Durable orchestration handoffs

Create a bounded packet that lets a fresh agent complete exactly one slice without access to the parent conversation.

This bundled skill deliberately differs from a personal session-summary skill: write durable packets inside the target repository, never to the operating-system temporary directory.

## Required sequence

1. Inspect only durable repository state and the exact immutable Git state.
2. Select the next zero-padded path:
   `.orchestration/handoffs/mvpNNN/sliceNNN/<agent>/handoffNNN.md`.
3. Build the packet from the required schema below. Reference existing PRDs, proposals, commits, and artifacts by path and digest instead of copying them.
4. Include the complete authorized patch or full-file addition inline. If it already exists as a durable artifact, include its repository-relative path and digest.
5. Persist the packet.
6. Re-inventory the worktree so every dirty path has an owner. Include the packet itself with owner `devops_orchestrator`. Put every dirty path outside the agent's allowed paths, including the packet, in both `forbidden_paths` and `byte_identical_paths`.
7. Validate before spawning:

   `python .codex/plugins/handoff/skills/handoff/scripts/handoff_packet.py validate --repo-root . --handoff <repository-relative-handoff-path>`

8. Spawn only after validation succeeds. Explicitly attach both:
   - `.codex/plugins/handoff/skills/handoff/SKILL.md`
   - the validated handoff document
9. Tell the fresh agent that these attachments and the referenced repository files are its complete context. Do not mention or rely on a parent chat.
10. For a retry, create a new incremented handoff, refresh all Git and content digests, validate it, and attach it. Never reuse a stale packet.

## Required JSON contract

Place one fenced `handoff-json` block near the top of the Markdown document. It must be valid JSON and include every field shown in `.codex/templates/handoff.md`.

Use `change.mode` values:

- `inline_patch`: include a fenced `diff` block under `## Exact patch`.
- `full_file`: include a fenced block under `## Full-file addition`.
- `artifact_reference`: identify the durable artifact and its digest.

Use a valid full Git SHA for at least one of `candidate_sha` or `target_sha`. For work not yet committed, use the exact target/base commit as `target_sha`; never invent a future SHA.

## Safety rules

- Keep the packet compact and limited to one slice.
- Never include credentials, secrets, private URLs, raw transcripts, shell-history dumps, or reusable approval grants.
- Never use a personal absolute path as a runtime dependency.
- A literal approval authorizes only `proposal.authorized_effect`. It does not authorize merge, deployment, release, destructive actions, protected-branch edits, or risk acceptance.
- Reviewer, Tester, Security, Docs, and PRD roles remain read-only unless their role policy explicitly authorizes a narrowly scoped durable artifact. Only Developer may change source-owned paths.
- Preserve user-owned and forbidden dirty paths byte-for-byte.
- Treat a validation failure as terminal for that spawn attempt. Return the single validator error; do not create a partial-context agent.
- Never report a dispatched or `running` assignment as complete.

## Assignment monitoring

Use the bundled monitor for Developer assignments:

`python .codex/plugins/handoff/skills/handoff/scripts/assignment_monitor.py <command> ...`

There may be only one active Developer assignment per slice. Require a heartbeat no less often than every 60 seconds. At 180 silent seconds, safely interrupt, record the last completed action and exact error, regenerate and revalidate a new handoff, and retry at most once. Monitor the assignment to `succeeded` or `exhausted`; dispatch confirmation is not completion.
