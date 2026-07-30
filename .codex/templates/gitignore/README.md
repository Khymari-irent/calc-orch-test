# `.gitignore` generation guidance

There is intentionally no universal root `.gitignore` template. During
bootstrap, detect the PRD and repository's actual languages, package managers,
frameworks, IDEs, operating systems, build outputs, infrastructure tools, and
secret-file conventions. Present the proposed patterns and their reasons in the
bootstrap preview.

## Always consider

```gitignore
# Workspace-private orchestration state
.codex/local/automation.toml

# Local environment overrides (keep documented examples)
.env
.env.*
!.env.example
```

The tracked `.codex/local/automation.example.toml` must remain visible. Do not
ignore the whole `.codex/local/` directory.

## Stack-derived categories

Add a category only when repository evidence supports it:

- dependency caches and virtual environments;
- compiler/bundler/build output;
- test caches and local coverage artifacts;
- framework-generated local state;
- Terraform/OpenTofu or other IaC working state, while preserving safe lock
  files according to the tool's recommendation;
- local database files, emulator state, and non-source artifacts;
- editor and OS metadata when the repository convention permits it.

## Never hide by default

- source, migrations, project manifests, or reproducibility lockfiles;
- provider-native CI;
- `.codex/` portable runtime and tracked example files;
- `.orchestration/` baselines, acceptance evidence, and audit state;
- required checked-in configuration examples;
- a pre-existing tracked file merely because a generic template lists it.

Merge with an existing `.gitignore` instead of overwriting it. Preserve comments
and ordering where practical, deduplicate equivalent patterns, and ask when an
existing negation conflicts with a proposed ignore rule.
