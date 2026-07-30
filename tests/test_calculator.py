"""Unit and command-line smoke tests for the calculator."""

from decimal import Decimal
from pathlib import Path
import subprocess
import sys

import pytest

from calculator.engine import (
    DivisionByZeroError,
    InvalidNumberError,
    UnsupportedOperatorError,
    calculate,
    evaluate,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("left", "operator", "right", "expected"),
    [
        ("7", "+", "3", Decimal("10")),
        ("7", "-", "3", Decimal("4")),
        ("7", "*", "3", Decimal("21")),
        ("8", "/", "2", Decimal("4")),
        ("5.5", "+", "2.25", Decimal("7.75")),
        ("5.5", "-", "2.25", Decimal("3.25")),
        ("5.5", "*", "2.25", Decimal("12.375")),
        ("5.5", "/", "2.2", Decimal("2.5")),
        ("-7", "+", "3", Decimal("-4")),
        ("-7", "-", "3", Decimal("-10")),
        ("-7", "*", "3", Decimal("-21")),
        ("-8", "/", "2", Decimal("-4")),
    ],
)
def test_calculate_supports_basic_integer_decimal_and_negative_operations(
    left: str, operator: str, right: str, expected: Decimal
) -> None:
    assert calculate(left, operator, right) == expected


@pytest.mark.parametrize("value", ["not-a-number", "NaN", "Infinity"])
def test_calculate_rejects_invalid_numbers(value: str) -> None:
    with pytest.raises(InvalidNumberError, match="Invalid number"):
        calculate(value, "+", "1")


def test_calculate_rejects_unsupported_operators() -> None:
    with pytest.raises(UnsupportedOperatorError, match="Unsupported operator: '%'"):
        calculate("4", "%", "2")


def test_calculate_rejects_division_by_zero() -> None:
    with pytest.raises(DivisionByZeroError, match="Division by zero"):
        calculate("4", "/", "0")


@pytest.mark.parametrize(
    ("expression", "expected"),
    [("2 + 3 * 4", Decimal("14")), ("(10 - 2) / 4", Decimal("2")), ("-2 * (3 + 4)", Decimal("-14"))],
)
def test_evaluate_supports_precedence_and_parentheses(expression: str, expected: Decimal) -> None:
    assert evaluate(expression) == expected


@pytest.mark.parametrize("expression", ["2 +", "(2 + 3", "2 ** 3", "2 3"])
def test_evaluate_rejects_malformed_expressions(expression: str) -> None:
    with pytest.raises(ValueError):
        evaluate(expression)


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (["7", "+", "3"], "10"),
        (["5.5", "-", "2.25"], "3.25"),
        (["-7", "*", "3"], "-21"),
        (["-8", "/", "2"], "-4"),
    ],
)
def test_cli_calculates_requested_operation(arguments: list[str], expected: str) -> None:
    result = run_cli(*arguments)

    assert result.returncode == 0
    assert result.stdout == f"{expected}\n"
    assert result.stderr == ""


def test_cli_help_is_available() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "usage: calculator" in result.stdout
    assert result.stderr == ""


def test_interactive_mode_supports_ans_and_quit() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "calculator"],
        cwd=PROJECT_ROOT,
        input="2 + 3 * 4\nAns + 10\nquit\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "14" in result.stdout
    assert "24" in result.stdout


def test_interactive_mode_accepts_case_insensitive_ans() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "calculator"],
        cwd=PROJECT_ROOT,
        input="2 + 3\naNs + 4\nquit\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "5" in result.stdout
    assert "9" in result.stdout


def test_interactive_mode_keeps_running_after_errors() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "calculator"],
        cwd=PROJECT_ROOT,
        input="Ans + 1\n2 + 2\nAns * 3\nquit\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Ans is not available" in result.stdout
    assert "4" in result.stdout
    assert "12" in result.stdout


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["not-a-number", "+", "1"], "Invalid expression"),
        (["4", "%", "2"], "Invalid expression"),
        (["4", "/", "0"], "Division by zero"),
        (["4", "+"], "Malformed expression"),
    ],
)
def test_cli_rejects_invalid_requests(arguments: list[str], message: str) -> None:
    result = run_cli(*arguments)

    assert result.returncode != 0
    assert message in result.stderr


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the package entry point from the project root without a shell."""

    return subprocess.run(
        [sys.executable, "-m", "calculator", *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
