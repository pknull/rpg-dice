"""Brute-force oracles for the exact engine.

Two independent oracles, both slow and both exact:

``replay_distribution`` runs the real ``DiceThrower`` under a scripted random
source that walks every possible sequence of die faces once, weighting each
complete sequence by the product of its choice probabilities.  It therefore
reproduces the roller's own semantics (rerolls, explosions, subrolls, groups)
by construction.  Sequences longer than ``max_draws`` faces are cut off and
their mass is returned as ``truncated``.

``product_distribution`` is the original enumeration over every ordered roll
(``itertools.product``) for plain pools without rerolls or explosions.  It
does not touch the roller at all.
"""
import itertools
from collections import defaultdict
from contextlib import contextmanager
from fractions import Fraction

import dice_roller.Die as die_module
from dice_roller.DiceThrower import DiceThrower
from dice_roller.safe_compare import safe_compare

FIELDS = ('total', 'success', 'fail', 'ns', 'nf', 'pass')


class _Truncated(BaseException):
    """Raised inside a replay when the draw budget is spent.

    BaseException so no ``except Exception`` in the roller can swallow it.
    """


class _Replay:
    def __init__(self, prefix, max_draws):
        self.prefix = prefix
        self.max_draws = max_draws
        self.choices = []
        self.sizes = []

    def choice(self, seq):
        seq = list(seq)
        i = len(self.choices)
        if i >= self.max_draws:
            raise _Truncated()
        idx = self.prefix[i] if i < len(self.prefix) else 0
        self.choices.append(idx)
        self.sizes.append(len(seq))
        return seq[idx]

    def randint(self, a, b):
        return self.choice(range(a, b + 1))


@contextmanager
def _patched_random(replay):
    """Route every face draw through ``replay``.

    ``Die.__init__`` rolls once and the roller overwrites that face before
    reading it; skipping that draw changes no result and keeps the walk from
    branching on faces nobody sees.
    """
    original_random = die_module.random
    original_init = die_module.Die.__init__

    def init_without_roll(self, sides):
        self.sides = sides
        self.showing = 0

    die_module.random = replay
    die_module.Die.__init__ = init_without_roll
    try:
        yield
    finally:
        die_module.random = original_random
        die_module.Die.__init__ = original_init


def outcome_of(result):
    """Map a throw() result dict to a tuple in FIELDS order (None if absent)."""
    out = []
    for field in FIELDS:
        value = result.get(field)
        if value is None:
            out.append(None)
        else:
            out.append(Fraction(value) if '/' in str(value) else int(value))
    return tuple(out)


def faces_of(result):
    """Sorted kept modified faces and sorted natural faces of a throw()."""
    return tuple(sorted(result['modified'], key=_face_key)), tuple(sorted(result['natural'], key=_face_key))


def _face_key(face):
    return (isinstance(face, str), face)


def replay_distribution(expression, max_draws=12, key=outcome_of, call=None):
    """Exact distribution of ``key(throw(expression))`` by exhaustive replay.

    ``call(thrower, expression)`` replaces ``thrower.throw(expression)``, for
    example to replay ``throw_string``.  Returns ``(dist, truncated)`` where
    ``dist`` maps keys to Fractions and ``truncated`` is the mass of sequences
    that needed more than ``max_draws`` faces.
    """
    thrower = DiceThrower()
    run = call if call is not None else (lambda t, e: t.throw(e))
    dist = defaultdict(Fraction)
    truncated = Fraction(0)
    stack: list[tuple[int, ...]] = [()]
    while stack:
        prefix = stack.pop()
        replay = _Replay(prefix, max_draws)
        with _patched_random(replay):
            try:
                result = run(thrower, expression)
            except _Truncated:
                result = None
        if isinstance(result, str):
            raise AssertionError(f'roller rejected {expression!r}: {result}')
        prob = Fraction(1)
        for size in replay.sizes:
            prob /= size
        for k in range(len(prefix), len(replay.choices)):
            for j in range(1, replay.sizes[k]):
                stack.append(tuple(replay.choices[:k]) + (j,))
        if result is None:
            truncated += prob
        else:
            dist[key(result)] += prob
    return dict(dist), truncated


def product_distribution(n, faces, per_die=0, keep=None, success=None, fail=None,
                         ns=None, nf=None, total_mod=0, check=None):
    """Enumerate every ordered roll of ``n`` dice over ``faces``.

    ``keep`` is ``(layer, count)`` with layer 'high' or 'low'.  Counters are
    ``(operator, value)``; ``success`` defaults to ``('>=', max(faces))`` as
    in the roller.  Returns a dict over FIELDS-ordered tuples.
    """
    if success is None:
        success = ('>=', max(faces))
    dist = defaultdict(Fraction)
    weight = Fraction(1, len(faces) ** n) if n else Fraction(1)
    for roll in itertools.product(faces, repeat=n):
        modified = [v + per_die for v in roll]
        if keep is not None:
            layer, count = keep
            modified = sorted(modified, reverse=(layer == 'high'))[:count]
        total = sum(modified) + total_mod
        key = (
            total,
            sum(1 for v in modified if safe_compare(v, *success)),
            None if fail is None else sum(1 for v in modified if safe_compare(v, *fail)),
            None if ns is None else sum(1 for v in roll if safe_compare(v, *ns)),
            None if nf is None else sum(1 for v in roll if safe_compare(v, *nf)),
            None if check is None else int(safe_compare(total, *check)),
        )
        dist[key] += weight
    return dict(dist)


def marginal(dist, field):
    index = FIELDS.index(field)
    out = defaultdict(Fraction)
    for key, prob in dist.items():
        out[key[index]] += prob
    return dict(out)
