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
    Evaluate a simple arithmetic expression containing only numbers and operators.

    Supports integers, decimals, +, -, *, /, unary minus, parentheses and
    whitespace, with the usual precedence and Python's true division.  It is
    a small recursive-descent evaluator: nothing is passed to eval(), and
    anything else, including ``**``, raises.

    Args:
        expression: String containing arithmetic expression

    Returns:
        Numeric result

    Raises:
        ValueError: If the expression is not plain arithmetic
    """
    tokens = _tokenize_arithmetic(expression)
    position = [0]

    def peek():
        return tokens[position[0]] if position[0] < len(tokens) else None

    def take():
        token = peek()
        position[0] += 1
        return token

    def expr(depth):
        value = term(depth)
        while peek() in ('+', '-'):
            value = value + term(depth) if take() == '+' else value - term(depth)
        return value

    def term(depth):
        value = factor(depth)
        while peek() in ('*', '/'):
            if take() == '*':
                value = value * factor(depth)
            else:
                divisor = factor(depth)
                if divisor == 0:
                    raise ValueError(f"Invalid arithmetic expression: {expression!r}")
                value = value / divisor
        return value

    def factor(depth):
        if depth > 64:
            raise ValueError(f"Invalid arithmetic expression: {expression!r}")
        token = take()
        if token == '-':
            return -factor(depth + 1)
        if token == '(':
            value = expr(depth + 1)
            if take() != ')':
                raise ValueError(f"Invalid arithmetic expression: {expression!r}")
            return value
        if isinstance(token, (int, float)):
            return token
        raise ValueError(f"Invalid arithmetic expression: {expression!r}")

    result = expr(0)
    if position[0] != len(tokens):
        raise ValueError(f"Invalid arithmetic expression: {expression!r}")
    return result


def _tokenize_arithmetic(expression):
    import re

    tokens = []
    for number, symbol, other in re.findall(r'(\d+(?:\.\d+)?)|([-+*/()])|(\S)', expression):
        if other:
            raise ValueError(f"Expression contains invalid characters: {expression!r}")
        if number:
            tokens.append(float(number) if '.' in number else int(number))
        else:
            tokens.append(symbol)
    for left, right in zip(tokens, tokens[1:]):
        if left == '*' and right == '*':
            raise ValueError(f"Invalid arithmetic expression: {expression!r}")
    return tokens


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
