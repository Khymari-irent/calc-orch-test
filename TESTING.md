# Testing

## Requirements

- Python 3.11 or later
- `pytest` available in the active Python environment

The calculator has no runtime dependencies. The commands below run locally and
do not require network access once `pytest` is installed.

## Offline verification

Run these commands from the repository root:

```text
python -m compileall -q calculator
python -m pytest
python -m calculator --help
python -m calculator
git diff --check
```

No lint tool is configured for this slice. `compileall` is the build/syntax
check; `pytest` covers engine behavior and CLI subprocess smoke tests.

## Manual CLI smoke checks

```text
python -m calculator 12 + 5
python -m calculator 5.5 / 2.2
python -m calculator 4 / 0
```

The first two commands should print results. The division-by-zero command should
print a clear error and return a non-zero exit code.

## Known limitations

- The CLI accepts exactly two operands and one operator.
- Chained expressions and GUI functionality are deferred to later MVP slices.
- Interactive mode uses `Ans` for the previous successful result and `quit` to exit.

## Environment rules

- Use local or disposable resources by default.
- Do not mutate production.
- A shared, paid, or externally mutable non-production test environment needs
  `APPROVE TEST ENVIRONMENT <environment-id>`.
- Never commit credentials, raw logs, or production data.

## Delivery evidence

Slice baselines, verification procedures, and acceptance reports will be
recorded under `.orchestration/` as work is approved.
