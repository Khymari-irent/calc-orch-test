# Testing

## Current status

No application stack, build command, or test command has been selected. The
first buildable slice must add the verified lint, build, and test commands here
and promote the matching CI proposal.

## Environment rules

- Use local or disposable resources by default.
- Do not mutate production.
- A shared, paid, or externally mutable non-production test environment needs
  `APPROVE TEST ENVIRONMENT <environment-id>`.
- Never commit credentials, raw logs, or production data.

## Delivery evidence

Slice baselines, verification procedures, and acceptance reports will be
recorded under `.orchestration/` as work is approved.
