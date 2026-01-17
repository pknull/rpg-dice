"""
Safe comparison and arithmetic operations for dice rolling.

Replaces sympy.sympify() string concatenation with explicit operator functions,
eliminating code injection risk while maintaining exact same behavior.
"""
import operator
from fractions import Fraction

# Mapping of operator strings to comparison functions
COMPARISON_OPERATORS = {
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
    '=': operator.eq,
    '==': operator.eq,
    '!=': operator.ne,
}

# Mapping of operator strings to arithmetic functions
ARITHMETIC_OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}


def safe_compare(left, op_str, right):
    """
    Safely compare two values using an operator string.

    This replaces patterns like:
        sympy.sympify(str(roll) + operator + val)

    Args:
        left: Left operand (number)
        op_str: Operator string (one of: >, <, >=, <=, =, ==, !=)
        right: Right operand (number or string that can be converted)

    Returns:
        bool: Result of comparison

    Raises:
        ValueError: If operator is not in whitelist
    """
    op_str = str(op_str).strip()
    if op_str not in COMPARISON_OPERATORS:
        raise ValueError(f"Invalid comparison operator: {op_str!r}")

    op_func = COMPARISON_OPERATORS[op_str]

    # Convert to numeric types for comparison
    # Handle sympy Rational, Fraction, int, float, str
    left_val = _to_number(left)
    right_val = _to_number(right)

    return op_func(left_val, right_val)


def safe_arithmetic(left, op_str, right):
    """
    Safely perform arithmetic on two values.

    This replaces patterns like:
        sympy.sympify(str(roll) + operator + val)

    Args:
        left: Left operand (number)
        op_str: Operator string (one of: +, -, *, /)
        right: Right operand (number or string that can be converted)

    Returns:
        Numeric result (Fraction for division to maintain precision)

    Raises:
        ValueError: If operator is not in whitelist
    """
    op_str = str(op_str).strip()
    if op_str not in ARITHMETIC_OPERATORS:
        raise ValueError(f"Invalid arithmetic operator: {op_str!r}")

    op_func = ARITHMETIC_OPERATORS[op_str]

    # Convert to numeric types
    left_val = _to_number(left)
    right_val = _to_number(right)

    # Use Fraction for division to maintain exact precision (like sympify did)
    if op_str == '/':
        return Fraction(left_val, right_val)

    return op_func(left_val, right_val)


def safe_eval_arithmetic(expression):
    """
    Safely evaluate a simple arithmetic expression containing only numbers and operators.

    This replaces sympy.sympify() for evaluating expressions like "7 + 15 + 5"
    after dice have been rolled and replaced with their totals.

    Only supports: integers, floats, +, -, *, /, parentheses, whitespace

    Args:
        expression: String containing arithmetic expression

    Returns:
        Numeric result

    Raises:
        ValueError: If expression contains invalid characters
    """
    import re

    # Only allow: digits, decimal points, operators, parentheses, whitespace
    if not re.match(r'^[\d\s\+\-\*\/\.\(\)]+$', expression):
        raise ValueError(f"Expression contains invalid characters: {expression!r}")

    # Use Python's eval with a restricted namespace (no builtins, no names)
    # This is safe because we've validated the characters above
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return result
    except (SyntaxError, TypeError, ZeroDivisionError) as e:
        raise ValueError(f"Invalid arithmetic expression: {expression!r}") from e


def _to_number(value):
    """
    Convert a value to a numeric type for comparison/arithmetic.

    Handles: int, float, str, Fraction, sympy types
    """
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, Fraction):
        return value
    if isinstance(value, str):
        # Try int first, then float
        try:
            return int(value)
        except ValueError:
            return float(value)
    # For sympy Rational or other numeric types, convert via float
    # This handles sympy.Rational, sympy.Integer, etc.
    try:
        # Check if it has a numerator/denominator (Fraction-like)
        if hasattr(value, 'p') and hasattr(value, 'q'):
            # sympy Rational has .p (numerator) and .q (denominator)
            return Fraction(int(value.p), int(value.q))
        return float(value)
    except (TypeError, ValueError):
        return value
