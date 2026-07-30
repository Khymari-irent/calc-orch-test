"""UI-independent arithmetic operations for the calculator."""

import re
from decimal import Decimal
from decimal import DecimalException, InvalidOperation, localcontext
from .scientific import apply as apply_scientific
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


class ExpressionError(CalculatorError):
    """Raised when an expression cannot be parsed or evaluated."""


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


def evaluate(expression: str, angle_mode: str = "radians") -> Decimal:
    """Evaluate a basic arithmetic expression with precedence and parentheses."""

    expression = re.sub(r"(?i)([a-z0-9]+)\(([-+*/().\d\s]+)\)", lambda match: str(apply_scientific(match.group(1).lower(), float(evaluate(match.group(2), angle_mode)), angle_mode)), expression)
    expression = re.sub(r"(?<!\d)\.(?=\d)", "0.", expression)
    tokens = re.findall(r"\d+(?:\.\d+)?|[()+\-*/]", expression.replace(" ", ""))
    compact = expression.replace(" ", "")
    if not tokens or re.search(r"\d\s+\d", expression) or "".join(tokens) != compact:
        raise ExpressionError("Invalid expression. Use numbers, parentheses, and +, -, *, /.")

    values: list[Decimal] = []
    operators: list[str] = []
    precedence = {"+": 1, "-": 1, "*": 2, "/": 2}

    def apply_operator() -> None:
        if len(values) < 2 or not operators:
            raise ExpressionError("Malformed expression.")
        operator = operators.pop()
        right, left = values.pop(), values.pop()
        values.append(calculate(left, operator, right))

    expect_value = True
    for token in tokens:
        if token[0].isdigit():
            if not expect_value:
                raise ExpressionError("Malformed expression.")
            values.append(_parse_number(token))
            expect_value = False
        elif token == "(":
            if not expect_value:
                raise ExpressionError("Malformed expression.")
            operators.append(token)
        elif token == ")":
            if expect_value:
                raise ExpressionError("Malformed expression.")
            while operators and operators[-1] != "(":
                apply_operator()
            if not operators:
                raise ExpressionError("Unmatched closing parenthesis.")
            operators.pop()
        else:
            if expect_value:
                if token == "-":
                    values.append(Decimal(0))
                else:
                    raise ExpressionError("Malformed expression.")
            while operators and operators[-1] != "(" and precedence[operators[-1]] >= precedence[token]:
                apply_operator()
            operators.append(token)
            expect_value = True

    if expect_value:
        raise ExpressionError("Malformed expression.")
    while operators:
        if operators[-1] == "(":
            raise ExpressionError("Unmatched opening parenthesis.")
        apply_operator()
    if len(values) != 1:
        raise ExpressionError("Malformed expression.")
    return values[0]
