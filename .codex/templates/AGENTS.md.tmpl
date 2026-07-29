<!-- orchestration-agents:start -->
# Managed orchestration guidance

This block is managed by the repository's DevOps Orchestrator. Preserve any
instructions outside the managed markers. If an existing instruction conflicts
with this block, stop and ask the user; do not silently choose a weaker rule.

## Branch safety

- Treat the configured production and integration branches as protected.
- Never implement directly on a protected branch. Create and verify the bound
  feature branch before editing source, configuration, tests, or documentation.
- Never stash, reset, clean, or overwrite unrelated work. Use an isolated
  worktree for unrelated dirty state and stop when changes overlap.
- Never direct-push, force-push, or delete a protected branch.
- A production PR/MR may be created only through an approved MVP or hotfix
  release. Its merge is always a human provider action.

## Role boundaries

- The Developer may edit tracked implementation files on the verified slice
  branch. It may also apply one exact approved PRD/changelog patch on a
  verified non-protected PRD-update branch, but must not synthesize or expand
  that patch. The Docs agent may edit and commit documentation-only changes to
  source-owned functions, methods, and constants after Security clearance.
- The PRD agent may append only completed answers to
  `.orchestration/grillme.md`.
- The Orchestrator synthesizes a bound PRD update from `PRD.md` and completed
  grill-log entries, delegates exact application to Developer after
  `APPROVE PRD UPDATE`, and verifies the resulting diff and digests.
- The Reviewer is read-only and performs static inspection only. It must not run
  builds or other artifact-producing commands.
- The Tester may run verification only in a disposable worktree. It must not
  edit tracked files, commit, push, merge, or deploy.
- Each review cycle uses a fresh Reviewer and fresh Tester on the same exact
  Developer commit.
- Security and Docs each run in their own fresh, single-slice thread. Security
  runs after review/test cycles; Docs runs once after Security and before the
  PR/MR.

## Delivery gates

- Treat approval commands as exact, case-sensitive, proposal-bound capability
  tokens. Conversational agreement is not approval.
- `APPROVE SLICE PLAN <slice-id>` authorizes the bound slice baseline and
  implementation cycles. `APPROVE SLICE <slice-id>` authorizes publication and
  a ready PR/MR to integration. `APPROVE FEATURE MERGE <slice-id>` authorizes
  only the verified feature-to-integration merge.
- Run exactly five standard Developer/Reviewer/Tester cycles. Continue beyond
  five without a maximum whenever substantive findings remain.
- P0/P1 findings always block. P2 findings block until remediated, adjudicated,
  or accepted through the required two-step risk command. P3 findings are
  always reported but are nonblocking.
- Security P0/P1/P2 findings pause publication, integration, release, and
  deployment. P0/P1 cannot be ignored. P2 requires `IGNORE SECURITY RISK
  <security-id>` and `CONFIRM SECURITY RISK IGNORE <security-id>`.

## CI and production

- CI is fail-fast: production-policy precheck when applicable, lint, build,
  then tests. Do not deploy, publish, schedule, upload coverage, or add
  production credentials to the bare pipeline.
- Never automate repository bootstrap, README overwrite, visibility, licensing,
  risk acceptance, shared test environments, published rebases, any production
  branch action, release, hotfix release, deployment, destructive action,
  credential change, or permission change.
- A merge to production never implies deployment. Production deployment needs
  the exact release-bound two-step approval and a PRD-defined rollback plan.

## GitHub authentication probe

- Run `gh auth status` normally first.
- If that exact read-only command fails with a sandbox, access-denied,
  execution, or likely sandbox-related network error, request platform
  approval to retry only `gh auth status` with elevated execution.
- The elevated retry verifies authentication only. It must not run login,
  refresh or expose tokens, change credentials, or mutate provider state.
- If the retry fails or elevation is declined, report authentication as
  unverified, not unauthenticated, with the actual error.

## Bundled plugins

- Explicitly inspect `.codex/plugins/*/.codex-plugin/plugin.json` and each
  manifest-declared `skills/*/SKILL.md`.
- Prefer a formally installed skill. If host discovery cannot find it, read
  the bundled `SKILL.md` directly and follow it as repository instructions.
- Directory presence does not prove installation. Reject paths escaping
  `.codex/plugins`, never execute plugin code for discovery, and report a
  required skill missing only after both host and bundled discovery fail.

## Evidence and secrets

- Use Conventional Commits with scope `ai`; include `Slice:` and `Issue:` when
  applicable plus `AI-Generated-By: OpenAI Codex`.
- Store sanitized baselines and evidence under `.orchestration/`. Never commit
  credentials, credential-bearing URLs, raw logs, production data, or private
  workspace automation state.
- Store compact, single-slice handoffs under
  `.orchestration/handoffs/mvpNNN/sliceNNN/<agent>/handoffNNN.md`; do not copy
  full chat transcripts or entire source files into handoffs.
- Detailed slice/MVP test instructions belong in `TESTING.md` and
  `.orchestration/**/testing.md`, not in the product README.
<!-- orchestration-agents:end -->
