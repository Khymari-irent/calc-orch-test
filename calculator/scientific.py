"""Scientific operations used by the calculator engine."""

import math


def apply(name: str, value: float, angle_mode: str = "radians") -> float:
    """Apply one supported scientific function using the selected angle mode."""

    if name in {"sin", "cos", "tan"}:
        angle = math.radians(value) if angle_mode == "degrees" else value
        return getattr(math, name)(angle)
    if name == "asin":
        result = math.asin(value)
        return math.degrees(result) if angle_mode == "degrees" else result
    if name == "acos":
        result = math.acos(value)
        return math.degrees(result) if angle_mode == "degrees" else result
    if name == "atan":
        result = math.atan(value)
        return math.degrees(result) if angle_mode == "degrees" else result
    if name == "sqrt":
        return math.sqrt(value)
    if name in {"square", "x2"}:
        return value * value
    if name in {"reciprocal", "inv"}:
        return 1 / value
    if name == "invsqrt":
        return 1 / math.sqrt(value)
    if name == "log":
        return math.log10(value)
    if name == "ln":
        return math.log(value)
    if name == "exp":
        return math.exp(value)
    if name == "abs":
        return abs(value)
    raise ValueError(f"Unsupported scientific function: {name}")
