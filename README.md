# calc-orch-test

A small Python calculator with a reusable arithmetic engine and command-line
interface.

## Requirements

- Python 3.11 or later
- No runtime dependencies or network access

## Run the CLI

Use one or more operations with standard precedence and parentheses:

```text
python -m calculator "<expression>"
```

Examples:

```text
python -m calculator "12 + 5"
python -m calculator "2 + 3 * 4"
python -m calculator "(10 - 2) / 4"
python -m calculator --help
```

Start interactive mode with no expression. Enter `Ans` to reuse the previous
successful result, and `quit` to exit:

```text
python -m calculator
calculator> 2 + 3 * 4
14
calculator> Ans + 10
24
calculator> quit
```

The supported operators are `+`, `-`, `*`, and `/`. Operands may be integers,
decimals, or negative numbers. Invalid operands, unsupported operators, missing
arguments, and division by zero produce an error and a non-zero exit code.

The engine uses Python's decimal arithmetic with 28 significant digits for
division. The CLI handles one operation at a time; chained expressions are not
part of this MVP.

## Architecture

`calculator.engine` contains the UI-independent calculation rules.
`calculator.__main__` parses command-line arguments and displays the result.
The planned GUI will reuse the same engine in a later MVP.

## Verification

Run the offline checks in [TESTING.md](TESTING.md).

## Launch the GUI

On systems with Tkinter available:

```text
python -m calculator --gui
```

## License

MIT
