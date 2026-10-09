"""Cross-check of the exact engine against icepool.

icepool is a test-only dependency (requirements-test.txt).  It is imported
here and nowhere in dice_roller.  Where icepool truncates explosions, both
sides carry a known residual and outcomes are compared within it.
"""
from fractions import Fraction

import icepool
import pytest
from icepool import Die, Pool, Vector, d4, d6, d8, d10, d20

from dice_roller.DiceProbability import DiceProbability


def exact(expression, **kwargs):
    return DiceProbability().exact(expression, **kwargs)


def icepool_dist(die):
    return {outcome: Fraction(q, die.denominator()) for outcome, q in die.items()}


def total_and_success(die_faces, success):
    return Die([Vector((face, int(success(face)))) for face in die_faces])


TOTAL_CASES = [
    ('3d6', 3 @ d6),
    ('2d6+3', 2 @ (d6 + 3)),
    ('3d4/2', 3 @ d4.map(lambda v: int(Fraction(v, 2)))),
    ('4d6dl1', d6.pool(4).highest(3).sum()),
    ('10d6kh3', d6.pool(10).highest(3).sum()),
    ('10d10kh3', d10.pool(10).highest(3).sum()),
    ('8d6kl2', d6.pool(8).lowest(2).sum()),
    ('5d6kh4dh1', d6.pool(5)[1:4].sum()),
    ('5d6kh4dl1', d6.pool(5).highest(3).sum()),
    ('4d6+1kh3', (d6 + 1).pool(4).highest(3).sum()),
    ('3d6r1', 3 @ d6.reroll([1], depth='inf')),
    ('3d6ro<3', 3 @ d6.reroll([1, 2], depth=1)),
    ('4d6r1kh3', d6.reroll([1], depth='inf').pool(4).highest(3).sum()),
    ('1d8+1d6', d8 + d6),
    ('1d20-1d4', d20 - d4),
    ('(1d8+1d6)*2', (d8 + d6) * 2),
    ('((2d6)+(2d8))kh3', Pool([d6, d6, d8, d8]).highest(3).sum()),
    ('4d{-1,0,1}=+2', 4 @ Die([-1, 0, 1]) + 2),
]


@pytest.mark.parametrize('expression, die', TOTAL_CASES, ids=[c[0] for c in TOTAL_CASES])
def test_total_distribution(expression, die):
    assert exact(expression).marginal('total') == icepool_dist(die)


PASS_CASES = [
    ('2d20=+5kh1t>=15', d20.pool(2).highest(1).sum() + 5 >= 15, Fraction(319, 400)),
    ('4d{-1,0,1}=+2t>=3', 4 @ Die([-1, 0, 1]) + 2 >= 3, Fraction(31, 81)),
    ('3d6t>=10', 3 @ d6 >= 10, Fraction(5, 8)),
    ('1d100t<=45', icepool.d100 <= 45, Fraction(9, 20)),
]


@pytest.mark.parametrize('expression, die, stated', PASS_CASES, ids=[c[0] for c in PASS_CASES])
def test_pass_probability(expression, die, stated):
    assert exact(expression).marginal('pass')[1] == die.probability(True) == stated


@pytest.mark.parametrize('expression, faces, success, n', [
    ('3d6>=5', range(1, 7), lambda v: v >= 5, 3),
    ('5d6>=6', range(1, 7), lambda v: v >= 6, 5),
    ('6d10>=8', range(1, 11), lambda v: v >= 8, 6),
])
def test_total_success_joint(expression, faces, success, n):
    joint = icepool_dist(n @ total_and_success(faces, success))
    mine = {Vector((k[0], k[1])): p for k, p in exact(expression).joint.items()}
    assert mine == joint


def within(mine, unresolved, theirs, their_residual):
    for key in set(mine) | set(theirs):
        a, b = mine.get(key, Fraction(0)), theirs.get(key, Fraction(0))
        assert b - a <= unresolved + their_residual, key
        assert a - b <= their_residual, key


def test_explode_total():
    result = exact('3d6x6', explode_depth=12)
    theirs = icepool_dist(3 @ d6.explode([6], depth=40))
    within(result.marginal('total'), result.unresolved, theirs, 3 * Fraction(1, 6) ** 40)


def test_compound_total_equals_explode_total():
    result = exact('2d6xx>=5', explode_depth=12)
    theirs = icepool_dist(2 @ d6.explode([5, 6], depth=40))
    within(result.marginal('total'), result.unresolved, theirs, 2 * Fraction(1, 3) ** 40)


def _wod_chain(depth):
    return d10.map(lambda v: int(v >= 8) + (_wod_chain(depth - 1) if v == 10 and depth > 0 else 0))


def test_world_of_darkness_ten_again():
    result = exact('10d10>=8x>=10', explode_depth=10)
    theirs = icepool_dist(10 @ _wod_chain(30))
    within(result.marginal('success'), result.unresolved, theirs, 10 * Fraction(1, 10) ** 30)
    assert result.unresolved == 1 - (1 - Fraction(1, 10) ** 11) ** 10


def test_savage_worlds_trait_and_wild_die():
    result = exact('((1d8xx)+(1d6xx))kh1', explode_depth=12)
    theirs = icepool_dist(icepool.highest(d8.explode([8], depth=40), d6.explode([6], depth=40)))
    within(result.marginal('total'), result.unresolved, theirs, Fraction(2, 6 ** 40))
