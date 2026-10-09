"""Exact joint distributions for rpg-dice expressions.

``exact(expression)`` returns an :class:`ExactResult`: one joint distribution
over the fields of a roll result, ``FIELDS``, with ``Fraction`` probabilities.
It reproduces ``DiceThrower.throw`` exactly; nothing is rolled.

How the parts are computed
--------------------------
* One draw: uniform over the face list (repeated faces weigh more).  Reroll
  until a face no longer matches is uniform over the non-matching faces;
  reroll once is a mixture.  The per-die modifier then maps the value.
* Explosions: every exploded die passes through the same pipeline.  Chains
  longer than ``explode_depth`` extra dice per die are not enumerated; their
  probability is reported as ``unresolved``, never folded into an outcome.
  Each probability in ``joint`` is the exact probability of that outcome with
  every die's chain inside the depth.
* A pool without keep/drop is the n-fold convolution of one die's joint
  contribution.  Zero dice is the identity.
* Keep/drop runs a dynamic programme over face values in sorted order,
  choosing how many dice show each value with binomial weights, so the cost
  grows with the number of distinct values rather than with faces ** dice.
* Subroll values are random variables: the result is the mixture over their
  exact distributions.
* Groups and arithmetic combine independent terms by convolution.

Internally a distribution is a dict from a packed integer key to an integer
weight, plus one integer denominator.  The key packs (total, success, fail,
ns, nf) into one int so that adding keys adds every field at once.
"""
import itertools
from dataclasses import dataclass, field
from fractions import Fraction
from math import comb, factorial

from dice_roller.DiceException import DiceException
from dice_roller.notation import (BinOp, Const, CountingRules, Dice, Group, bound,
                                  check_die_pipeline, leaves, parse, subrolls)
from dice_roller.safe_compare import safe_arithmetic, safe_compare

FIELDS = ('total', 'success', 'fail', 'ns', 'nf', 'pass')

DEFAULT_EXPLODE_DEPTH = 10
MAX_EXPLODE_DEPTH = 1000
DEFAULT_FACES_LIMIT = 250_000
MAX_SUBROLL_COMBINATIONS = 4096

_BITS = 20
_MASK = (1 << _BITS) - 1
_NF = 1
_NS = 1 << _BITS
_F = 1 << (2 * _BITS)
_S = 1 << (3 * _BITS)
_TOTAL_SHIFT = 4 * _BITS
_T = 1 << _TOTAL_SHIFT


def _pack(total=0, success=0, fail=0, ns=0, nf=0):
    return total * _T + success * _S + fail * _F + ns * _NS + nf * _NF


def _unpack(key):
    nf = key & _MASK
    key >>= _BITS
    ns = key & _MASK
    key >>= _BITS
    fail = key & _MASK
    key >>= _BITS
    success = key & _MASK
    key >>= _BITS
    return key, success, fail, ns, nf


# ---------------------------------------------------------------------------
# Integer-weight distributions

@dataclass
class _Dist:
    """weights[key] / denom is the probability of key; tscale divides totals."""
    weights: dict
    denom: int
    tscale: int = 1

    @staticmethod
    def point(key=0):
        return _Dist({key: 1}, 1)


def _convolve(a, b):
    if len(a) > len(b):
        a, b = b, a
    out = {}
    get = out.get
    for ka, wa in a.items():
        for kb, wb in b.items():
            k = ka + kb
            out[k] = get(k, 0) + wa * wb
    return out


def _power(weights, n):
    """weights ** n under convolution.

    Multiplying by the base n times beats repeated squaring here: with
    schoolbook convolution a square costs |A| ** 2 while a step costs
    |A| * |base|, and the base (one die) is small.  Measured on 100d6:
    7.3 s by squaring, 1.1 s this way.
    """
    result = {0: 1}
    for _ in range(n):
        result = _convolve(result, weights)
    return result


def _pool_power(weights, n):
    """n dice of one law when few counter patterns occur; same result as _power.

    A die's packed key is total * _T plus its counter flags.  Grouping the
    law by flags (classes), the pool is a multinomial over how many dice fall
    in each class times univariate total polynomials, so the joint costs about
    as much as the totals alone.  With many classes (deep explosion chains)
    the multinomial grows faster than plain convolution and _power is used.
    """
    classes = {}
    for key, w in weights.items():
        flags = key & (_T - 1)
        bucket = classes.setdefault(flags, {})
        bucket[key >> _TOTAL_SHIFT] = bucket.get(key >> _TOTAL_SHIFT, 0) + w
    if len(classes) > 3 or n < 4:
        return _power(weights, n)
    items = list(classes.items())
    states = {(0, 0): {0: 1}}
    for index, (flags, poly) in enumerate(items):
        powers = [{0: 1}]
        last = index == len(items) - 1
        nxt = {}
        for (used, flag_sum), totals in states.items():
            room = n - used
            while len(powers) <= room:
                powers.append(_convolve(powers[-1], poly))
            for k in ((room,) if last else range(room + 1)):
                coeff = comb(room, k)
                bucket = nxt.setdefault((used + k, flag_sum + k * flags), {})
                for t, w in _convolve(totals, powers[k]).items():
                    bucket[t] = bucket.get(t, 0) + w * coeff
        states = nxt
    out = {}
    for (_used, flag_sum), totals in states.items():
        for t, w in totals.items():
            k = t * _T + flag_sum
            out[k] = out.get(k, 0) + w
    return out


def _rescale(dist, tscale):
    """Express dist's totals over a larger common tscale."""
    if dist.tscale == tscale:
        return dist.weights
    factor = tscale // dist.tscale
    out = {}
    for key, w in dist.weights.items():
        total, s, f, ns, nf = _unpack(key)
        k = _pack(total * factor, s, f, ns, nf)
        out[k] = out.get(k, 0) + w
    return out


def _combine(a, b, negate_right=False):
    tscale = a.tscale * b.tscale // _gcd(a.tscale, b.tscale)
    wa, wb = _rescale(a, tscale), _rescale(b, tscale)
    if negate_right:
        wb = _map_total(wb, lambda t: -t)
    return _Dist(_convolve(wa, wb), a.denom * b.denom, tscale)


def _map_total(weights, fn):
    out = {}
    for key, w in weights.items():
        total, s, f, ns, nf = _unpack(key)
        k = _pack(fn(total), s, f, ns, nf)
        out[k] = out.get(k, 0) + w
    return out


def _shift_total(dist, delta):
    if not delta:
        return dist
    shift = delta * dist.tscale * _T
    return _Dist({k + shift: w for k, w in dist.weights.items()}, dist.denom, dist.tscale)


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


# ---------------------------------------------------------------------------
# Effective counting rules

class _LeafRules:
    """A leaf's counting rules with subroll values bound."""

    def __init__(self, dice, rules, binding):
        self.numeric = dice.types == 'int'
        self.cmp = {field: rules.bound_rule(dice, field, binding) for field in rules.FIELDS}
        self._kept = {}
        self._natural = {}

    def _hit(self, field, value):
        rule = self.cmp[field]
        return 1 if rule is not None and safe_compare(value, *rule) else 0

    def kept_key(self, value):
        """Packed contribution of one kept modified die."""
        if value not in self._kept:
            self._kept[value] = (_pack(int(value), self._hit('success', value), self._hit('fail', value))
                                 if self.numeric else 0)
        return self._kept[value]

    def natural_key(self, face):
        if face not in self._natural:
            self._natural[face] = (_pack(0, 0, 0, self._hit('ns', face), self._hit('nf', face))
                                   if self.numeric else 0)
        return self._natural[face]


# ---------------------------------------------------------------------------
# One die

def _draw(dice, binding):
    """Law of one draw as {(natural face, value after reroll and modifier): weight}."""
    faces = dice.faces
    size = len(faces)
    raw = {}
    if dice.reroll is None:
        for a in faces:
            raw[(a, a)] = raw.get((a, a), 0) + 1
        denom = size
    else:
        op, val = dice.reroll.operator, bound(dice.reroll.value, binding)
        match = [safe_compare(face, op, val) for face in faces]
        misses = [face for face, m in zip(faces, match) if not m]
        if dice.reroll.once:
            denom = size * size
            for a, m in zip(faces, match):
                if not m:
                    raw[(a, a)] = raw.get((a, a), 0) + size
                else:
                    for b in faces:
                        raw[(a, b)] = raw.get((a, b), 0) + 1
        else:
            denom = size * len(misses)
            for a, m in zip(faces, match):
                if not m:
                    raw[(a, a)] = raw.get((a, a), 0) + len(misses)
                else:
                    for b in misses:
                        raw[(a, b)] = raw.get((a, b), 0) + 1
    if dice.per_die is None:
        return raw, denom
    out = {}
    for (a, v), w in raw.items():
        key = (a, safe_arithmetic(v, *dice.per_die))
        out[key] = out.get(key, 0) + w
    return out, denom


def _explodes(dice, binding):
    if dice.explode is None:
        return None
    op, val = dice.explode.operator, bound(dice.explode.value, binding)
    return lambda v: safe_compare(v, op, val)


def _chain_values(dice, binding):
    """Law of one later draw of an explosion chain, split by whether it explodes.

    Returns (terminal, exploding, denom) as {penetrated value: weight}.
    """
    draw, denom = _draw(dice, binding)
    explodes = _explodes(dice, binding)
    pen = 1 if dice.explode.penetrate else 0
    terminal, exploding = {}, {}
    for (_a, v), w in draw.items():
        target = exploding if explodes(v) else terminal
        target[v - pen] = target.get(v - pen, 0) + w
    return terminal, exploding, denom


def _die_stats(dice, rules, binding, depth):
    """Joint contribution of one die (no keep/drop) as integer weights."""
    draw, denom = _draw(dice, binding)
    explodes = _explodes(dice, binding)
    if explodes is None:
        out = {}
        for (a, v), w in draw.items():
            k = rules.kept_key(v) + rules.natural_key(a)
            out[k] = out.get(k, 0) + w
        return out, denom
    if dice.explode.compound:
        values, vdenom = _compound_values(dice, binding, depth)
        out = {}
        for (a, v), w in values.items():
            k = rules.kept_key(v) + rules.natural_key(a)
            out[k] = out.get(k, 0) + w
        return out, vdenom
    terminal, exploding, _ = _chain_values(dice, binding)
    later_t = {}
    for v, w in terminal.items():
        k = rules.kept_key(v)
        later_t[k] = later_t.get(k, 0) + w
    later_e = {}
    for v, w in exploding.items():
        k = rules.kept_key(v)
        later_e[k] = later_e.get(k, 0) + w
    # tail[b]: the rest of a chain that may still add b dice, over denom ** b.
    tail = {}
    for budget in range(1, depth + 1):
        if budget == 1:
            tail = dict(later_t)
        else:
            nxt = {k: w * denom ** (budget - 1) for k, w in later_t.items()}
            for k, w in _convolve(later_e, tail).items():
                nxt[k] = nxt.get(k, 0) + w
            tail = nxt
    first_t, first_e = {}, {}
    for (a, v), w in draw.items():
        k = rules.kept_key(v) + rules.natural_key(a)
        target = first_e if explodes(v) else first_t
        target[k] = target.get(k, 0) + w
    out = {k: w * denom ** depth for k, w in first_t.items()}
    if depth:
        for k, w in _convolve(first_e, tail).items():
            out[k] = out.get(k, 0) + w
    return out, denom ** (depth + 1)


def _compound_values(dice, binding, depth):
    """{(natural face, compounded value): weight} over denom ** (depth + 1)."""
    draw, denom = _draw(dice, binding)
    explodes = _explodes(dice, binding)
    terminal, exploding, _ = _chain_values(dice, binding)
    tail = {}
    for budget in range(1, depth + 1):
        nxt = {v: w * denom ** (budget - 1) for v, w in terminal.items()}
        if budget > 1:
            for v, w in exploding.items():
                for u, x in tail.items():
                    nxt[v + u] = nxt.get(v + u, 0) + w * x
        tail = nxt
    out = {}
    for (a, v), w in draw.items():
        if not explodes(v):
            out[(a, v)] = out.get((a, v), 0) + w * denom ** depth
        elif depth:
            for u, x in tail.items():
                out[(a, v + u)] = out.get((a, v + u), 0) + w * x
    return out, denom ** (depth + 1)


def _single_values(dice, binding, depth):
    """{(natural face, value): weight} for dice yielding one value each, or None."""
    if dice.explode is None:
        return _draw(dice, binding)
    if dice.explode.compound:
        return _compound_values(dice, binding, depth)
    return None


# ---------------------------------------------------------------------------
# Keep/drop

def _window(total_dice, keep, drop):
    """Kept positions [lo, hi) in descending order, as the roller selects them."""
    lo, hi = 0, total_dice
    if keep is not None:
        layer, count = keep
        count = min(count, total_dice)
        if layer == 'high':
            lo, hi = 0, count
        else:
            lo, hi = total_dice - count, total_dice
    if drop is not None:
        layer, count = drop
        if count >= hi - lo:
            return 0, 0
        if layer == 'low':
            hi -= count
        else:
            lo += count
    return lo, hi


def _keep_drop(categories, keep, drop, cache=None):
    """Joint weights of kept stats plus naturals for a pool sorted by value.

    ``categories`` lists (count, outcomes, kept_key) in member order, where
    outcomes maps value -> {natural key: weight} and kept_key(value) packs one
    kept die.  Ties are kept in member order, as Python's stable sort does.
    The returned weights are over the product of each outcome law's total
    weight raised to its count.  ``cache`` may be shared between calls whose
    categories reuse the same outcome dicts.
    """
    cache = {} if cache is None else cache
    categories = [c for c in categories if c[0]]
    if any(not outcomes for _c, outcomes, _k in categories):
        return {}
    total_dice = sum(c for c, _o, _k in categories)
    lo, hi = _window(total_dice, keep, drop)
    values = sorted({v for _c, outcomes, _k in categories for v in outcomes})
    # Process from the end nearer the window; positions count from that end.
    desc_cost = hi if hi < total_dice else lo
    asc_cost = total_dice - lo if lo > 0 else total_dice - hi
    ascending = asc_cost < desc_cost
    if ascending:
        order = values
        lo, hi = total_dice - hi, total_dice - lo
    else:
        order = values[::-1]
    # The last step at which each category can still place a die.
    last = [max(i for i, v in enumerate(order) if v in outcomes) for _c, outcomes, _k in categories]

    def nat_pow(ci, v, k):
        outcomes = categories[ci][1]
        key = ('nat', id(outcomes), v, k)
        if key not in cache:
            cache[key] = _power(outcomes[v], k)
        return cache[key]

    def beyond_pow(ci, index, kept, r):
        """r dice of category ci, each showing a value from order[index] on."""
        outcomes, kept_key = categories[ci][1], categories[ci][2]
        key = ('beyond', id(outcomes), id(kept_key), ascending, order[index], kept, r)
        if key not in cache:
            one = {}
            for v in order[index:]:
                if v in outcomes:
                    shift = kept_key(v) if kept else 0
                    for k, w in outcomes[v].items():
                        one[k + shift] = one.get(k + shift, 0) + w
            cache[key] = _power(one, r)
        return cache[key]

    states = {tuple(c for c, _o, _k in categories): {0: 1}}
    finished = {}
    for index, v in enumerate(order):
        nxt = {}
        for remaining, weights in states.items():
            placed = total_dice - sum(remaining)
            if placed >= hi or (placed >= lo and hi >= total_dice):
                kept = placed < hi
                tail = {0: 1}
                for ci, r in enumerate(remaining):
                    if r:
                        tail = _convolve(tail, beyond_pow(ci, index, kept, r))
                for k, w in _convolve(weights, tail).items():
                    finished[k] = finished.get(k, 0) + w
                continue
            choices = []
            for ci, r in enumerate(remaining):
                if not r or v not in categories[ci][1]:
                    choices.append((0,))
                elif last[ci] == index:
                    choices.append((r,))
                else:
                    choices.append(range(r + 1))
            for picks in itertools.product(*choices):
                block = sum(picks)
                left = tuple(r - p for r, p in zip(remaining, picks))
                kept_left = max(0, min(placed + block, hi) - max(placed, lo))
                coeff = 1
                shift = 0
                block_nat = {0: 1}
                for ci, p in enumerate(picks):
                    if not p:
                        continue
                    coeff *= comb(remaining[ci], p)
                    take = min(p, kept_left)
                    kept_left -= take
                    shift += take * categories[ci][2](v)
                    block_nat = _convolve(block_nat, nat_pow(ci, v, p))
                bucket = nxt.setdefault(left, {})
                for kb, wb in block_nat.items():
                    add = kb + shift
                    scale = wb * coeff
                    for k, w in weights.items():
                        kk = k + add
                        bucket[kk] = bucket.get(kk, 0) + w * scale
        states = nxt
    for remaining, weights in states.items():
        if any(remaining):
            continue
        for k, w in weights.items():
            finished[k] = finished.get(k, 0) + w
    return finished


def _outcome_law(values, rules):
    """value -> {natural key: weight} from {(face, value): weight}."""
    law = {}
    for (a, v), w in values.items():
        bucket = law.setdefault(v, {})
        k = rules.natural_key(a)
        bucket[k] = bucket.get(k, 0) + w
    return law


def _select(suffix, binding):
    keep = drop = None
    if suffix.keep is not None:
        keep = (suffix.keep.layer, bound(suffix.keep.count, binding))
    if suffix.drop is not None:
        drop = (suffix.drop.layer, bound(suffix.drop.count, binding))
    return keep, drop


def _exploding_keep_drop(dice, rules, binding, depth, keep, drop):
    """Keep/drop over a non-compounding exploding pool, chains enumerated to depth.

    Every draw is independent.  Let J of the n first draws explode and L
    later draws explode in total; the pool is then n - J first terminals, J
    first explosions, L later explosions and J later terminals, each group
    i.i.d. from its conditional law.  Summing over (J, L) with the number of
    ways to split L among J chains of at most depth - 1 later explosions
    enumerates every chain within the depth exactly once.  Without
    penetration or natural counters first and later draws share one law, so
    the sum runs over K = J + L alone with two groups: n terminals and K
    explosions.
    """
    n = dice.count
    draw, denom = _draw(dice, binding)
    explodes = _explodes(dice, binding)
    pen = 1 if dice.explode.penetrate else 0
    first_t, first_e, later_t, later_e = {}, {}, {}, {}
    for (a, v), w in draw.items():
        nat = rules.natural_key(a)
        first = first_e if explodes(v) else first_t
        bucket = first.setdefault(v, {})
        bucket[nat] = bucket.get(nat, 0) + w
        later = later_e if explodes(v) else later_t
        bucket = later.setdefault(v - pen, {})
        bucket[0] = bucket.get(0, 0) + w
    kept_key = rules.kept_key
    top = n * (depth + 1)
    shapes = {}  # (J, L) -> number of chain arrangements
    for j in range(0, n + 1 if depth else 1):
        splits = _power({g: 1 for g in range(depth)}, j)
        for l_count, ways in splits.items():
            shapes[(j, l_count)] = comb(n, j) * ways
    cache = {}
    out = {}
    merged = not pen and first_t == later_t and first_e == later_e
    if merged:
        totals = {}
        for (j, l_count), ways in shapes.items():
            totals[j + l_count] = totals.get(j + l_count, 0) + ways
        runs = [([(n, first_t), (k, first_e)], k, ways) for k, ways in totals.items()]
    else:
        runs = [([(n - j, first_t), (j, first_e), (l_count, later_e), (j, later_t)], j + l_count, ways)
                for (j, l_count), ways in shapes.items()]
    for groups, extra, ways in runs:
        categories = [(count, law, kept_key) for count, law in groups if count]
        if any(not law for _c, law, _k in categories):
            continue
        weights = _keep_drop(categories, keep, drop, cache)
        scale = ways * denom ** (top - (n + extra))
        for k, w in weights.items():
            out[k] = out.get(k, 0) + w * scale
    return out, denom ** top


# ---------------------------------------------------------------------------
# Tree evaluation (joint statistics)

class _Evaluator:

    def __init__(self, tree, rules, binding, depth, limit):
        self.tree = tree
        self.rules = rules
        self.binding = binding
        self.depth = depth
        self.limit = limit

    def leaf_rules(self, dice):
        return _LeafRules(dice, self.rules, self.binding)

    def node(self, node):
        if isinstance(node, Const):
            return _Dist.point(_pack(node.value))
        if isinstance(node, Dice):
            return self.dice(node)
        if isinstance(node, Group):
            return self.group(node)
        if node.op in ('+', '-'):
            return _combine(self.node(node.left), self.node(node.right), node.op == '-')
        if node.op == '*':
            if isinstance(node.left, Const):
                factor, inner = node.left.value, self.node(node.right)
            else:
                factor, inner = node.right.value, self.node(node.left)
            return _Dist(_map_total(inner.weights, lambda t: t * factor), inner.denom, inner.tscale)
        inner = self.node(node.left)
        return _Dist(inner.weights, inner.denom, inner.tscale * node.right.value)

    def total_mods(self, suffix):
        return sum(sign * bound(value, self.binding) for sign, value in suffix.total_mods)

    def dice(self, dice):
        check_die_pipeline(dice, self.binding)
        rules = self.leaf_rules(dice)
        n = dice.count
        if dice.types != 'int' or n == 0:
            return _shift_total(_Dist.point(), self.total_mods(dice.suffix))
        keep, drop = _select(dice.suffix, self.binding)
        if keep is None and drop is None:
            weights, denom = _die_stats(dice, rules, self.binding, self.depth)
            dist = _Dist(_pool_power(weights, n), denom ** n)
        else:
            values = _single_values(dice, self.binding, self.depth)
            if values is None:
                weights, denom = _exploding_keep_drop(dice, rules, self.binding, self.depth,
                                                      keep, drop)
                dist = _Dist(weights, denom)
            else:
                law, denom = values
                weights = _keep_drop([(n, _outcome_law(law, rules), rules.kept_key)], keep, drop)
                dist = _Dist(weights, denom ** n)
        return _shift_total(dist, self.total_mods(dice.suffix))

    def group(self, group):
        keep, drop = _select(group.suffix, self.binding)
        if keep is None and drop is None:
            dist = self.node(group.child)
        else:
            members = [d for d in leaves(group.child) if d.count > 0]
            simple = all(not d.suffix.keep and not d.suffix.drop
                         and (d.explode is None or d.explode.compound) for d in members)
            if simple and members and _flat_sum(group.child):
                categories, denom = [], 1
                for d in members:
                    check_die_pipeline(d, self.binding)
                    rules = self.leaf_rules(d)
                    law, ddenom = _single_values(d, self.binding, self.depth)
                    categories.append((d.count, _outcome_law(law, rules), rules.kept_key))
                    denom *= ddenom ** d.count
                dist = _Dist(_keep_drop(categories, keep, drop), denom)
            else:
                dist = _multiset_group_stats(group, self)
        return _shift_total(dist, self.total_mods(group.suffix))


def _flat_sum(node):
    if isinstance(node, Dice):
        return True
    if isinstance(node, Group):
        return not node.suffix.keep and not node.suffix.drop and _flat_sum(node.child)
    return isinstance(node, BinOp) and node.op == '+' and _flat_sum(node.left) and _flat_sum(node.right)


# ---------------------------------------------------------------------------
# Multisets of faces (opt-in, bounded)

class _Multisets:
    """Distributions over (kept entries, natural entries, packed stats).

    Entries are (value, leaf index) sorted by value with leaves in order, the
    roller's tie order.  Every enumeration counts against ``limit``.
    """

    def __init__(self, evaluator, limit):
        self.ev = evaluator
        self.limit = limit
        self.index = {id(d): i for i, d in enumerate(leaves(evaluator.tree))}

    def spend(self, count, what):
        if count > self.limit:
            raise DiceException('Unable to analyse expression',
                                f'{what} needs {count} multisets, over the faces limit of '
                                f'{self.limit} (exact(..., faces_limit=N) raises it)')

    def node(self, node):
        if isinstance(node, Const):
            return {((), (), _pack(node.value)): 1}, 1, 1
        if isinstance(node, Dice):
            return self.dice(node)
        if isinstance(node, Group):
            return self.group(node)
        left, ld, ls = self.node(node.left)
        if node.op in ('+', '-'):
            right, rd, rs = self.node(node.right)
            tscale = ls * rs // _gcd(ls, rs)
            self.spend(len(left) * len(right), 'Combining terms')
            out = {}
            for (kl, nl, sl), wl in left.items():
                tl = _unpack(sl)
                for (kr, nr, sr), wr in right.items():
                    tr = _unpack(sr)
                    total = tl[0] * (tscale // ls) + (-1 if node.op == '-' else 1) * tr[0] * (tscale // rs)
                    stats = _pack(total, *[x + y for x, y in zip(tl[1:], tr[1:])])
                    key = (_merge(kl, kr), _merge(nl, nr), stats)
                    out[key] = out.get(key, 0) + wl * wr
            return out, ld * rd, tscale
        if node.op == '*':
            if isinstance(node.left, Const):
                factor, (inner, d, s) = node.left.value, self.node(node.right)
            else:
                factor, inner, d, s = node.right.value, left, ld, ls
            out = {}
            for (k, n, stats), w in inner.items():
                t, *rest = _unpack(stats)
                key = (k, n, _pack(t * factor, *rest))
                out[key] = out.get(key, 0) + w
            return out, d, s
        return left, ld, ls * node.right.value

    def dice(self, dice):
        ev = self.ev
        check_die_pipeline(dice, ev.binding)
        rules = ev.leaf_rules(dice)
        leaf = self.index[id(dice)]
        mods = ev.total_mods(dice.suffix)
        n = dice.count
        if n == 0:
            return {((), (), _pack(mods)): 1}, 1, 1
        types, denom = self.die_types(dice, ev.binding, ev.depth)
        self.spend(len(types), 'One die')
        count = comb(len(types) + n - 1, n)
        self.spend(count, f'{dice.text}')
        keep, drop = _select(dice.suffix, ev.binding)
        out = {}
        for combo in itertools.combinations_with_replacement(range(len(types)), n):
            weight = factorial(n)
            for _t, group in itertools.groupby(combo):
                weight //= factorial(len(list(group)))
            naturals, modified = [], []
            for t in combo:
                (a, chain), w = types[t]
                weight *= w
                naturals.append((a, leaf))
                modified.extend((v, leaf) for v in chain)
            kept = _apply_window(modified, keep, drop)
            stats = mods * _T
            for v, _leaf in kept:
                stats += rules.kept_key(v)
            for a, _leaf in naturals:
                stats += rules.natural_key(a)
            key = (_canonical(kept), _canonical(naturals), stats)
            out[key] = out.get(key, 0) + weight
        return out, denom ** n, 1

    def die_types(self, dice, binding, depth):
        """[((natural face, tuple of modified values), weight)] for one die."""
        draw, denom = _draw(dice, binding)
        explodes = _explodes(dice, binding)
        if explodes is None or dice.types != 'int':
            return [((a, (v,)), w) for (a, v), w in draw.items()], denom
        if dice.explode.compound:
            values, vdenom = _compound_values(dice, binding, depth)
            return [((a, (v,)), w) for (a, v), w in values.items()], vdenom
        terminal, exploding, _ = _chain_values(dice, binding)
        # level: chains of later draws that may add `budget` dice, over denom ** budget.
        level = []
        for budget in range(1, depth + 1):
            grown = [((v,), w * denom ** (budget - 1)) for v, w in terminal.items()]
            if budget > 1:
                grown += [((v,) + chain, w * x) for v, w in exploding.items() for chain, x in level]
            level = grown
            self.spend(len(level), 'Explosion chains')
        types = []
        for (a, v), w in draw.items():
            if not explodes(v):
                types.append(((a, (v,)), w * denom ** depth))
            elif depth:
                for chain, x in level:
                    types.append(((a, (v,) + chain), w * x))
        return _merge_types(types), denom ** (depth + 1)

    def group(self, group, own_mods=True):
        ev = self.ev
        inner, denom, tscale = self.node(group.child)
        keep, drop = _select(group.suffix, ev.binding)
        mods = ev.total_mods(group.suffix) if own_mods else 0
        out = {}
        if keep is None and drop is None:
            for (k, n, stats), w in inner.items():
                key = (k, n, stats + mods * tscale * _T)
                out[key] = out.get(key, 0) + w
            return out, denom, tscale
        leaf_rules = {self.index[id(d)]: ev.leaf_rules(d) for d in leaves(group.child)}
        for (k, n, stats), w in inner.items():
            kept = _apply_window(list(k), keep, drop)
            _t, _s, _f, ns, nf = _unpack(stats)
            new = mods * _T + _pack(0, 0, 0, ns, nf)
            for v, leaf in kept:
                new += leaf_rules[leaf].kept_key(v)
            key = (_canonical(kept), n, new)
            out[key] = out.get(key, 0) + w
        return out, denom, 1


def _merge_types(types):
    merged = {}
    for t, w in types:
        merged[t] = merged.get(t, 0) + w
    return list(merged.items())


def _face_key(entry):
    return (isinstance(entry[0], str), entry[0], entry[1])


def _canonical(entries):
    return tuple(sorted(entries, key=_face_key))


def _merge(a, b):
    return _canonical(a + b)


def _apply_window(entries, keep, drop):
    """Keep then drop, ties in leaf order, matching DiceRoller.keep_drop."""
    rolls = list(entries)
    if keep is not None:
        layer, count = keep
        rolls = sorted(rolls, key=_sort_high if layer == 'high' else _sort_low)[:count]
    if drop is not None:
        layer, count = drop
        size = len(rolls) - count
        if size <= 0:
            return []
        rolls = sorted(rolls, key=_sort_high if layer == 'low' else _sort_low)[:size]
    return rolls


def _sort_high(entry):
    return (-entry[0], entry[1])


def _sort_low(entry):
    return (entry[0], entry[1])


def _multiset_group_stats(group, evaluator):
    """Keep/drop on a group whose members are not plain dice: enumerate multisets."""
    out, denom, tscale = _Multisets(evaluator, evaluator.limit).group(group, own_mods=False)
    weights = {}
    for (_k, _n, stats), w in out.items():
        weights[stats] = weights.get(stats, 0) + w
    return _Dist(weights, denom, tscale)


# ---------------------------------------------------------------------------
# Public interface

@dataclass
class ExactResult:
    """Joint distribution of a dice expression.

    ``joint`` maps tuples in ``FIELDS`` order to exact probabilities.  A field
    the expression does not define is None in every key (``fail`` without an
    ``f`` token, ``pass`` without a total check).  Probabilities sum to
    ``1 - unresolved``; ``unresolved`` is the mass of explosion chains deeper
    than ``explode_depth`` and is zero without explosions.  ``faces``, when
    requested, maps (kept modified faces, natural faces, outcome) to
    probability, faces sorted ascending (text faces after numbers).
    """
    expression: str
    joint: dict
    unresolved: Fraction
    explode_depth: int
    faces: dict = None
    fields: tuple = FIELDS
    # The joint as integer numerators over one denominator, for fast sums.
    _numerators: dict = field(default=None, repr=False, compare=False)
    _denominator: int = field(default=1, repr=False, compare=False)

    def records(self):
        """The joint as a list of dicts with FIELDS keys plus 'probability'."""
        return [dict(zip(FIELDS, key), probability=p) for key, p in sorted(
            self.joint.items(), key=lambda item: tuple(_sortable(x) for x in item[0]))]

    def marginal(self, field):
        """{value: probability} of one field (None if the field is undefined)."""
        index = FIELDS.index(field)
        if self._numerators is None:
            out = {}
            for key, p in self.joint.items():
                out[key[index]] = out.get(key[index], 0) + p
            return out
        sums = {}
        for key, w in self._numerators.items():
            sums[key[index]] = sums.get(key[index], 0) + w
        return {value: Fraction(w, self._denominator) for value, w in sums.items()}

    def probability(self, predicate):
        """Probability of the outcomes whose field dict satisfies predicate."""
        return sum((p for key, p in self.joint.items() if predicate(dict(zip(FIELDS, key)))),
                   Fraction(0))

    def mean(self, field):
        """Exact mean over the resolved outcomes (sum of value * probability)."""
        marginal = self.marginal(field)
        if None in marginal:
            raise ValueError(f'Field {field!r} is not defined by {self.expression!r}')
        return sum((value * p for value, p in marginal.items()), Fraction(0))

    def variance(self, field):
        mean = self.mean(field)
        return sum(((value - mean) ** 2 * p for value, p in self.marginal(field).items()),
                   Fraction(0))


def _sortable(x):
    return (x is None, x if x is not None else 0)


def exact(expression, explode_depth=DEFAULT_EXPLODE_DEPTH, faces=False,
          faces_limit=DEFAULT_FACES_LIMIT):
    """Exact joint distribution of ``expression``; see ExactResult.

    ``explode_depth`` caps the extra dice one die may add by exploding.
    ``faces=True`` also returns the distribution of sorted faces, enumerating
    at most ``faces_limit`` multisets per step (DiceException beyond it).  The
    same limit bounds keep/drop on a group whose members are not plain dice
    terms (members with their own keep/drop or non-compounding explosions),
    which is computed by the same enumeration.
    """
    if not isinstance(explode_depth, int) or not 0 <= explode_depth <= MAX_EXPLODE_DEPTH:
        raise DiceException('Unable to analyse expression',
                            f'explode_depth must be an integer from 0 to {MAX_EXPLODE_DEPTH}')
    tree = parse(expression)
    rules = CountingRules(tree)
    defined = rules.defined
    check = tree.suffix.check if isinstance(tree, (Dice, Group)) else None
    joint_parts, face_parts = [], []
    for binding, (bw, bd) in _bindings(tree):
        evaluator = _Evaluator(tree, rules, binding, explode_depth, faces_limit)
        dist = evaluator.node(tree)
        checker = None if check is None else (check.operator, bound(check.value, binding))
        table = {}
        for key, w in dist.weights.items():
            outcome = _outcome(key, dist.tscale, defined, checker)
            table[outcome] = table.get(outcome, 0) + w * bw
        joint_parts.append((table, bd * dist.denom))
        if faces:
            multisets, denom, tscale = _Multisets(evaluator, faces_limit).node(tree)
            table = {}
            for (kept, natural, stats), w in multisets.items():
                outcome = _outcome(stats, tscale, defined, checker)
                key = (tuple(v for v, _l in kept), tuple(a for a, _l in natural), outcome)
                table[key] = table.get(key, 0) + w * bw
            face_parts.append((table, bd * denom))
    numerators, denominator = _over_common_denominator(joint_parts)
    joint = {k: Fraction(w, denominator) for k, w in numerators.items()}
    unresolved = Fraction(denominator - sum(numerators.values()), denominator)
    face_law = None
    if faces:
        face_numerators, face_denominator = _over_common_denominator(face_parts)
        face_law = {k: Fraction(w, face_denominator) for k, w in face_numerators.items()}
    return ExactResult(expression, joint, unresolved, explode_depth, face_law,
                       _numerators=numerators, _denominator=denominator)


def _over_common_denominator(parts):
    """Sum integer tables given over different denominators; drop zeros."""
    denominator = 1
    for _table, d in parts:
        denominator = denominator * d // _gcd(denominator, d)
    numerators = {}
    for table, d in parts:
        scale = denominator // d
        for key, w in table.items():
            numerators[key] = numerators.get(key, 0) + w * scale
    return {k: w for k, w in numerators.items() if w}, denominator


def _outcome(key, tscale, defined, checker):
    total, s, f, ns, nf = _unpack(key)
    if tscale != 1:
        total = Fraction(total, tscale)
        if total.denominator == 1:
            total = total.numerator
    return (
        total,
        s if defined['success'] else None,
        f if defined['fail'] else None,
        ns if defined['ns'] else None,
        nf if defined['nf'] else None,
        None if checker is None else int(safe_compare(total, *checker)),
    )


def _bindings(tree):
    """(binding, (weight, denominator)) over every joint value of the subrolls."""
    rolls = subrolls(tree)
    if not rolls:
        yield {}, (1, 1)
        return
    laws = []
    combinations = 1
    for roll in rolls:
        law = _power({face: 1 for face in range(1, roll.sides + 1)}, roll.count)
        laws.append((roll, law, roll.sides ** roll.count))
        combinations *= len(law)
    if combinations > MAX_SUBROLL_COMBINATIONS:
        raise DiceException('Unable to analyse expression',
                            f'Subrolls take {combinations} joint values, over the limit of '
                            f'{MAX_SUBROLL_COMBINATIONS}')
    denom = 1
    for _roll, _law, d in laws:
        denom *= d
    for picks in itertools.product(*[sorted(law.items()) for _r, law, _d in laws]):
        binding, weight = {}, 1
        for (roll, _law, _d), (value, w) in zip(laws, picks):
            binding[id(roll)] = value
            weight *= w
        yield binding, (weight, denom)
