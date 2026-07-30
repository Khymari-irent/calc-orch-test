# Orchestration operating policy

This file translates the machine-readable command and workflow registries into
the operating rules every orchestration role must follow. The registries remain
authoritative for exact syntax and invariants.

## Authority and approval binding

Use the authority order in workflow.toml and pause on unresolved conflict.
Approval is an exact, case-sensitive, full-line command from commands.toml. One
message contains one command. Bind every proposal to its target identifiers,
provider, remote identity, branch roles, relevant SHAs, scope, commands, and
policy version. A material change expires the proposal and its approval.

An exact workflow command expresses workflow intent only. It never overrides a
Codex sandbox prompt, managed policy, provider permission, SSO requirement, or
administrator control.

## Role boundary

- The Orchestrator owns discovery, proposal binding, delegation, provider
  operations, state transitions, compact handoff persistence, and user-facing
  summaries.
- The PRD agent uses one fresh thread per question and may append only completed
  answers to `.orchestration/grillme.md`.
- The Orchestrator synthesizes a PRD-update proposal from the current PRD and
  completed grill-log entries, but never applies tracked PRD changes.
- The Developer owns implementation edits and commits. It may also apply one
  exact approved PRD/changelog patch without synthesizing requirements. It
  never pushes, merges, releases, or deploys.
- Each cycle uses a fresh Reviewer that remains read-only and runs no
  artifact-producing command.
- Each cycle uses a fresh Tester in a disposable worktree. Temporary artifacts
  stay in that worktree.
- Reviewer and Tester inspect the same immutable commit in parallel.
- A fresh Security agent assesses one slice after review/test cycles and never
  fixes findings or creates provider issues.
- A fresh Docs agent runs once after Security and may edit and commit only
  native documentation for source-owned functions, methods, and constants on
  the verified slice branch.

The root and Orchestrator do not implement product changes themselves. They
delegate implementation to the Developer and the final documentation-only pass
to Docs after verifying the approved working branch.

## PRD update boundary

After PRD grilling resolves all blocking questions, the Orchestrator reads the
current PRD plus completed `.orchestration/grillme.md` entries and displays a
versioned update proposal. The proposal binds the PRD path and source digest
or `MISSING`, grill-log digest, exact unified diff or full-file addition,
resulting PRD digest, changelog entry, resolved question IDs, branch/base SHA,
and proposal digest. It must expose unanswered or conflicting entries rather
than infer missing requirements.

`APPROVE PRD UPDATE` authorizes only that unchanged proposal. The Orchestrator
delegates the exact patch to Developer on a verified non-protected PRD-update
branch. Developer does not reinterpret the grill log, rewrite the proposal, or
make adjacent improvements. If no safe branch exists, application waits for
the applicable approved bootstrap flow to establish one.

After the commit, Orchestrator verifies the changed paths, exact applied diff,
before/after PRD digests, proposal digest, branch/base, and unchanged grill-log
digest. Any drift expires approval and requires a newly displayed proposal.
Delivery planning cannot continue until the updated PRD and commit are
verified.

## Context and handoff boundary

Every PRD question and every Reviewer, Tester, Security, and Docs assignment
uses its own fresh agent thread. A delivery thread contains no more than one
slice. Give agents the baseline, exact commit, relevant durable files, and
compact prior handoffs instead of the full parent transcript or entire
codebase.

Persist handoffs under
`.orchestration/handoffs/mvpNNN/sliceNNN/<agent>/handoffNNN.md`. Keep them
self-contained and concise. Link to source and artifacts rather than copying
large files or raw logs. Never include credentials, private data, production
data, reusable approval, or full chat transcripts. Keep stable prompt prefixes
to improve available platform caching and measure actual cache usage when
exposed; never promise a fixed discount.

The bundled orchestration handoff skill is
`.codex/plugins/handoff/skills/handoff/SKILL.md`. It is distinct from
`i-have-adhd`: the latter controls communication style while `handoff` creates
durable agent packets. Neither skill may depend on a personal skill directory.

Before any fresh PRD, Developer, Reviewer, Tester, Security, or Docs agent is
spawned, Orchestrator must generate and persist a new packet, inventory and own
every dirty path, and run the bundled validator. Stop on the validator's first
concrete error. Spawn only after validation succeeds, with no parent-context
fork. Explicitly attach the handoff `SKILL.md` as a skill input and attach the
persisted packet's exact path and content as the bounded assignment input.
Merely mentioning a path is not an attachment.

Every packet binds the role and objective; applicable MVP, slice, cycle, and
finding IDs; proposal ID and digest; required literal approval and its exact
authorized effect; complete patch, full-file addition, or durable artifact;
allowed, forbidden, and byte-identical paths; branch, base, candidate or target
commit; source, result, and grill-log digests; dirty-worktree inventory and
ownership; exact verification; required skills; completion criteria; stop
conditions; and compact evidence references. The packet, referenced repository
files, attached skills, and immutable Git state are the fresh agent's complete
context. Parent conversation history is never a runtime dependency.

Developer assignments are bounded by the bundled assignment monitor. Permit
one active Developer assignment per slice, require a heartbeat at least every
60 seconds, and treat 180 seconds of silence as a timeout. Safely interrupt,
capture the last completed action and exact error, then regenerate and
revalidate a new handoff before the sole automatic retry. Never overlap retries
or treat `running` as a result. Monitor through `succeeded` or `exhausted`; two
failed attempts stop the workflow with the specific handoff or runtime defect.

## Bundled plugin discovery

At startup, Orchestrator scans `.codex/plugins/*/.codex-plugin/plugin.json` and
resolves only skill directories declared by each manifest. It inspects each
declared `skills/*/SKILL.md`, rejects any path escaping `.codex/plugins`, and
records a compact name/description/path inventory. Directory presence does not
mean the plugin is formally installed: Codex discovers repo skills under
`.agents/skills`, while installed plugins contribute their skills after
installation and a new session.

Prefer the host-exposed skill when available. If it is absent, read the bundled
`SKILL.md` directly and follow it as repository instructions. Pass that
canonical path to delegated agents. A required plugin or skill is missing only
when both host discovery and the explicit bundled scan fail. Discovery is
read-only and never executes plugin code.

## Discovery and bootstrap

Begin with read-only inspection of Git state, history, remotes, provider,
authentication, permissions, branch roles and protections, PRD, instructions,
README history, license, ignore rules, toolchains, CI, and test environments.
Preserve unrelated work. Never stash, reset, clean, or overwrite it. Use an
isolated worktree for non-overlapping dirty work; stop on overlap.

Run `gh auth status` normally when verifying GitHub CLI authentication. When
that exact read-only probe fails with a sandbox, access-denied, execution, or
likely sandbox-related network error, request platform approval and retry only
`gh auth status` with elevated execution. This retry verifies authentication;
it does not authorize login, token refresh or disclosure, credential changes,
or provider mutations. If elevation is declined or the retry still fails,
record GitHub authentication as unverified rather than unauthenticated and
report the actual error.

New repositories use a parentless, fileless production anchor and an
integration/default branch created from it. The approved genesis operation is
the only direct protected-branch push exception. Install protections
immediately afterward. Existing repositories preserve safe conventions and use
an approved bootstrap branch and PR/MR. A meaningful README replacement needs
its separate exact approval.

Do not activate local Git hooks until the approved new-repository genesis push
is complete. Otherwise the hooks correctly reject that direct protected-branch
operation. When activating them, record the discovered branch roles in local
Git config as orchestration.productionBranch and
orchestration.integrationBranch so existing-repository names do not fall back
to the new-repository main and dev defaults.

## Slice lifecycle

Keep one active slice and implement vertical user or operational value. Freeze
scope, acceptance criteria, exclusions, commands, applicable layers, base SHA,
and evidence expectations in the approved baseline. Verify the feature branch
before any tracked change.

Run five standard Developer/Reviewer/Tester cycles. After cycle five, continue
with as many substantive remediation cycles as necessary. P0 and P1 always
block. P2 blocks unless the unchanged finding is disregarded through the two
exact commands and linked technical-debt tracking. P3 never blocks but is
always reported.

After review and test cycles clear, run a fresh Security assessment on the
exact candidate commit. Create a separate provider issue for every Security
finding. P0/P1/P2 pause slice publication, integration, release, and
deployment; P3 is nonblocking. `FIX SECURITY RISK <security-id>` starts
remediation and requires fresh Reviewer/Tester/Security evidence. P0/P1 can
never be ignored. P2 requires both `IGNORE SECURITY RISK <security-id>` and
`CONFIRM SECURITY RISK IGNORE <security-id>` for the unchanged finding and
linked technical debt.

After Security clears, run one fresh Docs pass before PR/MR creation. Docs may
document all source-owned functions, methods, and constant variables using the
language-native format, excluding generated, vendored, dependency, fixture,
cache, and build-output trees. A behavioral change invalidates the Security
clearance and returns the slice to implementation and evidence cycles.

Only an accepted slice may be published as a ready PR/MR to integration. Only
the exact feature-merge approval may merge it to integration. Verify the remote
merge SHA and required checks before closing slice tracking.

## CI and provider operations

Treat GitHub and GitLab as equivalent first-class providers. Use native issues,
labels, protected branches, PRs/MRs, CI, and merge evidence when available. If
a mandatory protection cannot be installed, pause rather than downgrade it.

Bootstrap CI is a non-executable TOML proposal. The first buildable slice
promotes it to provider-native CI after validating detected versions and exact
lint, build, and test commands. CI is fail-fast, least-privilege, and limited to
PRs/MRs targeting integration or production plus manual dispatch. It never
deploys, publishes, uploads coverage, schedules itself, or receives production
credentials.

## Production boundary

No automation may cover production branches, releases, hotfix releases,
production merges, or deployment. Release and hotfix approvals may create only
the verified PR/MR to production. A human performs the protected provider
merge. Merge never implies deployment. Deployment requires its separate,
unchanged two-step approval.

Never automate or infer approval for bootstrap, README overwrite, public
visibility, licensing, risk acceptance, published rebase, shared test
environments, security-risk disposition, destructive actions, credentials, or
permission changes.

## Durable evidence

Commit sanitized decisions, versions, digests, SHAs, statuses, and provider
links under .orchestration. Never commit raw transcripts, full command logs,
tokens, credential-bearing URLs, production data, or reusable approval. Keep
workspace automation in the gitignored .codex/local/automation.toml and suspend
it on every material identity or policy change listed in workflow.toml.
