"""UI-independent arithmetic operations for the calculator."""

from decimal import Decimal, DecimalException, InvalidOperation, localcontext
from typing import TypeAlias


NumberInput: TypeAlias = Decimal | float | int | str
DECIMAL_PRECISION = 28


class CalculatorError(ValueError):
    """Base class for calculator requests that cannot be completed."""


class InvalidNumberError(CalculatorError):
    """Raised when an operand is not a finite integer or decimal value."""


class UnsupportedOperatorError(CalculatorError):
    """Raised when an operation is outside the supported arithmetic set."""


class DivisionByZeroError(CalculatorError):
    """Raised when division is requested with a zero right operand."""


def calculate(left: NumberInput, operator: str, right: NumberInput) -> Decimal:
    """Return the result of one basic arithmetic operation.

    Operands are converted to :class:`~decimal.Decimal` so the engine does not
    depend on the CLI and produces predictable decimal results.
    """

    left_number = _parse_number(left)
    right_number = _parse_number(right)

    if operator not in {"+", "-", "*", "/"}:
        raise UnsupportedOperatorError(
            f"Unsupported operator: {operator!r}. Supported operators are +, -, *, /."
        )

    if operator == "/" and right_number == 0:
        raise DivisionByZeroError("Division by zero is not allowed.")

    try:
        with localcontext() as context:
            context.prec = DECIMAL_PRECISION
            if operator == "+":
                return left_number + right_number
            if operator == "-":
                return left_number - right_number
            if operator == "*":
                return left_number * right_number
            return left_number / right_number
    except DecimalException as error:
        raise CalculatorError("The calculation could not be completed.") from error


def _parse_number(value: NumberInput) -> Decimal:
    """Convert one input value to a finite decimal, with a stable error."""

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise InvalidNumberError(
            f"Invalid number: {value!r}. Use an integer or decimal operand."
        ) from error

    if not number.is_finite():
        raise InvalidNumberError(
            f"Invalid number: {value!r}. Use an integer or decimal operand."
        )

    return number
