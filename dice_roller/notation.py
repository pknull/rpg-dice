"""Strict parser for rpg-dice notation.

The parser builds a tree and rejects any character it cannot place; nothing is
rolled while parsing.  Grammar (whitespace is allowed between tokens, never
inside a dice literal, number or method name)::

    expression := term (('+' | '-') term)*
    term       := factor (('*' | '/') factor)*
    factor     := dice | group | INT
    dice       := INT 'd' (INT | '{' face (',' face)* '}')
                  per_die? total_mod* (CMP value?)? method* (CMP value)?
    group      := '(' expression ')' total_mod* (CMP value)? group_method* (CMP value)?
    per_die    := ('+' | '-' | '*' | '/') INT        right after the sides
    total_mod  := '=+' value | '=-' value
    method     := NAME CMP? value?
    value      := INT | INT 'd' INT                  the second form is a subroll

``+``/``-`` after the sides is the per-die modifier only when an integer, not a
dice literal, follows; ``1d8+1d6`` is therefore a pool sum.  A comparator
before any method counts successes; one after the methods checks the total.
"""
import re
from dataclasses import dataclass, field
from typing import Optional, Union

from dice_roller.DiceException import DiceException
from dice_roller.safe_compare import safe_arithmetic, safe_compare

MAX_DICE = 200
MAX_SIDES = 100
MAX_NESTING = 32
MAX_TERMS = 200
MAX_DIGITS = 9

COMPARATORS = ('>=', '<=', '!=', '==', '>', '<', '=')
METHOD_NAMES = ('xxp', 'xx', 'xp', 'x', 'ro', 'r', 'kh', 'kl', 'k', 'dh', 'dl', 'd',
                'ns', 'nf', 's', 'f', 't')
GROUP_METHOD_NAMES = ('kh', 'kl', 'k', 'dh', 'dl', 'd', 'ns', 'nf', 's', 'f', 't')
HIGH_DEFAULT = ('s', 'x', 'xx', 'xp', 'xxp', 'k', 'kh', 'dh', 'ns')
LOW_DEFAULT = ('f', 'kl', 'd', 'dl', 'r', 'ro', 'nf')

_DICE_LITERAL = re.compile(r'([0-9]+)d([0-9]+|\{[^}]*\})')
_SUBROLL = re.compile(r'([0-9]+)d([0-9]+)')
_DIGITS = '0123456789'
_FACE = re.compile(r'[A-Za-z0-9-]+')


@dataclass(frozen=True)
class Subroll:
    """Dice used as a number: rolled once per throw, a mixture in exact mode."""
    count: int
    sides: int
    text: str


Value = Union[int, Subroll]


@dataclass(frozen=True)
class Comparison:
    operator: str  # one of '>=', '<=', '!=', '>', '<', '=='
    value: Value


@dataclass(frozen=True)
class Explode:
    operator: str
    value: Value
    compound: bool
    penetrate: bool


@dataclass(frozen=True)
class Reroll:
    operator: str
    value: Value
    once: bool


@dataclass(frozen=True)
class Select:
    """Keep or drop ``count`` dice from the 'high' or 'low' end."""
    layer: str
    count: Value


@dataclass
class Suffix:
    """Pool-level tokens shared by dice terms and groups."""
    total_mods: list = field(default_factory=list)  # (sign, Value)
    success: Optional[Comparison] = None
    fail: Optional[Comparison] = None
    ns: Optional[Comparison] = None
    nf: Optional[Comparison] = None
    keep: Optional[Select] = None
    drop: Optional[Select] = None
    check: Optional[Comparison] = None


@dataclass
class Dice:
    text: str
    start: int
    stop: int
    count: int
    faces: list
    types: str  # 'int', 'str' or 'mixed'
    per_die: Optional[tuple] = None  # (operator, int)
    explode: Optional[Explode] = None
    reroll: Optional[Reroll] = None
    suffix: Suffix = field(default_factory=Suffix)


@dataclass
class Group:
    text: str
    start: int
    stop: int
    child: object
    suffix: Suffix = field(default_factory=Suffix)


@dataclass
class Const:
    value: int


@dataclass
class BinOp:
    op: str
    left: object
    right: object


def parse(text, require_dice=True):
    """Parse ``text`` into a validated tree; raise DiceException on any defect.

    An expression must contain a dice term unless ``require_dice`` is False
    (throw_string evaluates plain arithmetic, as it always has).
    """
    if not isinstance(text, str):
        raise DiceException('Unable to parse expression', 'Expression must be a string')
    tree = _Parser(text).parse()
    if require_dice and not leaves(tree):
        raise DiceException('Unable to parse expression', 'No dice in expression')
    validate(tree)
    return tree


def leaves(node):
    """Dice terms in left-to-right order."""
    if isinstance(node, Dice):
        return [node]
    if isinstance(node, Group):
        return leaves(node.child)
    if isinstance(node, BinOp):
        return leaves(node.left) + leaves(node.right)
    return []


def subrolls(node):
    """Subroll occurrences in left-to-right order; each is rolled independently."""
    found = []

    def visit_value(value):
        if isinstance(value, Subroll):
            found.append(value)

    def visit_suffix(suffix):
        for _sign, value in suffix.total_mods:
            visit_value(value)
        for comparison in (suffix.success, suffix.fail, suffix.ns, suffix.nf):
            if comparison is not None:
                visit_value(comparison.value)
        for select in (suffix.keep, suffix.drop):
            if select is not None:
                visit_value(select.count)
        if suffix.check is not None:
            visit_value(suffix.check.value)

    def visit(n):
        if isinstance(n, Dice):
            if n.explode is not None:
                visit_value(n.explode.value)
            if n.reroll is not None:
                visit_value(n.reroll.value)
            visit_suffix(n.suffix)
        elif isinstance(n, Group):
            visit(n.child)
            visit_suffix(n.suffix)
        elif isinstance(n, BinOp):
            visit(n.left)
            visit(n.right)

    visit(node)
    return found


def bound(value, binding):
    """Resolve a Value: subrolls are looked up by identity in ``binding``."""
    if isinstance(value, Subroll):
        return binding[id(value)]
    return value


class CountingRules:
    """Each leaf's counting comparisons after group overrides.

    A group's s/f/ns/nf applies to every die inside it and replaces the
    members' own rule for that field; the outermost group that names a field
    wins.  ``defined[field]`` is True when any leaf counts that field.
    """

    FIELDS = ('success', 'fail', 'ns', 'nf')

    def __init__(self, tree):
        self.by_leaf = {}
        self._walk(tree, {})
        self.defined = {field: any(rules[field] is not None for rules in self.by_leaf.values())
                        for field in self.FIELDS}

    def _walk(self, node, outer):
        if isinstance(node, Dice):
            own = {field: getattr(node.suffix, field) for field in self.FIELDS}
            self.by_leaf[id(node)] = {f: outer.get(f, own[f]) for f in self.FIELDS}
        elif isinstance(node, Group):
            inner = dict(outer)
            for field in self.FIELDS:
                comparison = getattr(node.suffix, field)
                if comparison is not None and field not in outer:
                    inner[field] = comparison
            self._walk(node.child, inner)
        elif isinstance(node, BinOp):
            self._walk(node.left, outer)
            self._walk(node.right, outer)

    def bound_rule(self, dice, field, binding):
        comparison = self.by_leaf[id(dice)][field]
        if comparison is None:
            return None
        return comparison.operator, bound(comparison.value, binding)


def check_die_pipeline(dice, binding):
    """Reject per-die pipelines that never terminate for these subroll values.

    Reroll-until where every face matches loops forever; an explosion that
    every possible value triggers recurses without end.
    """
    if dice.types != 'int' or dice.count == 0:
        return
    faces = dice.faces
    possible = faces
    if dice.reroll is not None:
        op, val = dice.reroll.operator, bound(dice.reroll.value, binding)
        keep = [f for f in faces if not safe_compare(f, op, val)]
        if not keep and not dice.reroll.once:
            raise DiceException('Unable to perform roll', 'Reroll matches every face')
        if not dice.reroll.once:
            possible = keep
    if dice.explode is not None:
        values = possible
        if dice.per_die is not None:
            values = [safe_arithmetic(v, *dice.per_die) for v in values]
        op, val = dice.explode.operator, bound(dice.explode.value, binding)
        if all(safe_compare(v, op, val) for v in values):
            raise DiceException('Unable to perform roll', 'Every die explodes forever')


def validate(tree):
    leaf_list = leaves(tree)
    used = sum(d.count for d in leaf_list) + sum(s.count for s in subrolls(tree))
    if used > MAX_DICE:
        raise DiceException('Unable to perform roll', 'Too many dice requested')
    _validate_checks(tree, root=True)
    _validate_node(tree)
    if not subrolls(tree):
        for dice in leaf_list:
            check_die_pipeline(dice, {})


def _validate_checks(node, root):
    if isinstance(node, (Dice, Group)) and node.suffix.check is not None and not root:
        raise DiceException('Unable to parse expression',
                            'A total check (t) applies to the whole expression; '
                            'group the expression and put the check after it')
    if isinstance(node, Group):
        _validate_checks(node.child, root=False)
    elif isinstance(node, BinOp):
        _validate_checks(node.left, root=False)
        _validate_checks(node.right, root=False)


def _validate_node(node):
    if isinstance(node, Group):
        _validate_node(node.child)
        suffix = node.suffix
        if any(x is not None for x in (suffix.success, suffix.fail, suffix.ns, suffix.nf,
                                       suffix.keep, suffix.drop)):
            if any(d.types != 'int' for d in leaves(node.child)):
                raise DiceException('Unable to parse expression',
                                    'Counting or keep/drop on a group needs numeric faces')
        if suffix.keep is not None or suffix.drop is not None:
            _require_pure_pool(node.child)
    elif isinstance(node, BinOp):
        _validate_node(node.left)
        _validate_node(node.right)
        if node.op == '*' and not (isinstance(node.left, Const) or isinstance(node.right, Const)):
            raise DiceException('Unable to parse expression', 'Multiplication needs a constant factor')
        if node.op == '/':
            if not isinstance(node.right, Const):
                raise DiceException('Unable to parse expression', 'Division needs a constant divisor')
            if node.right.value == 0:
                raise DiceException('Unable to parse expression', 'Division by zero')


def _require_pure_pool(node):
    """Keep/drop on a group selects dice, so its members must be plain dice sums."""
    if isinstance(node, Dice):
        if node.types != 'int':
            raise DiceException('Unable to parse expression', 'Keep/drop on a group needs numeric faces')
        if node.suffix.total_mods:
            raise DiceException('Unable to parse expression',
                                'Keep/drop on a group cannot carry total modifiers of its members')
        return
    if isinstance(node, Group):
        if node.suffix.total_mods:
            raise DiceException('Unable to parse expression',
                                'Keep/drop on a group cannot carry total modifiers of its members')
        _require_pure_pool(node.child)
        return
    if isinstance(node, BinOp) and node.op == '+':
        _require_pure_pool(node.left)
        _require_pure_pool(node.right)
        return
    raise DiceException('Unable to parse expression',
                        'Keep/drop on a group needs a sum of dice terms, without constants or - * /')


class _Parser:

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.terms = 0

    # -- low-level helpers -------------------------------------------------

    def fail(self, reason):
        where = self.text[self.pos:self.pos + 10] or 'end of expression'
        raise DiceException('Unable to parse expression', f'{reason} at position {self.pos} ({where!r})')

    def skip_ws(self):
        while self.pos < len(self.text) and self.text[self.pos] in ' \t':
            self.pos += 1

    def peek(self):
        self.skip_ws()
        return self.text[self.pos] if self.pos < len(self.text) else ''

    def at_dice_literal(self):
        self.skip_ws()
        return _DICE_LITERAL.match(self.text, self.pos) is not None

    def read_int(self):
        self.skip_ws()
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] in _DIGITS:
            self.pos += 1
        if start == self.pos:
            self.fail('Expected a number')
        return _number(self.text[start:self.pos])

    def read_comparator(self):
        """Return a normalised comparator, or None if none starts here."""
        self.skip_ws()
        rest = self.text[self.pos:]
        for comparator in COMPARATORS:
            if rest.startswith(comparator):
                if comparator == '=' and rest[1:2] in ('+', '-'):
                    return None
                self.pos += len(comparator)
                if self.peek() in ('+', '-'):
                    self.fail('Comparison values are numbers without a sign')
                return '==' if comparator == '=' else comparator
        return None

    def at_comparator(self):
        start = self.pos
        try:
            return self.read_comparator() is not None
        finally:
            self.pos = start

    def read_value(self, required):
        """INT, or a contiguous INTdINT subroll; None if absent and optional."""
        self.skip_ws()
        if not (self.pos < len(self.text) and self.text[self.pos] in _DIGITS):
            if required:
                self.fail('Expected a value')
            return None
        match = _SUBROLL.match(self.text, self.pos)
        if match:
            count, sides = _number(match.group(1)), _number(match.group(2))
            if sides < 1 or sides > MAX_SIDES:
                self.fail('Subroll sides must be between 1 and %d' % MAX_SIDES)
            self.pos = match.end()
            return Subroll(count, sides, match.group(0))
        return self.read_int()

    def read_method_name(self, allowed):
        self.skip_ws()
        for name in METHOD_NAMES:
            if self.text.startswith(name, self.pos):
                if name not in allowed:
                    self.fail(f'Method {name!r} is not allowed here')
                self.pos += len(name)
                return name
        return None

    # -- grammar -------------------------------------------------------------

    def parse(self):
        node = self.expression(0)
        self.skip_ws()
        if self.pos != len(self.text):
            self.fail('Unexpected token')
        return node

    def expression(self, depth):
        node = self.term(depth)
        while self.peek() in ('+', '-'):
            op = self.text[self.pos]
            self.pos += 1
            node = BinOp(op, node, self.term(depth))
        return node

    def term(self, depth):
        node = self.factor(depth)
        while self.peek() in ('*', '/'):
            op = self.text[self.pos]
            self.pos += 1
            node = BinOp(op, node, self.factor(depth))
        return node

    def factor(self, depth):
        self.terms += 1
        if self.terms > MAX_TERMS:
            raise DiceException('Unable to parse expression', 'Too many terms')
        char = self.peek()
        if char == '(':
            if depth >= MAX_NESTING:
                self.fail('Groups nested too deeply')
            start = self.pos
            self.pos += 1
            child = self.expression(depth + 1)
            if self.peek() != ')':
                self.fail('Expected )')
            self.pos += 1
            suffix = self.suffix(GROUP_METHOD_NAMES, group=True)
            return Group(self.text[start:self.pos].strip(), start, self.pos, child, suffix)
        if char and char in _DIGITS:
            if self.at_dice_literal():
                return self.dice()
            return Const(self.read_int())
        self.fail('Expected dice, a number or (')

    def dice(self):
        start = self.pos
        match = _DICE_LITERAL.match(self.text, self.pos)
        assert match is not None  # guarded by at_dice_literal()
        self.pos = match.end()
        count = _number(match.group(1))
        faces, types = _parse_sides(match.group(2))
        if count > MAX_DICE:
            raise DiceException('Unable to perform roll', 'Too many dice requested')
        node = Dice('', start, start, count, faces, types)
        node.per_die = self.per_die()
        node.suffix = self.suffix(METHOD_NAMES, group=False, dice=node)
        node.stop = self.pos
        node.text = self.text[start:self.pos].strip()
        if types != 'int' and (node.per_die is not None or node.explode is not None or node.reroll
                               is not None or _has_tokens(node.suffix)):
            raise DiceException('Unable to parse expression',
                                'Modifiers need numeric faces; this die has text faces')
        if types == 'int' and node.suffix.success is None:
            node.suffix.success = Comparison('>=', max(faces))
        return node

    def per_die(self):
        """The per-die modifier: an operator and integer right after the sides.

        Spaces do not matter (README: spaces for readability only), so
        ``2d6 + 3`` is ``2d6+3``.  An operator followed by dice or a group ends
        the term instead.
        """
        start = self.pos
        op = self.peek()
        if op not in ('+', '-', '*', '/') or not op:
            return None
        self.pos += 1
        if self.at_dice_literal() or not self.peek() or self.peek() not in _DIGITS:
            self.pos = start
            return None
        value = self.read_int()
        if op == '/' and value == 0:
            raise DiceException('Unable to parse expression', 'Division by zero')
        return (op, value)

    def suffix(self, allowed, group, dice=None):
        suffix = Suffix()
        faces_max = max(dice.faces) if dice is not None and dice.types == 'int' else None
        # total modifiers
        while self.peek() == '=' and self.text[self.pos + 1:self.pos + 2] in ('+', '-'):
            sign = 1 if self.text[self.pos + 1] == '+' else -1
            self.pos += 2
            suffix.total_mods.append((sign, self.read_value(required=True)))
        # success comparator
        operator = self.read_comparator()
        if operator is not None:
            value = self.read_value(required=group or faces_max is None)
            suffix.success = Comparison(operator, faces_max if value is None else value)
        # methods
        seen = set()
        while True:
            name = self.read_method_name(allowed)
            if name is None:
                break
            family = _family(name)
            if family in seen or (family == 's' and suffix.success is not None):
                self.fail(f'Repeated or conflicting {name!r}')
            seen.add(family)
            self.apply_method(name, suffix, group, dice, faces_max)
        # trailing total check
        operator = self.read_comparator()
        if operator is not None:
            if suffix.check is not None:
                self.fail('Repeated total check')
            suffix.check = Comparison(operator, self.read_value(required=True))
        return suffix

    def apply_method(self, name, suffix, group, dice, faces_max):
        pool_method = name[0] in 'kd'
        operator = None if pool_method else self.read_comparator()
        if pool_method and self.at_comparator():
            self.fail('Keep/drop takes a count, not a comparison')
        value = self.read_value(required=group or (faces_max is None and name in HIGH_DEFAULT))
        if value is None:
            if name in HIGH_DEFAULT:
                value = faces_max
            elif name in LOW_DEFAULT:
                value = 1
            else:
                value = 0
        operator = operator or '=='
        if pool_method and isinstance(value, int) and value < 0:
            # The default count is the highest face, negative on dice like {-2,-1}.
            self.fail('Keep/drop needs a count of zero or more')
        if name[0] == 'k':
            suffix.keep = Select('low' if name == 'kl' else 'high', value)
        elif name[0] == 'd':
            suffix.drop = Select('high' if name == 'dh' else 'low', value)
        elif name[0] == 'x':
            dice.explode = Explode(operator, value, compound=name.startswith('xx'),
                                   penetrate=name.endswith('p'))
        elif name[0] == 'r':
            dice.reroll = Reroll(operator, value, once=(name == 'ro'))
        elif name == 's':
            suffix.success = Comparison(operator, value)
        elif name == 'f':
            suffix.fail = Comparison(operator, value)
        elif name == 'ns':
            suffix.ns = Comparison(operator, value)
        elif name == 'nf':
            suffix.nf = Comparison(operator, value)
        elif name == 't':
            suffix.check = Comparison(operator, value)


def _family(name):
    if name[0] in 'xrkd':
        return name[0]
    return name


def _has_tokens(suffix):
    return bool(suffix.total_mods) or any(
        x is not None for x in (suffix.success, suffix.fail, suffix.ns, suffix.nf,
                                suffix.keep, suffix.drop, suffix.check))


def _number(digits):
    """An ASCII integer literal of at most MAX_DIGITS digits."""
    if len(digits) > MAX_DIGITS:
        raise DiceException('Unable to parse expression', 'Number too large')
    return int(digits)


def _parse_sides(raw):
    """Return (faces, types) for '6' or '{a,b,c}', matching e179458's rules.

    The side count is checked before any face list is built.
    """
    if raw[0] != '{':
        sides = _number(raw)
        if sides <= 0:
            raise DiceException('Unable to parse expression', 'Impossible dice faces')
        if sides > MAX_SIDES:
            raise DiceException('Unable to perform roll', 'Too many dice faces')
        return list(range(1, sides + 1)), 'int'
    body = raw[1:-1]
    parts = body.split(',')
    if len(parts) < 2 or any(not _FACE.fullmatch(p) for p in parts):
        raise DiceException('Unable to parse expression', 'Unknown dice sides')
    faces = []
    for part in parts:
        try:
            faces.append(int(part))
        except ValueError:
            faces.append(part)
    first = type(faces[0])
    types = first.__name__ if all(type(f) is first for f in faces) else 'mixed'
    return faces, types
