"""Command-line entry point for the calculator."""

import argparse
from collections.abc import Sequence
from decimal import Decimal

from .engine import CalculatorError, evaluate


def build_parser() -> argparse.ArgumentParser:
    """Create the parser for a two-operand calculator request."""

    parser = argparse.ArgumentParser(
        prog="calculator",
        description="Calculate one expression with two operands and a basic operator.",
    )
    parser.add_argument("expression", nargs="+", help="arithmetic expression")
    return parser


def format_result(result: Decimal) -> str:
    """Format a decimal result without exponent notation or a negative zero."""

    if result.is_zero():
        return "0"
    return format(result.normalize(), "f")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return zero only after a successful calculation."""

    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        result = evaluate(" ".join(arguments.expression))
    except CalculatorError as error:
        parser.error(str(error))

    print(format_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
