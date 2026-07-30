"""Command-line entry point for the calculator."""

import argparse
from collections.abc import Sequence
from decimal import Decimal
import re

from .engine import CalculatorError, evaluate


def build_parser() -> argparse.ArgumentParser:
    """Create the parser for a two-operand calculator request."""

    parser = argparse.ArgumentParser(
        prog="calculator",
        description="Calculate one expression with two operands and a basic operator.",
    )
    parser.add_argument("expression", nargs="*", help="arithmetic expression")
    return parser


def format_result(result: Decimal) -> str:
    """Format a decimal result without exponent notation or a negative zero."""

    if result.is_zero():
        return "0"
    return format(result.normalize(), "f")


def main(argv: Sequence[str] | None = None) -> int:
    """Run one-shot or interactive calculation and return its exit status."""

    parser = build_parser()
    arguments = parser.parse_args(argv)

    if not arguments.expression:
        return interactive()

    try:
        result = evaluate(" ".join(arguments.expression))
    except CalculatorError as error:
        parser.error(str(error))

    print(format_result(result))
    return 0


def interactive() -> int:
    """Run a prompt that supports repeated expressions, ``Ans``, and ``quit``."""

    previous: Decimal | None = None
    while True:
        try:
            expression = input("calculator> ").strip()
        except EOFError:
            print()
            return 0
        if expression.lower() == "quit":
            return 0
        if not expression:
            continue
        if re.search(r"\bAns\b", expression, flags=re.IGNORECASE):
            if previous is None:
                print("Error: Ans is not available until a calculation succeeds.")
                continue
            expression = re.sub(r"\bAns\b", str(previous), expression, flags=re.IGNORECASE)
        try:
            previous = evaluate(expression)
        except CalculatorError as error:
            print(f"Error: {error}")
            continue
        print(format_result(previous))


if __name__ == "__main__":
    raise SystemExit(main())
